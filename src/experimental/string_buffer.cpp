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
#include "string_buffer.h"
StringBuffer::StringBuffer() : buffer()
{
}

StringBuffer &StringBuffer::operator<<(const char *s)
{
	buffer += s;
	//  buffer.insert(std::string(s));
	return *this;
}

StringBuffer &StringBuffer::operator<<(int i)
{
	buffer += std::to_string(i);
	return *this;
}

StringBuffer &StringBuffer::operator<<(std::string const &s)
{
	buffer += s;
	return *this;
}

StringBuffer &StringBuffer::operator<<(StringBuffer const &s)
{
	*this << s.string();
	return *this;
}

std::string const &StringBuffer::string() const
{
	return buffer;
}

void StringBuffer::erase(unsigned int end)
{
	buffer.erase(buffer.begin(), buffer.begin() + end);
}

void StringBuffer::addData(char const *s, size_t size)
{
	for (int i = 0; i < size; i++)
		buffer += s[0];
}
