###############################################################################
#
#	 Zevenet zproxy Load Balancer Software License
#	 This file is part of the Zevenet zproxy Load Balancer software package.
#
#	 Copyright (C) 2019-today ZEVENET SL, Sevilla (Spain)
#
#	 This program is free software: you can redistribute it and/or modify
#	 it under the terms of the GNU Affero General Public License as
#	 published by the Free Software Foundation, either version 3 of the
#	 License, or any later version.
#
#	 This program is distributed in the hope that it will be useful,
#	 but WITHOUT ANY WARRANTY; without even the implied warranty of
#	 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	 GNU Affero General Public License for more details.
#
#	 You should have received a copy of the GNU Affero General Public License
#	 along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
cmake_minimum_required(VERSION 3.6)
set(CMAKE_CXX_STANDARD 17)

if (NOT CMAKE_BUILD_TYPE)
	set(CMAKE_BUILD_TYPE RelWithDebInfo)
endif ()
string(TOLOWER ${CMAKE_BUILD_TYPE} CMAKE_BUILD_TYPE)
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")

set(CMAKE_ENABLE_EXPORTS TRUE)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(MAINFOLDER ${PROJECT_SOURCE_DIR})

project(zproxy)
set(PROJECT_VERSION "0.9.3")
set(PROJECT_DESCRIPTION "High-performance multithreaded and event-driven reverse proxy and load balancer")
set(PROJECT_GENERICNAME "zproxy")
set(TARGET_NAME "zproxy")

#options
option(ENABLE_WAF "Compile zproxy using WAF features" ON)
option(DEBUG_ZCU_LOG "Compile with debug messages" ON)
option(BUILD_DOC "Build documentation" OFF)
# debug
option(ENABLE_HEAP_PROFILE "Enable heap profiler, also need tcmalloc to be enabled" OFF)
option(ENABLE_LEAK_SANITIZER "Enable memory leak sanitizer" OFF)
option(ENABLE_ADDRESS_SANITIZER "Enable address sanitizer" OFF)

# get current git info
execute_process(
	COMMAND git log -1 --format=%h
	WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR}
	OUTPUT_VARIABLE GIT_COMMIT_HASH
	OUTPUT_STRIP_TRAILING_WHITESPACE)

add_definitions(-DPROJECT_NAME="zproxy-ng")
add_definitions(-DPROJECT_GENERICNAME="${PROJECT_GENERICNAME}")
add_definitions("-DPROJECT_VERSION=\"${PROJECT_VERSION} (${GIT_COMMIT_HASH})\"")

if (UNIQUE_BUILD_DIRECTORY)
	set(EXECUTABLE_OUTPUT_PATH "${MAINFOLDER}/build/bin")
endif ()

add_subdirectory(zcutils)

set(sources_h
	"include/macro.h"
	"include/list.h"
	"include/jhash.h"
	"include/json.h"
	"include/config.h"
	"include/ctl.h"
	"include/djb_hash.h"
	"include/proxy.h"
	"include/service.h"
	"include/socket.h"
	"include/ssl.h"
	"include/worker.h"
	"include/monitor.h"
	"include/session.h"
	"include/state.h"
	"include/http.h"
	"include/http_log.h"
	"include/http_protocol.h"
	"include/pico_http_parser.h"
	"include/http_parser.h"
	"include/http_request.h"
	"include/http_response.h"
	"include/http_stream.h"
	"include/http_manager.h"
	"include/zproxy.h"
)
set(sources_c
	"src/main.c"
	"src/config.cpp"
	"src/ctl.c"
	"src/ctl_handler.c"
	"src/proxy.c"
	"src/worker.c"
	"src/monitor.c"
	"src/socket.c"
	"src/ssl.c"
	"src/service.c"
	"src/session.c"
	"src/state.cpp"
	"src/json.cpp"
	"src/http.c"
	"src/http_protocol.cpp"
	"src/http_events.cpp"
	"src/pico_http_parser.cpp"
	"src/http_parser.cpp"
	"src/http_request.cpp"
	"src/http_response.cpp"
	"src/http_stream.cpp"
	"src/http_manager.cpp"
)

