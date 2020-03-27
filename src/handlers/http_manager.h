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

#include "../config/config_data.h"
#include "../http/http.h"
#include "../http/http_stream.h"
#include "../service/service.h"
#include "../util/common.h"
#ifdef ENABLE_ON_FLY_COMRESSION
#include "../util/zlib_util.h"
#endif

using namespace http;

class http_manager {
 public:
  /**
   * @brief Validates the request.
   *
   * It checks that all the headers are well formed and mark the headers off if
   * needed.
   *
   * @param request is the HttpRequest to modify.
   * @return if there is not any error it returns
   * validation::REQUEST_RESULT::OK. If errors happen, it returns the
   * corresponding element of validation::REQUEST_RESULT.
   */
  static validation::REQUEST_RESULT validateRequest(HttpStream &stream);

  /**
   * @brief Validates the response.
   *
   * It checks that all the headers are well formed and mark the headers off if
   * needed.
   *
   * @param stream is the HttpStream to get the HttpResponse from.
   * @return if there is not any error it returns
   * validation::REQUEST_RESULT::OK. If errors happen, it returns the
   * corresponding element of validation::REQUEST_RESULT.
   */
  static validation::REQUEST_RESULT validateResponse(HttpStream &stream);

  /**
   * @brief If the backend cookie is enabled adds the headers with the
   * parameters set.
   *
   * @param service is the Service to get the backend cookie parameters set.
   * @param stream is the HttpStream to get the request to add the headers.
   */
  static void setBackendCookie(Service *service, HttpStream *stream);

  /**
   * @brief Check if last chunk found in stream response and set stream chunk
   * status
   *
   * @param stream is the HttpStream to get the response to take the chunked
   * data.
   * @return current chunk pending bytes or -1 if need more data to get chunk
   * size.
   */

  /**/
  static ssize_t handleChunkedData(Connection &connection, http_parser::HttpData & http_data);
  /**
   * @brief Get chunk size from buffer
   * if
   * @param data buffer to search chunks
   * @param data_size buffer size
   * @param chunk_size_len bytes of data consumed in search
   * @param chunk_size_line_len store chunk size line length
   * @return Chunk size or -1 en case of error.
   */

  /**/
  static ssize_t getChunkSize(const std::string &data, size_t data_size,
                              int &chunk_size_line_len);
  /**
   * @brief Search for last chunk size in buffer data
   *
   *
   * @param data buffer to search chunks
   * @param data_size buffer size
   * @param data_offset bytes of data consumed in search
   * @param chunk_size_bytes_left reference to variable to store bytes left to
   * read for last chunk found
   * @param total_chunks_size reference to variable to add chunks size found
   * @return last chunk size found.
   */

  /**/
  static ssize_t getLastChunkSize(const char *data, size_t data_size,
                                  size_t &data_offset,
                                  size_t &chunk_size_bytes_left,
                                  size_t &total_chunks_size);
  /**
   * @brief Replies an specified error to the client.
   *
   * It replies the specified error @p code with the @p code_string and the
   * error page @p string. It also replies HTTPS errors.
   *
   * @param code of the error.
   * @param code_string is the error as string format.
   * @param string is the error page to show.
   * @param listener_config is the ListenerConfig used to get the HTTPS
   * information.
   * @param ssl_manager is the SSLConnectionManager that handles the HTTPS
   * client connection.
   */
  static void replyError(http::Code code, const std::string &code_string,
                         const std::string &str, Connection &target);

  /**
   * @brief Reply a redirect message with the configuration specified in the
   * BackendConfig.
   *
   * @param backend_config is the BackendConfig to get the redirect information.
   */
  static bool replyRedirect(HttpStream &stream,
                            const Backend &redirect_backend);

  /**
   * @brief Reply a redirect message with the @p code and pointing to the
   * @p url.
   *
   * @param code is the redirect code.
   * @param url is the url itself.
   */
  static bool replyRedirect(int code, const std::string &url,
                            HttpStream &stream);
};
