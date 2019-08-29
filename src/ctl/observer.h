#pragma once

#include <future>
#include <vector>

template <typename T, typename IResponse>
class CtlObserver {
 public:
  CtlObserver() = default;
  virtual ~CtlObserver() = default;
  virtual IResponse handleTask(T &arg) = 0;
  static IResponse handle(T arg, CtlObserver<T, IResponse> &obj) {
    return obj.handleTask(arg);
  }
  virtual bool isHandler(T &arg) = 0;
};
template <typename T, typename IResponse>
class CtlNotify {
 protected:
  std::vector<CtlObserver<T, IResponse> *> observers;

 public:
  void attach(CtlObserver<T, IResponse> &listener) {
    observers.push_back(&listener);
    onAttach(listener);
  }
  void deAttach(CtlObserver<T, IResponse> &listener) {
    // TODO:: how to do this    observers.erase(&listener);
  }

  std::vector<std::future<IResponse>> notify(T arg, bool lazy_eval = false) {
    std::vector<std::future<IResponse>> result_future;
    for (auto receiver : observers) {
      if (receiver->isHandler(arg)) {
        result_future.push_back(
            std::async(lazy_eval ? std::launch::deferred : std::launch::async,
                       receiver->handle, arg, std::ref(*receiver)));
      }
    }
    return result_future;
  }

  virtual void onResponseReady(CtlObserver<T, IResponse> &obj, IResponse arg){};
  virtual void onAttach(CtlObserver<T, IResponse> &listener) {}

 public:
  CtlNotify() = default;
  virtual ~CtlNotify() = default;
};
