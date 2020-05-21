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
#include "../config/regex_manager.h"
#include "../util/network.h"

//#define PRINT_DEBUG_CHUNKED 1

ssize_t http_manager::handleChunkedData(Connection &connection, http_parser::HttpData & http_data) {
  auto last_chunk_size = http_data.chunk_size_left;
  if (last_chunk_size >= connection.buffer_size) {
    http_data.chunk_size_left -= connection.buffer_size;
  } else {
    size_t data_offset = last_chunk_size;
    size_t new_chunk_left = 0;
    auto chunk_size = http_manager::getLastChunkSize(
        connection.buffer + last_chunk_size,
        connection.buffer_size - http_data.chunk_size_left,
        data_offset, new_chunk_left, http_data.content_length);
    //#if PRINT_DEBUG_CHUNKED
    const char *status = chunk_size < 0 ? "*" : chunk_size == 0 ? "/" : "";
    Logger::logmsg(LOG_REMOVE,
                   "[%s] buffer size: %6lu chunk left: %8d => Chunk size: %8d "
                   "Data offset: %6lu Content_length: %8d  next chunk left %8d",
                   status, connection.buffer_size,
                   last_chunk_size, chunk_size, data_offset,
                   http_data.content_length, new_chunk_left);
    //#endif
    if (chunk_size < 0) {
      //	  const char *new_chunk_buff = connection.buffer
      //+ http_data.chunk_size_left - 5;
      /* here we have a tricky situation, we have received the last pendind part
       * of last chunk, bute not enough data to process next chunk size */
      //	  http_data.chunk_buffer_size_offset =
      // connection.buffer_size -
      // http_data.chunk_size_left;
      return -1;
    } else if (chunk_size == 0) {
      http_data.chunk_size_left = 0;
      http_data.chunked_status = CHUNKED_STATUS::CHUNKED_LAST_CHUNK;
#if PRINT_DEBUG_CHUNKED
      Logger::logmsg(LOG_REMOVE, "LAST CHUNK");
#endif
      return 0;
    } else {
      http_data.chunk_size_left = new_chunk_left;
    }
    return static_cast<ssize_t>(new_chunk_left);
  }
  return static_cast<ssize_t>(http_data.chunk_size_left);
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
  if (!service->becookie.empty() && !stream->backend_connection.getBackend()->bekey.empty()) {
//    std::string set_cookie_header =
//        service->becookie + "=" +
//        stream->backend_connection.getBackend()->bekey;
//    if (!service->becdomain.empty())
//      set_cookie_header += "; Domain=" + service->becdomain;
//    if (!service->becpath.empty())
//      set_cookie_header += "; Path=" + service->becpath;
//    time_t time = std::time(nullptr);
//    if(service->becage != 0) {
//      if (service->becage > 0) {
//        time += service->becage;
//      } else {
//        time += service->ttl;
//      }
//      char time_string[MAXBUF];
//      strftime(time_string, MAXBUF - 1, "%a, %e-%b-%Y %H:%M:%S GMT",
//               gmtime(&time));
//      set_cookie_header += "; expires=";
//      set_cookie_header += time_string;
//    }
    stream->response.addHeader(http::HTTP_HEADER_NAME::SET_COOKIE,
                               stream->backend_connection.getBackend()->bekey);
  }
}

