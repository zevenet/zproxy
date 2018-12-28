cmake_minimum_required(VERSION 3.7)
project(zhttp LANGUAGES CXX)

#options
option(BUILD_DOC "Build Documentation" ON)
option(BUILD_TESTS "Build tests" ON)
option(UNIQUE_BUILD_DIRECTORY "enable built output build/bin directory" OFF)

if (NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif ()
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 ")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}   -m64 -std=c++11 -m64 -fpermissive  -Wshadow -pipe  -D__FILENAME__='\"$(subst  ${CMAKE_SOURCE_DIR}/,,$(abspath \$<))\"'")

SET(MAINFOLDER ${PROJECT_SOURCE_DIR})
if (UNIQUE_BUILD_DIRECTORY)
    SET(EXECUTABLE_OUTPUT_PATH "${MAINFOLDER}/build/bin/${CMAKE_BUILD_TYPE}")
endif()

set(CMAKE_CXX_STANDARD 11)

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
#add_subdirectory(lib)
if(BUILD_TESTS)
    add_subdirectory(tests)
endif()
add_subdirectory(src)
add_subdirectory(src/ctl)
# Doxygen Build
add_executable(zhttp src/main.cpp )
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
