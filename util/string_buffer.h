//
// Created by abdess on 4/5/18.
//

#ifndef NEW_ZHTTP_STREAM_BUFFER_H
#define NEW_ZHTTP_STREAM_BUFFER_H
#include <string>

class StringBuffer {
 public:
  StringBuffer();
  StringBuffer& operator<<(char const* s);
  StringBuffer& operator<<(int i);
  StringBuffer& operator<<(std::string const& s);
  StringBuffer& operator<<(StringBuffer const& s);
  std::string const& string() const;
  void erase(unsigned int end);

 private:
  std::string buffer;
};

#endif //NEW_ZHTTP_STREAM_BUFFER_H