validation::REQUEST_RESULT http_manager::validateRequest(HttpStream &stream) {
  regmatch_t matches[4];
  auto &listener_config_ = *stream.service_manager->listener_config_;
  HttpRequest &request = stream.request;
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
  bool connection_close_pending = false;
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
        case http::HTTP_HEADER_NAME::CONNECTION: {
          if (http_info::connection_values.count(std::string(header_value)) >
                  0 &&
              http_info::connection_values.at(std::string(header_value)) ==
                  CONNECTION_VALUES::UPGRADE)
            request.connection_header_upgrade = true;
          else if(header_value.find("close") != std::string::npos){
            connection_close_pending = true;
          }
          break;
        }
        case http::HTTP_HEADER_NAME::ACCEPT_ENCODING:
          request.accept_encoding_header = true;
          //          request.headers[i].header_off = true;
          break;
        case http::HTTP_HEADER_NAME::TRANSFER_ENCODING:
       //   if (listener_config_.ignore100continue)
         //   request.headers[i].header_off = true;
          switch (header_value[0]) {
            case 'c': {
              if (header_value[1] == 'h') {  // no content-length
                request.transfer_encoding_type =
                    TRANSFER_ENCODING_TYPE::CHUNKED;
                request.chunked_status = http::CHUNKED_STATUS::CHUNKED_ENABLED;
#ifdef CACHE_ENABLED
                if (request.message_length > 0) {
                  size_t data_offset = 0;
                  size_t new_chunk_left = 0;
                  auto chunk_size = http_manager::getLastChunkSize(
                      request.message, request.message_length,
                      data_offset, new_chunk_left, request.content_length);
#if PRINT_DEBUG_CHUNKED
                  Logger::logmsg(LOG_REMOVE, ">>>> Chunk size %d left %d ",
                                 chunk_size, new_chunk_left);
#endif
                  request.content_length +=
                      static_cast<size_t>(chunk_size);
                  if (chunk_size == 0) {
#if PRINT_DEBUG_CHUNKED
                    Logger::logmsg(LOG_REMOVE, "Set LAST CHUNK");
#endif
                    request.chunk_size_left = 0;
                    request.chunked_status =
                        CHUNKED_STATUS::CHUNKED_LAST_CHUNK;
                  } else {
                    request.chunk_size_left = new_chunk_left;
                  }
                }
#endif
              } else if (header_value[2] == 'o') {
                request.transfer_encoding_type =
                    TRANSFER_ENCODING_TYPE::COMPRESS;
              }
              break;
            }
            case 'd':  // deflate
              request.transfer_encoding_type = TRANSFER_ENCODING_TYPE::DEFLATE;
              break;
            case 'g':  // gzip
              request.transfer_encoding_type = TRANSFER_ENCODING_TYPE::GZIP;
              break;
            case 'i':  // identity
              request.transfer_encoding_type =
                  TRANSFER_ENCODING_TYPE::IDENTITY;
              break;
          }
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
  if(connection_close_pending && request.content_length == 0 && request.chunked_status == http::CHUNKED_STATUS::CHUNKED_DISABLED){
    //we have unknown amount of body data pending, wait until connection is closed
    //FIXME:: As workaround we use chunked
    request.transfer_encoding_type = TRANSFER_ENCODING_TYPE::CHUNKED;
    request.chunked_status = http::CHUNKED_STATUS::CHUNKED_ENABLED;
  }
  return validation::REQUEST_RESULT::OK;
}

