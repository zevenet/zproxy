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

#include "http_manager.h"
#include "../util/network.h"

ssize_t http_manager::handleChunkedData(HttpStream &stream) {
  auto last_chunk_size = stream.response.chunk_size_left;
  if (last_chunk_size >= stream.backend_connection.buffer_size) {
    stream.response.chunk_size_left -= stream.backend_connection.buffer_size;
  } else {
    size_t data_offset = last_chunk_size;
    size_t new_chunk_left = 0;
    auto chunk_size = http_manager::getLastChunkSize(
        stream.backend_connection.buffer + last_chunk_size,
        stream.backend_connection.buffer_size - stream.response.chunk_size_left,
        data_offset, new_chunk_left, stream.response.content_length);
    //#if PRINT_DEBUG_CHUNKED
    const char *status = chunk_size < 0 ? "*" : chunk_size == 0 ? "/" : "";
    Logger::logmsg(LOG_REMOVE,
                   "[%s] buffer size: %6lu chunk left: %8d => Chunk size: %8d "
                   "Data offset: %6lu Content_length: %8d  next chunk left %8d",
                   status, stream.backend_connection.buffer_size,
                   last_chunk_size, chunk_size, data_offset,
                   stream.response.content_length, new_chunk_left);
    //#endif
    if (chunk_size < 0) {
      //	  const char *new_chunk_buff = stream.backend_connection.buffer
      //+ stream.response.chunk_size_left - 5;
      /* here we have a tricky situation, we have received the last pendind part
       * of last chunk, bute not enough data to process next chunk size */
      //	  stream.response.chunk_buffer_size_offset =
      // stream.backend_connection.buffer_size -
      // stream.response.chunk_size_left;
      return -1;
    } else if (chunk_size == 0) {
      stream.response.chunk_size_left = 0;
      stream.response.chunked_status = CHUNKED_STATUS::CHUNKED_LAST_CHUNK;
      return 0;
    } else {
      stream.response.chunk_size_left = new_chunk_left;
    }
    return static_cast<ssize_t>(new_chunk_left);
  }
  return static_cast<ssize_t>(stream.response.chunk_size_left);
}

ssize_t http_manager::getChunkSize(const std::string &data, size_t data_size,
                                   int &chunk_size_line_len) {
  auto pos = data.find(http::CRLF);
  if (pos != std::string::npos && pos < data_size) {
    chunk_size_line_len = static_cast<int>(pos) + http::CRLF_LEN;
    auto hex = data.substr(0, pos);
    char *error;
    auto chunk_length = ::strtol(hex.data(), &error, 16);
    if (*error != 0) {
      Logger::logmsg(LOG_NOTICE, "strtol() failed: Data size: %d  Buffer: %.*s",
                     data_size, 10, data.data());
      return -1;
    } else {
#if PRINT_DEBUG_CHUNKED
      Logger::logmsg(LOG_DEBUG, "CHUNK found size %s => %d ", hex.data(),
                     chunk_length);
#endif
      return static_cast<ssize_t>(chunk_length);
    }
  }
  //  Logger::logmsg(LOG_NOTICE, "Chunk not found, need more data: Buff size: %d
  //  Buff %.*s ",data_size, 5, data.data());
  return -1;
}

ssize_t http_manager::getLastChunkSize(const char *data, size_t data_size,
                                       size_t &data_offset,
                                       size_t &chunk_size_bytes_left,
                                       size_t &content_length) {
  int chunk_size_len = 0;
  auto chunk_size = getChunkSize(data, data_size, chunk_size_len);
  if (chunk_size > 0) {
    content_length += static_cast<size_t>(chunk_size);
    auto offset = chunk_size + chunk_size_len + http::CRLF_LEN;
    if (data_size > (static_cast<size_t>(offset) + http::CRLF_LEN)) {
      data_offset += static_cast<size_t>(offset);
      auto data_ptr = data + offset;
      return getLastChunkSize(data_ptr, data_size - static_cast<size_t>(offset),
                              data_offset, chunk_size_bytes_left,
                              content_length);
    } else {
      data_offset += data_size;
      chunk_size_bytes_left = static_cast<size_t>(offset) - data_size;
      return chunk_size;
    }
  } else if (chunk_size == 0) {
    return 0;
  } else {
    // an error has ocurred;
    return chunk_size;
  }
}

