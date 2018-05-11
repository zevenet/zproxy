//
// Created by abdess on 5/10/18.
//
#pragma once

#define LIKELY(x) __builtin_expect((x), 1)
#define UNLIKELY(x) __builtin_expect((x), 0)