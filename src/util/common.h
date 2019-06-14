//
// Created by abdess on 5/10/18.
//
#pragma once

#define LIKELY(x) __builtin_expect((x), 1)
#define UNLIKELY(x) __builtin_expect((x), 0)
#define UNIQUE_NAME_0(a, b) UNIQUE_NAME_I(a, b)
#define UNIQUE_NAME_I(a, b) UNIQUE_NAME_II(~, a ## b)
#define UNIQUE_NAME_II(p, res) res
#define UNIQUE_NAME(base) UNIQUE_NAME_0(base, __COUNTER__)

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