#pragma once

#include "../../src/cache/HttpCacheManager.h"
#include "../lib/gtest/googletest/include/gtest/gtest.h"
#include "gtest/gtest.h"
#include "../../src/service/Service.h"
#include "../../src/http/http_parser.h"
#include <string>
#include "../../src/config/config.h"
#include "../../src/debug/Debug.h"
#include "../../src/util/utils.h"
#include "../../src/handlers/http_manager.h"
#include "../../src/stream/StreamManager.h"

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

/*
 * Tests start
 */

TEST(CacheTest, ReadCacheConfigFileTest ) {
    char *argv[] = {"../bin/zhttp", "-f",
                    "/home/developer/zhttp/tests/cache_http.cfg"};
    int argc = 3;
    regmatch_t matches[1];
    Config config;
    config.parseConfig(argc, argv);
    // auto fname = config.f_name;
    auto backend_config = config.listeners;
    auto services = backend_config->services;

    ASSERT_TRUE( services->cache_content.re_pcre != nullptr );
    ASSERT_TRUE(!regexec(&services->cache_content,"/index.html",1,matches,0));
    ASSERT_TRUE(!regexec(&services->cache_content,"/root/image.png",1,matches,0));
    ASSERT_TRUE( services->cache_timeout == 10);
}

TEST(CacheTest, CacheInitializationTest ) {
 int cache_timeout = 10;
 regex_t cache_pattern;
 HttpCacheManager c_manager;
 cache_pattern.re_pcre = nullptr;
 c_manager.cacheInit(&cache_pattern, cache_timeout, "myService", 204800, 5, "zhttpTest");
 ASSERT_FALSE( c_manager.cache_enabled );
 c_manager.cacheInit(&cache_pattern, cache_timeout, "myService", 204800, 5, "zhttpTest");
 ASSERT_FALSE( c_manager.cache_enabled );
 c_manager.cacheInit(&cache_pattern, 0, "myService", 204800, 5, "zhttpTest");
 ASSERT_FALSE( c_manager.cache_enabled );
 regcomp(&cache_pattern,".*html|.*png",REG_ICASE | REG_NEWLINE | REG_EXTENDED);
 c_manager.cacheInit(&cache_pattern, cache_timeout, "myService", 204800, 5, "zhttpTest");
 ASSERT_TRUE( c_manager.cache_enabled );
 ASSERT_TRUE( c_manager.getCacheTimeout() == cache_timeout );
}

