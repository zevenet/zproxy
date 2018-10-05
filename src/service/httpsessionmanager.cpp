#include "httpsessionmanager.h"

using namespace sessions;

std::unordered_map<std::string, SessionInfo *> HttpSessionManager::sessions_set;
std::mutex HttpSessionManager::lock_mtx;

HttpSessionManager::HttpSessionManager() : session_type(SESS_NONE) {}

HttpSessionManager::~HttpSessionManager() {
  for (auto &session : sessions_set) {
    delete session.second;
  }
}

SessionInfo *HttpSessionManager::addSession(HttpStream &stream,
                                            Backend &backend_to_assign) {
  if (this->session_type == sessions::SESS_NONE) return nullptr;
  // TODO::Implement

  std::string key("");
  switch (this->session_type) {
    case SESS_NONE:
      return nullptr;
    case SESS_IP: {
      key = stream.client_connection.getPeerAddress();
      break;
    }
      // TODO:: to Implement
    case SESS_COOKIE:
      break;
    case SESS_URL:
      break;
    case SESS_PARM:
      break;
    case SESS_HEADER:
      break;
    case SESS_BASIC:
      break;
  }
  // check if we have a new key to insert,
  if (!key.empty()) {
    auto new_session = new SessionInfo();
    new_session->assigned_backend = &backend_to_assign;
    std::lock_guard<std::mutex> locker(lock_mtx);
    sessions_set.insert({key, new_session});
    return new_session;
  }
  return nullptr;
}

void HttpSessionManager::deleteSession(HttpStream &stream) {
  std::lock_guard<std::mutex> locker(lock_mtx);
  auto ip_address = stream.client_connection.getPeerAddress();
  SessionInfo *session = nullptr;
  if ((session = sessions_set[ip_address]) != nullptr) {
    // we have a stored session
    delete session;
    if (sessions_set.erase(ip_address) < 1) {
      Debug::logmsg(LOG_DEBUG, "No session to delete for %s",
                    ip_address.c_str());
    }
  }
}

SessionInfo *HttpSessionManager::getSession(HttpStream &stream,
                                            bool update_if_exist) {
  std::string session_key("");
  SessionInfo *session = nullptr;
  switch (session_type) {
    case sessions::SESS_NONE:
      return nullptr;
    case sessions::SESS_IP: {
      session_key = stream.client_connection.getPeerAddress();
      // TODO::This must change !! no try catch !!!
      // sessions_set[ip_address];
      try {
        session = this->sessions_set.at(session_key);
      } catch (std::exception ex) {
        Debug::logmsg(LOG_REMOVE, "Something went wrong with the set");
        return nullptr;
      }
      break;
    }
    case sessions::SESS_URL:
      break;
    case sessions::SESS_PARM:
      break;
    default: {  // For SESS_BASIC, SESS_HEADER and SESS_COOKIE
      break;
    }
  }
  if (session != nullptr) {
    // we have a stored session, check if it has not expired.
    if (!session->hasExpired(this->ttl)) {
      if (update_if_exist) session->update();
      return session;
    } else {
      // TODO::free session info ?? maybe  not and avoid reallocation of new
      // SessionInfo struct
      if (!update_if_exist) {
        sessions_set.erase(session_key);
        delete session;
      }
    }
  }

  return nullptr;
}
