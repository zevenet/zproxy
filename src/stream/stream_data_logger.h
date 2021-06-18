#pragma once

#include "../http/http_stream.h"
#include "../service/service.h"

struct StreamDataLogger {
	static void logTransaction(HttpStream &stream);
};
