###############################################################################
#
#    Zevenet zproxy Load Balancer Software License
#    This file is part of the Zevenet zproxy Load Balancer software package.
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

if(EXISTS CMakeLists.txt)
    message(FATAL_ERROR"Please create a cmake build directory, running cmake form source tree root is not allowed\n")
endif()

project(zproxy LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)

if (NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif ()

set(CMAKE_CXX_STANDARD_REQUIRED ON)
SET(MAINFOLDER ${PROJECT_SOURCE_DIR})

#options

option(BUILD_DOC "Build Documentation" OFF)
option(BUILD_TESTS "Build tests" ON)
option(UNIQUE_BUILD_DIRECTORY "enable build directory" ON)
option(BUNDLED_OPENSSL "Use Bundled Openssl (build latest version)" OFF)
option(BUNDLED_ZLIB "Use Bundled ZLIB (build latest version)" OFF)
#debugging
option(ENABLE_HEAP_PROFILE "Enable heap profiler, also need tcmalloc to be enabled" OFF)
option(ENABLE_TCMALLOC "Use tcmalloc instead of standard library malloc " OFF)
option(ENABLE_ADDRESS_SANITIZER "Enable address sanitizer" OFF)
option(ENABLE_LEAK_SANITIZER "Enable memory leak sanitizer" OFF)
option(ENABLE_THREAD_SANITIZER "Enable thread sanitizer" OFF)
option(ENABLE_COVERAGE "Enable coverage" OFF)
#experimental, do not enable WIP
option(CACHE_SUPPORT "Build with cache support" OFF)
option(ENABLE_WAF "Compile zproxy using WAF features" ON)
set(CACHE_STORAGE_TYPE 1) # 1 ramfs,2 stdmap,3 memcached, default(1)
#option(MEMCACHED_ENABLED "memcached" OFF) deprecated
#option(ENABLE_APACHE_LOG_FORMAT "Enable message log in apache format" OFF) not implemented yet
option(ENABLE_ON_FLY_COMRESSION "Enable response compression" OFF)

set(RSA_TIMEOUT 7200 )#"RSA keys regeneratiom timeout in seconds")
set(DH "2048" CACHE STRING "Diffie-Hellman parameters bits length")


#file(REMOVE_RECURSE "${MAINFOLDER}/build")
#file(MAKE_DIRECTORY "${MAINFOLDER}/build")
#file(MAKE_DIRECTORY "${MAINFOLDER}/build/docs")

SET(PROJECT_DESCRIPTION "Zevenet L7 proxy core for zevenet load balancer")
SET(PROJECT_CODENAME "${PROJECT_NAME}")

SET(PROJECT_VERSION_MAJOR 0)
SET(PROJECT_VERSION_MINOR 2)
SET(PROJECT_VERSION_PATCH 3)
SET(PROJECT_VERSION_TWEAK 0)

SET(PROJECT_VENDOR_NAME "Zevenet")
SET(PROJECT_VENDOR_URL "https://www.zevenet.com")
execute_process(COMMAND "date" "+%Y"
        OUTPUT_VARIABLE DATE_YEAR)
string(TIMESTAMP DATE_YEAR "%Y")

SET(PROJECT_COPYRIGHT "Copyright (C) ${DATE_YEAR} ${PROJECT_VENDOR_NAME}")
SET(PROJECT_VERSION "${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}.${PROJECT_VERSION_PATCH}-${PROJECT_VERSION_TWEAK}")

SET(PROJECT_COMPILER_INFO "${CMAKE_CXX_COMPILER_ID}-${CMAKE_CXX_COMPILER_VERSION}")
SET(PROJECT_BUILD_TYPE "${CMAKE_BUILD_TYPE}")
EXECUTE_PROCESS( COMMAND uname -srm COMMAND tr -d '\n' OUTPUT_VARIABLE PROJECT_HOST_INFO )
#SET(PROJECT_HOST_INFO "${CMAKE_SYSTEM_NAME} ")#"${CMAKE_SYSTEM_PROCESSOR}")

# get current git info
if (EXISTS "${PROJECT_SOURCE_DIR}/.git/HEAD")
    file(READ "${PROJECT_SOURCE_DIR}/.git/HEAD"
        PROJECT_SOURCE_VERSION)
    if ("${PROJECT_SOURCE_VERSION}" MATCHES "^ref:")
        string(REGEX REPLACE "^ref: *([^ \n\r]*).*" "\\1"
            PROJECT_GIT_REF "${PROJECT_SOURCE_VERSION}")
        file(READ "${PROJECT_SOURCE_DIR}/.git/${PROJECT_GIT_REF}"
            PROJECT_SOURCE_VERSION)
    endif ()
    string(STRIP "${PROJECT_SOURCE_VERSION}"
        PROJECT_SOURCE_VERSION)
endif ()

# get build date and time

execute_process(COMMAND "date" "+%d %b %Y/%H:%M:%S"
    OUTPUT_VARIABLE DATE_TIME)
string(REGEX REPLACE "([^/]*)/.*" "\\1"
    PROJECT_BUILD_DATE "${DATE_TIME}")
string(REGEX REPLACE "[^/]*/([0-9:]*).*" "\\1"
    PROJECT_BUILD_TIME "${DATE_TIME}")

configure_file(
    "${PROJECT_SOURCE_DIR}/cmake/version.h.in"
    "${PROJECT_SOURCE_DIR}/src/version.h"
    )

#configure_file(
#    "${PROJECT_SOURCE_DIR}/cmake/project-info.in"
#    "${PROJECT_SOURCE_DIR}/build-pkg/project-info"
#    )

add_definitions(-DPROJECT_NAME="${PROJECT_NAME}")
add_definitions(-DPROJECT_VERSION="${PROJECT_VERSION}")

if (UNIQUE_BUILD_DIRECTORY)
    SET(EXECUTABLE_OUTPUT_PATH "${MAINFOLDER}/build/bin")
endif ()

set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 ")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -m64 -std=c++1z  -Wshadow -pipe -pthread")
#uncomment to show relative source file path
#set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D__FILENAME__='\"$(subst  ${CMAKE_SOURCE_DIR}/,,$(abspath \$<))\"'")

