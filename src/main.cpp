#include "config/config.h"
#include "ctl/ControlManager.h"
#include "stream/listener.h"
#include "util/system.h"
#include <csignal>
#include <sys/resource.h>

// Log initilization
std::mutex Debug::log_lock;
int Debug::log_level = 6;
int Debug::log_facility = -1;

void cleanExit() { closelog(); }

void handleInterrupt(int sig) {
  // stop listener
  exit(EXIT_FAILURE);
}

void redirectLogOutput(std::string name, std::string chroot_path,
                       std::string outfile, std::string errfile,
                       std::string infile) {
  if (chroot_path.empty()) {
    chroot_path = "/";
  }
  if (name.empty()) {
    name = "zhttp";
  }
  if (infile.empty()) {
    infile = "/dev/null";
  }
  if (outfile.empty()) {
    outfile = "/dev/null";
  }
  if (errfile.empty()) {
    errfile = "/dev/null";
  }
  // new file permissions
  umask(0);
  // change to path directory
  chdir(chroot_path.c_str());
  // Carefull Close all open file descriptors
  //  int fd;
  //  for (fd = ::sysconf(_SC_OPEN_MAX); fd > 0; --fd) {
  //    close(fd);
  //  }
  // reopen stdin, stdout, stderr
  stdin = fopen(infile.c_str(), "r");
  stdout = fopen(outfile.c_str(), "w+");
  stderr = fopen(errfile.c_str(), "w+");
}

bool daemonize() {
  pid_t child;
  if ((child = fork()) < 0) {
    std::cerr << "error: failed fork\n";
    exit(EXIT_FAILURE);
  }
  if (child > 0) { // parent
    //    std::this_thread::sleep_for(std::chrono::milliseconds(1000)); wait for
    //    childs to starts
    exit(EXIT_SUCCESS);
  }
  if (setsid() < 0) { // failed to become session leader
    std::cerr << "error: failed setsid\n";
    exit(EXIT_FAILURE);
  }

  // catch/ignore signals
  signal(SIGCHLD, SIG_IGN);
  signal(SIGHUP, SIG_IGN);

  // fork second time
  if ((child = fork()) < 0) { // failed fork
    std::cerr << "error: failed fork\n";
    exit(EXIT_FAILURE);
  }
  if (child > 0) {
    exit(EXIT_SUCCESS);
  }
  return true;
}

int main(int argc, char *argv[]) {
  Config config;
  // inicializar la interfaz de control (poundctl)
  // ControlInterface control_interface;
  Debug::logmsg(LOG_NOTICE, "zhttp starting...");
  config.parseConfig(argc, argv);
  Debug::log_level = config.listeners->log_level;
  Debug::log_facility = config.log_facility;
  openlog("ZHTTP", LOG_PERROR | LOG_CONS | LOG_PID | LOG_NDELAY, LOG_DAEMON);
  // Syslog initialization
  if (config.daemonize) {
    if (!daemonize()) {
      std::cerr << "error: daemonize failed\n";
      exit(EXIT_FAILURE);
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

  ::umask(077);
  ::srandom(static_cast<unsigned int>(::getpid()));

  // Increase num file descriptor ulimit
  // TODO:: take outside main initialization
  Debug::LogInfo("System info:");
  Debug::LogInfo("\tL1 Data cache size: " +
      std::to_string(SystemInfo::data()->getL1DataCacheSize()), LOG_DEBUG);
  Debug::LogInfo("\t\tCache line size: " +
      std::to_string(SystemInfo::data()->getL1DataCacheLineSize()), LOG_DEBUG);
  Debug::LogInfo("\tL2 Cache size: " +
      std::to_string(SystemInfo::data()->getL2DataCacheSize()), LOG_DEBUG);
  Debug::LogInfo("\t\tCache line size: " +
      std::to_string(SystemInfo::data()->getL2DataCacheLineSize()), LOG_DEBUG);
  rlimit r{};
  ::getrlimit(RLIMIT_NOFILE, &r);
  Debug::LogInfo("\tRLIMIT_NOFILE\tCurrent " + std::to_string(r.rlim_cur), LOG_DEBUG);
  Debug::LogInfo("\tRLIMIT_NOFILE\tMaximum " + std::to_string(::sysconf(_SC_OPEN_MAX)), LOG_DEBUG);
  if (r.rlim_cur != r.rlim_max) {
    r.rlim_cur = r.rlim_max;
    if (setrlimit(RLIMIT_NOFILE, &r) == -1) {
      Debug::logmsg(LOG_ERR, "\tsetrlimit failed ");
      return EXIT_FAILURE;
    }
  }
  ::getrlimit(RLIMIT_NOFILE, &r);
  Debug::LogInfo("\tRLIMIT_NOFILE\tSetCurrent " + std::to_string(r.rlim_cur), LOG_DEBUG);

  /*Set process user and group*/
  if (config.user != nullptr)
    Environment::setUid(std::string(config.user));
  if (config.group != nullptr)
    Environment::setGid(std::string(config.group));


  auto control_manager = ctl::ControlManager::getInstance();
  if (config.ctrl_name != nullptr) {
    control_manager->init(config);
    control_manager->start();
  }

  Listener listener;
  if(!listener.init(config.listeners[0])){
    Debug::LogInfo("Error initializing listener socket", LOG_ERR);
    exit(EXIT_FAILURE);
  }
  //  listener.init("127.0.0.1", 9999);
  listener.start();
  exit(EXIT_SUCCESS);
}
