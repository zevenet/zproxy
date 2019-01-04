cmake_minimum_required(VERSION 3.6)

project(zhttp LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 11)

if (NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif ()

set(CMAKE_CXX_STANDARD_REQUIRED ON)
SET(MAINFOLDER ${PROJECT_SOURCE_DIR})

#options
option(BUILD_DOC "Build Documentation" OFF)
option(BUILD_TESTS "Build tests" OFF)
option(UNIQUE_BUILD_DIRECTORY "enable build directory" OFF)

SET(PROJECT_DESCRIPTION "L7 proxy core for zevenet load balancer")
SET(PROJECT_CODENAME "${PROJECT_NAME}")


SET(PROJECT_VERSION_MAJOR 0)
SET(PROJECT_VERSION_MINOR 1)
SET(PROJECT_VERSION_PATCH 0)
SET(PROJECT_VERSION_TWEAK 0)

SET(PROJECT_VENDOR_NAME "Zevenet")
SET(PROJECT_VENDOR_URL "https://www.zevenet.com")
#execute_process(COMMAND "date" "+%Y"
#        OUTPUT_VARIABLE DATE_YEAR)
string(TIMESTAMP DATE_YEAR "%Y")

SET(PROJECT_COPYRIGHT "Copyright (C) ${DATE_YEAR} ${PROJECT_VENDOR_NAME}")
SET(PROJECT_VERSION "${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}.${PROJECT_VERSION_PATCH}-${PROJECT_VERSION_TWEAK}")

SET (PROJECT_COMPILER_INFO "${CMAKE_CXX_COMPILER_ID}-${CMAKE_CXX_COMPILER_VERSION}")
SET (PROJECT_BUILD_TYPE "${CMAKE_BUILD_TYPE}")
SET (PROJECT_HOST_INFO "${CMAKE_HOST_SYSTEM_NAME} ${CMAKE_HOST_SYSTEM_VERSION} ${CMAKE_HOST_SYSTEM_PROCESSOR}")


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

configure_file(
        "${PROJECT_SOURCE_DIR}/cmake/project-info.in"
        "${PROJECT_SOURCE_DIR}/build-pkg/project-info"
)

add_definitions(-DPROJECT_NAME="${PROJECT_NAME}")
add_definitions(-DPROJECT_VERSION="${PROJECT_VERSION}")

set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 ")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -m64 -std=c++11 -m64 -fpermissive  -Wshadow -pipe  ")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D__FILENAME__='\"$(subst  ${CMAKE_SOURCE_DIR}/,,$(abspath \$<))\"'")

if (UNIQUE_BUILD_DIRECTORY)
    SET(EXECUTABLE_OUTPUT_PATH "${MAINFOLDER}/bin")
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

if (BUILD_TESTS)
    add_subdirectory(tests)
endif ()
add_subdirectory(src)
add_subdirectory(src/ctl)
# Doxygen Build
add_executable(zhttp src/main.cpp)
target_link_libraries(zhttp libzhttp)


if (BUILD_DOC)
    find_package(Doxygen)
    if (DOXYGEN_FOUND)
        set(BUILD_DOC_DIR ${CMAKE_SOURCE_DIR}/build/docs)
        if (NOT EXISTS ${BUILD_DOC_DIR})
            file(MAKE_DIRECTORY ${BUILD_DOC_DIR})
        endif ()

        set(DOXYGEN_IN ${CMAKE_CURRENT_SOURCE_DIR}/docs/Doxyfile)
        set(DOXYGEN_OUT ${CMAKE_CURRENT_BINARY_DIR}/Doxyfile)
        configure_file(${DOXYGEN_IN} ${DOXYGEN_OUT} @ONLY)

        message("Doxygen buld started")
        add_custom_target(Doxygen ALL
                COMMAND ${DOXYGEN_EXECUTABLE} ${DOXYGEN_OUT}
                WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
                COMMENT "Generating API documentation with Doxygen"
                VERBATIM)
    else (DOXYGEN_FOUND)
        message("Doxygen needs to be installed to generate the documentation.")
    endif (DOXYGEN_FOUND)

    file(WRITE "${CMAKE_SOURCE_DIR}/QtCreatorDeployment.txt" "/root\n")

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
endif ()


#install
install(TARGETS "zhttp" DESTINATION bin)
