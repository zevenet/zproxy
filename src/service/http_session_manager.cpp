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
#include "http_session_manager.h"

using namespace sessions;

HttpSessionManager::HttpSessionManager():session_type(SESS_NONE)
{
}

HttpSessionManager::~HttpSessionManager()
{
      for (auto & session:sessions_set) {
		delete session.second;
	}
}

SessionInfo *
HttpSessionManager::addSession(Connection & source,
			       HttpRequest & request,
			       Backend & backend_to_assign)
{
	if (this->session_type == sessions::SESS_NONE)
		return nullptr;
	std::string key = getSessionKey(source, request);
	// check if we have a new key to insert,
	if (!key.empty()) {
		auto new_session = new SessionInfo();
		new_session->assigned_backend = &backend_to_assign;
		std::lock_guard < std::recursive_mutex > locker(lock_mtx);
		sessions_set.emplace(std::make_pair(key, new_session));
		return new_session;
	}
	return nullptr;
}

bool
sessions::HttpSessionManager::updateSession(Connection & source,
					    HttpRequest & request,
					    const std::
					    string & new_session_id,
					    Backend & backend_to_assign)
{
	std::string request_session_id = getSessionKey(source, request);
	std::string session_id = new_session_id;
	if (this->session_type == sessions::SESS_COOKIE) {
		session_id = getCookieValue(new_session_id, this->sess_id);
	}
	if (request_session_id == new_session_id)
		return true;
	if (!session_id.empty()) {
		std::lock_guard < std::recursive_mutex > locker(lock_mtx);
		SessionInfo *
			session_data
		{
		nullptr};
		if (!request_session_id.empty()) {
			auto
				it_old =
				sessions_set.find(request_session_id);
			if (it_old != sessions_set.end()) {
				session_data = it_old->second;
				sessions_set.erase(it_old);
			}
		}
		auto
			it_new = sessions_set.find(session_id);
		if (it_new != sessions_set.end()) {
			if (session_data == nullptr)
				session_data = it_new->second;
			else
				delete it_new->second;
			sessions_set.erase(it_new);
		}
		session_data =
			session_data ==
			nullptr ? new SessionInfo() : session_data;
		session_data->assigned_backend = &backend_to_assign;
		sessions_set.
			emplace(std::make_pair(session_id, session_data));
		return true;
	}
	return false;
}

void
HttpSessionManager::deleteSession(Connection & source, HttpRequest & request)
{
	std::lock_guard < std::recursive_mutex > locker(lock_mtx);
	auto session_key = getSessionKey(source, request);
	if (!session_key.empty()) {
		deleteSessionByKey(session_key);
	}
}

SessionInfo *
HttpSessionManager::getSession(Connection & source,
			       HttpRequest & request, bool update_if_exist)
{
	std::string session_key = getSessionKey(source, request);
	if (session_key.empty())
		return nullptr;
	std::lock_guard < std::recursive_mutex > locker(lock_mtx);
	auto session_it = sessions_set.find(session_key);
	if (session_it == sessions_set.end())
		return nullptr;
	if (session_it->second != nullptr) {
		// we have a stored session, check if it has not expired.
		if (!session_it->second->hasExpired(this->ttl)) {
			if (update_if_exist)
				session_it->second->update();
			return session_it->second;
		}
		else {
			deleteSessionByKey(session_key);
		}
	}
	return nullptr;
}

std::unique_ptr < json::JsonArray > HttpSessionManager::getSessionsJson()
{
	std::unique_ptr < json::JsonArray > data {
		new
	json::JsonArray()};
      for (auto & session:sessions_set) {
		std::unique_ptr < JsonObject > json_data {
			new
		json::JsonObject()};
		json_data->emplace(JSON_KEYS::ID,
				   std::make_unique < JsonDataValue >
				   (session.first));
		json_data->emplace(JSON_KEYS::BACKEND_ID,
				   std::make_unique < JsonDataValue >
				   (session.second->assigned_backend->
				    backend_id));

		json_data->emplace(JSON_KEYS::LAST_SEEN_TS,
				   std::make_unique < JsonDataValue >
				   (session.second->getTimeStamp()));
		data->emplace_back(std::move(json_data));
	}
	return data;
}

void
HttpSessionManager::deleteBackendSessions(int backend_id)
{
	std::lock_guard < std::recursive_mutex > locker(lock_mtx);
	for (auto it = sessions_set.cbegin(); it != sessions_set.cend();) {
		if (it->second != nullptr &&
		    it->second->assigned_backend->backend_id == backend_id) {
			sessions_set.erase(it++);
		}
		else
			it++;
	}
}

void
HttpSessionManager::doMaintenance()
{
	std::lock_guard < std::recursive_mutex > locker(lock_mtx);
	for (auto it = sessions_set.cbegin(); it != sessions_set.cend();) {
		if (it->second != nullptr && it->second->hasExpired(ttl)) {
			sessions_set.erase(it++);
		}
		else
			it++;
	}
}

