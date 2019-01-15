//
// Created by abdess on 1/11/19.
//
#pragma once

template <typename T>
class Counter
{
public:

  Counter()
  {
    count++;
  }
  virtual ~Counter()
  {
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