validation::REQUEST_RESULT http_manager::validateResponse(HttpStream &stream) {
  auto &listener_config_ = *stream.service_manager->listener_config_;
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
  bool connection_close_pending = false;
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
        case http::HTTP_HEADER_NAME::CONNECTION:
        {
          if(header_value.find("close") != std::string::npos){
            connection_close_pending = true;
          }
        }
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
          // Rewrite location
          std::string location_header_value(response.headers[i].value,
                                            response.headers[i].value_len);
          regmatch_t matches[4];

          if (regexec(&regex_set::LOCATION, location_header_value.data(), 4,
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
          std::string host_ip(ip);
          if (host_ip == listener_config_.address ||
              host_ip == stream.backend_connection.getBackend()->address) {
            if (!stream.request.getHeaderValue(http::HTTP_HEADER_NAME::HOST,
                                               host_ip)) {
              host_ip = listener_config_.address;
              host_ip += ":";
              host_ip += std::to_string(listener_config_.port);
            }
            std::string header_value_;
            if (listener_config_.rewr_loc < 2) {
              header_value_ =
                  listener_config_.ctx != nullptr ? "https://" : "http://";
            } else {
              header_value_ = proto;
              header_value_ += "://";
            }
            header_value_ += host_ip;
            header_value_ += path;
            response.addHeader(http::HTTP_HEADER_NAME::CONTENT_LOCATION,
                               header_value_);
            response.headers[i].header_off = true;
          }
          break;
        }
        case http::HTTP_HEADER_NAME::LOCATION: {
          if (listener_config_.rewr_loc == 0) continue;
          // Rewrite location
          std::string location_header_value(response.headers[i].value,
                                            response.headers[i].value_len);
          regmatch_t matches[4];

          if (regexec(&regex_set::LOCATION, location_header_value.data(), 4,
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
          std::string host_ip(ip);
          if (host_ip == listener_config_.address ||
              host_ip == stream.backend_connection.getBackend()->address) {
            if (!stream.request.getHeaderValue(http::HTTP_HEADER_NAME::HOST,
                                               host_ip)) {
              host_ip = listener_config_.address;
              host_ip += ":";
              host_ip += std::to_string(listener_config_.port);
            }
            std::string header_value_;
            if (listener_config_.rewr_loc < 2) {
              header_value_ =
                  listener_config_.ctx != nullptr ? "https://" : "http://";
            } else {
              header_value_ = proto;
              header_value_ += "://";
            }
            header_value_ += host_ip;
            header_value_ += path;
            response.addHeader(http::HTTP_HEADER_NAME::LOCATION, header_value_);
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
        case http::HTTP_HEADER_NAME::SET_COOKIE: {
          auto service = static_cast<Service *>(stream.request.getService());
          if (service->service_config.sess_type == SESS_TYPE::SESS_COOKIE) {
            service->updateSessionCookie(
                stream.client_connection, stream.request, header_value,
                *stream.backend_connection.getBackend());
          }
          break;
        }
        default:
          break;
      }
    }
    /* maybe header to be removed from response */
    MATCHER *m;
    for (m = listener_config_.response_head_off; m; m = m->next) {
      if (::regexec(&m->pat, response.headers[i].name, 0, nullptr, 0) == 0) {
        response.headers[i].header_off = true;
        break;
      }
    }
  }
  if(connection_close_pending && response.content_length == 0 && response.chunked_status == http::CHUNKED_STATUS::CHUNKED_DISABLED){
    //we have unknown amount of body data pending, wait until connection is closed
    //FIXME:: As workaround we use chunked
    response.transfer_encoding_type = TRANSFER_ENCODING_TYPE::CHUNKED;
    response.chunked_status = http::CHUNKED_STATUS::CHUNKED_ENABLED;
  }
  return validation::REQUEST_RESULT::OK;
}

void http_manager::replyError(http::Code code, const std::string &code_string,
                              const std::string &str, Connection &target) {
  char caddr[200];

  if (UNLIKELY(Network::getPeerAddress(target.getFileDescriptor(), caddr,
                                       200) == nullptr)) {
    Logger::LogInfo("Error getting peer address", LOG_DEBUG);
  } else {
    auto request_data_len = std::string_view(target.buffer).find('\r');
    Logger::logmsg(LOG_INFO, "(%lx) e%d %s %.*s from %s",
                   std::this_thread::get_id(), static_cast<int>(code),
                   code_string.data(), request_data_len, target.buffer, caddr);
  }
  auto response_ = http::getHttpResponse(code, code_string, str);
  size_t written = 0;
  IO::IO_RESULT result = IO::IO_RESULT::ERROR;

  do {
    size_t sent = 0;
    if (!target.ssl_connected) {
      result = target.write(response_.c_str() + written,
                            response_.length() - written, sent);
    } else if (target.ssl != nullptr) {
      result = ssl::SSLConnectionManager::handleWrite(
          target, response_.c_str() + written, response_.length() - written,
          written, true);
    }
    if (sent > 0) written += sent;
  } while (result == IO::IO_RESULT::DONE_TRY_AGAIN &&
           written < response_.length());
}

bool http_manager::replyRedirect(HttpStream &stream,
                                 const Backend &redirect_backend) {
  /* 0 - redirect is absolute,
   * 1 - the redirect should include the request path, or
   * 2 if it should use perl dynamic replacement */
  std::string new_url(redirect_backend.backend_config->url);
  auto service = static_cast<Service *>(stream.request.getService());
  switch (redirect_backend.backend_config->redir_req) {
    case 1:
      new_url += std::string(stream.request.path, stream.request.path_length);
      break;
    case 2: {  // Dynamic redirect
      auto buf = std::make_unique<char[]>(MAXBUF);
      std::string request_url(stream.request.path, stream.request.path_length);
      memset(buf.get(), 0, MAXBUF);
      regmatch_t umtch[10];
      char *chptr, *enptr, *srcptr;
      if (regexec(&service->service_config.url->pat, request_url.data(), 10,
                  umtch, 0)) {
        Logger::logmsg(
            LOG_WARNING,
            "URL pattern didn't match in redirdynamic... shouldn't happen %s",
            request_url.data());
      } else {
        chptr = buf.get();
        enptr = buf.get() + MAXBUF - 1;
        *enptr = '\0';
        srcptr =
            const_cast<char *>(redirect_backend.backend_config->url.data());
        for (; *srcptr && chptr < enptr - 1;) {
          if (srcptr[0] == '$' && srcptr[1] == '$') {
            *chptr++ = *srcptr++;
            srcptr++;
          }
          if (srcptr[0] == '$' && isdigit(srcptr[1])) {
            if (chptr + umtch[srcptr[1] - 0x30].rm_eo -
                    umtch[srcptr[1] - 0x30].rm_so >
                enptr - 1)
              break;
            memcpy(
                chptr, request_url.data() + umtch[srcptr[1] - 0x30].rm_so,
                umtch[srcptr[1] - 0x30].rm_eo - umtch[srcptr[1] - 0x30].rm_so);
            chptr +=
                umtch[srcptr[1] - 0x30].rm_eo - umtch[srcptr[1] - 0x30].rm_so;
            srcptr += 2;
            continue;
          }
          *chptr++ = *srcptr++;
        }
        *chptr++ = '\0';
        new_url = buf.get();
      }
      break;
    }
    case 0:
    default:
      break;
  }
  int redirect_code = redirect_backend.backend_config->be_type;
  switch (redirect_backend.backend_config->be_type) {
    case 301:
    case 307:
      break;
    default:
      redirect_code = 302;  // FOUND
      break;
  }
  return replyRedirect(redirect_code, new_url, stream);
}
bool http_manager::replyRedirect(int code, const std::string &url,
                                 HttpStream &stream) {
  auto response_ =
      http::getRedirectResponse(static_cast<http::Code>(code), url);

  IO::IO_RESULT result = IO::IO_RESULT::ERROR;
  size_t sent = 0;
  if (!stream.client_connection.ssl_connected) {
    result = stream.client_connection.write(response_.c_str(),
                                            response_.length(), sent);
  } else if (stream.client_connection.ssl != nullptr) {
    result = ssl::SSLConnectionManager::handleWrite(
        stream.client_connection, response_.c_str(), response_.length(), sent,
        true);
  }

  if (result == IO::IO_RESULT::DONE_TRY_AGAIN && sent < response_.length()) {
    std::strncpy(stream.backend_connection.buffer, response_.data() + sent,
                 response_.size() - sent);
    stream.backend_connection.buffer_size = response_.size() - sent;
    stream.upgrade.pinned_connection = true;
    stream.client_connection.enableWriteEvent();
    return false;
  }
  return true;
}
