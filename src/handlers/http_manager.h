//
// Created by abdess on 4/6/19.
//
#pragma once

#include <glob.h>
#include "../http/http_stream.h"
#include "../service/Service.h"
#include "../http/http.h"
#include "zlib_util.h"
#include "../config/pound_struct.h"
#include "../util/common.h"

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
 * @return if there is not any error it returns validation::REQUEST_RESULT::OK.
 * If errors happen, it returns the corresponding element of
 * validation::REQUEST_RESULT.
 */
  static validation::REQUEST_RESULT validateRequest(HttpRequest &request,const ListenerConfig & listener_config_);

  /**
   * @brief Validates the response.
   *
   * It checks that all the headers are well formed and mark the headers off if
   * needed.
   *
   * @param stream is the HttpStream to get the HttpResponse from.
   * @return if there is not any error it returns validation::REQUEST_RESULT::OK.
   * If errors happen, it returns the corresponding element of
   * validation::REQUEST_RESULT.
   */
  static validation::REQUEST_RESULT validateResponse(HttpStream &stream, const ListenerConfig & listener_config_);

  /**
   * @brief If the backend cookie is enabled adds the headers with the parameters
   * set.
   *
   * @param service is the Service to get the backend cookie parameters set.
   * @param stream is the HttpStream to get the request to add the headers.
   */
  static void setBackendCookie(Service *service, HttpStream *stream);

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

  /**
   * @brief Check if last chunk found in stream response and set stream chunk status
   *
   * @param stream is the HttpStream to get the response to take the chunked
   * data.
   * @return current chunk pending bytes or -1 if need more data to get chunk size.
   */

  /**/
  static ssize_t handleChunkedData(HttpStream &stream);
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
  static ssize_t getChunkSize(const std::string &data, size_t data_size, int &chunk_size_line_len);
  /**
 * @brief Search for last chunk size in buffer data
 *
 *
 * @param data buffer to search chunks
 * @param data_size buffer size
 * @param data_offset bytes of data consumed in search
 * @param chunk_size_bytes_left reference to variable to store bytes left to read for last chunk found
 * @param total_chunks_size reference to variable to add chunks size found
 * @return last chunk size found.
 */

  /**/
  static ssize_t getLastChunkSize(const char *data,
                                 size_t data_size,
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
  static void replyError(HttpStatus::Code code, const std::string&code_string,
                                  const std::string &str, Connection & target,
				  ssl::SSLConnectionManager *ssl_manager);

  /**
   * @brief Reply a redirect message with the configuration specified in the
   * BackendConfig.
   *
   * @param backend_config is the BackendConfig to get the redirect information.
   */
  static void replyRedirect(HttpStream&stream, SSLConnectionManager*ssl_manager);

  /**
   * @brief Reply a redirect message with the @p code and pointing to the
   * @p url.
   *
   * @param code is the redirect code.
   * @param url is the url itself.
   */
  static void replyRedirect(int code, const std::string &url,
                            Connection &target,
                            SSLConnectionManager *ssl_manager);
};

