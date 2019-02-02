//
// Created by abdess on 9/28/18.
//
#include "PoundClient.h"
#include "../util/Network.h"

bool PoundClient::trySetTargetId(int &target_id, char *possible_value) {
  if (possible_value)  // thorow error and show help
    target_id = std::atoi(possible_value);
  else
    return false;
  return true;
}

void PoundClient::trySetAllTargetId(char *argv[], int &option_index) {
  int to_consume = 1;
  int next_index = option_index + to_consume;
  switch (ctl_command_subject) { /*Intentional fallthrough*/
    case CTL_SUBJECT::SESSION:
      if (ctl_command == CTL_ACTION::ADD_SESSION) {
        to_consume++;
        next_index++;
      }
    case CTL_SUBJECT::BACKEND: {
      next_index++;
      if (ctl_command != CTL_ACTION::DELETE_SESSION &&
        !trySetTargetId(this->backend_id, argv[next_index--]))
        show_usage("no valid backend id found");

      if (ctl_command == CTL_ACTION::ADD_SESSION ||
          ctl_command == CTL_ACTION::DELETE_SESSION) {
        if (!argv[option_index]) show_usage("no valid session key found");
          session_key = std::string(argv[next_index--]);
        if (session_key.empty()) show_usage("no valid session key found");
      }
    }
    case CTL_SUBJECT::SERVICE:
      if (!trySetTargetId(this->service_id, argv[next_index--]))
        show_usage("no valid service id found");
    case CTL_SUBJECT::LISTENER:
      if (trySetTargetId(this->listener_id, argv[next_index--])) {
        option_index += to_consume;
        break;
      }
    default:
      show_usage("target id list error");
  }
}

void PoundClient::show_usage(const std::string error) {
  if (!error.empty())
    std::cout << "ERROR: " << error << std::endl;
  std::cout << "Usage: " << std::endl;
  std::cout << "\tProxy control interface in:\n\t\tLocal mode:\t" << binary_name
            << " -c /control/socket [ -X ] cmd" << std::endl;
  std::cout << "\t\tTCP mode:\t" << binary_name << " -a IP:PORT [ -X ] cmd\n"
            << std::endl;
  std::cout << "\twhere cmd is one of:" << std::endl;
  std::cout << "\t-L n - enable listener n" << std::endl;
  std::cout << "\t-l n - disable listener n" << std::endl;
  std::cout << "\t-S n m - enable service m in listener n (use -1 for "
               "global services)"
            << std::endl;
  std::cout << "\t-s n m - disable service m in listener n (use -1 for "
               "global services)"
            << std::endl;
  std::cout << "\t-B n m r - enable back-end r in service m in listener n"
            << std::endl;
  std::cout << "\t-b n m r - disable back-end r in service m in listener n"
            << std::endl;
  std::cout << "\t-f n m r - flush all sessions for back-end r in service m "
               "in listener n"
            << std::endl;
  std::cout << "\t-N n m k r - add a session with key k and back-end r in "
               "service m in listener n"
            << std::endl;
  std::cout << "\t-n n m k - remove a session with key k r in service m in "
               "listener n"
            << std::endl;
  std::cout << "" << std::endl;
  std::cout << "\tentering the command without arguments lists the current "
               "configuration."
            << std::endl;
  std::cout << "\tthe -X flag results in XML output." << std::endl;
  std::cout << "\tthe -H flag shows symbolic host names instead of addresses."
            << std::endl;
  std::cout << "\tthe -v flag enable verbose mode to STDOUT" << std::endl;
  exit(EXIT_FAILURE);
}

