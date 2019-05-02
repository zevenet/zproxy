//
// Created by abdess on 1/11/19.
//
#pragma once
#include <atomic>

template <typename T>
class Counter
{
    bool decrement__;
public:

    Counter(bool decrement = true): decrement__(decrement)
  {
    count++;
  }
  virtual ~Counter()
  {
      if(decrement__)
        count--;
  }
  static std::atomic<int> count;

  static std::atomic<int> established;

  void onConnect(){
    established++;
  }
  void onDisconect(){
    --established;
  }
};

template <typename T> std::atomic<int> Counter<T>::count( 0 );
template <typename T> std::atomic<int> Counter<T>::established( 0 );


#define DEFINE_OBJECT_COUNTER(ObjectName) \
    struct ObjectName:Counter<ObjectName>{ \
    ObjectName():Counter<ObjectName>(false){}};