void http_manager::setBackendCookie(Service *service, HttpStream *stream) {
  if (!service->becookie.empty()) {
    std::string set_cookie_header =
        service->becookie + "=" +
        stream->backend_connection.getBackend()->bekey;
    if (!service->becdomain.empty())
      set_cookie_header += "; Domain=" + service->becdomain;
    if (!service->becpath.empty())
      set_cookie_header += "; Path=" + service->becpath;
    time_t time = std::time(nullptr);
    if (service->becage > 0) {
      time += service->becage;
    } else {
      time += service->ttl;
    }
    char time_string[MAXBUF];
    strftime(time_string, MAXBUF - 1, "%a, %e-%b-%Y %H:%M:%S GMT",
             gmtime(&time));
    set_cookie_header += "; expires=";
    set_cookie_header += time_string;
    stream->response.addHeader(http::HTTP_HEADER_NAME::SET_COOKIE,
                               set_cookie_header);
  }
}

validation::REQUEST_RESULT http_manager::validateRequest(
    HttpRequest &request,
    const ListenerConfig &listener_config_) {  // FIXME
  regmatch_t matches[4];

  auto res = ::regexec(&listener_config_.verb, request.getRequestLine().data(),
                       3,  // include validation data package
                       matches, REG_EXTENDED);
  if (UNLIKELY(res == REG_NOMATCH)) {
    // TODO:: check RPC

    /*
       * if(!strncasecmp(request + matches[1].rm_so, "RPC_IN_DATA",
             matches[1].rm_eo - matches[1].rm_so)) is_rpc = 1; else
             if(!strncasecmp(request + matches[1].rm_so, "RPC_OUT_DATA",
             matches[1].rm_eo - matches[1].rm_so)) is_rpc = 0;
            *
            */

    // TODO:: Content lentgh required on POST command
    // error 411 Length Required
    return validation::REQUEST_RESULT::METHOD_NOT_ALLOWED;
  } else {
    request.setRequestMethod();
  }
  const auto request_url = std::string(request.path, request.path_length);
  if (request_url.find("%00") != std::string::npos) {
    return validation::REQUEST_RESULT::URL_CONTAIN_NULL;
  }

  if (listener_config_.has_pat &&
      regexec(&listener_config_.url_pat, request.path, 0, nullptr, 0)) {
    return validation::REQUEST_RESULT::BAD_URL;
  }

  // Check reqeuest size .
  if (UNLIKELY(listener_config_.max_req > 0 &&
               request.headers_length >
                   static_cast<size_t>(listener_config_.max_req) &&
               request.request_method != http::REQUEST_METHOD::RPC_IN_DATA &&
               request.request_method != http::REQUEST_METHOD::RPC_OUT_DATA)) {
    return validation::REQUEST_RESULT::REQUEST_TOO_LARGE;
  }

  // Check for correct headers
  for (size_t i = 0; i != request.num_headers; i++) {
#if DEBUG_HTTP_HEADERS
    Logger::logmsg(
        LOG_DEBUG, "\t%.*s",
        request.headers[i].name_len + request.headers[i].value_len + 2,
        request.headers[i].name);
#endif
    /* maybe header to be removed */
    MATCHER *m;
    for (m = listener_config_.head_off; m; m = m->next) {
      if (::regexec(&m->pat, request.headers[i].name, 0, nullptr, 0) == 0) {
        request.headers[i].header_off = true;
        break;
      }
    }
    if (request.headers[i].header_off) continue;

    //      Logger::logmsg(LOG_REMOVE, "\t%.*s",request.headers[i].name_len +
    //      request.headers[i].value_len + 2, request.headers[i].name);

    // check header values length
    if (request.headers[i].value_len > MAX_HEADER_VALUE_SIZE)
      return http::validation::REQUEST_RESULT::REQUEST_TOO_LARGE;

    auto header =
        std::string_view(request.headers[i].name, request.headers[i].name_len);
    auto header_value = std::string_view(request.headers[i].value,
                                         request.headers[i].value_len);

    auto it = http::http_info::headers_names.find(header);
    if (it != http::http_info::headers_names.end()) {
      auto header_name = it->second;
      switch (header_name) {
        case http::HTTP_HEADER_NAME::DESTINATION:
          if (listener_config_.rewr_dest != 0) {
            request.headers[i].header_off = true;
            request.add_destination_header = true;
          }
          break;
        case http::HTTP_HEADER_NAME::UPGRADE:
          request.upgrade_header = true;

          break;
        case http::HTTP_HEADER_NAME::CONNECTION:
          if (http_info::connection_values.count(std::string(header_value)) >
                  0 &&
              http_info::connection_values.at(std::string(header_value)) ==
                  CONNECTION_VALUES::UPGRADE)
            request.connection_header_upgrade = true;
          break;
        case http::HTTP_HEADER_NAME::ACCEPT_ENCODING:
          request.accept_encoding_header = true;
          //          request.headers[i].header_off = true;
          break;
        case http::HTTP_HEADER_NAME::TRANSFER_ENCODING:
          if (listener_config_.ignore100continue)
            request.headers[i].header_off = true;
          break;
        case http::HTTP_HEADER_NAME::CONTENT_LENGTH: {
          request.content_length =
              static_cast<size_t>(std::atoi(request.headers[i].value));
          if ((request.content_length - request.message_length) > 0)
            request.message_bytes_left =
                request.content_length - request.message_length;
          continue;
        }
        case http::HTTP_HEADER_NAME::HOST: {
          request.host_header_found = listener_config_.rewr_host == 0;
          request.headers[i].header_off = listener_config_.rewr_host == 1;
          continue;
        }
        case http::HTTP_HEADER_NAME::EXPECT: {
          if (header_value == "100-continue") {
            Logger::logmsg(LOG_REMOVE, "Client Expects 100 continue");
          }
          request.headers[i].header_off = listener_config_.ignore100continue;
          break;
        }
        case http::HTTP_HEADER_NAME::X_FORWARDED_FOR: {
          request.x_forwarded_for_string = header_value;
          request.headers[i].header_off = true;
          break;
        }
        default:
          continue;
      }
    }
  }
  // waf

  return validation::REQUEST_RESULT::OK;
}

