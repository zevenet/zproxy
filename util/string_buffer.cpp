//
// Created by abdess on 4/5/18.
//
#include "string_buffer.h"
StringBuffer::StringBuffer() :buffer(){

}
StringBuffer &StringBuffer::operator<<(char const *s) {
  buffer += s;
  return *this;
}

StringBuffer &StringBuffer::operator<<(int i) {
  buffer += std::to_string(i);
  return *this;
}
StringBuffer &StringBuffer::operator<<(std::string const &s) {
  buffer +=s;
  return *this;
}
StringBuffer &StringBuffer::operator<<(StringBuffer const &s) {
  *this << s.string();
  return *this;
}
std::string const &StringBuffer::string() const {
  return buffer;
}
void StringBuffer::erase(unsigned int end) {
  buffer.erase(buffer.begin(), buffer.begin() + end);
}
