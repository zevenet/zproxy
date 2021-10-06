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
#include "http_cache.h"
#include "../handlers/cache_manager.h"
#include "../../zcutils/zcutils.h"
// Returns the cache content with all the information stored
cache_commons::CacheObject *HttpCache::getCacheObject(HttpRequest request)
{
	return getCacheObject(std::hash<std::string>()(request.getUrl()));
}

cache_commons::CacheObject *HttpCache::getCacheObject(size_t hashed_url)
{
	cache_commons::CacheObject *c_object = nullptr;
	auto iter = cache.find(hashed_url);
	if (iter != cache.end()) {
		c_object = iter->second;
	}
	return c_object;
}

// Store in cache the response checking CacheObject parameters
void HttpCache::handleResponse(HttpResponse &response, HttpRequest request)
{
	auto c_opt = getCacheObject(request);
	if (c_opt != nullptr && c_opt->dirty == true) {
		this->stats.cache_not_stored++;
		return;
	}

	if (c_opt != nullptr && c_opt->isFresh(this->t_stamp)) {
		this->stats.cache_not_stored++;
		// If the stored response is fresh, we must not to store this response
		response.c_opt.cacheable = false;
	}
	// If the response/request is set as not cacheable, we can't cache it
	if (!response.c_opt.cacheable) {
		this->stats.cache_not_stored++;
		return;
	} else if (response.cache_control == false && response.pragma == true) {
		// Check the pragma only if no cache-control header in request nor in
		// response, if the pragma was present, disable cache
		this->stats.cache_not_stored++;
		return;
	}
	//  Check status code
	if (response.http_status_code != 200 &&
	    response.http_status_code != 301 &&
	    response.http_status_code != 308) {
		this->stats.cache_not_stored++;
		return;
	}
	if (((response.content_length + response.headers_length) >=
	     cache_max_size) &&
	    cache_max_size != 0) {
		//    cache_stats::cache_RAM_inserted_entries++;
		DEBUG_COUNTER_HIT(cache_stats__::cache_not_stored);
		this->stats.cache_not_stored++;
		zcu_log_print(
			LOG_ERR, "Not caching response with %d bytes size",
			response.content_length + response.headers_length);
		return;
	}

	// Check HTTP verb
	switch (http::http_info::http_verbs.at(
		std::string(request.method, request.method_len))) {
	case http::REQUEST_METHOD::GET:
		addResponse(response, request);
		break;
	case http::REQUEST_METHOD::HEAD:
		if (getCacheObject(request) != nullptr)
			updateResponse(response, request);
		break;
	default:
		return;
	}
	return;
}

// On Head request
void HttpCache::updateResponse(HttpResponse response, HttpRequest request)
{
	auto c_object = getCacheObject(request);
	if (response.content_length == 0) {
		zcu_log_print(LOG_ERR,
			      "Content-Length header with 0 value when trying "
			      "to update content in the cache");
	}
	if (response.content_length != c_object->content_length) {
		zcu_log_print(
			LOG_ERR,
			"Content-Length in response and Content-Length cached missmatch for %s",
			request.getUrl().data());
		return;
	}
	if (response.etag.compare(c_object->etag) != 0) {
		zcu_log_print(
			LOG_ERR,
			"ETag in response and ETag cached missmatch for %s",
			request.getUrl().data());
		return;
	}
	c_object->staled = false;
	c_object->date = this->t_stamp;

	return;
}

// Decide on which RAM storage to use
st::STORAGE_TYPE HttpCache::getStorageType()
{
#ifdef CACHE_STORAGE_STDMAP
	return st::STORAGE_TYPE::STDMAP;
#elif MEMCACHED_ENABLED
	return st::STORAGE_TYPE::MEMCACHED;
#else
	return st::STORAGE_TYPE::RAMFS;
#endif
}

