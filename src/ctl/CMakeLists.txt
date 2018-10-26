cmake_minimum_required(VERSION 3.7)

add_executable(zhttpctl main.cpp
    PoundClient.h
    PoundClient.cpp
    CtlClient.cpp CtlClient.h)
target_link_libraries( zhttpctl libzhttp)
