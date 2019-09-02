#include "../../src/debug/Debug.h"
#include "t_config.h"
#include "t_control_manager.h"
#include "t_crypto.h"
#include "t_epoll_manager.h"
#include "t_http_parser.h"
#include "t_json.h"
#include "t_observer.h"
#include "t_timerfd.h"
#include "t_compression.h"
#include "tst_basictest.h"
#include "t_sslcontext.h"
#include "t_cache_storage.h"
std::mutex Debug::log_lock;
int Debug::log_level = 8;
int Debug::log_facility = -1;

int main(int argc, char *argv[]) {
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
