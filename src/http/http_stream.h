//
// Created by abdess on 4/5/18.
//

#ifndef NEW_ZHTTP_HTTP_STREAM_H
#define NEW_ZHTTP_HTTP_STREAM_H

#include "../connection/backend_connection.h"
#include "../ssl/SSLConnectionManager.h"

#include "../event/TimerFd.h"
#include "../event/epoll_manager.h"
#include "../service/backend.h"
#include "HttpRequest.h"
#include "HttpStatus.h"
#include "../connection/client_connection.h"

struct UpgradeStatus {
  http::UPGRADE_PROTOCOLS protocol {http::UPGRADE_PROTOCOLS::NONE};
  bool pinned_connection{0};
};

/**
 * @class HttpStream http_stream.h "src/http/http_stream.h"
 *
 * @brief The HttpStream class contains both client and backend connections. It
 * also controls the requests and responses. Furthermore, it implements the
 * error replies.
 *
 */
class HttpStream: public Counter<HttpStream> {

public:
  HttpStream();
  ~HttpStream();
  // no copy allowed
  HttpStream(const HttpStream&) = delete;
  HttpStream& operator=(const HttpStream&) = delete;

  /** Connection between zhttp and the client. */
  ClientConnection client_connection;
  /** Connection between zhttp and the backend. */
  BackendConnection backend_connection;
  /** Timer descriptor used for the stream timeouts. */
  TimerFd timer_fd;
  /** HttpRequest containing the request sent by the client. */
  HttpRequest request;
  /** HttpResponse containing the response sent by the backend. */
  HttpResponse response;
  /** This struct indicates the upgrade mechanism status. */
  UpgradeStatus upgrade;
  /** This enumerate indicates the chunked mechanism status. */
  http::CHUNKED_STATUS chunked_status;

  /**
   * @brief Replies an specified error to the client.
   *
   * It replies the specified error @p code with the @p code_string and the
   * error page @p string. It also replies HTTPS errors.
   *
   * @param code of the error.
   * @param code_string is the error as string format.
   * @param string is the error page to show.
   * @param listener_config is the ListenerConfig used to get the HTTPS
   * information.
   * @param ssl_manager is the SSLConnectionManager that handles the HTTPS
   * client connection.
   */
  void replyError(HttpStatus::Code code, const char *code_string,
                  const char *string, const ListenerConfig &listener_config,
                  ssl::SSLConnectionManager &ssl_manager);

  /**
   * @brief Reply a redirect message with the configuration specified in the
   * BackendConfig.
   *
   * @param backend_config is the BackendConfig to get the redirect information.
   */
  void replyRedirect(BackendConfig &backend_config);

  /**
   * @brief Reply a redirect message with the @p code and pointing to the
   * @p url.
   *
   * @param code is the redirect code.
   * @param url is the url itself.
   */
  void replyRedirect(int code, const char * url);
};

#endif // NEW_ZHTTP_HTTP_STREAM_H
