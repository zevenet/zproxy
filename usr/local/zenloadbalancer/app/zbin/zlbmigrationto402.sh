#!/bin/bash
tplfile="/usr/local/zenloadbalancer/app/pound/etc/poundtpl.cfg"
confdir="/usr/local/zenloadbalancer/config"
dcookie="BackendCookie"
dssl="DisableSSLv3"
lcookie="#BackendCookie \"ZENSESSIONID\" \"domainname.com\" \"/\" 0"
ddhparam="DHParams"
ldhparam="DHParams 	\"/usr/local/zenloadbalancer/app/pound/etc/dh2048.pem\""
decdh="ECDHCurve"
lecdh="ECDHCurve 	\"prime256v1\""
dhfile="/usr/local/zenloadbalancer/app/pound/etc/dh2048.pem"
openssl=`which openssl`

if [ ! -f $dhfile ]; then
	$openssl dhparam -5 2048 -out $dhfile
fi

cd $confdir
if [ "`ls *_pound.cfg 2>/dev/null`" != "" ]
then
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
