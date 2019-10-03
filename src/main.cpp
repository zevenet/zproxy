#include <csetjmp>
#include <csignal>
#include "config/config.h"
#include "ctl/ControlManager.h"
#include "debug/backtrace.h"
#include "stream/listener.h"
#include "util/system.h"

static jmp_buf jmpbuf;

// Log initilization
std::mutex Debug::log_lock;
int Debug::log_level = 6;
int Debug::log_facility = -1;

std::map<std::thread::id,thread_info> Debug::log_info;

std::shared_ptr<SystemInfo> SystemInfo::instance = nullptr;

void cleanExit() { closelog(); }

void handleInterrupt(int sig) {

  Debug::logmsg(LOG_NOTICE, "[%s] received", ::strsignal(sig));
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
    case SIGUSR1: //Release free heap memory
      ::malloc_trim(0);
      break;
    default: {
      //  ::longjmp(jmpbuf, 1);
    }
  }
}

int main(int argc, char *argv[]) {
  Debug::init_log_info();
  debug::EnableBacktraceOnTerminate();
  Listener listener;
  auto control_manager = ctl::ControlManager::getInstance();
  if (setjmp(jmpbuf)) {
    // we are in signal context here
    control_manager->stop();
    listener.stop();  
    exit(EXIT_SUCCESS);
  }

  ::openlog("ZHTTP", LOG_PERROR | LOG_CONS | LOG_PID | LOG_NDELAY, LOG_DAEMON);
  Config config;
  Debug::logmsg(LOG_NOTICE, "zhttp starting...");
  config.parseConfig(argc, argv);  
  Debug::log_level = config.listeners->log_level;
  Debug::log_facility = config.log_facility;

  // Syslog initialization
  if (config.daemonize) {
    if (!Environment::daemonize()) {
      Debug::logmsg(LOG_ERR,"error: daemonize failed\n");
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

  if(!listener.init(config.listeners[0])){
    Debug::LogInfo("Error initializing listener socket", LOG_ERR);
    return EXIT_FAILURE;
  }

  listener.start();
  std::this_thread::sleep_for(std::chrono::seconds(1));
  cleanExit();
  return EXIT_SUCCESS;
}
