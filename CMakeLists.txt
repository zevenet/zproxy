cmake_minimum_required(VERSION 3.9)
project(s_http)

set(CMAKE_CXX_STANDARD 11)
find_package(Threads)
add_executable(${PROJECT_NAME} main.cpp event/event_manager.cpp event/event_manager.h connection/connection.cpp connection/connection.h StreamManager.cpp StreamManager.h http/http_stream.cpp http/http_stream.h string_buffer.cpp string_buffer.h debug/Debug.h connection/Network.h listener.cpp listener.h util/utils.h)
target_link_libraries(${PROJECT_NAME} ${CMAKE_THREAD_LIBS_INIT})