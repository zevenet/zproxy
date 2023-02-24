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

#include "http_request.h"
#include "http_response.h"

#define WAF_PASS    0

class HttpStream;

namespace Waf {

static void logModsec(void *data, const void *message)
{
}

static int parse_conf(const std::string &file, void **rules)
{
    printf("The proxy is not compiled with WAF options\n");
    return -1;
}

static void destroy_rules(void *rules)
{
}

static void dump_rules(void *rules)
{
}

static void *init_api(void)
{
    return nullptr;
}

static void destroy_api(void *modsec)
{
}

class Stream {
    public:

   Stream(void *api, void *rules) {}
    ~Stream() {}

    bool checkRequestHeaders(HttpStream *stream) {
        return WAF_PASS;
    }

    bool checkResponseHeaders(HttpStream *stream) {
        return WAF_PASS;
    }

    bool checkRequestBody(HttpStream *stream) {
        return WAF_PASS;
    }

    bool checkResponseBody(HttpStream *stream) {
        return WAF_PASS;
    }

    char *response(HttpStream *stream) {
        return nullptr;
    }

};

};

#endif
