#pragma  once

#include <gmock/gmock-matchers.h>
#include <gtest/gtest.h>
#include <cmath>

using namespace testing;

double square_root(double val) {
  if (val < 0) exit(-1);
  return sqrt(val);
}

TEST(basictest, zhttptest) {
  EXPECT_EQ(1, 1);
  ASSERT_THAT(0, Eq(0));

}
