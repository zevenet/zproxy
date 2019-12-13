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

#include "json.h"
#include <sstream>

namespace json {
// JSON_OP_RESULT
const std::string JSON_OP_RESULT::OK = "{\"result\":\"ok\"}";
const std::string JSON_OP_RESULT::ERROR = "{\"result\":\"error\"}";
const std::string JSON_OP_RESULT::WRONG_JSON_FORMAT = "{\"result\":\"error\",\"description\":\"wrong json format\"}";
const std::string JSON_OP_RESULT::EMPTY_OBJECT = "{}";
const std::string JSON_OP_RESULT::NONE = "";

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
const std::string JSON_KEYS::TYPE = "type";
#if WAF_ENABLED
const std::string JSON_KEYS::WAF = "waf";
#endif

const std::string JSON_KEYS::RESULT = "result";
const std::string JSON_KEYS::DEBUG = "debug";
const std::string JSON_KEYS::DEBUG1 = "debug1";
const std::string JSON_KEYS::DEBUG2 = "debug2";
const std::string JSON_KEYS::DEBUG3 = "debug3";
const std::string JSON_KEYS::DEBUG4 = "debug4";
const std::string JSON_KEYS::DEBUG5 = "debug5";

#ifdef CACHE_ENABLED
const std::string JSON_KEYS::CACHE = "cache";
const std::string JSON_KEYS::CACHE_MISS = "misses";
const std::string JSON_KEYS::CACHE_HIT = "matches";
const std::string JSON_KEYS::CACHE_STALE = "staled-entries";
const std::string JSON_KEYS::CACHE_RAM = "ram-cached-response";
const std::string JSON_KEYS::CACHE_RAM_USAGE = "ram-usage";
const std::string JSON_KEYS::CACHE_RAM_PATH = "ram-path";
const std::string JSON_KEYS::CACHE_DISK = "disk-cached-response";
const std::string JSON_KEYS::CACHE_DISK_USAGE = "disk-usage";
const std::string JSON_KEYS::CACHE_DISK_PATH = "disk-path";
const std::string JSON_KEYS::CACHE_AVOIDED = "not-stored";
const std::string JSON_KEYS::CACHE_CONTENT = "cache-content";
#endif
}  // namespace json

json::Json::~Json() {}

bool json::Json::isArray() { return false; }
