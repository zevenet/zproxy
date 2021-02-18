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

#include "ssl_connection_manager.h"
#include "../util/common.h"
#include "../../zcutils/zcutils.h"
#include <openssl/err.h>

using namespace ssl;

bool SSLConnectionManager::initSslConnection(SSL_CTX * ssl_ctx,
					     Connection & ssl_connection,
					     bool client_mode)
{
	if (ssl_connection.ssl != nullptr) {
		SSL_shutdown(ssl_connection.ssl);
		SSL_clear(ssl_connection.ssl);
		SSL_free(ssl_connection.ssl);
	}
	ssl_connection.ssl = SSL_new(ssl_ctx);
	if (ssl_connection.ssl == nullptr) {
		zcutils_log_print(LOG_ERR, "SSL_new failed");
		return false;
	}

#if USE_SSL_BIO_BUFFER
	ssl_connection.sbio =
		BIO_new_socket(ssl_connection.getFileDescriptor(),
			       BIO_NOCLOSE);
	BIO_set_nbio(ssl_connection.sbio, 1);
	SSL_set0_rbio(ssl_connection.ssl, ssl_connection.sbio);
	BIO_up_ref(ssl_connection.sbio);
	SSL_set0_wbio(ssl_connection.ssl, ssl_connection.sbio);
	ssl_connection.io = BIO_new(BIO_f_buffer());
	ssl_connection.ssl_bio = BIO_new(BIO_f_ssl());
	BIO_set_nbio(ssl_connection.io, 1);
	BIO_set_nbio(ssl_connection.ssl_bio, 1);
	BIO_set_ssl(ssl_connection.ssl_bio, ssl_connection.ssl, BIO_NOCLOSE);
	BIO_push(ssl_connection.io, ssl_connection.ssl_bio);
#else
	int r = SSL_set_fd(ssl_connection.ssl,
			   ssl_connection.getFileDescriptor());
	if (!r) {
		zcutils_log_print(LOG_ERR, "SSL_set_fd failed");
		return false;
	}
#endif

	if (client_mode && ssl_connection.server_name != nullptr) {
		if (!SSL_set_tlsext_host_name
		    (ssl_connection.ssl, ssl_connection.server_name)) {
			zcutils_log_print(LOG_DEBUG,
					  "could not set SNI host name  to %s",
					  ssl_connection.server_name);
			return false;
		}
		else {
			zcutils_log_print(LOG_DEBUG,
					  "Set SNI host name \"%s\"",
					  ssl_connection.server_name);
		}
	}

	//  SSL_set_options(ssl_connection.ssl, SSL_OP_NO_COMPRESSION);
	SSL_set_mode(ssl_connection.ssl, SSL_MODE_RELEASE_BUFFERS);
	SSL_set_mode(ssl_connection.ssl, SSL_MODE_ACCEPT_MOVING_WRITE_BUFFER);
	!client_mode ? SSL_set_accept_state(ssl_connection.ssl) :
		SSL_set_connect_state(ssl_connection.ssl);
	ssl_connection.ssl_conn_status = SSL_STATUS::NEED_HANDSHAKE;
	return true;
}

