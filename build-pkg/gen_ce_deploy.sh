#!/bin/bash

set -e

if [ -z $1 ]; then
	echo "The CE IP where it is going to be deployed is required"
	echo "Usage: $0 <ce_ip>"
	exit 1
fi

REM_PATH="/opt/"
IP=$1

./e2c
cd CE_WORKDIR/build-pkg
./gen_pkg.sh
cd packages

PKG_NAME=`ls -t *.deb | head -1`

scp $PKG_NAME root@$IP:$REM_PATH
ssh root@$IP "dpkg -i ${REM_PATH}$PKG_NAME"
