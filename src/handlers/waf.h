#pragma once

#include <modsecurity/modsecurity.h>
#include <modsecurity/rules.h>
#include <modsecurity/transaction.h>
#include "../debug/logger.h"
#include "../connection/client_connection.h"
#include "../http/http_request.h"
#include "../config/config_data.h"
#include "../config/config.h"
#include "../util/network.h"

using modsecurity::ModSecurity;
using modsecurity::Rules;
using modsecurity::Transaction;

/**
 * @brief contanis the methods needed to give WAF features to the proxy.
 * Those functions uses the libmodsecurity functions.
 */
class Waf
{
public:
    /**
     * @brief frees an struct of type FILE_LIST
     * @param is the pointer, passed by reference, to the FILE_LIST struct
     */
    static void freeFileList(FILE_LIST **list);
    /**
     * @brief initializates an transaction object using a WAF ruleset. This function clean the struct
     * previously if it is initializated
     * @param is the pointer, passed by reference, to the transanction is going to be created
     * @param is the instance of the modsec where is going to be added the new transaction
     * @param is the ruleset used for the new transaction
     */
    static void newModsecTransaction(modsecurity::Transaction **transaction, modsecurity::ModSecurity *mod, std::shared_ptr<modsecurity::Rules> rules);
    /**
     * @brief removes a transaction object and point the pointer to null
     * @param is the pointer to a transaction object passed by referece
     */
    static void delModsecTransaction(modsecurity::Transaction **transaction);
    /**
     * @brief passes the client HTTP information from the proxy to the modsec lib, gets the modsec resolution and logs it.
     * @param is the transaction object where is going to be saved the req/resp information, in order to be analyzed by the modsec lib
     * @param is the request proxy object where proxy has saved the incomming request
     * @param is the client connection object where proxy has saved the client socket connection
     * @return the modsec intervention which contains the actions that the proxy must reply to the client
     */
    static modsecurity::ModSecurityIntervention checkRequestWaf(modsecurity::Transaction *transaction, HttpRequest *request, ClientConnection *client);
    /**
     * @brief passes the backend HTTP information from the proxy to the modsec lib, gets the modsec resolution and logs it.
     * @param is the transaction object where is going to be saved the req/resp information, in order to be analyzed by the modsec lib
     * @param is the response proxy object where proxy has saved the response from the backend to the client
     * @param is the HTTP version that is being used between the client and the backend
     * @return the modsec intervention which contains the actions that the proxy must reply to the client
     */
    static modsecurity::ModSecurityIntervention checkResponseWaf(modsecurity::Transaction *transaction, HttpResponse *response, http::HTTP_VERSION http_version);
    /**
     * @brief reloads the ruleset of the listener, parsing the configuration file and creating a new ruleset with all the WafRules directives
     * @param is the pointer to the rules object to save the WAF rulesets
     * @return returns 'true' on success or 'false' on failure
     */
    static bool reloadRules(modsecurity::Rules **rules);
    /**
     * @brief parses the configuraton file to get the WafRules directives
     * @return returns a sorted list with all the rules files that must be loaded
     */
    static FILE_LIST *parseConf();
    /**
     * @brief is the log callback function used by the modsec library
     * @param non used
     * @param is the message is going to be logged
     */
    static void logModsec(void *log, const void *data);

};
