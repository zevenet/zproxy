//
// Created by abdess on 10/4/18.
//

#include "json.h"
#include <sstream>

namespace json {
// JSON_OP_RESULT
const std::string JSON_OP_RESULT::OK = "{\"result\":\"ok\"}";
const std::string JSON_OP_RESULT::ERROR = "{\"result\":\"error\"}";
const std::string JSON_OP_RESULT::WRONG_JSON_FORMAT = "{\"result\":\"error\",\"description\":\"wrong json format\"}";

// JSON_KEYS
const std::string JSON_KEYS::LISTENER = "listener";
const std::string JSON_KEYS::SERVICE = "service";
const std::string JSON_KEYS::BACKEND = "backend";
const std::string JSON_KEYS::SESSION = "session";

const std::string JSON_KEYS::SERVICES = "services";
const std::string JSON_KEYS::BACKENDS = "backends";
const std::string JSON_KEYS::SESSIONS = "sessions";
const std::string JSON_KEYS::ID = "id";
const std::string JSON_KEYS::NAME = "name";
const std::string JSON_KEYS::UNKNOWN = "unknown";

const std::string JSON_KEYS::STATUS = "status";
const std::string JSON_KEYS::STATUS_ACTIVE = "active";
const std::string JSON_KEYS::STATUS_UP = "up";

const std::string JSON_KEYS::STATUS_DOWN = "down";
const std::string JSON_KEYS::STATUS_DISABLED = "disabled";
const std::string JSON_KEYS::ADDRESS = "address";
const std::string JSON_KEYS::PORT = "port";
const std::string JSON_KEYS::HTTPS = "https";
const std::string JSON_KEYS::BACKEND_ID = "backend-id";
const std::string JSON_KEYS::FROM = "from";
const std::string JSON_KEYS::TO = "to";
const std::string JSON_KEYS::LAST_SEEN_TS = "last-seen";
const std::string JSON_KEYS::CONNECTIONS = "connections";
const std::string JSON_KEYS::PENDING_CONNS = "pending-connections";
const std::string JSON_KEYS::RESPONSE_TIME = "response-time";
const std::string JSON_KEYS::CONNECT_TIME = "connect-time";
const std::string JSON_KEYS::WEIGHT = "weight";
const std::string JSON_KEYS::CONFIG = "config";

const std::string JSON_KEYS::RESULT = "result";

}  // namespace json

json::Json::~Json() { freeJson(); }

bool json::Json::isArray() { return false; }
