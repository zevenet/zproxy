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

#include "service.h"
#include <numeric>
#include "../../zcutils/zcutils.h"
#include "../../zcutils/zcu_network.h"

Backend *Service::getBackend(Connection &source, HttpRequest &request)
{
	if (backend_set.empty())
		return getEmergencyBackend();

	if (session_type != sessions::SESS_NONE) {
		auto session = getSession(source, request);
		if (session != nullptr) {
			if (session->assigned_backend->getStatus() !=
			    BACKEND_STATUS::BACKEND_UP) {
				// invalidate all sessions backend is down
				deleteBackendSessions(
					session->assigned_backend->backend_id);
				return getBackend(source, request);
			}
			session->update();
			return session->assigned_backend;
		} else {
			// get a new backend
			// need to set a new backend server for the newly created session!!!!
			Backend *new_backend = nullptr;
			if ((new_backend = getNextBackend()) != nullptr) {
				session = addSession(source, request,
						     *new_backend);
				if (session == nullptr) {
					zcu_log_print(
						LOG_DEBUG,
						"Error adding new session, session info not found in request");
				}
			}
			return new_backend;
		}
	} else {
		return getNextBackend();
	}
}

bool Service::setBackendHostInfo(Backend *backend)
{
	if (backend == nullptr)
		return false;
	::freeaddrinfo(backend->address_info);
	auto address = zcu_net_get_address(backend->address, backend->port);
	if (address == nullptr) {
		// maybe the backend still not available, we set it as down;
		backend->setStatus(BACKEND_STATUS::BACKEND_DOWN);
		zcu_log_print(
			LOG_INFO,
			"srv: %s,  Could not resolve backend host \" %s \" .",
			this->name.data(), backend->address.data());
		return false;
	}
	backend->address_info = address.release();
	//  if (zcu_net_get_address(backend->address.data(), backend->address_info, PF_UNSPEC, backend->port)) {
	//    // maybe the backend still not available, we set it as down;
	//    backend->setStatus(BACKEND_STATUS::BACKEND_DOWN);
	//    zcu_log_print(LOG_INFO, "srv: %s,  Could not resolve backend host \" %s \" .", this->name.data(),
	//                   backend->address.data());
	//    return false;
	//  }
	if (backend->address_info == nullptr)
		return false;
	if (becookie.empty())
		return true;
	if (backend->backend_config->bekey.empty()) {
		char lin[ZCU_DEF_BUFFER_SIZE];
		char *cp;
		if (backend->address_info->ai_family == AF_INET)
			snprintf(lin, ZCU_DEF_BUFFER_SIZE - 1, "4-%08x-%x",
				 htonl((reinterpret_cast<sockaddr_in *>(
						backend->address_info->ai_addr))
					       ->sin_addr.s_addr),
				 htons((reinterpret_cast<sockaddr_in *>(
						backend->address_info->ai_addr))
					       ->sin_port));
		else if (backend->address_info->ai_family == AF_INET6) {
			cp = reinterpret_cast<char *>(
				&((reinterpret_cast<sockaddr_in6 *>(
					   backend->address_info->ai_addr))
					  ->sin6_addr));
			snprintf(
				lin, ZCU_DEF_BUFFER_SIZE - 1,
				"6-%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%"
				"02x%02x-%x",
				cp[0], cp[1], cp[2], cp[3], cp[4], cp[5], cp[6],
				cp[7], cp[8], cp[9], cp[10], cp[11], cp[12],
				cp[13], cp[14], cp[15],
				htons((reinterpret_cast<sockaddr_in6 *>(
					       backend->address_info->ai_addr))
					      ->sin6_port));
		} else {
			backend->setStatus(BACKEND_STATUS::BACKEND_DOWN);
			zcu_log_print(
				LOG_NOTICE,
				"cannot autogenerate backendkey, please specify one'");
			return false;
		}
		backend->bekey = becookie;
		backend->bekey += "=";
		backend->bekey += std::string(lin);

		if (!becdomain.empty())
			backend->bekey += "; Domain=" + becdomain;
		if (!becpath.empty())
			backend->bekey += "; Path=" + becpath;

		if (becage != 0) {
			backend->bekey += "; Max-Age=";
			if (becage > 0) {
				backend->bekey += std::to_string(becage * 1000);
			} else {
				backend->bekey += std::to_string(ttl * 1000);
			}
		}
	}
	return true;
}

