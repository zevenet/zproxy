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

#include "stream_manager.h"
#include <cstdio>
#include <thread>
#include "../handlers/https_manager.h"
#include "../../zcutils/zcu_network.h"
#ifdef ON_FLY_COMRESSION
#include "../handlers/compression.h"
#endif

void StreamManager::HandleEvent(int fd, EVENT_TYPE event_type,
				EVENT_GROUP event_group)
{
	switch (event_type) {
#if SM_HANDLE_ACCEPT
	case EVENT_TYPE::CONNECT: {
		DEBUG_COUNTER_HIT(debug__::event_connect);

		int new_fd;
		do {
			new_fd = Connection::doAccept(fd);
			if (new_fd > 0) {
				auto spt = service_manager_set[fd].lock();
				if (!spt) {
					deleteFd(
						fd); // remove listener from epoll manager.
					::close(fd); // we close the listening socket
					return;
				}
				addStream(new_fd, std::move(spt));
			} else {
				DEBUG_COUNTER_HIT(debug__::event_connect_fail);
			}
		} while (new_fd > 0);

		return;
	}
#endif
	case EVENT_TYPE::READ:
	case EVENT_TYPE::READ_ONESHOT: {
		switch (event_group) {
		case EVENT_GROUP::ACCEPTOR:
			break;
		case EVENT_GROUP::SERVER: {
			DEBUG_COUNTER_HIT(debug__::event_backend_read);
			onResponseEvent(fd);
			break;
		}
		case EVENT_GROUP::CLIENT: {
			DEBUG_COUNTER_HIT(debug__::event_client_read);
			onRequestEvent(fd);
			break;
		}
		case EVENT_GROUP::CONNECT_TIMEOUT:
			onConnectTimeoutEvent(fd);
			break;
		case EVENT_GROUP::REQUEST_TIMEOUT:
			onRequestTimeoutEvent(fd);
			break;
		case EVENT_GROUP::RESPONSE_TIMEOUT:
			onResponseTimeoutEvent(fd);
			break;
		case EVENT_GROUP::SIGNAL:
			onSignalEvent(fd);
			break;
		case EVENT_GROUP::MAINTENANCE:
			break;
		default:
			deleteFd(fd);
			close(fd);
			break;
		}
		return;
	}
	case EVENT_TYPE::WRITE: {
		switch (event_group) {
		case EVENT_GROUP::ACCEPTOR:
			break;
		case EVENT_GROUP::SERVER: {
			DEBUG_COUNTER_HIT(debug__::event_backend_write);
			auto stream = bck_streams_set[fd];
			if (stream == nullptr) {
				deleteFd(fd);
				::close(fd);
				return;
			}
			onServerWriteEvent(stream);
			break;
		}
		case EVENT_GROUP::CLIENT: {
			DEBUG_COUNTER_HIT(debug__::event_client_write);
			auto stream = cl_streams_set[fd];
			if (stream == nullptr) {
				deleteFd(fd);
				::close(fd);
				return;
			}
			onClientWriteEvent(stream);
			break;
		}
		default: {
			deleteFd(fd);
			::close(fd);
		}
		}

		return;
	}
	case EVENT_TYPE::DISCONNECT: {
		DEBUG_COUNTER_HIT(debug__::event_disconnect);

		switch (event_group) {
		case EVENT_GROUP::SERVER: {
			DEBUG_COUNTER_HIT(debug__::event_backend_disconnect);
			auto stream = bck_streams_set[fd];
			if (stream == nullptr) {
				char addr[150];
				zcu_log_print(
					LOG_NOTICE,
					"Remote backend \"%s\" closed connection prematurely",
					zcu_soc_get_peer_address(
						fd, addr, 150) != nullptr ?
						      addr :
						      "");
				deleteFd(fd);
				::close(fd);
				return;
			}
			onServerDisconnect(stream);
			return;
		}
		case EVENT_GROUP::CLIENT: {
			DEBUG_COUNTER_HIT(debug__::event_client_disconnect);
			auto stream = cl_streams_set[fd];
			if (stream == nullptr) {
				char addr[150];
				zcu_log_print(
					LOG_NOTICE,
					"Remote client \"%s\" closed connection prematurely",
					zcu_soc_get_peer_address(
						fd, addr, 150) != nullptr ?
						      addr :
						      "");
				deleteFd(fd);
				::close(fd);
				return;
			}
			onClientDisconnect(stream);
			return;
		}
		default:
			deleteFd(fd);
			::close(fd);
			return;
		}
		break;
	}
	default:
		zcu_log_print(LOG_ERR, "%s():%d: unexpected event type",
			      __FUNCTION__, __LINE__);
		deleteFd(fd);
		::close(fd);
	}
}

void StreamManager::stop()
{
	is_running = false;
	if (this->worker.joinable())
		this->worker.join();
}

void StreamManager::start(int thread_id_)
{
	ctl::ControlManager::getInstance()->attach(std::ref(*this));

	is_running = true;
	worker_id = thread_id_;

	for (auto &[sm_id, sm] : ServiceManager::getInstance()) {
		if (sm->disabled)
			continue;
		if (!this->registerListener(sm)) {
			zcu_log_print(
				LOG_ERR,
				"%s():%d: error initializing StreamManager for farm %s",
				__FUNCTION__, __LINE__,
				sm->listener_config_->name.data());
			return;
		}
	}

	this->worker = std::thread([this] { doWork(); });
	if (worker_id >= 0) {
		//    helper::ThreadHelper::setThreadAffinity(worker_id,
		//    worker.native_handle());
		helper::ThreadHelper::setThreadName(
			"WORKER_" + std::to_string(worker_id),
			worker.native_handle());
	}
}

StreamManager::StreamManager(){
	// TODO:: do attach for config changes
};

StreamManager::~StreamManager()
{
	ctl::ControlManager::getInstance()->deAttach(std::ref(*this));
	stop();
	if (worker.joinable())
		worker.join();
	for (auto &key_pair : cl_streams_set) {
		delete key_pair.second;
	}
	for (auto &key_pair : bck_streams_set) {
		delete key_pair.second;
	}
}

void StreamManager::doWork()
{
	while (is_running) {
		if (loopOnce(EPOLL_WAIT_TIMEOUT) <= 0) {
			//       something bad happend
		}
		// if(needMainatance)
		//    doMaintenance();
	}
}

void StreamManager::addStream(int fd,
			      std::shared_ptr<ServiceManager> service_manager)
{
	DEBUG_COUNTER_HIT(debug__::on_client_connect);
#if SM_HANDLE_ACCEPT
	HttpStream *stream = cl_streams_set[fd];
	if (UNLIKELY(stream != nullptr)) {
		streamLogMessage(stream, "recycling stream");
		clearStream(stream);
	}
	stream = new HttpStream();
	stream->client_connection.setFileDescriptor(fd);
	stream->service_manager =
		std::move(service_manager); // TODO::benchmark!!
	cl_streams_set[fd] = stream;
	auto &listener_config = *stream->service_manager->listener_config_;
	stream->status |= helper::to_underlying(STREAM_STATUS::CL_READ_PENDING);
#if USE_TIMER_FD_TIMEOUT
	stream->timer_fd.set(listener_config.to * 1000);
	addFd(stream->timer_fd.getFileDescriptor(), EVENT_TYPE::TIMEOUT,
	      EVENT_GROUP::REQUEST_TIMEOUT);
	timers_set[stream->timer_fd.getFileDescriptor()] = stream;
#else
	this->setTimeOut(fd, TIMEOUT_TYPE::CLIENT_READ_TIMEOUT,
			 listener_config.to);
#endif
	stream->client_connection.enableEvents(this, EVENT_TYPE::READ,
					       EVENT_GROUP::CLIENT);
	//increment connections
	stream->service_manager->conns_stats.established_connection++;

	if (stream->service_manager->is_https_listener) {
		stream->client_connection.ssl_conn_status =
			ssl::SSL_STATUS::NEED_HANDSHAKE;
	}
#if WAF_ENABLED
	if (listener_config.rules) {
		stream->waf_rules = listener_config.rules;
	}
#endif
// configurar
#else
	if (!this->addFd(fd, EVENT_TYPE::READ, EVENT_GROUP::CLIENT))
		zcu_log_print(LOG_ERR, "%s():%d: error adding to epoll manager",
			      __FUNCTION__, __LINE__);
#endif
}

int StreamManager::getWorkerId()
{
	return worker_id;
}

