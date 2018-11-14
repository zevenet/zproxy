#!/bin/bash

if_mgmt=$1

show_usage() {
  echo usage: `basename $0`  interface_name
  exit 1
}

if [ -z "${if_mgmt}" ]; then
  show_usage
fi

if [ ! -d "/sys/class/net/${if_mgmt}" ]; then
        echo "Specified interface does not exist"
fi 
echo "Parando procesos"
for AP in $(ps aux | grep zen | grep -v grep | awk '{print $2}')
do
        echo "Parando el proceso  $AP"
        ps -ef | grep $AP |grep -v grep 
        pkill $AP
done
kill -9 `ps aux | grep sec |grep -v grep | awk '{print $2}'`

echo "Parando proceso cron y cherokee"
/etc/init.d/cron stop
/etc/init.d/cherokee stop
/etc/init.d/zevenet stop

echo "Borrando ficheros de configuracion"
rm -fr /var/log/*
rm -fr /opt/*
rm -fr /tmp/*
rm -fr /usr/local/zevenet/logs/*
rm -fr /usr/local/zevenet/backups/*
rm -fr /usr/local/zevenet/www/zlbcertfile.pem
rm -fr /usr/local/zevenet/app/zenrrd/rrd/*
rm -fr /usr/local/zevenet/www/img/graphs/*
rm -fr /usr/local/zevenet/config/if*
rm -fr /usr/local/zevenet/config/notifications/*
rm -fr /usr/local/zevenet/config/float.conf
rm -fr /usr/local/zevenet/config/*.html
rm -fr /usr/local/zevenet/config/*.cfg
rm -fr /etc/apt/sources.list

#borrar todo excpeto: zencert*, zlb-*, global.con, if_eth0_conf

echo "Limpiando apt"
apt-get update
apt-get clean

echo "Borrando config"
DGW=`grep defaultgw= /usr/local/zevenet/config/global.conf`
sed -i "s/$DGW/\$defaultgw=\"\";/g" /usr/local/zevenet/config/global.conf
DGW=`grep defaultgwif= /usr/local/zevenet/config/global.conf`
sed -i "s/$DGW/\$defaultgwif=\"\";/g" /usr/local/zevenet/config/global.conf
SERVER=`grep "server!bind!1!interface =" /usr/local/zevenet/app/cherokee/etc/cherokee/cherokee.conf`
sed -i "s/$SERVER/\#server\!bind\!1\!interface = \;/g" /usr/local/zevenet/app/cherokee/etc/cherokee/cherokee.conf
PORT=`grep "server!bind!1!port =" /usr/local/zevenet/app/cherokee/etc/cherokee/cherokee.conf`
sed -i "s/$PORT/server\!bind\!1\!port = 444/g" /usr/local/zevenet/app/cherokee/etc/cherokee/cherokee.conf
 
echo "Preparando para el primer arranque"
if [ ! -f /etc/firstzlbboot ]; then
        touch /etc/firstzlbboot
fi
echo "creating interface config file  if_${if_mgmt}_conf"
echo "status=up" > /usr/local/zevenet/config/if_${if_mgmt}_conf
echo "${if_mgmt};192.168.0.99;255.255.255.0;;" >> /usr/local/zevenet/config/if_${if_mgmt}_conf
echo "Borrando el home de root"
rm -rf /root/.bash_history
rm -rf /root/* {.bashrc}