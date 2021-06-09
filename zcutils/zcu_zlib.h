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

static inline bool
zcu_zlib_compress_message_deflate(const std::string &str,
				  std::string &outstring,
				  int compressionlevel = Z_BEST_COMPRESSION)
{
	z_stream zs; // z_stream is zlib's control structure
	memset(&zs, 0, sizeof(zs));

	if (deflateInit(&zs, compressionlevel) != Z_OK)
		return false;

	zs.next_in = (Bytef *)str.data();
	zs.avail_in = str.size(); // set the z_stream's input

	int ret;
	char outbuffer[32768];

	// retrieve the compressed bytes blockwise
	do {
		zs.next_out = reinterpret_cast<Bytef *>(outbuffer);
		zs.avail_out = sizeof(outbuffer);

		ret = deflate(&zs, Z_FINISH);

		if (outstring.size() < zs.total_out) {
			// append the block to the output string
			outstring.append(outbuffer,
					 zs.total_out - outstring.size());
		}
	} while (ret == Z_OK);

	deflateEnd(&zs);

	if (ret != Z_STREAM_END) { // an error occurred that was not EOF
		std::ostringstream oss;
		oss << "Exception during zlib compression: (" << ret << ") "
		    << zs.msg;
		return false;
	}

	return true;
}

static inline bool
zcu_zlib_compress_message_gzip(const std::string &str, std::string &outstring,
			       int compressionlevel = Z_BEST_COMPRESSION)
{
	z_stream zs; // z_stream is zlib's control structure
	memset(&zs, 0, sizeof(zs));

	if (deflateInit2(&zs, compressionlevel, Z_DEFLATED,
			 MOD_GZIP_ZLIB_WINDOWSIZE + 16, MOD_GZIP_ZLIB_CFACTOR,
			 Z_DEFAULT_STRATEGY) != Z_OK) {
		return false;
	}

	zs.next_in = (Bytef *)str.data();
	zs.avail_in = str.size(); // set the z_stream's input

	int ret;
	char outbuffer[32768];

	// retrieve the compressed bytes blockwise
	do {
		zs.next_out = reinterpret_cast<Bytef *>(outbuffer);
		zs.avail_out = sizeof(outbuffer);

		ret = deflate(&zs, Z_FINISH);

		if (outstring.size() < zs.total_out) {
			// append the block to the output string
			outstring.append(outbuffer,
					 zs.total_out - outstring.size());
		}
	} while (ret == Z_OK);

	deflateEnd(&zs);

	if (ret != Z_STREAM_END) { // an error occurred that was not EOF
		std::ostringstream oss;
		oss << "Exception during zlib compression: (" << ret << ") "
		    << zs.msg;
		return false;
	}

	return true;
}

/** Decompress an STL string using zlib and return the original data. */
static inline bool zcu_zlib_decompress_message_deflate(const std::string &str,
						       std::string &outstring)
{
	z_stream zs; // z_stream is zlib's control structure
	memset(&zs, 0, sizeof(zs));

	if (inflateInit(&zs) != Z_OK)
		return false;

	zs.next_in = (Bytef *)str.data();
	zs.avail_in = str.size();

	int ret;
	char outbuffer[32768];

	// get the decompressed bytes blockwise using repeated calls to inflate
	do {
		zs.next_out = reinterpret_cast<Bytef *>(outbuffer);
		zs.avail_out = sizeof(outbuffer);

		ret = inflate(&zs, 0);

		if (outstring.size() < zs.total_out) {
			outstring.append(outbuffer,
					 zs.total_out - outstring.size());
		}

	} while (ret == Z_OK);

	inflateEnd(&zs);

	if (ret != Z_STREAM_END) { // an error occurred that was not EOF
		std::ostringstream oss;
		oss << "Exception during zlib decompression: (" << ret << ") "
		    << zs.msg;
		return false;
	}

	return true;
}

static inline bool zcu_zlib_decompress_message_gzip(const std::string &str,
						    std::string &outstring)
{
	z_stream zs; // z_stream is zlib's control structure
	memset(&zs, 0, sizeof(zs));

	if (inflateInit2(&zs, MOD_GZIP_ZLIB_WINDOWSIZE + 16) != Z_OK)
		return false;

	zs.next_in = (Bytef *)str.data();
	zs.avail_in = str.size();

	int ret;
	char outbuffer[32768];

	// get the decompressed bytes blockwise using repeated calls to inflate
	do {
		zs.next_out = reinterpret_cast<Bytef *>(outbuffer);
		zs.avail_out = sizeof(outbuffer);

		ret = inflate(&zs, 0);

		if (outstring.size() < zs.total_out) {
			outstring.append(outbuffer,
					 zs.total_out - outstring.size());
		}

	} while (ret == Z_OK);

	inflateEnd(&zs);

	if (ret != Z_STREAM_END) { // an error occurred that was not EOF
		std::ostringstream oss;
		oss << "Exception during zlib decompression: (" << ret << ") "
		    << zs.msg;
		return false;
	}

	return true;
}

#endif /* _ZCU_ZLIB_H_ */