void StreamManager::onRequestEvent(int fd)
{
	HttpStream *stream = cl_streams_set[fd];

	if (stream == nullptr) {
		deleteFd(fd);
		::close(fd);
		return;
	}

	streamLogDebug(stream, "onRequestEvent");

	auto &listener_config_ = *stream->service_manager->listener_config_;
#if DEBUG_ZCU_LOG
	HttpStream::debugBufferData(__FUNCTION__, __LINE__, stream, "OnRequest",
				    "init");
#endif

	if (stream->hasStatus(STREAM_STATUS::REQUEST_PENDING)) {
		DEBUG_COUNTER_HIT(debug__::on_request);
		stream->status |=
			helper::to_underlying(STREAM_STATUS::CL_READ_PENDING);
		stream->backend_connection.enableWriteEvent();
		stream->client_connection.disableEvents();
		HttpStream::debugBufferData(__FUNCTION__, __LINE__, stream,
					    "OnRequest", "REQUEST_PENDING");
		return;
	}
	IO::IO_RESULT result = IO::IO_RESULT::ERROR;
	if (stream->service_manager->is_https_listener) {
		HttpStream::debugBufferData(__FUNCTION__, __LINE__, stream,
					    "OnRequest", "HTTPS");
		result = ssl::SSLConnectionManager::handleDataRead(
			stream->client_connection);
	} else {
		HttpStream::debugBufferData(__FUNCTION__, __LINE__, stream,
					    "OnRequest", "HTTP");
		result = stream->client_connection.read();
	}

	HttpStream::debugBufferData(__FUNCTION__, __LINE__, stream, "OnRequest",
				    IO::getResultString(result).data());

	switch (result) {
	case IO::IO_RESULT::SSL_HANDSHAKE_ERROR:
	case IO::IO_RESULT::SSL_NEED_HANDSHAKE: {
		if (!ssl::SSLConnectionManager::handleHandshake(
			    *stream->service_manager->ssl_context,
			    stream->client_connection)) {
			HttpStream::debugBufferData(__FUNCTION__, __LINE__,
						    stream, "OnRequest",
						    "HANDSHAKE");

			streamLogNoResponse(stream,
					    "handshake error with client");
			clearStream(stream);
			return;
		}
		if (stream->client_connection.ssl_connected) {
			HttpStream::debugBufferData(__FUNCTION__, __LINE__,
						    stream, "OnRequest",
						    "HANDSHAKE");
			DEBUG_COUNTER_HIT(debug__::on_handshake);
			httpsHeaders(stream, listener_config_.clnt_check);
			stream->backend_connection.server_name =
				stream->client_connection.server_name;
			onRequestEvent(fd);
			return;
		} else if ((ERR_GET_REASON(ERR_peek_error()) ==
			    SSL_R_HTTP_REQUEST) &&
			   (ERR_GET_LIB(ERR_peek_error()) == ERR_LIB_SSL)) {
			/* the client speaks plain HTTP on our HTTPS port */
			streamLogMessage(
				stream,
				"The client sent a plain HTTP message to an SSL port");
			if (listener_config_.nossl_redir > 0) {
				if (http_manager::replyRedirect(
					    listener_config_.nossl_redir,
					    listener_config_.nossl_url,
					    *stream))
					clearStream(stream);
				return;
			} else {
				http_manager::replyError(
					stream, listener_config_.codenossl,
					http::reasonPhrase(
						listener_config_.codenossl),
					listener_config_.errnossl,
					stream->client_connection,
					listener_config_.response_stats);
				clearStream(stream);
			}
		}
		return;
	}
	case IO::IO_RESULT::SUCCESS:
	case IO::IO_RESULT::DONE_TRY_AGAIN:
	case IO::IO_RESULT::ZERO_DATA:
	case IO::IO_RESULT::FULL_BUFFER:
	case IO::IO_RESULT::FD_CLOSED:
		break;
	case IO::IO_RESULT::ERROR:
	case IO::IO_RESULT::CANCELLED:
	default: {
		streamLogNoResponse(stream, "Error reading the request");
		clearStream(stream);
		return;
	}
	}

	DEBUG_COUNTER_HIT(debug__::on_request);
	if (stream->client_connection.buffer_size == 0) {
		stream->client_connection.enableReadEvent();
		return;
	}
	this->stopTimeOut(stream->client_connection.getFileDescriptor());
	if (result == IO::IO_RESULT::FULL_BUFFER) {
		stream->status |=
			helper::to_underlying(STREAM_STATUS::CL_READ_PENDING);
		stream->client_connection.disableEvents();
	} else {
		stream->clearStatus(STREAM_STATUS::CL_READ_PENDING);
	}

	if (stream->hasOption(STREAM_OPTION::PINNED_CONNECTION) ||
	    stream->request.hasPendingData()) {
#ifdef CACHE_ENABLED
		if (stream->request.chunked_status !=
		    CHUNKED_STATUS::CHUNKED_DISABLED) {
			auto pending_chunk_bytes =
				http_manager::handleChunkedData(
					stream->client_connection,
					stream->request);
			if (pending_chunk_bytes <
			    0) { // we don't have enough data to get next
				// chunk size, so we wait for more data
				stream->client_connection.enableReadEvent();
				return;
			}
		}
#endif
#if DEBUG_ZCU_LOG
		HttpStream::debugBufferData(__FUNCTION__, __LINE__, stream,
					    "OnRequestContinue", "");
#endif
#if ENABLE_QUICK_RESPONSE
		onServerWriteEvent(stream);
#else
		stream->backend_connection.enableWriteEvent();
#endif
		return;
	}
#if DEBUG_ZCU_LOG
	HttpStream::debugBufferData(__FUNCTION__, __LINE__, stream, "OnRequest",
				    "");
#endif

	/* Parse HTTP request */
	size_t parsed = 0;
	http_parser::PARSE_RESULT parse_result;

	parse_result = stream->request.parseRequest(
		stream->client_connection.buffer +
			stream->client_connection.buffer_offset,
		stream->client_connection.buffer_size,
		&parsed); // parsing http data as response structured

	switch (parse_result) {
	case http_parser::PARSE_RESULT::SUCCESS: {
		stream->status |=
			helper::to_underlying(STREAM_STATUS::REQUEST_PENDING);
		break;
	}
	case http_parser::PARSE_RESULT::TOOLONG:
		streamLogMessage(stream, "http request parser TOOLONG");
		http_manager::replyError(
			stream, http::Code::URITooLong,
			http::reasonPhrase(http::Code::URITooLong),
			listener_config_.err414, stream->client_connection,
			listener_config_.response_stats);
		this->clearStream(stream);
		return;
	case http_parser::PARSE_RESULT::INCOMPLETE:
		streamLogDebug(stream, "http request parser INCOMPLETE");
		return;
	case http_parser::PARSE_RESULT::FAILED:
		streamLogMessage(stream, "http request parser FAILED");
		http_manager::replyError(
			stream, http::Code::BadRequest,
			http::reasonPhrase(http::Code::BadRequest),
			listener_config_.errreq, stream->client_connection,
			listener_config_.response_stats);
		this->clearStream(stream);
		return;
	}

	/* Select a service */
	auto service = stream->service_manager->getService(stream->request);
	if (service == nullptr) {
		http_manager::replyError(
			stream, http::Code::ServiceUnavailable,
			validation::request_result_reason.at(
				validation::REQUEST_RESULT::SERVICE_NOT_FOUND),
			listener_config_.err503, stream->client_connection,
			listener_config_.response_stats);
		this->clearStream(stream);
		return;
	}
	auto last_service_ptr = stream->request.getService();
	stream->request.setService(service);

	/* Validate Request and manage (rem/add/mod) HTTP fields */
	auto valid = http_manager::validateRequest(*stream);
	if (UNLIKELY(validation::REQUEST_RESULT::OK != valid)) {
		http_manager::replyError(
			stream, http::Code::NotImplemented,
			validation::request_result_reason.at(valid),
			listener_config_.err501, stream->client_connection,
			listener_config_.response_stats);
		this->clearStream(stream);
		return;
	}

	// Add the headers configured (addXheader direcitves). Service context has more
	// priority. These headers are not removed for removeheader directive
	if (!service->service_config.add_head_req.empty()) {
		stream->request.addHeader(service->service_config.add_head_req,
					  true);
	} else if (!listener_config_.add_head_req.empty()) {
		stream->request.addHeader(listener_config_.add_head_req, true);
	}

#if WAF_ENABLED
	if (stream->waf_rules) {
		// rule struct is unitializate if no rulesets are configured
		delete stream->modsec_transaction;
		stream->modsec_transaction = new modsecurity::Transaction(
			listener_config_.modsec.get(),
			listener_config_.rules.get(), nullptr);
		if (Waf::checkRequestWaf(*stream)) {
			listener_config_.response_stats.increaseWaf();
			if (stream->modsec_transaction->m_it.url != nullptr) {
				streamLogWaf(stream,
					     "WAF redirected a request");
				if (http_manager::replyRedirect(
					    stream->modsec_transaction->m_it
						    .status,
					    stream->modsec_transaction->m_it.url,
					    *stream))
					clearStream(stream);
				return;
			} else {
				streamLogWaf(stream, "WAF rejected a request");
				auto code = static_cast<http::Code>(
					stream->modsec_transaction->m_it.status);
				http_manager::replyError(
					stream, code, reasonPhrase(code),
					listener_config_.errwaf,
					stream->client_connection,
					listener_config_.response_stats);
			}
			clearStream(stream);
			return;
		}
	}
#endif
	std::string x_forwarded_for_header;
	if (!stream->request.x_forwarded_for_string.empty()) {
		// set extra header to forward to the backends
		x_forwarded_for_header = stream->request.x_forwarded_for_string;
		x_forwarded_for_header += ", ";
	}
	x_forwarded_for_header += stream->client_connection.getPeerAddress();
	stream->request.addHeader(http::HTTP_HEADER_NAME::X_FORWARDED_FOR,
				  x_forwarded_for_header);
#if USE_TIMER_FD_TIMEOUT
	stream->timer_fd.unset();
	deleteFd(stream->timer_fd.getFileDescriptor());
	timers_set[stream->timer_fd.getFileDescriptor()] = nullptr;
#else
	stopTimeOut(fd);
#endif

#ifdef CACHE_ENABLED
	// If the cache is enabled and the request is cached and it is also fresh
	auto ret = CacheManager::handleRequest(stream, service,
					       listener_config_set);
	// Must return error
	if (ret == -1) {
		// If the directive only-if-cached is in the request and the content
		// is not cached, reply an error 504 as stated in the rfc7234
		http_manager::replyError(
			stream, http::Code::GatewayTimeout,
			http::reasonPhrase(http::Code::GatewayTimeout), "",
			stream->client_connection, this->ssl_manager);
		this->clearStream(stream);
		return;
	}
	// Return, using the cache from response
	if (ret == 0) {
		return;
	}

#endif
	auto bck =
		service->getBackend(stream->client_connection, stream->request);
	if (bck == nullptr) {
		// No backend available
		http_manager::replyError(
			stream, http::Code::ServiceUnavailable,
			validation::request_result_reason.at(
				validation::REQUEST_RESULT::BACKEND_NOT_FOUND),
			listener_config_.err503, stream->client_connection,
			listener_config_.response_stats);
		this->clearStream(stream);
		return;
	}
	IO::IO_OP op_state = IO::IO_OP::OP_ERROR;
	stream->response.reset_parser();
	switch (bck->backend_type) {
	case BACKEND_TYPE::REMOTE: {
		bool need_new_backend = true;
		if (last_service_ptr != nullptr) {
			auto last_service =
				static_cast<Service *>(last_service_ptr);
			if (last_service->id == service->id &&
			    stream->backend_connection.isConnected() &&
			    stream->backend_connection.getBackend() !=
				    nullptr) {
				need_new_backend = false;
			}
		}
		if (need_new_backend) {
			// null
			if (stream->backend_connection.getFileDescriptor() >
			    0) {
				deleteFd(
					stream->backend_connection
						.getFileDescriptor()); // Client cannot
				// Client cannot  be connected to more than one backend at
				// time
				bck_streams_set.erase(
					stream->backend_connection
						.getFileDescriptor());
				if (stream->backend_connection.isConnected() &&
				    stream->backend_connection.getBackend() !=
					    nullptr)
					stream->backend_connection.getBackend()
						->decreaseConnection();
			}
			stream->backend_connection.reset();
			stream->backend_connection.setBackend(bck);
			Time::getTime(stream->backend_connection.time_start);
			op_state = stream->backend_connection.doConnect(
				*bck->address_info, bck->conn_timeout, true,
				bck->nf_mark);
			switch (op_state) {
			case IO::IO_OP::OP_ERROR: {
				streamLogMessage(
					stream,
					"error connecting to the backend %s",
					bck->address.data());
				onBackendConnectionError(stream);
				return;
			}
			case IO::IO_OP::OP_IN_PROGRESS: {
				stream->status |= helper::to_underlying(
					STREAM_STATUS::BCK_CONN_PENDING);
#if USE_TIMER_FD_TIMEOUT
				stream->timer_fd.set(bck->conn_timeout * 1000);
				this->addFd(
					stream->timer_fd.getFileDescriptor(),
					EVENT_TYPE::READ_ONESHOT,
					EVENT_GROUP::CONNECT_TIMEOUT);
#else
				setTimeOut(stream->backend_connection
						   .getFileDescriptor(),
					   events::TIMEOUT_TYPE::
						   SERVER_WRITE_TIMEOUT,
					   bck->conn_timeout);
#endif
				stream->backend_connection.getBackend()
					->increaseConnTimeoutAlive();
				break;
			}
			case IO::IO_OP::OP_SUCCESS: {
				DEBUG_COUNTER_HIT(debug__::on_backend_connect);
				if (stream->backend_connection.getBackend()
					    ->isConnectionLimit()) {
					http_manager::replyError(
						stream,
						http::Code::ServiceUnavailable,
						validation::request_result_reason
							.at(validation::REQUEST_RESULT::
								    BACKEND_NOT_FOUND),
						listener_config_.err503,
						stream->client_connection,
						listener_config_.response_stats);
					this->clearStream(stream);
				}
				stream->backend_connection.getBackend()
					->increaseConnection();
				break;
			}
			}
			auto bck_stream = bck_streams_set.find(
				stream->backend_connection.getFileDescriptor());
			if (bck_stream != bck_streams_set.end()) {
				streamLogDebug(stream,
					       "bck stream exists in set");
				// delete bck_stream->second;
			}
			bck_streams_set[stream->backend_connection
						.getFileDescriptor()] = stream;
			stream->backend_connection.enableEvents(
				this, EVENT_TYPE::WRITE, EVENT_GROUP::SERVER);
		}

		streamLogDebug(stream, "%s %s",
			       need_new_backend ? "NEW" : "REUSED",
			       stream->request.http_message_str.data());

		// Rewrite destination
		if (stream->request.add_destination_header) {
			std::string header_value =
				stream->backend_connection.getBackend()
						->isHttps() ?
					      "https://" :
					      "http://";
			header_value +=
				stream->backend_connection.getPeerAddress();
			header_value += ':';
			header_value += stream->request.path;
			stream->request.addHeader(
				http::HTTP_HEADER_NAME::DESTINATION,
				header_value);
		}
		if (!stream->request.host_header_found) {
			std::string header_value;
			header_value +=
				stream->backend_connection.getBackend()->address;
			header_value += ':';
			header_value += std::to_string(
				stream->backend_connection.getBackend()->port);
			stream->request.addHeader(http::HTTP_HEADER_NAME::HOST,
						  header_value);
		}
		/* After setting the backend and the service in the first request,
			 * pin the connection if the PinnedConnection service config
			 * parameter is true. Note: The first request must be HTTP. */
		if (service->service_config.pinned_connection) {
			stream->options |= helper::to_underlying(
				STREAM_OPTION::PINNED_CONNECTION);
		}
		stream->backend_connection.enableWriteEvent();
		break;
	}

	case BACKEND_TYPE::EMERGENCY_SERVER:

		break;
	case BACKEND_TYPE::REDIRECT: {
		if (http_manager::replyRedirect(*stream, *bck))
			clearStream(stream);
		return;
	}
	case BACKEND_TYPE::CACHE_SYSTEM:
		break;
	case BACKEND_TYPE::TEST_SERVER:
		http_manager::replyTestServer(*stream);
		return;
	}
	stream->client_connection.enableReadEvent();
}

