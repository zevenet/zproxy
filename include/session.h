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

#ifndef _ZPROXY_SESSION_H_
#define _ZPROXY_SESSION_H_

#include <string>
#include <mutex>
#include <unordered_map>
#include <jansson.h>
#include "config.h"
#include "http_request.h"
#include "zcu_time.h"

namespace sessions
{
class Info {
public:
	// last_seen is used to calculate if the session has expired.
	// If it has the value 0 means that the session does not expired, it is permanent
	time_t last_seen;
	struct sockaddr_in bck_addr;

	Info(zproxy_backend_cfg *backend)
	{
		Time::updateTime();
		bck_addr = backend->runtime.addr;
		last_seen = Time::getTimeSec();
	}

	bool isStatic(void) const
	{
		return last_seen == 0 ? true : false;
	}
	inline time_t getTimeDiff(void) const
	{
		if (this->isStatic())
			return 0;
		return Time::getTimeSec() - last_seen;
	}
	bool hasExpired(unsigned int ttl)
	{
		// check if has not reached ttl
		if (this->isStatic())
			return false;
		return Time::getTimeSec() - last_seen > ttl;
	}
	void update(void)
	{
		if (!this->isStatic())
			last_seen = Time::getTimeSec();
	}
	long getTimeStamp(void)
	{
		return last_seen;
	}
	void setTimeStamp(long seconds_since_epoch_count)
	{
		std::chrono::seconds dur(seconds_since_epoch_count);
		std::chrono::time_point<std::chrono::system_clock> dt(dur);
		last_seen = dt.time_since_epoch().count();
	}
};

class Set {
	std::recursive_mutex lock_mtx;

public:
	std::unordered_map<std::string, Info *>
		sessions_set; // key can be anything, depending on the session type
	SESS_TYPE session_type;
	std::string sess_id; // id to construct the pattern
	unsigned int sess_ttl{};

	Set(SESS_TYPE type, std::string id, unsigned int ttl);
	~Set();

	// it adds a new item to the session map
	Info *addSession(std::string &client_addr, HttpRequest &request, zproxy_backend_cfg *backend_to_assign);
	Info *addSession(const std::string &key,
			 struct zproxy_backend_cfg *backend_to_assign);
	// it updates or create a sessions if it does not exist
	void update(std::string &client_addr, std::string key, zproxy_backend_cfg *backend_to_assign);
	// it deletes a map entry by session key
	bool deleteSessionByKey(const std::string &key);
	// it deletes a map entry looking for by bc
	void deleteSessionByBackend(std::string &client_addr, HttpRequest &request);
	// it returns the assigned session for a key or nullptr if session is not found or sesssion expired
	Info *getSession(std::string &client_addr, HttpRequest &request,
				bool update_if_exist = false);
	// it looks for the backend depending on the session key
	struct sockaddr_in *getBackend(std::string &client_addr,
				       HttpRequest &request,
				       const char *service_name,
				       bool update_if_exist = false);

	void deleteBackendSessions(zproxy_backend_cfg *backend,
				   bool delete_static = false);

	int updateSession(const std::string &key,
			  struct zproxy_backend_cfg *new_backend,
			  time_t last_seen);

	void removeExpiredSessions(void);

	// it cleans the session map
	void flushSessions(void);
	// it removes the expires sessions
	void doMaintenance(void);

	json_t *to_json(const struct zproxy_service_cfg *service);

private:
	static std::string getQueryParameter(const std::string &url,
					     const std::string &sess_id);
	static std::string getUrlParameter(const std::string &url);
	std::string getSessionKey(const std::string &client_ip, HttpRequest &request);
};

static std::string getCookieValue(std::string_view cookie_header_value,
					  std::string_view sess_id)
{
	auto it_start = cookie_header_value.find(sess_id);
	if (it_start == std::string::npos)
		return std::string();
	it_start = cookie_header_value.find('=', it_start);
	auto it_end = cookie_header_value.find(';', it_start++);
	it_end = it_end != std::string::npos ? it_end :
							 cookie_header_value.size();
	std::string res(cookie_header_value.data() + it_start,
			it_end - it_start);
	return res;
}

} // namespace sessions

#endif
