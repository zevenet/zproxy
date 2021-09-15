#pragma once

#include "../http/http_stream.h"
#include "../service/service.h"

struct StreamDataLogger {
	static std::string logTag(HttpStream *stream, const char *tag);
	static void logTransaction(HttpStream &stream);
};
