/*
 * Copyright (C) 2023  Zevenet S.L. <support@zevenet.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef _ZPROXY_WAF_H
#define _ZPROXY_WAF_H

#include <modsecurity/modsecurity.h>
#include <modsecurity/rules.h>
#include <modsecurity/transaction.h>

#define WAF_PASS    0

class HttpStream;

namespace Waf {

void logModsec(void *data, const void *message);

int parse_conf(const std::string &file, void **rules);

void destroy_rules(void *rules);

void dump_rules(void *rules);

void *init_api(void);

void destroy_api(void *modsec);


class Stream {

	modsecurity::Rules *waf_rules;
	modsecurity::ModSecurity *waf_api;
	modsecurity::Transaction *modsec_transaction{nullptr};
	bool waf_enable{false};

    void initTransaction();
    void resetTransaction();

    public:
    Stream(void *api, void *rules);
    ~Stream();

    bool checkRequestHeaders(HttpStream *stream);

    bool checkResponseHeaders(HttpStream *stream);

    bool checkRequestBody(HttpStream *stream);

    bool checkResponseBody(HttpStream *stream);

    char *response(HttpStream *stream);
};

};

#endif
