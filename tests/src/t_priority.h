/*
 *    Zevenet zproxy Load Balancer Software License
 *    This file is part of the Zevenet zproxy Load Balancer software package.
 *
 *    Copyright (C) 2020-today ZEVENET SL, Sevilla (Spain)
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

#include "gtest/gtest.h"

enum class status { up, down, disabled };

struct backend {
  int priority = 1;
  status _status = status::up;
};

// int getCurrentBackendPriority_(std::vector<backend> &backend_set) {
//  int enabled_priority = 1;
//  int first_backend_up_priority = 0;
//  int max_backend_priority = 1;
//  bool done = status::down;
//  for (auto &bck : backend_set) {
//    if (bck.priority > max_backend_priority)
//      max_backend_priority = bck.priority;
//  }
//  // get priority of first backend active with lowest priority
//  for (int priority_index = 1; priority_index <= max_backend_priority &&
//  !done;
//       priority_index++) {  // make sure that every backend has been checked
//    // for the current priority
//    for (auto &bck : backend_set) {
//      if (bck.priority != priority_index) continue;
//      if (bck.active) {
//        first_backend_up_priority = bck.priority;
//        done = status::up;
//        break;
//      }
//    }
//  }
//  // increment priority for every backend not active
//  for (auto &bck : backend_set) {
//    if (bck.priority > first_backend_up_priority) continue;
//    if (!bck.active) {
//      enabled_priority++;
//    }
//  }
//  return enabled_priority;
//}

int getAllowedPriority(std::vector<backend> &backend_set) {
  int backend_down_count = 1;
  std::string res;
  for (auto &bck : backend_set) {
    res += " (" + std::to_string(bck.priority);
    switch (bck._status) {
      case status::up:
        res += ":U) |";
        break;
      case status::down:
        res += ":D) |";
        break;
      case status::disabled:
        res += ":M) |";
        break;
    }
  }
  // get priority of first backend active with lowest priority
  backend_down_count = 1;
  for (int priority_index = 1; priority_index <= backend_down_count;
       priority_index++) {  // make sure that every backend has been checked
                            // for the current priority
    for (auto &bck : backend_set) {
      if (bck.priority == priority_index && bck._status != status::up) {
        backend_down_count++;
      }
    }
  }
  std::cout << " Priority: " << backend_down_count << " >> " << res
            << std::endl;
  return backend_down_count;
}

TEST(Priority, Priority1) {
  std::cout << "\n" << std::endl;
  std::vector<backend> backends_list;
  backends_list.push_back({1, status::up});
  backends_list.push_back({1, status::up});
  backends_list.push_back({2, status::up});
  backends_list.push_back({2, status::up});
  backends_list.push_back({4, status::up});
  backends_list.push_back({4, status::up});
  int expected_priority = 1;
  ASSERT_EQ(getAllowedPriority(backends_list), expected_priority);
}
TEST(Priority, Priority2) {
  std::vector<backend> backends_list;
  backends_list.push_back({1, status::disabled});
  backends_list.push_back({1, status::up});
  backends_list.push_back({2, status::up});
  backends_list.push_back({2, status::up});
  backends_list.push_back({4, status::up});
  backends_list.push_back({4, status::up});
  int expected_priority = 2;
  ASSERT_EQ(getAllowedPriority(backends_list), expected_priority);
}

TEST(Priority, Priority3) {
  std::vector<backend> backends_list;
  backends_list.push_back({1, status::down});
  backends_list.push_back({1, status::down});
  backends_list.push_back({2, status::up});
  backends_list.push_back({2, status::up});
  backends_list.push_back({4, status::up});
  backends_list.push_back({4, status::up});
  int expected_priority = 3;
  ASSERT_EQ(getAllowedPriority(backends_list), expected_priority);
}

TEST(Priority, Priority4) {
  std::vector<backend> backends_list;
  backends_list.push_back({1, status::up});
  backends_list.push_back({1, status::up});
  backends_list.push_back({4, status::down});
  backends_list.push_back({4, status::up});
  int expected_priority = 1;
  ASSERT_EQ(getAllowedPriority(backends_list), expected_priority);
}

TEST(Priority, Priority5) {
  std::vector<backend> backends_list;
  backends_list.push_back({1, status::up});
  backends_list.push_back({1, status::down});
  backends_list.push_back({4, status::down});
  backends_list.push_back({4, status::up});
  int expected_priority = 2;
  ASSERT_EQ(getAllowedPriority(backends_list), expected_priority);
}

TEST(Priority, Priority6) {
  std::vector<backend> backends_list;
  backends_list.push_back({1, status::down});
  backends_list.push_back({1, status::down});
  backends_list.push_back({4, status::down});
  backends_list.push_back({4, status::up});
  int expected_priority = 3;
  ASSERT_EQ(getAllowedPriority(backends_list), expected_priority);
}
TEST(Priority, Priority7) {
  std::vector<backend> backends_list;
  backends_list.push_back({1, status::down});
  backends_list.push_back({1, status::down});
  backends_list.push_back({1, status::down});
  backends_list.push_back({4, status::up});
  backends_list.push_back({4, status::up});
  int expected_priority = 4;
  ASSERT_EQ(getAllowedPriority(backends_list), expected_priority);
}
TEST(Priority, Priority8) {
  std::vector<backend> backends_list;
  backends_list.push_back({1, status::down});
  backends_list.push_back({1, status::down});
  backends_list.push_back({1, status::down});
  backends_list.push_back({1, status::down});
  backends_list.push_back({4, status::down});
  backends_list.push_back({4, status::up});
  int expected_priority = 6;
  ASSERT_EQ(getAllowedPriority(backends_list), expected_priority);
}

TEST(Priority, Priority9) {
  std::vector<backend> backends_list;
  backends_list.push_back({1, status::down});
  backends_list.push_back({3, status::down});
  backends_list.push_back({3, status::up});
  int expected_priority = 2;
  ASSERT_EQ(getAllowedPriority(backends_list), expected_priority);
}
