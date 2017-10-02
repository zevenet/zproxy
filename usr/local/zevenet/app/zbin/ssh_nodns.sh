#!/bin/bash

USEDNS="UseDNS no"
SSHD_FILE="/etc/ssh/sshd_config"

grep "${USEDNS}" ${SSHD_FILE} >/dev/null
if [ "$?" -ne "0"   ]
then
	echo "Disabling DNS resolution in SSH"
	logger "Disabling DNS resolution in SSH"
	#sed -i '/$USEDNS/a ListenAddress' $SSHD_FILE
	sed  -i   '0,/.*permitrootLogin.*/Is//&\n'"${USEDNS}"'/' $SSHD_FILE
	/etc/init.d/ssh restart 
fi
