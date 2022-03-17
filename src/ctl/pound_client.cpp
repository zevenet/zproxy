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
#include "pound_client.h"
#include "../service/backend.h"
#include "../../zcutils/zcu_network.h"
#include "../../zcutils/zcutils.h"

class Timer {
	std::thread th;
	bool running = false;

    public:
	void start(int timeout_sec)
	{
		std::chrono::milliseconds interval =
			std::chrono::milliseconds(CTL_TO_INTERVAL);
		running = true;

		th = std::thread([=]() {
			int milliseconds = timeout_sec * 1000;

			while (running && milliseconds > 0) {
				std::this_thread::sleep_for(interval);
				milliseconds -= CTL_TO_INTERVAL;
			}

			if (running) {
				zcu_log_print(
					LOG_ERR,
					"Error: zproxyctl reached the timeout %d",
					timeout_sec);
				exit(EXIT_FAILURE);
			}
		});
	}

	void stop()
	{
		running = false;
		th.join();
	}
};

bool PoundClient::trySetTargetId(int &target_id, char *possible_value)
{
	if (possible_value) // throw error and show help
		target_id = std::atoi(possible_value);
	else
		return false;
	return true;
}

void PoundClient::trySetAllTargetId(char *argv[], int &option_index)
{
	int to_consume = 1;
	// workaround for listeners
	if (CTL_SUBJECT::LISTENER == ctl_command_subject)
		to_consume = 0;

	int next_index = option_index + to_consume;
	switch (ctl_command_subject) { /*Intentional fallthrough */
	case CTL_SUBJECT::SESSION:
		if (ctl_command == CTL_ACTION::ADD_SESSION) {
			to_consume++;
			next_index++;
		}
	case CTL_SUBJECT::BACKEND: {
		next_index++;
		if (ctl_command != CTL_ACTION::DELETE_SESSION &&
		    !trySetTargetId(this->backend_id, argv[next_index--]))
			showHelp("no valid backend id found");

		if (ctl_command == CTL_ACTION::ADD_SESSION ||
		    ctl_command == CTL_ACTION::DELETE_SESSION) {
			if (!argv[option_index])
				showHelp("no valid session key found");
			session_key = std::string(argv[next_index--]);
			if (session_key.empty())
				showHelp("no valid session key found");
		}
	}
	case CTL_SUBJECT::SERVICE:
		if (!trySetTargetId(this->service_id, argv[next_index--]))
			showHelp("no valid service id found");
	case CTL_SUBJECT::LISTENER:
		if (trySetTargetId(this->listener_id, argv[next_index--])) {
			option_index += to_consume;
			break;
		}
	default:
		showHelp("target id list error");
	}
}

void PoundClient::showHelp(const std::string error, bool exit_on_error)
{
	if (!error.empty())
		std::cout << "ERROR: " << error << std::endl;
	std::cout << "Usage: " << std::endl;
	std::cout << "\tProxy control interface in:\n\t\tLocal mode:\t"
		  << binary_name
		  << " [-t <timeout>] -c /control/socket [ -X ] cmd"
		  << std::endl;
	std::cout << "\t\tTCP mode:\t" << binary_name
		  << " [-t <timeout>] -a IP:PORT [ -X ] cmd\n"
		  << std::endl;
	std::cout << "\twhere cmd is one of:" << std::endl;
	std::cout << "\t-L n - enable listener n" << std::endl;
	std::cout << "\t-l n - disable listener n" << std::endl;
	std::cout << "\t-R n - reload the listener configuration from file"
		  << std::endl;
	std::cout << "\t-S n m - enable service m in listener n (use -1 for "
		     "global services)"
		  << std::endl;
	std::cout << "\t-s n m - disable service m in listener n (use -1 for "
		     "global services)"
		  << std::endl;
	std::cout << "\t-B n m r - enable back-end r in service m in listener n"
		  << std::endl;
	std::cout
		<< "\t-b n m r - disable back-end r in service m in listener n"
		<< std::endl;
	std::cout
		<< "\t-f n m r - flush all sessions for back-end r in service m "
		   "in listener n"
		<< std::endl;
	std::cout
		<< "\t-N n m k r - add a session with key k and back-end r in "
		   "service m in listener n"
		<< std::endl;
	std::cout
		<< "\t-n n m k - remove a session with key k r in service m in "
		   "listener n"
		<< std::endl;
	std::cout << "" << std::endl;
	std::cout
		<< "\tentering the command without arguments lists the current "
		   "configuration."
		<< std::endl;
	std::cout << "\tthe -X flag results in XML output." << std::endl;
	std::cout
		<< "\tthe -H flag shows symbolic host names instead of addresses."
		<< std::endl;
	std::cout << "\tthe -v flag enable verbose mode to STDOUT" << std::endl;
	if (exit_on_error)
		exit(EXIT_FAILURE);
}

