#include "tst_basictest.h"
#include "t_config.h"
#include "t_http_parser.h"
#include "../src/debug/Debug.h"

std::mutex Debug::log_lock;
int Debug::log_level = 8;
int Debug::log_facility = -1;

int main(int argc, char *argv[]) {
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
