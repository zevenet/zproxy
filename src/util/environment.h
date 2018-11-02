//
// Created by abdess on 9/28/18.
//
#pragma once

#include "../debug/Debug.h"
#include <grp.h>
#include <pwd.h>
#include <string>
#include <sys/stat.h>
#include <unistd.h>

class Environment {

public:
  static bool setFileUserName(const std::string &user_name,
                              const std::string &file_name) {

    if (!user_name.empty()) {
      struct passwd *pw;

      if ((pw = ::getpwnam(user_name.c_str())) == NULL) {
        Debug::logmsg(LOG_ERR, "no such user %s - aborted", user_name.c_str());
        return false;
      }
      if (::chown(file_name.c_str(), pw->pw_uid, -1)) {
        Debug::logmsg(LOG_ERR, "chown error on control socket - aborted (%s)",
                      strerror(errno));
        return false;
      }
      return true;
    }
    return false;
  }

  static bool setFileGroupName(const std::string &group_name,
                               const std::string &file_name) {
    if (!group_name.empty()) {
      struct group *gr;
      if ((gr = ::getgrnam(group_name.c_str())) == NULL) {
        Debug::logmsg(LOG_ERR, "no such group %s - aborted",
                      group_name.c_str());
        return false;
      }
      if (::chown(file_name.c_str(), -1, gr->gr_gid)) {
        Debug::logmsg(LOG_ERR, "chown error on control socket - aborted (%s)",
                      strerror(errno));
        return false;
      }
      return true;
    }
    return false;
  }

  static bool setFileUserMode(long user_mode, const std::string &file_name) {
    if (::chmod(file_name.c_str(), user_mode)) {
      Debug::logmsg(LOG_ERR, "chmod error on control socket - aborted (%s)",
                    strerror(errno));
      return false;
    }
    return true;
  }

  static bool setUid(const std::string &user) {
    if (!user.empty()) {
      struct passwd *pw;
      if ((pw = ::getpwnam(user.c_str())) == NULL) {
        Debug::logmsg(LOG_ERR, "no such user %s - aborted", user.c_str());
        return false;
      }
      auto user_id = pw->pw_uid;
      if (::setuid(user_id) || seteuid(user_id)) {
        Debug::logmsg(LOG_ERR, "setuid: %s - aborted", strerror(errno));
        return false;
      }
      return true;
    }
    return false;
  }

  static bool setGid(const std::string &group_name) {
    if (!group_name.empty()) {
      struct group *gr;
      if ((gr = ::getgrnam(group_name.c_str())) == NULL) {
        Debug::logmsg(LOG_ERR, "no such group %s - aborted",
                      group_name.c_str());
        return false;
      }
      auto group_id = gr->gr_gid;
      if (::setgid(group_id) || setegid(group_id)) {
        Debug::logmsg(LOG_ERR, "setgid: %s - aborted", strerror(errno));
        return false;
      }
      return true;
    }
    return false;
  }

  static bool createPidFile(const std::string &pid_file_name, int pid = -1) {
    auto pid_file_hl = ::fopen(pid_file_name.c_str(), "wt");
    if (pid_file_hl != NULL) {
      fprintf(pid_file_hl, "%d\n", pid != -1 ? pid : getpid());
      fclose(pid_file_hl);
      return true;
    } else
      logmsg(LOG_NOTICE, "Create \"%s\": %s", pid_file_name.c_str(),
             strerror(errno));
    return false;
  }

  static bool setChrootRoot(const std::string &chroot_path) {
    if (!chroot_path.empty()) {
      if (::chroot(chroot_path.c_str())) {
        Debug::logmsg(LOG_ERR, "chroot: %s - aborted", strerror(errno));
        return false;
      }
      if (chdir("/")) {
        Debug::logmsg(LOG_ERR, "chroot/chdir: %s - aborted", strerror(errno));
        return false;
      }
      return true;
    }
    return false;
  }
};
