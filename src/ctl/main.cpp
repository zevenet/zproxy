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
#include "pound_client.h"
#include <cstdlib>
#include <iostream>

#define POUND_CTL_MODE 1

std::mutex Logger::log_lock;
int Logger::log_level = 8;
int Logger::log_facility = -1;

std::map<std::thread::id, thread_info> Logger::log_info;

int main(int argc, char *argv[]) {
  PoundClient client;

  return client.init(argc, argv) ? EXIT_SUCCESS : EXIT_FAILURE;
}
