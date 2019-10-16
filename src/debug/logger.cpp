#include "logger.h"

std::map<std::thread::id, thread_info> Logger::log_info;
std::mutex Logger::log_lock;