void StreamManager::onResponseEvent(int fd)
{
	HttpStream *stream = bck_streams_set[fd];

	if (stream == nullptr) {
		deleteFd(fd);
		::close(fd);
		return;
	}

	streamLogDebug(stream, "");

	auto &listener_config_ = *stream->service_manager->listener_config_;

	if (stream->hasStatus(STREAM_STATUS::RESPONSE_PENDING)) {
		stream->status |=
			helper::to_underlying(STREAM_STATUS::BCK_READ_PENDING);
		stream->client_connection.enableWriteEvent();
		stream->backend_connection.disableEvents();
		return;
	}

#if DEBUG_ZCU_LOG
	HttpStream::debugBufferData(__FUNCTION__, __LINE__, stream,
				    "OnResponse", "RESPONSE_PENDING");
#endif
	DEBUG_COUNTER_HIT(debug__::on_response);
	IO::IO_RESULT result;

	auto service = static_cast<Service *>(stream->request.getService());

	if (stream->backend_connection.getBackend()->isHttps()) {
		result = ssl::SSLConnectionManager::handleDataRead(
			stream->backend_connection);
	} else {
#if ENABLE_ZERO_COPY
		if (stream->response.message_bytes_left > 0 &&
		    !stream->backend_connection.getBackend()->isHttps() &&
		    !this->is_https_listener
		    /*&& stream->response.transfer_encoding_header */) {
			result = stream->backend_connection.zeroRead();
			if (result == IO::IO_RESULT::ERROR) {
				streamLogNoResponse(
					stream,
					"error reading response from backend");
				clearStream(stream);
				return;
			}
#if ENABLE_QUICK_RESPONSE
			result = stream->backend_connection.zeroWrite(
				stream->client_connection.getFileDescriptor(),
				stream->response);
			switch (result) {
			case IO::IO_RESULT::FD_CLOSED:
			case IO::IO_RESULT::ERROR: {
				streamLogNoResponse(
					stream,
					"error writing response from backend");
				clearStream(stream);
				return;
			}
			case IO::IO_RESULT::SUCCESS:
				return;
			case IO::IO_RESULT::DONE_TRY_AGAIN:
				stream->client_connection.enableWriteEvent();
				return;
			case IO::IO_RESULT::FULL_BUFFER:
				break;
			}
#endif
		} else
#endif
			result = stream->backend_connection.read();
	}

	switch (result) {
	case IO::IO_RESULT::SSL_HANDSHAKE_ERROR:
	case IO::IO_RESULT::SSL_NEED_HANDSHAKE: {
		stream->backend_connection.server_name =
			stream->client_connection.server_name;
		if (!ssl::SSLConnectionManager::handleHandshake(
			    stream->backend_connection.getBackend()->ctx.get(),
			    stream->backend_connection, true)) {
			streamLogMessage(
				stream,
				"SSL_NEED_HANDSHAKE, error in backend handshake on request");
			http_manager::replyError(
				stream, http::Code::ServiceUnavailable,
				http::reasonPhrase(
					http::Code::ServiceUnavailable),
				listener_config_.err503,
				stream->client_connection,
				listener_config_.response_stats);
			clearStream(stream);
		}
		if (stream->backend_connection.ssl_connected) {
			stream->backend_connection.enableWriteEvent();
		}
		return;
	}
	case IO::IO_RESULT::FULL_BUFFER:
	case IO::IO_RESULT::FD_CLOSED:
	case IO::IO_RESULT::ZERO_DATA:
	case IO::IO_RESULT::SUCCESS:
	case IO::IO_RESULT::DONE_TRY_AGAIN: {
		if (stream->backend_connection.buffer_size == 0) {
			stream->backend_connection.enableReadEvent();
			return;
		}
		break;
	}
	case IO::IO_RESULT::ERROR:
	case IO::IO_RESULT::CANCELLED:
	default: {
		streamLogMessage(stream, "backend read error");
		clearStream(stream);
		return;
	}
	}
// disable response timeout timerfd
#if USE_TIMER_FD_TIMEOUT
	if (stream->backend_connection.getBackend()->response_timeout > 0) {
		stream->timer_fd.unset();
		events::EpollManager::deleteFd(
			stream->timer_fd.getFileDescriptor());
	}
#else
	this->stopTimeOut(fd);
#endif
	if (result == IO::IO_RESULT::FULL_BUFFER) {
		stream->status |=
			helper::to_underlying(STREAM_STATUS::BCK_READ_PENDING);
		stream->backend_connection.disableEvents();
	} else {
		stream->clearStatus(STREAM_STATUS::BCK_READ_PENDING);
	}
#if DEBUG_ZCU_LOG
	HttpStream::debugBufferData(__FUNCTION__, __LINE__, stream,
				    "OnResponse",
				    IO::getResultString(result).data());
#endif

	if (stream->hasOption(STREAM_OPTION::PINNED_CONNECTION) ||
	    stream->response.hasPendingData()) {
#ifdef CACHE_ENABLED
		if (stream->response.chunked_status !=
		    CHUNKED_STATUS::CHUNKED_DISABLED) {
			auto pending_chunk_bytes =
				http_manager::handleChunkedData(
					stream->backend_connection,
					stream->response);
			if (pending_chunk_bytes <
			    0) { // we don't have enough data to get next
				// chunk size, so we wait for more data
				stream->backend_connection.enableReadEvent();
				return;
			}
		}
		if (service->cache_enabled) {
			CacheManager::handleResponse(stream, service);
		}
#endif

#if ENABLE_QUICK_RESPONSE
		onClientWriteEvent(stream);
#else
		stream->client_connection.enableWriteEvent();
#endif
		return;
	} else {
		if (stream->backend_connection.buffer_size == 0)
			return;
		streamLogDebug(stream, "managed requests: %d",
			       ++stream->managed_requests);
		size_t parsed = 0;
		auto ret = stream->response.parseResponse(
			stream->backend_connection.buffer +
				stream->backend_connection.buffer_offset,
			stream->backend_connection.buffer_size, &parsed);

		switch (ret) {
		case http_parser::PARSE_RESULT::SUCCESS: {
			stream->backend_connection.getBackend()
				->calculateLatency(
					stream->backend_connection.time_start);
			stream->request.chunked_status =
				CHUNKED_STATUS::CHUNKED_DISABLED;
			stream->backend_connection.buffer_offset = 0;
			stream->client_connection.buffer_offset = 0;
			stream->client_connection.buffer_size = 0;
			break;
		}
		case http_parser::PARSE_RESULT::TOOLONG:
		case http_parser::PARSE_RESULT::FAILED: {
			streamLogMessage(
				stream,
				"HTTP response parser %s - Response data in buffer (size:%luB): %.*s",
				(ret == http_parser::PARSE_RESULT::TOOLONG) ?
					      "TOOLONG" :
					      "FAILED",
				stream->backend_connection.buffer_size,
				stream->backend_connection.buffer_size,
				stream->backend_connection.buffer);
			clearStream(stream);
			return;
		}
		case http_parser::PARSE_RESULT::INCOMPLETE:
			stream->backend_connection.enableReadEvent();
			return;
		}
		auto latency =
			Time::getElapsed(stream->backend_connection.time_start);
		streamLogDebug(stream, "backend response: %s -> %s, %lf",
			       stream->response.http_message_str.data(),
			       stream->request.http_message_str.data(),
			       latency);

		stream->backend_connection.getBackend()->setAvgTransferTime(
			stream->backend_connection.time_start);

		if (http_manager::validateResponse(*stream) !=
		    validation::REQUEST_RESULT::OK) {
			streamLogMessage(
				stream,
				"error validating the backend response - %.*s",
				stream->backend_connection.buffer_size,
				stream->backend_connection.buffer);
			http_manager::replyError(
				stream, http::Code::ServiceUnavailable,
				http::reasonPhrase(
					http::Code::ServiceUnavailable),
				listener_config_.err503,
				stream->client_connection,
				listener_config_.response_stats);
			this->clearStream(stream);
			return;
		}
		stream->status |=
			helper::to_underlying(STREAM_STATUS::RESPONSE_PENDING);

		// Add custom headers
		if (!service->service_config.add_head_resp.empty()) {
			stream->response.addHeader(
				service->service_config.add_head_resp, true);
		} else if (!listener_config_.add_head_resp.empty()) {
			stream->response.addHeader(
				listener_config_.add_head_resp, true);
		}

#if WAF_ENABLED
		if (stream->modsec_transaction != nullptr) {
			if (Waf::checkResponseWaf(*stream)) {
				listener_config_.response_stats.increaseWaf();
				if (stream->modsec_transaction->m_it.url !=
				    nullptr) {
					streamLogWaf(
						stream,
						"WAF redirected a response from the backend");
					// send redirect
					if (http_manager::replyRedirect(
						    stream->modsec_transaction
							    ->m_it.status,
						    stream->modsec_transaction
							    ->m_it.url,
						    *stream))
						clearStream(stream);
					return;
				} else {
					// reject the request
					auto code = static_cast<http::Code>(
						stream->modsec_transaction->m_it
							.status);
					http_manager::replyError(
						stream, code,
						reasonPhrase(code),
						listener_config_.errwaf,
						stream->client_connection,
						listener_config_.response_stats);
					streamLogWaf(
						stream,
						"WAF rejected a response from the backend");
				}
				clearStream(stream);
				return;
			}
		}
#endif
		// increase stat for backend response code
		auto code = static_cast<http::Code>(
			stream->response.http_status_code);
		stream->backend_connection.getBackend()
			->backend_config->response_stats.increaseCode(code);

#ifdef CACHE_ENABLED
		if (service->cache_enabled) {
			CacheManager::handleResponse(stream, service);
		}
#endif
		http_manager::setBackendCookie(service, stream);
		setStrictTransportSecurity(service, stream);
#if ON_FLY_COMRESSION
		if (!this->is_https_listener) {
			Compression::applyCompression(service, stream);
		}
#endif
		stream->logSuccess();

#if ENABLE_QUICK_RESPONSE
		onClientWriteEvent(stream);
#else
		stream->client_connection.enableWriteEvent();
#endif
	}
}