// Decide if should be used Disk or RAM
st::STORAGE_TYPE HttpCache::getStorageType(HttpResponse response)
{
	size_t ram_size_left =
		ram_storage->max_size - ram_storage->current_size;

	size_t response_size =
		response.http_message_length + response.content_length;
	// If chunked -> store in disk
	if ((response.chunked_status !=
		     http::CHUNKED_STATUS::CHUNKED_DISABLED &&
	     response.transfer_encoding_type ==
		     http::TRANSFER_ENCODING_TYPE::CHUNKED) ||
	    response_size > ram_storage->max_size * ram_storage->cache_thr ||
	    response_size >= ram_size_left) {
		return st::STORAGE_TYPE::DISK;
	} else {
		return getStorageType();
	}
}

// Destructor free pattern and stop storage
HttpCache::~HttpCache()
{
	// Free cache pattern
	if (cache_pattern != nullptr) {
		regfree(cache_pattern);
		cache_pattern = nullptr;
		ram_storage->stopCacheStorage();
		disk_storage->stopCacheStorage();
		cache.clear();
	}
}

// Init cache storage and set needed parameters
void HttpCache::cacheInit(regex_t *pattern, const int timeout,
			  const std::string &svc, long storage_size,
			  int storage_threshold, const std::string &f_name,
			  const std::string &cache_ram_mpoint,
			  const std::string &cache_disk_mpoint)
{
	if (pattern != nullptr) {
		if (pattern->re_pcre != nullptr) {
			this->cache_pattern = pattern;
			this->cache_timeout = timeout;
			this->service_name = svc;
		} else {
			return;
		}
		if (cache_ram_mpoint.size() > 0) {
			ramfs_mount_point = cache_ram_mpoint;
			if (ramfs_mount_point.back() == '/') {
				ramfs_mount_point.erase(
					ramfs_mount_point.size() - 1);
			}
		}
		if (cache_disk_mpoint.size() > 0) {
			disk_mount_point = cache_disk_mpoint;
			if (disk_mount_point.back() == '/') {
				disk_mount_point.erase(disk_mount_point.size() -
						       1);
			}
		}
		// Create directory, if fails, and it's not because the folder is already
		// created, just return an error
		if (mkdir(ramfs_mount_point.data(), 0777) == -1) {
			if (errno != EEXIST) {
				zcu_log_print(LOG_ERR,
					      "Error creating the directory %s",
					      ramfs_mount_point.data());
				exit(1);
			}
		}
		if (mkdir(disk_mount_point.data(), 0777) == -1) {
			if (errno != EEXIST) {
				zcu_log_print(LOG_ERR,
					      "Error creating the directory %s",
					      disk_mount_point.data());
				exit(1);
			}
		}

		// Set mount point farm name dependant
		ramfs_mount_point.append("/");
		ramfs_mount_point.append(f_name);
		disk_mount_point.append("/");
		disk_mount_point.append(f_name);

		st::STORAGE_STATUS svc_status;
		// RAM
		switch (getStorageType()) {
		case st::STORAGE_TYPE::RAMFS:
			ram_storage = RamfsCacheStorage::getInstance();
			ram_storage->initCacheStorage(
				static_cast<unsigned long>(storage_size),
				static_cast<double>(storage_threshold) / 100,
				svc, ramfs_mount_point);
			svc_status = ram_storage->initServiceStorage(svc);
			// recover cache status
			if (svc_status ==
			    st::STORAGE_STATUS::MPOINT_ALREADY_EXISTS) {
				recoverCache(svc, st::STORAGE_TYPE::RAMFS);
			}
			break;
		case st::STORAGE_TYPE::STDMAP:
			ram_storage = StdmapCacheStorage::getInstance();
			ram_storage->initCacheStorage(
				static_cast<unsigned long>(storage_size),
				static_cast<double>(storage_threshold) / 100,
				svc, ramfs_mount_point);
			svc_status = ram_storage->initServiceStorage(svc);
			// recover cache status
			if (svc_status ==
			    st::STORAGE_STATUS::MPOINT_ALREADY_EXISTS) {
				recoverCache(svc, st::STORAGE_TYPE::STDMAP);
			}
			break;
#if MEMCACHED_ENABLED == 1
		case st::STORAGE_TYPE::MEMCACHED:
			ram_storage = MemcachedStorage::getInstance();
			ram_storage->initCacheStorage(
				static_cast<unsigned long>(storage_size),
				static_cast<double>(storage_threshold) / 100,
				svc, cache_ram_mpoint);
			svc_status = ram_storage->initServiceStorage(svc);
			// recover cache status
			break;
#endif
		default:
			zcu_log_print(
				LOG_ERR,
				"ERROR Fatal, not able to determine the storage");
		}

		// DISK
		disk_storage = DiskCacheStorage::getInstance();
		disk_storage->initCacheStorage(0, 0, svc, disk_mount_point);
		svc_status = disk_storage->initServiceStorage(svc);
		// recover cache status
		if (svc_status == st::STORAGE_STATUS::MPOINT_ALREADY_EXISTS) {
			recoverCache(svc, st::STORAGE_TYPE::DISK);
		}

		this->stats.cache_RAM_mountpoint = ramfs_mount_point;
		this->stats.cache_DISK_mountpoint = disk_mount_point;
	}
}

