//
// Created by abdess on 1/18/19.
//

#pragma once

#include "../connection/connection.h"
#include "SSLContext.h"
#include "ssl_common.h"

namespace ssl {

  /**
   * @class SSLConnectionManager SSLConnectionManager.h "src/ssl/SSLConnectionManager.h"
   *
   * @brief The SSLConnnectionManager class manage all the operations between
   * both client and backend SSL Connections.
   *
   * This includes handshake, write and read operations.
   */
class SSLConnectionManager {
  void setSslInfoCallback(Connection &ssl_connection, SslInfoCallback callback);

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

  /** SSLContext used by the manager. */
  SSLContext *ssl_context;

  /**
   * @brief Reads from the @p ssl_connection.
   * @param ssl_connection used to read from.
   * @return the result of the read operation with a IO:IO_RESULT format.
   */
  IO::IO_RESULT handleDataRead(Connection &ssl_connection);

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
  bool handleHandshake(Connection &ssl_connection, bool client_mode = false);

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
  IO::IO_RESULT handleDataWrite(Connection &target_ssl_connection, Connection &ssl_connection, http_parser::HttpData &http_data);

  /**
   * @brief Handles the SSL handshake with the @p ssl_connection using BIO.
   *
   * It handles the SSL handshake with the @p ssl_connection using BIO, if you
   * want to use SSL please refer to handleHandshake().
   *
   * @param ssl_connection to handshake.
   * @return @c true if everything is ok, if not @c false.
   */
  bool handleBioHandshake(Connection & ssl_connection);

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
  IO::IO_RESULT handleWrite(Connection &ssl_connection, const char *data,
                            size_t data_size, size_t &written, bool flush_data = true);

  /**
   * @brief Reads from the @p ssl_connection.
   * @param ssl_connection used to read from.
   * @return the result of the read operation with a IO:IO_RESULT format.
   */
  IO::IO_RESULT sslRead(Connection & ssl_connection);

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
  IO::IO_RESULT sslWrite(Connection &ssl_connection,
                         const char *data,
                         size_t data_size,
                         size_t &written);
  SSLConnectionManager();
  virtual ~SSLConnectionManager();
  bool init(SSLContext &context);

  /**
   * @brief Initialize the SSLConnectionManager with the configuration specified
   * in the @p backend_config.
   *
   * @param backend_config to get the configuration.
   * @return @c true if everything is ok, if not @c false.
   */
  bool init(const BackendConfig &backend_config);

  /**
   * @brief Initialize the SSLConnectionManager with the configuration specified
   * in the @p listener_config.
   *
   * @param listener_config to get the configuration.
   * @return @c true if everything is ok, if not @c false.
   */
  bool init(const ListenerConfig &listener_config);

  /**
   * @brief Initialize the @p ssl_connection with the configuration established
   * in the SSLConnectionManager.
   *
   * @param ssl_connection to initialize.
   * @param client_mode specify if the @p ssl_connection is a client or a server.
   * @return @c true if everything is ok, if not @c false.
   */
  bool initSslConnection(Connection &ssl_connection, bool client_mode = false);

  /**
   * @brief Initialize the @p ssl_connection with the configuration established
   * in the SSLConnectionManager.
   *
   * This function uses BIO, if you want to use SSL please refer to
   * initSslConnection().
   *
   * @param ssl_connection to initialize.
   * @param client_mode specify if the @p ssl_connection is a client or a server.
   * @return @c true if everything is ok, if not @c false.
   */
  bool initSslConnection_BIO(Connection &ssl_connection, bool client_mode = false);

  /**
  * @brief Async Shutdown
  * @param ssl_connection used to read from.
  * @return the result of the read operation with a IO:IO_RESULT format.
  */
  IO::IO_RESULT sslShutdown(Connection &ssl_connection);
};
} // namespace ssl
