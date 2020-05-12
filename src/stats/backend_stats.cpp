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
#include "backend_stats.h"
#include "../util/time.h"

void Statistics::BackendInfo::setAvgResponseTime(double latency) {
  if (avg_response_time < 0) {
    avg_response_time = latency;
  } else {
    avg_response_time = (avg_response_time + latency) / 2;
  }
}

void Statistics::BackendInfo::setMinResponseTime(double latency) {
  if (min_response_time < 0) {
    min_response_time = latency;
  } else if (latency < min_response_time) {
    min_response_time = latency;
  }
}

void Statistics::BackendInfo::setMaxResponseTime(double latency) {
  if (latency > max_response_time) max_response_time = latency;
}

void Statistics::BackendInfo::setAvgConnTime(const timeval & start_time) {
  double latency = Time::getDiff(start_time);
  if (avg_conn_time < 0) {
    avg_conn_time = latency;
  } else {
    avg_conn_time = (avg_conn_time + latency) / 2;
  }
}

Statistics::BackendInfo::BackendInfo() {
  current_time = Time::getTimeSec();
  established_conn = 0;
  total_connections = 0;
  pending_connections = 0;
  max_response_time = -1;
  avg_response_time = -1;
  min_response_time = -1;
  avg_conn_time = -1;
  avg_complete_response_time = -1;
}

Statistics::BackendInfo::~BackendInfo() {}

void Statistics::BackendInfo::increaseConnection() { established_conn++; }

void Statistics::BackendInfo::setAvgTransferTime(const timeval & start_time ){
  if (Time::getTimeSec() - current_time > 60) {
    avg_complete_response_time = -1;
    current_time = Time::getTimeSec();
  }
  auto latency = Time::getDiff(start_time);
  if (avg_complete_response_time < 0) {
    avg_complete_response_time = latency;
  } else {
    avg_complete_response_time = (avg_complete_response_time + latency) / 2;
  }
}

void Statistics::BackendInfo::decreaseConnection() { established_conn--; }

void Statistics::BackendInfo::increaseTotalConn() { total_connections++; }

void Statistics::BackendInfo::increaseConnTimeoutAlive() { pending_connections++; }

void Statistics::BackendInfo::decreaseConnTimeoutAlive() { pending_connections--; }

int Statistics::BackendInfo::getPendingConn() { return pending_connections; }

int Statistics::BackendInfo::getAssignedConn() { return total_connections; }

int Statistics::BackendInfo::getEstablishedConn() { return established_conn; }

double Statistics::BackendInfo::getAvgLatency() { return avg_response_time; }

void Statistics::BackendInfo::calculateLatency(const timeval & start_time) {
//  if (Time::getTimeSec() - current_time > 60) {
//    total_connections = 0;
//    max_response_time = -1;
//    avg_response_time = -1;
//    min_response_time = -1;
//  }
//  current_time = Time::getTimeSec();

  double latency = Time::getDiff(start_time);
  setAvgResponseTime(latency);
  setMaxResponseTime(latency);
  setMinResponseTime(latency);
}

double Statistics::BackendInfo::getConnPerSec() { return total_connections / 60; }
