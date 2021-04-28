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
#include "backend.h"
#include "../../zcutils/zcutils.h"

Backend::Backend():status(BACKEND_STATUS::NO_BACKEND)
{
}

Backend::~Backend()
{
	if (address_info != nullptr) {
		::freeaddrinfo(address_info);
	}
}

std::string Backend::handleTask(ctl::CtlTask & task)
{
	if (!isHandler(task) || this->backend_type != BACKEND_TYPE::REMOTE)
		return "";
	zcu_log_print(LOG_DEBUG, "%s():%d: backend %d handling task",
			  __FUNCTION__, __LINE__, backend_id);
	if (task.command == ctl::CTL_COMMAND::GET) {
		switch (task.subject) {
		case ctl::CTL_SUBJECT::STATUS:{
				JsonObject status_;
				switch (this->status) {
				case BACKEND_STATUS::BACKEND_UP:
					status_.emplace(JSON_KEYS::STATUS,
							std::make_unique <
							JsonDataValue >
							(JSON_KEYS::STATUS_UP));
					break;
				case BACKEND_STATUS::BACKEND_DOWN:
					status_.emplace(JSON_KEYS::STATUS,
							std::make_unique <
							JsonDataValue >
							(JSON_KEYS::STATUS_DOWN));
					break;
				case BACKEND_STATUS::BACKEND_DISABLED:
					status_.emplace(JSON_KEYS::STATUS,
							std::make_unique <
							JsonDataValue >
							(JSON_KEYS::STATUS_DISABLED));
					break;
				default:
					status_.emplace(JSON_KEYS::STATUS,
							std::make_unique <
							JsonDataValue >
							(JSON_KEYS::UNKNOWN));
					break;
				}
				return status_.stringify();
			}
		case ctl::CTL_SUBJECT::WEIGHT:{
				JsonObject weight_;
				weight_.emplace(JSON_KEYS::WEIGHT,
						std::make_unique <
						JsonDataValue >
						(this->weight));
				return weight_.stringify();
			}
		default:
			auto backend_status = this->getBackendJson();
			if (backend_status != nullptr)
				return backend_status->stringify();
			return JSON_OP_RESULT::ERROR;
		}
	}
	else if (task.command == ctl::CTL_COMMAND::UPDATE) {
		auto status_object = JsonParser::parse(task.data);
		if (status_object == nullptr)
			return JSON_OP_RESULT::ERROR;
		switch (task.subject) {
		case ctl::CTL_SUBJECT::CONFIG:
			// TODO:: update  config (timeouts, headers)
			break;
		case ctl::CTL_SUBJECT::STATUS:{
				if (status_object->
				    at(JSON_KEYS::STATUS)->isValue()) {
					auto value =
						dynamic_cast <
						JsonDataValue *
						>(status_object->at
						  (JSON_KEYS::STATUS).get())
						->string_value;
					if (value == JSON_KEYS::STATUS_ACTIVE
					    || value ==
					    JSON_KEYS::STATUS_UP) {
						this->status =
							BACKEND_STATUS::BACKEND_UP;
					}
					else if (value ==
						 JSON_KEYS::STATUS_DOWN) {
						this->status =
							BACKEND_STATUS::BACKEND_DOWN;
					}
					else if (value ==
						 JSON_KEYS::STATUS_DISABLED) {
						this->status =
							BACKEND_STATUS::BACKEND_DISABLED;
					}
					zcu_log_print(LOG_NOTICE,
							  "Set Backend %d %s",
							  backend_id,
							  value.c_str());
					return JSON_OP_RESULT::OK;
				}
				break;
			}
		case ctl::CTL_SUBJECT::WEIGHT:{
				if (status_object->
				    at(JSON_KEYS::WEIGHT)->isValue()) {
					auto value =
						dynamic_cast <
						JsonDataValue *
						>(status_object->at
						  (JSON_KEYS::WEIGHT).get())
						->number_value;
					this->weight =
						static_cast < int >(value);
					return JSON_OP_RESULT::OK;
				}
				return JSON_OP_RESULT::ERROR;
			}
		default:
			break;
		}
	}
	return "";
}

bool Backend::isConnectionLimit() {
	bool ret = (connection_limit > 0 && (connection_limit <= getEstablishedConn()) ) ? true : false;
	if (ret) {
		zcu_log_print(LOG_DEBUG,
			  "Connection limit %d hit in backend %d",
			  backend_id,
			  connection_limit );
	}
	return ret;
}


bool Backend::isHandler(ctl::CtlTask & task)
{
	return			/*task.target == ctl::CTL_HANDLER_TYPE::BACKEND && */
		(task.backend_id == this->backend_id
		 || task.backend_id == -1);
}