TEST(CacheTest, StoreResponseTest ) {
  //
    HttpCacheManager c_manager;
    HttpStream stream;
    regex_t cache_patt;
    int cache_timeout = 4;
    size_t parsed = 0;
    std::string response_buffer = createResponseBuffer(nullptr);
    std::string request_buffer = createRequestBuffer(nullptr);
    createRequest(&request_buffer, &stream);
    createResponse(&response_buffer, &stream);
    //Init the cache
    regcomp(&cache_patt,".*html|.*png",REG_ICASE | REG_NEWLINE | REG_EXTENDED);
    c_manager.cacheInit(&cache_patt, cache_timeout, "myService", 204800, 5, "zhttpTest");

    //Parse the request
    auto req_ret = stream.request.parseRequest(request_buffer, &parsed);
    ASSERT_TRUE( req_ret == http_parser::PARSE_RESULT::SUCCESS );
    //Parse the response
    auto resp_ret = stream.response.parseResponse(response_buffer, &parsed);
    ASSERT_TRUE( resp_ret == http_parser::PARSE_RESULT::SUCCESS );
    //Check that isCached returns false while it hasn't been cached yet
    ASSERT_FALSE ( c_manager.isCached(stream.request) );
    std::string buffer;
    HttpResponse cached_response;
    //Store and check that is stored
    c_manager.handleResponse(stream.response,stream.request);
    ASSERT_TRUE ( c_manager.isCached(stream.request) );
    //Check that the buffer stored is the same as the original
    EXPECT_EQ ( c_manager.getResponseFromCache(stream.request,cached_response,buffer), response_buffer );
    //Check that the timeout is
    ASSERT_TRUE ( c_manager.getCacheObject(stream.request)->max_age == cache_timeout );
}
//Check that when no timeout set, uses the heuristic timeout
TEST(CacheTest, HeuristicTest){
    HttpCacheManager c_manager;
    HttpStream stream;
    regex_t cache_patt;

    regcomp(&cache_patt,".*html|.*png",REG_ICASE | REG_NEWLINE | REG_EXTENDED);
    c_manager.cacheInit(&cache_patt,-1, "myService", 204800, 5, "zhttpTest");
    string req_buffer = createRequestBuffer(nullptr);
    string resp_buffer = createResponseBuffer(nullptr);
    createRequest(&req_buffer, &stream);
    createResponse(&resp_buffer, &stream);

    time_t heuristic_value = (timeHelper::gmtTimeNow() - stream.response.last_mod) * 0.1;

    c_manager.handleResponse(stream.response, stream.request);

    ASSERT_TRUE ( heuristic_value == c_manager.getCacheObject(stream.request)->max_age );
}
//Check if a response is correctly staled by isFresh() when reached its timeout
TEST(CacheTest, StalingTest){
    HttpCacheManager c_manager;
    HttpStream stream;
    regex_t cache_patt;
    int cache_timeout = 2;
    regcomp(&cache_patt,".*html|.*png",REG_ICASE | REG_NEWLINE | REG_EXTENDED);
    c_manager.cacheInit(&cache_patt,cache_timeout, "myService", 204800, 5, "zhttpTest");

    string req_buffer = createRequestBuffer(nullptr);
    string resp_buffer = createResponseBuffer(nullptr);
    createRequest(&req_buffer, &stream);
    createResponse(&resp_buffer, &stream);

    c_manager.handleResponse(stream.response,stream.request);
    ASSERT_TRUE( c_manager.isFresh(stream.request) );
    ASSERT_FALSE( c_manager.getCacheObject(stream.request)->staled );
    sleep(cache_timeout+1);
    ASSERT_FALSE( c_manager.isFresh(stream.request) );
    ASSERT_TRUE( c_manager.getCacheObject(stream.request)->staled );

    //Refresh the response
    resp_buffer = createResponseBuffer(nullptr);
    createResponse(&resp_buffer, &stream);

    c_manager.handleResponse(stream.response,stream.request);
    //Check if refreshed
    ASSERT_TRUE( c_manager.isFresh(stream.request) );
    ASSERT_FALSE( c_manager.getCacheObject(stream.request)->staled );
    sleep(cache_timeout+1);
    ASSERT_FALSE( c_manager.isFresh(stream.request) );
    ASSERT_TRUE( c_manager.getCacheObject(stream.request)->staled );
}

TEST(CacheTest, CanBeServedTest){
    HttpCacheManager c_manager;
    HttpStream stream;
    regex_t cache_patt;
    int cache_timeout = 5;
    regcomp(&cache_patt,".*html|.*png",REG_ICASE | REG_NEWLINE | REG_EXTENDED);
    c_manager.cacheInit(&cache_patt,cache_timeout, "myService", 204800, 5, "zhttpTest");

    string req_buffer = createRequestBuffer(nullptr);
    string resp_buffer = createResponseBuffer(nullptr);
    createRequest(&req_buffer, &stream);
    createResponse(&resp_buffer, &stream);

    c_manager.handleResponse(stream.response, stream.request);

    string c_control("no-cache");
    req_buffer = createRequestBuffer(&c_control);
    createRequest(&req_buffer, &stream);
    ASSERT_TRUE(c_manager.isFresh(stream.request));
    ASSERT_FALSE(c_manager.canBeServedFromCache(stream.request));
}

