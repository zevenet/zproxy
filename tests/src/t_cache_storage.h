#pragma once

#include "../../src/stream/stream_manager.h"
#include "../lib/gtest/googletest/include/gtest/gtest.h"
#include "gtest/gtest.h"
#include <filesystem>
#include <regex>
#include <string>

TEST(CacheTestStorage, InitializationTests ) {
    std::string svc("myService");
    std::string f_name ("zproxyTest");
    HttpCacheManager * c_manager = new HttpCacheManager;
    regex_t cache_re;
    regcomp(&cache_re,".*html|.*css", REG_ICASE | REG_NEWLINE | REG_EXTENDED);
    c_manager-> cacheInit(&cache_re, 30, svc, 2048000, 5, f_name, "/tmp/prueba/cache_ramfs","/tmp/prueba/cache_disk");
    RamICacheStorage * ram_storage = RamfsCacheStorage::getInstance();
    DiskICacheStorage * disk_storage = DiskCacheStorage::getInstance();
    namespace fs = std::filesystem;
    auto path = ram_storage->mount_path;
    path += "/";
    path += svc;
    ASSERT_TRUE(fs::exists(path));
    path = disk_storage->mount_path;
    path += "/";
    path += svc;
    ASSERT_TRUE(fs::exists(path));

    delete c_manager;
    path = ram_storage->mount_path;
    path += "/";
    path += svc;
    bool status = fs::exists(path);
    ASSERT_FALSE(status);
    path = disk_storage->mount_path;
    path += "/";
    path += svc;
    ASSERT_FALSE(fs::exists(path));
}