bool
HttpSessionManager::addSession(JsonObject * json_object,
			       std::vector < Backend * >backend_set)
{
	if (json_object == nullptr)
		return false;
	std::unique_ptr < SessionInfo > new_session(new SessionInfo());
	if (json_object->at(JSON_KEYS::BACKEND_ID)->isValue() &&
	    json_object->at(JSON_KEYS::ID)->isValue()) {
		auto session_json_backend_id =
			dynamic_cast <
			JsonDataValue *
			>(json_object->at(JSON_KEYS::BACKEND_ID).get())
			->number_value;
	      for (auto backend:backend_set) {
			if (backend->backend_id != session_json_backend_id)
				continue;
			new_session->assigned_backend = backend;
		}
		if (new_session->assigned_backend == nullptr)
			return false;
		std::lock_guard < std::recursive_mutex > locker(lock_mtx);
		std::string key =
			dynamic_cast <
			JsonDataValue *
			>(json_object->at(JSON_KEYS::ID).get())
			->string_value;
		if (json_object->count(JSON_KEYS::LAST_SEEN_TS) > 0 &&
		    json_object->at(JSON_KEYS::LAST_SEEN_TS)->isValue())
			new_session->setTimeStamp(dynamic_cast <
						  JsonDataValue *
						  >(json_object->
						    at(JSON_KEYS::
						       LAST_SEEN_TS).get())
						  ->number_value);
		sessions_set.
			emplace(std::make_pair(key, new_session.release()));
		return true;
	}
	else {
		return false;
	}
}

bool
HttpSessionManager::deleteSession(const JsonObject & json_object)
{
	std::lock_guard < std::recursive_mutex > locker(lock_mtx);
	if (json_object.count(JSON_KEYS::BACKEND_ID) > 0 &&
	    json_object.at(JSON_KEYS::BACKEND_ID)->isValue()) {
		auto session_json_backend_id =
			dynamic_cast <
			JsonDataValue *
			>(json_object.at(JSON_KEYS::BACKEND_ID).get())
			->number_value;
		auto itr = sessions_set.begin();
		while (itr != sessions_set.end()) {
			if (itr->second->assigned_backend->backend_id ==
			    session_json_backend_id) {
				sessions_set.erase(itr++);
			}
			else {
				++itr;
			}
		}
		return true;
	}
	else {
		auto it = json_object.find(JSON_KEYS::ID);
		if (it != json_object.end() &&
		    json_object.at(JSON_KEYS::ID)->isValue()) {
			std::string key =
				dynamic_cast <
				JsonDataValue * >(it->second.get())
				->string_value;
			return deleteSessionByKey(key);
		}
		return false;
	}
}

std::string HttpSessionManager::getQueryParameter(const std::string & url,
						  const std::string & sess_id)
{
	auto
		it_start = url.find(sess_id);
	if (it_start == std::string::npos)
		return std::string();
	it_start = url.find('=', it_start);
	auto
		it_end = url.find(';', it_start++);
	it_end = it_end != std::string::npos ? it_end : url.find('&',
								 it_start);;
	it_end = it_end != std::string::npos ? it_end : url.size();
	std::string res(url.data() + it_start, it_end - it_start);
	return res;
}

std::string HttpSessionManager::getCookieValue(std::
					       string_view
					       cookie_header_value,
					       std::string_view sess_id)
{
	auto
		it_start = cookie_header_value.find(sess_id);
	if (it_start == std::string::npos)
		return std::string();
	it_start = cookie_header_value.find('=', it_start);
	auto
		it_end = cookie_header_value.find(';', it_start++);
	it_end = it_end !=
		std::string::npos ? it_end : cookie_header_value.size();
	std::string res(cookie_header_value.data() + it_start,
			it_end - it_start);
	return res;
}

std::string HttpSessionManager::getUrlParameter(const std::string & url)
{
	std::string expr_ = "[;][^?]*";
	std::smatch match;
	std::regex rgx(expr_);
	if (std::regex_search(url, match, rgx)) {
		std::string result = match[0];
		return result.substr(1);
	}
	else {
		return std::string();
	}
}

bool
HttpSessionManager::deleteSessionByKey(const std::string & key)
{
	std::lock_guard < std::recursive_mutex > locker(lock_mtx);
	auto it = sessions_set.find(key);
	if (it == sessions_set.end())
		return false;
	delete it->second;
	it->second = nullptr;
	sessions_set.erase(it);
	return true;
}

std::string HttpSessionManager::getSessionKey(Connection & source,
					      HttpRequest & request)
{
	std::string session_key;
	switch (session_type) {
	case sessions::SESS_NONE:
		break;
	case sessions::SESS_IP:{
			session_key = source.getPeerAddress();
			break;
		}
	case sessions::SESS_COOKIE:{
			if (!request.
			    getHeaderValue(http::HTTP_HEADER_NAME::COOKIE,
					   session_key)) {
				session_key = "";
			}
			else {
				session_key =
					getCookieValue(session_key, sess_id);
			}
			break;
		}
	case sessions::SESS_URL:{
			std::string url = request.getUrl();
			session_key = getQueryParameter(url, sess_id);
			break;
		}
	case sessions::SESS_PARM:{
			std::string url = request.getUrl();
			session_key = getUrlParameter(url);
			break;
		}
	case sessions::SESS_HEADER:{
			if (!request.getHeaderValue(sess_id, session_key)) {
				session_key = "";
			}
			break;
		}
	case sessions::SESS_BASIC:{
			if (!request.
			    getHeaderValue(http::HTTP_HEADER_NAME::
					   AUTHORIZATION, session_key)) {
				session_key = "";
			}
			else {
				std::stringstream
					string_to_iterate(session_key);
				std::istream_iterator < std::string >
					begin(string_to_iterate);
				std::istream_iterator < std::string > end;
				std::vector < std::string >
					header_value_parts(begin, end);
				if (header_value_parts[0] != "Basic") {
					session_key = "";
				}
				else {
					session_key = header_value_parts[1];	// Currently it stores username:password
				}
			}
			break;
		}
	default:{
			break;
		}
	}
	return session_key;
}

void
HttpSessionManager::flushSessions()
{
	std::lock_guard < std::recursive_mutex > locker(lock_mtx);
      for (const auto & session:sessions_set)
		delete session.second;
	sessions_set.clear();
}
