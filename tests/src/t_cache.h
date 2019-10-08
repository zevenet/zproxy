#pragma once

#include "../../src/stream/stream_manager.h"
#include "../lib/gtest/googletest/include/gtest/gtest.h"
#include "cache_helpers.h"
#include "gtest/gtest.h"

/*
 * Tests start
 */
using namespace cache_helper;

TEST(CacheTest, ReadCacheConfigFileTest ) {
    char *argv[] = {"../bin/zproxy", "-f",
                    "/home/developer/zproxy/tests/cache_http.cfg"};
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
 c_manager.cacheInit(&cache_pattern, cache_timeout, "myService", 204800, 5, "zproxyTest", "/tmp/prueba/cache_ramfs","/tmp/prueba/cache_disk");
 ASSERT_FALSE( c_manager.cache_enabled );
 c_manager.cacheInit(&cache_pattern, cache_timeout, "myService", 204800, 5, "zproxyTest", "/tmp/prueba/cache_ramfs","/tmp/prueba/cache_disk");
 ASSERT_FALSE( c_manager.cache_enabled );
 c_manager.cacheInit(&cache_pattern, 0, "myService", 204800, 5, "zproxyTest", "/tmp/prueba/cache_ramfs","/tmp/prueba/cache_disk");
 ASSERT_FALSE( c_manager.cache_enabled );
 regcomp(&cache_pattern,".*html|.*png",REG_ICASE | REG_NEWLINE | REG_EXTENDED);
 c_manager.cacheInit(&cache_pattern, cache_timeout, "myService", 204800, 5, "zproxyTest", "/tmp/prueba/cache_ramfs","/tmp/prueba/cache_disk");
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
    c_manager.cacheInit(&cache_patt, cache_timeout, "myService", 204800, 5, "zproxyTest", "/tmp/prueba/cache_ramfs","/tmp/prueba/cache_disk");

    //Parse the request
    auto req_ret = stream.request.parseRequest(request_buffer, &parsed);
    ASSERT_TRUE( req_ret == http_parser::PARSE_RESULT::SUCCESS );
    //Parse the response
    auto resp_ret = stream.response.parseResponse(response_buffer, &parsed);
    ASSERT_TRUE( resp_ret == http_parser::PARSE_RESULT::SUCCESS );
    //Check that isCached returns false while it hasn't been cached yet
    c_manager.validateCacheRequest(stream.request);
    c_manager.validateCacheResponse(stream.response);
    ASSERT_FALSE ( c_manager.getCacheObject(stream.request) != nullptr );
    std::string buffer;
    HttpResponse cached_response;
    //Store and check that is stored
    c_manager.handleResponse(stream.response,stream.request);
    ASSERT_TRUE (c_manager.getCacheObject(stream.request) != nullptr );
    //Check that the buffer stored is the same as the original
    ASSERT_TRUE( c_manager.getResponseFromCache(stream.request,cached_response,buffer) == 0 );
    EXPECT_EQ ( buffer , response_buffer ); //TODO:: check if cmp is correct
    //Check that the timeout is
    ASSERT_TRUE ( c_manager.getCacheObject(stream.request)->max_age == cache_timeout );
}
//Check that when no timeout set, uses the heuristic timeout
TEST(CacheTest, HeuristicTest){
    HttpCacheManager c_manager;
    HttpStream stream;
    regex_t cache_patt;

    regcomp(&cache_patt,".*html|.*png",REG_ICASE | REG_NEWLINE | REG_EXTENDED);
    c_manager.cacheInit(&cache_patt,-1, "myService", 204800, 5, "zproxyTest", "/tmp/prueba/cache_ramfs","/tmp/prueba/cache_disk");
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
    c_manager.cacheInit(&cache_patt,cache_timeout, "myService", 204800, 5, "zproxyTest", "/tmp/prueba/cache_ramfs","/tmp/prueba/cache_disk");

    string req_buffer = createRequestBuffer(nullptr);
    string resp_buffer = createResponseBuffer(nullptr);
    createRequest(&req_buffer, &stream);
    createResponse(&resp_buffer, &stream);

    c_manager.handleResponse(stream.response,stream.request);
    auto c_object = c_manager.getCacheObject(stream.request);
    ASSERT_TRUE( c_object->isFresh() );
    ASSERT_FALSE( c_object->staled );
    sleep(cache_timeout+1);
    c_object = c_manager.getCacheObject(stream.request);
    ASSERT_FALSE( c_object->isFresh() );
    ASSERT_TRUE( c_object->staled );

    //Refresh the response
    resp_buffer = createResponseBuffer(nullptr);
    createResponse(&resp_buffer, &stream);

    c_manager.handleResponse(stream.response,stream.request);
    //Check if refreshed
    c_object = c_manager.getCacheObject(stream.request);
    ASSERT_TRUE( c_object->isFresh() );
    ASSERT_FALSE( c_object->staled );
    sleep(cache_timeout+1);
    c_object = c_manager.getCacheObject(stream.request);
    ASSERT_FALSE( c_object->isFresh() );
    ASSERT_TRUE( c_manager.getCacheObject(stream.request)->staled );
}