if (ENABLE_HEAP_PROFILER)
    add_definitions(-DENABLE_HEAP_PROFILE)
    set (CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -ltcmalloc -fno-builtin-malloc -fno-builtin-calloc
        -fno-builtin-realloc -fno-builtin-free")
endif ()

if (ENABLE_ADDRESS_SANITIZER)
  message("Building with -fsanitize=address ")
  set(CMAKE_C_FLAGS   "${CMAKE_C_FLAGS}   -fsanitize=address -fno-omit-frame-pointer")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=address -fno-omit-frame-pointer")
elseif(ENABLE_LEAK_SANITIZER)
  message("Building with -fsanitize=leak ")
  set(CMAKE_C_FLAGS   "${CMAKE_C_FLAGS}   -fsanitize=leak -fno-omit-frame-pointer ")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=leak -fno-omit-frame-pointer ")
elseif(ENABLE_THREAD_SANITIZER)
  message("Building with -fsanitize=thread ")
  set(CMAKE_C_FLAGS   "${CMAKE_C_FLAGS}   -fsanitize=thread -fno-omit-frame-pointer ")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=thread -fno-omit-frame-pointer ")
endif()
if(ENABLE_COVERAGE)
  message("Building with code coverage")
  set(CMAKE_C_FLAGS   "${CMAKE_C_FLAGS}   --coverage")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} --coverage")
endif()

if (ENABLE_ON_FLY_COMRESSION)
    add_definitions(-DON_FLY_COMRESSION=1)
endif ()

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
# Search OpenSSL

find_package(PkgConfig REQUIRED)