bool PoundClient::executeCommand()
{
	Connection client;
	switch (interface_mode) {
	case CTL_INTERFACE_MODE::CTL_NONE: {
		// Lanzar error: "No se ha especificado metodo de conexion"
		showHelp("Unspecified connection method.");
	}
	case CTL_INTERFACE_MODE::CTL_AF_INET: {
		int port;
		size_t pos = this->address.rfind(':');
		if (pos == std::string::npos)
			return false;
		port = std::stoi(this->address.substr(
			pos + 1, this->address.size() - pos));
		this->address = this->address.substr(0, pos);
		client.address =
			zcu_net_get_address(this->address, port).release();
		IO::IO_OP res_connect =
			client.doConnect(*client.address, 0, false);
		if (res_connect != IO::IO_OP::OP_SUCCESS)
			showError("Error: TCP mode connection failed.");
		break;
	}
	default: {
		auto res = client.doConnect(control_socket, 0);
		if (res != IO::IO_OP::OP_SUCCESS) {
			showError("Error: local connection failed.");
		}
	}
	}

	json::JsonObject json_object;
	std::string buffer;
	std::string path = "/listener/" + std::to_string(listener_id);
	http::REQUEST_METHOD method = http::REQUEST_METHOD::NONE;
	if (ctl_command == CTL_ACTION::ENABLE ||
	    ctl_command == CTL_ACTION::DISABLE) {
		json_object.emplace(
			json::JSON_KEYS::STATUS,
			std::unique_ptr<
				json::JsonDataValue>(new json::JsonDataValue(
				ctl_command == CTL_ACTION::ENABLE ?
					json::JSON_KEYS::STATUS_ACTIVE :
					      json::JSON_KEYS::STATUS_DISABLED)));
		method = http::REQUEST_METHOD::PATCH;
		switch (ctl_command_subject) {
		case CTL_SUBJECT::LISTENER: {
			path += "/status";
			break;
		}
		case CTL_SUBJECT::SERVICE: {
			path += "/service/" + std::to_string(service_id) +
				"/status";
			break;
		}
		case CTL_SUBJECT::BACKEND: {
			path += "/service/" + std::to_string(service_id) +
				"/backend/" + std::to_string(backend_id) +
				"/status";
			break;
		}
		default:
			exit(EXIT_FAILURE);
		}
	}
	if (ctl_command == CTL_ACTION::RELOAD) {
		path = "/config";
		method = http::REQUEST_METHOD::UPDATE;
	}
	if (ctl_command_subject == CTL_SUBJECT::SESSION) {
		path += "/service/" + std::to_string(service_id) + "/session/";
		switch (ctl_command) {
		case CTL_ACTION::ADD_SESSION: {
			json_object.emplace(
				json::JSON_KEYS::BACKEND_ID,
				new json::JsonDataValue(this->backend_id));
			json_object.emplace(
				json::JSON_KEYS::ID,
				new json::JsonDataValue(this->session_key));
			method = http::REQUEST_METHOD::PUT;
			break;
		}
		case CTL_ACTION::DELETE_SESSION: {
			json_object.emplace(
				json::JSON_KEYS::ID,
				new json::JsonDataValue(this->session_key));
			method = http::REQUEST_METHOD::DELETE;
			break;
		}
		case CTL_ACTION::FLUSH_SESSIONS: {
			json_object.emplace(
				json::JSON_KEYS::BACKEND_ID,
				new json::JsonDataValue(this->backend_id));
			method = http::REQUEST_METHOD::DELETE;
			break;
		}
		default: {
			exit(EXIT_FAILURE);
		}
		}
	}
	if (method == http::REQUEST_METHOD::NONE) {
		path += "/services";
		method = http::REQUEST_METHOD::GET;
	}
	if (doRequest(method, http::HTTP_VERSION::HTTP_1_0,
		      json_object.stringify(), path, buffer)) {
		verboseLog(buffer);
	}
	size_t sent = 0;
	IO::IO_RESULT read_result =
		client.write(buffer.c_str(), buffer.size(), sent);
	if (read_result != IO::IO_RESULT::SUCCESS)
		showError(
			"Error: Request sending failed."); // TODO::print error
	bool done = false;
	std::string str;
	do {
		read_result = client.read();
		switch (read_result) {
		case IO::IO_RESULT::SUCCESS: {
			str += std::string(client.buffer, client.buffer_size);
			client.buffer_size = 0;
			done = true;
			break;
		}
		case IO::IO_RESULT::FULL_BUFFER:
		case IO::IO_RESULT::DONE_TRY_AGAIN:
		case IO::IO_RESULT::ZERO_DATA: {
			str += std::string(client.buffer, client.buffer_size);
			client.buffer_size = 0;
			break;
		}
		default:
			if (client.buffer_size > 0) {
				str += std::string(client.buffer,
						   client.buffer_size);
				client.buffer_size = 0;
			}
			done = true;
			break;
		}
	} while (!done);

	if (read_result != IO::IO_RESULT::SUCCESS)
		showError("Error: Response reading failed.");
	HttpResponse response;
	size_t used_bytes;

	auto parse_result = response.parseResponse(str, &used_bytes);
	if (parse_result != http_parser::PARSE_RESULT::SUCCESS)
		showError("Error parsing response");
	str = std::string(response.message, response.message_length);
	auto json_object_ptr = json::JsonParser::parse(str);
	if (json_object_ptr == nullptr)
		showError("Error parsing response json");
	std::unique_ptr<json::JsonObject> json_response(
		std::move(json_object_ptr));
	if (ctl_command == CTL_ACTION::NONE)
		outputStatus(json_response.get());
	return (response.http_status_code >= 200 &&
		response.http_status_code < 300);
}

