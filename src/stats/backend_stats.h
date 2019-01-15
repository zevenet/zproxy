#pragma once

#include <chrono>
#include <atomic>

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
    //TODO: TRANSFERENCIA BYTES/SEC (NO HACER)
    //TODO: WRITE/READ TIME (TIEMPO COMPLETO)
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
}
