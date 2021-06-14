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

#include "../http/http.h"
#include "../http/http_stream.h"
#include "../service/service.h"
#include "../../zcutils/zcu_zlib.h"

class Compression {
    public:
	/**
   * @brief Applies compression to the response message.
   *
   * If one of the encoding accepted in the Accept Encoding Header matchs with
   * the set in the CompressionAlgorithm parameter and the response is not
   * already compressed, compress the response message.
   *
   * @param service is the Service to get the compression algorithm parameter
   * set.
   * @param stream is the HttpStream to get the response to compress.
   */
	static void applyCompression(Service *service, HttpStream *stream);
};