IO::IO_RESULT SSLConnectionManager::handleDataRead(Connection &
						   ssl_connection)
{
#if USE_SSL_BIO_BUFFER==0
	return sslRead(ssl_connection);
#endif
	if (!ssl_connection.ssl_connected) {
		return IO::IO_RESULT::SSL_NEED_HANDSHAKE;
	}
	if (MAX_DATA_SIZE == ssl_connection.buffer_size)
		return IO::IO_RESULT::FULL_BUFFER;
	//  zcutils_log_print(LOG_DEBUG, "> handleRead");
	int rc = -1;
	size_t total_bytes_read = 0;
	for (;;) {
		BIO_clear_retry_flags(ssl_connection.io);
		ERR_clear_error();
		size_t bytes_read = 0;
		rc = BIO_read_ex(ssl_connection.io,
				 ssl_connection.buffer +
				 ssl_connection.buffer_offset +
				 ssl_connection.buffer_size,
				 static_cast <
				 int >(MAX_DATA_SIZE -
				       ssl_connection.buffer_size -
				       ssl_connection.buffer_offset),
				 &bytes_read);
		//    zcutils_log_print(LOG_DEBUG,
		//                   "BIO_read return code %d buffer size %d bytes_read %d",
		//                   rc, ssl_connection.buffer_size, bytes_read);

		if (rc == 0) {
			if (total_bytes_read > 0)
				return IO::IO_RESULT::SUCCESS;
			else {
				return IO::IO_RESULT::ZERO_DATA;
			}
		}
		else if (rc < 0) {
			if (BIO_should_retry(ssl_connection.io)) {
				if (total_bytes_read > 0)
					return IO::IO_RESULT::SUCCESS;
				else {
					return IO::IO_RESULT::DONE_TRY_AGAIN;
				}
			}
			return IO::IO_RESULT::ERROR;
		}
		total_bytes_read += bytes_read;
		ssl_connection.buffer_size +=
			static_cast < size_t >(bytes_read);
		if (static_cast <
		    int >(MAX_DATA_SIZE - ssl_connection.buffer_size -
			  ssl_connection.buffer_offset) == 0)
			return IO::IO_RESULT::FULL_BUFFER;
		// return IO::IO_RESULT::SUCCESS;
	}
}

IO::IO_RESULT SSLConnectionManager::handleWrite(Connection & ssl_connection,
						const char *data,
						size_t data_size,
						size_t &total_written,
						bool flush_data)
{
	if (!ssl_connection.ssl_connected) {
		return IO::IO_RESULT::SSL_NEED_HANDSHAKE;
	}
	if (data_size == 0)
		return IO::IO_RESULT::SUCCESS;
	IO::IO_RESULT result;
	int rc = -1;
	//  // FIXME: Buggy, used just for test
	//  zcutils_log_print(LOG_DEBUG, "### IN handleWrite data size %d", data_size);
	total_written = 0;
	ERR_clear_error();
	for (;;) {
		size_t written = 0;
		BIO_clear_retry_flags(ssl_connection.io);
		rc = BIO_write_ex(ssl_connection.io, data + total_written,
				  static_cast <
				  int >(data_size - total_written), &written);
//    if(rc != written){
//      zcutils_log_print(LOG_DEBUG, "BIO_write_ex return code %d written: %d total %d size: %d", rc,written, total_written, data_size);
//    }

		if (rc == 0) {
			if (total_written > 0) {
				if ((data_size - total_written) == 0)
					result = IO::IO_RESULT::SUCCESS;
				else
					result = IO::
						IO_RESULT::DONE_TRY_AGAIN;
			}
			else
				result = IO::IO_RESULT::ZERO_DATA;
			break;
		}
		else if (rc < 0) {
			if (BIO_should_retry(ssl_connection.io)) {
				{
					if ((data_size - total_written) == 0)
						result = IO::
							IO_RESULT::SUCCESS;
					else
						result = IO::
							IO_RESULT::DONE_TRY_AGAIN;
					break;
				}
			}
			else {
				{
					result = IO::IO_RESULT::ERROR;
					break;
				}
			}
		}
		total_written += static_cast < size_t >(written);
		if ((data_size - total_written) == 0) {
			result = IO::IO_RESULT::SUCCESS;
			break;
		}
	}
	if (flush_data && result == IO::IO_RESULT::SUCCESS) {
		zcutils_log_print(LOG_DEBUG, "%s():%d: flushing",
				  __FUNCTION__, __LINE__);
		BIO_flush(ssl_connection.io);
	}
	//  zcutils_log_print(LOG_DEBUG, "### IN handleWrite data write: %d ssl error: %s",
	//                data_size, IO::getResultString(result).c_str());
	return result;
}

