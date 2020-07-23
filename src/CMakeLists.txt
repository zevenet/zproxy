
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
cmake_minimum_required(VERSION 3.6)

add_definitions(-DLOGGER_DEBUG=0)
add_definitions(-DDEBUG_EVENT_MANAGER=0 -DHELLO_WORLD_SERVER=0)
add_definitions(-DPRINT_READ_STADISTICS=0)
add_definitions(-DDEBUG_CONNECTION_FLOW=0)
add_definitions(-DMAXBUF=4096)
add_definitions(-DMAX_URI_SIZE=16500)
add_definitions(-DMAX_HEADER_VALUE_SIZE=16500)
add_definitions(-DMAX_NUM_HEADERS=50)
add_definitions(-DSM_HANDLE_ACCEPT=1) #StreamManager handle accept connections
add_definitions(-DDEBUG_STREAM_EVENTS_COUNT=0)
#SSL stuff
add_definitions(-DSSL_DISABLE_SESSION_CACHE=0) #internal ssl session caching
add_definitions(-DDEBUG_SSL=0)
add_definitions(-DENABLE_SSL_SESSION_CACHING=0)
add_definitions(-DENABLE_ZERO_COPY=0)
add_definitions(-DPRINT_DEBUG_FLOW_BUFFERS=0)
add_definitions(-DENABLE_QUICK_RESPONSE=0)
add_definitions(-DUSE_SSL_BIO_BUFFER=1)
add_definitions(-DDEBUG_HTTP_HEADERS=0)
add_definitions(-DMALLOC_TRIM_TIMER=1 -DMALLOC_TRIM_TIMER_INTERVAL=60) # force release of memory back to the system
add_definitions(-DDEFAULT_MAINTENANCE_INTERVAL=10)
add_definitions(-DENABLE_CI_HEADERS=1) #enable case insensitive comparator in header map.
add_definitions(-DUSE_TIMER_FD_TIMEOUT=0)

set(l7core_sources
    debug/logger.h debug/logger.cpp
    debug/backtrace.h debug/backtrace.cpp
    ssl/ssl_common.h
    ssl/ssl_context.h ssl/ssl_context.cpp
    ssl/ssl_connection_manager.h ssl/ssl_connection_manager.cpp
    ssl/ssl_session.h ssl/ssl_session.cpp
    json/json.h json/json.cpp
    json/json_data_value.h json/json_data_value.cpp
    json/json_data_value_types.h json/json_data_value_types.cpp
    json/json_data.h json/json_data.cpp
    json/json_parser.h json/json_parser.cpp
    event/timer_fd.h event/timer_fd.cpp
    event/signal_fd.h event/signal_fd.cpp
    event/epoll_manager.h event/epoll_manager.cpp
    event/descriptor.h
    connection/client_connection.h
    connection/connection.h connection/connection.cpp
    connection/backend_connection.h connection/backend_connection.cpp
    stream/stream_manager.h stream/stream_manager.cpp
	stream/listener_manager.h stream/listener_manager.cpp
    stream/stream_data_logger.h stream/stream_data_logger.cpp
    service/backend.h service/backend.cpp
    service/http_session_manager.h service/http_session_manager.cpp
    service/service.h service/service.cpp
    service/service_manager.h service/service_manager.cpp
    config/config_node.h
    config/config_data.h
    config/config.h config/config.cpp
    http/http_stream.h http/http_stream.cpp
    http/http_parser.h http/http_parser.cpp
    http/pico_http_parser.h http/pico_http_parser.cpp
    http/http_request.h http/http_request.cpp
    http/http.h http/http.cpp
    util/common.h util/system.h util/network.h util/crypto.h util/environment.h util/utils.h
    ctl/control_manager.h ctl/control_manager.cpp ctl/observer.h ctl/ctl.h
    stats/backend_stats.h stats/backend_stats.cpp
    stats/counter.h
    handlers/http_manager.h handlers/http_manager.cpp
    handlers/https_manager.h handlers/https_manager.cpp
    config/regex_manager.cpp config/regex_manager.h
    config/ssl_helper.cpp config/ssl_helper.h config/global.cpp config/global.h
    util/time.h)

if (ENABLE_ON_FLY_COMRESSION)
    set(l7core_sources ${l7core_sources}
        util/zlib_util.h
        handlers/compression.h
        handlers/compression.cpp
        )
endif ()

if (CACHE_SUPPORT)
    message(STATUS "Cache support enabled")
    set(l7core_sources ${l7core_sources}
        cache/http_cache.cpp
        cache/http_cache.h
        cache/i_cache_storage.h
        cache/cache_commons.h
        cache/ram_cache_storage.h
        cache/ram_cache_storage.cpp
        cache/disk_cache_storage.h
        cache/disk_cache_storage.cpp
        handlers/cache_manager.cpp
        handlers/cache_manager.h
        )
endif ()

if (ENABLE_WAF)
    set(l7core_sources "${l7core_sources}"
        handlers/waf.h
        handlers/waf.cpp)
endif()

set_source_files_properties(http/http_parser.cpp
    http/http_parser.h http/picohttpparser.c http/pico_http_parser.h PROPERTIES COMPILE_FLAGS -fpermissive)
add_library(l7pcore ${l7core_sources})
target_link_libraries(l7pcore PRIVATE ${CMAKE_THREAD_LIBS_INIT} ${PCRE_LIBRARIES} ${ZLIB_LIBRARIES})

if (ENABLE_ON_FLY_COMRESSION)
    target_link_libraries(l7pcore PRIVATE ${ZLIB_LIBRARIES})
endif ()

if (BUNDLED_OPENSSL)
    add_dependencies(l7pcore openssl)
    link_directories(l7pcore ${OPENSSL_INSTALL_DIR}/lib)
    target_link_libraries(l7pcore PRIVATE ${OPENSSL_LIBRARY_SSL} ${OPENSSL_LIBRARY_CRYPTO} -lz -ldl)
else ()
    target_link_libraries(l7pcore PRIVATE ${OPENSSL_LIBRARIES})
endif ()

if (CACHE_SUPPORT)
    if (MEMCACHED_ENABLED)
        target_link_libraries(l7pcore PRIVATE ${MEMCACHED_LIBRARIES})
    endif ()
    target_link_libraries(l7pcore PRIVATE stdc++fs)
endif ()

if (ENABLE_WAF)
    target_link_libraries(l7pcore PRIVATE ${LIBMODSECURITY_LIBRARY})
endif()
