//
// Created by abdess on 4/15/18.
//

#include <cstring>
#include <iostream>
#include "test_runner.h"
#include "../util/string_buffer.h"

#define  PRINT_INFO \
std::cout << "String buffer size " << sb.string().size() << std::endl;\
std::cout << "String buffer length " << sb.string().length() << std::endl;\
std::cout << sb.string() << std::endl;

void test_runner::test_stringBuffer() {
  const char *data =
      "todo esto es una puebas de masdsdf sadflksadjf laksjdf jsdklf jalskdjflañksdjflkasjdflkajsdlfk jaslkdjflaksdjfa sdfkasjdflkjasdlfkjaslkdfjlaksdjflkasjdflkajsdlkfjaslkdf k kajsd fkjaskldf aj sdfkljasklfka sdf a ksdjfkl asdfkla sdfkl asdlkf askldjf kadflka sdf ad f a";

  std::cout << "buffer size " << ::strlen(data) << std::endl;
  StringBuffer sb;
  PRINT_INFO
  sb << data;
  PRINT_INFO
  sb.erase(40);
  PRINT_INFO
  sb << "Esto es el fin de todo";
  PRINT_INFO

  std::cout << strlen(sb.string().c_str()) << std::endl;

}
