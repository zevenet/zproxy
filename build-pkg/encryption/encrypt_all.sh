#!/bin/bash

source encryption/config
SYMKEY=1135628147310
SALT="2D04E04389FBB423"
ITER="14"

echo -e "\nEncrypting modules"

for file in "${encrypted_files[@]}"; do
	printf "%-60s" "$file"
	CMD="openssl aes-256-cbc -a -salt -S $SALT -iter $ITER -k $SYMKEY -in $file -md md5"

	if $CMD > "${file}e"; then
		echo "[ OK ]"
	else
		echo "FAILED !!!"
	fi

	rm "$file"
done
