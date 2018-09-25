#include <EXTERN.h>
#include <perl.h>

/* SSL & Base64 Support */
#include <stdio.h>
#include <string.h>
#include <openssl/crypto.h>
#include <openssl/bio.h>
#include <openssl/evp.h>
#include <openssl/conf.h>
#include <openssl/err.h>
#include <stdint.h>
#include <assert.h>

EXTERN_C void xs_init(pTHX);
size_t calcDecodeLength(const char *b64input);
int Base64Decode(char *b64message, unsigned char **buffer, size_t *length);
int decrypt(unsigned char *ciphertext, int ciphertext_len, char *pass,
			unsigned char *plaintext);
void handleErrors(void);
void generator(void);

static PerlInterpreter *my_perl;

static char *PerlExecB64 = "#{FILECONTENTB64}";
static unsigned char Geny[14];

int main(int argc, char **argv, char **env)
{
	size_t basesize;
	int plainsize, i, retstat = 1;

	unsigned char *CryptPerlExec;
	unsigned char *PerlExec;
	char **PerlScript;

	/* Passthrough arguments */
	PerlScript = (char **)malloc((argc + 2) * sizeof(char *));
	PerlScript[0] = "";
	PerlScript[1] = "-e";

	for (i = 0; i < argc - 1; i++) {
		PerlScript[i + 3] = argv[i + 1];
	}

	/* Decrypt protected perl code and generate the Perl code*/
	Base64Decode(PerlExecB64, &CryptPerlExec, &basesize);
	PerlExec = malloc((int)basesize);
	generator();
	plainsize = decrypt(CryptPerlExec, (int)basesize, Geny, PerlExec);
	free(CryptPerlExec);
	PerlExec[(int)plainsize - 1] = '\0';
	PerlScript[2] = PerlExec;

	my_perl = perl_alloc();
	perl_construct(my_perl);
	perl_parse(my_perl, xs_init, argc + 2, PerlScript, (char **)env);

	retstat = perl_run(my_perl);

	perl_destruct(my_perl);
	perl_free(my_perl);

	free(PerlExec);

	return retstat;
}

/* Base64 Support */
size_t calcDecodeLength(const char *b64input)
{
	//Calculates the length of a decoded string
	size_t len = strlen(b64input), padding = 0;

	if (b64input[len - 1] == '=' && b64input[len - 2] == '=') { //last two chars are =
		padding = 2;
	} else if (b64input[len - 1] == '=') { //last char is =
		padding = 1;
	}

	return (len * 3) / 4 - padding;
}

int Base64Decode(char *b64message, unsigned char **buffer, size_t *length)
{
	//Decodes a base64 encoded string
	BIO *bio, *b64;

	int decodeLen = calcDecodeLength(b64message);
	*buffer = (unsigned char *)malloc(decodeLen + 1);
	(*buffer)[decodeLen] = '\0';

	bio = BIO_new_mem_buf(b64message, -1);
	b64 = BIO_new(BIO_f_base64());
	bio = BIO_push(b64, bio);

	BIO_set_flags(bio, BIO_FLAGS_BASE64_NO_NL); //Do not use newlines to flush buffer
	*length = BIO_read(bio, *buffer, strlen(b64message));
	assert(*length == decodeLen); //length should equal decodeLen, else something went horribly wrong
	BIO_free_all(bio);

	return (0); //success
}

/* SSL AES Decryption Support */
int decrypt(unsigned char *ciphertext, int ciphertext_len, char *pass,
			unsigned char *plaintext)
{
	EVP_CIPHER_CTX *ctx;

	int len;
	const unsigned char *salt = NULL;
	int plaintext_len;
	unsigned char key[EVP_MAX_KEY_LENGTH], iv[EVP_MAX_IV_LENGTH];

# if OPENSSL_VERSION_NUMBER < 0x10100000L
	/* Openssl 1.0. */
	ERR_load_crypto_strings();
	OpenSSL_add_all_algorithms();
	OPENSSL_config(NULL);
# else
	/* Openssl 1.1 */
	OPENSSL_init_crypto(OPENSSL_INIT_ADD_ALL_CIPHERS | OPENSSL_INIT_ADD_ALL_DIGESTS | OPENSSL_INIT_LOAD_CRYPTO_STRINGS, NULL);
# endif

	const EVP_CIPHER *cipher = EVP_get_cipherbyname("aes-256-cbc");
	const EVP_MD *dgst = EVP_get_digestbyname("md5");

	/* Create and initialise the context */
	if (!(ctx = EVP_CIPHER_CTX_new())) {
		handleErrors();
	}

	if (!EVP_BytesToKey(cipher, dgst, salt, (unsigned char *)pass, strlen(pass), 1, key, iv)) {
		handleErrors();
	}

	/* Initialise the decryption operation. IMPORTANT - ensure you use a key
	 * and IV size appropriate for your cipher
	 * In this example we are using 256 bit AES (i.e. a 256 bit key). The
	 * IV size for *most* modes is the same as the block size. For AES this
	 * is 128 bits
	 */
	if (1 != EVP_DecryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv)) {
		handleErrors();
	}

	/* Provide the message to be decrypted, and obtain the plaintext output.
	 * EVP_DecryptUpdate can be called multiple times if necessary
	 */
	if (1 != EVP_DecryptUpdate(ctx, plaintext, &len, ciphertext, ciphertext_len)) {
		handleErrors();
	}

	plaintext_len = len;

	/* Finalise the decryption. Further plaintext bytes may be written at
	 * this stage.
	 */
	if (1 != EVP_DecryptFinal_ex(ctx, plaintext + len, &len)) {
		handleErrors();
	}
	plaintext_len += len;

	/* Clean up */
	EVP_CIPHER_CTX_free(ctx);

	return plaintext_len;
}

void handleErrors(void)
{
	ERR_print_errors_fp(stderr);
	abort();
}

void generator(void)
{
	int sem = 113;

	sprintf(Geny, "%s%d", Geny, sem);
	while (sem > 0) {
		sem = sem / 2;
		sprintf(Geny, "%s%d", Geny, sem);
	};
}