std::unique_ptr < JsonObject > Backend::getBackendJson()
{
	auto root = std::make_unique < JsonObject > ();
	root->emplace(JSON_KEYS::NAME,
		      std::make_unique < JsonDataValue > (this->name));
	root->emplace(JSON_KEYS::HTTPS,
		      std::make_unique < JsonDataValue > (this->isHttps()));
	root->emplace(JSON_KEYS::ID,
		      std::make_unique < JsonDataValue > (this->backend_id));
	root->emplace(JSON_KEYS::TYPE,
		      std::make_unique < JsonDataValue > (static_cast <
							  int
							  >
							  (this->backend_type)));
	if (this->backend_type != BACKEND_TYPE::REDIRECT) {
		root->emplace(JSON_KEYS::ADDRESS,
			      std::make_unique < JsonDataValue >
			      (this->address));
		root->emplace(JSON_KEYS::PORT,
			      std::make_unique < JsonDataValue >
			      (this->port));
		root->emplace(JSON_KEYS::WEIGHT,
			      std::make_unique < JsonDataValue >
			      (this->weight));
		root->emplace(JSON_KEYS::PRIORITY,
			      std::make_unique < JsonDataValue >
			      (this->priority));
		switch (this->status) {
		case BACKEND_STATUS::BACKEND_UP:
			root->emplace(JSON_KEYS::STATUS,
				      std::make_unique < JsonDataValue >
				      (JSON_KEYS::STATUS_ACTIVE));
			break;
		case BACKEND_STATUS::BACKEND_DOWN:
			root->emplace(JSON_KEYS::STATUS,
				      std::make_unique < JsonDataValue >
				      (JSON_KEYS::STATUS_DOWN));
			break;
		case BACKEND_STATUS::BACKEND_DISABLED:
			root->emplace(JSON_KEYS::STATUS,
				      std::make_unique < JsonDataValue >
				      (JSON_KEYS::STATUS_DISABLED));
			break;
		default:
			root->emplace(JSON_KEYS::STATUS,
				      std::make_unique < JsonDataValue >
				      (JSON_KEYS::UNKNOWN));
			break;
		}
		root->emplace(JSON_KEYS::CONNECTIONS,
			      std::make_unique < JsonDataValue >
				  (this->established_conn));
		root->emplace(JSON_KEYS::CONNECTION_LIMIT,
				  std::make_unique < JsonDataValue >
				  (this->connection_limit));
		root->emplace(JSON_KEYS::PENDING_CONNS,
			      std::make_unique < JsonDataValue >
			      (this->pending_connections));
		root->emplace(JSON_KEYS::RESPONSE_TIME,
			      std::make_unique < JsonDataValue >
			      (this->avg_response_time));
		root->emplace(JSON_KEYS::CONNECT_TIME,
			      std::make_unique < JsonDataValue >
			      (this->avg_conn_time));
		root->emplace(JSON_KEYS::CODE_200_HITS,
				  std::make_unique < JsonDataValue >
				  (this->response_stats.code_2xx));
		root->emplace(JSON_KEYS::CODE_300_HITS,
				  std::make_unique < JsonDataValue >
				  (this->response_stats.code_3xx));
		root->emplace(JSON_KEYS::CODE_400_HITS,
				  std::make_unique < JsonDataValue >
				  (this->response_stats.code_4xx));
		root->emplace(JSON_KEYS::CODE_500_HITS,
				  std::make_unique < JsonDataValue >
				  (this->response_stats.code_5xx));
	}
	return root;
}

void Backend::doMaintenance()
{
	if (this->status != BACKEND_STATUS::BACKEND_DOWN)
		return;

	Connection checkOut;
	auto res = checkOut.doConnect(*address_info, 5, false, this->nf_mark);

	switch (res) {
	case IO::IO_OP::OP_SUCCESS:{
			zcu_log_print(LOG_NOTICE,
					  "BackEnd %s:%d resurrect in farm: '%s', service: '%s'",
					  this->address.data(), this->port,
					  this->backend_config->f_name.data(),
					  this->backend_config->
					  srv_name.data());
			this->status = BACKEND_STATUS::BACKEND_UP;
			break;
		}
	default:
		this->status = BACKEND_STATUS::BACKEND_DOWN;
	}
}

bool Backend::isHttps()
{
	return ctx != nullptr;
}

void Backend::setStatus(BACKEND_STATUS new_status)
{
	this->status = new_status;
}

BACKEND_STATUS Backend::getStatus()
{
	return status;
}
