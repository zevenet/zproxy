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

#include <atomic>
#include <chrono>

namespace Statistics {
enum BACKENDSTATS_PARAMETER {
  BP_RESPONSE_TIME,
  BP_CONN_TIME,
  BP_COMPLETE_RESPONSE_TIME,
  BP_ESTABLISHED_CONN,
  BP_PENDING_CONN,
  BP_TOTAL_CONN,
};

class BackendInfo {
 protected:
  std::chrono::steady_clock::time_point current_time;
  std::atomic<double> max_response_time;
  std::atomic<double> avg_response_time;
  std::atomic<double> min_response_time;
  std::atomic<double> avg_conn_time;
  std::atomic<double> avg_complete_response_time;
  std::atomic<int> established_conn;
  std::atomic<int> total_connections;
  std::atomic<int> pending_connections;
  // TODO: TRANSFERENCIA BYTES/SEC (NO HACER)
  // TODO: WRITE/READ TIME (TIEMPO COMPLETO)
 public:
  void setAvgResponseTime(double latency);

  void setMinResponseTime(double latency);

  void setMaxResponseTime(double latency);

  void setAvgConnTime(double latency);

 public:
  BackendInfo();

  ~BackendInfo();

  void increaseConnection();

  void setAvgTransferTime(double latency);

  void decreaseConnection();

  void increaseTotalConn();

  void increaseConnTimeoutAlive();

  void decreaseConnTimeoutAlive();

  int getPendingConn();

  int getAssignedConn();

  int getEstablishedConn();

  double getAvgLatency();

  void calculateLatency(double latency);

  double getConnPerSec();
};
}  // namespace Statistics
