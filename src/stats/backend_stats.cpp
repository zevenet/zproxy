#include "backend_stats.h"


void Statistics::BackendInfo::setAvgResponseTime(double latency) {
  if (avg_response_time < 0) {
      avg_response_time = latency;
    } else {
      avg_response_time = (avg_response_time + latency)/2;
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
  if (latency > max_response_time)
    max_response_time = latency;
}

void Statistics::BackendInfo::setAvgConnTime(double latency) {
  if (avg_conn_time < 0) {
      avg_conn_time = latency;
    } else {
      avg_conn_time = (avg_conn_time + latency)/2;
    }
}

Statistics::BackendInfo::BackendInfo() {
  current_time = std::chrono::steady_clock::now();
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

void Statistics::BackendInfo::increaseConnection() {
  established_conn++;
}

void Statistics::BackendInfo::setAvgTransferTime(double latency) {
  if (std::chrono::duration_cast<std::chrono::duration<double>>
      (std::chrono::steady_clock::now() - current_time).count() > 60) {
      avg_complete_response_time = -1;
    }
  if (avg_complete_response_time < 0) {
      avg_complete_response_time = latency;
    } else {
      avg_complete_response_time = (avg_complete_response_time + latency)/2;
    }
}

void Statistics::BackendInfo::decreaseConnection() {
  established_conn--;
}

void Statistics::BackendInfo::increaseTotalConn() {
  total_connections++;
}

void Statistics::BackendInfo::increaseConnTimeoutAlive() {
  pending_connections++;
}

void Statistics::BackendInfo::decreaseConnTimeoutAlive() {
  pending_connections--;
}

int Statistics::BackendInfo::getPendingConn() {
  return pending_connections;
}

int Statistics::BackendInfo::getAssignedConn() {
  return total_connections;
}

int Statistics::BackendInfo::getEstablishedConn() {
  return established_conn;
}

double Statistics::BackendInfo::getAvgLatency() {
  return avg_response_time;
}

void Statistics::BackendInfo::calculateLatency(double latency) {
  if (std::chrono::duration_cast<std::chrono::duration<double>>
      (std::chrono::steady_clock::now() - current_time).count() > 60) {
      current_time = std::chrono::steady_clock::now();
      total_connections = 0;
      max_response_time = -1;
      avg_response_time = -1;
      min_response_time = -1;
    }
  setAvgResponseTime(latency);
  setMaxResponseTime(latency);
  setMinResponseTime(latency);
}

double Statistics::BackendInfo::getConnPerSec() {
  return total_connections / 60;
}
