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

#include "../../src/event/epoll_manager.h"
#include "../../src/event/timer_fd.h"
#include "testserver.h"
#include "gtest/gtest.h"
#include <thread>

static void run_loop_server(bool testing){
  ServerHandler server;
  server.setUp("127.0.0.1", 9999);
 while (testing) {
      if(server.loopOnce(5000) <= 0)
        break;
    }
}

 static void run_loop_client(bool testing){
   ClientHandler client;
   client.setUp(100, "127.0.0.1", 9999);
   while(testing) {
       if (client.loopOnce(5000) <= 0)
         break;
     }
 }
TEST(EpollManagerTest, EpollManagerEvents1) {

  std::thread t1 (run_loop_server, true);
    std::this_thread::sleep_for(std::chrono::milliseconds(400));
    run_loop_client(true);
    t1.join();
}

TEST(EpollManagerTest, EpollManagerBasicOp) {
  ServerHandler e;
  TimerFd t_fd;
  bool success;

  /* Check that we are not getting errors when a file descriptor is first time added. */
  success = e.addFd(t_fd.getFileDescriptor(), EVENT_TYPE::READ, EVENT_GROUP::SERVER);
  EXPECT_TRUE(errno != EEXIST && success);

  /* Check that we get EEXIST error if the file descriptor have been already added. */
  success = e.addFd(t_fd.getFileDescriptor(), EVENT_TYPE::READ, EVENT_GROUP::SERVER);
  EXPECT_TRUE(errno == EEXIST && success);

  /* Check that we are cannot add a not valid file descriptor. */
  success = e.addFd(-1, EVENT_TYPE::READ, EVENT_GROUP::SERVER);
  EXPECT_FALSE(success);
  EXPECT_TRUE(errno == EBADF);

  /* Check that we are not getting errors when an existing file descriptor is updated. */
  success = e.updateFd(t_fd.getFileDescriptor(), EVENT_TYPE::READ, EVENT_GROUP::SERVER);
  EXPECT_TRUE(errno != ENOENT && success);

  /* Check that we are cannot update a not valid file descriptor. */
  success = e.updateFd(-1, EVENT_TYPE::READ, EVENT_GROUP::SERVER);
  EXPECT_FALSE(success);
  EXPECT_TRUE(errno == EBADF);

  /* Check that we are not getting errors when an existing file descriptor is deleted. */
  success = e.deleteFd(t_fd.getFileDescriptor());
  EXPECT_TRUE(errno != ENOENT && success);

  /* Check that we get ENOENT error if the file descriptor have not been already added. */
  success = e.deleteFd(t_fd.getFileDescriptor());
  EXPECT_TRUE(success);
  EXPECT_TRUE(errno == ENOENT);

  /* Check that we get ENOENT error if the file descriptor have not been already added. */
  success = e.updateFd(t_fd.getFileDescriptor(), EVENT_TYPE::READ, EVENT_GROUP::SERVER);
  EXPECT_TRUE(success);
  EXPECT_TRUE(errno == ENOENT);

}