bool SSLConnectionManager::handleHandshake(const SSLContext & ssl_context,
					   Connection & ssl_connection,
					   bool client_mode)
{
	auto result =
		handleHandshake(ssl_context.ssl_ctx.get(), ssl_connection,
				client_mode);
	if (result && ssl_connection.ssl_connected) {
		if (!client_mode &&
		    ssl_context.
		    listener_config->ssl_forward_sni_server_name) {
			if ((ssl_connection.server_name =
			     SSL_get_servername(ssl_connection.ssl,
						TLSEXT_NAMETYPE_host_name)) ==
			    nullptr) {
				zcutils_log_print(LOG_DEBUG,
						  "(%lx) could not get SNI host name  to %s",
						  pthread_self(),
						  ssl_connection.server_name);
			}
			else {
				zcutils_log_print(LOG_DEBUG,
						  "(%lx) Got SNI host name %s",
						  pthread_self(),
						  ssl_connection.server_name);
				ssl_connection.server_name = nullptr;
			}
		}
		else {
			ssl_connection.server_name = nullptr;
		}
	}
	return result;
}

bool SSLConnectionManager::handleHandshake(SSL_CTX * ssl_ctx,
					   Connection & ssl_connection,
					   bool client_mode)
{
	//    zcutils_log_print(LOG_DEBUG, "SSL_HANDSHAKE: %d", ssl_connection.getFileDescriptor());
	if (ssl_connection.ssl == nullptr) {
		if (!initSslConnection(ssl_ctx, ssl_connection, client_mode)) {
			return false;
		}
	}
	if (++ssl_connection.handshake_retries > 50) {
		return false;
	}
	ssl_connection.ssl_conn_status = SSL_STATUS::HANDSHAKE_START;
	ERR_clear_error();
#if USE_SSL_BIO_BUFFER
	BIO_clear_retry_flags(ssl_connection.io);
	auto i = BIO_do_handshake(ssl_connection.io);
	if (i <= 0) {
		auto errno__ = errno;
		if (!BIO_should_retry(ssl_connection.io)) {
			if (SSL_in_init(ssl_connection.ssl)) {
				//        zcutils_log_print(LOG_DEBUG,
				//                       ">>PROGRESS>>fd:%d BIO_do_handshake "
				//                       "return:%d error: with %s errno: %d:%s \n "
				//                       "Ossl errors: %s",
				//                       ssl_connection.getFileDescriptor(), i,
				//                       ssl_connection.getPeerAddress().data(),
				//                       errno__, std::strerror(errno__),
				//                       ossGetErrorStackString().get());
				return true;
			}
			if (SSL_is_init_finished(ssl_connection.ssl)) {
				//        zcutils_log_print(LOG_DEBUG,
				//                       ">>FINISHED>>fd:%d BIO_do_handshake "
				//                       "return:%d error: with %s errno: %d:%s \n "
				//                       "Ossl errors: %s",
				//                       ssl_connection.getFileDescriptor(), i,
				//                       ssl_connection.getPeerAddress().data(),
				//                       errno__, std::strerror(errno__),
				//                       ossGetErrorStackString().get());
				return true;
			}
			zcutils_log_print(LOG_DEBUG,
					  "fd:%d BIO_do_handshake "
					  "return:%d error: with %s errno: %d:%s \n "
					  "Ossl errors: %s",
					  ssl_connection.getFileDescriptor(),
					  i,
					  ssl_connection.
					  getPeerAddress().data(), errno__,
					  std::strerror(errno__),
					  ossGetErrorStackString().get());
			ssl_connection.ssl_conn_status =
				SSL_STATUS::HANDSHAKE_ERROR;
			SSL_clear(ssl_connection.ssl);
			return errno__ == 0;
		}
		if (BIO_should_write(ssl_connection.io)) {
			ssl_connection.enableWriteEvent();
			ssl_connection.ssl_conn_status =
				SSL_STATUS::WANT_WRITE;
			return true;
		}
		else if (BIO_should_read(ssl_connection.io)) {
			ssl_connection.enableReadEvent();
			ssl_connection.ssl_conn_status =
				SSL_STATUS::WANT_READ;
			return true;
		}
		else {
			zcutils_log_print(LOG_DEBUG,
					  "fd:%d BIO_do_handshake - BIO_should_XXX failed",
					  ssl_connection.getFileDescriptor());
			return false;
		}
	}
#else
	int r = SSL_do_handshake(ssl_connection.ssl);
	if (r == 0) {
		zcutils_log_print(LOG_DEBUG,
				  " fd:%d SSL_do_handshake return:%d error: with %s \n "
				  "Ossl errors: %s",
				  ssl_connection.getFileDescriptor(), r,
				  ssl_connection.getPeerAddress().data(),
				  ossGetErrorStackString().get());
		ssl_connection.ssl_conn_status = SSL_STATUS::HANDSHAKE_ERROR;
		SSL_clear(ssl_connection.ssl);
		return false;
	}
	else if (r == 1) {
#endif
		ssl_connection.ssl_connected = true;
		const SSL_CIPHER *cipher =
			SSL_get_current_cipher(ssl_connection.ssl);
		if (cipher) {
			auto buf =
				std::make_unique < char[] >
				(ZCU_DEF_BUFFER_SIZE);
			auto buf_size = ZCU_DEF_BUFFER_SIZE;
			SSL_CIPHER_description(cipher, &buf[0], buf_size - 1);

			zcutils_log_print(LOG_DEBUG,
					  "SSL: %s, %s REUSED, Ciphers: %s\n",
					  SSL_get_version(ssl_connection.ssl),
					  SSL_session_reused
					  (ssl_connection.ssl) ? "" : "Not ",
					  &buf[0]);
		}
#ifdef DEBUG_PRINT_SSL_SESSION_INFO
		SSL_SESSION *session = SSL_get_session(ssl_connection.ssl);
		auto session_info = ssl::ossGetSslSessionInfo(session);
		zcutils_log_print(LOG_ERR, "%s():%d: %s", session_info.get());
#endif
		ssl_connection.ssl_conn_status = SSL_STATUS::HANDSHAKE_DONE;
		!client_mode ? ssl_connection.enableReadEvent()
			: ssl_connection.enableWriteEvent();
		return true;
#if USE_SSL_BIO_BUFFER == 0
	}
	else {
		int errno__ = errno;
		int err = SSL_get_error(ssl_connection.ssl, r);
		switch (err) {
		case SSL_ERROR_WANT_READ:{
				ssl_connection.enableReadEvent();
				ssl_connection.ssl_conn_status =
					SSL_STATUS::WANT_READ;
				return true;
			}
		case SSL_ERROR_WANT_WRITE:{
				ssl_connection.enableWriteEvent();
				ssl_connection.ssl_conn_status =
					SSL_STATUS::WANT_WRITE;
				return true;
			}
		case SSL_ERROR_SYSCALL:{
				if (errno__ == EAGAIN) {
					return true;
				}
				zcutils_log_print(LOG_DEBUG,
						  "fd:%d SSL_do_handshake error: %s with <<%s>> \n Ossl errors:%s ",
						  ssl_connection.getFileDescriptor
						  (), getErrorString(err),
						  ssl_connection.getPeerAddress
						  ()
						  .data(),
						  ossGetErrorStackString().get
						  ());
				ssl_connection.ssl_conn_status =
					SSL_STATUS::HANDSHAKE_ERROR;
				SSL_clear(ssl_connection.ssl);
				return false;
			}
		case SSL_ERROR_SSL:{
				zcutils_log_print(LOG_DEBUG,
						  "fd:%d SSL_do_handshake error: %s with <<%s>> \n Ossl errors:%s",
						  ssl_connection.getFileDescriptor
						  (), getErrorString(err),
						  ssl_connection.getPeerAddress
						  ()
						  .data(),
						  ossGetErrorStackString().get
						  ());
				ssl_connection.ssl_conn_status =
					SSL_STATUS::HANDSHAKE_ERROR;
				SSL_clear(ssl_connection.ssl);
				return false;
			}
		case SSL_ERROR_ZERO_RETURN:
		default:{
				zcutils_log_print(LOG_DEBUG,
						  "fd:%d SSL_do_handshake return: %d error: %s  errno = %s with %s "
						  "Handshake status: %s Ossl errors: %s ",
						  ssl_connection.getFileDescriptor
						  (), r, getErrorString(err),
						  std::strerror(errno__),
						  ssl_connection.getPeerAddress
						  ().data(),
						  ssl::getSslStatusString
						  (ssl_connection.ssl_conn_status).
						  data(),
						  ossGetErrorStackString().get
						  ());
				ssl_connection.ssl_conn_status =
					SSL_STATUS::HANDSHAKE_ERROR;
				return false;
			}
		}
	}
#endif
}

