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

#include "listener_manager.h"

#include <memory>
#include "../config/global.h"
#include "../ssl/ssl_session.h"
#ifdef ENABLE_HEAP_PROFILE
#include <gperftools/heap-profiler.h>
#endif
#if WAF_ENABLED
#include "../handlers/waf.h"
#endif
#ifndef DEFAULT_MAINTENANCE_INTERVAL
#define DEFAULT_MAINTENANCE_INTERVAL 2
#endif
#ifndef MALLOC_TRIM_TIMER_INTERVAL
#define MALLOC_TRIM_TIMER_INTERVAL 300
#endif

void ListenerManager::HandleEvent(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group) {
  if (event_group == EVENT_GROUP::MAINTENANCE) {
    if (fd == timer_maintenance.getFileDescriptor()) {
      // general maintenance timer
      for (const auto& lc : listener_config_set){
        if(lc->disabled)
          continue;
        for(auto service : ServiceManager::getInstance(*lc)->getServices()) {
            service->doMaintenance();
        }
      }
      timer_maintenance.set(global::run_options::getCurrent().backend_resurrect_timeout * 1000);
      updateFd(timer_maintenance.getFileDescriptor(), EVENT_TYPE::READ_ONESHOT,
               EVENT_GROUP::MAINTENANCE);
    }
    if (fd == ssl_maintenance_timer.getFileDescriptor()) {
      // timer for ssl rsa keys regeneration
      global::SslHelper::doRSAgen();
      ssl_maintenance_timer.set(T_RSA_KEYS * 1000);
      updateFd(ssl_maintenance_timer.getFileDescriptor(),
               EVENT_TYPE::READ_ONESHOT, EVENT_GROUP::MAINTENANCE);
    }
#if MALLOC_TRIM_TIMER
    if (fd == timer_internal_maintenance.getFileDescriptor()) {
      // release memory back to the system
      ::malloc_trim(0);
      timer_internal_maintenance.set(MALLOC_TRIM_TIMER_INTERVAL * 1000);
      updateFd(timer_internal_maintenance.getFileDescriptor(), EVENT_TYPE::READ_ONESHOT, EVENT_GROUP::MAINTENANCE);
    }
#endif
    return;
  } else if (event_group == EVENT_GROUP::SIGNAL && fd == signal_fd.getFileDescriptor()) {
    Logger::logmsg(LOG_DEBUG, "Received singal %x", signal_fd.getSignal());
    if (signal_fd.getSignal() == SIGTERM) {
//      stop();
//      exit(EXIT_SUCCESS);
    }
    return;
  }
}