// Add response to CacheObject representation and to storage
void HttpCache::addResponse(HttpResponse &response, HttpRequest request)
{
	auto cache_entry = new cache_commons::CacheObject();
	std::unique_ptr<cache_commons::CacheObject> c_object(cache_entry);
	auto hashed_url = hash<std::string>()(request.getUrl());
	cache[hashed_url] = c_object.get();

	createResponseEntry(response, c_object.get());
	// FIXME: Review if to set the URI here is the best option
	c_object.get()->uri = request.getUrl();
	// link response with c_object
	response.c_object = c_object.get();

	// Check what storage to use
	st::STORAGE_STATUS err;

	// Create the path string
	std::string rel_path = service_name;
	rel_path.append("/");
	rel_path.append(to_string(hashed_url));

	switch (c_object->storage) {
	case st::STORAGE_TYPE::STDMAP:
	case st::STORAGE_TYPE::MEMCACHED:
	case st::STORAGE_TYPE::RAMFS:
		err = ram_storage->putInStorage(
			rel_path,
			std::string(response.buffer, response.buffer_size),
			(response.content_length + response.headers_length));
		if (err == st::STORAGE_STATUS::SUCCESS) {
			DEBUG_COUNTER_HIT(cache_stats__::cache_RAM_entries);
			this->stats.cache_RAM_inserted_entries++;
			this->stats.cache_RAM_used =
				static_cast<long>(ram_storage->current_size);
		}
		break;
	case st::STORAGE_TYPE::DISK:
		err = disk_storage->putInStorage(
			rel_path,
			std::string(response.buffer, response.buffer_size),
			(response.content_length + response.headers_length));
		if (err == st::STORAGE_STATUS::SUCCESS) {
			DEBUG_COUNTER_HIT(cache_stats__::cache_DISK_entries);
			this->stats.cache_DISK_inserted_entries++;
			this->stats.cache_DISK_used =
				static_cast<long>(disk_storage->current_size);
		}
		break;
	default:
		return;
	}
	// If success, store in the unordered map
	if (err != st::STORAGE_STATUS::SUCCESS) {
		zcu_log_print(LOG_ERR,
			      "Error trying to store the response in storage");
		deleteEntry(request);
		return;
	}
	c_object->headers_size = response.headers_length;
	if (response.chunked_status == http::CHUNKED_STATUS::CHUNKED_DISABLED) {
		if (response.content_length == response.message_length) {
			c_object->dirty = false;
		}
	}
	// TRY
	if (response.chunked_status ==
	    http::CHUNKED_STATUS::CHUNKED_LAST_CHUNK) {
		c_object->dirty = false;
		c_object->content_length = response.content_length;
	}

	c_object.release();
	return;
}

