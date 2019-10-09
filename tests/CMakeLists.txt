
###############################################################################
#
#    Zevenet zProxy Load Balancer Software License
#    This file is part of the Zevenet zProxy Load Balancer software package.
#
#    Copyright (C) 2019-today ZEVENET SL, Sevilla (Spain)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

CMAKE_MINIMUM_REQUIRED(VERSION 3.1)

PROJECT(zproxy_test
    LANGUAGES CXX)
#enable_testing()
add_definitions(-DGTEST_LANGUAGE_CXX11 -DGTEST_BUILD_SAMPLES=OFF -DGTEST_HAS_POSIX_RE=0)
#add_definitions(-DGTEST_USES_PCRE=1)

#find_package(Threads REQUIRED)

SET(GOOGLETEST_DIR "${CMAKE_SOURCE_DIR}/tests/lib/gtest")

if (NOT EXISTS ${GOOGLETEST_DIR})
    #    message(FATAL_ERROR "No googletest src dir found - set GOOGLETEST_DIR to enable!")
    find_package(Git REQUIRED)
    message("Downloading google test library...")
    execute_process(COMMAND ${GIT_EXECUTABLE} clone https://github.com/google/googletest ${GOOGLETEST_DIR} RESULT_VARIABLE ret)
    if(NOT ret EQUAL "0")
        message( FATAL_ERROR "google test repo clone failed")
    endif()
endif ()

SET(GTestSrc ${GOOGLETEST_DIR}/googletest)
SET(GMockSrc ${GOOGLETEST_DIR}/googlemock)

include_directories(${GTestSrc} ${GTestSrc}/include ${GMockSrc} ${GMockSrc}/include)

add_library(gtest
    ${GTestSrc}/src/gtest-all.cc
    ${GMockSrc}/src/gmock-all.cc)

target_include_directories(gtest
    PUBLIC ${GTestSrc}/include ${GMockSrc} ${GMockSrc}/include
    )

add_executable(${PROJECT_NAME}
    src/main.cpp
    src/tst_basictest.h
    src/t_timerfd.h
    src/t_epoll_manager.h
    src/testserver.h
    #t_backend_connection.h
    src/t_compression.h
    src/t_http_parser.h
    src/t_config.h
    src/t_observer.h
    src/t_control_manager.h
    src/t_json.h
    src/t_ctlclient.h
    src/t_sslcontext.h
    #src/t_cache.h
    #src/t_cache_storage.h
    src/cache_helpers.h
    )

add_test(${PROJECT_NAME} COMMAND ${PROJECT_NAME})

target_link_libraries(${PROJECT_NAME} PRIVATE l7pcore gtest ${CMAKE_THREAD_LIBS_INIT} ${PCRE_LIBRARIES} ${OPENSSL_LIBRARIES})


