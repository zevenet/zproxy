//
// Created by abdess on 30/8/19.
//

#pragma once

#include <functional>
#include <string>
#include <execinfo.h>
#include "Debug.h"
#include "../util/utils.h"
#include <sys/resource.h>
#include <cassert>

namespace debug {
static void printBackTrace(int max_stack_size = 100) {
  void *frames[max_stack_size];
  int frame_count = ::backtrace(frames, max_stack_size);
  char **symbols = backtrace_symbols(frames, frame_count);
  for (int frame_idx = 1; frame_idx < frame_count; ++frame_idx) {
    if (symbols) {
      Debug::logmsg(LOG_ERR, "** %d/%lu ** %s ", frame_idx, frame_count - 1, symbols[frame_idx]);
    } else {
      Debug::logmsg(LOG_ERR, "** %d/%lu ** %s ", frame_idx, frame_count - 1, frames[frame_idx]);
    }
  }
}

// enable core dumps for debug builds on crash
static void enableCoreDump(){
  struct rlimit core_limit = {RLIM_INFINITY, RLIM_INFINITY};
  assert(setrlimit(RLIMIT_CORE, &core_limit) == 0);
}

static void EnableBacktraceOnTerminate() {
  std::set_terminate([]() {
    printBackTrace();
  });
}
}
