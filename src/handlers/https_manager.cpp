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
#include "https_manager.h"

/** If a client browser connects via HTTPS and if it presents a certificate and
 * if HTTPSHeaders is set, Pound will obtain the certificate data and add the
 * following HTTP headers to the request it makes to the server:
 *
 *  - X-SSL-Subject: information about the certificate owner
 *  - X-SSL-Issuer: information about the certificate issuer (CA)
 *  - X-SSL-notBefore: begin validity date for the certificate
 *  - X-SSL-notAfter: end validity date for the certificate
 *  - X-SSL-serial: certificate serial number (in decimal)
 *  - X-SSL-cipher: the cipher currently in use
 *  - X-SSL-certificate: the full client certificate (multi-line)
 */
void httpsHeaders(HttpStream *stream, ssl::SSLConnectionManager *ssl_manager, int clnt_check) {
  if (ssl_manager == nullptr) return;
  std::string header_value;
  header_value.reserve(MAXBUF);
  const SSL_CIPHER *cipher;
  std::unique_ptr<X509, decltype(&::X509_free)> x509(SSL_get_peer_certificate(stream->client_connection.ssl),
                                                     ::X509_free);
  /** client check less than maximum */
  if (x509 != nullptr && clnt_check < 3 && SSL_get_verify_result(stream->client_connection.ssl) != X509_V_OK) {
    Logger::logmsg(LOG_ERR, "Bad certificate from %s", stream->client_connection.address_str.c_str());
  }

  if ((cipher = SSL_get_current_cipher(stream->client_connection.ssl)) != nullptr) {
    char cipher_buf[MAXBUF];
    SSL_CIPHER_description(cipher, cipher_buf, 200);
    header_value = SSL_get_version(stream->client_connection.ssl);
    header_value += '/';
    header_value += cipher_buf;
    header_value.erase(std::remove(header_value.begin(), header_value.end(), '\n'), header_value.end());
    header_value.erase(std::remove(header_value.begin(), header_value.end(), '\r'), header_value.end());
    stream->request.addHeader(http::HTTP_HEADER_NAME::X_SSL_CIPHER, header_value, true);
  }
  /** client check enable */
  if (clnt_check > 0 && x509 != nullptr) {
    int line_len = 0;
    char buf[MAXBUF]{'\0'};
    std::unique_ptr<BIO, decltype(&::BIO_free)> bb(BIO_new(BIO_s_mem()), ::BIO_free);
    X509_NAME_print_ex(bb.get(), ::X509_get_subject_name(x509.get()), 8, XN_FLAG_ONELINE & ~ASN1_STRFLGS_ESC_MSB);
    ssl::get_line(bb.get(), buf, MAXBUF, &line_len);
    stream->request.addHeader(http::HTTP_HEADER_NAME::X_SSL_SUBJECT, buf, true);

    X509_NAME_print_ex(bb.get(), X509_get_issuer_name(x509.get()), 8, XN_FLAG_ONELINE & ~ASN1_STRFLGS_ESC_MSB);
    ssl::get_line(bb.get(), buf, MAXBUF, &line_len);
    stream->request.addHeader(http::HTTP_HEADER_NAME::X_SSL_ISSUER, buf, true);

    ASN1_TIME_print(bb.get(), X509_get_notBefore(x509.get()));
    ssl::get_line(bb.get(), buf, MAXBUF, &line_len);
    stream->request.addHeader(http::HTTP_HEADER_NAME::X_SSL_NOTBEFORE, buf, true);

    ASN1_TIME_print(bb.get(), X509_get0_notAfter(x509.get()));
    ssl::get_line(bb.get(), buf, MAXBUF, &line_len);
    stream->request.addHeader(http::HTTP_HEADER_NAME::X_SSL_NOTAFTER, buf, true);

    long serial = ASN1_INTEGER_get(X509_get_serialNumber(x509.get()));
    stream->request.addHeader(http::HTTP_HEADER_NAME::X_SSL_SERIAL, std::to_string(serial), true);

    PEM_write_bio_X509(bb.get(), x509.get());
    ssl::get_line(bb.get(), buf, MAXBUF, &line_len);
    header_value = buf;
    while (ssl::get_line(bb.get(), buf, MAXBUF, &line_len) == 0) {
      header_value += buf;
    }
    stream->request.addHeader(http::HTTP_HEADER_NAME::X_SSL_CERTIFICATE, header_value, true);
  }
}

/** If the StrictTransportSecurity is set then adds the header. */
void setStrictTransportSecurity(Service *service, HttpStream *stream) {
  if (service->service_config.sts > 0) {
    std::string sts_header_value = "max-age=";
    sts_header_value += std::to_string(service->service_config.sts);
    stream->response.addHeader(http::HTTP_HEADER_NAME::STRICT_TRANSPORT_SECURITY, sts_header_value);
  }
}
