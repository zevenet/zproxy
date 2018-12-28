//
// Created by abdess on 9/28/18.
//

#include "ControlManager.h"

#define CTL_DEFAULT_IP "127.0.0.1"
#define CTL_DEFAULT_PORT 6001

using namespace ctl;

std::unique_ptr<ControlManager> ControlManager::instance =
    std::unique_ptr<ControlManager>(new ControlManager);

ctl::ControlManager::ControlManager(ctl::CTL_INTERFACE_MODE listener_mode)
    : is_running(false), ctl_listener_mode(listener_mode) {}

ctl::ControlManager::~ControlManager() { stop(); }

bool ctl::ControlManager::init(Config &configuration,
                               ctl::CTL_INTERFACE_MODE listener_mode) {
  ctl_listener_mode = ctl::CTL_INTERFACE_MODE::CTL_UNIX != listener_mode
                          ? listener_mode
                          : ctl_listener_mode;
  if (listener_mode == CTL_INTERFACE_MODE::CTL_UNIX) {
    std::string control_path_name(configuration.ctrl_name);
    control_listener.listen(control_path_name);
    if (configuration.ctrl_user)
      Environment::setFileUserName(std::string(configuration.ctrl_user),
                                   control_path_name);
    if (configuration.ctrl_group)
      Environment::setFileGroupName(std::string(configuration.ctrl_group),
                                    control_path_name);
    if (configuration.ctrl_mode > 0)
      Environment::setFileUserMode(configuration.ctrl_mode, control_path_name);
  } else {
    control_listener.listen(CTL_DEFAULT_IP, CTL_DEFAULT_PORT);
  }
  handleAccept(control_listener.getFileDescriptor());
  return true;
}

void ctl::ControlManager::start() {
  is_running = true;
  control_thread = std::thread([this] { doWork(); });
  helper::ThreadHelper::setThreadName("CTL_WORKER",
                                      control_thread.native_handle());
}

void ctl::ControlManager::stop() {
  if(is_running)
    control_thread.join();
  is_running = false;
}

void ctl::ControlManager::HandleEvent(int fd, EVENT_TYPE event_type,
                                      EVENT_GROUP event_group) {
  if (event_group != EVENT_GROUP::CTL_INTERFACE && event_group != EVENT_GROUP::ACCEPTOR) {
    ::close(fd);
    return;
  }

  switch (event_type) {
  case CONNECT: {
    int new_fd;
    new_fd = control_listener.doAccept();
    if (new_fd > 0) {
      addFd(new_fd, EVENT_TYPE::READ, EVENT_GROUP::CTL_INTERFACE);
    }
    break;
  }
  case READ: {
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
    auto parse_result = request.parseRequest(connection.buffer,
                                             connection.buffer_size, &parsed);

    if (parse_result != http_parser::PARSE_RESULT::SUCCESS) {
      deleteFd(fd);
      connection.closeConnection();
      return;
    }
    Debug::logmsg(LOG_DEBUG, "CTL API Request: %s", connection.buffer);

    std::string response = handleCommand(request);

    if (!response.empty()) {
      connection.write(response.c_str(), response.length());
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
    if (loopOnce() < 1) {
      // this should not happends
    }
  }
}

ctl::ControlManager *ctl::ControlManager::getInstance() {
  if (instance == nullptr)
    instance = std::unique_ptr<ControlManager>(new ControlManager());
  return instance.get();
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
    return HttpStatus::getHttpResponse(HttpStatus::Code::MethodNotAllowed, "",
                                       "");
  }

  // remove tailing "/"

  if (!setTaskTarget(request, task) && task.target == CTL_HANDLER_TYPE::NONE) {
    Debug::logmsg(LOG_WARNING, "Bad API request : %s",
                  request.getUrl().c_str());
    return HttpStatus::getHttpResponse(HttpStatus::Code::BadRequest, "", "");
  }
  if (task.command == CTL_COMMAND::ADD || task.command == CTL_COMMAND::UPDATE || task.command == CTL_COMMAND::DELETE) {
    task.data = std::string(request.message, request.message_length);
  }
  // TODO:: Concatenate more than one future result
  auto result = notify(task, false);
  std::string res = "";
  for (auto &future_result : result) {
    res += future_result.get();
  }
  res += "";

  auto response = HttpStatus::getHttpResponse(HttpStatus::Code::OK, "", res);
  return response;
}

bool ControlManager::setTaskTarget(HttpRequest &request, CtlTask &task) {
  std::istringstream f(request.getUrl());
  std::string str;
  bool done = false;
  while (getline(f, str, '/') && !done) {
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
    // TODO:: Enable???    task.target = CTL_HANDLER_TYPE::SERVICE;
    if (getline(ss, str, '/')) {
      if (str == JSON_KEYS::BACKEND) {
        return setBackendTarget(task, ss);
      } else if (str == JSON_KEYS::CONFIG) {
        task.subject = CTL_SUBJECT::CONFIG;
      } else if (str == JSON_KEYS::STATUS) {
        task.subject = CTL_SUBJECT::STATUS;
      } else if (str == JSON_KEYS::SESSION || str == JSON_KEYS::SESSIONS) {
        task.subject = CTL_SUBJECT::SESSION;
      } else {
        return false;
      }
    }
  }
  return true;
}

bool ControlManager::setBackendTarget(CtlTask &task, std::istringstream &ss) {
  std::string str;
  // TODO:: Enable???   task.target = CTL_HANDLER_TYPE::BACKEND;
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