// Create the CacheObject with important information about the req/resp cached
void HttpCache::createResponseEntry(HttpResponse response,
				    cache_commons::CacheObject *c_object)
{
	if (c_object == nullptr) {
		c_object = new cache_commons::CacheObject();
	}
	// Store the response date in the cache
	if (response.date <= 0) {
		response.date = this->t_stamp;
	}
	if (response.last_mod <= 0) {
		response.last_mod = this->t_stamp;
	}

	c_object->date = response.date;

	// If the max_age is not set nor the timeout exist, we have to calculate
	// heuristically
	if (response.c_opt.max_age >= 0 && this->cache_timeout != 0) {
		// Set the most restrictive value
		response.c_opt.max_age > this->cache_timeout ?
			      c_object->max_age = this->cache_timeout :
			      c_object->max_age = response.c_opt.max_age;
	} else if (this->cache_timeout >= 0) {
		// Store the config file timeout
		c_object->max_age = this->cache_timeout;
	} else if (response.c_opt.max_age >= 0) {
		// Store the response cache max-age
		c_object->max_age = response.c_opt.max_age;
	} else if (response.last_mod >= 0) {
		// heuristic algorithm -> 10% of last-modified
		time_t now = this->t_stamp;
		c_object->max_age =
			static_cast<long>((now - response.last_mod) * 0.1);
	} else {
		// If not available value, use the defined default timeout
		c_object->max_age = DEFAULT_TIMEOUT
	}
	/*
	 *must-revalidate, proxy-revalidate
	 */
	if (response.expires >= 0) {
		c_object->expires = response.expires;
	}
	// If there is etag, then store it
	if (!response.etag.empty()) {
		c_object->etag = response.etag;
	}

	c_object->revalidate = response.c_opt.revalidate;
	// Reset the stale flag, the cache has been created or updated
	c_object->staled = false;
	c_object->content_length = response.content_length;
	c_object->no_cache_response = response.c_opt.no_cache;

	c_object->encoding = response.transfer_encoding_type;

	switch (getStorageType(response)) {
	case st::STORAGE_TYPE::RAMFS:
		c_object->storage = st::STORAGE_TYPE::RAMFS;
		break;
	case st::STORAGE_TYPE::DISK:
		c_object->storage = st::STORAGE_TYPE::DISK;
		break;
	case st::STORAGE_TYPE::STDMAP:
		c_object->storage = st::STORAGE_TYPE::STDMAP;
		break;
	case st::STORAGE_TYPE::MEMCACHED:
		c_object->storage = st::STORAGE_TYPE::MEMCACHED;
		break;
	default:
		zcu_log_print(LOG_ERR, "Not able to decide storage, exiting");
		exit(-1);
	}

	// TODO: Add information (backend ID and URI) to the cache object

	return;
}

// Append pending data to its cached content
void HttpCache::addData(HttpResponse &response, std::string_view data,
			const std::string &url)
{
	auto c_object = getCacheObject(std::hash<std::string>()(url));
	if (c_object == nullptr) {
		zcu_log_print(LOG_ERR,
			      "Incoming data for a cache entry not stored yet");
		return;
	}
	if (response.c_object == nullptr)
		return;

	// create the path string
	size_t hashed_url = std::hash<std::string>()(url);
	std::string rel_path = service_name;
	rel_path.append("/");
	rel_path.append(to_string(hashed_url));

	storage_commons::STORAGE_STATUS err;
	// Check what storage to use
	switch (c_object->storage) {
	case st::STORAGE_TYPE::STDMAP:
	case st::STORAGE_TYPE::MEMCACHED:
	case st::STORAGE_TYPE::RAMFS:
		err = ram_storage->appendData(rel_path, data);
		this->stats.cache_RAM_used =
			static_cast<long>(ram_storage->current_size);
		break;
	case st::STORAGE_TYPE::DISK:
		err = disk_storage->appendData(rel_path, data);
		this->stats.cache_DISK_used =
			static_cast<long>(disk_storage->current_size);
		break;
	default:
		return;
	}
	if (err != storage_commons::STORAGE_STATUS::SUCCESS) {
		zcu_log_print(
			LOG_ERR,
			"There was an unexpected error result while appending data "
			"to the cache content %s",
			url.data());
	}
	// disable flag
	if (response.chunked_status == http::CHUNKED_STATUS::CHUNKED_DISABLED &&
	    response.message_bytes_left == data.size()) {
		response.c_object->dirty = false;
	} else if (response.chunked_status ==
		   http::CHUNKED_STATUS::CHUNKED_LAST_CHUNK) {
		response.c_object->dirty = false;
		c_object->content_length = response.content_length;
	}
	return;
}

