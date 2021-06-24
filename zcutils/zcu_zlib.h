/*
 *   This file is part of zcutils, ZEVENET Core Utils.
 *
 *   Copyright (C) ZEVENET SL.
 *
 *   This program is free software: you can redistribute it and/or modify
 *   it under the terms of the GNU Affero General Public License as
 *   published by the Free Software Foundation, either version 3 of the
 *   License, or any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU Affero General Public License for more details.
 *
 *   You should have received a copy of the GNU Affero General Public License
 *   along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#ifndef _ZCU_ZLIB_H_
#define _ZCU_ZLIB_H_

#include <string.h>
#include <zlib.h>
#include <sstream>
#include <stdexcept>
#include <string>

using std::string;
using std::stringstream;

// http://mail-archives.apache.org/mod_mbox/trafficserver-dev/201110.mbox/%3CCACJPjhYf=+br1W39vyazP=ix
// eQZ-4Gh9-U6TtiEdReG3S4ZZng@mail.gmail.com%3E
#define MOD_GZIP_ZLIB_WINDOWSIZE 15
#define MOD_GZIP_ZLIB_CFACTOR 9
#define MOD_GZIP_ZLIB_BSIZE 8096

bool zcu_zlib_compress_message_deflate(
	const std::string &str, std::string &outstring,
	int compressionlevel = Z_BEST_COMPRESSION);

bool zcu_zlib_compress_message_gzip(const std::string &str,
				    std::string &outstring,
				    int compressionlevel = Z_BEST_COMPRESSION);

/** Decompress an STL string using zlib and return the original data. */
bool zcu_zlib_decompress_message_deflate(const std::string &str,
					 std::string &outstring);

bool zcu_zlib_decompress_message_gzip(const std::string &str,
				      std::string &outstring);

#endif /* _ZCU_ZLIB_H_ */
