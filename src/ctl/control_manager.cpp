/*
 *    Zevenet zproxy Load Balancer Software License
 *    This file is part of the Zevenet zproxy Load Balancer software package.
 *
 *    Copyright (C) 2019-today ZEVENET SL, Sevilla (Spain)
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Affero General Public License as
 *    published by the Free Software Foundation, either version 3 of the
 *    License, or any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Affero General Public License for more details.
 *
 *    You should have received a copy of the GNU Affero General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#include "control_manager.h"

/* Not used right now */
#define CTL_DEFAULT_IP "127.0.0.1"
#define CTL_DEFAULT_PORT 6001

using namespace ctl;

std::shared_ptr<ControlManager> ControlManager::instance = nullptr;

ctl::ControlManager::ControlManager(ctl::CTL_INTERFACE_MODE listener_mode)
    : is_running(false), ctl_listener_mode(listener_mode) {}

ctl::ControlManager::~ControlManager() {
  stop();
  // Stop current worker thread
  if (control_thread.joinable()) control_thread.join();
}

bool ctl::ControlManager::init(Config &configuration, ctl::CTL_INTERFACE_MODE listener_mode) {
  if (!configuration.ctrl_ip.empty() && configuration.ctrl_port != 0) {
    listener_mode = ctl::CTL_INTERFACE_MODE::CTL_AF_INET;
  } else {
    ctl_listener_mode = ctl::CTL_INTERFACE_MODE::CTL_UNIX != listener_mode ? listener_mode : ctl_listener_mode;
  }
  if (listener_mode == CTL_INTERFACE_MODE::CTL_UNIX) {
    std::string control_path_name(configuration.ctrl_name);
    control_listener.listen(control_path_name);
    if (!configuration.ctrl_user.empty())
      Environment::setFileUserName(std::string(configuration.ctrl_user), control_path_name);
    if (!configuration.ctrl_group.empty())
      Environment::setFileGroupName(std::string(configuration.ctrl_group), control_path_name);
    if (configuration.ctrl_mode > 0) Environment::setFileUserMode(configuration.ctrl_mode, control_path_name);
  } else {
    control_listener.listen(configuration.ctrl_ip, configuration.ctrl_port);
  }
  handleAccept(control_listener.getFileDescriptor());
  return true;
}

void ctl::ControlManager::start() {
  is_running = true;
  control_thread = std::thread([this] { doWork(); });
  helper::ThreadHelper::setThreadName("CTL_WORKER", control_thread.native_handle());
}

void ctl::ControlManager::stop() {
  // Notify stop to suscribers
  if (!is_running) return;
  is_running = false;
  Logger::logmsg(LOG_REMOVE, "Stop");
  CtlTask task;
  task.command = CTL_COMMAND::EXIT;
  task.target = CTL_HANDLER_TYPE::ALL;
  auto result = notify(task, false);
}

void ctl::ControlManager::HandleEvent(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group) {
  if (event_group != EVENT_GROUP::CTL_INTERFACE && event_group != EVENT_GROUP::ACCEPTOR) {
    ::close(fd);
    return;
  }

  switch (event_type) {
    case EVENT_TYPE::CONNECT: {
      int new_fd;
      do {
        new_fd = control_listener.doAccept();
        if (new_fd > 0) {
          addFd(new_fd, EVENT_TYPE::READ, EVENT_GROUP::CTL_INTERFACE);
        }
      } while (new_fd > 0);
      break;
    }
    case EVENT_TYPE::READ: {
      Connection connection;
      HttpRequest request;
      connection.setFileDescriptor(fd);
      auto res = connection.read();
      if (res != IO::IO_RESULT::SUCCESS && res != IO::IO_RESULT::DONE_TRY_AGAIN) {
        deleteFd(fd);
        ::close(fd);
        return;
      }
      size_t parsed = 0;
      auto parse_result = request.parseRequest(connection.buffer, connection.buffer_size, &parsed);

      if (parse_result != http_parser::PARSE_RESULT::SUCCESS) {
        deleteFd(fd);
        connection.closeConnection();
        return;
      }
      // Logger::logmsg(LOG_DEBUG, "CTL API Request: %s", connection.buffer);
      std::string response = handleCommand(request);
      size_t written = 0;
      if (!response.empty()) {
        IO::IO_RESULT result;
        do {
          size_t sent;
          result = connection.write(response.c_str() + written,
                                    response.length() - written, sent);
          if (sent > 0) written += sent;
        } while (result == IO::IO_RESULT::DONE_TRY_AGAIN &&
                 written < response.length());
      }

      deleteFd(fd);
      connection.closeConnection();
      return;
    }
    default:
      // why would we be here???
      deleteFd(fd);
      ::close(fd);
      break;
  }
}

void ctl::ControlManager::doWork() {
  while (is_running) {
    if (loopOnce(EPOLL_WAIT_TIMEOUT) < 1) {
      // this should not happends
    }
  }
  Logger::logmsg(LOG_REMOVE, "Exiting loop");
}