SSLConnectionManager::~SSLConnectionManager()
{
}

SSLConnectionManager::SSLConnectionManager()
{
}

IO::IO_RESULT SSLConnectionManager::getSslErrorResult(SSL *
						      ssl_connection_context,
						      int &rc)
{
	rc = SSL_get_error(ssl_connection_context, rc);
	switch (rc) {
	case SSL_ERROR_NONE:
		return IO::IO_RESULT::SUCCESS;
	case SSL_ERROR_WANT_READ:	/* We need more data to finish the frame. */
		return IO::IO_RESULT::DONE_TRY_AGAIN;
	case SSL_ERROR_WANT_WRITE:{
			// Warning - Renegotiation is not possible in a TLSv1.3 connection!!!!
			// handle renegotiation, after a want write ssl
			// error,
			zcutils_log_print(LOG_DEBUG,
					  "Renegotiation of SSL connection requested by peer");
			return IO::IO_RESULT::SSL_WANT_RENEGOTIATION;
		}
	case SSL_ERROR_SSL:
		zcutils_log_print(LOG_DEBUG,
				  "corrupted data detected while reading");
		logSslErrorStack();
		[[fallthrough]];
	case SSL_ERROR_ZERO_RETURN:	/* Received a SSL close_notify alert.The operation
					   failed due to the SSL session being closed. The
					   underlying connection medium may still be open.  */
	default:
		zcutils_log_print(LOG_DEBUG, "SSL_read failed with error %s.",
				  getErrorString(rc));
		return IO::IO_RESULT::ERROR;
	}
}

