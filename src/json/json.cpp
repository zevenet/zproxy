//
// Created by abdess on 10/4/18.
//

#include "json.h"
#include <sstream>
json::Json * json::Json::parse(std::string data) {
  std::istringstream f(data);
  std::string s;

//  while (getline(f, s, ':')) {
//    switch (s[0]) {
//      case '"':
//        JsonData * json_data = new JsonData
//        root->setName(s.substr(1, s.length() - 1));
//        break;
//      case '{':
//        break;
//      case '[':
//        break;
//      case ',':
//        break;
//    }
//  }
  return nullptr;
}
/*
 * {

        if (getline(f, s, '/')) {
          if (!helper::try_lexical_cast<int>(s, task.listener_id)) {
            Debug::logmsg(LOG_WARNING,
                          "Error parsing API request target listener: %s",
                          request.getUrl().c_str());
            break;
          }
 */