void StreamManager::onConnectTimeoutEvent(int fd)
{
	DEBUG_COUNTER_HIT(debug__::on_backend_connect_timeout);
#if USE_TIMER_FD_TIMEOUT
	HttpStream *stream = timers_set[fd];
#else
	HttpStream *stream = bck_streams_set[fd];
#endif
	if (stream == nullptr) {
		zcu_log_print(LOG_DEBUG, "%s():%d: stream null pointer",
			      __FUNCTION__, __LINE__);
		deleteFd(fd);
		::close(fd);
		return;
	}
	if (stream->hasStatus(STREAM_STATUS::BCK_CONN_PENDING)
#if USE_TIMER_FD_TIMEOUT
	    && stream->timer_fd.isTriggered()
#endif
	) {

		streamLogNoResponse(
			stream, "onConnectTimeoutEvent after %d seconds",
			stream->backend_connection.getBackend()->conn_timeout);
		onBackendConnectionError(stream);
		return;
	}
}

void StreamManager::onRequestTimeoutEvent(int fd)
{
	DEBUG_COUNTER_HIT(debug__::on_request_timeout);
#if USE_TIMER_FD_TIMEOUT
	HttpStream *stream = timers_set[fd];
#else
	HttpStream *stream = cl_streams_set[fd];
#endif
	if (stream == nullptr) {
		deleteFd(fd);
		::close(fd);
		return;
	}

#if USE_TIMER_FD_TIMEOUT
	if (stream->timer_fd.isTriggered()) {
#endif
		streamLogNoResponse(
			stream, "onRequestTimeoutEvent after %d seconds",
			stream->service_manager->listener_config_->to);
		clearStream(stream);
#if USE_TIMER_FD_TIMEOUT
	}
#endif
}

