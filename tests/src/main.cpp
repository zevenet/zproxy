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
#include "../../src/debug/logger.h"
#ifdef ENABLE_ON_FLY_COMRESSION
#include "t_compression.h"
#endif
#include "t_config.h"
#include "t_control_manager.h"
#include "t_crypto.h"
#include "t_epoll_manager.h"
#include "t_http_parser.h"
#include "t_json.h"
#include "t_observer.h"
#include "t_sslcontext.h"
#include "t_timerfd.h"
#include "tst_basictest.h"
#include "t_priority.h"

#if CACHE_ENABLED
//#include "t_cache.h"
//#include "t_cache_storage.h"
#endif

int Logger::log_level = 8;
int Logger::log_facility = -1;

int main(int argc, char *argv[]) {
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