IO::IO_RESULT SSLConnectionManager::sslRead(Connection & ssl_connection)
{
	if (!ssl_connection.ssl_connected) {
		return IO::IO_RESULT::SSL_NEED_HANDSHAKE;
	}
	IO::IO_RESULT result = IO::IO_RESULT::ERROR;
	int rc = -1;
	do {
		ERR_clear_error();
		rc = SSL_read(ssl_connection.ssl,
			      ssl_connection.buffer +
			      ssl_connection.buffer_offset +
			      ssl_connection.buffer_size,
			      static_cast <
			      int >(MAX_DATA_SIZE -
				    ssl_connection.buffer_size -
				    ssl_connection.buffer_offset));
		auto ssle = SSL_get_error(ssl_connection.ssl, rc);
		switch (ssle) {
		case SSL_ERROR_NONE:
			ssl_connection.buffer_size +=
				static_cast < size_t >(rc);
			result = IO::IO_RESULT::SUCCESS;
			break;
		case SSL_ERROR_WANT_READ:
		case SSL_ERROR_WANT_WRITE:{
				zcutils_log_print(LOG_DEBUG,
						  "SSL_read return %d error %d errno %d msg %s",
						  rc, ssle, errno,
						  strerror(errno));
				return IO::IO_RESULT::DONE_TRY_AGAIN;	// TODO::  check want read
			}
		case SSL_ERROR_ZERO_RETURN:
			zcutils_log_print(LOG_NOTICE,
					  "SSL has been shutdown.");
			return IO::IO_RESULT::FD_CLOSED;
		default:
			ERR_print_errors_fp(stderr);
			zcutils_log_print(LOG_NOTICE,
					  "Connection has been aborted.");
			return IO::IO_RESULT::FD_CLOSED;
		}
	} while (rc > 0);	// SSL_pending(ssl) seems unreliable

	return result;
}