// Check if the request can be satisfied with the stored content.
cache_commons::CacheObject *
HttpCache::canBeServedFromCache(HttpRequest &request)
{
	cache_commons::CacheObject *c_object = getCacheObject(request);

	if (c_object == nullptr) {
		return nullptr;
	}
	if (c_object->dirty) {
		return nullptr;
	}
	if (request.c_opt.no_cache ||
	    (!request.cache_control && request.pragma)) {
		return nullptr;
	}
	if (request.c_opt.only_if_cached) {
		return c_object;
	}
	if (!validateResponseEncoding(request, c_object)) {
		return nullptr;
	}
	bool serveable = true;
	bool prev_staled = c_object->staled;
	if (!c_object->isFresh(this->t_stamp)) {
		if (!prev_staled) {
			this->stats.cache_staled_entries++;
		}
		serveable = false;
	}

	std::time_t now = this->t_stamp;

	// if staled and must revalidate is included, we MUST revalidate the
	// response
	if (!serveable && c_object->revalidate) {
		return nullptr;
	}
	// If max-age request directive is set, we must check if the response
	// complies
	if (request.c_opt.max_age >= 0) {
		if (!c_object->staled) {
			if ((now - c_object->date) > request.c_opt.max_age) {
				serveable = false;
			}
		}
	}
	// Check if complies with the request directive min-fresh
	if (request.c_opt.min_fresh >= 0) {
		if (!c_object->staled) {
			if ((now - c_object->date) > request.c_opt.min_fresh) {
				return nullptr;
			}
		}
	}
	// Check if complies with the request directive max-stale
	if (request.c_opt.max_stale >= 0) {
		if (c_object->staled && !c_object->revalidate) {
			if ((now - c_object->date - c_object->max_age) <
			    request.c_opt.max_stale) {
				serveable = true;
			}
		}
	}

	return serveable ? c_object : nullptr;
}

