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
#include "../util/time.h"
#include "../util/common.h"
#include "../http/http.h"

namespace Statistics
{
	enum BACKENDSTATS_PARAMETER
	{
		BP_RESPONSE_TIME,
		BP_CONN_TIME,
		BP_COMPLETE_RESPONSE_TIME,
		BP_ESTABLISHED_CONN,
		BP_PENDING_CONN,
		BP_TOTAL_CONN,
	};

	class HttpResponseHits
	{
		public:
		std::atomic < int >code_2xx {0};
		std::atomic < int >code_3xx {0};
		std::atomic < int >code_4xx {0};
		std::atomic < int >code_5xx {0};
		std::atomic < int >others {0};
#if WAF_ENABLED
		std::atomic < int >waf {0};
#endif

		inline void increaseCode(http::Code codeName)
		{
			int code = helper::to_underlying(codeName) / 100;

			if (code == 2) {
				code_2xx++;
			} else if (code == 3) {
				code_3xx++;
			} else if (code == 4) {
				code_4xx++;
			} else if (code == 5) {
				code_5xx++;
			} else {
				others++;
			}
		}
#if WAF_ENABLED
		inline void increaseWaf()
		{
			waf++;
		}
#endif
	};

	class ListenerInfo
	{
		public:
	  std::atomic < int > total_connections {0}; // sumatory of backend connections
	  std::atomic < int > established_connection {0};
	};


	class BackendInfo
	{
	      protected:
		std::atomic < double >max_response_time;
		  std::atomic < double >avg_response_time;
		  std::atomic < double >min_response_time;
		  std::atomic < double >avg_conn_time;
		  std::atomic < double >avg_complete_response_time;
		  std::atomic < int >established_conn;
		  std::atomic < int >total_connections;
		  std::atomic < int >pending_connections;
		  public:
		  ListenerInfo *listener_stats {nullptr};
		protected:
		time_t current_time;
		// TODO: TRANSFERENCIA BYTES/SEC (NO HACER)
		// TODO: WRITE/READ TIME (TIEMPO COMPLETO)
	      public:
		void setAvgResponseTime(double latency);

		void setMinResponseTime(double latency);

		void setMaxResponseTime(double latency);

		void setAvgConnTime(const timeval & start_time);

	      public:
		  BackendInfo();

		 ~BackendInfo();

		void increaseConnection();

		void setAvgTransferTime(const timeval & start_time);

		inline void decreaseConnection()
		{
			if (established_conn.load() > 0) {
				established_conn--;
				if (listener_stats != nullptr && listener_stats->total_connections > 0)
					listener_stats->total_connections--;
			}
		}

		inline void increaseTotalConn()
		{
			if (total_connections.load() > 0) {
				total_connections++;
			}
		}

		inline void increaseConnTimeoutAlive()
		{
			pending_connections++;
		}

		inline void decreaseConnTimeoutAlive()
		{
			if (pending_connections.load() > 0)
				pending_connections--;
		}

		inline int getPendingConn()
		{
			return pending_connections;
		}

		inline int getAssignedConn()
		{
			return total_connections;
		}

		inline int getEstablishedConn()
		{
			return established_conn;
		}

		inline double getAvgLatency()
		{
			return avg_response_time;
		}

		inline void calculateLatency(const timeval & start_time)
		{
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

		inline double getConnPerSec()
		{
			return total_connections / 60.0;
		}
	};
}				// namespace Statistics
