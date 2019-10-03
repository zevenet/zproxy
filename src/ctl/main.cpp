#include <cstdlib>
#include <iostream>
#include "PoundClient.h"

#define POUND_CTL_MODE 1

std::mutex Debug::log_lock;
int Debug::log_level = 8;
int Debug::log_facility = -1;

std::map<std::thread::id,thread_info> Debug::log_info;

int main(int argc, char *argv[]) {
    Debug::init_log_info();
    PoundClient client;

    return client.init(argc, argv) ? EXIT_SUCCESS : EXIT_FAILURE;
}
