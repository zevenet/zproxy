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

#include "cache_commons.h"
#include <cstring>
#include <filesystem>
#include <fstream>
#include <pcreposix.h>
#include <string>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unordered_map>

using namespace std;
namespace st = storage_commons;

#define MAX_STORAGE_SIZE 268435456; //256MB

/**
 * @class ICacheStorage ICacheStorage.h "src/handlers/ICacheStorage.h"
 *
 * @brief Definition for the interface ICacheStorage for implementation
 */
class ICacheStorage {
    protected:
	ICacheStorage()
	{
	}

    public:
	/**
     * @brief initCacheStorage Initialize the storage, setting the mount point and max size
     * @param max_size The max size for the storage
     * @param mount_point the mount point where to put the cached content
     * @return st::STORAGE_STATUS return the status of the storage
     */
	virtual st::STORAGE_STATUS
	initCacheStorage(const size_t max_size, double st_threshold,
			 const std::string &svc,
			 const std::string &mount_point) = 0;
	/**
     * @brief initServiceStorage Initialize the service directory once the system is mounted/ initialized
     * @param svc service name
     * @return STORAGE_STATUS return the status of the storage
     */
	virtual st::STORAGE_STATUS
	initServiceStorage(const std::string &svc) = 0;
	/**
     * @brief getFromStorage get from the storage system the data from the rel_path path
     * @param rel_path is the path where to recover the stored data from
     * @param out_buffer is the buffer where the stored content will be recovered to
     * @return STORAGE_STATUS return the status of the storage
     */
	virtual st::STORAGE_STATUS getFromStorage(const std::string &rel_path,
						  std::string &out_buffer) = 0;
	/**
     * @brief putInStorage store in the mount_point/rel_path path the buffer
     * @param rel_path is the path where to store the buffer content
     * @param buffer is the string with data to store
     * @param response_size its the size of the response for size operations
     * @return STORAGE_STATUS return the status of the storage
     */
	virtual st::STORAGE_STATUS putInStorage(const std::string &rel_path,
						std::string_view buffer,
						size_t response_size) = 0;
	/**
     * @brief getStorageType return the current storage type
     * @return STORAGE_STATUS return the status of the storage
     */
	virtual st::STORAGE_TYPE getStorageType() = 0;
	/**
     * @brief stopCacheStorage stop and clean cache storage paths
     * @return STORAGE_STATUS return the status of the storage
     */
	virtual st::STORAGE_STATUS stopCacheStorage() = 0;
	/**
     * @brief appendData append incoming data to an existing data
     * @param rel_path the path where to append data
     * @param buffer the buffer containing the data to store
     * @return STORAGE_STATUS return the status of the storage
     */
	virtual st::STORAGE_STATUS appendData(const std::string &rel_path,
					      std::string_view buffer) = 0;
	/**
     * @brief deleteInStorage clean the content of an url
     * @param url used to determine the path to delete
     * @return STORAGE_STATUS return the status of the storage
     */
	virtual st::STORAGE_STATUS deleteInStorage(const std::string &url) = 0;
	/**
     * @brief isInStorage checks whether the data file determine by svc and url exists or not
     * @param svc the service name
     * @param url the response url
     * @return STORAGE_STATUS return the status of the storage
     */
	virtual bool isInStorage(const std::string &svc,
				 const std::string &url) = 0;
	/**
     * @brief ~ICacheStorage
     */
	virtual ~ICacheStorage()
	{
	}
};