TEST(CacheTest, CcontrolNoCacheTest){
    HttpCacheManager c_manager;
    HttpStream stream;
    regex_t cache_patt;
    int cache_timeout = 5;
    regcomp(&cache_patt,".*html|.*png",REG_ICASE | REG_NEWLINE | REG_EXTENDED);
    c_manager.cacheInit(&cache_patt,cache_timeout, "myService", 204800, 5, "zhttpTest");
    //In response:
    string c_control_values = "no-cache";
    string req_buffer = createRequestBuffer(nullptr);
    string resp_buffer = createResponseBuffer(&c_control_values);
    createRequest(&req_buffer, &stream);
    createResponse(&resp_buffer, &stream);

    c_manager.handleResponse(stream.response, stream.request);

    ASSERT_FALSE( c_manager.isCached(stream.request));
    //Not cached, return false
    ASSERT_FALSE( c_manager.isFresh(stream.request));

    //In request:
    //  -Not cached: We must cache the response
    //  -Cached: can't use cached content to satisfy the request, the cached content must be refreshed by the response
    c_control_values = "no-cache";
    req_buffer = createRequestBuffer(&c_control_values);
    resp_buffer = createResponseBuffer(nullptr);
    createRequest(&req_buffer, &stream);
    createResponse(&resp_buffer, &stream);
    c_manager.handleResponse(stream.response, stream.request);
    ASSERT_FALSE( c_manager.canBeServedFromCache(stream.request));
    ASSERT_TRUE( c_manager.isCached(stream.request));
    ASSERT_TRUE( c_manager.isFresh(stream.request));
    time_t previous_time = c_manager.getCacheObject(stream.request)->date;
    //Update response timers
    //Adding a delay between responses, to ensure that is refreshed
    sleep(1);
    ASSERT_FALSE( c_manager.canBeServedFromCache(stream.request));
    resp_buffer = createResponseBuffer(nullptr);
    createResponse(&resp_buffer, &stream);
    c_manager.handleResponse(stream.response, stream.request);
    ASSERT_FALSE( c_manager.canBeServedFromCache(stream.request));
    ASSERT_TRUE( previous_time < c_manager.getCacheObject(stream.request)->date );
    //The content is refreshed and it is not served the stored content
}

TEST(CacheTest, CcontrolNoStoreTest){
    HttpCacheManager c_manager;
    HttpStream stream;
    regex_t cache_patt;
    int cache_timeout = 5;
    regcomp(&cache_patt,".*html|.*png",REG_ICASE | REG_NEWLINE | REG_EXTENDED);
    c_manager.cacheInit(&cache_patt,cache_timeout, "myService", 204800, 5, "zhttpTest");
    //In response:
    string c_control_values = "no-store";
    string req_buffer = createRequestBuffer(nullptr);
    string resp_buffer = createResponseBuffer(&c_control_values);
    createRequest(&req_buffer, &stream);
    createResponse(&resp_buffer, &stream);
    //Check if we can store
    c_manager.handleResponse(stream.response, stream.request);
    ASSERT_FALSE( c_manager.isCached(stream.request));

    //In request:
    c_control_values = "no-store";
    req_buffer = createRequestBuffer(&c_control_values);
    resp_buffer = createResponseBuffer(nullptr);
    createRequest(&req_buffer, &stream);
    createResponse(&resp_buffer, &stream);
    //Check if we can store
    c_manager.handleResponse(stream.response, stream.request);
    ASSERT_FALSE( c_manager.isCached(stream.request));

}

TEST(CacheTest, CcontrolMaxAgeTest){
    HttpCacheManager c_manager;
    HttpStream stream;
    regex_t cache_patt;
    int cache_timeout = 5;
    regcomp(&cache_patt,".*html|.*png",REG_ICASE | REG_NEWLINE | REG_EXTENDED);
    c_manager.cacheInit(&cache_patt,cache_timeout, "myService", 204800, 5, "zhttpTest");
    //In response:
    string c_control_values = "max-age=4";
    string req_buffer = createRequestBuffer(nullptr);
    string resp_buffer = createResponseBuffer(&c_control_values);
    createRequest(&req_buffer, &stream);
    createResponse(&resp_buffer, &stream);
    //Check what is the max-age value
    c_manager.handleResponse(stream.response, stream.request);
    ASSERT_TRUE( c_manager.getCacheObject(stream.request)->max_age == 4 );
    //Check value higher that the value set on the config file, must use the most restrictive
    c_control_values = "max-age=10";
    resp_buffer = createResponseBuffer(&c_control_values);
    createResponse(&resp_buffer, &stream);
    //Check what is the max-age value
    c_manager.handleResponse(stream.response, stream.request);
    ASSERT_FALSE( c_manager.getCacheObject(stream.request)->max_age == 10 );

    //In request
    c_control_values = "max-age=2";
    req_buffer = createRequestBuffer(&c_control_values);
    resp_buffer = createResponseBuffer(nullptr);
    createResponse(&resp_buffer, &stream);
    createRequest(&req_buffer, &stream);
    //Check what is the max-age value
    c_manager.handleResponse(stream.response, stream.request);
    ASSERT_TRUE( c_manager.getCacheObject(stream.request)->max_age == 5 );
    ASSERT_TRUE(c_manager.canBeServedFromCache(stream.request));
    sleep(3);
    ASSERT_FALSE(c_manager.canBeServedFromCache(stream.request));

}

