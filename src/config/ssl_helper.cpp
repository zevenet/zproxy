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

#include "ssl_helper.h"
#include "config_data.h"
#include "../../zcutils/zcutils.h"

#ifndef SSL3_ST_SR_CLNT_HELLO_A
#define SSL3_ST_SR_CLNT_HELLO_A (0x110 | SSL_ST_ACCEPT)
#endif
#ifndef SSL23_ST_SR_CLNT_HELLO_A
#define SSL23_ST_SR_CLNT_HELLO_A (0x210 | SSL_ST_ACCEPT)
#endif

DH *global::SslHelper::DH512_params
{
nullptr};
#if DH_LEN == 1024
DH *global::Config::DH1024_params
{
nullptr};
#else
DH *global::SslHelper::DH2048_params
{
nullptr};
#endif

global::SslHelper global::SslHelper::current
{
};

RSA *global::SslHelper::RSA_tmp_callback([[maybe_unused]] SSL * ssl,
					 [[maybe_unused]]
					 int is_export, int keylength)
{
	RSA *res;
	std::lock_guard < std::mutex > lock__(RSA_mut);
	res = (keylength <= 512) ? RSA512_keys[rand() % N_RSA_KEYS]
		: RSA1024_keys[rand() % N_RSA_KEYS];
	return res;
}

void global::SslHelper::SSLINFO_callback(const SSL * ssl, int where,
					 [[maybe_unused]]
					 int rc)
{
	RENEG_STATE *reneg_state;

	/* Get our thr_arg where we're tracking this connection info */
	if ((reneg_state =
	     static_cast < RENEG_STATE * >(SSL_get_app_data(ssl))) == nullptr)
		return;

	/* If we're rejecting renegotiations, move to ABORT if Client Hello is being
	 * read. */
	if ((where & SSL_CB_ACCEPT_LOOP) &&
	    *reneg_state == RENEG_STATE::RENEG_REJECT) {
		int state;

		state = SSL_get_state(ssl);
		if (state == SSL3_ST_SR_CLNT_HELLO_A
		    || state == SSL23_ST_SR_CLNT_HELLO_A) {
			*reneg_state = RENEG_STATE::RENEG_ABORT;
			zcutils_log_print(LOG_WARNING,
					  "rejecting client initiated renegotiation");
		}
	}
	else if (where & SSL_CB_HANDSHAKE_DONE &&
		 *reneg_state == RENEG_STATE::RENEG_INIT) {
		// Reject any followup renegotiations
		*reneg_state = RENEG_STATE::RENEG_REJECT;
	}
}

DH *global::SslHelper::load_dh_params(char *file)
{
	DH *dh = nullptr;
	BIO *bio;

	if ((bio = BIO_new_file(file, "r")) == nullptr) {
		zcutils_log_print(LOG_WARNING, "unable to open DH file - %s",
				  file);
		return nullptr;
	}

	dh = PEM_read_bio_DHparams(bio, nullptr, nullptr, nullptr);
	BIO_free(bio);
	return dh;
}

int global::SslHelper::generate_key(RSA ** ret_rsa, unsigned long bits)
{
	int rc = 0;
	RSA *rsa;

	rsa = RSA_new();
	if (rsa) {
		BIGNUM *bne = BN_new();
		if (BN_set_word(bne, RSA_F4))
			rc = RSA_generate_key_ex(rsa, bits, bne, nullptr);
		BN_free(bne);
		if (rc)
			*ret_rsa = rsa;
		else
			RSA_free(rsa);
	}
	return rc;
}

void global::SslHelper::doRSAgen()
{
	int n;
	RSA *t_RSA512_keys[N_RSA_KEYS];
	RSA *t_RSA1024_keys[N_RSA_KEYS];

	for (n = 0; n < N_RSA_KEYS; n++) {
		/* FIXME: Error handling */
		generate_key(&t_RSA512_keys[n], 512);
		generate_key(&t_RSA1024_keys[n], 1024);
	}
	std::lock_guard < std::mutex > lock__(RSA_mut);
	for (n = 0; n < N_RSA_KEYS; n++) {
		RSA_free(RSA512_keys[n]);
		RSA512_keys[n] = t_RSA512_keys[n];
		RSA_free(RSA1024_keys[n]);
		RSA1024_keys[n] = t_RSA1024_keys[n];
	}
}

global::SslHelper::~ SslHelper()
{
	if (DH512_params != nullptr) {
		DH_free(DH512_params);
	}
#if DH_LEN == 1024
	if (DH1024_params != nullptr) {
		DH_free(DH1024_params);
	}
#else
	if (DH2048_params != nullptr) {
		DH_free(DH2048_params);
	}
#endif
	for (int n = 0; n < N_RSA_KEYS; n++) {
		RSA_free(RSA512_keys[n]);
		RSA_free(RSA1024_keys[n]);
	}
}

void global::SslHelper::initDhParams()
{
	int n;
	/*
	 * Pre-generate ephemeral RSA keys
	 */
	for (n = 0; n < N_RSA_KEYS; n++) {
		if (!generate_key(&RSA512_keys[n], 512)) {
			zcutils_log_print(LOG_WARNING,
					  "%s():%d: RSA_generate(%d, 512) failed",
					  __FUNCTION__, __LINE__, n);
			return;
		}
		if (!generate_key(&RSA1024_keys[n], 1024)) {
			zcutils_log_print(LOG_WARNING,
					  "%s():%d: RSA_generate(%d, 1024) failed",
					  __FUNCTION__, __LINE__, n);
			return;
		}
	}
	std::lock_guard < std::mutex > lock__(RSA_mut);
	DH512_params = get_dh512();
#if DH_LEN == 1024
	DH1024_params = get_dh1024();
#else
	DH2048_params = get_dh2048();
#endif
}

global::SslHelper & global::SslHelper::getCurrent()
{
	return current;
}

int global::SslHelper::verifyCertificate_OK([[maybe_unused]]
					    int pre_ok,
					    [[maybe_unused]] X509_STORE_CTX *
					    ctx)
{
	return 1;
}
