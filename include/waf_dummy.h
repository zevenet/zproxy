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

enum WAF_ACTION {
	WAF_PASS = 0,
	WAF_REDIRECTION,
	WAF_BLOCK,
};

class HttpStream;

inline int zproxy_waf_parse_conf(const char *file, void **rules)
{
	printf("The proxy is not compiled with WAF options\n");
	return -1;
}
inline void zproxy_waf_destroy_rules(void *rules) { return; }
inline void zproxy_waf_dump_rules(void *rules) { return; }
inline void *zproxy_waf_init_api(void) { return NULL; }
inline void zproxy_waf_destroy_api(void *modsec) { return; }

struct zproxy_waf_stream {};

inline struct zproxy_waf_stream *zproxy_waf_stream_init(void *api, void *rules) { return NULL; }
inline void zproxy_waf_stream_destroy(struct zproxy_waf_stream *waf_stream) { return; }
inline bool zproxy_waf_stream_checkrequestheaders(struct zproxy_waf_stream *waf_stream, HttpStream *stream) { return WAF_PASS; }
inline bool zproxy_waf_stream_checkresponseheaders(struct zproxy_waf_stream *waf_stream, HttpStream *stream) { return WAF_PASS; }
inline bool zproxy_waf_stream_checkrequestbody(struct zproxy_waf_stream *waf_stream, HttpStream *stream) { return WAF_PASS; }
inline bool zproxy_waf_stream_checkresponsebody(struct zproxy_waf_stream *waf_stream, HttpStream *stream) { return WAF_PASS; }
inline char *zproxy_waf_stream_response(struct zproxy_waf_stream *waf_stream, HttpStream *stream) { return nullptr; }

#endif
