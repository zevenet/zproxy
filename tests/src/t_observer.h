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

//#include "gmock/gmock-matchers.h"
#include "../../src/ctl/observer.h"
#include "../../src/debug/logger.h"
#include "gtest/gtest.h"
#include <string>

struct Task {
  std::string data;
};
struct Result {
  int i;
};

class Student : public CtlObserver<Task, Result> {
 public:
  int id;
  Student(int id_) : id(id_){};
  Result handleTask(Task &arg) override {
    Logger::logmsg(LOG_DEBUG, "%d received command", id);
    return {id};
  }
  bool isHandler(Task &arg) override { return true; }
};

class Teacher : public CtlNotify<Task, Result> {
 public:
  int run() {
    auto res = notify({"Who are you?"});
    //    std::this_thread::sleep_for(std::chrono::seconds(5));
    for (auto &data : res) {
      Logger::LogInfo("Yielding result from: " + std::to_string(data.get().i));
    }
    return static_cast<int>(res.size());
  }

  void onResponseReady(CtlObserver<Task, Result> &obj, Result arg) override {}

  void onAttach(CtlObserver<Task, Result> &obj) override {
    Logger::LogInfo("Attached student id: " +
               std::to_string(dynamic_cast<Student *>(&obj)->id));
  }
};

TEST(IObserver, IObserver1) {
  Logger::LogInfo("Starting Observer test");
  std::vector<Student *> students;
  Teacher teacher;
  int num_student = 20;
  for (int i = 0; i < num_student; i++) {
    Student *student = new Student(i);
    teacher.attach(*student);
    students.push_back(student);
  }
  auto res = teacher.run();
  Logger::LogInfo("Result " + std::to_string(res));
  ASSERT_TRUE(res == num_student);
}
