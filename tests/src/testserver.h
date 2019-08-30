// Created by fernando on 09/07/18.
#pragma once

#include "../../src/event/epoll_manager.h"
#include "../../src/connection/connection.h"
#include "../../src/util/Network.h"
#include "../../src/debug/Debug.h"
#include "gtest/gtest.h"
#include <thread>
#include <unordered_map>

using namespace events;

class ServerHandler : public EpollManager
{
  Connection lst;
public:
  void setUp(std::string addr, int port){
    lst.address = Network::getAddress(addr, port);
    lst.listen(*lst.address);
    handleAccept(lst.getFileDescriptor());
  }

  void HandleEvent(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group) override {
    int new_fd;
    char *buf = "Hello! I am the server";
    switch (event_type) {
      case EVENT_TYPE::DISCONNECT: {
          deleteFd(fd);
          ::close(fd);
          break;
      }
      case EVENT_TYPE::CONNECT: {
          switch (event_group) {
          case EVENT_GROUP::ACCEPTOR: {
                do {
                    new_fd = lst.doAccept();
                    if (new_fd > 0)
                      addFd(new_fd, EVENT_TYPE::READ, EVENT_GROUP::SERVER);
                  }while(new_fd > 0);
              }
            }
          break;
        }
      case EVENT_TYPE::READ: {
          switch(event_group) {
          case EVENT_GROUP::SERVER: {
                auto data = Network::read(fd);
                if (data.length() > 0)
                   EXPECT_EQ(data.length(),22);
                updateFd(fd, EVENT_TYPE::WRITE, EVENT_GROUP::SERVER);
              }
            }
          break;
        }
      case EVENT_TYPE::WRITE: {
          switch(event_group) {
          case EVENT_GROUP::SERVER: {
                write(fd, buf, strlen(buf));
                updateFd(fd, EVENT_TYPE::READ, EVENT_GROUP::SERVER);
              }
            }
        }
        break;
      }
  }

  ServerHandler() {}
};

class ClientHandler :public EpollManager
{
public:
  std::unordered_map<int, Connection *> connections_set;

  void setUp(int n_clients, std::string addr, int port){
    for (int i=0; i<n_clients; i++)
      {
        Connection *connection = new Connection;
        connection->address = Network::getAddress(addr, port);
        connection->doConnect(*connection->address, 30);
        connections_set[connection->getFileDescriptor()] = connection;
        if(connection->getFileDescriptor() > 0)
            addFd(connection->getFileDescriptor(), EVENT_TYPE::WRITE, EVENT_GROUP::CLIENT);
      }
  }

  void HandleEvent(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group) override{
    char *buf = "Hello! I am the client";
    char *check_buf = "Hello! I am the server";
    switch(event_type){
      case EVENT_TYPE::WRITE: {
        switch(event_group) {
        case EVENT_GROUP::CLIENT: {
            connections_set.at(fd)->write(buf, strlen(buf));
            updateFd(fd, EVENT_TYPE::READ, EVENT_GROUP::CLIENT);
          }
        }
        break;
      }
      case EVENT_TYPE::READ: {
        switch(event_group) {
        case EVENT_GROUP::CLIENT: {
            auto connect = connections_set.at(fd);
            auto a = connect->read();
            if (connect->buffer_size > 0)
              EXPECT_EQ(connect->buffer_size, 22);
            if (a == IO::IO_RESULT::SUCCESS) {
              deleteFd(fd);
              connections_set.erase(fd);
              delete connect;
              ::close(fd);
             }
            }
            break;
          }
        }
     }
  }

  ClientHandler() {}
};


