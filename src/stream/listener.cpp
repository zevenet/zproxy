//
// Created by abdess on 4/5/18.
//

#include "listener.h"
#include "../service/httpsessionmanager.h"

#define DEFAULT_MAINTENANCE_INTERVAL 2000

void Listener::HandleEvent(int fd, EVENT_TYPE event_type,
                           EVENT_GROUP event_group) {
  if (event_group == EVENT_GROUP::MAINTENANCE &&
      fd == timer_maintenance.getFileDescriptor()) {
    Debug::LogInfo("Doing maintenance", LOG_REMOVE);
    //Debug::LogInfo("Session table\n\t\tKey\tbackend", LOG_REMOVE);
    //    std::vector<std::string> keys_to_delete;
    //    if (!sessions::HttpSessionManager::sessions_set.empty()) {
    //      for (auto session : sessions::HttpSessionManager::sessions_set) {
    //        if (session.second->hasExpired(10)) {
    //          keys_to_delete.push_back(session.first);
    //        }
    //        Debug::logmsg(LOG_REMOVE, "\t%s\t%s", session.first.c_str(),
    //                      session.second->assigned_backend->address.c_str());
    //      }

    //      for (auto& key : keys_to_delete) {
    //        std::lock_guard<std::mutex> locked(
    //            sessions::HttpSessionManager::lock_mtx);
    //        auto session = sessions::HttpSessionManager::sessions_set.at(key);
    //        sessions::HttpSessionManager::sessions_set.erase(key);
    //        delete session;
    //      }
    //    }
    //for (auto service : service_manager->services) {
    //  service->doMaintenance();
    //}
    timer_maintenance.set(DEFAULT_MAINTENANCE_INTERVAL);
    updateFd(timer_maintenance.getFileDescriptor(), EVENT_TYPE::READ,
             EVENT_GROUP::MAINTENANCE);

    for (auto serv : service_manager->getServices()) {
      serv->doMaintenance();
    }
    return;
  }
  switch (event_type) {
    case CONNECT: {
      int new_fd;
      do {
        new_fd = listener_connection.doAccept();
        if (new_fd > 0) {
          auto sm = getManager(new_fd);
          if (sm != nullptr) {
            // sm->stream_set.size() ????
            sm->addStream(new_fd);
          } else {
            Debug::LogInfo("StreamManager not found");
          }
        }
      } while (new_fd > 0);
      break;
    }
      //    case READ: {
      //      Connection cnt;
      //      cnt.setFileDescriptor(fd);
      //      cnt.read();
      //      //      Debug::LogInfo(cnt.string_buffer.string());
      //      std::string send_e200 =
      //          "HTTP/1.1 200 OK\r\nContent-Length: 11\r\n\r\nHello World";
      //      cnt.write(send_e200.c_str(), send_e200.length());
      //    } break;
    default:
      Debug::LogInfo("###################Why!!!!!!!! ");  // TODO::REMOVE
      break;
  }
}

std::string Listener::handleTask(ctl::CtlTask& task) {
  Debug::logmsg(LOG_DEBUG, "listener handling task");
  return "{id:0;type:listener}";
}

bool Listener::isHandler(ctl::CtlTask& task) {
  return task.target != ctl::CTL_HANDLER_TYPE::LISTENER ? false : true;
}

bool Listener::init(std::string address, int port) {
  if (!listener_connection.listen(address, port)) return false;
  return true;  // handleAccept(listener_connection.getFileDescriptor());
}

Listener::Listener()
    : is_running(false), listener_connection(), stream_manager_set() {
  ctl::ControlManager::getInstance()->attach(std::ref(*this));
  auto concurrency_lever = std::thread::hardware_concurrency() - 1;
  for (int sm = 0; sm < concurrency_lever; sm++) {
    stream_manager_set[sm] = new StreamManager();
  }
}

Listener::~Listener() {
  is_running = false;
  for (auto& sm : stream_manager_set) {
    sm.second->stop();
    delete sm.second;
  }
  worker_thread.join();
}

void Listener::doWork() {
  while (is_running) {
    if (loopOnce() <= 0) {
      // something bad happend
      //      Debug::LogInfo("No event received");
    }
  }
}

void Listener::stop() { is_running = false; }

void Listener::start() {
  ctl::ControlManager::getInstance()->deAttach(std::ref(*this));
  int service_id = 0;
  for (auto service_config = listener_config.services;
       service_config != nullptr; service_config = service_config->next) {
    if (!service_config->disabled) {
      ServiceManager::getInstance(listener_config)
          ->addService(*service_config, ++service_id);
    } else {
      Debug::LogInfo("Backend " + std::string(service_config->name) +
                     " disabled in config file",
                 LOG_NOTICE);
    }
  }
  for (int i = 0; i < stream_manager_set.size(); i++) {
    auto sm = stream_manager_set[i];
    if (sm != nullptr && sm->init(listener_config)) {
      sm->setListenSocket(listener_connection.getFileDescriptor());
      sm->start(i);
    } else {
      Debug::LogInfo("StreamManager id doesn't exist : " + std::to_string(i),
                 LOG_ERR);
    }
  }
  is_running = true;
  //  worker_thread = std::thread([this] { doWork(); });
  //  helper::ThreadHelper::setThreadAffinity(
  //      0, pthread_self());  // worker_thread.native_handle());
  //#if SM_HANDLE_ACCEPT
  //  while (is_running) {
  //    std::this_thread::sleep_for(std::chrono::seconds(5));
  //  }
  //#else

    timer_maintenance.set(DEFAULT_MAINTENANCE_INTERVAL);
    addFd(timer_maintenance.getFileDescriptor(), EVENT_TYPE::READ,
          EVENT_GROUP::MAINTENANCE);

  helper::ThreadHelper::setThreadName("LISTENER", pthread_self());
  doWork();
  //#endif
}

StreamManager* Listener::getManager(int fd) {
  static unsigned long c;
  ++c;
  unsigned long id = c % stream_manager_set.size();
  return stream_manager_set[id];
}

bool Listener::init(ListenerConfig& config) {
  listener_config = config;
  service_manager = ServiceManager::getInstance(listener_config);

  if (!listener_connection.listen(listener_config.addr)) return false;
#if SM_HANDLE_ACCEPT
  return true;
#else
  return handleAccept(listener_connection.getFileDescriptor());
#endif
}