if (ENABLE_WAF)

    find_path(LIBMODSECURITY_INCLUDE_DIR modsecurity/modsecurity.h
        HINTS ${PC_MODSECURITY_INCLUDEDIR} ${PC_MODSECURITY_INCLUDE_DIRS}
        PATH_SUFFIXES modsecurity )

    find_library(LIBMODSECURITY_LIBRARY NAMES modsecurity libmodsecurity
        HINTS ${PC_MODSECURITY_LIBDIR} ${PC_MODSECURITY_LIBRARY_DIRS} )

    if (NOT LIBMODSECURITY_LIBRARY)
        message(FATAL_ERROR "libmodsecurity lib was not found")
    endif ()

    file(STRINGS "${LIBMODSECURITY_INCLUDE_DIR}/modsecurity/modsecurity.h"  LIBMODSECURITY_VERSION_DEFINE REGEX "^#define MODSECURITY_.*$")
    string(REGEX MATCH "^#define MODSECURITY_MAJOR[ ]\"([0-9]*)\".*$" _ ${LIBMODSECURITY_VERSION_DEFINE})
    set(MODSECURITY_MAJOR ${CMAKE_MATCH_1})

    file(STRINGS "${LIBMODSECURITY_INCLUDE_DIR}/modsecurity/modsecurity.h"  LIBMODSECURITY_VERSION_DEFINE REGEX "^#define MODSECURITY_MINOR.*$")
    string(REGEX MATCH "^#define MODSECURITY_MINOR[ ]\"([0-9]*)\".*$" _ ${LIBMODSECURITY_VERSION_DEFINE})
    set(MODSECURITY_MINOR ${CMAKE_MATCH_1})

    file(STRINGS "${LIBMODSECURITY_INCLUDE_DIR}/modsecurity/modsecurity.h"  LIBMODSECURITY_VERSION_DEFINE REGEX "^#define MODSECURITY_PATCHLEVEL.*$")
    string(REGEX MATCH "^#define MODSECURITY_PATCHLEVEL[ ]\"([0-9]*)\".*$" _ ${LIBMODSECURITY_VERSION_DEFINE})
    set(MODSECURITY_PATCHLEVEL ${CMAKE_MATCH_1})

    set(LIBMODSECURITY_VERSION "${MODSECURITY_MAJOR}.${MODSECURITY_MINOR}.${MODSECURITY_PATCHLEVEL}")
    message(STATUS "Using libmodsecurity ${LIBMODSECURITY_VERSION}")
    include_directories(${LIBMODSECURITY_INCLUDE_DIR})
    add_definitions(-DWAF_ENABLED=1)
endif()
if(ENABLE_ON_FLY_COMRESSION)
    add_definitions(-DENABLE_ON_FLY_COMRESSION=1)
    if (BUNDLED_ZLIB)
        #
        # zlib
        #
        message(STATUS "Building zlib")
        include(ExternalProject)
        include(GNUInstallDirs)
        set(ZLIB_BUNDLE_DIR "${MAINFOLDER}/build/zlib/src/zlib")
        set(ZLIB_INSTALL_DIR "${MAINFOLDER}/build/zlib/target")
        set(ZLIB_INCLUDE_DIR "${MAINFOLDER}/build/zlib/target/include")
        set(ZLIB_LIBRARY_SO "${ZLIB_INSTALL_DIR}/lib/libz.so")
        set(ZLIB_LIBRARIES "${ZLIB_INSTALL_DIR}/lib/libz.a")
        set(BUILD_AND_INSTALL_CMD "${CMD_MAKE} make install")
        message(STATUS "Using bundled zlib in '${ZLIB_BUNDLE_DIR}'")
        #Debug build
        # ./config --prefix=/usr/local/ssl --zlibdir=/usr/local/ssl -d shared no-asm no-ssl2 -g3 -ggdb -gdwarf-4 -fno-inline -O0 -fno-omit-frame-pointer
        ExternalProject_Add( zlib
            URL "http://zlib.net/zlib-1.2.11.tar.gz"
            CONFIGURE_COMMAND ./configure --static --prefix=${ZLIB_INSTALL_DIR}
            BUILD_COMMAND make -j8
            BUILD_IN_SOURCE 1
            INSTALL_COMMAND make install -j8)

        #    set(ENV{PKG_CONFIG_PATH} "${ZLIB_INSTALL_DIR}/lib/pkgconfig")
        #add_dependencies(zlib)
        include_directories(${ZLIB_INCLUDE_DIR})
        link_directories(${ZLIB_INSTALL_DIR}/lib)
    else ()
        find_package(ZLIB REQUIRED)
        if (ZLIB_FOUND)
            #message(STATUS "Zlib includes ${ZLIB_INCLUDE_DIRS}")
            #message(STATUS "Zlib link ${ZLIB_LIBRARIES}")
            include_directories(${ZLIB_INCLUDE_DIRS})
            message(STATUS "Using Zlib ${ZLIB_VERSION_STRING}")
        endif ()
    endif()
