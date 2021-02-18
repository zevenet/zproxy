/*
 *    Zevenet zproxy Load Balancer Software License
 *    This file is part of the Zevenet zproxy Load Balancer software package.
 *
 *    Copyright (C) 2019-today ZEVENET SL, Sevilla (Spain)
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Affero General Public License as
 *    published by the Free Software Foundation, either version 3 of the
 *    License, or any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Affero General Public License for more details.
 *
 *    You should have received a copy of the GNU Affero General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */
#pragma once

#include "../../src/connection/connection.h"
#include "../../zcutils/zcutils.h"
#include "../../src/event/epoll_manager.h"
#include "../../zcutils/zcu_network.h"
#include "gtest/gtest.h"
#include <thread>
#include <unordered_map>

using namespace events;

class ServerHandler : public EpollManager {
  Connection lst;

 public:
  void setUp(std::string addr, int port);

  void HandleEvent(int fd, EVENT_TYPE event_type,
                   EVENT_GROUP event_group) override;

  ServerHandler() {}
};

class ClientHandler : public EpollManager {
 public:
  std::unordered_map<int, Connection *> connections_set;

  void setUp(int n_clients, std::string addr, int port);

  void HandleEvent(int fd, EVENT_TYPE event_type,
                   EVENT_GROUP event_group) override;

  ClientHandler() {}
};

void ClientHandler::setUp(int n_clients, std::string addr, int port) {
  for (int i = 0; i < n_clients; i++) {
    Connection *connection = new Connection;
    connection->address = zcutils_net_get_address(addr, port).release();
    connection->doConnect(*connection->address, 30);
    connections_set[connection->getFileDescriptor()] = connection;
    if (connection->getFileDescriptor() > 0)
      addFd(connection->getFileDescriptor(), EVENT_TYPE::WRITE,
            EVENT_GROUP::CLIENT);
  }
}

void ClientHandler::HandleEvent(int fd, EVENT_TYPE event_type,
                                EVENT_GROUP event_group) {
  const char *buf = "Hello! I am the client";
  //    const char *check_buf = "Hello! I am the server";
  switch (event_type) {
    case EVENT_TYPE::WRITE: {
      switch (event_group) {
        case EVENT_GROUP::CLIENT: {
          size_t sent = 0;
          connections_set.at(fd)->write(buf, strlen(buf), sent);
          updateFd(fd, EVENT_TYPE::READ, EVENT_GROUP::CLIENT);
          break;
        }
        default:
          break;
      }
      break;
    }
    case EVENT_TYPE::READ: {
      switch (event_group) {
        case EVENT_GROUP::CLIENT: {
          auto connect = connections_set.at(fd);
          auto a = connect->read();
          if (connect->buffer_size > 0) EXPECT_EQ(connect->buffer_size, 22);
          if (a == IO::IO_RESULT::SUCCESS) {
            deleteFd(fd);
            connections_set.erase(fd);
            delete connect;
            ::close(fd);
          }
          break;
        }
        default:
          break;
      }
      break;
    }
    default:
      break;
  }
}

void ServerHandler::setUp(std::string addr, int port) {
  lst.address = zcutils_net_get_address(addr, port).release();
  lst.listen(*lst.address);
  handleAccept(lst.getFileDescriptor());
}

void ServerHandler::HandleEvent(int fd, EVENT_TYPE event_type,
                                EVENT_GROUP event_group) {
  int new_fd;
  const char *buf = "Hello! I am the server";

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
            new_fd = Connection::doAccept(lst.getFileDescriptor());
            if (new_fd > 0)
              addFd(new_fd, EVENT_TYPE::READ, EVENT_GROUP::SERVER);
          } while (new_fd > 0);
          break;
        }
        default:
          break;
      }
      break;
    }
    case EVENT_TYPE::READ: {
      switch (event_group) {
        case EVENT_GROUP::SERVER: {
          Connection connection;
          connection.setFileDescriptor(fd);
          std::array<char, 50> data;
          auto res = ::read(fd, data.data(), 50);
          if (data.size() > 0) EXPECT_EQ(res, 22);
          updateFd(fd, EVENT_TYPE::WRITE, EVENT_GROUP::SERVER);
          break;
        }
        default:
          break;
      }
      break;
    }
    case EVENT_TYPE::WRITE: {
      switch (event_group) {
        case EVENT_GROUP::SERVER: {
          write(fd, buf, strlen(buf));
          updateFd(fd, EVENT_TYPE::READ, EVENT_GROUP::SERVER);
          break;
        }
        default:
          break;
      }
      break;
    }
    default:
      break;
  }
}