void Service::addBackend(std::shared_ptr<BackendConfig> backend_config,
			 int backend_id, bool emergency)
{
	auto backend = std::make_unique<Backend>();
	backend->status_flag = &this->update_piority;
	backend->backend_config = backend_config;
	backend->backend_id = backend_id;
	backend->weight = backend_config->weight;
	backend->priority = backend_config->priority;
	backend->name = "bck_" + std::to_string(backend_id);
	backend->setStatus(backend_config->disabled ?
					 BACKEND_STATUS::BACKEND_DISABLED :
					 BACKEND_STATUS::BACKEND_UP);
	if (backend_config->be_type == 0) {
		backend->address = std::move(backend_config->address);
		backend->port = backend_config->port;
		backend->backend_type = BACKEND_TYPE::REMOTE;
		backend->nf_mark = backend_config->nf_mark;
		backend->ctx = backend_config->ctx;
		backend->conn_timeout = backend_config->conn_to;
		backend->response_timeout = backend_config->rw_timeout;
		backend->connection_limit = backend_config->connection_limit;
		setBackendHostInfo(backend.get());
	} else if (backend_config->be_type == 2) {
		backend->backend_type = BACKEND_TYPE::TEST_SERVER;
	} else if (backend_config->be_type >= 300) {
		backend->backend_type = BACKEND_TYPE::REDIRECT;
	}
	if (emergency)
		emergency_backend_set.push_back(backend.release());
	else
		backend_set.push_back(backend.release());
}

bool Service::addBackend(JsonObject *json_object)
{
	if (json_object == nullptr) {
		return false;
	} else { // Redirect
		auto config = std::make_unique<Backend>();
		if (json_object->count(JSON_KEYS::ID) > 0 &&
		    json_object->at(JSON_KEYS::ID)->isValue()) {
			config->backend_id =
				dynamic_cast<JsonDataValue *>(
					json_object->at(JSON_KEYS::ID).get())
					->number_value;
		} else {
			return false;
		}

		if (json_object->count(JSON_KEYS::WEIGHT) > 0 &&
		    json_object->at(JSON_KEYS::WEIGHT)->isValue()) {
			config->weight =
				dynamic_cast<JsonDataValue *>(
					json_object->at(JSON_KEYS::WEIGHT).get())
					->number_value;
		} else {
			return false;
		}

		if (json_object->count(JSON_KEYS::NAME) > 0 &&
		    json_object->at(JSON_KEYS::NAME)->isValue()) {
			config->name =
				dynamic_cast<JsonDataValue *>(
					json_object->at(JSON_KEYS::NAME).get())
					->string_value;
		} else {
			config->name =
				"bck_" + std::to_string(config->backend_id);
		}

		if (json_object->count(JSON_KEYS::ADDRESS) > 0 &&
		    json_object->at(JSON_KEYS::ADDRESS)->isValue()) {
			config->address =
				dynamic_cast<JsonDataValue *>(
					json_object->at(JSON_KEYS::ADDRESS)
						.get())
					->string_value;
			setBackendHostInfo(config.get());
		} else {
			return false;
		}

		if (json_object->count(JSON_KEYS::PORT) > 0 &&
		    json_object->at(JSON_KEYS::PORT)->isValue()) {
			config->port =
				dynamic_cast<JsonDataValue *>(
					json_object->at(JSON_KEYS::PORT).get())
					->number_value;
		} else {
			return false;
		}
		config->setStatus(BACKEND_STATUS::BACKEND_DISABLED);
		config->backend_type = BACKEND_TYPE::REMOTE;
		backend_set.push_back(config.release());
	}

	return true;
}

