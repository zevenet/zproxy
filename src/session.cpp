/*
 * Copyright (C) 2023  Zevenet S.L. <support@zevenet.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <iterator>
#include "session.h"
#include "monitor.h"

using namespace sessions;

Set::Set(SESS_TYPE type, std::string id, unsigned int ttl)
{
	session_type = type;
	sess_id = id;
	sess_ttl = ttl;
}

Set::~Set()
{
	flushSessions();
}

Info *Set::addSession(std::string &client_addr,
						HttpRequest &request,
						zproxy_backend_cfg *backend_to_assign)
{
	if (session_type == SESS_TYPE::SESS_NONE)
		return nullptr;

	std::string key = getSessionKey(client_addr, request);
	// check if we have a new key to insert,
	if (!key.empty()) {
		auto new_session = new Info(backend_to_assign);

		std::lock_guard<std::recursive_mutex> locker(lock_mtx);
		sessions_set.emplace(std::make_pair(key, new_session));
		return new_session;
	}

	return nullptr;
}

Info *Set::addSession(const std::string &key,
		      struct zproxy_backend_cfg *backend_to_assign)
{
	if (session_type == SESS_TYPE::SESS_NONE)
		return nullptr;

	// check if we have a new key to insert
	if (sessions_set.find(key) == sessions_set.end()) {
		auto new_session = new Info(backend_to_assign);

		std::lock_guard<std::recursive_mutex> locker(lock_mtx);
		sessions_set.emplace(std::make_pair(key, new_session));
		return new_session;
	}

	return nullptr;
}

void Set::update(std::string &client_addr,
						std::string key,
						zproxy_backend_cfg *backend_to_assign)
{
	if (session_type == SESS_TYPE::SESS_NONE)
		return;

	auto sess = sessions_set.find(key);
	if (sess == sessions_set.end()) {
		auto new_session = new Info(backend_to_assign);
		std::lock_guard<std::recursive_mutex> locker(lock_mtx);
		sessions_set.emplace(std::make_pair(key, new_session));
	} else {
		sess->second->update();
	}
}

struct sockaddr_in *
Set::getBackend(std::string &client_addr, HttpRequest &request,
		const char *service_name, bool update_if_exist)
{
	struct zproxy_monitor_backend_state backend_state = {};
	struct sockaddr_in *backend = nullptr;

	if (session_type == SESS_TYPE::SESS_NONE)
		return nullptr;

	auto session = getSession(client_addr, request, update_if_exist);

	if (session != nullptr) {
		if (session->isStatic())
			return &session->bck_addr;
		if (!zproxy_monitor_backend_state(&session->bck_addr,
						  service_name,
						  &backend_state)) {
			return nullptr;
		}
		if (backend_state.status != ZPROXY_MONITOR_UP)
			return nullptr;

		session->update();
		backend = &session->bck_addr;
	}

	return backend;
}

void Set::deleteBackendSessions(zproxy_backend_cfg *backend, bool delete_static)
{
	const struct sockaddr_in *backend_addr = &backend->runtime.addr;
	std::lock_guard<std::recursive_mutex> locker(lock_mtx);
	auto it = sessions_set.cbegin();

	while (it != sessions_set.cend()) {
		const struct sockaddr_in *sess_bck_addr = &it->second->bck_addr;

		if (it->second != nullptr &&
		    sess_bck_addr->sin_addr.s_addr == backend_addr->sin_addr.s_addr &&
		    sess_bck_addr->sin_port == backend_addr->sin_port &&
		    (!it->second->isStatic() || delete_static)) {
			delete it->second;
			auto aux_it = it;
			aux_it++;
			sessions_set.erase(it++);
			it = aux_it;
		} else {
			it++;
		}
	}
}

void Set::removeExpiredSessions(void)
{
	std::lock_guard<std::recursive_mutex> locker(lock_mtx);
	auto it = sessions_set.cbegin();

	while (it != sessions_set.cend()) {
		if (it->second->hasExpired(sess_ttl)) {
			delete it->second;
			auto aux_it = it;
			aux_it++;
			sessions_set.erase(it);
			it = aux_it;
		} else {
			it++;
		}
	}
}

void Set::flushSessions(void)
{
	std::lock_guard<std::recursive_mutex> locker(lock_mtx);
	for (const auto &session : sessions_set)
		delete session.second;
	sessions_set.clear();
}


// Private methods

std::string Set::getQueryParameter(const std::string &url,
						  const std::string &sess_id)
{
	auto it_start = url.find(sess_id);
	if (it_start == std::string::npos)
		return std::string();
	it_start = url.find('=', it_start);
	auto it_end = url.find(';', it_start++);
	it_end = it_end != std::string::npos ? it_end : url.find('&', it_start);
	;
	it_end = it_end != std::string::npos ? it_end : url.size();
	std::string res(url.data() + it_start, it_end - it_start);
	return res;
}

std::string Set::getUrlParameter(const std::string &url)
{
	std::string expr_ = "[;][^?]*";
	std::smatch match;
	std::regex rgx(expr_);

	if (std::regex_search(url, match, rgx)) {
		std::string result = match[0];
		return result.substr(1);
	} else {
		return std::string();
	}
}

std::string Set::getSessionKey(const std::string &client_ip, HttpRequest &request)
{
	std::string session_key;

	switch (session_type) {
	case SESS_TYPE::SESS_NONE:
		break;
	case SESS_TYPE::SESS_IP: {
		session_key = client_ip;
		break;
	}
	case SESS_TYPE::SESS_BCK_COOKIE:
	case SESS_TYPE::SESS_COOKIE: {
		if (!request.getHeaderValue(http::HTTP_HEADER_NAME::COOKIE,
						session_key)) {
			session_key = "";
		} else {
			session_key = getCookieValue(session_key, sess_id);
		}
		break;
	}
	case SESS_TYPE::SESS_URL: {
		std::string url = request.getUrl();

		session_key = getQueryParameter(url, sess_id);
		break;
	}
	case SESS_TYPE::SESS_PARM: {
		std::string url = request.getUrl();

		session_key = getUrlParameter(url);
		break;
	}
	case SESS_TYPE::SESS_HEADER: {
		if (!request.getHeaderValue(sess_id, session_key))
			session_key = "";
		break;
	}
	case SESS_TYPE::SESS_BASIC: {
		if (!request.getHeaderValue(
				http::HTTP_HEADER_NAME::AUTHORIZATION,
				session_key)) {
			session_key = "";
		} else {
			std::stringstream string_to_iterate(session_key);
			std::istream_iterator<std::string> begin(
				string_to_iterate);
			std::istream_iterator<std::string> end;
			std::vector<std::string> header_value_parts(begin, end);
			if (header_value_parts[0] != "Basic") {
				session_key = "";
			} else {
				session_key = header_value_parts
					[1]; // Currently it stores username:password
			}
		}
		break;
	}
	default: {
		break;
	}
	}
	return session_key;
}

int Set::updateSession(const std::string &key,
		       struct zproxy_backend_cfg *new_backend,
		       time_t last_seen)
{
	if (!new_backend)
		return -2;

	std::lock_guard<std::recursive_mutex> locker(lock_mtx);
	auto session_it = sessions_set.find(key);
	if (session_it == sessions_set.end())
		return -1;

	session_it->second->bck_addr = new_backend->runtime.addr;
	session_it->second->last_seen = last_seen;

	return 1;
}

Info *Set::getSession(std::string &client_ip,
						HttpRequest &request,
						bool update_if_exist)
{
	std::string session_key = getSessionKey(client_ip, request);

	if (session_key.empty())
		return nullptr;

	Time::updateTime();

	std::lock_guard<std::recursive_mutex> locker(lock_mtx);
	auto session_it = sessions_set.find(session_key);
	if (session_it == sessions_set.end())
		return nullptr;
	if (session_it->second != nullptr) {
		// we have a stored session, check if it has not expired.
		if (!session_it->second->hasExpired(sess_ttl)) {
			if (update_if_exist)
				session_it->second->update();
			return session_it->second;
		}
		deleteSessionByKey(session_key);
	}
	return nullptr;
}

bool Set::deleteSessionByKey(const std::string &key)
{
	std::lock_guard<std::recursive_mutex> locker(lock_mtx);
	auto it = sessions_set.find(key);

	if (it == sessions_set.end())
		return false;
	delete it->second;
	it->second = nullptr;
	sessions_set.erase(it);

	return true;
}

json_t *Set::to_json(const struct zproxy_service_cfg *service) {
	json_t *sessions = json_array();
	json_t *session;
	const char *key;
	const struct zproxy_backend_cfg *backend_cfg;
	const Info *session_info;

	std::lock_guard<std::recursive_mutex> locker(lock_mtx);

	for (const auto &it : sessions_set) {
		session = json_object();
		key = it.first.c_str();
		session_info = it.second;
		backend_cfg = zproxy_backend_cfg_lookup(service,
							&session_info->bck_addr);

		json_object_set_new(session, "id", json_string(key));
		json_object_set_new(session, "backend-id",
				    json_string(backend_cfg->runtime.id));
		json_object_set_new(session, "last-seen",
				    json_integer((json_int_t)session_info->last_seen));
		json_array_append_new(sessions, session);
	}

	return sessions;
}