endif()
if (BUNDLED_OPENSSL)
    #
    # OpenSSL
    #
    message(STATUS "Building openssl")
    include(ExternalProject)
    include(GNUInstallDirs)
    set(OPENSSL_BUNDLE_DIR "${MAINFOLDER}/build/openssl/src/openssl")
    set(OPENSSL_INSTALL_DIR "${MAINFOLDER}/build/openssl/target")
    set(OPENSSL_INCLUDE_DIR "${MAINFOLDER}/build/openssl/target/include")
    set(OPENSSL_LIBRARY_SSL_SO "${OPENSSL_INSTALL_DIR}/lib/libssl.so")
    set(OPENSSL_LIBRARY_CRYPTO_SO "${OPENSSL_INSTALL_DIR}/lib/libcrypto.so")
    set(OPENSSL_LIBRARY_SSL "${OPENSSL_INSTALL_DIR}/lib/libssl.a")
    set(OPENSSL_LIBRARY_CRYPTO "${OPENSSL_INSTALL_DIR}/lib/libcrypto.a")
    set(BUILD_AND_INSTALL_CMD "${CMD_MAKE} make install")
    message(STATUS "Using bundled openssl in '${OPENSSL_BUNDLE_DIR}'")
    #Debug build
    # ./config --prefix=/usr/local/ssl --openssldir=/usr/local/ssl -d shared no-asm no-ssl2 -g3 -ggdb -gdwarf-4 -fno-inline -O0 -fno-omit-frame-pointer
    ExternalProject_Add(openssl
        URL "https://www.openssl.org/source/openssl-1.1.1c.tar.gz"
        CONFIGURE_COMMAND ./config shared --prefix=${OPENSSL_INSTALL_DIR} -lz -ldl -O2
        BUILD_COMMAND make -j8
        BUILD_IN_SOURCE 1
        BUILD_BYPRODUCTS ${OPENSSL_LIBRARY_SSL} ${OPENSSL_LIBRARY_CRYPTO}
        INSTALL_COMMAND make install -j8)
    set(ENV{PKG_CONFIG_PATH} "${OPENSSL_INSTALL_DIR}/lib/pkgconfig")
    #add_dependencies(openssl)
    include_directories(${OPENSSL_INCLUDE_DIR})
    link_directories(${OPENSSL_INSTALL_DIR}/lib)
else ()
    pkg_search_module(OPENSSL openssl)
    if (OPENSSL_FOUND)
        #message(STATUS "Openssl includes ${OPENSSL_INCLUDE_DIRS}")
        #message(STATUS "Openssl link ${OPENSSL_LIBRARIES}")
        include_directories(${OPENSSL_INCLUDE_DIRS})
        message(STATUS "Using OpenSSL ${OPENSSL_VERSION}")
        if (OPENSSL_VERSION VERSION_LESS "1.1.0")
            MESSAGE(FATAL_ERROR "openssl >= 1.1.0 required for TLS")
        endif()
    endif()
endif ()

if (CACHE_SUPPORT)
    add_definitions(-DCACHE_ENABLED=1)
    if (CACHE_STORAGE_TYPE EQUAL 2)
        message(STATUS "Using stdmap")
        add_definitions(-DCACHE_STORAGE_STDMAP=1)
    elseif (CACHE_STORAGE_TYPE EQUAL 3)
        message(STATUS "Using memcached")
        set(MEMCACHED_ENABLED 1)
    else()
        message(STATUS "Using ramfs")
    endif()
    set(ENV{PKG_CONFIG_PATH} "/usr/lib/x86_64-linux-gnu/pkgconfig")
    if (MEMCACHED_ENABLED)
        # Search memcached
        add_definitions(-DMEMCACHED_ENABLED=1)
        pkg_search_module(MEMCACHED libmemcached REQUIRED)
        if (MEMCACHED_FOUND)
            message(STATUS "Memcached includes ${MEMCACHED_INCLUDE_DIRS}")
            message(STATUS "Memcached link ${MEMCACHED_LIBRARIES}")
            include_directories(${MEMCACHED_INCLUDE_DIRS})
            message(STATUS "Using memcached ${MEMCACHED_VERSION}")
        endif ()
    else ()
        add_definitions(-DMEMCACHED_ENABLED=0)
    endif ()
endif ()


if (NOT EXISTS "${MAINFOLDER}/src/config/dh512.h")
    message(STATUS "Generating DH EC 512 parameters")
    execute_process(
        COMMAND openssl dhparam -5 -C -noout 512
        RESULT_VARIABLE ret
        OUTPUT_FILE "${MAINFOLDER}/src/config/dh512.h")
    if(NOT ret EQUAL "0")
        message( FATAL_ERROR "openssl dhparam failed")
    endif()