Service::Service(ServiceConfig &service_config_)
	: service_config(service_config_)
{
	//  ctl::ControlManager::getInstance()->attach(std::ref(*this));
	// session data initialization
	name = std::string(service_config.name);
	disabled = service_config.disabled;
	pinned_connection = service_config.pinned_connection == 1;

	// Information related with the setCookie
	if (service_config.becookie != nullptr)
		becookie = std::string(service_config.becookie);
	if (service_config.becdomain != nullptr)
		becdomain = std::string(service_config.becdomain);
	if (service_config.becpath != nullptr)
		becpath = std::string(service_config.becpath);
	becage = service_config.becage;
	this->session_type = static_cast<sessions::HttpSessionType>(
		service_config_.sess_type);
	this->ttl = static_cast<unsigned int>(service_config_.sess_ttl);
	this->sess_id = service_config_.sess_id;
	if (this->session_type != sessions::HttpSessionType::SESS_HEADER)
		this->sess_id += '=';
	this->sess_pat = service_config_.sess_pat;
	this->sess_start = service_config_.sess_start;
	this->routing_policy =
		static_cast<ROUTING_POLICY>(service_config_.routing_policy);
#ifdef CACHE_ENABLED
	// Initialize cache manager
	if (service_config_.cache_content.re_pcre != nullptr) {
		this->cache_enabled = true;
		http_cache = make_shared<HttpCache>();
		http_cache->cacheInit(&service_config.cache_content,
				      service_config.cache_timeout,
				      service_config.name,
				      service_config.cache_size,
				      service_config.cache_threshold,
				      service_config.f_name,
				      service_config.cache_ram_path,
				      service_config.cache_disk_path);
		http_cache->cache_max_size = service_config.cache_max_size;
	}
#endif
	// backend initialization
	int backend_id = 0;
	for (auto bck = service_config_.backends; bck != nullptr;
	     bck = bck->next) {
		if (!bck->disabled) {
			this->addBackend(bck, backend_id++);
			// this->addBackend(bck->address, bck->port, backend_id++);
		} else {
			zcu_log_print(LOG_NOTICE, "Backend %s:%s disabled",
				      bck->address, std::to_string(bck->port));
		}
	}
	for (auto bck = service_config_.emergency; bck != nullptr;
	     bck = bck->next) {
		if (!bck->disabled) {
			this->addBackend(bck, backend_id++, true);
			// this->addBackend(bck->address, bck->port, backend_id++);
		} else {
			zcu_log_print(LOG_NOTICE,
				      "Emergency Backend %s:%s disabled",
				      bck->address, std::to_string(bck->port));
		}
	}
}

bool Service::doMatch(HttpRequest &request)
{
	int i, found;

	/* check for request */
	regmatch_t eol{ 0, static_cast<regoff_t>(request.path_length) };
	for (auto m = service_config.url; m; m = m->next)
		if (regexec(&m->pat, request.path, 1, &eol, REG_STARTEND) != 0)
			return false;

	/* check for required headers */
	for (auto m = service_config.req_head; m; m = m->next) {
		for (found = i = 0;
		     i < static_cast<int>(request.num_headers) && !found; i++) {
			eol.rm_so = 0;
			eol.rm_eo = request.headers[i].line_size;
			if (regexec(&m->pat, request.headers[i].name, 1, &eol,
				    REG_STARTEND) == 0)
				found = 1;
		}
		if (!found)
			return false;
	}

	/* check for forbidden headers */
	for (auto m = service_config.deny_head; m; m = m->next) {
		for (found = i = 0; i < static_cast<int>(request.num_headers);
		     i++) {
			eol.rm_so = 0;
			eol.rm_eo = request.headers[i].line_size;
			if (regexec(&m->pat, request.headers[i].name, 1, &eol,
				    REG_STARTEND) == 0)
				return false;
		}
	}
	return true;
}

void Service::setBackendsPriorityBy(BACKENDSTATS_PARAMETER)
{
	// TODO: DYNSCALE DEPENDING ON BACKENDSTAT PARAMETER
}

