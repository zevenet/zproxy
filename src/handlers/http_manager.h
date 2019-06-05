//
// Created by abdess on 4/6/19.
//
#pragma once

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
   * @brief Handles all the chunked operations.
   *
   * If the http::CHUNKED_STATUS is enabled then matchs the chunk length and
   * updates the status.
   *
   * @param stream is the HttpStream to get the response to take the chunked
   * data.
   * @return if chunked is enabled returns true, if not returns false.
   */
  static bool transferChunked(HttpStream *stream);

};

