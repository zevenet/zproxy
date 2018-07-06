cmake_minimum_required(VERSION 3.9)
project(s_zhttp)
#if (NOT CMAKE_BUILD_TYPE)
#    set(CMAKE_BUILD_TYPE Debug)
#endif ()
set(CMAKE_CXX_FLAGS_RELEASE "-O2")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}   -m64 -std=c++11 -m64 -fpermissive  -Wshadow -pipe   -D__FILENAME__='\"$(subst  ${CMAKE_SOURCE_DIR}/,,$(abspath $<))\"'")
add_definitions(-DDEBUG_EVENT_MANAGER=0 -DHELLO_WORLD_SERVER=0)
add_definitions(-DPRINT_READ_STADISTICS=0)
add_definitions(-DDEBUG_CONNECTION_FLOW=0)

#Features to implement !!
add_definitions(-DACCEPT_RANGES=0)

set(CMAKE_CXX_STANDARD 11)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DVERSION='\"zhttp_abdess\"'")

find_package(PkgConfig)
pkg_check_modules(PC_PCRE QUIET libpcre)
set(PCRE_DEFINITIONS ${PC_PCRE_CFLAGS_OTHER})
find_path(PCRE_INCLUDE_DIR pcre.h
    HINTS ${PC_PCRE_INCLUDEDIR} ${PC_PCRE_INCLUDE_DIRS}
    PATH_SUFFIXES pcre)

find_library(PCRE_PCRE_LIBRARY NAMES pcre HINTS ${PC_PCRE_LIBDIR} ${PC_PCRE_LIBRARY_DIRS})

find_library(PCRE_PCREPOSIX_LIBRARY NAMES pcreposix HINTS ${PC_PCRE_LIBDIR} ${PC_PCRE_LIBRARY_DIRS})

include(FindPackageHandleStandardArgs)

find_package_handle_standard_args(PCRE DEFAULT_MSG PCRE_INCLUDE_DIR PCRE_PCRE_LIBRARY PCRE_PCREPOSIX_LIBRARY)
set(PCRE_LIBRARIES ${PCRE_PCREPOSIX_LIBRARY} ${PCRE_PCRE_LIBRARY})
mark_as_advanced(PCRE_INCLUDE_DIR PCRE_LIBRARIES PCRE_PCRE_LIBRARY)

find_package(Threads)
set(ENV{PKG_CONFIG_PATH} "/usr/lib/openssl-1.0/pkgconfig")
# Search OpenSSL

find_package(PkgConfig REQUIRED)
pkg_search_module(OPENSSL REQUIRED openssl)

#if (OPENSSL_FOUND)
#  status_message(STATUS "Openssl includes ${OPENSSL_INCLUDE_DIRS}")
#  status_message(STATUS "Openssl link ${OPENSSL_LIBRARIES}")
#  include_directories(${OPENSSL_INCLUDE_DIRS})
#  status_message(STATUS "Using OpenSSL ${OPENSSL_VERSION}")
#else ()
#  # Error; with REQUIRED, pkg_search_module() will throw an error by it's own
#endif ()
#
include_directories(/usr/include/openssl-1.0)
link_directories(/usr/lib/openssl-1.0)

add_executable(${PROJECT_NAME}
    main.cpp
    event/epoll_manager.cpp
    event/epoll_manager.h
    connection/connection.cpp
    connection/connection.h
    stream/StreamManager.cpp
    stream/StreamManager.h
    http/http_stream.cpp
    http/http_stream.h
    util/string_buffer.cpp
    util/string_buffer.h
    debug/Debug.h
    util/Network.h
    stream/listener.cpp
    stream/listener.h
    util/utils.h
    config/BackendConfig.h
    tests/test_runner.cpp
    tests/test_runner.h
    config/config.cpp
    config/config.h
    config/pound_struct.h
    config/svc.h
    config/svc.cpp
    http/HttpStatus.cpp http/HttpStatus.h http/http_parser.cpp
    http/http_parser.h http/picohttpparser.cpp http/picohttpparser.h
    http/HttpRequest.h service/Service.cpp service/Service.h service/ServiceManager.cpp service/ServiceManager.h
    connection/backend_connection.cpp connection/backend_connection.h event/TimerFd.cpp event/TimerFd.h
    event/SignalFd.cpp event/SignalFd.h http/http.h util/common.h util/system.h)

target_link_libraries(${PROJECT_NAME} ${CMAKE_THREAD_LIBS_INIT} ${PCRE_LIBRARIES} libssl.so libcrypto.so)# ${OPENSSL_LIBRARIES})
