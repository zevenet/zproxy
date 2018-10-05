#pragma once
#include <chrono>
#include <string>
#include "../http/http_stream.h"

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

struct SessionInfo {
  SessionInfo() : last_seen(steady_clock::now()), assigned_backend(nullptr) {}
  steady_clock::time_point last_seen;
  Backend *assigned_backend;
  bool hasExpired(unsigned int ttl) {
    duration<double> time_span =
        duration_cast<duration<double>>(steady_clock::now() - last_seen);

    // check if has not reached ttl
    return time_span.count() > ttl;
  }
  void update() { last_seen = steady_clock::now(); }
};

class HttpSessionManager {
  // used

 protected:
  HttpSessionType session_type;
  unsigned int ttl;
  std::string sessions_id;
  regex_t sess_start; /* pattern to identify the session data */
  regex_t sess_pat;   /* pattern to match the session data */

 public:
  static std::mutex lock_mtx;
  static std::unordered_map<std::string, SessionInfo *>
      sessions_set;  // key can be anything, deppending on the type of session
  HttpSessionManager();
  virtual ~HttpSessionManager();  // TODO:: WARNING, multiple derived clasess
  // may exist, so which one is going to release
  // the map resources!!
  // return the created SessionInfo
  // must check if it already exist !!!
  SessionInfo *addSession(HttpStream &stream, Backend &backend_to_assign);

  void deleteSession(HttpStream &stream);
  // return the assigned backend or nullptr if no session is found or sesssion
  // has expired
  SessionInfo *getSession(HttpStream &stream, bool update_if_exist = false);
};

}  // namespace sessions
