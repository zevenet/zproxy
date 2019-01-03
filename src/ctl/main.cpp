
#include <cstdlib>
#include <iostream>
#include "PoundClient.h"

#define POUND_CTL_MODE 1

std::mutex Debug::log_lock;
int Debug::log_level = 8;
int Debug::log_facility = -1;

int main(int argc, char *argv[]) {
  PoundClient client;

  return client.init(argc, argv) ? EXIT_SUCCESS : EXIT_FAILURE;
}
