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

#ifndef _ZPROXY_COUNTER_H_
#define _ZPROXY_COUNTER_H_

#include <atomic>

template < typename T > class Counter {
	bool decrement__;

public:
	Counter(bool decrement = true) : decrement__(decrement)
	{
		count++;
	}
	virtual ~Counter()
	{
		if (decrement__)
		count--;
	}
	static std::atomic < int > count;
};

template < typename T > std::atomic < int > Counter < T > ::count(0);

namespace debug__
{
#define DEFINE_OBJECT_COUNTER(ObjectName)                                      \
	struct ObjectName : Counter < ObjectName > {                              \
		ObjectName() : Counter < ObjectName > (false)                      \
		{                                                              \
		}                                                              \
	};
#if DEBUG_ZCU_LOG
#define DEBUG_COUNTER_HIT(x) x UNIQUE_NAME(counter_hit)
#else
#define DEBUG_COUNTER_HIT(x)
#endif
} // namespace debug__

#endif /* _ZPROXY_COUNTER_H_ */
