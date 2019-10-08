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
#include "../../src/cache/HttpCacheManager.h"
#include "../../src/http/http_stream.h"
#include "../../src/handlers/http_manager.h"
#include <string>

namespace cache_helper {
/*
 *
 * Functions created in order to use some other functions out of the scope of these tests
 *
 */
std::string createResponseBuffer( string*  c_control_values)
{
    std::string date = *timeHelper::strTimeNow();
    std::string c_control_header;
    if ( c_control_values != nullptr && c_control_values->length() > 0 )
    {
        c_control_header = "Cache-Control: ";
        c_control_header.append(*c_control_values);
        c_control_header.append("\r\n");
    }
    std::string response_buffer = "HTTP/1.1 200 OK\r\n"
             "Date: ";
    response_buffer += date.data();
    response_buffer += "\r\n";
    if ( c_control_header.length() != 0 )
        response_buffer += c_control_header.data();
    response_buffer += "Server: Apache/2.4.10 (Debian)\r\n"
             "Last-Modified: Wed, 24 Jul 2019 11:33:00 GMT\r\n"
             "ETag: \"5d-58e6babe49f24\"\r\n"
             "Accept-Ranges: bytes\r\n"
             "Content-Length: 93\r\n"
             "Vary: Accept-Encoding\r\n"
             "Content-Type: text/html\r\n"
             "\r\n"
                 "<html>\n"
                 "<head>\n"
                 "<title>hello world page</title>\n"
                 "</head>\n"
                 "<body>\n"
                 "<p>Hello world!\n"
                 "</body>\n"
                 "</html>\n";
return response_buffer;
}
void createResponse ( std::string * resp_buffer, HttpStream * stream){
    ListenerConfig listener_config_;
    size_t parsed = 0;
    stream->response.buffer = resp_buffer->data();
    stream->response.buffer_size = resp_buffer->size();
    //RESET c_opt
    bool no_cache = false;
    bool transform = true;
    bool cacheable = true; // Set by the request with no-store
    bool revalidate = false;
    int max_age = -1;

    stream->response.c_opt.max_age = -1;
    stream->response.c_opt.cacheable = true;
    stream->response.c_opt.revalidate = false;
    stream->response.c_opt.no_cache = false;
    stream->response.cache_control = false;
    stream->response.cached = false;
    stream->response.parseResponse(*resp_buffer, &parsed);
    auto result = http_manager::validateResponse(*stream, listener_config_);
}
void createRequest ( std::string * req_buffer, HttpStream * stream){
    ListenerConfig listener_config_;
    size_t parsed = 0;
    const char *xhttp =
        "^(GET|POST|HEAD|PUT|PATCH|DELETE|LOCK|UNLOCK|PROPFIND|PROPPATCH|SEARCH|"
        "MKCOL|MKCALENDAR|MOVE|COPY|OPTIONS|TRACE|MKACTIVITY|CHECKOUT|MERGE|"
        "REPORT|SUBSCRIBE|UNSUBSCRIBE|BPROPPATCH|POLL|BMOVE|BCOPY|BDELETE|"
        "BPROPFIND|NOTIFY|CONNECT|RPC_IN_DATA|RPC_OUT_DATA) ([^ ]+) HTTP/1.[01].*$";
    regcomp(&listener_config_.verb, xhttp, REG_ICASE | REG_NEWLINE | REG_EXTENDED);
    regcomp(&listener_config_.url_pat, ".*",REG_NEWLINE | REG_EXTENDED |  REG_ICASE );
    listener_config_.head_off = nullptr;

    stream->request.buffer = req_buffer->data();
    stream->request.buffer_size = req_buffer->size();
    stream->request.http_message = req_buffer->data();
    stream->request.http_message_length = req_buffer->size();
    //RESET c_opt
    stream->request.c_opt.max_age = -1;
    stream->request.c_opt.max_stale = -1;
    stream->request.c_opt.min_fresh = -1;
    stream->request.c_opt.only_if_cached = false;
    stream->request.c_opt.no_store = false;
    stream->request.c_opt.no_cache = false;
    stream->request.cache_control = false;
    stream->request.parseRequest(*req_buffer, &parsed);

    auto result = http_manager::validateRequest(stream->request,listener_config_);
    regfree(&listener_config_.verb);
    regfree(&listener_config_.url_pat);
}
std::string createRequestBuffer ( string * c_control_values )
{
    std::string c_control_header;
    if ( c_control_values != nullptr && c_control_values->length() > 0 )
    {
        c_control_header = "Cache-Control: ";
        c_control_header.append(*c_control_values);
        c_control_header.append("\r\n");
    }

    string req_buffer ("GET /index.html HTTP/1.1\r\nHost: 192.168.100.147\r\nUser-Agent: \343\201\262\343/1.0\r\n");
    if ( c_control_header.length() != 0 )
        req_buffer.append(c_control_header);

    req_buffer.append("\r\n");
return req_buffer;
}
}