IO::IO_RESULT SSLConnectionManager::sslWrite(Connection & ssl_connection,
					     const char *data,
					     size_t data_size,
					     size_t &written)
{
	if (!ssl_connection.ssl_connected) {
		return IO::IO_RESULT::SSL_NEED_HANDSHAKE;
	}
	if (data_size == 0)
		return IO::IO_RESULT::ZERO_DATA;
	size_t sent = 0;
	ssize_t rc = -1;
	//  // FIXME: Buggy, used just for test
	// zcutils_log_print(LOG_DEBUG, "### IN handleWrite data size %d", data_size);
	ERR_clear_error();
	do {
		rc = SSL_write(ssl_connection.ssl, data + sent, static_cast < int >(data_size - sent));	//, &written);
		if (rc > 0)
			sent += static_cast < size_t >(rc);
		// zcutils_log_print(LOG_DEBUG, "BIO_write return code %d sent %d", rc,
		// sent);
	} while (rc > 0 && static_cast < size_t >(rc) < (data_size - sent));

	if (sent > 0) {
		written = static_cast < size_t >(sent);
		return IO::IO_RESULT::SUCCESS;
	}
	int ssle = SSL_get_error(ssl_connection.ssl, static_cast < int >(rc));
	if (rc < 0 && ssle != SSL_ERROR_WANT_WRITE) {
		// Renegotiation is not possible in a TLSv1.3 connection
		zcutils_log_print(LOG_DEBUG,
				  "SSL_read return %d error %d errno %d msg %s",
				  rc, ssle, errno, strerror(errno));
		return IO::IO_RESULT::DONE_TRY_AGAIN;
	}
	if (rc == 0) {
		if (ssle == SSL_ERROR_ZERO_RETURN)
			zcutils_log_print(LOG_DEBUG,
					  "SSL connection has been shutdown.");
		else
			zcutils_log_print(LOG_DEBUG,
					  "Connection has been aborted.");
		return IO::IO_RESULT::FD_CLOSED;
	}
	return IO::IO_RESULT::ERROR;
}

IO::IO_RESULT SSLConnectionManager::sslWriteIOvec(Connection &
						  target_ssl_connection,
						  const iovec * __iovec,
						  int count, size_t &nwritten)
{
	size_t written = 0;
	IO::IO_RESULT result = IO::IO_RESULT::ERROR;
	zcutils_log_print(LOG_DEBUG,
			  "%s():%d: count: %d written: %d totol_written: %d",
			  __FUNCTION__, __LINE__, count, written, nwritten);
	for (auto it = 0; it < count; it++) {
		if (__iovec[it].iov_len == 0)
			continue;
		zcutils_log_print(LOG_DEBUG,
				  "%s():%d: it = %d iov base len: %d",
				  __FUNCTION__, __LINE__, it,
				  __iovec[it].iov_len);
#if USE_SSL_BIO_BUFFER
		result = handleWrite(target_ssl_connection,
				     static_cast <
				     char *>(__iovec[it].iov_base),
				     __iovec[it].iov_len, written,
				     (it == count - 1));
#else
		result = sslWrite(target_ssl_connection,
				  static_cast < char *>(__iovec[it].iov_base),
				  __iovec[it].iov_len, written);
#endif
		nwritten += written;
		zcutils_log_print(LOG_DEBUG,
				  "%s():%d: it = %d written: %d totol_written: %d",
				  __FUNCTION__, __LINE__, it, written,
				  nwritten);
		if (result != IO::IO_RESULT::SUCCESS)
			break;
	}
	zcutils_log_print(LOG_DEBUG, "%s():%d: result: %s errno: %d = %s",
			  __FUNCTION__, __LINE__,
			  IO::getResultString(result).data(), errno,
			  std::strerror(errno));
	return result;
}