void StreamManager::onResponseTimeoutEvent(int fd)
{
	DEBUG_COUNTER_HIT(debug__::on_response_timeout);
#if USE_TIMER_FD_TIMEOUT
	HttpStream *stream = timers_set[fd];
#else
	HttpStream *stream = bck_streams_set[fd];
#endif
	if (stream == nullptr) {
		zcu_log_print(LOG_DEBUG, "%s():%d: stream null pointer",
			      __FUNCTION__, __LINE__);
		deleteFd(fd);
		::close(fd);
		return;
	}
	auto &listener_config_ = *stream->service_manager->listener_config_;

	streamLogMessage(
		stream, "timeout on backend response after %d seconds",
		stream->backend_connection.getBackend()->response_timeout);

#if USE_TIMER_FD_TIMEOUT
	if (stream->timer_fd.isTriggered()) {
#endif
		if (!stream->response.getHeaderSent())
			http_manager::replyError(
				stream, http::Code::GatewayTimeout,
				http::reasonPhrase(http::Code::GatewayTimeout),
				http::reasonPhrase(http::Code::GatewayTimeout),
				stream->client_connection,
				listener_config_.response_stats);
		else
			streamLogNoResponse(
				stream,
				"timeout (%d seconds) reached in the backend response",
				stream->backend_connection.getBackend()
					->response_timeout);

		this->clearStream(stream);
#if USE_TIMER_FD_TIMEOUT
	}
#endif
}

void StreamManager::onSignalEvent([[maybe_unused]] int fd)
{
	// TODO::IMPLEMENET
}

void StreamManager::setStreamBackend(HttpStream *stream)
{
	auto service = static_cast<Service *>(stream->request.getService());
	this->stopTimeOut(stream->client_connection.getFileDescriptor());

	auto &listener_config_ = *stream->service_manager->listener_config_;
	if (service == nullptr) {
		service = stream->service_manager->getService(stream->request);
		if (service == nullptr) {
			http_manager::replyError(
				stream, http::Code::ServiceUnavailable,
				validation::request_result_reason.at(
					validation::REQUEST_RESULT::
						SERVICE_NOT_FOUND),
				listener_config_.err503,
				stream->client_connection,
				listener_config_.response_stats);
			this->clearStream(stream);
			return;
		}
		stream->request.setService(service);
	}

	if (stream->backend_connection.connection_retries >=
	    service->getBackendSetSize()) {
		// No backend available
		//streamLogMessage(stream,"service connection limit reached");
		http_manager::replyError(
			stream, http::Code::ServiceUnavailable,
			validation::request_result_reason.at(
				validation::REQUEST_RESULT::BACKEND_NOT_FOUND),
			listener_config_.err503, stream->client_connection,
			listener_config_.response_stats);
		this->clearStream(stream);
		return;
	}
	if (stream->backend_connection.getFileDescriptor() > 0) { //TODO::
		if (stream->hasStatus(STREAM_STATUS::BCK_CONN_PENDING)) {
			stream->backend_connection.getBackend()
				->decreaseConnTimeoutAlive();
		} else {
			stream->backend_connection.getBackend()
				->decreaseConnection();
		}
		deleteFd(stream->backend_connection.getFileDescriptor());
		bck_streams_set[stream->backend_connection.getFileDescriptor()] =
			nullptr;
		bck_streams_set.erase(
			stream->backend_connection.getFileDescriptor());
		stream->backend_connection.closeConnection();
	}
	stream->backend_connection.reset();
	auto bck =
		service->getBackend(stream->client_connection, stream->request);
	if (bck == nullptr) {
		// No backend available
		http_manager::replyError(
			stream, http::Code::ServiceUnavailable,
			validation::request_result_reason.at(
				validation::REQUEST_RESULT::BACKEND_NOT_FOUND),
			listener_config_.err503, stream->client_connection,
			listener_config_.response_stats);
		this->clearStream(stream);
		return;
	} else {
		// update log info
		IO::IO_OP op_state;
		stream->backend_connection.reset();
		stream->response.reset_parser();
		streamLogMessage(stream, "RETRY \"%s\" -> %s",
				 stream->request.http_message_str.data(),
				 bck->address.c_str());

		switch (bck->backend_type) {
		case BACKEND_TYPE::REMOTE: {
			stream->backend_connection.setBackend(bck);
			Time::getTime(stream->backend_connection.time_start);
			stream->status |= helper::to_underlying(
				STREAM_STATUS::BCK_CONN_PENDING);
			op_state = stream->backend_connection.doConnect(
				*bck->address_info, bck->conn_timeout, true,
				bck->nf_mark);
			switch (op_state) {
			case IO::IO_OP::OP_ERROR: {
				streamLogMessage(
					stream,
					"OP_ERROR error connecting to the backend %s",
					bck->address.data());
				onBackendConnectionError(stream);
				return;
			}
			case IO::IO_OP::OP_IN_PROGRESS: {
				stream->status |= helper::to_underlying(
					STREAM_STATUS::BCK_CONN_PENDING);
#if USE_TIMER_FD_TIMEOUT
				stream->timer_fd.set(bck->conn_timeout * 1000);
				addFd(stream->timer_fd.getFileDescriptor(),
				      EVENT_TYPE::READ_ONESHOT,
				      EVENT_GROUP::CONNECT_TIMEOUT);
#else
				setTimeOut(stream->backend_connection
						   .getFileDescriptor(),
					   TIMEOUT_TYPE::SERVER_WRITE_TIMEOUT,
					   bck->conn_timeout);
#endif
				stream->backend_connection.getBackend()
					->increaseConnTimeoutAlive();
			} break;
			case IO::IO_OP::OP_SUCCESS: {
				DEBUG_COUNTER_HIT(debug__::on_backend_connect);
				if (stream->backend_connection.getBackend()
					    ->isConnectionLimit()) {
					http_manager::replyError(
						stream,
						http::Code::ServiceUnavailable,
						validation::request_result_reason
							.at(validation::REQUEST_RESULT::
								    BACKEND_NOT_FOUND),
						listener_config_.err503,
						stream->client_connection,
						listener_config_.response_stats);
					this->clearStream(stream);
				}
				stream->backend_connection.getBackend()
					->increaseConnection();
				break;
			}
			}
			bck_streams_set[stream->backend_connection
						.getFileDescriptor()] = stream;
			stream->backend_connection.enableEvents(
				this, EVENT_TYPE::WRITE, EVENT_GROUP::SERVER);
			if (stream->backend_connection.getBackend()->nf_mark >
			    0)
				zcu_soc_set_somarkoption(
					stream->backend_connection
						.getFileDescriptor(),
					stream->backend_connection.getBackend()
						->nf_mark);
			// Rewrite destination
			if (stream->request.add_destination_header) {
				// remove previously added headers
				stream->request.removeHeader(
					http::HTTP_HEADER_NAME::DESTINATION);
				std::string header_value =
					stream->backend_connection.getBackend()
							->isHttps() ?
						      "https://" :
						      "http://";
				header_value += stream->backend_connection
							.getPeerAddress();
				header_value += ':';
				header_value += stream->request.path;
				stream->request.addHeader(
					http::HTTP_HEADER_NAME::DESTINATION,
					header_value);
			}
			if (!stream->request.host_header_found) {
				stream->request.removeHeader(
					http::HTTP_HEADER_NAME::HOST);
				std::string header_value = "";
				header_value +=
					stream->backend_connection.getBackend()
						->address;
				header_value += ':';
				header_value += std::to_string(
					stream->backend_connection.getBackend()
						->port);
				stream->request.addHeader(
					http::HTTP_HEADER_NAME::HOST,
					header_value);
			}
			/* After setting the backend and the service in the first request,
				 * pin the connection if the PinnedConnection service config
				 * parameter is true. Note: The first request must be HTTP. */
			if (service->service_config.pinned_connection) {
				stream->options |= helper::to_underlying(
					STREAM_OPTION::PINNED_CONNECTION);
			}
			break;
		}

		case BACKEND_TYPE::EMERGENCY_SERVER:

			break;
		case BACKEND_TYPE::REDIRECT: {
			if (http_manager::replyRedirect(*stream, *bck))
				clearStream(stream);
			return;
		}
		case BACKEND_TYPE::CACHE_SYSTEM:
			break;
		}
	}
}

