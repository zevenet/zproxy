#include "backend.h"

Backend::Backend() {
  ctl::ControlManager::getInstance()->attach(std::ref(*this));
}

Backend::~Backend() {
  ctl::ControlManager::getInstance()->deAttach(std::ref(*this));
}

std::string Backend::handleTask(ctl::CtlTask& task) {
  Debug::logmsg(LOG_DEBUG, "backend handling task");
  return "{id:" + std::to_string(backen_id) + ";type:backend}";
}
bool Backend::isHandler(ctl::CtlTask& task) {
  return task.target == ctl::CTL_BACKEND;
}
