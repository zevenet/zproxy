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
#include "../config/config_data.h"
#include "../connection/connection.h"
#include "../ctl/ctl.h"
#include "../ctl/observer.h"
#include "../json/json_data_value_types.h"
#include "backend.h"
#include "http_session_manager.h"
#include <vector>
#if CACHE_ENABLED
#include "../cache/http_cache.h"
#endif
using namespace json;

/**
 * @class Service Service.h "src/service/Service.h"
 * @brief The Service class contains the configuration parameters set in the
 * service section.
 *
 * This class contains the backend set in the configuration file and inherits
 * from sessions::HttpSessionManager to be able to manage all the sessions of
 * this Service.
 */
class Service : public sessions::HttpSessionManager,
		public CtlObserver<ctl::CtlTask, std::string> {
	std::vector<Backend *> backend_set;
	std::vector<Backend *> emergency_backend_set;

	/**
   * @brief It checks if the backend is ready to manage the request.
   *
   * It checks if the backend accomplishment the requirement to get the connection:
   * the status is up, the limit of connections were not reached...
   *
   * @param the backend struct to check.
   * @param the current service priority, the backend one has to be lower or equal to this value.
   * @return is true if the backend is available, or false if it's not.
   */
	bool checkBackendAvailable(Backend *bck);

	/**
   * @brief It sort the list of backend based on the priority
   *
   * It returns a vector with the backend index ordered by backend priority
   *
   * @return is the backend indexes vector
   */
	std::vector<int> sortBackendsByPrio();

	/**
   * @brief It modifies the backend index and get the following one
   *
   * This function checks if the index get the last possition and restart index in that case.
   * It resets the connection counter too.
   *
   * It is used for the round robin algorithm
   *
   * @param is the current backend id passed by reference.
   * @param is the counter passed by reference.
   * @param is the number of backends in the service.
   */
	void getNextBackendIndex(int *bck_id, int *bck_counter,
				 int bck_list_size);

	/**
   * @brief It selects the backend to forward the incoming request
   *
   * This function check the backends of the service and it decides which will
   * receive the request using the configured algorithm.
   *
   * If no backend available, return an emergency backend if possible.
   *
   * @return always a Backend. A new one or the associated to the session.
   */
	Backend *getNextBackend();

	std::mutex mtx_lock;

    public:
	/** True if the Service is disabled, false if it is enabled. */
#if CACHE_ENABLED
	bool cache_enabled = false;
	std::shared_ptr<HttpCache> http_cache;
#endif
	std::atomic<bool> disabled{ false };
	/** If a backend change of status, this flag is enabled
	 * to update the service priority limit*/
	std::atomic<bool> update_piority{ false };
	std::atomic<int> backend_priority{ 1 };
	/** Service id. */
	int id;
	bool ignore_case;
	std::string name;
	/** Backend Cookie Name */
	std::string becookie,
		/** Backend Cookie domain */
		becdomain,
		/** Backend cookie path */
		becpath;
	/** Backend cookie age */
	int becage;
	/** True if the connection if pinned, false if not. */
	bool pinned_connection;
	ROUTING_POLICY routing_policy;
	ReplaceHeader *rewr_url{ nullptr };
	int rewr_loc, rewr_loc_path;

    private:
	bool addBackend(JsonObject *json_object);

    public:
	/** ServiceConfig from the Service. */
	ServiceConfig &service_config;

	/**
   * @brief it returns a vector with the service backends
   */
	std::vector<Backend *> getBackends();

	/**
   * @brief It updates the maximum backend priority for the service
   *
   * This values does as limit, the backends that have a priority as this
   * o minor will entry in the active backend pool
   *
   */
	void updateBackendPriority();

	/**
   * @brief Checks if we need a new backend or not.
   *
   * If we already have a session it returns the backend associated to the
   * session. If not, it returns a new Backend.
   *
   * @param stream to get the information to decide if we have already a session
   * for it.
   * @return always a Backend. A new one or the associated to the session.
   */
	Backend *getBackend(Connection &source, HttpRequest &request);
	explicit Service(ServiceConfig &service_config_);
	~Service() final;

	/**
   * @brief Creates a new Backend from a BackendConfig.
   *
   * Creates a new Backend from the @p backend_config and adds it to the
   * service's backend vector.
   *
   * @param backend_config to get the Backend information.
   * @param backend_id to assign the Backend.
   * @param emergency set the Backend as emergency.
   */
	void addBackend(std::shared_ptr<BackendConfig> backend_config,
			int backend_id, bool emergency = false);

	/**
   * @brief Checks if the backends still alive and deletes the expired sessions.
   */
	void doMaintenance();

	/**
   * @brief Check if the Service should handle the HttpRequest.
   *
   * It checks the request line, required headers and the forbidden headers. If
   * the Service should handle it, returns true if not false.
   *
   * @param request to check.
   * @return @c true or @c false if the Service should handle the @p request or
   * not.
   */
	bool doMatch(HttpRequest &request);
	static void setBackendsPriorityBy(BACKENDSTATS_PARAMETER);
	Backend *getEmergencyBackend();

	/**
   * @brief This function handles the @p tasks received with the API format.
   *
   * It calls the needed functions depending on the @p task received. The task
   * must be a API formatted request.
   *
   * @param task to check.
   * @return json formatted string with the result of the operation.
   */
	std::string handleTask(ctl::CtlTask &task) override;

	/**
   * @brief Checks if the Service should handle the @p task.
   *
   * @param task to check.
   * @return true if should handle the task, false if not.
   */
	bool isHandler(ctl::CtlTask &task) override;

	/**
   * @brief Generates a JsonObject with all the Service information.
   * @return JsonObject with the Service information.
   */
	std::unique_ptr<JsonObject> getServiceJson();
	inline int getBackendSetSize()
	{
		return backend_set.size();
	}
	bool setBackendHostInfo(Backend *backend);

	inline void initBackendStats(Statistics::ListenerInfo *listener_stats)
	{
		for (auto &bck : backend_set) {
			bck->listener_stats = listener_stats;
		}
	}
};
