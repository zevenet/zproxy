#pragma once

#include <modsecurity/modsecurity.h>
#include <modsecurity/rules.h>
#include <modsecurity/transaction.h>
#include "../config/config.h"
#include "../http/http_stream.h"

using
	modsecurity::ModSecurity;
using
	modsecurity::Rules;
using
	modsecurity::Transaction;

/**
 * @brief contanis the methods needed to give WAF features to the proxy.
 * Those functions uses the libmodsecurity functions.
 */
class
	Waf
{
      public:
  /**
   * @brief passes the client HTTP information from the proxy to the modsec lib,
   * gets the modsec resolution and logs it.
   * @param HttpStream
   * @return true if the modsec intervention is distruptive for the request
   * given.
   */
	static bool
	checkRequestWaf(HttpStream & stream);
  /**
   * @brief passes the backend HTTP information from the proxy to the modsec
   * lib, gets the modsec resolution and logs it.
   * @param HttpStream
   * @return true if the modsec intervention is distruptive for the response
   * given.
   */
	static bool
	checkResponseWaf(HttpStream & stream);
  /**
   * @brief reloads the ruleset of the listener, parsing the configuration file
   * and creating a new ruleset with all the WafRules directives
   * @param is the pointer to the rules object to save the WAF rulesets
   * @return returns 'true' on success or 'false' on failure
   */
	static
		std::shared_ptr <
		modsecurity::Rules >
	reloadRules();
  /**
   * @brief is the log callback function used by the modsec library
   * @param non used
   * @param is the message is going to be logged
   */
	static void
	logModsec(void *log = nullptr, const void *data = nullptr);
  /**
   * @brief Print to log a human readable rule list provided.
   * @param rules to be printed.
   */
	static void
	dumpRules(modsecurity::Rules & rules);
};
