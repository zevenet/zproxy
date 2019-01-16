//
// Created by abdess on 5/10/18.
//
#pragma once

#define LIKELY(x) __builtin_expect((x), 1)
#define UNLIKELY(x) __builtin_expect((x), 0)

template<typename T, typename U>
std::unique_ptr<T> make_unique(U&& u)
{
  return std::unique_ptr<T>(new T(std::forward<U>(u)));
}

template<typename T>
std::unique_ptr<T> make_unique()
{
  return std::unique_ptr<T>(new T());
}