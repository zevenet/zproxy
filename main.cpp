#include <sys/stat.h>
#include <iostream>
#include <openssl/ssl.h>
#include <csignal>
#include "debug/Debug.h"
#include "stream/listener.h"
#include "config/config.h"
#include <sys/resource.h>

void cleanExit() { closelog(); }
std::mutex Debug::log_lock;
int Debug::log_level;

void handleInterrupt(int sig) {
  // stop listener
  exit(1);
}

int main(int argc, char *argv[]) {
  Debug::log_level = 5;

  Debug::logmsg(LOG_NOTICE, "zhttp starting...");

  ::signal(SIGPIPE, SIG_IGN);
  ::signal(SIGINT, handleInterrupt);
  ::signal(SIGTERM, handleInterrupt);
  ::signal(SIGABRT, handleInterrupt);

  ::umask(077);
  ::srandom(static_cast<unsigned int>(::getpid()));

  // Increase num file descriptor ulimit
  //TODO:: take outside main initialization
  struct rlimit r;
  getrlimit(RLIMIT_NOFILE, &r);
  Debug::Log("RLIMIT_NOFILE\tCurrent " +
      std::to_string(r.rlim_cur));
  Debug::Log("RLIMIT_NOFILE\tMaximum " + std::to_string(r.rlim_max));
  if (r.rlim_cur != r.rlim_max) {
    r.rlim_cur = r.rlim_max * 1000;
    if (setrlimit(RLIMIT_NOFILE, &r) == -1) {
      Debug::logmsg(LOG_ERR, "setrlimit failed ");
      return EXIT_FAILURE;
    }
  }
  getrlimit(RLIMIT_NOFILE, &r);
  Debug::Log("RLIMIT_NOFILE\tSetCurrent " +
      std::to_string(r.rlim_cur));

  /* SSL stuff */
  SSL_load_error_strings();
  SSL_library_init();
  OpenSSL_add_all_algorithms();

  //  l_init();
  //  init_thr_arg();
  //  CRYPTO_set_id_callback(l_id);
  //  CRYPTO_set_locking_callback(l_lock);

  Config config;
  //ControlInterface control_interface;
  config.parseConfig(argc, argv);
  Debug::log_level = config.listeners->log_level;
  Listener listener;
  listener.init(config.listeners[0]);
//  listener.init("127.0.0.1", 9999);
  listener.start();

  return EXIT_SUCCESS;
}