void StreamManager::onServerWriteEvent(HttpStream *stream)
{
	DEBUG_COUNTER_HIT(debug__::on_send_request);
	auto &listener_config_ = *stream->service_manager->listener_config_;

	streamLogDebug(stream, "");

	int fd = stream->backend_connection.getFileDescriptor();
	// Send client request to backend server
#if USE_TIMER_FD_TIMEOUT
	this->deleteFd(stream->timer_fd.getFileDescriptor());
	stream->timer_fd.unset();
#else
	stopTimeOut(fd);
#endif
	if (stream->hasStatus(STREAM_STATUS::BCK_CONN_PENDING)) {
		DEBUG_COUNTER_HIT(debug__::on_backend_connect);
		stream->clearStatus(STREAM_STATUS::BCK_CONN_PENDING);
		stream->backend_connection.getBackend()
			->decreaseConnTimeoutAlive();

		if (stream->backend_connection.getBackend()
			    ->isConnectionLimit()) {
			http_manager::replyError(
				stream, http::Code::ServiceUnavailable,
				validation::request_result_reason.at(
					validation::REQUEST_RESULT::
						BACKEND_NOT_FOUND),
				listener_config_.err503,
				stream->client_connection,
				listener_config_.response_stats);
			clearStream(stream);
			return;
		}
		stream->backend_connection.getBackend()->increaseConnection();
		stream->backend_connection.getBackend()->setAvgConnTime(
			stream->backend_connection.time_start);
	}
	/*Check if the buffer has data to be send */
	if (stream->client_connection.buffer_size == 0) {
		stream->client_connection.enableReadEvent();
		stream->backend_connection.enableReadEvent();
		return;
	}
	/* If the connection is pinned or we have content length remaining to send
	 * , then we need to write the buffer content without
	 * applying any kind of modification. */
	IO::IO_RESULT result = IO::IO_RESULT::ERROR;
	if (stream->hasOption(STREAM_OPTION::PINNED_CONNECTION) ||
	    stream->request.hasPendingData()) {
		size_t written = 0;

		if (stream->backend_connection.getBackend()->isHttps()) {
			result = ssl::SSLConnectionManager::handleWrite(
				stream->backend_connection,
				stream->client_connection, written);
		} else {
			if (stream->client_connection.buffer_size > 0)
				result = stream->client_connection.writeTo(
					stream->backend_connection
						.getFileDescriptor(),
					written);
#if ENABLE_ZERO_COPY
			else if (stream->client_connection.splice_pipe.bytes >
				 0)
				result = stream->client_connection.zeroWrite(
					stream->backend_connection
						.getFileDescriptor(),
					stream->request);
#endif
		}

		switch (result) {
		case IO::IO_RESULT::SSL_HANDSHAKE_ERROR:
		case IO::IO_RESULT::SSL_NEED_HANDSHAKE: {
			if (!ssl::SSLConnectionManager::handleHandshake(
				    stream->backend_connection.getBackend()
					    ->ctx.get(),
				    stream->backend_connection, true)) {
				streamLogMessage(
					stream,
					"SSL_NEED_HANDSHAKE, error while the handshake with the backend");
				http_manager::replyError(
					stream, http::Code::ServiceUnavailable,
					http::reasonPhrase(
						http::Code::ServiceUnavailable),
					listener_config_.err503,
					stream->client_connection,
					listener_config_.response_stats);
				clearStream(stream);
			}
			if (stream->backend_connection.ssl_connected) {
				stream->backend_connection.enableWriteEvent();
			}
			return;
		}
		case IO::IO_RESULT::FD_CLOSED:
		case IO::IO_RESULT::CANCELLED:
		case IO::IO_RESULT::FULL_BUFFER:
		case IO::IO_RESULT::ERROR:
		default:
			streamLogNoResponse(
				stream, "error sending request to the backend");
			clearStream(stream);
			return;
		case IO::IO_RESULT::SUCCESS:
		case IO::IO_RESULT::DONE_TRY_AGAIN:
			break;
		}
		if (!stream->hasOption(STREAM_OPTION::PINNED_CONNECTION)) {
			if (stream->request.chunked_status ==
				    http::CHUNKED_STATUS::CHUNKED_LAST_CHUNK &&
			    stream->client_connection.buffer_size == 0) {
				stream->request.reset_parser();
			} else if (stream->request.message_bytes_left > 0) {
				stream->request.message_bytes_left -= written;
				if (stream->request.message_bytes_left == 0) {
					stream->request.reset_parser();
				}
			}
		}
		if (stream->client_connection.buffer_size > 0) {
			stream->client_connection.buffer_offset += written;
			stream->backend_connection.enableWriteEvent();
			return;
		}
		stream->client_connection.buffer_offset = 0;
		stream->backend_connection.enableReadEvent();
		stream->client_connection.enableReadEvent();
		if (stream->hasStatus(STREAM_STATUS::CL_READ_PENDING)) {
#if DEBUG_ZCU_LOG
			HttpStream::debugBufferData(__FUNCTION__, __LINE__,
						    stream,
						    "ClientW-ReadPending",
						    "WROTE REQ PENDING ");
#endif
			//stream->client_connection.enableReadEvent();
			onRequestEvent(
				stream->client_connection.getFileDescriptor());
		}
		return;
	}

	if (stream->backend_connection.getBackend()->isHttps()) {
		result = ssl::SSLConnectionManager::handleDataWrite(
			stream->backend_connection, stream->client_connection,
			stream->request);
	} else {
		result = stream->client_connection.writeTo(
			stream->backend_connection, stream->request);
	}

	switch (result) {
	case IO::IO_RESULT::SSL_HANDSHAKE_ERROR:
	case IO::IO_RESULT::SSL_NEED_HANDSHAKE: {
		stream->backend_connection.server_name =
			stream->client_connection.server_name;
		if (!ssl::SSLConnectionManager::handleHandshake(
			    stream->backend_connection.getBackend()->ctx.get(),
			    stream->backend_connection, true)) {
			streamLogNoResponse(
				stream,
				"error while the handshake witht the backend");
			clearStream(stream);
			return;
		}
		if (!stream->backend_connection.ssl_connected) {
			stream->backend_connection.enableReadEvent();
			return;
		} else {
			stream->backend_connection.enableWriteEvent();
		}
		return;
	}
	case IO::IO_RESULT::FD_CLOSED:
	case IO::IO_RESULT::CANCELLED:
	case IO::IO_RESULT::FULL_BUFFER:
	case IO::IO_RESULT::ERROR:
		streamLogNoResponse(stream, "error sending request to backend");
		clearStream(stream);
		return;
	case IO::IO_RESULT::SUCCESS:
	case IO::IO_RESULT::DONE_TRY_AGAIN:
		if (!stream->request.getHeaderSent()) {
			stream->backend_connection.enableWriteEvent();
			return;
		}
		break;
	default:
		streamLogNoResponse(stream,
				    "error sending data to backend server");
		clearStream(stream);
		return;
	}
#if USE_TIMER_FD_TIMEOUT
	stream->timer_fd.set(
		stream->backend_connection.getBackend()->response_timeout *
		1000);
	addFd(stream->timer_fd.getFileDescriptor(), EVENT_TYPE::READ_ONESHOT,
	      EVENT_GROUP::RESPONSE_TIMEOUT);
#else
	setTimeOut(stream->backend_connection.getFileDescriptor(),
		   TIMEOUT_TYPE::SERVER_READ_TIMEOUT,
		   stream->backend_connection.getBackend()->response_timeout);
#endif
#if DEBUG_ZCU_LOG
	streamLogDebug(stream,
		       "OUT buffer size: %8lu\tContent-length: %lu\tleft: "
		       "%lu\tIO: %s",
		       stream->client_connection.buffer_size,
		       stream->request.content_length,
		       stream->request.message_bytes_left,
		       IO::getResultString(result).data());
#endif
	Time::getTime(stream->backend_connection.time_start);
	stream->client_connection.enableReadEvent();
	stream->backend_connection.enableReadEvent();
	stream->clearStatus(STREAM_STATUS::REQUEST_PENDING);
	if (stream->hasStatus(STREAM_STATUS::CL_READ_PENDING)) {
#if DEBUG_ZCU_LOG
		HttpStream::debugBufferData(__FUNCTION__, __LINE__, stream,
					    "ClientW-ReadPending",
					    "WROTE REQ PENDING ");
#endif
		onRequestEvent(stream->client_connection.getFileDescriptor());
	}
}

