#!/bin/bash

if [ "$1" = "" -o ! -f "$1" ]; then
	echo "Error: no input file"
	exit 1
fi

SYMKEY="1135628147310"
PERLVERSION=$(perl -e "print $^V;" | cut -d "." -f 1-2 | tr -d "v")
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

FILE="$1"
NAME=$(basename "$FILE")
FILECONTENTB64=$(openssl enc -aes-256-cbc -md md5 -nosalt -k "$SYMKEY" -in "$FILE" 2>/dev/null | base64 | tr -d '\n')

echo -e "\nCompiling ${NAME} executable ..."
sed "s|#{FILECONTENTB64}|${FILECONTENTB64}|g" "${BASE_DIR}/perlembed.c" > "${BASE_DIR}/${NAME}.c"
sync
gcc -o "${BASE_DIR}/${NAME}" "${BASE_DIR}/${NAME}.c" "${BASE_DIR}/perlxsi.c" $(perl -MExtUtils::Embed -e ccopts -e ldopts) -lcrypto
strip "${BASE_DIR}/${NAME}"
