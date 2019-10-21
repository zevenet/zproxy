#include "waf.h"

void Waf::freeFileList(FILE_LIST **list)
{
    FILE_LIST *next =*list;

    while (next != nullptr){
        *list = (*list)->next;
        free(next);
        next =*list;
    }
}

void Waf::newModsecTransaction(modsecurity::Transaction **transaction, modsecurity::ModSecurity *mod,std::shared_ptr<modsecurity::Rules> rules) {
    // If a modsecuriy transaction exists, delete it. This mustn't occur
    delModsecTransaction(transaction);

    if (rules.get() != nullptr){
        *transaction = new modsecurity::Transaction(mod, rules.get(), nullptr);
        Logger::logmsg(LOG_DEBUG, "Created Modsecurity transaction");
    }
}

void Waf::delModsecTransaction(modsecurity::Transaction **transaction) {
    if (*transaction != nullptr) {
        // modsec_transaction->processLogging();

        Logger::logmsg(LOG_DEBUG, "Deleted Modsecurity transaction");
        delete *transaction;
        *transaction = nullptr;
    }
}

modsecurity::ModSecurityIntervention Waf::checkRequestWaf(modsecurity::Transaction *transaction, HttpRequest *request, ClientConnection *client) {

    modsecurity::ModSecurityIntervention intervention;
    intervention.status = 200;
    intervention.url = nullptr;
    intervention.log = nullptr;
    intervention.disruptive = 0;
    intervention.pause = 0;
    std::string httpVersion = "";

    switch (request->http_version) {
    case http::HTTP_VERSION::HTTP_1_0:httpVersion = "1.0";
        break;
    case http::HTTP_VERSION::HTTP_1_1:httpVersion = "1.1";
        break;
    case http::HTTP_VERSION::HTTP_2_0:httpVersion = "2.0";
    }

    transaction->processConnection( client->getPeerAddress().c_str(),
                                      client->getPeerPort(),
                                      client->getLocalAddress().c_str(),
                                      client->getLocalPort());

    for (int i = 0; i < (int)request->num_headers; i++) {
        transaction->addRequestHeader((unsigned char *) request->headers[i].name, request->headers[i].name_len, \
                                             (unsigned char *) request->headers[i].value, request->headers[i].value_len);
    }

    transaction->processURI(request->path, request->method, httpVersion.c_str());
    transaction->processRequestHeaders();

    transaction->appendRequestBody((unsigned char *) request->message, request->message_length);
    transaction->processRequestBody();

    // Checking interaction
    if (transaction->intervention(&intervention)) {

        // log event?
        if (intervention.log != nullptr) {
          Logger::logmsg(LOG_WARNING, "[WAF] (%lx) %s", pthread_self(), intervention.log );
        }

        // redirect returns disruptive=1

        // process is going to be cut. Execute the logging phase
        if (intervention.disruptive) {
            if (!transaction->processLogging())
                Logger::logmsg(LOG_WARNING, "(%lx) WAF, error processing the log", pthread_self());
        }
    }

    return intervention;
}

modsecurity::ModSecurityIntervention Waf::checkResponseWaf(modsecurity::Transaction *transaction, HttpResponse *response, http::HTTP_VERSION http_version) {

    modsecurity::ModSecurityIntervention intervention;
    intervention.status = 200;
    intervention.url = nullptr;
    intervention.log = nullptr;
    intervention.disruptive = 0;
    std::string httpVersion = "";

    switch (http_version) {
    case http::HTTP_VERSION::HTTP_1_0:httpVersion = "1.0";
        break;
    case http::HTTP_VERSION::HTTP_1_1:httpVersion = "1.1";
        break;
    case http::HTTP_VERSION::HTTP_2_0:httpVersion = "2.0";
    }

    for (int i = 0; i < response->num_headers; i++) {
        transaction->addResponseHeader((unsigned char *) response->headers[i].name,
                                              response->headers[i].name_len,
                                              (unsigned char *) response->headers[i].value,
                                              response->headers[i].value_len);
    }
    transaction->appendResponseBody((unsigned char *) response->message, response->message_length);

    transaction->processResponseHeaders(response->http_status_code, "HTTP " + httpVersion);
    transaction->processResponseBody();

    transaction->processLogging();

    // Checking interaction
    if (transaction->intervention(&intervention)) {
        // log event?
        if (intervention.log != nullptr) {
          Logger::logmsg(LOG_WARNING, "[WAF] (%lx) %s", pthread_self(), intervention.log );
        }
    }

    if (intervention.disruptive) {
        transaction->processLogging();
        Logger::logmsg(LOG_DEBUG, "WAF wants to apply an action for the REQUEST");
    }

    return intervention;
}

bool Waf::reloadRules(modsecurity::Rules **rules) {

    // parse file
    FILE_LIST *waf_files = parseConf();

    // reload rules
    if (Config::loadWafConfig(rules, waf_files))
        return false;

    Logger::logmsg(LOG_INFO, "The WAF rulesets waf reloaded properly");

    return true;
}

// todo: parse only the directives of a listener
FILE_LIST *Waf::parseConf()
{
    FILE_LIST *bef_file, *file, *initList = nullptr;
    int err = 0;
    regex_t WafRules;
    char lin[MAXBUF];
    regmatch_t matches[5];
    Config config;
    config.conf_init(Config::config_file);
    config.compile_regex();

    Logger::logmsg(LOG_WARNING, "file to update %s", Config::config_file.c_str());

    if (regcomp(&WafRules, "^[ \t]*WafRules[ \t]+\"(.+)\"[ \t]*$",
               REG_ICASE | REG_NEWLINE | REG_EXTENDED))
        return nullptr;

    // compile regexp
    while (config.conf_fgets(lin, MAXBUF) && !err) {

        if(!regexec(&WafRules, lin, 4, matches, 0)) {
            if ((file = (FILE_LIST *)malloc(sizeof (FILE_LIST)) ) == nullptr ){
                logmsg(LOG_ERR, "WAF config: out of memory - aborted");
                err=1;
            }

            else {
                lin[matches[1].rm_eo] = '\0';
                file->file = strdup(lin + matches[1].rm_so);
                file->next = nullptr;
                if(initList == nullptr)
                    initList = file;
                else
                    bef_file->next = file;
                bef_file = file;
            }
        }
    }

    // remove regexp
    config.clean_regex();

    if (err){
        Waf::freeFileList(&initList);
        return nullptr;
    }

    return initList;
}

void Waf::logModsec(void *data, const void *message) {

    if (data != nullptr)
        Logger::logmsg(LOG_WARNING, "%s", (const char *)data);
    if (message != nullptr)
        Logger::logmsg(LOG_WARNING, "[WAF] %s", (const char *)message);
}