int HttpCache::getResponseFromCache(HttpRequest request,
				    HttpResponse &cached_response,
				    std::string &buffer)
{
	auto c_object = getCacheObject(request);
	c_object->updateFreshness(this->t_stamp);

	size_t parsed = 0;
	std::string rel_path = service_name;
	rel_path.append("/");
	rel_path.append(to_string(std::hash<std::string>()(request.getUrl())));

	buffer = "";
	// Get the response from the right storage
	switch (c_object->storage) {
	case st::STORAGE_TYPE::STDMAP:
	case st::STORAGE_TYPE::MEMCACHED:
	case st::STORAGE_TYPE::RAMFS:
		ram_storage->getFromStorage(rel_path, buffer);
		break;
	case st::STORAGE_TYPE::DISK:
		disk_storage->getFromStorage(rel_path, buffer);
		break;
	default:
		return -1;
	}

	auto ret = cached_response.parseResponse(buffer, &parsed);
	cached_response.cached = true;

	for (size_t j = 0; j < cached_response.num_headers; j++) {
		if (std::string(cached_response.headers[j].name)
			    .compare("date") == 0) {
			cached_response.headers[j].header_off = true;
			cached_response.addHeader(
				http::HTTP_HEADER_NAME::DATE,
				time_helper::strTime(c_object->date));
		}
		cached_response.headers[j].header_off = false;
	}

	if (ret == http_parser::PARSE_RESULT::FAILED) {
		zcu_log_print(LOG_ERR,
			      "The cached response failed to be parsed");
		return -1;
	} else if (ret == http_parser::PARSE_RESULT::SUCCESS) {
		// Add warning header
		std::vector<std::string> w_codes;
		std::vector<std::string> w_text;
		// Take the date for the warning
		auto w_date = this->t_stamp;
		// Create warnings if needed
		if (c_object->staled) {
			w_codes.push_back(std::to_string(
				http::WARNING_CODE::RESPONSE_STALE));
			w_text.push_back(
				http::http_info::warning_code_values_strings.at(
					http::WARNING_CODE::RESPONSE_STALE));
		}
		// Defined by RFC7234
		if (c_object->heuristic && c_object->max_age >= 86400 &&
		    c_object->staled) {
			w_codes.push_back(std::to_string(
				http::WARNING_CODE::HEURISTIC_EXPIRATION));
			w_text.push_back(
				http::http_info::warning_code_values_strings.at(
					http::WARNING_CODE::
						HEURISTIC_EXPIRATION));
		}
		// Add warning headers if needed
		std::string warn;
		for (unsigned long i = 0;
		     i < w_codes.size() && i < w_text.size(); i++) {
			warn = w_codes.at(i);
			warn.append(" - ");
			warn.append("\"");
			warn.append(w_text.at(i));
			warn.append("\" \"");
			warn.append(time_helper::strTime(w_date));
			warn.append("\"");
			cached_response.addHeader(
				http::HTTP_HEADER_NAME::WARNING, warn);
		}
		// Add Age header
		time_t now = this->t_stamp - c_object->date;
		cached_response.addHeader(
			http::HTTP_HEADER_NAME::AGE,
			std::to_string(
				now >= 0 ?
					      now :
					      0)); // ensure that it is greater or equal than 0
	}
	this->stats.cache_match++;
	return 0;
}

// Handle API commands
std::string HttpCache::handleCacheTask(ctl::CtlTask &task)
{
	int err = 0;
	if (task.subject != ctl::CTL_SUBJECT::CACHE)
		return JSON_OP_RESULT::ERROR;
	switch (task.command) {
	case ctl::CTL_COMMAND::GET: {
		JsonObject response;
		json::JsonArray *data{ new json::JsonArray() };
		JsonObject *json_data{ new json::JsonObject() };
		json_data->emplace(JSON_KEYS::CACHE_HIT,
				   std::make_unique<JsonDataValue>(
					   this->stats.cache_match));
		json_data->emplace(JSON_KEYS::CACHE_MISS,
				   std::make_unique<JsonDataValue>(
					   this->stats.cache_miss));
		json_data->emplace(JSON_KEYS::CACHE_STALE,
				   std::make_unique<JsonDataValue>(
					   this->stats.cache_staled_entries));
		json_data->emplace(JSON_KEYS::CACHE_AVOIDED,
				   std::make_unique<JsonDataValue>(
					   this->stats.cache_not_stored));
		json_data->emplace(
			JSON_KEYS::CACHE_RAM,
			std::make_unique<JsonDataValue>(
				this->stats.cache_RAM_inserted_entries));
		json_data->emplace(JSON_KEYS::CACHE_RAM_USAGE,
				   std::make_unique<JsonDataValue>(
					   this->stats.cache_RAM_used));
		json_data->emplace(JSON_KEYS::CACHE_RAM_PATH,
				   std::make_unique<JsonDataValue>(
					   this->stats.cache_RAM_mountpoint));
		json_data->emplace(
			JSON_KEYS::CACHE_DISK,
			std::make_unique<JsonDataValue>(
				this->stats.cache_DISK_inserted_entries));
		json_data->emplace(JSON_KEYS::CACHE_DISK_USAGE,
				   std::make_unique<JsonDataValue>(
					   this->stats.cache_DISK_used));
		json_data->emplace(JSON_KEYS::CACHE_DISK_PATH,
				   std::make_unique<JsonDataValue>(
					   this->stats.cache_DISK_mountpoint));
		data->emplace_back(json_data);
		response.emplace(JSON_KEYS::CACHE.data(), data);
		return response.stringify();
	}
	case ctl::CTL_COMMAND::DELETE: {
		auto json_data = JsonParser::parse(task.data);
		if (json_data != nullptr) {
			// Error handling when trying to use the key
			try {
				json_data->at(JSON_KEYS::CACHE_CONTENT);
			} catch (const std::out_of_range &oor) {
				std::cerr << "Wrong key found, must be \""
					  << JSON_KEYS::CACHE_CONTENT
					  << "\", caused by " << oor.what()
					  << '\n';
				return JSON_OP_RESULT::ERROR;
			}
			auto url =
				dynamic_cast<JsonDataValue *>(
					json_data->at(JSON_KEYS::CACHE_CONTENT)
						.get())
					->string_value;
			err = deleteEntry(std::hash<std::string>()(url));
		} else {
			flushCache();
		}
		break;
	}
	default:
		zcu_log_print(LOG_ERR, "Not a valid cache command");
		return JSON_OP_RESULT::ERROR;
	}
	if (err != 0) {
		return JSON_OP_RESULT::ERROR;
	}
	return JSON_OP_RESULT::OK;
}

