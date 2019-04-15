cmake_minimum_required(VERSION 3.6)

add_executable(zhttpctl main.cpp
    PoundClient.h
    PoundClient.cpp
    CtlClient.cpp CtlClient.h)
add_dependencies(zhttpctl libzhttp)
target_link_libraries( zhttpctl libzhttp)
install(TARGETS "zhttpctl" DESTINATION bin)