std::string ListenerManager::handleTask(ctl::CtlTask &task) {
  if (!isHandler(task)) return JSON_OP_RESULT::ERROR;

  if (task.command == ctl::CTL_COMMAND::EXIT) {
    Logger::logmsg(LOG_REMOVE, "Exit command received");
    is_running = false;
    return JSON_OP_RESULT::OK;
  }

  switch (task.subject) {
    case ctl::CTL_SUBJECT::DEBUG: {
      std::unique_ptr<JsonObject> root{new JsonObject()};
      std::unique_ptr<JsonObject> status{new JsonObject()};
      std::unique_ptr<JsonObject> backends_stats{new JsonObject()};
      std::unique_ptr<JsonObject> clients_stats{new JsonObject()};
      std::unique_ptr<JsonObject> ssl_stats{new JsonObject()};
      std::unique_ptr<JsonObject> events_count{new JsonObject()};
#ifdef CACHE_ENABLED
      std::unique_ptr<JsonObject> cache_count{new JsonObject()};
#endif
      status->emplace("ClientConnection",
                      std::make_unique<JsonDataValue>(Counter<ClientConnection>::count));
      status->emplace("BackendConnection",
                      std::make_unique<JsonDataValue>(Counter<BackendConnection>::count));
      status->emplace("HttpStream", std::make_unique<JsonDataValue>(Counter<HttpStream>::count));
      // root->emplace(JSON_KEYS::DEBUG, std::unique_ptr<JsonDataValue>(new
      // JsonDataValue(Counter<HttpStream>)));
      double vm, rss;
      SystemInfo::getMemoryUsed(vm, rss);
      status->emplace("VM", std::make_unique<JsonDataValue>(vm));
      status->emplace("RSS", std::make_unique<JsonDataValue>(rss));
      root->emplace("status", std::move(status));
#if DEBUG_STREAM_EVENTS_COUNT

      clients_stats->emplace("on_client_connect", std::unique_ptr<JsonDataValue>(
                                                      new JsonDataValue(Counter<debug__::on_client_connect>::count)));
      backends_stats->emplace(
          "on_backend_connect",
          std::unique_ptr<JsonDataValue>(new JsonDataValue(Counter<debug__::on_backend_connect>::count)));
      backends_stats->emplace(
          "on_backend_connect_timeout",
          std::unique_ptr<JsonDataValue>(new JsonDataValue(Counter<debug__::on_backend_connect_timeout>::count)));
      ssl_stats->emplace("on_handshake",
                         std::unique_ptr<JsonDataValue>(new JsonDataValue(Counter<debug__::on_handshake>::count)));
      clients_stats->emplace("on_request",
                             std::unique_ptr<JsonDataValue>(new JsonDataValue(Counter<debug__::on_request>::count)));
      backends_stats->emplace("on_response",
                              std::unique_ptr<JsonDataValue>(new JsonDataValue(Counter<debug__::on_response>::count)));
      clients_stats->emplace("on_request_timeout", std::unique_ptr<JsonDataValue>(
                                                       new JsonDataValue(Counter<debug__::on_request_timeout>::count)));
      backends_stats->emplace(
          "on_response_timeout",
          std::unique_ptr<JsonDataValue>(new JsonDataValue(Counter<debug__::on_response_timeout>::count)));
      backends_stats->emplace("on_send_request", std::unique_ptr<JsonDataValue>(
                                                     new JsonDataValue(Counter<debug__::on_send_request>::count)));
      clients_stats->emplace("on_send_response", std::unique_ptr<JsonDataValue>(
                                                     new JsonDataValue(Counter<debug__::on_send_response>::count)));
      clients_stats->emplace(
          "on_client_disconnect",
          std::unique_ptr<JsonDataValue>(new JsonDataValue(Counter<debug__::on_client_disconnect>::count)));
      backends_stats->emplace(
          "on_backend_disconnect",
          std::unique_ptr<JsonDataValue>(new JsonDataValue(Counter<debug__::on_backend_disconnect>::count)));

      events_count->emplace(
          "client_read", std::unique_ptr<JsonDataValue>(new JsonDataValue(Counter<debug__::event_client_read>::count)));
      events_count->emplace("client_write", std::unique_ptr<JsonDataValue>(
                                                new JsonDataValue(Counter<debug__::event_client_write>::count)));
      events_count->emplace(
          "client_disconnect",
          std::unique_ptr<JsonDataValue>(new JsonDataValue(Counter<debug__::event_client_disconnect>::count)));
      events_count->emplace("backend_read", std::unique_ptr<JsonDataValue>(
                                                new JsonDataValue(Counter<debug__::event_backend_read>::count)));
      events_count->emplace("backend_write", std::unique_ptr<JsonDataValue>(
                                                 new JsonDataValue(Counter<debug__::event_backend_write>::count)));
      events_count->emplace(
          "backend_disconnect",
          std::unique_ptr<JsonDataValue>(new JsonDataValue(Counter<debug__::event_backend_disconnect>::count)));

      events_count->emplace("event_connect",
                            std::unique_ptr<JsonDataValue>(new JsonDataValue(Counter<debug__::event_connect>::count)));
      events_count->emplace(
          "event_connect_failed",
          std::unique_ptr<JsonDataValue>(new JsonDataValue(Counter<debug__::event_connect_fail>::count)));
#ifdef CACHE_ENABLED
#if MEMCACHED_ENABLED == 1
      RamICacheStorage *ram_storage = MemcachedStorage::getInstance();
#else
      RamICacheStorage *ram_storage = RamfsCacheStorage::getInstance();
#endif
      DiskICacheStorage *disk_storage = DiskCacheStorage::getInstance();

      int ram_free = (ram_storage->max_size - ram_storage->current_size);
      int ram_used = (ram_storage->current_size);
      int disk_used = (disk_storage->current_size);

      cache_count->emplace(
          "cache_hit", std::unique_ptr<JsonDataValue>(new JsonDataValue(Counter<cache_stats__::cache_match>::count)));
      cache_count->emplace(
          "cache_ram_entries",
          std::unique_ptr<JsonDataValue>(new JsonDataValue(Counter<cache_stats__::cache_RAM_entries>::count)));
      cache_count->emplace(
          "cache_disk_entries",
          std::unique_ptr<JsonDataValue>(new JsonDataValue(Counter<cache_stats__::cache_DISK_entries>::count)));
      cache_count->emplace("cache_staled", std::unique_ptr<JsonDataValue>(
                                               new JsonDataValue(Counter<cache_stats__::cache_staled_entries>::count)));
      cache_count->emplace(
          "cache_miss", std::unique_ptr<JsonDataValue>(new JsonDataValue(Counter<cache_stats__::cache_miss>::count)));
      cache_count->emplace("cache_ram_free", std::unique_ptr<JsonDataValue>(new JsonDataValue(ram_free)));
      cache_count->emplace("cache_ram_usage", std::unique_ptr<JsonDataValue>(new JsonDataValue(ram_used)));
      cache_count->emplace("cache_disk_usage", std::unique_ptr<JsonDataValue>(new JsonDataValue(disk_used)));
      cache_count->emplace("cache_ram_mountpoint",
                           std::unique_ptr<JsonDataValue>(new JsonDataValue(ram_storage->mount_path)));
      cache_count->emplace("cache_disk_mountpoint",
                           std::unique_ptr<JsonDataValue>(new JsonDataValue(disk_storage->mount_path)));
      cache_count->emplace(
          "cache_responses_not_stored",
          std::unique_ptr<JsonDataValue>(new JsonDataValue(Counter<cache_stats__::cache_not_stored>::count)));
      root->emplace("cache", std::move(cache_count));
#endif
      root->emplace("events", std::move(events_count));
      root->emplace("backends", std::move(backends_stats));
      root->emplace("clients", std::move(clients_stats));
      root->emplace("ssl", std::move(ssl_stats));

#if ENABLE_SSL_SESSION_CACHING
      root->emplace("SESSION list size", std::unique_ptr<JsonDataValue>(new JsonDataValue(static_cast<int>(
                                             ssl::SslSessionManager::getInstance()->sessions.size()))));
#endif
#endif

      /*
  struct debug_status{};
  struct on_none:debug_status, Counter<on_none>{};
  struct on_connect:debug_status, Counter<on_connect>{};
  struct on_backend_connect:debug_status, Counter<on_backend_connect>{};
  struct on_backend_disconnect:debug_status, Counter<on_backend_disconnect>{};
  struct on_connect_timeout:debug_status, Counter<on_connect_timeout>{};
  struct on_handshake: debug_status, Counter<on_handshake>{};
  struct on_request:debug_status, Counter<on_request>{};
  struct on_response:debug_status, Counter<on_response>{};
  struct on_request_timeout:debug_status, Counter<on_request_timeout>{};
  struct on_response_timeout:debug_status, Counter<on_response_timeout>{};
  struct on_send_request:debug_status, Counter<on_send_request>{};
  struct on_send_response:debug_status, Counter<on_send_response>{};
  struct on_client_disconnect:debug_status, Counter<on_client_disconnect>{};*/

      return root->stringify();
    }
    default: {
      return JSON_OP_RESULT::ERROR;
    }
  }
}