void HttpCache::recoverCache(const string &svc, st::STORAGE_TYPE st_type)
{
	// We have to read all headers and load it in memory
	std::string path;
	switch (st_type) {
	case st::STORAGE_TYPE::RAMFS:
		path = ram_storage->mount_path;
		path.append("/");
		path.append(svc);
		break;
	case st::STORAGE_TYPE::DISK:
		path = disk_storage->mount_path;
		path.append("/");
		path.append(svc);
		break;
	default:
		return;
	}
	std::ifstream in_file;
	std::string in_line, file_name;
	std::string buffer;
	std::unique_ptr<cache_commons::CacheObject> c_object(
		new cache_commons::CacheObject);
	for (const auto &entry : std::filesystem::directory_iterator(path)) {
		HttpResponse stored_response;
		// Iterate through all the files
		in_file.open(entry.path());
		file_name = std::filesystem::path(entry.path()).filename();
		while (std::getline(in_file, in_line)) {
			buffer.append(in_line + "\n");
			// The \r line alone separate the HTTP header from body
			if (in_line.compare("\r") == 0) {
				// finished reading, need to store the response obtained
				size_t bytes = 0;

				stored_response.parseResponse(buffer, &bytes);
				CacheManager::validateCacheResponse(
					stored_response);
				if (c_object.get() == nullptr) {
					c_object = make_unique<
						cache_commons::CacheObject>();
				}
				createResponseEntry(stored_response,
						    c_object.get());
				c_object->dirty = false;
				c_object->storage = st_type;
				// Increment the current size of the storage
				switch (st_type) {
				case st::STORAGE_TYPE::RAMFS:
					ram_storage->current_size +=
						c_object->content_length +
						stored_response.headers_length;
					break;
				case st::STORAGE_TYPE::DISK:
					disk_storage->current_size +=
						c_object->content_length +
						stored_response.headers_length;
					break;
				default:
					zcu_log_print(LOG_ERR,
						      "Wrong storage type");
					break;
				}
				break;
			}
		}
		if (c_object != nullptr) {
			c_object->dirty = false;
			if (c_object->content_length == 0) {
				c_object->encoding =
					http::TRANSFER_ENCODING_TYPE::CHUNKED;
			}
			cache[strtoul(file_name.data(), nullptr, 0)] =
				c_object.release();
		}
		in_file.close();
	}
}

int HttpCache::deleteEntry(HttpRequest request)
{
	return deleteEntry(std::hash<std::string>()(request.getUrl()));
}

