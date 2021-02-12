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

#include "../../zcutils/zcutils.h"
#include <future>
#include <vector>

template <typename T, typename IResponse>
class CtlObserver {
 public:
  uint64_t __id__;
  CtlObserver() {
    static uint64_t id;
    id++;
    this->__id__ = id;
  }
  virtual ~CtlObserver() = default;
  virtual IResponse handleTask(T &arg) = 0;
  static IResponse handle(T arg, CtlObserver<T, IResponse> &obj) { return obj.handleTask(arg); }
  virtual bool isHandler(T &arg) = 0;
  bool operator==(const CtlObserver& rhs) {
    return this->__id__ == rhs.__id__;
  }
};
template <typename T, typename IResponse>
class CtlNotify {
 protected:
  std::vector<CtlObserver<T, IResponse> *> observers;

 public:
  void attach(CtlObserver<T, IResponse> &listener) {
    //    Logger::logmsg(LOG_DEBUG, "Attaching id: %d observer",
    //    listener.__id__);
    observers.push_back(&listener);
    onAttach(listener);
  }
  void deAttach(CtlObserver<T, IResponse> &listener) {
    for (auto it = observers.begin(); it != observers.end();) {
      if(*it == nullptr){
        Logger::logmsg(LOG_ERR, "Removing null observer");
        it = observers.erase(it);
        continue;
      }else if(*(*it) == listener){
        //        Logger::logmsg(LOG_DEBUG, "deAttaching id: %d observer",
        //        listener.__id__);
        it = observers.erase(it);
        break;
      }
      it++;
    }
  }

  std::vector<std::future<IResponse>> notify(T arg, bool lazy_eval = false) {
    std::vector<std::future<IResponse>> result_future;
    for (auto it = observers.begin(); it != observers.end();) {

      if(*it == nullptr){
        zcutils_log_print(LOG_DEBUG, "%s():%d: observer not found, removing", __FUNCTION__, __LINE__);
        it = observers.erase(it);
        continue;
      }
      if ((*it)->isHandler(arg)) {
        result_future.push_back(std::async(lazy_eval ? std::launch::deferred : std::launch::async, (*it)->handle,
                                           arg, std::ref(*(*it))));
      }
      it++;
    }
    return result_future;
  }

  virtual void onResponseReady(CtlObserver<T, IResponse> &obj, IResponse arg){};
  virtual void onAttach(CtlObserver<T, IResponse> &listener) {}

 public:
  CtlNotify() = default;
  virtual ~CtlNotify() = default;
};
