CMAKE_MINIMUM_REQUIRED(VERSION 3.1)

PROJECT(zhttp_test
    LANGUAGES CXX)
#enable_testing()
add_definitions(-DGTEST_LANGUAGE_CXX11 -DGTEST_BUILD_SAMPLES=OFF -DGTEST_HAS_POSIX_RE=0)
#add_definitions(-DGTEST_USES_PCRE=1)

find_package(Threads REQUIRED)

SET(GOOGLETEST_DIR ${CMAKE_SOURCE_DIR}/tests/lib/gtest)

if (EXISTS ${GOOGLETEST_DIR})
  SET(GTestSrc ${GOOGLETEST_DIR}/googletest)
  SET(GMockSrc ${GOOGLETEST_DIR}/googlemock)
else ()
  find_package(Git REQUIRED)
  execute_process(
      COMMAND ${GIT_EXECUTABLE} clone https://github.com/google/googletest ${GOOGLETEST_DIR}
  )
  message(FATAL_ERROR "No googletest src dir found - set GOOGLETEST_DIR to enable!")
endif ()

include_directories(${GTestSrc} ${GTestSrc}/include ${GMockSrc} ${GMockSrc}/include)

add_library(gtest
    ${GTestSrc}/src/gtest-all.cc
    ${GMockSrc}/src/gmock-all.cc)

target_include_directories(gtest
    PUBLIC ${GTestSrc}/include ${GMockSrc} ${GMockSrc}/include
    )

add_executable(${PROJECT_NAME}
    main.cpp
    tst_basictest.h
    t_timerfd.h
    t_epoll_manager.h
    testserver.h
#    t_backend_connection.h
    t_http_parser.h
    t_config.h
    )

add_test(${PROJECT_NAME} COMMAND ${PROJECT_NAME})

target_link_libraries(${PROJECT_NAME} PRIVATE Threads::Threads libzhttp gtest ${CMAKE_THREAD_LIBS_INIT} ${PCRE_LIBRARIES} ${OPENSSL_LIBRARIES})

#