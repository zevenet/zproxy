//
// Created by abdess on 10/2/18.
//

#pragma once
#include <string>
#include "../http/HttpRequest.h"

namespace ctl {

enum class CTL_COMMAND {
	NONE,
	ADD,
	DELETE,
	ENABLE,
	DISABLE,
	UPDATE,
	GET,
	SUSCRIBE,
    UNSUSCRIBE,
};

enum class CTL_HANDLER_TYPE {
	NONE,
	LISTENER,
	BACKEND,
	SERVICE,
	SERVICE_MANAGER,
	GLOBAL_CONF,
	STREAM_MANAGER,
    ENVIRONMENT,
#if CACHE_ENABLED
    CACHE
#endif
};

enum class CTL_SUBJECT {
	NONE,
	SESSION,
	BACKEND,
	SERVICE,
	LISTENER,
	CONFIG,
	STATUS,
	WEIGHT,
	DEBUG,
	S_BACKEND,
#if CACHE_ENABLED
    CACHE,
#endif
};

struct CtlTask {
	HttpRequest* request;
	CTL_COMMAND command = CTL_COMMAND::NONE;
	CTL_HANDLER_TYPE target = CTL_HANDLER_TYPE::NONE;
	CTL_SUBJECT subject = CTL_SUBJECT::NONE;

	int listener_id = -1;
	int service_id = -1;
	int backend_id = -1;

	std::string target_subject_id = "";

	std::string service_name;
	std::string backend_name;
	std::string data;
};

enum class CTL_INTERFACE_MODE {
	CTL_UNIX,
	CTL_AF_INET,
	CTL_NONE,
};

}  // namespace ctl
