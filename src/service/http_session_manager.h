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
#pragma once
#include <chrono>
#include <string>
#include <unordered_map>
#include "../http/http_stream.h"
#include "../json/json_data_value.h"

using namespace std::chrono;

namespace sessions {

enum HttpSessionType {
  SESS_NONE,
  SESS_IP,
  SESS_COOKIE,
  SESS_URL,
  SESS_PARM,
  SESS_HEADER,
  SESS_BASIC
};

typedef std::chrono::duration<long double> SessionDurationSeconds;

struct SessionInfo {
  SessionInfo() : last_seen(system_clock::now()), assigned_backend(nullptr) {}
  system_clock::time_point last_seen;
  Backend *assigned_backend{nullptr};
  bool hasExpired(unsigned int ttl) {
    SessionDurationSeconds time_span(system_clock::now() - last_seen);
    // check if has not reached ttl
    return time_span.count() > ttl;
  }
  void update() { last_seen = system_clock::now(); }
  long getTimeStamp() {
    return std::chrono::duration_cast<std::chrono::seconds>(
               last_seen.time_since_epoch())
        .count();
  }
  void setTimeStamp(long seconds_since_epoch_count) {
    std::chrono::seconds dur(seconds_since_epoch_count);
    std::chrono::time_point<std::chrono::system_clock> dt(dur);
    last_seen = dt;
  }
};

class HttpSessionManager {
  // used
  std::mutex lock_mtx;
  std::unordered_map<std::string, SessionInfo *>
      sessions_set;  // key can be anything, depending on the session type
 protected:
  HttpSessionType session_type;
  std::string sess_id;  /* id to construct the pattern */
  regex_t sess_start{}; /* pattern to identify the session data */
  regex_t sess_pat{};   /* pattern to match the session data */

 public:
  unsigned int ttl{};
  HttpSessionManager();
  virtual ~HttpSessionManager();
  // may exist, so which one is going to release
  // the map resources!!
  // return the created SessionInfo
  // must check if it already exist !!!
  bool addSession(JsonObject *json_object, std::vector<Backend *> backend_set);
  SessionInfo *addSession(HttpStream &stream, Backend &backend_to_assign);
  bool deleteSessionByKey(const std::string& key);
  bool deleteSession(const JsonObject &json_object);
  void deleteSession(HttpStream &stream);
  // return the assigned backend or nullptr if no session is found or sesssion
  // has expired
  SessionInfo *getSession(HttpStream &stream, bool update_if_exist = false);
  std::unique_ptr<json::JsonArray> getSessionsJson();
  void deleteBackendSessions(int backend_id);
  void doMaintenance();

 private:
  static std::string getQueryParameter(const std::string &url,
                                       const std::string &sess_id);
  static std::string getCookieValue(const std::string &cookie_header_value,
                                    std::string_view sess_id);
  static std::string getUrlParameter(const std::string &url);
  std::string getSessionKey(HttpStream &stream);
};
}  // namespace sessions