TEST(CacheTest, CcontrolSMaxAgeTest){
    HttpCacheManager c_manager;
    HttpStream stream;
    regex_t cache_patt;
    int cache_timeout = 5;
    regcomp(&cache_patt,".*html|.*png",REG_ICASE | REG_NEWLINE | REG_EXTENDED);
    c_manager.cacheInit(&cache_patt,cache_timeout, "myService", 204800, 5, "zhttpTest");
    //In response:
    string c_control_values = "max-age=3, s-maxage=4";
    string req_buffer = createRequestBuffer(nullptr);
    string resp_buffer = createResponseBuffer(&c_control_values);
    createRequest(&req_buffer, &stream);
    createResponse(&resp_buffer, &stream);
    //Check what is the max-age value
    c_manager.handleResponse(stream.response, stream.request);
    ASSERT_TRUE( c_manager.getCacheObject(stream.request)->max_age == 4 );
}

TEST(CacheTest, CcontrolSMinFreshTest){
    HttpCacheManager c_manager;
    HttpStream stream;
    regex_t cache_patt;
    int cache_timeout = 10;
    regcomp(&cache_patt,".*html|.*png",REG_ICASE | REG_NEWLINE | REG_EXTENDED);
    c_manager.cacheInit(&cache_patt,cache_timeout,"myService", 204800, 5, "zhttpTest" );
    //In response:
    string c_control_values = "min-fresh=5";
    string req_buffer = createRequestBuffer(&c_control_values);
    string resp_buffer = createResponseBuffer(nullptr);
    createRequest(&req_buffer, &stream);
    createResponse(&resp_buffer, &stream);
    c_manager.handleResponse(stream.response, stream.request);
    ASSERT_TRUE( stream.request.c_opt.min_fresh == 5 );
    ASSERT_TRUE( c_manager.canBeServedFromCache(stream.request));
    sleep( 6);
    ASSERT_FALSE( c_manager.canBeServedFromCache(stream.request));
}
TEST(CacheTest, CcontrolSMaxStaleTest){
    HttpCacheManager c_manager;
    HttpStream stream;
    regex_t cache_patt;
    int cache_timeout = 10;
    regcomp(&cache_patt,".*html|.*png",REG_ICASE | REG_NEWLINE | REG_EXTENDED);
    c_manager.cacheInit(&cache_patt,cache_timeout,"myService", 204800, 5, "zhttpTest" );
    //In response:
    string c_control_values = "max-stale=5";
    string req_buffer = createRequestBuffer(&c_control_values);
    string resp_buffer = createResponseBuffer(nullptr);
    createRequest(&req_buffer, &stream);
    createResponse(&resp_buffer, &stream);
    c_manager.handleResponse(stream.response, stream.request);
    ASSERT_TRUE( stream.request.c_opt.max_stale == 5 );
    ASSERT_TRUE( c_manager.canBeServedFromCache(stream.request));
    ASSERT_FALSE( c_manager.getCacheObject(stream.request)->staled);
    sleep( 11);
    ASSERT_TRUE( c_manager.canBeServedFromCache(stream.request));
    ASSERT_TRUE( c_manager.getCacheObject(stream.request)->staled);
    sleep( 3);
    ASSERT_TRUE( c_manager.canBeServedFromCache(stream.request));
    ASSERT_TRUE( c_manager.getCacheObject(stream.request)->staled);
    sleep( 5);
    ASSERT_FALSE( c_manager.canBeServedFromCache(stream.request));
    ASSERT_TRUE( c_manager.getCacheObject(stream.request)->staled);
}
