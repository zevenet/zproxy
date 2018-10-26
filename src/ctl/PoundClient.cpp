//
// Created by abdess on 9/28/18.
//
#include "PoundClient.h"

bool PoundClient::trySetTargetId(int &target_id, char *possible_value) {
  if (possible_value)  // thorow error and show help
    target_id = std::atoi(possible_value);
  else
    return false;
  return true;
}

void PoundClient::trySetAllTargetId(char *argv[], int &option_index) {
  // TODO: Fix reverse parsing
  int to_consume = 2;
  int next_index = option_index + to_consume;
  switch (ctl_command_subject) { /*Intentional fallthrough*/
    case CTL_SUBJECT::SESSION:
      if (ctl_command == CTL_ACTION::ADD_SESSION) {
        to_consume++;
        next_index++;
      }
    case CTL_SUBJECT::BACKEND: {
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
  // 1. connect to zhttp daemon depending on interface mode selected
  // 2. compose a http request
  // 3. print result in pound format
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

  if (ctl_command == CTL_ACTION::NONE) {
    show_usage("No action specified");
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
  return true;
}
