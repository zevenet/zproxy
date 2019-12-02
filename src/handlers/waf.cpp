#include "waf.h"

bool Waf::checkRequestWaf(HttpStream &stream) {
  std::string httpVersion = "";

  switch (stream.request.http_version) {
    case http::HTTP_VERSION::HTTP_1_0:
      httpVersion = "1.0";
      break;
    case http::HTTP_VERSION::HTTP_1_1:
      httpVersion = "1.1";
      break;
    case http::HTTP_VERSION::HTTP_2_0:
      httpVersion = "2.0";
      break;
  }
  modsecurity::intervention::reset(&stream.modsec_transaction->m_it);
  stream.modsec_transaction->processConnection(
      stream.client_connection.getPeerAddress().c_str(),
      stream.client_connection.getPeerPort(),
      stream.client_connection.getLocalAddress().c_str(),
      stream.client_connection.getLocalPort());

  for (int i = 0; i < static_cast<int>(stream.request.num_headers); i++) {
    if (stream.request.headers[i].header_off) continue;
    auto name = reinterpret_cast<unsigned char *>(
        const_cast<char *>(stream.request.headers[i].name));
    auto value = reinterpret_cast<unsigned char *>(
        const_cast<char *>(stream.request.headers[i].value));
    stream.modsec_transaction->addRequestHeader(
        name, stream.request.headers[i].name_len, value,
        stream.request.headers[i].value_len);
  }

  stream.modsec_transaction->processURI(
      stream.request.path, stream.request.method, httpVersion.c_str());
  stream.modsec_transaction->processRequestHeaders();

  stream.modsec_transaction->appendRequestBody(
      (unsigned char *)stream.request.message, stream.request.message_length);
  stream.modsec_transaction->processRequestBody();

  // Checking interaction
  if (stream.modsec_transaction->m_it.disruptive) {
    // log event?
    if (stream.modsec_transaction->m_it.log != nullptr) {
      Logger::logmsg(LOG_WARNING, "[WAF] (%lx) %s", pthread_self(),
                     stream.modsec_transaction->m_it.log);
    }

    // redirect returns disruptive=1

    // process is going to be cut. Execute the logging phase
    if (!stream.modsec_transaction->processLogging())
      Logger::logmsg(LOG_WARNING, "(%lx) WAF, error processing the log",
                     pthread_self());

    return true;
  }

  return false;
}

bool Waf::checkResponseWaf(HttpStream &stream) {
  std::string httpVersion = "";

  switch (stream.request.http_version) {
    case http::HTTP_VERSION::HTTP_1_0:
      httpVersion = "1.0";
      break;
    case http::HTTP_VERSION::HTTP_1_1:
      httpVersion = "1.1";
      break;
    case http::HTTP_VERSION::HTTP_2_0:
      httpVersion = "2.0";
      break;
  }
  modsecurity::intervention::reset(&stream.modsec_transaction->m_it);
  for (int i = 0; i < static_cast<int>(stream.response.num_headers); i++) {
    if (stream.response.headers[i].header_off) continue;
    auto name = reinterpret_cast<unsigned char *>(
        const_cast<char *>(stream.response.headers[i].name));
    auto value = reinterpret_cast<unsigned char *>(
        const_cast<char *>(stream.response.headers[i].value));
    stream.modsec_transaction->addResponseHeader(
        name, stream.response.headers[i].name_len, value,
        stream.response.headers[i].value_len);
  }
  stream.modsec_transaction->appendResponseBody(
      reinterpret_cast<unsigned char *>(stream.response.message),
      stream.response.message_length);
  stream.modsec_transaction->processResponseHeaders(
      stream.response.http_status_code, httpVersion);
  stream.modsec_transaction->processResponseBody();
  stream.modsec_transaction->processLogging();
  // Checking interaction
  if (stream.modsec_transaction->m_it.disruptive) {
    // log event?
    if (stream.modsec_transaction->m_it.log != nullptr) {
      Logger::logmsg(LOG_WARNING, "[WAF] (%lx) %s", pthread_self(),
                     stream.modsec_transaction->m_it.log);
    }
    stream.modsec_transaction->processLogging();  // TODO:: is it necessary??
    Logger::logmsg(LOG_DEBUG, "WAF wants to apply an action for the REQUEST");

    return true;
  }
  return false;
}

// todo: parse only the directives of a listener
std::shared_ptr<Rules> Waf::reloadRules() {
  int err = 0;
  regex_t WafRules;
  char lin[MAXBUF];
  regmatch_t matches[5];
  Config config;
  config.conf_init(Config::config_file);
  auto rules = std::make_shared<Rules>();
  Logger::logmsg(LOG_WARNING, "file to update %s", Config::config_file.c_str());

  if (regcomp(&WafRules, "^[ \t]*WafRules[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED))
    return nullptr;

  // compile regexp
  while (config.conf_fgets(lin, MAXBUF) && !err) {
    if (!regexec(&WafRules, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      auto file = std::string(lin + matches[1].rm_so,
                              lin + matches[1].rm_eo - lin + matches[1].rm_so);
      err = rules->loadFromUri(file.data());
      if (err == -1) {
        logmsg(LOG_ERR, "Error loading waf ruleset file %s: %s", file.data(),
               rules->getParserError().data());
        return nullptr;
      }
    }
  }
  // enable for debug purpose only
  // dumpRules(*rules);
  Logger::logmsg(LOG_INFO, "The WAF rulesets waf reloaded properly");
  return rules;
}

void Waf::logModsec(void *data, const void *message) {
  if (data != nullptr)
    Logger::logmsg(LOG_WARNING, "%s", static_cast<char *>(data));
  if (message != nullptr)
    Logger::logmsg(LOG_WARNING, "[WAF] %s",
                   static_cast<char *>(const_cast<void *>(message)));
}

void Waf::dumpRules(modsecurity::Rules &rules) {
  Logger::logmsg(LOG_DEBUG, "Rules: ");
  for (int i = 0; i <= modsecurity::Phases::NUMBER_OF_PHASES; i++) {
    auto rule = rules.getRulesForPhase(i);
    if (rule) {
      for (auto &x : *rule) {
        Logger::logmsg(LOG_DEBUG, "\tRule Id: %d From %s at %d ", x->m_ruleId,
                       x->m_fileName.data(), x->m_lineNumber);
      }
    }
  }
}