bool PoundClient::executeCommand() {
  Connection client;
  switch (interface_mode) {
  case CTL_INTERFACE_MODE::CTL_NONE: {
    //Lanzar error: "No se ha especificado metodo de conexion"
    show_usage("Unspecified connection method.");
  }
  case CTL_INTERFACE_MODE::CTL_AF_INET: {
    int port;
    size_t pos = this->address.rfind(':');
    if (pos == std::string::npos)
      return false;
    port = std::stoi(this->address.substr(pos + 1, this->address.size() - pos));
    this->address = this->address.substr(0, pos);
    client.address = Network::getAddress(this->address, port);
    IO::IO_OP res_connect = client.doConnect(*client.address, 0);
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
  if (ctl_command == CTL_ACTION::ENABLE || ctl_command == CTL_ACTION::DISABLE) {
    json_object.emplace(json::JSON_KEYS::STATUS, std::unique_ptr<json::JsonDataValue>(
        new json::JsonDataValue(ctl_command == CTL_ACTION::ENABLE ? json::JSON_KEYS::STATUS_ACTIVE
                                                                  : json::JSON_KEYS::STATUS_DISABLED)));
    method = http::REQUEST_METHOD::PATCH;
    switch (ctl_command_subject) {
    case CTL_SUBJECT::LISTENER: {
      path += "/status";
      break;
    }
    case CTL_SUBJECT::SERVICE: {
      path += "/service/" + std::to_string(service_id) + "/status";
      break;
    }
    case CTL_SUBJECT::BACKEND: {
      path += "/service/" + std::to_string(service_id) + "/backend/" + std::to_string(backend_id) + "/status";
      break;
    }
    default:
      exit(EXIT_FAILURE);
    }

  }
  if (ctl_command_subject == CTL_SUBJECT::SESSION) {
    path += "/service/" + std::to_string(service_id) + "/session/";
    switch (ctl_command) {
    case CTL_ACTION::ADD_SESSION: {
      json_object.emplace(json::JSON_KEYS::BACKEND_ID, new json::JsonDataValue(this->backend_id));
      json_object.emplace(json::JSON_KEYS::ID, new json::JsonDataValue(this->session_key));
      method = http::REQUEST_METHOD::PUT;
      break;
    }
    case CTL_ACTION::DELETE_SESSION: {
      json_object.emplace(json::JSON_KEYS::ID, new json::JsonDataValue(this->session_key));
      method = http::REQUEST_METHOD::DELETE;
      break;
    }
    case CTL_ACTION::FLUSH_SESSIONS: {
      json_object.emplace(json::JSON_KEYS::BACKEND_ID, new json::JsonDataValue(this->backend_id));
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
  if (doRequest(method, http::HTTP_VERSION::HTTP_1_0, json_object.stringify(), path, buffer)) {
    verboseLog(buffer);
  }
  IO::IO_RESULT read_result = client.write(buffer.c_str(), buffer.size());
  if (read_result != IO::IO_RESULT::SUCCESS)
    showError("Error: Request sending failed.");//TODO::print error
  read_result = client.read();
  if (read_result != IO::IO_RESULT::SUCCESS)
    showError("Error: Response reading failed.");
  HttpResponse response;
  size_t used_bytes;
  auto str = std::string(client.buffer, client.buffer_size);
  auto parse_result = response.parseResponse(str, &used_bytes);
  if (parse_result != http_parser::PARSE_RESULT::SUCCESS)
    showError("Error parsing response");
  str = std::string(response.message, response.message_length);
  auto json_object_ptr = json::JsonParser::parse(str);
  if (json_object_ptr == nullptr)
    showError("Error parsing response json");
  std::unique_ptr<json::JsonObject> json_response(std::move(json_object_ptr));
  if (ctl_command == CTL_ACTION::NONE)
    outputStatus(json_response.get());
  return true;
}


bool PoundClient::init(int argc, char *argv[]) {
  int opt = 0;
  int option_index = 0;

  binary_name = std::string(argv[0]);
  while ((opt = getopt_long(argc, argv, options_string, long_options,
                            &option_index)) != -1) {
    switch (opt) {
      case 'c': {
        if (interface_mode != CTL_INTERFACE_MODE::CTL_NONE)
          show_usage("Only one interface control mode allowed");
        interface_mode = CTL_INTERFACE_MODE::CTL_UNIX;
        control_socket = optarg;
        if (control_socket.empty()) show_usage("No valid socket path found");
        break;
      }
      case 'a': {
        if (interface_mode != CTL_INTERFACE_MODE::CTL_NONE)
          show_usage("Only one interface control mode allowed");
        interface_mode = CTL_INTERFACE_MODE::CTL_AF_INET;
        address = optarg;
        if (address.empty()) show_usage("No valid address found");
        break;
      }
      case 'X': xml_output = true;
        break;
      case 'H': resolve_hosts = true;
        break;
      case 'v': verbose = true;
        break;
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
        show_usage("HELP");
        break;
      default:
        show_usage("Unknown uption");
        break;
    }
  }

  if (verbose) {
    std::string action_message = "";
    switch (ctl_command) {
      case CTL_ACTION::NONE: action_message = "No action found";
        break;
      case CTL_ACTION::ENABLE: action_message = "Enable";
        break;
      case CTL_ACTION::DISABLE: action_message = "Disable";
        break;
      case CTL_ACTION::ADD_SESSION: action_message = "Add session";
        break;
      case CTL_ACTION::DELETE_SESSION: action_message = "Delete";
        break;
      case CTL_ACTION::FLUSH_SESSIONS: action_message = "Flush session";
        break;
    }

    if (!session_key.empty()) {
      action_message += "\tsession : " + session_key;
    }

    if (backend_id != NO_VALUE) {
      action_message += "\tbackend: " + std::to_string(backend_id) + " in ";
    }

    if (service_id != NO_VALUE) {
      action_message += "\tservice: " + std::to_string(service_id) + " in ";
    }
    if (listener_id != NO_VALUE) {
      action_message += "\tlistener: " + std::to_string(listener_id);
    }
    action_message += "\nOptions:";
    action_message += xml_output ? "\n\tXML output: ON" : "\n\tXML output: OFF";
    action_message +=
        resolve_hosts ? "\n\tResolve host : ON" : "\n\tResolve host : OFF";
    //    for (int i = 0; i < argc; i++) std::cout << argv[i] << " ";
    std::cout << "\n" << action_message << std::endl;
  }
  executeCommand();
  return true;
}

bool PoundClient::doRequest(http::REQUEST_METHOD request_method,http::HTTP_VERSION http_version, std::string json_object, std::string path, std::string &buffer) {
  if (http::http_info::http_verb_strings.count(request_method) > 0) {
    buffer = http::http_info::http_verb_strings.at(request_method);
    buffer = buffer + " ";
  } else {
    return false;
  }

  buffer += path;
  buffer += " ";

  switch (http_version) {
    case http::HTTP_VERSION::HTTP_1_0: {
      buffer += "HTTP/1.0\r\n";
      break;
    }
    case http::HTTP_VERSION::HTTP_1_1: {
      buffer += "HTTP/1.1\r\n";
      break;
    }
    case http::HTTP_VERSION::HTTP_2_0: {
      //buffer = buffer + "HTTP/2.O\r\";
      //break;
      return false; //TODO: COMPROBAR SI ES ASÍ LA LINE REQUEST.
    }
  }

  buffer += "Connection: close\r\n";
  buffer += "Accept: application/json\r\n";

  buffer += "\r\n";

  buffer += json_object;
  buffer += "\r\n";

  return true;
}

void PoundClient::verboseLog(const std::string &str){
  if (verbose)
    std::cout << str << std::endl;
}

void PoundClient::outputStatus(json::JsonObject *json_response_listener) {
  std::string buffer;
  buffer += "Requests in queue: 0\n";
  std::string protocol = "HTTP";
  std::string listener_status = "a";

//  Use this if we have multiple listeners
//  if(dynamic_cast<json::JsonDataValue*>(json_response_listener->at(json::JSON_KEYS::STATUS))->string_value == "disabled")
//    listener_status = "*D";

  if(dynamic_cast<json::JsonDataValue*>(json_response_listener->at(json::JSON_KEYS::HTTPS).get()))
    protocol += "HTTPS";
  buffer += "  0. " + protocol + " Listener " + dynamic_cast<json::JsonDataValue*>(json_response_listener->at(json::JSON_KEYS::ADDRESS).get())->string_value + " " + listener_status + "\n";

  auto services = dynamic_cast<json::JsonArray *>(json_response_listener->at(json::JSON_KEYS::SERVICES).get());
  //TODO recorrer servicios
  for (const auto & service : *services) {
      //TODO: AQUI DESAPARECE EL RESPONSE-TIME (ES POSIBLE QUE POR EL -1)
      auto service_json = dynamic_cast<json::JsonObject *>(service.get());
      auto backends = dynamic_cast<json::JsonArray *>(service_json->at(json::JSON_KEYS::BACKENDS).get());
      int total_weight = 0;
      int service_counter = 0;
      for (const auto &backend : *backends) {
        auto backend_json = dynamic_cast<json::JsonObject *>(backend.get());
        total_weight += dynamic_cast<json::JsonDataValue *>(backend_json->at(json::JSON_KEYS::WEIGHT).get())->number_value;
      }
      std::string service_name = dynamic_cast<json::JsonDataValue *>(service_json->at(json::JSON_KEYS::NAME).get())->string_value;
      std::string service_status = dynamic_cast<json::JsonDataValue *>(service_json->at(json::JSON_KEYS::STATUS).get())->string_value;
      buffer += "    ";
      buffer += std::to_string(service_counter);
      buffer += ". Service \"";
      buffer += service_name;
      buffer += "\" ";
      buffer += service_status;
      buffer += " (";
      buffer += std::to_string(total_weight);
      buffer += ")\n";
      service_counter++;

      int backend_counter = 0;
      for (const auto& backend : *backends) {
        auto backend_json = dynamic_cast<json::JsonObject *>(backend.get());
        auto weight = dynamic_cast<json::JsonDataValue *>(backend_json->at(json::JSON_KEYS::WEIGHT).get())->number_value;
        std::string backend_address = dynamic_cast<json::JsonDataValue *>(backend_json->at(json::JSON_KEYS::ADDRESS).get())->string_value;
        std::string backend_status = dynamic_cast<json::JsonDataValue *>(backend_json->at(json::JSON_KEYS::STATUS).get())->string_value;
        auto backend_port = dynamic_cast<json::JsonDataValue *>(backend_json->at(json::JSON_KEYS::PORT).get())->number_value;
        double response_time = dynamic_cast<json::JsonDataValue *>(backend_json->at(json::JSON_KEYS::RESPONSE_TIME).get())->double_value;
        auto connections = dynamic_cast<json::JsonDataValue *>(backend_json->at(json::JSON_KEYS::CONNECTIONS).get())->number_value;

        buffer += "      ";
        buffer += std::to_string(backend_counter);
        buffer += ". Backend ";
        buffer += backend_address;
        buffer += ":";
        buffer += std::to_string(backend_port);
        buffer += " ";
        buffer += backend_status;
        buffer += " (";
        buffer += std::to_string(weight);
        buffer += " ";
        buffer += conversionHelper::to_string_with_precision(response_time);
        buffer += ") alive (";
        buffer += std::to_string(connections);
        buffer += ")\n";
        backend_counter++;
      }

      auto sessions = dynamic_cast<json::JsonArray *>(service_json->at(json::JSON_KEYS::SESSIONS).get());
      int session_counter = 0;
      for (const auto &session : *sessions) {
        auto session_json = dynamic_cast<json::JsonObject *>(session.get());
        std::string session_id = dynamic_cast<json::JsonDataValue *>(session_json->at(json::JSON_KEYS::ID).get())->string_value;
        auto session_backend =
            dynamic_cast<json::JsonDataValue *>(session_json->at(json::JSON_KEYS::BACKEND_ID).get())->number_value;
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

void PoundClient::showError(std::string error) {
  Debug::LogInfo(error, LOG_ERR);
  exit(EXIT_FAILURE);
}