void StreamManager::onClientWriteEvent(HttpStream *stream)
{
	if (stream == nullptr)
		return;

	streamLogDebug(stream, "");

	DEBUG_COUNTER_HIT(debug__::on_send_response);
	auto &listener_config_ = *stream->service_manager->listener_config_;

#if DEBUG_ZCU_LOG
	streamLogDebug(stream,
		       "IN\tbuffer size: %8lu\tContent-length: %lu\tleft: %lu",
		       stream->backend_connection.buffer_size,
		       stream->response.content_length,
		       stream->response.message_bytes_left);
	auto buffer_size_in = stream->backend_connection.buffer_size;
#endif
#if USE_TIMER_FD_TIMEOUT
	this->deleteFd(stream->timer_fd.getFileDescriptor());
	stream->timer_fd.unset();
#else
	stopTimeOut(stream->client_connection.getFileDescriptor());
#endif
	IO::IO_RESULT result = IO::IO_RESULT::ERROR;

	/* If the connection is pinned, then we need to write the buffer
	 * content without applying any kind of modification. */
	if (stream->hasOption(STREAM_OPTION::PINNED_CONNECTION) ||
	    stream->response.hasPendingData()) {
		size_t written = 0;

		if (stream->service_manager->is_https_listener) {
			result = ssl::SSLConnectionManager::handleWrite(
				stream->client_connection,
				stream->backend_connection, written);
		} else {
			if (stream->backend_connection.buffer_size > 0)
				result = stream->backend_connection.writeTo(
					stream->client_connection
						.getFileDescriptor(),
					written);
#if ENABLE_ZERO_COPY
			else if (stream->backend_connection.splice_pipe.bytes >
				 0)
				result = stream->backend_connection.zeroWrite(
					stream->client_connection
						.getFileDescriptor(),
					stream->response);
#endif
		}

		switch (result) {
		case IO::IO_RESULT::SSL_HANDSHAKE_ERROR:
		case IO::IO_RESULT::SSL_NEED_HANDSHAKE: {
			if (!ssl::SSLConnectionManager::handleHandshake(
				    *stream->service_manager->ssl_context,
				    stream->client_connection)) {
				streamLogNoResponse(
					stream,
					"error in the handshake with the client");
				clearStream(stream);
			}
			if (stream->client_connection.ssl_connected) {
				stream->backend_connection.server_name =
					stream->client_connection.server_name;
				onRequestEvent(stream->client_connection
						       .getFileDescriptor());
				return;
			}
			return;
		}
		case IO::IO_RESULT::ZERO_DATA:
		case IO::IO_RESULT::SUCCESS:
		case IO::IO_RESULT::DONE_TRY_AGAIN:
			break;
		case IO::IO_RESULT::FD_CLOSED:
		case IO::IO_RESULT::CANCELLED:
		case IO::IO_RESULT::FULL_BUFFER:
		case IO::IO_RESULT::ERROR:
		default:
			auto error = IO::getResultString(result);
			HttpStream::debugBufferData(__FUNCTION__, __LINE__,
						    stream, "onServerW-ERROR",
						    error.data());
			streamLogMessage(stream, "Error sending response: %s",
					 error.data());
			clearStream(stream);
			return;
		}
		if (!stream->hasOption(STREAM_OPTION::PINNED_CONNECTION)) {
			if (stream->response.chunked_status ==
				    http::CHUNKED_STATUS::CHUNKED_LAST_CHUNK &&
			    stream->backend_connection.buffer_size == 0) {
				stream->response.reset_parser();
			} else if (stream->response.message_bytes_left > 0) {
				stream->response.message_bytes_left -= written;
				if (stream->response.message_bytes_left <= 0)
					stream->response.reset_parser();
			}
		}
		if (stream->backend_connection.buffer_size > 0) {
			stream->backend_connection.buffer_offset += written;
			stream->client_connection.enableWriteEvent();
			return;
		}
		stream->client_connection.enableReadEvent();

		if (stream->hasStatus(STREAM_STATUS::BCK_READ_PENDING)) {
#if DEBUG_ZCU_LOG
			HttpStream::debugBufferData(__FUNCTION__, __LINE__,
						    stream,
						    "ClientW-ReadPending",
						    "WROTE RESP PENDING ");
#endif
			//stream->backend_connection.enableReadEvent();
			onResponseEvent(
				stream->backend_connection.getFileDescriptor());
			return;
		}
		if (stream->hasStatus(STREAM_STATUS::CLOSE_CONNECTION)) {
			streamLogDebug(stream, "closing connection");
			clearStream(stream);
			return;
		}
		stream->backend_connection.buffer_offset = 0;
		stream->backend_connection.enableReadEvent();
		return;
	}

	if (stream->backend_connection.buffer_size == 0
#ifdef CACHE_ENABLED
	    && !stream->response.isCached()
#endif
	)
		return;

	if (stream->service_manager->is_https_listener) {
		result = ssl::SSLConnectionManager::handleDataWrite(
			stream->client_connection, stream->backend_connection,
			stream->response);
	} else {
		result = stream->backend_connection.writeTo(
			stream->client_connection, stream->response);
	}

	switch (result) {
	case IO::IO_RESULT::SSL_HANDSHAKE_ERROR:
	case IO::IO_RESULT::SSL_NEED_HANDSHAKE: {
		if (!ssl::SSLConnectionManager::handleHandshake(
			    *stream->service_manager->ssl_context,
			    stream->client_connection)) {
			if ((ERR_GET_REASON(ERR_peek_error()) ==
			     SSL_R_HTTP_REQUEST) &&
			    (ERR_GET_LIB(ERR_peek_error()) == ERR_LIB_SSL)) {
				/* the client speaks plain HTTP on our HTTPS port */
				streamLogMessage(
					stream,
					"the client sent a plain HTTP message to an SSL port");
				if (listener_config_.nossl_redir > 0) {
					if (http_manager::replyRedirect(
						    listener_config_.nossl_redir,
						    listener_config_.nossl_url,
						    *stream))
						clearStream(stream);
					return;
				} else {
					http_manager::replyError(
						stream,
						listener_config_.codenossl,
						http::reasonPhrase(
							listener_config_
								.codenossl),
						listener_config_.errnossl,
						stream->client_connection,
						listener_config_.response_stats);
				}
			} else {
				streamLogMessage(
					stream,
					"fd: %d:%d error in the client while the handshake",
					stream->client_connection
						.getFileDescriptor(),
					stream->backend_connection
						.getFileDescriptor());
			}
			clearStream(stream);
			return;
		}
		if (stream->client_connection.ssl_connected) {
			DEBUG_COUNTER_HIT(debug__::on_handshake);
			httpsHeaders(stream, listener_config_.clnt_check);
			stream->backend_connection.server_name =
				stream->client_connection.server_name;
		}
		return;
	}
	case IO::IO_RESULT::FD_CLOSED:
	case IO::IO_RESULT::CANCELLED:
	case IO::IO_RESULT::FULL_BUFFER:
	case IO::IO_RESULT::ERROR:
		streamLogNoResponse(stream, "error sending response: %s",
				    IO::getResultString(result).data());
		clearStream(stream);
		return;
	case IO::IO_RESULT::SUCCESS:
	case IO::IO_RESULT::DONE_TRY_AGAIN:
		if (!stream->response.getHeaderSent()) {
			// TODO:: retry with left headers data in response.
			stream->client_connection.enableWriteEvent();
			return;
		}
		break;
	default:
		streamLogNoResponse(
			stream,
			"fd: %d:%d %.*s Error sending response IN\tbuffer size: "
			"%8lu\tContent-length: %lu\tleft: %lu "
			"header_sent: %s chunk_size_left: %d IO RESULT: %s CH= %s",
			stream->client_connection.getFileDescriptor(),
			stream->backend_connection.getFileDescriptor(),
			stream->request.http_message_str.data(),
			stream->backend_connection.buffer_size,
			stream->response.content_length,
			stream->response.message_bytes_left,
			stream->response.getHeaderSent() ? "true" : "false",
			stream->response.chunk_size_left,
			IO::getResultString(result).data(),
			stream->response.chunked_status !=
					CHUNKED_STATUS::CHUNKED_DISABLED ?
				      "T" :
				      "F");
		clearStream(stream);
		return;
	}
#if DEBUG_ZCU_LOG
	if (stream->backend_connection.buffer_size != 0)
		streamLogDebug(
			stream,
			"OUT EAGAIN  %s buffer size: %lu > %8lu \tContent-length: "
			"%lu\tleft: "
			"%lu\tIO: %s",
			stream->request.http_message_str.data(),
			stream->backend_connection.buffer_size,
			stream->response.content_length,
			stream->response.message_bytes_left,
			IO::getResultString(result).data());
#endif
	if (stream->request.upgrade_header &&
	    stream->request.connection_header_upgrade &&
	    stream->response.http_status_code == 101) {
		stream->options |=
			helper::to_underlying(STREAM_OPTION::PINNED_CONNECTION);
		std::string upgrade_header_value;
		stream->request.getHeaderValue(http::HTTP_HEADER_NAME::UPGRADE,
					       upgrade_header_value);
		auto it = http::http_info::upgrade_protocols.find(
			upgrade_header_value);
		if (it != http::http_info::upgrade_protocols.end()) {
			switch (it->second) {
			case UPGRADE_PROTOCOLS::NONE:
				break;
			case UPGRADE_PROTOCOLS::WEBSOCKET:
				stream->options |= helper::to_underlying(
					STREAM_OPTION::WS);
				break;
			case UPGRADE_PROTOCOLS::H2C:
				stream->options |= helper::to_underlying(
					STREAM_OPTION::H2C);
				break;
			case UPGRADE_PROTOCOLS::TLS:
				break;
			}
		}
	}

	if (stream->backend_connection.buffer_size > 0) {
		stream->client_connection.enableWriteEvent();
		return;
	}
	stream->clearStatus(STREAM_STATUS::RESPONSE_PENDING);
	stream->client_connection.enableReadEvent();
	if (stream->hasStatus(STREAM_STATUS::BCK_READ_PENDING)) {
#if DEBUG_ZCU_LOG
		HttpStream::debugBufferData(__FUNCTION__, __LINE__, stream,
					    "ClientW-ReadPending", "PENDING ");
#endif
		//stream->backend_connection.enableReadEvent();
		onResponseEvent(stream->backend_connection.getFileDescriptor());
		return;
	}
	if (stream->hasStatus(STREAM_STATUS::CLOSE_CONNECTION)) {
		streamLogDebug(stream, "the writing in the client finished");
		clearStream(stream);
		return;
	}
#ifdef CACHE_ENABLED
	if (!stream->response.isCached())
#endif
		setTimeOut(stream->backend_connection.getFileDescriptor(),
			   TIMEOUT_TYPE::SERVER_READ_TIMEOUT,
			   stream->backend_connection.getBackend()
				   ->response_timeout);
	stream->backend_connection.enableReadEvent();
}