bool PoundClient::init(int argc, char *argv[])
{
	Timer timeout;
	int ms_to = DEFAULT_CTL_TIMEOUT;
	int opt = 0;
	int option_index = 0;

	binary_name = std::string(argv[0]);
	while ((opt = getopt_long(argc, argv, options_string, long_options,
				  &option_index)) != -1) {
		switch (opt) {
		case 't': {
			ms_to = atoi(optarg);
			if (ms_to <= 0)
				showHelp("The timeout must be bigger than 0");
			break;
		}
		case 'c': {
			if (interface_mode != CTL_INTERFACE_MODE::CTL_NONE)
				showHelp(
					"Only one interface control mode allowed");
			interface_mode = CTL_INTERFACE_MODE::CTL_UNIX;
			control_socket = optarg;
			if (control_socket.empty())
				showHelp("No valid socket path found");
			break;
		}
		case 'a': {
			if (interface_mode != CTL_INTERFACE_MODE::CTL_NONE)
				showHelp(
					"Only one interface control mode allowed");
			interface_mode = CTL_INTERFACE_MODE::CTL_AF_INET;
			address = optarg;
			if (address.empty())
				showHelp("No valid address found");
			break;
		}
		case 'X':
			xml_output = true;
			break;
		case 'H':
			resolve_hosts = true;
			break;
		case 'v':
			verbose = true;
			break;
		case 'R': {
			ctl_command = CTL_ACTION::RELOAD;
			ctl_command_subject = CTL_SUBJECT::LISTENER;
			trySetAllTargetId(argv, optind);
			break;
		}
		case 'L': {
			ctl_command = CTL_ACTION::ENABLE;
			ctl_command_subject = CTL_SUBJECT::LISTENER;
			trySetAllTargetId(argv, optind);
			break;
		}
		case 'S': {
			ctl_command = CTL_ACTION::ENABLE;
			ctl_command_subject = CTL_SUBJECT::SERVICE;
			trySetAllTargetId(argv, optind);
			break;
		}
		case 'B': {
			ctl_command = CTL_ACTION::ENABLE;
			ctl_command_subject = CTL_SUBJECT::BACKEND;
			trySetAllTargetId(argv, optind);
			break;
		}
		case 'l': {
			ctl_command = CTL_ACTION::DISABLE;
			ctl_command_subject = CTL_SUBJECT::LISTENER;
			trySetAllTargetId(argv, optind);
			break;
		}
		case 's': {
			ctl_command = CTL_ACTION::DISABLE;
			ctl_command_subject = CTL_SUBJECT::SERVICE;
			trySetAllTargetId(argv, optind);
			break;
		}
		case 'b': {
			ctl_command = CTL_ACTION::DISABLE;
			ctl_command_subject = CTL_SUBJECT::BACKEND;
			trySetAllTargetId(argv, optind);
			break;
		}
		case 'N': {
			ctl_command = CTL_ACTION::ADD_SESSION;
			ctl_command_subject = CTL_SUBJECT::SESSION;
			trySetAllTargetId(argv, optind);
			break;
		}
		case 'n': {
			ctl_command = CTL_ACTION::DELETE_SESSION;
			ctl_command_subject = CTL_SUBJECT::SESSION;
			trySetAllTargetId(argv, optind);
			break;
		}
		case 'f': {
			ctl_command = CTL_ACTION::FLUSH_SESSIONS;
			ctl_command_subject = CTL_SUBJECT::SESSION;
			trySetAllTargetId(argv, optind);
			break;
		}
		case 'h':
		case '?':
			showHelp("HELP");
			break;
		default:
			showHelp("Unknown uption");
			break;
		}
	}

	if (verbose) {
		std::string action_message = "";
		switch (ctl_command) {
		case CTL_ACTION::NONE:
			action_message = "No action found";
			break;
		case CTL_ACTION::ENABLE:
			action_message = "Enable";
			break;
		case CTL_ACTION::DISABLE:
			action_message = "Disable";
			break;
		case CTL_ACTION::ADD_SESSION:
			action_message = "Add session";
			break;
		case CTL_ACTION::DELETE_SESSION:
			action_message = "Delete";
			break;
		case CTL_ACTION::FLUSH_SESSIONS:
			action_message = "Flush session";
			break;
		case CTL_ACTION::RELOAD:
			action_message = "Reload WAF rulesets";
			break;
		}

		if (!session_key.empty()) {
			action_message += "\tsession : " + session_key;
		}

		if (backend_id != NO_VALUE) {
			action_message +=
				"\tbackend: " + std::to_string(backend_id) +
				" in ";
		}

		if (service_id != NO_VALUE) {
			action_message +=
				"\tservice: " + std::to_string(service_id) +
				" in ";
		}
		if (listener_id != NO_VALUE) {
			action_message +=
				"\tlistener: " + std::to_string(listener_id);
		}
		action_message += "\nOptions:";
		action_message += xml_output ? "\n\tXML output: ON" :
						     "\n\tXML output: OFF";
		action_message += resolve_hosts ? "\n\tResolve host : ON" :
							"\n\tResolve host : OFF";
		//    for (int i = 0; i < argc; i++) std::cout << argv[i] << " ";
		std::cout << "\n" << action_message << std::endl;
	}

	timeout.start(ms_to);
	auto rt = executeCommand();
	timeout.stop();
	return rt;
}

