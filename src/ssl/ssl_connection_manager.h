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

#include "../connection/connection.h"
#include "ssl_common.h"
#include "ssl_context.h"

namespace ssl
{
/**
 * @class SSLConnectionManager SSLConnectionManager.h "src/ssl/SSLConnectionManager.h"
 *
 * @brief The SSLConnnectionManager class manage all the operations between
 * both client and backend SSL Connections.
 *
 * This includes handshake, write and read operations.
 */
class SSLConnectionManager {
	/**
   * @brief Gets the error result in the IO::IO_RESULT format.
   *
   * Reads the status code from the @p ssl_connection_context and transform it
   * to a IO::IO_RESULT format.
   *
   * @param ssl_connection_context is the SSL object used to check the status.
   * @param rc is the pointer where it is load the error code after the look up.
   * @return the error code in a IO::IO_RESULT format.
   */
	IO::IO_RESULT getSslErrorResult(SSL *ssl_connection_context, int &rc);

    public:
	SSLConnectionManager();
	virtual ~SSLConnectionManager();
	/**
   * @brief Reads from the @p ssl_connection.
   * @param ssl_connection used to read from.
   * @return the result of the read operation with a IO:IO_RESULT format.
   */
	static IO::IO_RESULT handleDataRead(Connection &ssl_connection);

	/**
   * @brief Handles the SSL handshake with the @p ssl_connection.
   *
   * It handles the SSL handshake with the @p ssl_connection as a server and as
   * a client if @p client_mode is @c true.
   *
   * @param ssl_connection to handshake.
   * @param client_mode specify if the handshake must be done as a client or as
   * a server.
   * @return @c true if everything is ok, if not @c false.
   */
	static bool handleHandshake(const SSLContext &ssl_context,
				    Connection &ssl_connection,
				    bool client_mode = false);
	static bool handleHandshake(SSL_CTX *ssl_ctx,
				    Connection &ssl_connection,
				    bool client_mode = false);

	/**
   * @brief Writes to the @p target_ssl_connection.
   *
   * Writes the @p ssl_connection buffer content to the @p target_ssl_connection
   * nd store it in the @p http_data.
   *
   * @param target_ssl_connection is the Connection to write to.
   * @param ssl_connection is the
   * @param http_data
   * @return the result of the write operation with a IO:IO_RESULT format.
   */
	static IO::IO_RESULT handleDataWrite(Connection &target_ssl_connection,
					     Connection &ssl_connection,
					     http_parser::HttpData &http_data);

	/**
   * @brief Writes to the @p target_ssl_connection.
   *
   * Writes the @p data to the @p ssl_connection and set the written bytes in
   * @p written. If the @p flush_data is @c true, the data is deleted from the
   * buffer.
   *
   * @param ssl_connection is the Connection to write to.
   * @param data is the data to write.
   * @param data_size bytes to write.
   * @param written is the amount of data written.
   * @param flush_data true if the data is deleted after the write operation.
   * @return the result of the write operation with a IO:IO_RESULT format.
   */
	static IO::IO_RESULT handleWrite(Connection &target_ssl_connection,
					 Connection &source_ssl_connection,
					 size_t &written,
					 bool flush_data = true);
	/**
   * @brief Writes to the @p target_ssl_connection.
   *
   * Writes the @p data to the @p ssl_connection and set the total_written bytes in
   * @p total_written. If the @p flush_data is @c true, the data is deleted from the
   * buffer.
   *
   * @param ssl_connection is the Connection to write to.
   * @param data is the data to write.
   * @param data_size bytes to write.
   * @param total_written is the amount of data total_written.
   * @param flush_data true if the data is deleted after the write operation.
   * @return the result of the write operation with a IO:IO_RESULT format.
   */
	static IO::IO_RESULT handleWrite(Connection &ssl_connection,
					 const char *data, size_t data_size,
					 size_t &total_written,
					 bool flush_data = true);

	/**
   * @brief Reads from the @p ssl_connection.
   * @param ssl_connection used to read from.
   * @return the result of the read operation with a IO:IO_RESULT format.
   */
	static IO::IO_RESULT sslRead(Connection &ssl_connection);

	/**
   * @brief Writes to the @p target_ssl_connection using SSL functions.
   *
   * Writes the @p data to the @p ssl_connection and set the written bytes in
   * @p written.
   *
   * @param ssl_connection is the Connection to write to.
   * @param data is the data to write.
   * @param data_size bytes to write.
   * @param written is the amount of data written.
   * @return the result of the write operation with a IO:IO_RESULT format.
   */
#if USE_SSL_BIO_BUFFER == 0
	static IO::IO_RESULT sslWrite(Connection &ssl_connection,
				      const char *data, size_t data_size,
				      size_t &written);
#endif
	static IO::IO_RESULT sslWriteIOvec(Connection &target_ssl_connection,
					   const iovec *__iovec, size_t count,
					   size_t &nwritten);
	static IO::IO_RESULT handleWriteIOvec(Connection &target_ssl_connection,
					      iovec *iov, size_t &iovec_size,
					      size_t &iovec_written,
					      size_t &nwritten);

	/**
   * @brief Initialize the @p ssl_connection with the configuration established
   * in the SSLConnectionManager.
   *
   * @param ssl_connection to initialize.
   * @param client_mode specify if the @p ssl_connection is a client or a
   * server.
   * @return @c true if everything is ok, if not @c false.
   */
	static bool initSslConnection(SSL_CTX *ssl_ctx,
				      Connection &ssl_connection,
				      bool client_mode = false);

	/**
   * @brief Async Ssl connection Shutdown
   * @param ssl_connection used to read from.
   * @return the result of the read operation with a IO:IO_RESULT format.
   */
	static IO::IO_RESULT sslShutdown(Connection &ssl_connection);
};
} // namespace ssl
