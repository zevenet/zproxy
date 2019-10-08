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
#include "ram_cache_storage.h"

// Ram Static variables definitions
RamICacheStorage *RamICacheStorage::instance = nullptr;

RamICacheStorage *RamICacheStorage::getInstance() {
  if (instance == nullptr) {
#ifdef CACHE_STORAGE_STDMAP
    instance = new StdmapCacheStorage();
#elif MEMCACHED_ENABLED
    instance = new MemcachedStorage();
#else
    instance = new RamfsCacheStorage();
#endif
  }
  return instance;
}
// FIXME: svc is not used in initcachestorage
st::STORAGE_STATUS RamfsCacheStorage::initCacheStorage(
    size_t m_size, double st_threshold, const std::string &svc,
    const std::string &m_point) {
  st::STORAGE_STATUS ret = st::STORAGE_STATUS::SUCCESS;
  if (initialized) return st::STORAGE_STATUS::ALREADY_INIT;

  // Ensure that the size is always set
  if (m_size <= 0)
    m_size = MAX_STORAGE_SIZE

        // Create directory, if fails, and it's not because the folder is
        // already created, just return an error
        if (mkdir(m_point.data(), 0777) == -1) {
      if (errno == EEXIST) {
        initialized = true;
        max_size = m_size;
        mount_path = m_point.data();
        cache_thr = st_threshold;
        // TODO: Recover from here
        return st::STORAGE_STATUS::MPOINT_ALREADY_EXISTS;
      } else
        return st::STORAGE_STATUS::MKDIR_ERROR;
    }
  mount_path = m_point.data();

  // try to mount the RAMFS filesystem, return MOUNT_ERROR if failed
  if (mount(nullptr, mount_path.data(), "ramfs", 0, "mode=rw,uid=0")) {
    printf("Error trying to mount the RAMFS filesystem in the path %s",
           mount_path.data());
    return st::STORAGE_STATUS::MOUNT_ERROR;
  }
  current_size = 0;
  max_size = m_size;
  cache_thr = st_threshold;

  initialized = true;

  return ret;
}
// Create the service folder
st::STORAGE_STATUS RamfsCacheStorage::initServiceStorage(
    const std::string &svc) {
  if (!initialized) return st::STORAGE_STATUS::NOT_INIT;
  auto path = mount_path;
  path.append("/");
  path.append(svc);
  if (mkdir(path.data(), 0777) == -1) {
    if (errno == EEXIST)
      return st::STORAGE_STATUS::MPOINT_ALREADY_EXISTS;
    else {
      Debug::logmsg(LOG_ERR, "Error :  %s", std::strerror(errno));
      return st::STORAGE_STATUS::MKDIR_ERROR;
    }
  }
  return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_TYPE RamfsCacheStorage::getStorageType() {
  return st::STORAGE_TYPE::RAMFS;
};
st::STORAGE_STATUS RamfsCacheStorage::getFromStorage(
    const std::string &rel_path, std::string &out_buffer) {
  // We have the file_path created as follows: /mount_point/svc1/hashed_url
  string file_path(mount_path);
  file_path.append(string("/"));
  file_path.append(rel_path);

  std::ifstream in_stream(file_path.data());

  if (!in_stream.is_open()) return st::STORAGE_STATUS::OPEN_ERROR;

  std::stringstream buffer;
  buffer << in_stream.rdbuf();
  out_buffer = buffer.str();
  return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS RamfsCacheStorage::putInStorage(const std::string &rel_path,
                                                   std::string_view buffer,
                                                   size_t response_size) {
  if (!initialized) return st::STORAGE_STATUS::NOT_INIT;
  if (max_size <= current_size + response_size)
    // Storage full, set flag??
    return st::STORAGE_STATUS::STORAGE_FULL;

  // We have the file_path created as follows: /mount_point/svc1/hashed_url
  string file_path(mount_path);
  file_path.append("/");
  file_path.append(rel_path);

  if (std::filesystem::exists(file_path)) {
    current_size -= std::filesystem::file_size(file_path);
  }

  // increment the current storage size
  current_size += buffer.size();

  std::ofstream out_stream(file_path.data(), std::ofstream::trunc);
  if (!out_stream.is_open()) return st::STORAGE_STATUS::OPEN_ERROR;
  out_stream.write(buffer.data(), static_cast<long>(buffer.size()));
  out_stream.close();

  if (!out_stream) return st::STORAGE_STATUS::FD_CLOSE_ERROR;

  return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS RamfsCacheStorage::stopCacheStorage() {
  int err = umount(mount_path.data());
  if (err) {
    Debug::logmsg(LOG_REMOVE, "Error umounting the cache path %s ",
                  mount_path.data());
    return st::STORAGE_STATUS::GENERIC_ERROR;
  }
  std::filesystem::remove(mount_path.data());
  this->initialized = false;
  return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS RamfsCacheStorage::appendData(const std::string &rel_path,
                                                 std::string_view buffer) {
  ofstream fout;  // Create Object of Ofstream
  auto path(mount_path);
  path.append("/");
  path.append(rel_path);

  fout.open(path, std::ofstream::app);  // Append mode
  if (fout.is_open())
    fout.write(buffer.data(), static_cast<long>(buffer.size()));
  else
    return st::STORAGE_STATUS::APPEND_ERROR;
  fout.close();  // Closing the file
  current_size += buffer.size();
  return st::STORAGE_STATUS::SUCCESS;
}
bool RamfsCacheStorage::isInStorage(const std::string &svc,
                                    const std::string &url) {
  size_t hashed_url = std::hash<std::string>()(url);
  auto path = mount_path;
  path.append("/");
  path.append(svc);
  path.append("/");
  path.append(to_string(hashed_url));
  return isInStorage(path);
}
bool RamfsCacheStorage::isInStorage(const std::string &path) {
  struct stat buffer;
  return (stat(path.data(), &buffer) == 0);
}

st::STORAGE_STATUS RamfsCacheStorage::deleteInStorage(const std::string &path) {
  // Create the path string
  auto full_path = mount_path;
  full_path.append("/");
  full_path.append(path);
  size_t file_size = std::filesystem::file_size(full_path);
  if (isInStorage(full_path)) {
    if (std::remove(full_path.data())) {
      return st::STORAGE_STATUS::GENERIC_ERROR;
    }
    this->current_size -= file_size;
  } else
    return st::STORAGE_STATUS::NOT_FOUND;
  return st::STORAGE_STATUS::SUCCESS;
}

st::STORAGE_TYPE StdmapCacheStorage::getStorageType() {
  return st::STORAGE_TYPE::STDMAP;
}
st::STORAGE_STATUS StdmapCacheStorage::initCacheStorage(
    const size_t _max_size, double st_threshold, const std::string &_svc,
    const std::string &m_point) {
  this->mount_path = m_point;
  this->max_size = _max_size;
  this->cache_thr = st_threshold;
  return initServiceStorage(_svc);
}
st::STORAGE_STATUS StdmapCacheStorage::initServiceStorage(
    const std::string &_svc) {
  this->svc = _svc;
  return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS StdmapCacheStorage::getFromStorage(
    const std::string &rel_path, std::string &out_buffer) {
  std::string path = mount_path;
  path += "/";
  path += rel_path;
  out_buffer = storage.at(path);
  return st::STORAGE_STATUS::SUCCESS;
}
// FIXME: response_size Not used
st::STORAGE_STATUS StdmapCacheStorage::putInStorage(const std::string &rel_path,
                                                    std::string_view buffer,
                                                    size_t response_size) {
  current_size += buffer.size();
  std::string path = mount_path;
  path.append("/");
  path.append(rel_path);
  storage[path] = std::string(buffer);
  return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS StdmapCacheStorage::stopCacheStorage() {
  this->initialized = false;

  return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS StdmapCacheStorage::appendData(const std::string &rel_path,
                                                  std::string_view buffer) {
  std::string path = mount_path;
  path.append("/");
  path.append(rel_path);
  std::string out_buffer = storage.at(path);
  out_buffer.append(buffer);
  storage[path] = out_buffer;
  return st::STORAGE_STATUS::SUCCESS;
}
bool StdmapCacheStorage::isInStorage(const std::string &_svc,
                                     const std::string &url) {
  std::string path = mount_path;
  path.append("/");
  path.append(_svc);
  path.append("/");

  size_t hashed_url = hash<std::string>()(url);
  path += to_string(hashed_url);
  return isInStorage(path);
}
st::STORAGE_STATUS StdmapCacheStorage::deleteInStorage(
    const std::string &path) {
  if (storage.erase(path) != 1) return st::STORAGE_STATUS::GENERIC_ERROR;
  return st::STORAGE_STATUS::SUCCESS;
}
bool StdmapCacheStorage::isInStorage(const std::string &path) {
  if (storage.find(path) == storage.end())
    return false;
  else
    return true;
}
#if MEMCACHED_ENABLED == 1
/*
 * MEMCACHEDst::STORAGE
 */
st::STORAGE_TYPE MemcachedStorage::getStorageType() {
  return st::STORAGE_TYPE::MEMCACHED;
}

storage_commons::STORAGE_STATUS MemcachedStorage::initCacheStorage(
    const size_t m_size, double st_threshold, const string &svc,
    const string &m_point) {
  this->max_size = m_size;
  this->threshold = st_threshold;
  this->socket = m_point;
  memc = memcached_create(nullptr);
  memcached_server_add_unix_socket(memc, m_point.data());
  if (memc == nullptr) {
    return st::STORAGE_STATUS::GENERIC_ERROR;
  }
  return st::STORAGE_STATUS::SUCCESS;
}

storage_commons::STORAGE_STATUS MemcachedStorage::initServiceStorage(
    const string &svc) {
  this->svc = svc;
  return st::STORAGE_STATUS::SUCCESS;
}

storage_commons::STORAGE_STATUS MemcachedStorage::getFromStorage(
    const string &rel_path, string &out_buffer) {
  memcached_st *tmp_memc = nullptr;
  tmp_memc = memcached_clone(tmp_memc, memc);
  if (tmp_memc == nullptr) {
    return st::STORAGE_STATUS::GENERIC_ERROR;
  }

  auto aux_path = svc;
  aux_path.append("/");
  size_t hashed_key = std::hash<std::string>()(rel_path);
  aux_path.append(to_string(hashed_key));

  size_t buff_length = 0;
  char *buff = nullptr;

  memcached_return rc;

  buff = memcached_get(tmp_memc, aux_path.data(), aux_path.size(), &buff_length,
                       nullptr, &rc);
  if (rc != MEMCACHED_SUCCESS) {
    if (buff != nullptr) {
      free(buff);
    }
    const char *err = ::memcached_strerror(tmp_memc, rc);
    Debug::logmsg(LOG_ERR, "The error is: %s", err);
    memcached_free(tmp_memc);
    return st::STORAGE_STATUS::GENERIC_ERROR;
  }
  if (buff != nullptr && buff_length != 0) {
    out_buffer = string(buff, buff_length);
  }
  if (buff != nullptr) {
    free(buff);
  }
  memcached_free(tmp_memc);
  return st::STORAGE_STATUS::SUCCESS;
}

storage_commons::STORAGE_STATUS MemcachedStorage::putInStorage(
    const string &rel_path, string_view buffer, size_t response_size) {
  memcached_st *tmp_memc = nullptr;
  tmp_memc = memcached_clone(tmp_memc, memc);
  if (tmp_memc == nullptr) {
    return st::STORAGE_STATUS::GENERIC_ERROR;
  }
  auto aux_path = this->svc;
  aux_path.append("/");
  size_t hashed_key = std::hash<std::string>()(rel_path);
  aux_path.append(to_string(hashed_key));
  auto err = memcached_set(tmp_memc, aux_path.data(), aux_path.size(),
                           buffer.data(), buffer.size(), 0, 0);
  if (err != MEMCACHED_SUCCESS) {
    memcached_free(tmp_memc);
    return st::STORAGE_STATUS::GENERIC_ERROR;
  }
  memcached_free(tmp_memc);
  return st::STORAGE_STATUS::SUCCESS;
}

storage_commons::STORAGE_STATUS MemcachedStorage::stopCacheStorage() {
  memcached_free(memc);
  return st::STORAGE_STATUS::SUCCESS;
}

storage_commons::STORAGE_STATUS MemcachedStorage::appendData(
    const string &rel_path, string_view buffer) {
  memcached_st *tmp_memc = nullptr;
  tmp_memc = memcached_clone(tmp_memc, memc);
  if (tmp_memc == nullptr) {
    return st::STORAGE_STATUS::GENERIC_ERROR;
  }
  auto aux_path = this->svc;
  aux_path.append("/");
  size_t hashed_key = std::hash<std::string>()(rel_path);
  aux_path.append(to_string(hashed_key));
  if (memcached_append(tmp_memc, aux_path.data(), aux_path.size(),
                       buffer.data(), buffer.size(), 0,
                       0) != MEMCACHED_SUCCESS) {
    memcached_free(tmp_memc);
    return st::STORAGE_STATUS::GENERIC_ERROR;
  }
  memcached_free(tmp_memc);
  return st::STORAGE_STATUS::SUCCESS;
}
bool MemcachedStorage::isInStorage(const std::string &svc,
                                   const std::string &url) {
  auto aux_path = svc;
  aux_path.append("/");
  size_t hashed_key = std::hash<std::string>()(url);
  aux_path.append(to_string(hashed_key));
  return isInStorage(aux_path);
}
st::STORAGE_STATUS MemcachedStorage::deleteInStorage(const std::string &path) {
  memcached_st *tmp_memc = nullptr;
  tmp_memc = memcached_clone(tmp_memc, memc);
  auto aux_path = this->svc;
  aux_path.append("/");
  size_t hashed_key = std::hash<std::string>()(path);
  aux_path.append(to_string(hashed_key));

  time_t expire = 0;
  memcached_delete(tmp_memc, aux_path.data(), aux_path.size(), expire);
  memcached_free(tmp_memc);
  return st::STORAGE_STATUS::SUCCESS;
}
bool MemcachedStorage::isInStorage(const std::string &path) {
  memcached_st *tmp_memc = nullptr;
  memcached_return rc;
  tmp_memc = memcached_clone(tmp_memc, memc);
  if (tmp_memc == nullptr) {
    return st::STORAGE_STATUS::GENERIC_ERROR;
  }
  std::string buffer;
  std::size_t buff_length = 0;
  char *buff = memcached_get(tmp_memc, path.data(), path.size(), &buff_length,
                             nullptr, &rc);
  if (buff == nullptr) {
    memcached_free(tmp_memc);
    return false;
  }
  memcached_free(tmp_memc);
  return true;
}

// st::STORAGE_STATUS MemcachedStorage::stopCacheStorage(){
//    memcached_free(memc);
//    return st::STORAGE_STATUS::SUCCESS;

#endif
