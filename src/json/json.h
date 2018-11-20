//
// Created by abdess on 10/4/18.
//
#pragma once

#include <string>
#include <vector>
namespace json {
// JSON Keys

struct JSON_OP_RESULT {
  static const std::string OK;
  static const std::string ERROR;
  static const std::string WRONG_JSON_FORMAT;
};

struct JSON_KEYS {
  static const std::string LISTENER;
  static const std::string SERVICE;
  static const std::string BACKEND;
  static const std::string SESSION;

  static const std::string SERVICES;
  static const std::string BACKENDS;
  static const std::string SESSIONS;

  static const std::string ID;
  static const std::string NAME;
  static const std::string UNKNOWN;

  static const std::string STATUS;
  static const std::string STATUS_ACTIVE;
  static const std::string STATUS_UP;
  static const std::string STATUS_DOWN;
  static const std::string STATUS_DISABLED;

  static const std::string ADDRESS;
  static const std::string PORT;
  static const std::string BACKEND_ID;
  static const std::string FROM;
  static const std::string TO;
  static const std::string LAST_SEEN_TS;
  static const std::string CONNECTIONS;
  static const std::string PENDING_CONNS;
  static const std::string RESPONSE_TIME;
  static const std::string CONNECT_TIME;
  static const std::string WEIGHT;
  static const std::string CONFIG;
};

enum class JSON_VALUE_TYPE {
  JSON_T_NULL,
  JSON_T_STRING,
  JSON_T_BOOL,
  JSON_T_NUMBER,
  JSON_T_DOUBLE,
  JSON_T_OBJECT,
  JSON_T_ARRAY
};

class Json {
public:
  Json() = default;
  virtual ~Json();
  int json_size;
  virtual bool isArray();
  virtual bool isObject() { return false; }
  virtual bool isData() { return false; }
  virtual bool isValue() { return false; }
  virtual std::string stringify(bool prettyfy = false, int tabs = -1) {
    return std::string();
  }
  virtual void freeJson() {}
};

} // namespace json