IO::IO_RESULT SSLConnectionManager::handleWriteIOvec(Connection &
						     target_ssl_connection,
						     iovec * iov,
						     size_t &iovec_size,
						     size_t &iovec_written,
						     size_t &nwritten)
{
	IO::IO_RESULT result = IO::IO_RESULT::ERROR;
	size_t count = 0;
	auto nvec = iovec_size;
	nwritten = 0;
	iovec_written = 0;
	do {
		result = sslWriteIOvec(target_ssl_connection,
				       &(iov[iovec_written]),
				       static_cast <
				       int >(nvec - iovec_written), count);
		zcutils_log_print(LOG_DEBUG,
				  "%s():%d: result: %s written %d iovecwritten %d",
				  __FUNCTION__, __LINE__,
				  IO::getResultString(result).data(), count,
				  iovec_written);
		if (count > 0) {
			size_t remaining = static_cast < size_t >(count);
			for (auto it = iovec_written; it != iovec_size; it++) {
				if (remaining >= iov[it].iov_len) {
					remaining -= iov[it].iov_len;
					iov[it].iov_len = 0;
					iovec_written++;
				}
				else {
					iov[it].iov_base =
						static_cast <
						char *>(iov[iovec_written].
							iov_base) + remaining;
					zcutils_log_print(LOG_DEBUG,
							  "%s():%d: recalculating data ... remaining %d niovec_written: %d iov size %d",
							  __FUNCTION__,
							  __LINE__,
							  iov[it].iov_len -
							  remaining,
							  iovec_written,
							  iovec_size);
					iov[it].iov_len -= remaining;
					break;
				}
			}
			nwritten += static_cast < size_t >(count);
		}
		if (result != IO::IO_RESULT::SUCCESS)
			return IO::IO_RESULT::DONE_TRY_AGAIN;
		else
			result = IO::IO_RESULT::SUCCESS;
#if PRINT_DEBUG_FLOW_BUFFERS
		zcutils_log_print(LOG_DEBUG,
				  "%s():%d: headers sent, size: %d iovec_written: %d nwritten: %d IO::RES %s",
				  __FUNCTION__, __LINE__, nvec, iovec_written,
				  nwritten,
				  IO::getResultString(result).data());
#endif

	} while (iovec_written < nvec && result == IO::IO_RESULT::SUCCESS);

	return result;
}

