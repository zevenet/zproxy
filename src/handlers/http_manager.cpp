//
// Created by abdess on 4/6/19.
//

#include "http_manager.h"
#include "../util/Network.h"

bool http_manager::transferChunked(const Connection &connection, http_parser::HttpData &stream) {
  if (stream.chunked_status != http::CHUNKED_STATUS::CHUNKED_DISABLED) {
    auto pos = std::string(connection.buffer);
    stream.chunked_status =
            isLastChunk(pos) ? http::CHUNKED_STATUS::CHUNKED_LAST_CHUNK : http::CHUNKED_STATUS::CHUNKED_ENABLED;
    return true;
  }
  return false;
}

bool http_manager::isLastChunk(const std::string& data)
{
    return getChunkSize(data)==0;
}

size_t http_manager::getChunkSize(const std::string& data)
{
  auto pos = data.find('\r');
  for (auto c = pos; c > -1; c--) {
    Debug::logmsg(LOG_REMOVE, " 0x%x %c", data[c], data[c]);
  }
//  if (pos < data.size()) {
//    auto hex = data.substr(0, pos);
//    Debug::logmsg(LOG_DEBUG, "RESPONSE:\n %x", data.c_str());
//    int chunk_length = std::stoul(hex.data(), nullptr, 16);
//    return chunk_length;
//  }
  return data[0] == 0x00 ? 0 : data.size();
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

void http_manager::applyCompression(Service *service, HttpStream *stream) {
  http::TRANSFER_ENCODING_TYPE compression_type;
  if (service->service_config.compression_algorithm.empty())
    return;
  /* Check if we have found the accept encoding header in the request but not the transfer encoding in the response. */
  if ((stream->response.chunked_status == CHUNKED_STATUS::CHUNKED_DISABLED) && stream->request.accept_encoding_header) {
    std::string compression_value;
    stream->request.getHeaderValue(http::HTTP_HEADER_NAME::ACCEPT_ENCODING, compression_value);

    /* Check if we accept any of the compression algorithms. */
    size_t initial_pos;
    initial_pos = compression_value.find(service->service_config.compression_algorithm);
    if (initial_pos != std::string::npos) {
      compression_value = service->service_config.compression_algorithm;
      stream->response.addHeader(http::HTTP_HEADER_NAME::TRANSFER_ENCODING, compression_value);
      stream->response.chunked_status = CHUNKED_STATUS::CHUNKED_ENABLED;
      compression_type = http::http_info::compression_types.at(compression_value);

      /* Get the message_uncompressed. */
      std::string message_no_compressed = std::string(stream->response.message, stream->response.message_length);
      /* We are going to do the compression depending on the compression algorithm. */
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


validation::REQUEST_RESULT http_manager::validateRequest(HttpRequest &request, const ListenerConfig & listener_config_) {  //FIXME
  regmatch_t matches[4];

  auto res = ::regexec(&listener_config_.verb, request.getRequestLine().data(), 3, //include validation data package
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
  const auto request_url =
      std::string_view(request.path, request.path_length);
  if (request_url.find("%00") != std::string::npos) {
    return validation::REQUEST_RESULT::URL_CONTAIN_NULL;
  }

  if (listener_config_.has_pat &&
      regexec(&listener_config_.url_pat, request.path, 0, NULL, 0)) {
    return validation::REQUEST_RESULT::BAD_URL;
  }

  // Check reqeuest size .
  if (UNLIKELY(listener_config_.max_req > 0 &&
      request.headers_length > listener_config_.max_req &&
      request.request_method != http::REQUEST_METHOD::RPC_IN_DATA &&
      request.request_method != http::REQUEST_METHOD::RPC_OUT_DATA)) {
    return validation::REQUEST_RESULT::REQUEST_TOO_LARGE;
  }

  // Check for correct headers
  for (auto i = 0; i != request.num_headers; i++) {
    /* maybe header to be removed */
    MATCHER *m;
    for (m = listener_config_.head_off; m; m = m->next) {
      if(::regexec(&m->pat, request.headers[i].name, 0, NULL, 0) == 0){
        request.headers[i].header_off = true;
        break;
      }
    }
    if(request.headers[i].header_off)
      continue;

//      Debug::logmsg(LOG_REMOVE, "\t%.*s",request.headers[i].name_len + request.headers[i].value_len + 2, request.headers[i].name);

    // check header values length
    if (request.headers[i].value_len > MAX_HEADER_VALUE_SIZE)
      return http::validation::REQUEST_RESULT::REQUEST_TOO_LARGE;

    auto header = std::string_view(request.headers[i].name,
                                   request.headers[i].name_len);
    auto header_value = std::string_view(
        request.headers[i].value, request.headers[i].value_len);

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
        case http::HTTP_HEADER_NAME::UPGRADE:request.upgrade_header = true;

          break;
        case http::HTTP_HEADER_NAME::CONNECTION:
          if (http_info::connection_values.count(std::string(header_value)) > 0
              && http_info::connection_values.at(std::string(header_value)) == CONNECTION_VALUES::UPGRADE)
            request.connection_header_upgrade = true;
          break;
        case http::HTTP_HEADER_NAME::ACCEPT_ENCODING:request.accept_encoding_header = true;
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
          continue;
        }
        case http::HTTP_HEADER_NAME::EXPECT : {
          if (header_value == "100-continue") {
            Debug::logmsg(LOG_REMOVE, "Client Expects 100 continue");
          }
          if (listener_config_.ignore100continue)
            request.headers[i].header_off = true;
          break;
        }
        default: continue;
      }

    }
  }
  // waf

  return validation::REQUEST_RESULT::OK;
}

validation::REQUEST_RESULT http_manager::validateResponse(HttpStream &stream,const ListenerConfig & listener_config_) {
  HttpResponse &response = stream.response;
  /* If the response is 100 continue we need to enable chunked transfer. */
  if (response.http_status_code < 200) {
//    stream.response.chunked_status = http::CHUNKED_STATUS::CHUNKED_ENABLED;
//    Debug::logmsg(LOG_DEBUG, "Chunked transfer enabled");
    return validation::REQUEST_RESULT::OK;
  }

  for (auto i = 0; i != response.num_headers; i++) {
    // check header values length

    auto header = std::string_view(response.headers[i].name,
                                   response.headers[i].name_len);
    auto header_value = std::string_view(
        response.headers[i].value, response.headers[i].value_len);

//    Debug::logmsg(LOG_REMOVE, "\t%.*s",response.headers[i].name_len + response.headers[i].value_len + 2, response.headers[i].name);
    auto it = http::http_info::headers_names.find(header);
    if (it != http::http_info::headers_names.end()) {
      const auto header_name = it->second;
      switch (header_name) {
      case http::HTTP_HEADER_NAME::CONTENT_LENGTH: {
        stream.response.content_length =
            static_cast<size_t>(std::atoi(header_value.data()));
        if ((stream.response.content_length - stream.response.message_length) > 0)
          stream.response.message_bytes_left =
              stream.response.content_length - stream.response.message_length;
        continue;
      }
      case http::HTTP_HEADER_NAME::LOCATION: {
        // Rewrite location
        std::string location_header_value(
            response.headers[i].value, response.headers[i].value_len);
        if (listener_config_.rewr_loc == 0) continue;
        regmatch_t matches[4];

        if (regexec(&Config::LOCATION, location_header_value.data(), 4, matches, 0)) {
          continue;
        }

        std::string proto(location_header_value.data() + matches[1].rm_so, matches[1].rm_eo - matches[1].rm_so);
        std::string host(location_header_value.data() + matches[2].rm_so, matches[2].rm_eo - matches[2].rm_so);

//        if (location_header_value[matches[3].rm_so] == '/') {
//          matches[3].rm_so++;
//        }
        std::string path(location_header_value.data() + matches[3].rm_so, matches[3].rm_eo - matches[3].rm_so);

        char ip[100]{'\0'};
        if (!Network::HostnameToIp(host.data(), ip)) {
          Debug::logmsg(LOG_NOTICE, "Couldn't get host ip");
          continue;
        }
        std::string_view host_ip(ip);
        if (host_ip == listener_config_.address ||
            host_ip == stream.backend_connection.getBackend()->address) {
          std::string header_value_ = listener_config_.ctx != nullptr ? "https://" : "http://";
          header_value_ += host;
          header_value_ += ":";
          header_value_ += std::to_string(listener_config_.port);
//          header_value_ += path;
          response.addHeader(http::HTTP_HEADER_NAME::LOCATION,
                             header_value_);
          response.addHeader(http::HTTP_HEADER_NAME::CONTENT_LOCATION,
                             path);
          response.headers[i].header_off = true;
        }
        break;
      }
      case http::HTTP_HEADER_NAME::STRICT_TRANSPORT_SECURITY:
        if (static_cast<Service*>(stream.request.getService())->service_config.sts > 0)
          response.headers[i].header_off = true;
        break;

        case http::HTTP_HEADER_NAME::TRANSFER_ENCODING:response.chunked_status = http::CHUNKED_STATUS::CHUNKED_ENABLED;
      default:continue;
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