validation::REQUEST_RESULT http_manager::validateResponse(
    HttpStream &stream, const ListenerConfig &listener_config_) {
  HttpResponse &response = stream.response;
  /* If the response is 100 continue we need to enable chunked transfer. */
  if (response.http_status_code < 200) {
    //    stream.response.chunked_status =
    //    http::CHUNKED_STATUS::CHUNKED_ENABLED; Logger::logmsg(LOG_DEBUG,
    //    "Chunked transfer enabled");
    return validation::REQUEST_RESULT::OK;
  }
#ifdef CACHE_ENABLED
  stream.request.c_opt.no_store ? response.c_opt.cacheable = false
                                : response.c_opt.cacheable = true;
#endif
  for (size_t i = 0; i != response.num_headers; i++) {
    // check header values length

    auto header = std::string_view(response.headers[i].name,
                                   response.headers[i].name_len);
    auto header_value = std::string_view(response.headers[i].value,
                                         response.headers[i].value_len);
#if DEBUG_HTTP_HEADERS
    Logger::logmsg(
        LOG_DEBUG, "\t%.*s",
        response.headers[i].name_len + response.headers[i].value_len + 2,
        response.headers[i].name);
#endif
    auto it = http::http_info::headers_names.find(header);
    if (it != http::http_info::headers_names.end()) {
      const auto header_name = it->second;
      switch (header_name) {
        case http::HTTP_HEADER_NAME::CONTENT_LENGTH: {
          stream.response.content_length =
              static_cast<size_t>(std::atoi(header_value.data()));
          if ((stream.response.content_length -
               stream.response.message_length) > 0)
            stream.response.message_bytes_left =
                stream.response.content_length - stream.response.message_length;
          continue;
        }
        case http::HTTP_HEADER_NAME::CONTENT_LOCATION: {
          if (listener_config_.rewr_loc == 0) continue;
          break;
        }
        case http::HTTP_HEADER_NAME::LOCATION: {
          // Rewrite location
          std::string location_header_value(response.headers[i].value,
                                            response.headers[i].value_len);
          if (listener_config_.rewr_loc == 0) continue;
          regmatch_t matches[4];

          if (regexec(&Config::LOCATION, location_header_value.data(), 4,
                      matches, 0)) {
            continue;
          }

          std::string proto(
              location_header_value.data() + matches[1].rm_so,
              static_cast<size_t>(matches[1].rm_eo - matches[1].rm_so));
          std::string host(
              location_header_value.data() + matches[2].rm_so,
              static_cast<size_t>(matches[2].rm_eo - matches[2].rm_so));

          //        if (location_header_value[matches[3].rm_so] == '/') {
          //          matches[3].rm_so++;
          //        }
          std::string path(
              location_header_value.data() + matches[3].rm_so,
              static_cast<size_t>(matches[3].rm_eo - matches[3].rm_so));

          char ip[100]{'\0'};
          if (!Network::HostnameToIp(host.data(), ip)) {
            Logger::logmsg(LOG_NOTICE, "Couldn't get host ip");
            continue;
          }
          std::string_view host_ip(ip);
          if (host_ip == listener_config_.address ||
              host_ip == stream.backend_connection.getBackend()->address) {
            std::string header_value_ =
                listener_config_.ctx != nullptr ? "https://" : "http://";
            header_value_ += host;
            header_value_ += ":";
            header_value_ += std::to_string(listener_config_.port);
            header_value_ += path;
            response.addHeader(http::HTTP_HEADER_NAME::LOCATION, header_value_);
            //          response.addHeader(http::HTTP_HEADER_NAME::CONTENT_LOCATION,
            //                  getLastChunkSize           path);
            response.headers[i].header_off = true;
          }
          break;
        }
        case http::HTTP_HEADER_NAME::STRICT_TRANSPORT_SECURITY:
          if (static_cast<Service *>(stream.request.getService())
                  ->service_config.sts > 0)
            response.headers[i].header_off = true;
          break;
        case http::HTTP_HEADER_NAME::TRANSFER_ENCODING:
          switch (header_value[0]) {
            case 'c': {
              if (header_value[1] == 'h') {  // no content-length
                response.transfer_encoding_type =
                    TRANSFER_ENCODING_TYPE::CHUNKED;
                response.chunked_status = http::CHUNKED_STATUS::CHUNKED_ENABLED;
#ifdef CACHE_ENABLED
                if (stream.response.message_length > 0) {
                  size_t data_offset = 0;
                  size_t new_chunk_left = 0;
                  auto chunk_size = http_manager::getLastChunkSize(
                      stream.response.message, stream.response.message_length,
                      data_offset, new_chunk_left, response.content_length);
#if PRINT_DEBUG_CHUNKED
                  Logger::logmsg(LOG_REMOVE, ">>>> Chunk size %d left %d ",
                                 chunk_size, new_chunk_left);
#endif
                  stream.response.content_length +=
                      static_cast<size_t>(chunk_size);
                  if (chunk_size == 0) {
#if PRINT_DEBUG_CHUNKED
                    Logger::logmsg(LOG_REMOVE, "Set LAST CHUNK");
#endif
                    stream.response.chunk_size_left = 0;
                    stream.response.chunked_status =
                        CHUNKED_STATUS::CHUNKED_LAST_CHUNK;
                  } else {
                    stream.response.chunk_size_left = new_chunk_left;
                  }
                }
#endif
              } else if (header_value[2] == 'o') {
                response.transfer_encoding_type =
                    TRANSFER_ENCODING_TYPE::COMPRESS;
              }
              break;
            }
            case 'd':  // deflate
              response.transfer_encoding_type = TRANSFER_ENCODING_TYPE::DEFLATE;
              break;
            case 'g':  // gzip
              response.transfer_encoding_type = TRANSFER_ENCODING_TYPE::GZIP;
              break;
            case 'i':  // identity
              response.transfer_encoding_type =
                  TRANSFER_ENCODING_TYPE::IDENTITY;
              break;
          }
          break;
        default:
          continue;
      }
    }

    /* maybe header to be removed from responses */
    //  MATCHER *m;
    // for (m = listener_config_.head_off; m; m = m->next) {
    //  if ((response.headers[i].header_off =
    //          ::regexec(&m->pat, response.headers[i].name, 0, nullptr, 0) !=
    //          0))
    //    break;
    // }
  }
  return validation::REQUEST_RESULT::OK;
}

