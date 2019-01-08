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
  if (!error.empty()) std::cout << "ERROR: " << error << std::endl;
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
  switch(interface_mode) {
    case CTL_INTERFACE_MODE::CTL_NONE: {
    //Lanzar error: "No se ha especificado metodo de conexion"
    show_usage("Unspecified connection method.");
    }

    case CTL_INTERFACE_MODE::CTL_AF_INET: {
      int port;

      size_t pos = this->address.rfind(':');
      if (pos == std::string::npos)
        return false;

      port = std::stoi(this->address.substr(pos+1, this->address.size() - pos));
      this->address = this->address.substr(0, pos);
      client.address = Network::getAddress(this->address, port);
      client.doConnect(*client.address, 0);
      break;
    }

    default: {
      client.doConnect(control_socket, 0);
    }
  }

  json::JsonObject json_object;
  std::string buffer;

  switch (ctl_command) {
    case CTL_ACTION::ENABLE: {
        switch (ctl_command_subject) {
          case CTL_SUBJECT::LISTENER: {
              std::string path = "/listener/" + std::to_string(listener_id) + "/status";
              json_object.emplace(json::JSON_KEYS::STATUS, new json::JsonDataValue(json::JSON_KEYS::STATUS_ACTIVE));
              if (doRequest(http::REQUEST_METHOD::PATCH, http::HTTP_VERSION::HTTP_1_0, json_object.stringify(), path, buffer)){
                  verboseLog(buffer);
              }
              client.write(buffer.c_str(), buffer.size());
              client.read();
              return true;
         }
         case CTL_SUBJECT::SERVICE: {
              std::string path = "/listener/" + std::to_string(listener_id) + "/service/" + std::to_string(service_id) + "/status";
              json_object.emplace(json::JSON_KEYS::STATUS, new json::JsonDataValue(json::JSON_KEYS::STATUS_ACTIVE));
              if (doRequest(http::REQUEST_METHOD::PATCH, http::HTTP_VERSION::HTTP_1_0, json_object.stringify(), path, buffer)){
                  verboseLog(buffer);
              }
              client.write(buffer.c_str(), buffer.size());
              client.read();
              return true;
         }
         case CTL_SUBJECT::BACKEND: {
               std::string path = "/listener/" + std::to_string(listener_id) + "/service/" + std::to_string(service_id) + "/backend/" + std::to_string(backend_id) + "/status";
               json_object.emplace(json::JSON_KEYS::STATUS, new json::JsonDataValue(json::JSON_KEYS::STATUS_UP));
               if (doRequest(http::REQUEST_METHOD::PATCH, http::HTTP_VERSION::HTTP_1_0, json_object.stringify(), path, buffer)){
                   verboseLog(buffer);
               }
               client.write(buffer.c_str(), buffer.size());
               client.read();
               return true;
          }
      }
    }
    case CTL_ACTION::DISABLE: {
        switch (ctl_command_subject) {
          case CTL_SUBJECT::LISTENER: {
              std::string path = "/listener/" + std::to_string(listener_id) + "/status";
              json_object.emplace(json::JSON_KEYS::STATUS, new json::JsonDataValue(json::JSON_KEYS::STATUS_DISABLED));
              if (doRequest(http::REQUEST_METHOD::PATCH, http::HTTP_VERSION::HTTP_1_0, json_object.stringify(), path, buffer)){
                  verboseLog(buffer);
              }
              client.write(buffer.c_str(), buffer.size());
              client.read();
              return true;
          }
          case CTL_SUBJECT::SERVICE: {
              std::string path = "/listener/" + std::to_string(listener_id) + "/service/" + std::to_string(service_id) + "/status";
              json_object.emplace(json::JSON_KEYS::STATUS, new json::JsonDataValue(json::JSON_KEYS::STATUS_DISABLED));
              if (doRequest(http::REQUEST_METHOD::PATCH, http::HTTP_VERSION::HTTP_1_0, json_object.stringify(), path, buffer)){
                  verboseLog(buffer);
              }
              client.write(buffer.c_str(), buffer.size());
              client.read();
              return true;
          }
          case CTL_SUBJECT::BACKEND: {
              std::string path = "/listener/" + std::to_string(listener_id) + "/service/" + std::to_string(service_id) + "/backend/" + std::to_string(backend_id) + "/status";
              json_object.emplace(json::JSON_KEYS::STATUS, new json::JsonDataValue(json::JSON_KEYS::STATUS_DISABLED));
              if (doRequest(http::REQUEST_METHOD::PATCH, http::HTTP_VERSION::HTTP_1_0, json_object.stringify(), path, buffer)){
                  verboseLog(buffer);
              }
              client.write(buffer.c_str(), buffer.size());
              client.read();
              return true;
          }
        }
    }
    case CTL_ACTION::ADD_SESSION: {
        switch (ctl_command_subject) {
          case CTL_SUBJECT::SESSION: {
            std::string path = "/listener/" + std::to_string(listener_id) + "/service/" + std::to_string(service_id) + "/session/";
            json_object.emplace(json::JSON_KEYS::BACKEND_ID, new json::JsonDataValue(this->backend_id));
            json_object.emplace(json::JSON_KEYS::ID, new json::JsonDataValue(this->session_key));
            if (doRequest(http::REQUEST_METHOD::PUT, http::HTTP_VERSION::HTTP_1_0, json_object.stringify(), path, buffer)){
                verboseLog(buffer);
            }
            client.write(buffer.c_str(), buffer.size());
            client.read();
            return true;
          }
        }
      }
    case CTL_ACTION::DELETE_SESSION: {
      switch (ctl_command_subject) {
        case CTL_SUBJECT::SESSION: {
          std::string path = "/listener/" + std::to_string(listener_id) + "/service/" + std::to_string(service_id) + "/session/";
          json_object.emplace(json::JSON_KEYS::ID, new json::JsonDataValue(this->session_key));
          if (doRequest(http::REQUEST_METHOD::DELETE, http::HTTP_VERSION::HTTP_1_0, json_object.stringify(), path, buffer)){
              verboseLog(buffer);
            }
          client.write(buffer.c_str(), buffer.size());
          client.read();
          return true;
        }
      }
    }
    case CTL_ACTION::FLUSH_SESSIONS: {
      switch (ctl_command_subject) {
        case CTL_SUBJECT::SESSION: {
            std::string path = "/listener/" + std::to_string(listener_id) + "/service/" + std::to_string(service_id) + "/session/";
            json_object.emplace(json::JSON_KEYS::BACKEND_ID, new json::JsonDataValue(this->backend_id));
            if (doRequest(http::REQUEST_METHOD::DELETE, http::HTTP_VERSION::HTTP_1_0, json_object.stringify(), path, buffer)){
                verboseLog(buffer);
              }
            client.write(buffer.c_str(), buffer.size());
            client.read();
            return true;
        }
      }
    }
    default: {
        std::string path = "/listener/" + std::to_string(listener_id) + "/service";
        if (doRequest(http::REQUEST_METHOD::GET, http::HTTP_VERSION::HTTP_1_0, "", path, buffer)){
            verboseLog(buffer);
        }
        client.write(buffer.c_str(), buffer.size());
        IO::IO_RESULT read_result = client.read();
        if (read_result != IO::IO_RESULT::SUCCESS)
          exit(EXIT_FAILURE);
        //TODO: AÑADIR COMPROBACIONES
        HttpResponse response;
        size_t used_bytes;
        auto parse_result = response.parseResponse(std::string(client.buffer, client.buffer_size), &used_bytes);
        if (parse_result != http_parser::PARSE_RESULT::SUCCESS)
          exit(EXIT_FAILURE);
        json::JsonObject *json_response(json::JsonParser::parse(std::string(response.message, response.message_length)));
        outputStatus(json_response);
        return true;
    }
  }
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
      case 'X':
        xml_output = true;
        break;
      case 'H':
        resolve_hosts = true;
        break;
      case 'v':
        verbose = true;
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

  buffer = buffer + path + " ";

  switch (http_version) {
    case http::HTTP_VERSION::HTTP_1_0: {
      buffer = buffer + "HTTP/1.0\r\n";
      break;
    }
    case http::HTTP_VERSION::HTTP_1_1: {
      buffer = buffer + "HTTP/1.1\r\n";
      break;
    }
    case http::HTTP_VERSION::HTTP_2_0: {
      //buffer = buffer + "HTTP/2.O\r\";
      //break;
      return false; //TODO: COMPROBAR SI ES ASÍ LA LINE REQUEST.
    }
  }

  buffer = buffer + "Connection: close\r\n";
  buffer = buffer + "Accept: application/json\r\n";

  buffer = buffer + "\r\n";

  buffer = buffer + json_object;
  buffer = buffer + "\r\n";

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
//  if(static_cast<json::JsonDataValue*>(json_response_listener->at(json::JSON_KEYS::STATUS))->string_value == "disabled")
//    listener_status = "*D";

  if(static_cast<json::JsonDataValue*>(json_response_listener->at(json::JSON_KEYS::HTTPS)))
    protocol += "HTTPS";
  buffer += "  0. " + protocol + " Listener " + static_cast<json::JsonDataValue*>(json_response_listener->at(json::JSON_KEYS::ADDRESS))->string_value + " " + listener_status + "\n";

  auto services = static_cast<json::JsonArray *>(json_response_listener->at(json::JSON_KEYS::SERVICES));
  //TODO recorrer servicios
  for (auto service : *services) {
      //TODO: AQUI DESAPARECE EL RESPONSE-TIME (ES POSIBLE QUE POR EL -1)
      auto service_json = reinterpret_cast<json::JsonObject *>(service);
      auto backends = static_cast<json::JsonArray *>(service_json->at(json::JSON_KEYS::BACKENDS));
      int total_weight = 0;
      int service_counter = 0;
      for (auto backend : *backends) {
        auto backend_json = reinterpret_cast<json::JsonObject *>(backend);
        total_weight += static_cast<json::JsonDataValue *>(backend_json->at(json::JSON_KEYS::WEIGHT))->number_value;
      }
      std::string service_name = static_cast<json::JsonDataValue *>(service_json->at(json::JSON_KEYS::NAME))->string_value;
      std::string service_status = static_cast<json::JsonDataValue *>(service_json->at(json::JSON_KEYS::STATUS))->string_value;
      buffer += "    " + std::to_string(service_counter) + ". Service \"" + service_name + "\" " + service_status + " (" + std::to_string(total_weight) + ")\n";
      service_counter++;

      int backend_counter = 0;
      for (auto backend : *backends) {
        auto backend_json = reinterpret_cast<json::JsonObject *>(backend);
        int weight = static_cast<json::JsonDataValue *>(backend_json->at(json::JSON_KEYS::WEIGHT))->number_value;
        std::string backend_address = static_cast<json::JsonDataValue *>(backend_json->at(json::JSON_KEYS::ADDRESS))->string_value;
        std::string backend_status = static_cast<json::JsonDataValue *>(backend_json->at(json::JSON_KEYS::STATUS))->string_value;
        int backend_port = static_cast<json::JsonDataValue *>(backend_json->at(json::JSON_KEYS::PORT))->number_value;
        double response_time = static_cast<json::JsonDataValue *>(backend_json->at(json::JSON_KEYS::RESPONSE_TIME))->double_value;
        int connections = static_cast<json::JsonDataValue *>(backend_json->at(json::JSON_KEYS::CONNECTIONS))->number_value;

        buffer += "      " + std::to_string(backend_counter) + ". Backend " + backend_address + ":" + std::to_string(backend_port) + " " + backend_status + " (" + std::to_string(weight) + " " + conversionHelper::to_string_with_precision(response_time) + ") alive (" + std::to_string(connections) + ")\n";
        backend_counter++;
      }

      auto sessions = static_cast<json::JsonArray *>(service_json->at(json::JSON_KEYS::SESSIONS));
      int session_counter = 0;
      for (auto session : *sessions) {
        auto session_json = reinterpret_cast<json::JsonObject *>(session);
        std::string session_id = static_cast<json::JsonDataValue *>(session_json->at(json::JSON_KEYS::ID))->string_value;
        int session_backend = static_cast<json::JsonDataValue *>(session_json->at(json::JSON_KEYS::BACKEND_ID))->number_value;
        buffer += "      " + std::to_string(session_counter) + ". Session " + session_id + " -> " + std::to_string(session_backend-1) + "\n";
        session_counter++;
      }

  }

  std::cout << buffer << std::endl;
}