endif()

if (DH EQUAL "1024" )
        if(NOT EXISTS  "${MAINFOLDER}/src/config/dh1024.h")
        message(STATUS "Generating DH EC 1024 parameters file")
        execute_process(
            COMMAND openssl dhparam -5 -C -noout 1024
            RESULT_VARIABLE ret
            OUTPUT_FILE "${MAINFOLDER}/src/config/dh1024.h")
        if(NOT ret EQUAL "0")
            message( FATAL_ERROR "openssl dhparam failed")
        endif()
    endif()
elseif(DH EQUAL "2048" )
        if (NOT EXISTS "${MAINFOLDER}/src/config/dh2048.h")
        message(STATUS "Generating DH EC 2048 parameters file")
        execute_process(
            COMMAND openssl dhparam -5 -C -noout 2048
            RESULT_VARIABLE ret
            OUTPUT_FILE "${MAINFOLDER}/src/config/dh2048.h")
        if(NOT ret EQUAL "0")
            message( FATAL_ERROR "openssl dhparam failed")
        endif()
    endif()
elseif()
    message( FATAL_ERROR "Invalid DH bits length specified")
endif()
if (NOT EXISTS "${MAINFOLDER}/src/config/dh2048.pem")
    message(STATUS "Generating dh2048.pem")
    execute_process(COMMAND openssl dhparam -5 -out "${MAINFOLDER}/src/config/dh2048.pem" 2048 RESULT_VARIABLE ret)
    if(NOT ret EQUAL "0")
        message( FATAL_ERROR "openssl dhparam failed")
    endif()
endif()
add_definitions(-DDH_LEN=${DH} -DT_RSA_KEYS=${RSA_TIMEOUT})

add_subdirectory(src)
add_subdirectory(src/ctl)
if (BUILD_TESTS)
    add_subdirectory(tests)
endif ()

add_executable(zproxy src/main.cpp)
add_dependencies(zproxy l7pcore)
target_link_libraries(zproxy l7pcore)

# Doxygen Build
if (BUILD_DOC)
    find_package(Doxygen)
    if (DOXYGEN_FOUND)
        set(BUILD_DOC_DIR ${MAINFOLDER}/build/docs)
        if (NOT EXISTS ${BUILD_DOC_DIR})
            message("The directory ${BUILD_DOC_DIR} does not exists")
            file(MAKE_DIRECTORY ${BUILD_DOC_DIR})
        endif ()
        message("The directory ${BUILD_DOC_DIR} exists")

        set(DOXYGEN_IN ${CMAKE_CURRENT_SOURCE_DIR}/docs/Doxyfile)
        set(DOXYGEN_OUT ${CMAKE_CURRENT_BINARY_DIR}/Doxyfile)
        configure_file(${DOXYGEN_IN} ${DOXYGEN_OUT} @ONLY)

        message("Doxygen build started")
        add_custom_target(Doxygen ALL
            COMMAND ${DOXYGEN_EXECUTABLE} ${DOXYGEN_OUT}
            WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
            COMMENT "Generating API documentation with Doxygen"
            VERBATIM)
    else (DOXYGEN_FOUND)
        message("Doxygen needs to be installed to generate the documentation.")
    endif (DOXYGEN_FOUND)
endif ()

#project deployment
macro(add_deployment_file SRC DEST)
    file(RELATIVE_PATH path ${CMAKE_SOURCE_DIR} ${CMAKE_CURRENT_SOURCE_DIR})
    file(APPEND "${CMAKE_SOURCE_DIR}/QtCreatorDeployment.txt" "${path}/${SRC}:${DEST}\n")
endmacro()

macro(add_deployment_directory SRC DEST)
    file(GLOB_RECURSE files RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}" "${SRC}/*")
    foreach (filename ${files})
        get_filename_component(path ${filename} PATH)
        add_deployment_file("${filename}" "${DEST}/${path}")
    endforeach (filename)
endmacro()

#install
install(TARGETS "zproxy" DESTINATION bin COMPONENT binaries)
install(FILES "${MAINFOLDER}/src/config/dh2048.pem" DESTINATION etc)
install(FILES "${MAINFOLDER}/docs/zproxy.8" DESTINATION share/man/man8 )
install(FILES "${MAINFOLDER}/docs/zproxyctl.8" DESTINATION share/man/man8 )