bool PoundClient::doRequest(http::REQUEST_METHOD request_method,
			    http::HTTP_VERSION http_version,
			    std::string json_object, std::string path,
			    std::string &buffer)
{
	auto it = http::http_info::http_verb_strings.find(request_method);
	if (it != http::http_info::http_verb_strings.end()) {
		buffer = it->second;
		buffer = buffer + " ";
	} else {
		return false;
	}

	buffer += path;
	buffer += " ";

	if (http_version == http::HTTP_VERSION::HTTP_1_0) {
		buffer += "HTTP/1.0\r\n";
	} else {
		buffer += "HTTP/1.1\r\n";
	}
	buffer += "Connection: close\r\n";
	buffer += "Content-Length: ";
	buffer += std::to_string(json_object.size() + http::CRLF_LEN);
	buffer += http::CRLF;
	buffer += "Accept: application/json\r\n";
	buffer += http::CRLF;
	buffer += json_object;
	buffer += http::CRLF;
	return true;
}

void PoundClient::verboseLog(const std::string &str)
{
	if (verbose)
		std::cout << str << std::endl;
}

void PoundClient::outputStatus(json::JsonObject *json_response_listener)
{
	std::string buffer;
	buffer += "Requests in queue: 0\n";
	std::string protocol = "HTTP";
	std::string listener_status = "a";
	int backend_counter = 0;

	//  Use this if we have multiple listeners
	//  if(dynamic_cast<json::JsonDataValue*>(json_response_listener->at(json::JSON_KEYS::STATUS))->string_value
	//  == "disabled")
	//    listener_status = "*D";
	auto is_ssl = json_response_listener->at(json::JSON_KEYS::HTTPS).get();
	if (is_ssl)
		protocol = "HTTPS";
	buffer += "  0. ";
	buffer += protocol;
	buffer += " Listener ";
	buffer += dynamic_cast<json::JsonDataValue *>(
			  json_response_listener->at(json::JSON_KEYS::ADDRESS)
				  .get())
			  ->string_value;
	buffer += " ";
	buffer += listener_status;
	buffer += "\n";

	auto services = dynamic_cast<json::JsonArray *>(
		json_response_listener->at(json::JSON_KEYS::SERVICES).get());
	// TODO recorrer servicios
	for (const auto &service : *services) {
		// TODO: AQUI DESAPARECE EL RESPONSE-TIME (ES POSIBLE QUE POR EL -1)
		auto service_json =
			dynamic_cast<json::JsonObject *>(service.get());
		auto backends = dynamic_cast<json::JsonArray *>(
			service_json->at(json::JSON_KEYS::BACKENDS).get());
		int total_weight = 0;
		auto service_counter =
			dynamic_cast<json::JsonDataValue *>(
				service_json->at(json::JSON_KEYS::ID).get())
				->number_value;
		for (const auto &backend : *backends) {
			auto backend_json =
				dynamic_cast<json::JsonObject *>(backend.get());
			auto backend_type =
				dynamic_cast<json::JsonDataValue *>(
					backend_json->at(json::JSON_KEYS::TYPE)
						.get())
					->number_value;
			if (static_cast<BACKEND_TYPE>(backend_type) ==
			    BACKEND_TYPE::REDIRECT)
				continue;
			total_weight +=
				dynamic_cast<json::JsonDataValue *>(
					backend_json
						->at(json::JSON_KEYS::WEIGHT)
						.get())
					->number_value;
		}
		std::string service_name =
			dynamic_cast<json::JsonDataValue *>(
				service_json->at(json::JSON_KEYS::NAME).get())
				->string_value;
		std::string service_status =
			dynamic_cast<json::JsonDataValue *>(
				service_json->at(json::JSON_KEYS::STATUS).get())
				->string_value;
		buffer += "    ";
		buffer += std::to_string(static_cast<int>(service_counter));
		buffer += ". Service \"";
		buffer += service_name;
		buffer += "\" ";
		buffer += service_status;
		buffer += " (";
		buffer += std::to_string(total_weight);
		buffer += ")\n";

		backend_counter = 0;
		for (const auto &backend : *backends) {
			auto backend_json =
				dynamic_cast<json::JsonObject *>(backend.get());
			auto backend_type =
				dynamic_cast<json::JsonDataValue *>(
					backend_json->at(json::JSON_KEYS::TYPE)
						.get())
					->number_value;
			if (static_cast<BACKEND_TYPE>(backend_type) ==
			    BACKEND_TYPE::REDIRECT)
				continue;
			auto weight =
				dynamic_cast<json::JsonDataValue *>(
					backend_json
						->at(json::JSON_KEYS::WEIGHT)
						.get())
					->number_value;
			std::string backend_address =
				dynamic_cast<json::JsonDataValue *>(
					backend_json
						->at(json::JSON_KEYS::ADDRESS)
						.get())
					->string_value;
			std::string backend_status =
				dynamic_cast<json::JsonDataValue *>(
					backend_json
						->at(json::JSON_KEYS::STATUS)
						.get())
					->string_value;
			auto backend_port =
				dynamic_cast<json::JsonDataValue *>(
					backend_json->at(json::JSON_KEYS::PORT)
						.get())
					->number_value;
			double response_time =
				dynamic_cast<json::JsonDataValue *>(
					backend_json
						->at(json::JSON_KEYS::
							     RESPONSE_TIME)
						.get())
					->double_value;
			auto connections =
				dynamic_cast<json::JsonDataValue *>(
					backend_json
						->at(json::JSON_KEYS::CONNECTIONS)
						.get())
					->number_value;

			// PoundCtl transform backend disabled status to uppercase
			if (backend_status == "disabled")
				std::transform(backend_status.begin(),
					       backend_status.end(),
					       backend_status.begin(),
					       ::toupper);

			buffer += "      ";
			buffer += std::to_string(
				static_cast<int>(backend_counter++));
			buffer += ". Backend ";
			buffer += backend_address;
			buffer += ":";
			buffer += std::to_string(backend_port);
			buffer += " ";
			buffer += backend_status;
			buffer += " (";
			buffer += std::to_string(weight);
			buffer += " ";
			buffer += conversionHelper::toStringWithPrecision(
				response_time < 0 ? 0.0 : response_time);
			if (backend_status == "down")
				buffer += ") DEAD (";
			else
				buffer += ") alive (";
			buffer += std::to_string(connections);
			buffer += ")\n";
		}

		auto sessions = dynamic_cast<json::JsonArray *>(
			service_json->at(json::JSON_KEYS::SESSIONS).get());
		int session_counter = 0;
		for (const auto &session : *sessions) {
			auto session_json =
				dynamic_cast<json::JsonObject *>(session.get());
			std::string session_id =
				dynamic_cast<json::JsonDataValue *>(
					session_json->at(json::JSON_KEYS::ID)
						.get())
					->string_value;
			auto session_backend =
				dynamic_cast<json::JsonDataValue *>(
					session_json
						->at(json::JSON_KEYS::BACKEND_ID)
						.get())
					->number_value;
			buffer += "      ";
			buffer += std::to_string(session_counter);
			buffer += ". Session ";
			buffer += session_id;
			buffer += " -> ";
			buffer += std::to_string(session_backend);
			buffer += "\n";
			session_counter++;
		}
	}

	std::cout << buffer << std::endl;
}

void PoundClient::showError(std::string error)
{
	zcu_log_print(LOG_ERR, "%s():%d: %s", __FUNCTION__, __LINE__,
		      error.data());
	exit(EXIT_FAILURE);
}
