#!/bin/bash
###############################################################################
#
#    Zevenet Software License
#    This file is part of the Zevenet Load Balancer software package.
#
#    Copyright (C) 2014-today ZEVENET SL, Sevilla (Spain)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

tplfile="/usr/local/zevenet/app/pound/etc/poundtpl.cfg"
confdir="/usr/local/zevenet/config"
dcookie="BackendCookie"
dssl="DisableSSLv3"
lcookie="#BackendCookie \"ZENSESSIONID\" \"domainname.com\" \"/\" 0"
ddhparam="DHParams"
ldhparam="DHParams 	\"/usr/local/zevenet/app/pound/etc/dh2048.pem\""
decdh="ECDHCurve"
lecdh="ECDHCurve 	\"prime256v1\""
dhfile="/usr/local/zevenet/app/pound/etc/dh2048.pem"
openssl=`which openssl`

if [ ! -f $dhfile ]; then
	$openssl dhparam -out $dhfile -5 2048
fi

cd $confdir
if [ `ls *_pound_cfg 2>/dev/null` ]; then
	for file in $(grep -l $dssl *_pound.cfg); do
		sed -i "s/$dssl/Disable\ SSLv3/g" $file
		echo "Directive $dssl migrated in the file $file"
	done

	for file in $(ls -1 *_pound.cfg); do
		if [ "`grep $dcookie $file`" == "" ]; then
			sed -e "/DynScale/ a$lcookie"  $file | sed -e "s?$lcookie?\t\t$lcookie?g" > /tmp/migratefile.txt
			mv /tmp/migratefile.txt $file
			echo "Directive $dcookie added to file $file"
		fi
	done

	for file in $(ls -1 *_pound.cfg); do
		if [ "`grep $ddhparam $file`" == "" ]; then
			sed -i "/^Control/ a$ldhparam" $file
			sync
			sed -i "/^$ddhparam/ a$lecdh" $file
			echo "Directives $ddhparam and $decdh added to file $file"
		fi
	done
fi
cd - > /dev/null

exit 0