std::string Service::handleTask(ctl::CtlTask &task)
{
	if (!isHandler(task))
		return JSON_OP_RESULT::ERROR;
	zcu_log_print(LOG_DEBUG, "%s():%d: service %d handling task",
		      __FUNCTION__, __LINE__, id);
	if (task.backend_id > -1) {
		for (auto backend : backend_set) {
			if (backend->isHandler(task))
				return backend->handleTask(task);
		}
		return JSON_OP_RESULT::ERROR;
	}
#ifdef CACHE_ENABLED
	if (this->cache_enabled && task.subject == ctl::CTL_SUBJECT::CACHE) {
		return http_cache->handleCacheTask(task);
	} else {
#endif
		switch (task.command) {
		case ctl::CTL_COMMAND::DELETE: {
			if (task.subject == ctl::CTL_SUBJECT::SESSION) {
				if (!task.data.empty()) {
					auto json_data =
						JsonParser::parse(task.data);
					if (!deleteSession(*json_data))
						return JSON_OP_RESULT::ERROR;
				} else {
					flushSessions();
				}
				return JSON_OP_RESULT::OK;
			} else if (task.subject == ctl::CTL_SUBJECT::BACKEND) {
				// TODO::Implement
			} else if (task.subject == ctl::CTL_SUBJECT::CONFIG) {
				// TODO::Implements
			}
			return "";
		}
		case ctl::CTL_COMMAND::ADD: {
			switch (task.subject) {
			case ctl::CTL_SUBJECT::SESSION: {
				auto json_data = JsonParser::parse(task.data);
				if (!addSession(json_data.get(), backend_set))
					return JSON_OP_RESULT::ERROR;
				return JSON_OP_RESULT::OK;
			}
			case ctl::CTL_SUBJECT::S_BACKEND: {
				auto json_data = JsonParser::parse(task.data);
				if (!addBackend(json_data.get()))
					return JSON_OP_RESULT::ERROR;
				return JSON_OP_RESULT::OK;
			}
			default:
				break;
			}
			break;
		}
		case ctl::CTL_COMMAND::GET:
			switch (task.subject) {
			case ctl::CTL_SUBJECT::SESSION: {
				JsonObject response;
				response.emplace(JSON_KEYS::SESSIONS,
						 getSessionsJson());
				return response.stringify();
			}
			case ctl::CTL_SUBJECT::STATUS: {
				JsonObject status;
				status.emplace(
					JSON_KEYS::STATUS,
					std::make_unique<JsonDataValue>(
						this->disabled ?
							      JSON_KEYS::STATUS_DOWN :
							      JSON_KEYS::
								STATUS_ACTIVE));
				return status.stringify();
			}
			case ctl::CTL_SUBJECT::BACKEND:
			default:
				auto response = getServiceJson();
				return response != nullptr ?
						     response->stringify() :
						     "";
			}
		case ctl::CTL_COMMAND::UPDATE:
			switch (task.subject) {
			case ctl::CTL_SUBJECT::CONFIG:
				// TODO:: update service config (timeouts, headers, routing policy)
				break;
			case ctl::CTL_SUBJECT::SESSION: {
				return getSessionsJson()->stringify();
			}
			case ctl::CTL_SUBJECT::STATUS: {
				std::unique_ptr<JsonObject> status(
					JsonParser::parse(task.data));
				if (status == nullptr)
					return JSON_OP_RESULT::ERROR;
				if (status->at(JSON_KEYS::STATUS)->isValue()) {
					auto value =
						dynamic_cast<JsonDataValue *>(
							status->at(JSON_KEYS::
									   STATUS)
								.get())
							->string_value;
					if (value == JSON_KEYS::STATUS_ACTIVE ||
					    value == JSON_KEYS::STATUS_UP) {
						this->disabled = false;
					} else if (value ==
						   JSON_KEYS::STATUS_DOWN) {
						this->disabled = true;
					} else if (value ==
						   JSON_KEYS::STATUS_DISABLED) {
						this->disabled = true;
					}
					zcu_log_print(LOG_NOTICE,
						      "set Service %d %s", id,
						      value.c_str());
					return JSON_OP_RESULT::OK;
				}
				break;
			}
			default:
				break;
			}
			break;
		default:
			return JSON_OP_RESULT::OK;
		}
#ifdef CACHE_ENABLED
	}
#endif
	return "";
}

