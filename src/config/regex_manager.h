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

#include <pcreposix.h>
#include "../../zcutils/zcutils.h"

struct Regex : public regex_t {
	explicit Regex(const char *reg_ex_expression) : regex_t()
	{
		if (::regcomp(this, reg_ex_expression,
			      REG_ICASE | REG_NEWLINE | REG_EXTENDED)) {
			zcu_log_print(LOG_ERR,
				      "%s():%d: error compiling regex: %s",
				      __FUNCTION__, __LINE__,
				      reg_ex_expression);
		}
	}
	bool doMatch(const char *str, size_t n_match, regmatch_t p_match[],
		     int e_flags = 0)
	{
		return ::regexec(this, str, n_match, p_match, e_flags) == 0;
	}
	~Regex()
	{
		::regfree(this);
	}
};

namespace regex_set
{
static const Regex Empty("^[ \t]*$");
static const Regex Comment("^[ \t]*#.*$");
static const Regex User("^[ \t]*User[ \t]+\"(.+)\"[ \t]*$");
static const Regex Group("^[ \t]*Group[ \t]+\"(.+)\"[ \t]*$");
static const Regex Name("^[ \t]*Name[ \t]+\"?([a-zA-Z0-9_-]+)\"?[ \t]*$");
static const Regex HTTPTracerDir("^[ \t]*HTTPTracerDir[ \t]+\"(.+)\"[ \t]*$");
static const Regex RootJail("^[ \t]*RootJail[ \t]+\"(.+)\"[ \t]*$");
static const Regex Daemon("^[ \t]*Daemon[ \t]+([01])[ \t]*$");
static const Regex Threads("^[ \t]*Threads[ \t]+([1-9][0-9]*)[ \t]*$");
static const Regex ThreadModel("^[ \t]*ThreadModel[ \t]+(pool|dynamic)[ \t]*$");
static const Regex LogFacility("^[ \t]*LogFacility[ \t]+([a-z0-9-]+)[ \t]*$");
static const Regex LogLevel("^[ \t]*LogLevel[ \t]+([0-9])[ \t]*$");
static const Regex Grace("^[ \t]*Grace[ \t]+([0-9]+)[ \t]*$");
static const Regex Alive("^[ \t]*Alive[ \t]+([1-9][0-9]*)[ \t]*$");
static const Regex SSLEngine("^[ \t]*SSLEngine[ \t]+\"(.+)\"[ \t]*$");
static const Regex Control("^[ \t]*Control[ \t]+\"(.+)\"[ \t]*$");
static const Regex ControlIP("^[ \t]*ControlIP[ \t]+([^ \t]+)[ \t]*$");
static const Regex ControlPort("^[ \t]*ControlPort[ \t]+([1-9][0-9]*)[ \t]*$");
static const Regex ControlUser("^[ \t]*ControlUser[ \t]+\"(.+)\"[ \t]*$");
static const Regex ControlGroup("^[ \t]*ControlGroup[ \t]+\"(.+)\"[ \t]*$");
static const Regex ControlMode("^[ \t]*ControlMode[ \t]+([0-7]+)[ \t]*$");
static const Regex ListenHTTP("^[ \t]*ListenHTTP[ \t]*$");
static const Regex ListenHTTPS("^[ \t]*ListenHTTPS[ \t]*$");
static const Regex End("^[ \t]*End[ \t]*$");
static const Regex BackendKey("^[ \t]*Key[ \t]+\"(.+)\"[ \t]*$");
static const Regex Address("^[ \t]*Address[ \t]+([^ \t]+)[ \t]*$");
static const Regex Port("^[ \t]*Port[ \t]+([1-9][0-9]*)[ \t]*$");
static const Regex Cert("^[ \t]*Cert[ \t]+\"(.+)\"[ \t]*$");
static const Regex CertDir("^[ \t]*CertDir[ \t]+\"(.+)\"[ \t]*$");
static const Regex xHTTP("^[ \t]*xHTTP[ \t]+([012345])[ \t]*$");
static const Regex Client("^[ \t]*Client[ \t]+([1-9][0-9]*)[ \t]*$");
static const Regex CheckURL("^[ \t]*CheckURL[ \t]+\"(.+)\"[ \t]*$");
static const Regex SSLConfigFile("^[ \t]*SSLConfigFile[ \t]+\"(.+)\"[ \t]*$");
#if WAF_ENABLED
static const Regex ErrWAF("^[ \t]*ErrWAF[ \t]+\"(.+)\"[ \t]*$");
#endif
static const Regex
	ErrNoSsl("^[ \t]*ErrNoSsl[ \t]+([45][0-9][0-9][ \t]+)?\"(.+)\"[ \t]*$");
static const Regex Err414("^[ \t]*Err414[ \t]+\"(.+)\"[ \t]*$");
static const Regex Err500("^[ \t]*Err500[ \t]+\"(.+)\"[ \t]*$");
static const Regex Err501("^[ \t]*Err501[ \t]+\"(.+)\"[ \t]*$");
static const Regex Err503("^[ \t]*Err503[ \t]+\"(.+)\"[ \t]*$");
static const Regex NoSslRedirect(
	"^[ \t]*NoSslRedirect[ \t]+(30[127][ \t]+)?\"(.+)\"[ \t]*$");
static const Regex
	SSLConfigSection("^[ \t]*SSLConfigSection[ \t]+([^ \t]+)[ \t]*$");
static const Regex MaxRequest("^[ \t]*MaxRequest[ \t]+([1-9][0-9]*)[ \t]*$");
static const Regex AddRequestHeader(
	"^[ \t]*(?:AddHeader|AddRequestHeader)[ \t]+\"(.+)\"[ \t]*$");
static const Regex RemoveRequestHeader(
	"^[ \t]*(?:HeadRemove|RemoveRequestHeader)[ \t]+\"(.+)\"[ \t]*$");
static const Regex
	AddResponseHeader("^[ \t]*AddResponseHead(?:er)?[ \t]+\"(.+)\"[ \t]*$");
static const Regex RemoveResponseHeader(
	"^[ \t]*RemoveResponseHead(?:er)?[ \t]+\"(.+)\"[ \t]*$");
static const Regex RewriteLocation(
	"^[ \t]*RewriteLocation[ \t]+([012])([ \t]+path)?[ \t]*$");
static const Regex
	RewriteDestination("^[ \t]*RewriteDestination[ \t]+([01])[ \t]*$");
static const Regex RewriteHost("^[ \t]*RewriteHost[ \t]+([01])[ \t]*$");
static const Regex RewriteUrl(
	"^[ \t]*RewriteUrl[ \t]+\"(.+)\"[ \t]+\"(.*)\"([ \t]+last)?[ \t]*$");
static const Regex Service("^[ \t]*Service[ \t]*$");
static const Regex ServiceName("^[ \t]*Service[ \t]+\"(.+)\"[ \t]*$");
static const Regex URL("^[ \t]*URL[ \t]+\"(.+)\"[ \t]*$");
static const Regex OrURLs("^[ \t]*OrURLS[ \t]*$");
static const Regex BackendCookie(
	"^[ \t]*BackendCookie[ \t]+\"(.+)\"[ \t]+\"(.*)\"[ \t]+\"(.*)\"[ \t]+([0-9]+|Session)[ \t]*$");
static const Regex HeadRequire("^[ \t]*HeadRequire[ \t]+\"(.+)\"[ \t]*$");
static const Regex HeadDeny("^[ \t]*HeadDeny[ \t]+\"(.+)\"[ \t]*$");
static const Regex StrictTransportSecurity(
	"^[ \t]*StrictTransportSecurity[ \t]+([0-9]+)[ \t]*$");
static const Regex BackEnd("^[ \t]*BackEnd[ \t]*$");
static const Regex Emergency("^[ \t]*Emergency[ \t]*$");
static const Regex Priority("^[ \t]*Priority[ \t]+([1-9])[ \t]*$");
static const Regex Weight("^[ \t]*Weight[ \t]+([1-9]*)[ \t]*$");
static const Regex TimeOut("^[ \t]*TimeOut[ \t]+([1-9][0-9]*)[ \t]*$");
static const Regex HAport("^[ \t]*HAport[ \t]+([1-9][0-9]*)[ \t]*$");
static const Regex
	HAportAddr("^[ \t]*HAport[ \t]+([^ \t]+)[ \t]+([1-9][0-9]*)[ \t]*$");
static const Regex Redirect(
	"^[ \t]*Redirect(Append|Dynamic|)[ \t]+(30[127][ \t]+|)\"(.+)\"[ \t]*$");
static const Regex Session("^[ \t]*Session[ \t]*$");
static const Regex Type("^[ \t]*Type[ \t]+([^ \t]+)[ \t]*$");
static const Regex TTL("^[ \t]*TTL[ \t]+([1-9][0-9]*)[ \t]*$");
static const Regex ID("^[ \t]*ID[ \t]+\"(.+)\"[ \t]*$");
static const Regex DynScale("^[ \t]*DynScale[ \t]+([01])[ \t]*$");
static const Regex CompressionAlgorithm(
	"^[ \t]*CompressionAlgorithm[ \t]+([^ \t]+)[ \t]*$");
static const Regex
	PinnedConnection("^[ \t]*PinnedConnection[ \t]+([01])[ \t]*$");
static const Regex RoutingPolicy("^[ \t]*RoutingPolicy[ \t]+([^ \t]+)[ \t]*$");
static const Regex
	ClientCert("^[ \t]*ClientCert[ \t]+([0-3])[ \t]+([1-9])[ \t]*$");
static const Regex SSLAllowClientRenegotiation(
	"^[ \t]*SSLAllowClientRenegotiation[ \t]+([012])[ \t]*$");
static const Regex DisableProto(
	"^[ \t]*Disable[ \t]+(SSLv2|SSLv3|TLSv1|TLSv1_1|TLSv1_2|TLSv1_3)[ \t]*$");
static const Regex
	SSLHonorCipherOrder("^[ \t]*SSLHonorCipherOrder[ \t]+([01])[ \t]*$");
static const Regex Ciphers("^[ \t]*Ciphers[ \t]+\"(.+)\"[ \t]*$");
static const Regex CAlist("^[ \t]*CAlist[ \t]+\"(.+)\"[ \t]*$");
static const Regex VerifyList("^[ \t]*VerifyList[ \t]+\"(.+)\"[ \t]*$");
static const Regex CRLlist("^[ \t]*CRLlist[ \t]+\"(.+)\"[ \t]*$");
static const Regex NoHTTPS11("^[ \t]*NoHTTPS11[ \t]+([0-2])[ \t]*$");
static const Regex ForceHTTP10("^[ \t]*ForceHTTP10[ \t]+\"(.+)\"[ \t]*$");
static const Regex
	SSLUncleanShutdown("^[ \t]*SSLUncleanShutdown[ \t]+\"(.+)\"[ \t]*$");
static const Regex Include("^[ \t]*Include[ \t]+\"(.+)\"[ \t]*$");
static const Regex IncludeDir("^[ \t]*IncludeDir[ \t]+\"(.+)\"[ \t]*$");
static const Regex ConnLimit("^[ \t]*ConnLimit[ \t]+([1-9][0-9]*)[ \t]*$");
static const Regex ConnTO("^[ \t]*ConnTO[ \t]+([1-9][0-9]*)[ \t]*$");
static const Regex IgnoreCase("^[ \t]*IgnoreCase[ \t]+([01])[ \t]*$");
static const Regex
	Ignore100continue("^[ \t]*Ignore100continue[ \t]+([01])[ \t]*$");
static const Regex HTTPS("^[ \t]*HTTPS[ \t]*$");
static const Regex Disabled("^[ \t]*Disabled[ \t]+([01])[ \t]*$");
static const Regex DHParams("^[ \t]*DHParams[ \t]+\"(.+)\"[ \t]*$");
static const Regex CNName(".*[Cc][Nn]=([-*.A-Za-z0-9]+).*$");
static const Regex Anonymise("^[ \t]*Anonymise[ \t]*$");
#ifdef CACHE_ENABLED
static const Regex Cache("^[ \t]*Cache[ \t]*$");
static const Regex CacheContent("^[ \t]*Content[ \t]+\"(.+)\"[ \t]*$");
static const Regex CacheTO("^[ \t]*CacheTO[ \t]+([1-9][0-9]*)[ \t]*$");
static const Regex CacheRamSize(
	"^[ \t]*CacheRamSize[ \t]+([1-9][0-9]*)([gmkbGMKB]*)[ \t]*$");
static const Regex
	CacheThreshold("^[ \t]*CacheThreshold[ \t]+([1-9][0-9]*)[ \t]*$");
static const Regex MaxSize("^[ \t]*MaxSize[ \t]+([1-9][0-9]*)[ \t]*$");
static const Regex
	CacheRamPath("^[ \t]*CacheRamPath[ \t]+\"([a-zA-Z\\/\\._]*)\"[ \t]*$");
static const Regex CacheDiskPath(
	"^[ \t]*CacheDiskPath[ \t]+\"([a-zA-Z\\/\\._]*)\"[ \t]*$");
#endif
#ifndef OPENSSL_NO_ECDH
static const Regex ECDHCurve("^[ \t]*ECDHCurve[ \t]+\"(.+)\"[ \t]*$");
#endif
static const Regex ForwardSNI("^[ \t]*ForwardSNI[ \t]+([01])[ \t]*$");
static const Regex HEADER("^([a-z0-9!#$%&'*+.^_`|~-]+):[ \t]*(.*)[ \t]*$");
static const Regex CONN_UPGRD("(^|[ \t,])upgrade([ \t,]|$)");
static const Regex CHUNK_HEAD("^([0-9a-f]+).*$");
static const Regex RESP_SKIP("^HTTP/1.1 100.*$");
static const Regex
	RESP_IGN("^HTTP/1.[01] (10[1-9]|1[1-9][0-9]|204|30[456]).*$");
static const Regex LOCATION("(http|https)://([^/]+)(.*)");
static const Regex
	AUTHORIZATION("Authorization:[ \t]*Basic[ \t]*\"?([^ \t]*)\"?[ \t]*");

static const Regex NfMark("^[ \t]*NfMark[ \t]+([1-9][0-9]*)[ \t]*$");
#if WAF_ENABLED
static const Regex WafRules("^[ \t]*WafRules[ \t]+\"(.+)\"[ \t]*$");
#endif
static const Regex TestServer("^[ \t]*Server[ \t]+([1-9-][0-9]*)[ \t]*$");
static const Regex ReplaceHeader(
	"^[ \t]*ReplaceHeader[ \t]+(Request|Response)[ \t]+\"(.+)\"[ \t]+\"(.+)\"[ \t]+\"(.*)\"[ \t]*$");
}; // namespace regex_set
