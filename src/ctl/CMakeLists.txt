
###############################################################################
#
#Zevenet zProxy Load Balancer Software License
#This file is part of the Zevenet zProxy Load Balancer software package.
#
#Copyright (C) 2019-today ZEVENET SL, Sevilla (Spain)
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as
#published by the Free Software Foundation, either version 3 of the
#License, or any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with this program.  If not, see <http:	//www.gnu.org/licenses/>.
#
###############################################################################

cmake_minimum_required(VERSION 3.6)
	project(zproxyctl LANGUAGES CXX)
	set(CMAKE_CXX_STANDARD 17)
	add_executable(zproxyctl main.cpp
	       pound_client.h pound_client.cpp ctl_client.cpp ctl_client.h)
	add_dependencies(zproxyctl l7pcore)
	target_link_libraries(zproxyctl l7pcore)
	install(TARGETS "zproxyctl" DESTINATION bin)
