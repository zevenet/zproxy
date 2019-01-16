//
// Created by abdess on 10/2/18.
//
#pragma once

//#include "gmock/gmock-matchers.h"
#include <string>
#include "../../src/ctl/observer.h"
#include "../../src/debug/Debug.h"
#include "gtest/gtest.h"

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
    Debug::logmsg(LOG_DEBUG, "%d received command", id);
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
      Debug::LogInfo("Yielding result from: " + std::to_string(data.get().i));
    }
    return static_cast<int>(res.size());
  }

  void onResponseReady(CtlObserver<Task, Result> &obj, Result arg) override {}

  void onAttach(CtlObserver<Task, Result> &obj) override {
    Debug::LogInfo("Attached student id: " +
               std::to_string(dynamic_cast<Student *>(&obj)->id));
  }
};

TEST(IObserver, IObserver1) {
  Debug::LogInfo("Starting Observer test");
  std::vector<Student *> students;
  Teacher teacher;
  int num_student = 20;
  for (int i = 0; i < num_student; i++) {
    Student *student = new Student(i);
    teacher.attach(*student);
    students.push_back(student);
  }
  auto res = teacher.run();
  Debug::LogInfo("Result " + std::to_string(res));
  ASSERT_TRUE(res == num_student);
}
