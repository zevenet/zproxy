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