void http_manager::replyError(http::Code code, const std::string &code_string,
                              const std::string &str, Connection &target,
                              SSLConnectionManager *ssl_manager) {
  size_t result;
  char caddr[200];

  if (UNLIKELY(Network::getPeerAddress(target.getFileDescriptor(), caddr,
                                       200) == nullptr)) {
    Logger::LogInfo("Error getting peer address", LOG_DEBUG);
  } else {
    Logger::logmsg(LOG_WARNING, "(%lx) e%d %s %s from %s",
                   std::this_thread::get_id(), static_cast<int>(code),
                   code_string.data(), target.buffer, caddr);
  }
  auto response_ = http::getHttpResponse(code, code_string, str);

  if (!target.ssl_connected) {
    target.write(response_.c_str(), response_.length());
  } else if (ssl_manager != nullptr) {
    ssl_manager->handleWrite(target, response_.c_str(), response_.length(),
                             result);
  }
}

void http_manager::replyRedirect(HttpStream &stream,
                                 SSLConnectionManager *ssl_manager) {
  std::string new_url =
      stream.backend_connection.getBackend()->backend_config.url;
  new_url += stream.request.getUrl();
  auto response_ = http::getRedirectResponse(
      static_cast<http::Code>(
          stream.backend_connection.getBackend()->backend_config.be_type),
      new_url);
  stream.client_connection.write(response_.c_str(), response_.length());
  if (!stream.client_connection.ssl_connected) {
    stream.client_connection.write(response_.c_str(), response_.length());
  } else if (ssl_manager != nullptr) {
    size_t written = 0;
    ssl_manager->handleWrite(stream.client_connection, response_.c_str(),
                             response_.length(), written);
  }
}
void http_manager::replyRedirect(int code, const std::string &url,
                                 Connection &target,
                                 SSLConnectionManager *ssl_manager) {
  auto response_ =
      http::getRedirectResponse(static_cast<http::Code>(code), url);
  if (!target.ssl_connected) {
    target.write(response_.c_str(), response_.length());
  } else if (ssl_manager != nullptr) {
    size_t written = 0;
    ssl_manager->handleWrite(target, response_.c_str(), response_.length(),
                             written);
  }
}
