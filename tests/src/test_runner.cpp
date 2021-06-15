/*
 *    Zevenet zproxy Load Balancer Software License
 *    This file is part of the Zevenet zproxy Load Balancer software package.
 *
 *    Copyright (C) 2019-today ZEVENET SL, Sevilla (Spain)
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Affero General Public License as
 *    published by the Free Software Foundation, either version 3 of the
 *    License, or any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Affero General Public License for more details.
 *
 *    You should have received a copy of the GNU Affero General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#pragma once

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