bool ListenerManager::isHandler(ctl::CtlTask &task) {
  return (task.target == ctl::CTL_HANDLER_TYPE::LISTENER || task.target == ctl::CTL_HANDLER_TYPE::ALL);
}

ListenerManager::ListenerManager() : is_running(false), stream_manager_set() {}

ListenerManager::~ListenerManager() {
  Logger::logmsg(LOG_REMOVE, "Destructor");
  is_running = false;
  for (auto &sm : stream_manager_set) {
    sm.second->stop();
    delete sm.second;
  }
#ifdef ENABLE_HEAP_PROFILE
  HeapProfilerDump("Heap profile data");
  HeapProfilerStop();
#endif
}

void ListenerManager::doWork() {
  while (is_running) {
    if (loopOnce(EPOLL_WAIT_TIMEOUT) <= 0) {
      // something bad happend
      //      Logger::LogInfo("No event received");
    }
  }
  Logger::logmsg(LOG_REMOVE, "Exiting loop");
}

void ListenerManager::stop() {
  is_running = false;
  if (worker_thread.joinable()) worker_thread.join();
  ctl::ControlManager::getInstance()->deAttach(std::ref(*this));
}

void ListenerManager::start() {
  auto cm = ctl::ControlManager::getInstance();
  cm->attach(std::ref(*this));
  auto concurrency_level = std::thread::hardware_concurrency() < 2
                               ? 2
                               : std::thread::hardware_concurrency();
  auto num_threads = global::run_options::getCurrent().num_threads != 0
                         ? global::run_options::getCurrent().num_threads
                         : concurrency_level;
  for (int sm = 0; sm < num_threads; sm++) {
    stream_manager_set[sm] = new StreamManager();
  }
  int service_id = 0;
  for(const auto& listener_config_item : listener_config_set) {
    for (auto service_config = listener_config_item->services;
         service_config != nullptr; service_config = service_config->next) {
      if (!service_config->disabled) {
        ServiceManager::getInstance(*listener_config_item)
            ->addService(*service_config, service_id++);
      } else {
        Logger::logmsg(LOG_NOTICE,
                       " (%s) service %s disabled in config file ",
                       listener_config_item->name.data(),
                       service_config->name.data());
      }
    }
  }
#ifdef ENABLE_HEAP_PROFILE
  HeapProfilerStart("/tmp/zproxy");
#endif
  is_running = true;
  for (int i = 0; i < stream_manager_set.size(); i++) {
    auto sm = stream_manager_set[i];
    if (sm != nullptr) {
      for (auto &listener_config : listener_config_set) {
        if (!sm->registerListener(listener_config)) {
          Logger::logmsg(LOG_ERR,
                         "Error initializing StreamManager for farm %s",
                         listener_config->name.data());
          exit(EXIT_FAILURE);
        }
      }
      sm->start(i);
    } else {
      Logger::logmsg(LOG_ERR, "StreamManager id: %d doesn't exist  ", i);
    }
  }
  //  signal_fd.init();
  auto alive_to = global::run_options::getCurrent().backend_resurrect_timeout;
  timer_maintenance.set(
      (alive_to > 0 ? alive_to : DEFAULT_MAINTENANCE_INTERVAL) * 1000);
  //  addFd(signal_fd.getFileDescriptor(), EVENT_TYPE::READ,
  //  EVENT_GROUP::SIGNAL);
  addFd(timer_maintenance.getFileDescriptor(), EVENT_TYPE::READ_ONESHOT, EVENT_GROUP::MAINTENANCE);
  ssl_maintenance_timer.set(T_RSA_KEYS * 1000);
  addFd(ssl_maintenance_timer.getFileDescriptor(), EVENT_TYPE::READ_ONESHOT,
        EVENT_GROUP::MAINTENANCE);
#if MALLOC_TRIM_TIMER
  timer_internal_maintenance.set(MALLOC_TRIM_TIMER_INTERVAL * 1000);
  addFd(timer_internal_maintenance.getFileDescriptor(), EVENT_TYPE::READ_ONESHOT, EVENT_GROUP::MAINTENANCE);
#endif
  //  helper::ThreadHelper::setThreadAffinity(
  //      0, pthread_self());  // worker_thread.native_handle());
  helper::ThreadHelper::setThreadName("LISTENER", pthread_self());
  doWork();
}

StreamManager *ListenerManager::getManager(int fd) {
  static unsigned long c;
  ++c;
  unsigned long id = c % stream_manager_set.size();
  return stream_manager_set[id];
}

bool Listener::init(std::shared_ptr<ListenerConfig> config) {
#if WAF_ENABLED
  config->modsec = std::make_shared<modsecurity::ModSecurity>();
  config->modsec->setConnectorInformation(
      "zproxy_" + config->name + "_connector");
  config->modsec->setServerLogCb(Waf::logModsec);
#endif
  listener_config_set.push_back(std::move(config));
  return true;
}
