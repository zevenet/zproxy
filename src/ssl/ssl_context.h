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

#include "../config/config.h"
#include <openssl/bio.h>
#include <openssl/err.h>
#include <openssl/ssl.h>
namespace ssl
{
/**
 * @brief The SSLData struct is used to allow SNI (Server Name Indication)
 *
 * It is a linked list and each member of the list is used by one certificate.
 */
struct SSLData {
	SSL_CTX *ctx;
	char *server_name;
	unsigned char **subjectAltNames;
	size_t subjectAltNameCount;
	SSLData *next;
};

/**
 * @class SSLContext SSLContext.h "src/ssl/SSLContext.h"
 * @brief The SSLContext class contains all the infrastructure needed to
 * operate with the SSL connections.
 *
 * This includes BIO, SSL_CTX, SSLData to support SNI and some functions to
 * initialize/modify them.
 */
class SSLContext {
    public:
	/** SSL_CTX used for store the ssl information of the connection. */
	std::shared_ptr<SSL_CTX> ssl_ctx{ nullptr };
	/** ListenerConfig used to get the information needed for the SSL_CTX. */
	std::shared_ptr<ListenerConfig> listener_config;
	/** This struct is used to support SNI. */
	SSLData ctx;

	SSLContext();
	virtual ~SSLContext();

	/**
   * @brief Initialize SSLContext with default configurations.
   * @return @c true if everything is ok, @c false if not.
   */
	static bool initOpenssl();

	/**
   * @brief Initialize SSLContext with the @p cert_file and @p key_file
   * specified.
   *
   * @return @c true if everything is ok, @c false if not.
   */
	bool init(const std::string &cert_file, const std::string &key_file);

	/**
   * @brief Initialize SSLContext with the SSL_CTX from the @p backend_config_
   * specified.
   *
   * @return @c true if everything is ok, @c false if not.
   */
	bool init(std::shared_ptr<BackendConfig> backend_config_);

	/**
   * @brief Initialize SSLContext with the configuration from the
   * @p listener_config_ specified.
   *
   * @return @c true if everything is ok, @c false if not.
   */
	bool init(std::shared_ptr<ListenerConfig> listener_config_);

	/**
   * @brief Read the configuration from a OpenSSL configuration file and loads
   * it in the @p ctx specified.
   *
   * @param config_file_path is the path of the OpenSSL configuration file.
   * @param config_file_section is the
   * @param ctx is the SSL_CTX to load the configuration.
   * @return @c true if everything is ok, @c false if not.
   */
	bool loadOpensslConfig(const std::string &config_file_path,
			       const std::string &config_file_section,
			       SSL_CTX *__ctx);

	/**
   * @brief Callback used by OpenSSL SNI support.
   *
   * @param ssl is the SSL object to load.
   * @param dummy is a OpenSSL internal.
   * @param ctx is the linked list with the different SSL_CTX.
   *
   * @return SSL_TLSEXT_ERR_OK if everything is ok, if not return an OpenSSL
   * error code.
   */
	static int SNIServerName(SSL *ssl, int dummy, POUND_CTX *ctx);

	/**
   * @brief Check if the @p engine_id set in the configuration file is valid and
   * load the engine specified.
   *
   * @param engine_id is the engine name set in the configuration file.
   *
   * @return @c true if everything is ok, @c false if not.
   */
	static bool initEngine(const std::string &engine_id);
};
} // namespace ssl
