//
// Created by abdess on 5/7/18.
//

#pragma once

#include "descriptor.h"
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/signalfd.h>
#include <unistd.h>

class SignalFd : public Descriptor {

public:
  sigset_t mask{};
  SignalFd() {}
  bool init() {
    sigemptyset(&mask);
    sigaddset(&mask, SIGTERM);
    sigaddset(&mask, SIGINT);
    sigaddset(&mask, SIGQUIT);
    sigaddset(&mask, SIGHUP);
    sigaddset(&mask, SIGPIPE);
    /* Block signals so that they aren't handled
                  according to their default dispositions */
    if (sigprocmask(SIG_BLOCK, &mask, NULL) == -1) {
      Debug::logmsg(LOG_ERR, "sigprocmask () failed");
      return false;
    }
    fd_ = signalfd(-1, &mask, 0);
    if (fd_ < 0) {
      Debug::logmsg(LOG_ERR, "sigprocmask () failed");
      return false;
    }
    return true;
  }
  uint32_t getSignal() {
    ssize_t s;
    signalfd_siginfo fdsi{};
    s = read(fd_, &fdsi, sizeof(struct signalfd_siginfo));
    if (s != sizeof(struct signalfd_siginfo)) {
      Debug::logmsg(LOG_ERR, "sigprocmask () failed");
      return false;
    }
    return fdsi.ssi_signo;
  }
};
