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

#include <csetjmp>
#include <csignal>
#include "config/config.h"
#include "config/global.h"
#include "ctl/control_manager.h"
#include "debug/backtrace.h"
#include "stream/listener_manager.h"
#include "util/system.h"

static jmp_buf jmpbuf;

// Default Log initilization
int Logger::log_level = 5;
int Logger::log_facility = LOG_DAEMON;

std::shared_ptr<SystemInfo> SystemInfo::instance = nullptr;




void cleanExit() { closelog(); }

void handleInterrupt(int sig) {
  Logger::logmsg(LOG_NOTICE, "[%s] received", ::strsignal(sig));
  switch (sig) {
    case SIGINT:
    case SIGHUP:
    case SIGTERM: {
      auto cm = ctl::ControlManager::getInstance();
      cm->stop();
      break;
    }
    case SIGABRT:
    case SIGSEGV: {
      debug::printBackTrace();
      std::exit(EXIT_FAILURE);
    }
    case SIGUSR1:  // Release free heap memory
      ::malloc_trim(0);
      break;
    default: {
      //  ::longjmp(jmpbuf, 1);
    }
  }
}

int main(int argc, char *argv[]) {
  debug::EnableBacktraceOnTerminate();

  ListenerManager listener;
  auto control_manager = ctl::ControlManager::getInstance();
  if (setjmp(jmpbuf)) {
    // we are in signal context here
    control_manager->stop();
    listener.stop();
    exit(EXIT_SUCCESS);
  }

  ::openlog("zproxy", LOG_PERROR | LOG_CONS | LOG_PID | LOG_NDELAY, LOG_DAEMON);
  Config config;
  Logger::logmsg(LOG_NOTICE, "zproxy starting...");
  auto start_options = global::StartOptions::parsePoundOption(argc,argv, true);
  auto parse_result = config.init(*start_options);
  if(!parse_result){
    Logger::logmsg(LOG_ERR,"Error parsing configuration file %s",
        start_options->conf_file_name.data());
    std::exit(EXIT_FAILURE);
  }

  if(start_options->check_only ){
    std::exit(EXIT_SUCCESS);
  }

  Logger::log_level = config.listeners->log_level;
  Logger::log_facility = config.log_facility;

  config.setAsCurrent();

  // Syslog initialization
  if (config.daemonize) {
    if (!Environment::daemonize()) {
      Logger::logmsg(LOG_ERR, "error: daemonize failed\n");
      closelog();
      return EXIT_FAILURE;
    }
  }

  //  /* block all signals. we take signals synchronously via signalfd */
  //  sigset_t all;
  //  sigfillset(&all);
  //  sigprocmask(SIG_SETMASK,&all,NULL);

  ::signal(SIGPIPE, SIG_IGN);
  ::signal(SIGINT, handleInterrupt);
  ::signal(SIGTERM, handleInterrupt);
  ::signal(SIGABRT, handleInterrupt);
  ::signal(SIGHUP, handleInterrupt);
  ::signal(SIGSEGV, handleInterrupt);
  ::signal(SIGUSR1, handleInterrupt);
  ::umask(077);
  ::srandom(static_cast<unsigned int>(::getpid()));
  Environment::setUlimitData();

  /* record pid in file */
  if (!config.pid_name.empty()) {
    Environment::createPidFile(config.pid_name, ::getpid());
  }
  /* chroot if necessary */
  if (!config.root_jail.empty()) {
    Environment::setChrootRoot(config.root_jail);
  }

  /*Set process user and group*/
  if (!config.user.empty()) {
    Environment::setUid(std::string(config.user));
  }

  if (!config.group.empty()) {
    Environment::setGid(std::string(config.group));
  }

  if (!config.ctrl_name.empty() || !config.ctrl_ip.empty()) {
    control_manager->init(config);
    control_manager->start();
  }

  for (auto listener_conf = config.listeners; listener_conf != nullptr;
       listener_conf = listener_conf->next) {
    if (!listener.init(std::shared_ptr<ListenerConfig>(listener_conf))) {
      Logger::LogInfo("Error initializing listener socket", LOG_ERR);
      return EXIT_FAILURE;
    }
  }

  listener.start();
  std::this_thread::sleep_for(std::chrono::seconds(1));
  cleanExit();
  return EXIT_SUCCESS;
}