int HttpCache::deleteEntry(size_t hashed_url)
{
	std::string path(service_name);
	path.append("/");
	path.append(to_string(hashed_url));
	auto c_object = getCacheObject(hashed_url);
	if (c_object == nullptr) {
		zcu_log_print(
			LOG_ERR,
			"Trying to discard a non existing entry from the cache");
		return -1;
	}
	// Create the key and the file path

	storage_commons::STORAGE_STATUS err;

	switch (c_object->storage) {
	case storage_commons::STORAGE_TYPE::MEMCACHED:
	case storage_commons::STORAGE_TYPE::STDMAP:
	case storage_commons::STORAGE_TYPE::RAMFS:
		err = ram_storage->deleteInStorage(path);
		this->stats.cache_RAM_used =
			static_cast<long>(ram_storage->current_size);
		break;
	case storage_commons::STORAGE_TYPE::DISK:
		err = disk_storage->deleteInStorage(path);
		this->stats.cache_DISK_used =
			static_cast<long>(disk_storage->current_size);
		break;
	default:
		return -1;
	}
	if (err != storage_commons::STORAGE_STATUS::SUCCESS &&
	    err != storage_commons::STORAGE_STATUS::NOT_FOUND) {
		zcu_log_print(
			LOG_ERR,
			"Error trying to delete cache content from the storage");
		return -1;
	}
	free(c_object);
	if (cache.erase(hashed_url) != 1) {
		zcu_log_print(LOG_ERR, "Error deleting cache entry");
		return -1;
	}
	return 0;
}

void HttpCache::doCacheMaintenance()
{
	// Iterate over all the content, check staled, check how long, discard if
	// entry old enough
	auto current_time = time_helper::gmtTimeNow();
	for (auto iter = cache.begin(); iter != cache.end();) {
		bool prev_staled = iter->second->staled;
		iter->second->updateFreshness(current_time);
		//        If not staled continue with the loop
		if (!iter->second->staled) {
			iter++;
			continue;
		} else {
			if (!prev_staled) {
				this->stats.cache_staled_entries++;
			}
			int expiration_to = CACHE_EXPIRATION auto entry_age =
				current_time - iter->second->date;
			//            Greater than 10 times the max age
			if (entry_age > iter->second->max_age * expiration_to) {
				zcu_log_print(
					LOG_DEBUG,
					"%s():%d: removing old cache entry: %zu",
					__FUNCTION__, __LINE__, iter->first);
				deleteEntry((iter++)->first);
				break;
			}
		}
		iter++;
	}
}

bool HttpCache::validateResponseEncoding(HttpRequest request,
					 cache_commons::CacheObject *c_object)
{
	if (c_object == nullptr) {
		return false;
	}
	std::string compression_value;
	request.getHeaderValue(http::HTTP_HEADER_NAME::ACCEPT_ENCODING,
			       compression_value);
	if (compression_value.size() == 0) {
		return true;
	}
	// we have all the accepted compressions in compression_value string
	size_t found;
	switch (c_object->encoding) {
	case http::TRANSFER_ENCODING_TYPE::BR:
		found = compression_value.find("br");
		break;
	case http::TRANSFER_ENCODING_TYPE::NONE:
		return true;
	case http::TRANSFER_ENCODING_TYPE::DEFLATE:
		found = compression_value.find("deflate");
		break;
	case http::TRANSFER_ENCODING_TYPE::GZIP:
		found = compression_value.find("gzip");
		break;
	case http::TRANSFER_ENCODING_TYPE::CHUNKED:
		found = compression_value.find("chunked");
		break;
	case http::TRANSFER_ENCODING_TYPE::COMPRESS:
		found = compression_value.find("compress");
		break;
	case http::TRANSFER_ENCODING_TYPE::IDENTITY:
		found = compression_value.find("identity");
		break;
	}

	return found != std::string::npos;
}

// Flush the full cache
void HttpCache::flushCache()
{
	for (auto iter = cache.begin(); iter != cache.end();) {
		if (iter->second == nullptr) {
			iter++;
			continue;
		} else {
			deleteEntry((iter++)->first);
		}
	}
}