IO::IO_RESULT SSLConnectionManager::handleDataWrite(Connection &
						    target_ssl_connection,
						    Connection &
						    ssl_connection,
						    http_parser::
						    HttpData & http_data)
{
	if (!target_ssl_connection.ssl_connected) {
		return IO::IO_RESULT::SSL_NEED_HANDSHAKE;
	}
	if (http_data.iov_size == 0) {
		ssl_connection.buffer_offset = ssl_connection.buffer_size;
		http_data.prepareToSend();
	}

	size_t nwritten = 0;
	size_t iovec_written = 0;

	auto result =
		handleWriteIOvec(target_ssl_connection, &http_data.iov[0],
				 http_data.iov_size, iovec_written, nwritten);

	zcutils_log_print(LOG_DEBUG,
			  "%s():%d: iov_written %d bytes_written: %d IO result: %s",
			  __FUNCTION__, __LINE__, iovec_written, nwritten,
			  IO::getResultString(result).data());

	if (result != IO::IO_RESULT::SUCCESS)
		return result;

	ssl_connection.buffer_size =
		ssl_connection.buffer_size - ssl_connection.buffer_offset;
	if (ssl_connection.buffer_size == 0)
		ssl_connection.buffer_offset = 0;

	http_data.message_length = 0;
	http_data.setHeaderSent(true);
	http_data.iov_size = 0;

#if PRINT_DEBUG_FLOW_BUFFERS
	zcutils_log_print(LOG_DEBUG, "%s():%d: \tin buffer size: %d",
			  __FUNCTION__, __LINE__, ssl_connection.buffer_size);
	zcutils_log_print(LOG_DEBUG, "%s():%d: \tbuffer offset: %d",
			  __FUNCTION__, __LINE__,
			  ssl_connection.buffer_offset);
	zcutils_log_print(LOG_DEBUG, "%s():%d: \tout buffer size: %d",
			  __FUNCTION__, __LINE__, ssl_connection.buffer_size);
	zcutils_log_print(LOG_DEBUG, "%s():%d: \tcontent length: %d",
			  __FUNCTION__, __LINE__, http_data.content_length);
	zcutils_log_print(LOG_DEBUG, "%s():%d: \tmessage length: %d",
			  __FUNCTION__, __LINE__, http_data.message_length);
	zcutils_log_print(LOG_DEBUG, "%s():%d: \tmessage bytes left: %d",
			  __FUNCTION__, __LINE__,
			  http_data.message_bytes_left);
#endif
	return IO::IO_RESULT::SUCCESS;
}

IO::IO_RESULT SSLConnectionManager::sslShutdown(Connection & ssl_connection)
{
	int retries = 0;
	ERR_clear_error();
	int ret = SSL_shutdown(ssl_connection.ssl);
	do {
		retries++;
		ERR_clear_error();
		/* We only do unidirectional shutdown */
		ret = SSL_shutdown(ssl_connection.ssl);
		if (ret < 0) {
			switch (SSL_get_error(ssl_connection.ssl, ret)) {
			case SSL_ERROR_WANT_READ:
				zcutils_log_print(LOG_DEBUG,
						  "%s():%d: SSL_ERROR_WANT_READ",
						  __FUNCTION__, __LINE__);
				continue;
			case SSL_ERROR_WANT_WRITE:
				zcutils_log_print(LOG_DEBUG,
						  "%s():%d: SSL_ERROR_WANT_WRITE",
						  __FUNCTION__, __LINE__);
				continue;
			case SSL_ERROR_WANT_ASYNC:
				zcutils_log_print(LOG_DEBUG,
						  "%s():%d: SSL_ERROR_WANT_ASYNC",
						  __FUNCTION__, __LINE__);
				continue;
			}
			ret = 0;
		}
	} while (ret < 0 && retries < 10);

	return IO::IO_RESULT::SUCCESS;
}

IO::IO_RESULT SSLConnectionManager::handleWrite(Connection &
						target_ssl_connection,
						Connection &
						source_ssl_connection,
						size_t &written,
						bool flush_data)
{
#if USE_SSL_BIO_BUFFER
	auto result = handleWrite(target_ssl_connection,
				  source_ssl_connection.buffer +
				  source_ssl_connection.buffer_offset,
				  source_ssl_connection.buffer_size,
				  written, flush_data);
#else
	auto result =
		stream->backend_connection.getBackend()->
		ssl_manager.sslWrite(stream->backend_connection,
				     stream->client_connection.buffer +
				     source_ssl_connection.buffer_offset,
				     stream->client_connection.buffer_size,
				     written);
#endif
	if (written > 0)
		source_ssl_connection.buffer_size -= written;
	return result;
}