TEST(CacheTest, CanBeServedTest){
    HttpCacheManager c_manager;
    HttpStream stream;
    regex_t cache_patt;
    int cache_timeout = 5;
    regcomp(&cache_patt,".*html|.*png",REG_ICASE | REG_NEWLINE | REG_EXTENDED);
    c_manager.cacheInit(&cache_patt,cache_timeout, "myService", 204800, 5, "zproxyTest", "/tmp/prueba/cache_ramfs","/tmp/prueba/cache_disk");

    string req_buffer = createRequestBuffer(nullptr);
    string resp_buffer = createResponseBuffer(nullptr);
    createRequest(&req_buffer, &stream);
    createResponse(&resp_buffer, &stream);

    c_manager.handleResponse(stream.response, stream.request);

    string c_control("no-cache");
    req_buffer = createRequestBuffer(&c_control);
    createRequest(&req_buffer, &stream);
    auto c_object = c_manager.getCacheObject(stream.request);
    ASSERT_TRUE(c_object->isFresh());
    ASSERT_FALSE(c_manager.canBeServedFromCache(stream.request));
}

TEST(CacheTest, CcontrolNoCacheTest){
    HttpCacheManager c_manager;
    HttpStream stream;
    regex_t cache_patt;
    int cache_timeout = 5;
    regcomp(&cache_patt,".*html|.*png",REG_ICASE | REG_NEWLINE | REG_EXTENDED);
    c_manager.cacheInit(&cache_patt,cache_timeout, "myService", 204800, 5, "zproxyTest", "/tmp/prueba/cache_ramfs","/tmp/prueba/cache_disk");
    //In response:
    string c_control_values = "no-cache";
    string req_buffer = createRequestBuffer(nullptr);
    string resp_buffer = createResponseBuffer(&c_control_values);
    createRequest(&req_buffer, &stream);
    createResponse(&resp_buffer, &stream);

    c_manager.handleResponse(stream.response, stream.request);
    auto c_object = c_manager.getCacheObject(stream.request);
    ASSERT_FALSE( c_object != nullptr );
    //Not cached, return false
    ASSERT_FALSE( c_object->isFresh());

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
    c_object = c_manager.getCacheObject(stream.request);
    ASSERT_TRUE( c_object  != nullptr);
    ASSERT_TRUE( c_object->isFresh());
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
    c_manager.cacheInit(&cache_patt,cache_timeout, "myService", 204800, 5, "zproxyTest", "/tmp/prueba/cache_ramfs","/tmp/prueba/cache_disk");
    //In response:
    string c_control_values = "no-store";
    string req_buffer = createRequestBuffer(nullptr);
    string resp_buffer = createResponseBuffer(&c_control_values);
    createRequest(&req_buffer, &stream);
    createResponse(&resp_buffer, &stream);
    //Check if we can store
    c_manager.handleResponse(stream.response, stream.request);
    ASSERT_FALSE( c_manager.getCacheObject(stream.request) != nullptr);

    //In request:
    c_control_values = "no-store";
    req_buffer = createRequestBuffer(&c_control_values);
    resp_buffer = createResponseBuffer(nullptr);
    createRequest(&req_buffer, &stream);
    createResponse(&resp_buffer, &stream);
    //Check if we can store
    c_manager.handleResponse(stream.response, stream.request);
    ASSERT_FALSE( c_manager.getCacheObject(stream.request) != nullptr);

}

TEST(CacheTest, CcontrolMaxAgeTest){
    HttpCacheManager c_manager;
    HttpStream stream;
    regex_t cache_patt;
    int cache_timeout = 5;
    regcomp(&cache_patt,".*html|.*png",REG_ICASE | REG_NEWLINE | REG_EXTENDED);
    c_manager.cacheInit(&cache_patt,cache_timeout, "myService", 204800, 5, "zproxyTest", "/tmp/prueba/cache_ramfs","/tmp/prueba/cache_disk");
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
    c_manager.cacheInit(&cache_patt,cache_timeout, "myService", 204800, 5, "zproxyTest", "/tmp/prueba/cache_ramfs","/tmp/prueba/cache_disk");
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
    c_manager.cacheInit(&cache_patt,cache_timeout,"myService", 204800, 5, "zproxyTest", "/tmp/prueba/cache_ramfs","/tmp/prueba/cache_disk");
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
    c_manager.cacheInit(&cache_patt,cache_timeout,"myService", 204800, 5, "zproxyTest", "/tmp/prueba/cache_ramfs","/tmp/prueba/cache_disk" );
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
