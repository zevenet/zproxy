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

#pragma once

#include "../util/utils.h"
#include "../../zcutils/zcutils.h"
#include <cassert>
#include <cxxabi.h> // for __cxa_demangle
#include <dlfcn.h>  // for dladdr
#include <execinfo.h>
#include <execinfo.h> // for backtrace
#include <functional>
#include <sstream>
#include <string>
#include <sys/resource.h>

namespace debug {

static std::string addr2line(const std::string &bin, const std::string &address) {
  char cmd[ZCU_DEF_BUFFER_SIZE];
  std::array<char, ZCU_DEF_BUFFER_SIZE> buffer;
  std::string result;
  sprintf(cmd, "addr2line -s -a -p -f -C -e %s %s", bin.c_str(), address.c_str());
  std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd, "r"), pclose);
  if (!pipe) {
    return std::string();
  }
  while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
    result += buffer.data();
  }
  result.erase(std::remove(result.begin(), result.end(), '\n'), result.end());
  auto pos = result.find_first_of(':');
  if (pos != std::string::npos) result = result.substr(pos + 1, result.length());
  return result;
}

static std::string addr2line(const std::string &symbol) {
  std::string bin, addr;
  auto s = symbol.find('(');
  auto e = symbol.find(')');
  if (std::string::npos != s) {
    bin = symbol.substr(0, s);
  }
  if (std::string::npos != e) {
    addr = std::string(symbol.data() + s + 1, e - s - 1);
  }
  // zcutils_log_print(LOG_DEBUG, "%s():%d: [ bin: %s Addr: %s ]", __FUNCTION__, __LINE__, error, bin.data(), addr.data());
  return addr2line(bin, addr);
}

static void printBackTrace(int max_stack_size = 100) {
  void *frames[max_stack_size];
  int frame_count = ::backtrace(frames, max_stack_size);
  char **symbols = backtrace_symbols(frames, frame_count);
  std::ostringstream trace_buf;
  trace_buf << "Backtrace:";
  for (int frame_idx = 1; frame_idx < frame_count; ++frame_idx) {
    trace_buf << "\n** " << frame_idx << "/" << frame_count - 1 << " ** ";
    if (symbols) {
      std::string debug_data = "";
      //#ifdef DEBUG
      debug_data = addr2line(symbols[frame_idx]);
      //#endif
      trace_buf << symbols[frame_idx] << " ** " << debug_data;
    } else {
      trace_buf << frames[frame_idx];
    }
  }
  zcutils_log_print(LOG_DEBUG, "%s():%d: %s", __FUNCTION__, __LINE__, trace_buf.str().data());
}

// enable core dumps for debug builds on crash
static void enableCoreDump() {
  struct rlimit core_limit = {RLIM_INFINITY, RLIM_INFINITY};
  assert(setrlimit(RLIMIT_CORE, &core_limit) == 0);
}

static void EnableBacktraceOnTerminate() {
  std::set_terminate([]() { printBackTrace(); });
}
}  // namespace debug
