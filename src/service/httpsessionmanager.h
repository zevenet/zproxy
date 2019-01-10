#pragma once
#include <chrono>
#include <string>
#include "../http/http_stream.h"
#include "../json/JsonDataValue.h"
#include <unordered_map>

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
  Backend *assigned_backend;
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
protected:
  HttpSessionType session_type;
  std::string sess_id; /* id to construct the pattern */
  regex_t sess_start; /* pattern to identify the session data */
  regex_t sess_pat;   /* pattern to match the session data */

public:
  unsigned int ttl;
  static std::mutex lock_mtx;
  std::unordered_map<std::string, SessionInfo *>
      sessions_set;  // key can be anything, deppending on the type of session
  HttpSessionManager();
  ~HttpSessionManager();
  // may exist, so which one is going to release
  // the map resources!!
  // return the created SessionInfo
  // must check if it already exist !!!
  bool addSession(JsonObject *json_object, std::vector<Backend *> backend_set);
  SessionInfo *addSession(HttpStream &stream, Backend &backend_to_assign);

  bool deleteSession(const JsonObject &json_object, std::vector<Backend *> backend_set);
  void deleteSession(HttpStream &stream);
  // return the assigned backend or nullptr if no session is found or sesssion
  // has expired
  SessionInfo *getSession(HttpStream &stream, bool update_if_exist = false);
  std::unique_ptr<json::JsonArray> getSessionsJson();
};
}  // namespace sessions
