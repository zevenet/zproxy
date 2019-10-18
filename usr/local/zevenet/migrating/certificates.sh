#!/bin/bash

# Migrate certificates files to new directory
mv /usr/local/zevenet/config/{*.pem,*.csr,*.key} /usr/local/zevenet/config/certificates/ 2>/dev/null

# Migrate certificate of farm config file
for i in $(find /usr/local/zevenet/config/ -name "*_proxy.cfg");
do
	if grep -q 'Cert \"\/usr\/local\/zevenet\/config\/\w*\.pem' $i; then
		echo "Migrating certificate directory of config file"
		sed -i -e 's/Cert \"\/usr\/local\/zevenet\/config/Cert \"\/usr\/local\/zevenet\/config\/certificates/' $i
	fi
done