bool StreamManager::registerListener(
	std::weak_ptr<ServiceManager> service_manager)
{
	auto &listener_config = service_manager.lock()->listener_config_;
	auto address = zcu_net_get_address(listener_config->address,
					   listener_config->port);
	listener_config->addr_info = address.release();
	int listen_fd = Connection::listen(*listener_config->addr_info);

	if (listen_fd > 0) {
		service_manager_set[listen_fd] = service_manager;
		return handleAccept(listen_fd);
	}
	return false;
}

/** Clears the HttpStream. It deletes all the timers and events. Finally,
 * deletes the HttpStream.
 */
void StreamManager::clearStream(HttpStream *stream)
{
	if (stream == nullptr) {
		return;
	}
	streamLogDebug(stream, "clearStream");

#ifdef CACHE_ENABLED
	CacheManager::handleStreamClose(stream);
#endif
#if USE_TIMER_FD_TIMEOUT
	if (stream->timer_fd.getFileDescriptor() > 0) {
		deleteFd(stream->timer_fd.getFileDescriptor());
		stream->timer_fd.unset();
		timers_set[stream->timer_fd.getFileDescriptor()] = nullptr;
		timers_set.erase(stream->timer_fd.getFileDescriptor());
#if DEBUG_ZCU_LOG
		clear_timer++;
#endif
	}
#endif
	if (stream->client_connection.getFileDescriptor() > 0) {
		deleteFd(stream->client_connection.getFileDescriptor());
		cl_streams_set[stream->client_connection.getFileDescriptor()] =
			nullptr;
		cl_streams_set.erase(
			stream->client_connection.getFileDescriptor());
		stream->client_connection.closeConnection();
#if DEBUG_ZCU_LOG
		clear_client++;
#endif
	}
	if (stream->backend_connection.getFileDescriptor() > 0) {
		if (stream->hasStatus(STREAM_STATUS::BCK_CONN_PENDING)) {
			stream->backend_connection.getBackend()
				->decreaseConnTimeoutAlive();
		} else {
			stream->backend_connection.getBackend()
				->decreaseConnection();
		}
#if DEBUG_ZCU_LOG
		clear_backend++;
#endif
		deleteFd(stream->backend_connection.getFileDescriptor());
		bck_streams_set[stream->backend_connection.getFileDescriptor()] =
			nullptr;
		bck_streams_set.erase(
			stream->backend_connection.getFileDescriptor());
		stream->backend_connection.closeConnection();
	}
#if DEBUG_ZCU_LOG
	clear_stream++;
#endif
	DEBUG_COUNTER_HIT(debug__::on_clear_stream);
	stream->service_manager->conns_stats.established_connection--;
	delete stream;
}

void StreamManager::onClientDisconnect(HttpStream *stream)
{
	if (stream == nullptr)
		return;
	DEBUG_COUNTER_HIT(debug__::on_client_disconnect);
	streamLogDebug(stream, "Client Disconnected");
	clearStream(stream);
}

std::string StreamManager::handleTask(ctl::CtlTask &task)
{
	if (!isHandler(task))
		return JSON_OP_RESULT::ERROR;

	if (task.command == ctl::CTL_COMMAND::EXIT) {
		zcu_log_print(LOG_DEBUG, "%s():%d: exit command received",
			      __FUNCTION__, __LINE__);
		stop();

		return JSON_OP_RESULT::OK;
	}
#if DEBUG_ZCU_LOG
	switch (task.subject) {
	case ctl::CTL_SUBJECT::DEBUG: {
		std::unique_ptr<JsonObject> root{ new JsonObject() };
		std::unique_ptr<JsonObject> status{ new JsonObject() };
		status->emplace("HttpSteam", std::make_unique<JsonDataValue>(
						     cl_streams_set.size()));
		status->emplace("clear_stream",
				std::make_unique<JsonDataValue>(clear_stream));
		status->emplace("clear_client",
				std::make_unique<JsonDataValue>(clear_client));
		status->emplace("clear_backend",
				std::make_unique<JsonDataValue>(clear_backend));
		status->emplace("clear_timer",
				std::make_unique<JsonDataValue>(clear_timer));
		root->emplace("W_" + std::to_string(this->getWorkerId()),
			      std::move(status));
		return root->stringify();
	}
	}
#endif
	return JSON_OP_RESULT::ERROR;
}

bool StreamManager::isHandler(ctl::CtlTask &task)
{
	return task.target == ctl::CTL_HANDLER_TYPE::ALL ||
	       task.target == ctl::CTL_HANDLER_TYPE::STREAM_MANAGER;
}

void StreamManager::onServerDisconnect(HttpStream *stream)
{
	if (stream == nullptr)
		return;
	DEBUG_COUNTER_HIT(debug__::on_backend_disconnect);
	auto &listener_config_ = *stream->service_manager->listener_config_;
	// update log info
	//~ StreamDataLogger logger(stream, listener_config_);
#if DEBUG_ZCU_LOG
	HttpStream::debugBufferData(__FUNCTION__, __LINE__, stream,
				    "onServerDisconnect", "DISCONNECT");
#endif

	if (stream->backend_connection.getFileDescriptor() > 0 &&
	    !stream->hasStatus(STREAM_STATUS::BCK_READ_PENDING)) {
#if DEBUG_ZCU_LOG
		clear_backend++;
#endif
		deleteFd(stream->backend_connection.getFileDescriptor());
		bck_streams_set[stream->backend_connection.getFileDescriptor()] =
			nullptr;
		bck_streams_set.erase(
			stream->backend_connection.getFileDescriptor());
		stream->backend_connection.closeConnection();
	}

	if (stream->backend_connection.getBackend() != nullptr &&
	    stream->hasStatus(STREAM_STATUS::BCK_CONN_PENDING)) {
		onBackendConnectionError(stream);
		return;
	} else {
		if (stream->backend_connection.getBackend() != nullptr)
			stream->backend_connection.getBackend()
				->decreaseConnection();
		if (stream->backend_connection.buffer_size > 0
#if ENABLE_ZERO_COPY
		    || stream->backend_connection.splice_pipe.bytes > 0
#endif
		) {
			stream->status |= helper::to_underlying(
				STREAM_STATUS::CLOSE_CONNECTION);
			stream->client_connection.enableWriteEvent();
			return;
		} else if (!stream->response.getHeaderSent()) {
			streamLogMessage(stream, "Backend disconnected");
			http_manager::replyError(
				stream, http::Code::InternalServerError,
				http::reasonPhrase(
					http::Code::InternalServerError),
				listener_config_.err503,
				stream->client_connection,
				listener_config_.response_stats);
		}
	}
	clearStream(stream);
}

void StreamManager::stopListener(int listener_id, bool cut_connection)
{
	for (const auto &lc : service_manager_set) {
		auto spt = lc.second.lock();
		if (spt && listener_id == spt->id) {
			this->stopAccept(lc.first);

			::close(lc.first);
		}
	}
	for (auto it = service_manager_set.begin();
	     it != service_manager_set.end();) {
		auto spt = it->second.lock();
		if (spt && listener_id == spt->id) {
			this->stopAccept(it->first);
			::close(it->first);
			//      it = listener_config_set.erase(it);
			break;
		} else {
			it++;
		}
	}
	if (cut_connection) {
		for (auto it = cl_streams_set.begin();
		     it != cl_streams_set.end();) {
			if (it->second->service_manager->id == listener_id) {
				auto item = it++;
				clearStream(item->second);
			} else
				it++;
		}
	}
}

#if USE_TIMER_FD_TIMEOUT == 0
void StreamManager::onTimeOut(int fd, TIMEOUT_TYPE type)
{
	switch (type) {
	case TIMEOUT_TYPE::SERVER_WRITE_TIMEOUT:
		onConnectTimeoutEvent(fd);
		break;
	case TIMEOUT_TYPE::CLIENT_READ_TIMEOUT:
		onRequestTimeoutEvent(fd);
		break;
	case TIMEOUT_TYPE::SERVER_READ_TIMEOUT:
		onResponseTimeoutEvent(fd);
		break;
	case TIMEOUT_TYPE::INACTIVE_TIMEOUT:
	case TIMEOUT_TYPE::CLIENT_WRITE_TIMEOUT:
		break;
	}
}
#endif

void StreamManager::onBackendConnectionError(HttpStream *stream)
{
	DEBUG_COUNTER_HIT(debug__::on_backend_connect_error);
	auto &listener_config_ = *stream->service_manager->listener_config_;

	stream->backend_connection.getBackend()->setStatus(
		BACKEND_STATUS::BACKEND_DOWN);
	zcu_log_print(
		LOG_NOTICE,
		"(%lx) BackEnd %s:%d dead (killed) in farm: '%s', service: '%s'",
		pthread_self(),
		stream->backend_connection.getBackend()->address.data(),
		stream->backend_connection.getBackend()->port,
		listener_config_.name.data(),
		stream->backend_connection.getBackend()
			->backend_config->srv_name.data());

	stream->backend_connection.getBackend()->decreaseConnTimeoutAlive();
	setStreamBackend(stream);

	//  // No backend available
	//  http_manager::replyError(stream,http::Code::ServiceUnavailable,
	//                           validation::request_result_reason.at(
	//                               validation::REQUEST_RESULT::BACKEND_NOT_FOUND),
	//                           listener_config_.err503,
	//                           stream->client_connection
	//                           listener_config_.response_stats);
	//  this->clearStream(stream);
}