bool Service::isHandler(ctl::CtlTask &task)
{
	return /*task.target == ctl::CTL_HANDLER_TYPE::SERVICE && */
		(task.service_id == this->id || task.service_id == -1);
}

std::unique_ptr<JsonObject> Service::getServiceJson()
{
	auto root = std::make_unique<JsonObject>();
	root->emplace(JSON_KEYS::NAME,
		      std::make_unique<JsonDataValue>(this->name));
	root->emplace(JSON_KEYS::ID, std::make_unique<JsonDataValue>(this->id));
	root->emplace(JSON_KEYS::PRIORITY,
		      std::make_unique<JsonDataValue>(this->backend_priority));
	root->emplace(JSON_KEYS::STATUS,
		      std::make_unique<JsonDataValue>(
			      this->disabled ? JSON_KEYS::STATUS_DISABLED :
						     JSON_KEYS::STATUS_ACTIVE));
	auto backends_array = std::make_unique<JsonArray>();
	for (auto backend : backend_set) {
		auto bck = backend->getBackendJson();
		backends_array->emplace_back(std::move(bck));
	}
	root->emplace(JSON_KEYS::BACKENDS, std::move(backends_array));
	root->emplace(JSON_KEYS::SESSIONS, this->getSessionsJson());
	return std::move(root);
}

bool Service::checkBackendAvailable(Backend *bck)
{
	bool valid;
	valid = (bck->getStatus() != BACKEND_STATUS::BACKEND_UP ||
		 bck->priority > backend_priority ||
		 bck->weight <= 0 /* This line maybe is not required */
		 || bck->isConnectionLimit() /* This is an early check */
		 ) ?
			      false :
			      true;

	return valid;
}

std::vector<int> Service::sortBackendsByPrio()
{
	std::vector<int> sorted_index;

	for (int index = 0; index < backend_set.size(); index++) {
		if (sorted_index.empty())
			sorted_index.insert(sorted_index.begin(), index);
		else {
			for (int index2 = 0; index2 < sorted_index.size();
			     index2++) {
				if (backend_set[sorted_index[index2]]->priority >
				    backend_set[index]->priority) {
					sorted_index.insert(
						sorted_index.begin() + index2,
						index);
					break;
				} else if (index2 ==
					   sorted_index.size() -
						   1) { // last item and the greater
					sorted_index.emplace_back(index);
					break;
				}
			}
		}
	}
	return sorted_index;
}

void Service::updateBackendPriority()
{
	int enabled_priority = 1;
	std::vector<int> sort_bcks;

	if (!update_piority)
		return;
	update_piority = false;

	if (backend_set.empty()) {
		backend_priority = enabled_priority;
		return;
	}

	sort_bcks = sortBackendsByPrio();
	// set the minimum value
	for (int index = 0; index < backend_set.size(); index++) {
		if (backend_set[sort_bcks[index]]->priority <=
			    enabled_priority &&
		    backend_set[sort_bcks[index]]->getStatus() !=
			    BACKEND_STATUS::BACKEND_UP) {
			enabled_priority++;
		} else
			break;
	}

	backend_priority = enabled_priority;
}

void Service::getNextBackendIndex(int *bck_id, int *bck_counter,
				  int bck_list_size)
{
	*bck_counter = 0;
	*bck_id += 1;

	if (*bck_id >= bck_list_size)
		*bck_id = 0;
}

/** Selects the corresponding Backend to which the connection will be routed
 * according to the established balancing algorithm. */
