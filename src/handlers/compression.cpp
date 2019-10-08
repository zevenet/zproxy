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

#include "compression.h"

void Compression::applyCompression(Service *service, HttpStream *stream) {
  http::TRANSFER_ENCODING_TYPE compression_type;
  if (service->service_config.compression_algorithm.empty()) return;
  /* Check if we have found the accept encoding header in the request but not
   * the transfer encoding in the response. */
  if ((stream->response.chunked_status == http::CHUNKED_STATUS::CHUNKED_DISABLED)
	  && stream->request.accept_encoding_header) {
	std::string compression_value;
	stream->request.getHeaderValue(http::HTTP_HEADER_NAME::ACCEPT_ENCODING, compression_value);

	/* Check if we accept any of the compression algorithms. */
	size_t initial_pos;
	initial_pos = compression_value.find(service->service_config.compression_algorithm);
	if (initial_pos != std::string::npos) {
	  compression_value = service->service_config.compression_algorithm;
	  stream->response.addHeader(http::HTTP_HEADER_NAME::TRANSFER_ENCODING, compression_value);
	  stream->response.chunked_status = http::CHUNKED_STATUS::CHUNKED_ENABLED;
	  compression_type = http::http_info::compression_types.at(compression_value);

	  /* Get the message_uncompressed. */
	  std::string message_no_compressed = std::string(stream->response.message, stream->response.message_length);
	  /* We are going to do the compression depending on the compression
	   * algorithm. */
	  switch (compression_type) {
		case http::TRANSFER_ENCODING_TYPE::GZIP: {
		  std::string message_compressed_gzip;
		  if (!zlib::compress_message_gzip(message_no_compressed, message_compressed_gzip))
			Debug::logmsg(LOG_ERR, "Error while compressing.");
		  strncpy(stream->response.message, message_compressed_gzip.c_str(), stream->response.message_length);
		  break;
		}
		case http::TRANSFER_ENCODING_TYPE::DEFLATE: {
		  std::string message_compressed_deflate;
		  if (!zlib::compress_message_deflate(message_no_compressed, message_compressed_deflate))
			Debug::logmsg(LOG_ERR, "Error while compressing.");
		  strncpy(stream->response.message, message_compressed_deflate.c_str(), stream->response.message_length);
		  break;
		}
		default: break;
	  }
	}
  }
}