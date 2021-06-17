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

#include <fstream>
#include <strings.h>
#include <unistd.h>
#include <memory>

class SystemInfo {
	ssize_t page_size;
	ssize_t l1_data_cache_size;
	ssize_t l2_cache_size;
	ssize_t l1_data_cache_line_size;
	ssize_t l2_cache_line_size;
	static std::shared_ptr<SystemInfo> instance;

    public:
	SystemInfo()
	{
		update();
	}

	static std::shared_ptr<SystemInfo> data()
	{
		if (instance == nullptr)
			instance =
				std::shared_ptr<SystemInfo>(new SystemInfo());
		return instance;
	}

	/**
   * return the number of bytes in a memory page.
   */
	inline ssize_t getSystemPageSize() const
	{
		return page_size;
	}

	/**
   * Get the the line length of the Level 1 data cache in bytes.
   */
	inline ssize_t getL1DataCacheLineSize() const
	{
		return l1_data_cache_line_size;
	}

	/**
 * Get the Level 1 data cache size in bytes.
 */
	inline ssize_t getL2DataCacheLineSize() const
	{
		return l2_cache_line_size;
	}

	/**
   * Get L1 data cache size in bytes
   */
	inline ssize_t getL1DataCacheSize() const
	{
		return l1_data_cache_size;
	}

	/**
 * Get L1 data cache size in bytes
 */
	inline ssize_t getL2DataCacheSize() const
	{
		return l2_cache_size;
	}

	/**
   * update system data
   */
	inline void update()
	{
		page_size = ::sysconf(_SC_PAGESIZE);
		l1_data_cache_size = ::sysconf(_SC_LEVEL1_DCACHE_SIZE);
		l1_data_cache_line_size = ::sysconf(_SC_LEVEL1_DCACHE_LINESIZE);
		l2_cache_size = ::sysconf(_SC_LEVEL2_CACHE_SIZE);
		l2_cache_line_size = ::sysconf(_SC_LEVEL2_CACHE_LINESIZE);
	}

	inline static void getMemoryUsed(double &vm_usage, double &resident_set)
	{
		vm_usage = 0.0;
		resident_set = 0.0;

		// the two fields we want
		unsigned long vsize;
		long rss;
		{
			std::string ignore;
			std::ifstream ifs("/proc/self/stat", std::ios_base::in);
			ifs >> ignore >> ignore >> ignore >> ignore >> ignore >>
				ignore >> ignore >> ignore >> ignore >>
				ignore >> ignore >> ignore >> ignore >>
				ignore >> ignore >> ignore >> ignore >>
				ignore >> ignore >> ignore >> ignore >>
				ignore >> vsize >> rss;
		}

		long page_size_kb =
			sysconf(_SC_PAGE_SIZE) /
			1024; // in case x86-64 is configured to use 2MB pages
		vm_usage = vsize / 1024.0;
		resident_set = rss * page_size_kb;
	}
};
