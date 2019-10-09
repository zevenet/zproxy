#pragma once

#include "../debug/logger.h"
#include "../http/http_stream.h"
#include "../service/service.h"

struct StreamDataLogger {
  static void setLogData(HttpStream *stream, ListenerConfig &listener_config);
  StreamDataLogger(HttpStream *stream, ListenerConfig &listener_config) { setLogData(stream, listener_config); }
  static void logTransaction(HttpStream &stream);
  static void resetLogData();
  ~StreamDataLogger();
};