if (ENABLE_WAF)
	set(sources_h ${sources_h} include/waf.h)
	set(sources_c ${sources_c} src/waf.cpp)
	add_definitions(-DENABLE_WAF)
else ()
	set(sources_h ${sources_h} include/waf_dummy.h)
endif ()

# force to manage sources files as c++
set_source_files_properties(${sources_c} PROPERTIES LANGUAGE CXX )

include_directories(${PROJECT_SOURCE_DIR}/include)
include_directories(${PROJECT_SOURCE_DIR}/zcutils/include)

set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)
find_package(OpenSSL REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_search_module(JANSSON REQUIRED jansson)

# system libs
set(linked_libs "-ldl ${JANSSON_LDFLAGS} -lev -lpcreposix")
if (ENABLE_WAF)
	set(linked_libs "${linked_libs} -lmodsecurity")
endif ()

# gcc flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -m64 -pipe -Wall -Wno-unused-function")
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS} -g -O0")
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS} -O3")
set(CMAKE_CXX_FLAGS_RELWITHDEBINFO "${CMAKE_CXX_FLAGS} -g -O3")
set(CMAKE_CXX_FLAGS_MINSIZEREL "${CMAKE_CXX_FLAGS} -Os")

if (ENABLE_HEAP_PROFILER)
	add_definitions(-DENABLE_HEAP_PROFILE)
	set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -ltcmalloc -fno-builtin-malloc -fno-builtin-calloc -fno-builtin-realloc -fno-builtin-free")
endif ()
if (ENABLE_ADDRESS_SANITIZER)
	message("Building with -fsanitize=address")
	set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fsanitize=address -fno-omit-frame-pointer")
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=address -fno-omit-frame-pointer")
elseif (ENABLE_LEAK_SANITIZER)
	message("Building with -fsanitize=leak ")
	set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fsanitize=leak -fno-omit-frame-pointer ")
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=leak -fno-omit-frame-pointer ")
endif ()

# create bin
add_executable(${TARGET_NAME} ${sources_c} ${sources_h})

set_target_properties(${TARGET_NAME} PROPERTIES LINKER_LANGUAGE CXX)

# add lib deps
add_dependencies(${TARGET_NAME} zcutils)
target_link_libraries(${TARGET_NAME}
	PRIVATE ${linked_libs}
	PRIVATE Threads::Threads
	PRIVATE OpenSSL::SSL
	PRIVATE OpenSSL::Crypto
	PRIVATE zcutils)

if (BUILD_DOC)
	find_package(Doxygen REQUIRED)
	set(BUILD_DOC_DIR "${PROJECT_SOURCE_DIR}/build/doc")
	if (NOT EXISTS ${BUILD_DOC_DIR})
		message("Creating ${BUILD_DOC_DIR} directory.")
		file(MAKE_DIRECTORY ${BUILD_DOC_DIR})
	else ()
		message("Found ${BUILD_DOC_DIR}.")
	endif ()
	set(DOXYGEN_IN "${CMAKE_CURRENT_SOURCE_DIR}/doc/Doxyfile")
	set(DOXYGEN_OUT "${CMAKE_CURRENT_BINARY_DIR}/Doxyfile")
	configure_file(${DOXYGEN_IN} ${DOXYGEN_OUT} @ONLY)

	add_custom_target(docs ALL
		COMMAND ${DOXYGEN_EXECUTABLE} ${DOXYGEN_OUT}
		WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
		COMMENT "Generating API documentation with Doxygen"
		VERBATIM)
endif ()

# install
install(TARGETS "${TARGET_NAME}" DESTINATION bin COMPONENT binaries)