std::shared_ptr<ControlManager> ctl::ControlManager::getInstance() {
  if (instance == nullptr) instance = std::shared_ptr<ControlManager>(new ControlManager());
  return instance;
}
std::string ctl::ControlManager::handleCommand(HttpRequest &request) {
  /* https://www.restapitutorial.com/lessons/httpmethods.html */
  /*
   *PUT: create or replace the object
    PATCH: set properties of the object
    POST: perform an operation on the object
    GET: retrieve the object
    DELETE: delete the object
   */
  CtlTask task;
  // get task action
  switch (request.getRequestMethod()) {
    case http::REQUEST_METHOD::DELETE:
      task.command = CTL_COMMAND::DELETE;
      break;
    case http::REQUEST_METHOD::POST:
    case http::REQUEST_METHOD::PUT:
      task.command = CTL_COMMAND::ADD;
      break;
    case http::REQUEST_METHOD::PATCH:
    case http::REQUEST_METHOD::UPDATE:
      task.command = CTL_COMMAND::UPDATE;
      break;
    case http::REQUEST_METHOD::GET:
      task.command = CTL_COMMAND::GET;
      break;
    case http::REQUEST_METHOD::SUBSCRIBE:
      task.command = CTL_COMMAND::SUSCRIBE;
      break;
    case http::REQUEST_METHOD::UNSUBSCRIBE:
      task.command = CTL_COMMAND::UNSUSCRIBE;
      break;
    default:
      return http::getHttpResponse(http::Code::MethodNotAllowed, "", "");
  }

  // remove tailing "/"

  if (!setTaskTarget(request, task) && task.target == CTL_HANDLER_TYPE::NONE) {
    Logger::logmsg(LOG_WARNING, "Bad API request : %s", request.getUrl().c_str());
    return http::getHttpResponse(http::Code::BadRequest, "", "");
  }
  if (task.command == CTL_COMMAND::ADD || task.command == CTL_COMMAND::UPDATE || task.command == CTL_COMMAND::DELETE) {
    task.data = std::string(request.message, request.message_length);
  }

  auto result = notify(task, false);
  std::string res;
  for (auto &future_result : result) {
    res += future_result.get();
  }
  res += "";
  if (res.empty()) res = JSON_OP_RESULT::ERROR;
  auto response = http::getHttpResponse(http::Code::OK, "", res);
  return response;
}

bool ControlManager::setTaskTarget(HttpRequest &request, CtlTask &task) {
  std::istringstream f(request.getUrl());
  std::string str;
  while (getline(f, str, '/')) {
    switch (str[0]) {
      case 'l': {
        if (str == JSON_KEYS::LISTENER) {
          if (setListenerTarget(task, f)) {
            return true;
          }
        }
        break;
      }
      case 's': {
        if (str == JSON_KEYS::SERVICE) {
          if (setServiceTarget(task, f)) {
            return true;
          }
        }
        break;
      }
      case 'b': {
        if (str == JSON_KEYS::BACKEND) {
          if (setBackendTarget(task, f)) {
            return true;
          }
        }
        break;
      }
    }
  }
  return false;
}

bool ControlManager::setListenerTarget(CtlTask &task, std::istringstream &ss) {
  std::string str;
  task.target = CTL_HANDLER_TYPE::LISTENER;
  if (getline(ss, str, '/')) {
    if (!helper::try_lexical_cast<int>(str, task.listener_id)) {
      return false;
    }
    if (getline(ss, str, '/')) {
      if (str == JSON_KEYS::SERVICE || str == JSON_KEYS::SERVICES) {
        return setServiceTarget(task, ss);
      } else if (str == JSON_KEYS::CONFIG) {
        task.subject = CTL_SUBJECT::CONFIG;
      } else if (str == JSON_KEYS::STATUS) {
        task.subject = CTL_SUBJECT::STATUS;
      } else if (str == JSON_KEYS::DEBUG) {
        task.subject = CTL_SUBJECT::DEBUG;
      } else {
        return false;
      }
    }
  }
  return true;
}

bool ControlManager::setServiceTarget(CtlTask &task, std::istringstream &ss) {
  std::string str;
  task.target = CTL_HANDLER_TYPE::SERVICE_MANAGER;
  if (getline(ss, str, '/')) {
    if (!helper::try_lexical_cast<int>(str, task.service_id)) {
      task.service_id = -1;
      task.service_name = str;
    }
    if (getline(ss, str, '/')) {
      if (str == JSON_KEYS::BACKEND) {
        return setBackendTarget(task, ss);
      } else if (str == JSON_KEYS::CONFIG) {
        task.subject = CTL_SUBJECT::CONFIG;
      } else if (str == JSON_KEYS::STATUS) {
        task.subject = CTL_SUBJECT::STATUS;
      } else if (str == JSON_KEYS::SESSION || str == JSON_KEYS::SESSIONS) {
        task.subject = CTL_SUBJECT::SESSION;
#ifdef CACHE_ENABLED
      } else if (str == JSON_KEYS::CACHE) {
        task.subject = CTL_SUBJECT::CACHE;
#endif
      } else if (str == JSON_KEYS::BACKENDS) {
        task.subject = CTL_SUBJECT::S_BACKEND;
      } else {
        return false;
      }
    }
  }
  return true;
}

bool ControlManager::setBackendTarget(CtlTask &task, std::istringstream &ss) {
  std::string str;
  if (getline(ss, str, '/')) {
    if (!helper::try_lexical_cast<int>(str, task.backend_id)) {
      task.backend_id = -1;
      task.backend_name = str;
    }
    if (getline(ss, str, '/')) {
      if (str == JSON_KEYS::CONFIG) {
        task.subject = CTL_SUBJECT::CONFIG;
      } else if (str == JSON_KEYS::STATUS) {
        task.subject = CTL_SUBJECT::STATUS;
      } else if (str == JSON_KEYS::WEIGHT) {
        task.subject = CTL_SUBJECT::WEIGHT;
      } else {
        return false;
      }
    }
  }
  return true;
}
