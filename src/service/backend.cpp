#include "backend.h"

Backend::Backend() {
  //  ctl::ControlManager::getInstance()->attach(std::ref(*this));
}

Backend::~Backend() {
  //  ctl::ControlManager::getInstance()->deAttach(std::ref(*this));
}

std::string Backend::handleTask(ctl::CtlTask& task) {
  if (!isHandler(task)) return "";
//  Debug::logmsg(LOG_REMOVE, "Backend %d handling task", backend_id);
  if (task.command == ctl::CTL_COMMAND::GET) {
    switch (task.subject) {
      case ctl::CTL_SUBJECT::STATUS: {
        JsonObject status;
        switch (this->status) {
          case BACKEND_UP:
            status.emplace(JSON_KEYS::STATUS,
                           new JsonDataValue(JSON_KEYS::STATUS_UP));
            break;
          case BACKEND_DOWN:
            status.emplace(JSON_KEYS::STATUS,
                           new JsonDataValue(JSON_KEYS::STATUS_DOWN));
            break;
          case BACKEND_DISABLED:
            status.emplace(JSON_KEYS::STATUS,
                           new JsonDataValue(JSON_KEYS::STATUS_DISABLED));
            break;
          default:
            status.emplace(JSON_KEYS::STATUS,
                           new JsonDataValue(JSON_KEYS::UNKNOWN));
            break;
        }
        return status.stringify();
      }
      case ctl::CTL_SUBJECT::WEIGHT:{
        JsonObject weight;
        weight.emplace(JSON_KEYS::WEIGHT,
                       new JsonDataValue(this->weight));
        return weight.stringify();
      }
      default:
        std::unique_ptr<JsonObject> status(this->getBackendJson());
        if (status.get() != nullptr) return status->stringify();
        return JSON_OP_RESULT::ERROR;
    }
  } else if (task.command == ctl::CTL_COMMAND::UPDATE) {
      std::unique_ptr<JsonObject> status(JsonParser::parse(task.data));
      if (status.get() == nullptr) return JSON_OP_RESULT::ERROR;
    switch (task.subject) {
      case ctl::CTL_SUBJECT::CONFIG:
        // TODO:: update  config (timeouts, headers)
        break;
      case ctl::CTL_SUBJECT::STATUS: {


        if (status->at(JSON_KEYS::STATUS)->isValue()) {
          auto value =
              static_cast<JsonDataValue*>(status->at(JSON_KEYS::STATUS))
                  ->string_value;
          if (value == JSON_KEYS::STATUS_ACTIVE ||
              value == JSON_KEYS::STATUS_UP) {
            this->status = BACKEND_UP;
          } else if (value == JSON_KEYS::STATUS_DOWN) {
            this->status = BACKEND_DOWN;
          } else if (value == JSON_KEYS::STATUS_DISABLED) {
            this->status = BACKEND_DISABLED;
          }
          Debug::logmsg(LOG_NOTICE, "Set Backend %d %s", backend_id,
                        value.c_str());
          //TODO:: Cut mode?
          return JSON_OP_RESULT::OK;
        }
        break;
      }
    case ctl::CTL_SUBJECT::WEIGHT:{
        if (status->at(JSON_KEYS::WEIGHT)->isValue()) {
          auto value =
              static_cast<JsonDataValue*>(status->at(JSON_KEYS::WEIGHT))
                  ->number_value;
          this->weight = value;
          return JSON_OP_RESULT::OK;}
        return JSON_OP_RESULT::ERROR;
        break;
    }
      default:
        break;
    }
  }
  return "";
}

bool Backend::isHandler(ctl::CtlTask& task) {
  return /*task.target == ctl::CTL_HANDLER_TYPE::BACKEND &&*/
      (task.backend_id == this->backend_id || task.backend_id == -1);
}

JsonObject* Backend::getBackendJson() {
  JsonObject* root = new JsonObject();
  // TODO:: Add backend stats info.

  root->emplace(JSON_KEYS::NAME, new JsonDataValue(this->name));
  root->emplace(JSON_KEYS::ID, new JsonDataValue(this->backend_id));
  root->emplace(JSON_KEYS::ADDRESS, new JsonDataValue(this->address));
  root->emplace(JSON_KEYS::PORT, new JsonDataValue(this->port));
  root->emplace(JSON_KEYS::WEIGHT, new JsonDataValue(this->weight));
  switch (this->status) {
    case BACKEND_UP:
      root->emplace(JSON_KEYS::STATUS,
                    new JsonDataValue(JSON_KEYS::STATUS_ACTIVE));
      break;
    case BACKEND_DOWN:
      root->emplace(JSON_KEYS::STATUS,
                    new JsonDataValue(JSON_KEYS::STATUS_DOWN));
      break;
    case BACKEND_DISABLED:
      root->emplace(JSON_KEYS::STATUS,
                    new JsonDataValue(JSON_KEYS::STATUS_DISABLED));
      break;
    default:

      root->emplace(JSON_KEYS::STATUS, new JsonDataValue(JSON_KEYS::UNKNOWN));
      break;
  }
  root->emplace(JSON_KEYS::CONNECTIONS, new JsonDataValue(this->established_conn));
  root->emplace(JSON_KEYS::PENDING_CONNS, new JsonDataValue(this->pending_connections));
  root->emplace(JSON_KEYS::RESPONSE_TIME, new JsonDataValue(this->avg_response_time));
  root->emplace(JSON_KEYS::CONNECT_TIME, new JsonDataValue(this->avg_conn_time));

  return root;
}

void Backend::doMaintenance() {
  Connection checkOut;
  if (checkOut.doConnect(*address_info, 0) != IO::IO_OP::OP_SUCCESS) {
    this->status = BACKEND_STATUS::BACKEND_DOWN;
    checkOut.closeConnection();
  }
  return;
}
