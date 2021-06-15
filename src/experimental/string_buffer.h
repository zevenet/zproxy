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

#ifndef NEW_ZPROXY_STREAM_BUFFER_H
#define NEW_ZPROXY_STREAM_BUFFER_H
#include <string>

class StringBuffer {
    public:
	StringBuffer();
	StringBuffer &operator<<(char const *s);
	StringBuffer &operator<<(int i);
	StringBuffer &operator<<(std::string const &s);
	StringBuffer &operator<<(StringBuffer const &s);
	std::string const &string() const;
	void erase(unsigned int end);
	void addData(char const *s, size_t size);

    private:
	std::string buffer;
};

#endif //NEW_ZPROXY_STREAM_BUFFER_H
