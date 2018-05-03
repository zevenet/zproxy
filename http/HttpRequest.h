//
// Created by abdess on 4/20/18.
//
#pragma  once

#include "http_parser.h"

class HttpRequest : public http_parser::HttpParser {
 public:
  char *data;
  ssize_t data_size;

};

class HttpResponse : public http_parser::HttpParser {
 public:
  char *data;
  ssize_t data_size;
};