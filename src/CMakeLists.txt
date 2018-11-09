cmake_minimum_required(VERSION 3.7)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DVERSION='\"zhttp_abdess\"'")

add_definitions(-DDEBUG_EVENT_MANAGER=0 -DHELLO_WORLD_SERVER=0)
add_definitions(-DPRINT_READ_STADISTICS=0)
add_definitions(-DDEBUG_CONNECTION_FLOW=0)
add_definitions(-DMAXBUF=4096)
add_definitions(-DSM_HANDLE_ACCEPT=1) #StreamManager handle accept connections

add_library(libzhttp
    json/json.h
    json/json.cpp
    json/JsonDataValue.h
    json/JsonDataValue.cpp
    json/JsonDataValueTypes.h
    json/JsonDataValueTypes.cpp
    json/JsonData.h
    json/JsonData.cpp
    json/jsonparser.h
    json/jsonparser.cpp
    config/config_node.h
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
    util/crypto.h
    stream/listener.cpp
    stream/listener.h
    util/utils.h
    service/backend.h
    service/backend.cpp
    config/config.cpp
    config/config.h
    config/pound_struct.h
    stats/backend_stats.h
    stats/backend_stats.cpp
    config/svc.h
    config/svc.cpp
    http/HttpStatus.cpp http/HttpStatus.h http/http_parser.cpp
    http/http_parser.h http/picohttpparser.cpp http/picohttpparser.h
    http/HttpRequest.h service/Service.cpp service/Service.h service/ServiceManager.cpp service/ServiceManager.h
    connection/backend_connection.cpp connection/backend_connection.h event/TimerFd.cpp event/TimerFd.h
    event/SignalFd.cpp event/SignalFd.h http/http.h http/http.cpp util/common.h util/system.h service/httpsessionmanager.h
    service/httpsessionmanager.cpp ctl/ControlManager.cpp ctl/ControlManager.h util/environment.h ctl/observer.h ctl/ctl.h
    stats/backend_stats.h stats/backend_stats.cpp)

link_libraries(${JSONCPP_LIBRARIES})

target_link_libraries(libzhttp PRIVATE ${CMAKE_THREAD_LIBS_INIT} ${PCRE_LIBRARIES} ${OPENSSL_LIBRARIES}  ${JSONCPP_LIBRARIES})