Backend *Service::getNextBackend()
{
	if (backend_set.empty())
		return nullptr;
	else if (backend_set.size() == 1)
		return backend_set[0]->getStatus() !=
				       BACKEND_STATUS::BACKEND_UP ?
				     nullptr :
				     backend_set[0];

	updateBackendPriority();

	switch (routing_policy) {
	default:
	case ROUTING_POLICY::ROUND_ROBIN: {
		static int backend_id = 0;
		static int backend_counter = 0;

		Backend *selected_backend = nullptr;
		int bck_size = static_cast<int>(backend_set.size());

		for (int i = 0; i < bck_size; i++) {
			selected_backend = backend_set[backend_id];

			if (!checkBackendAvailable(selected_backend))
				getNextBackendIndex(&backend_id,
						    &backend_counter, bck_size);
			else {
				backend_counter++;
				if (selected_backend->weight <= backend_counter)
					getNextBackendIndex(&backend_id,
							    &backend_counter,
							    bck_size);
				return selected_backend;
			}
		}
		break;
	}

	case ROUTING_POLICY::W_LEAST_CONNECTIONS: {
		Backend *selected_backend = nullptr;
		for (auto &it : backend_set) {
			if (!checkBackendAvailable(it))
				continue;
			if (selected_backend == nullptr) {
				selected_backend = it;
			} else {
				if (selected_backend->getEstablishedConn() == 0)
					return selected_backend;
				if (selected_backend->getEstablishedConn() *
					    it->weight >
				    it->getEstablishedConn() *
					    selected_backend->weight)
					selected_backend = it;
			}
		}
		return selected_backend;
		break;
	}

	case ROUTING_POLICY::RESPONSE_TIME: {
		Backend *selected_backend = nullptr;
		for (auto &it : backend_set) {
			if (!checkBackendAvailable(it))
				continue;
			if (selected_backend == nullptr) {
				selected_backend = it;
			} else {
				if (selected_backend->getAvgLatency() < 0)
					return selected_backend;
				if (it->getAvgLatency() *
					    selected_backend->weight >
				    selected_backend->getAvgLatency() *
					    selected_backend->weight)
					selected_backend = it;
			}
		}
		return selected_backend;
		break;
	}

	case ROUTING_POLICY::PENDING_CONNECTIONS: {
		Backend *selected_backend = nullptr;

		for (auto &it : backend_set) {
			if (!checkBackendAvailable(it))
				continue;
			if (selected_backend == nullptr) {
				selected_backend = it;
			} else {
				if (selected_backend->getPendingConn() == 0)
					return selected_backend;
				if (selected_backend->getPendingConn() *
					    selected_backend->weight >
				    it->getPendingConn() *
					    selected_backend->weight)
					selected_backend = it;
			}
		}
		return selected_backend;
		break;
	}
	}
	return getEmergencyBackend();
}

void Service::doMaintenance()
{
	HttpSessionManager::doMaintenance();
	for (Backend *bck : this->backend_set) {
		if (bck->backend_type != BACKEND_TYPE::REMOTE)
			continue;
		if (setBackendHostInfo(bck)) {
			bck->doMaintenance();
		}
		if (bck->getStatus() == BACKEND_STATUS::BACKEND_DOWN) {
			deleteBackendSessions(bck->backend_id);
		}
	}
#ifdef CACHE_ENABLED
	if (this->cache_enabled) {
		http_cache->doCacheMaintenance();
	}
#endif
}

/** There is not backend available, trying to pick an emergency backend. If
 * there is not an emergency backend available it returns nullptr. */
Backend *Service::getEmergencyBackend()
{
	// There is no backend available, looking for an emergency backend.
	if (emergency_backend_set.empty())
		return nullptr;
	Backend *bck{ nullptr };
	for ([[maybe_unused]] auto &tmp : emergency_backend_set) {
		static uint64_t emergency_seed;
		emergency_seed++;
		bck = emergency_backend_set[emergency_seed % backend_set.size()];
		if (bck != nullptr) {
			if (bck->getStatus() != BACKEND_STATUS::BACKEND_UP) {
				bck = nullptr;
				continue;
			}
			break;
		}
	}
	return bck;
}

Service::~Service()
{
	for (auto &bck : backend_set)
		delete bck;
	//  ctl::ControlManager::getInstance()->deAttach(std::ref(*this));
}
