#!/bin/bash


# load LB variables
source ./usr/local/zevenet/bin/load_global_conf.sh
load_global_conf


# vars
IP_MANAGEMENT="192.168.0.99"

GLOBALCONF_TPL=$globalcfg_tpl
CONF_DIR=$configdir
TEMPLATE_DIR=$templatedir


# functions
show_usage() {
  echo usage: `basename $0` -i interface_name
  echo "  Mandatory parameters:"
  echo "      -i|--interface, this interface will not be deleted. It will set with the same configuration. It is recomentadable set the management interface here."
  echo ""
  echo "  Optional parameters: "
  echo "      --remove-backups, removes the load balancer backups in the reset process"
  echo "      --hard-reset, removes all user configuration: Activation certificate, backups, "
  echo "      --hardware, is a hard reset but set by default the ip $IP_MANAGEMENT in the manager interface"
  echo ""
  echo "  The factory reset, in its soft version, will delete:"
  echo "      *) All the interfaces configuration, excepts the interface received as argument. "
  echo "      *) All farm configuration. "
  echo "      *) All certificates. "
  echo "      *) Logs. "
  echo "      *) Graphs. "
  echo "      *) Graphs. "
  echo "      *) System directories: /opt, /root, /tmp "
  echo "      *) Command history"
  echo "      *) Users and API configuration"
  echo ""
  echo "  After a hard reset in the system will keep:"
  echo "      *) Cherokee SSL certificate"
  echo "      *) Zevenet updates"
  echo "      *) The host name"
  echo "      *) The password for the root user"
  echo ""

  exit 1
}


# script

while [ $# -gt 0 ]; do
	case $1 in
	"-interface"|"-i")
			if_mgmt=$2
			shift
			shift
		;;
	"--hard-reset")
		HARD=1
		REM_BACKUPS=1
		shift
		;;
	"--remove-backups")
		REM_BACKUPS=1
		shift
		;;
	"--hardware")
		REM_BACKUPS=1
		HARD=1
		HW=1
		shift
		;;
	*)
		echo "Invalid option: $1"
		show_usage
		exit 1
		;;
	esac

	shift
done

if [ -z "${if_mgmt}" ]; then
  show_usage
fi

if [ ! -d "/sys/class/net/${if_mgmt}" ]; then
        echo "Specified interface does not exist"
fi

# save interface conf file
IF_CONF="${CONF_DIR}/if_${if_mgmt}_conf"
IF_CONF_TMP="/tmp/if_conf_file_tmp"
cp $IF_CONF $IF_CONF_TMP

echo "Stopping processes"
for AP in $(ps aux | grep zen | grep -v grep | awk '{print $2}')
do
        echo "Parando el proceso  $AP"
        ps -ef | grep $AP |grep -v grep
        pkill $AP
done
kill -9 `ps aux | grep sec |grep -v grep | awk '{print $2}'`

echo "Stopping cron process"
/etc/init.d/cron stop
echo "Stopping cherokee process"
/etc/init.d/cherokee stop
echo "Stopping zevenet process"
/etc/init.d/zevenet stop

echo "Deleting configuration files"
rm -fr /var/log/*
rm -fr /opt/*
rm -fr /tmp/*
rm -fr /usr/local/zevenet/logs/*
rm -fr /usr/local/zevenet/app/zenrrd/rrd/*
rm -fr /usr/local/zevenet/www/img/graphs/*

if [ $HARD -eq 1 ]
then
	echo "Deleting Zevenet certificate"
	rm -fr /usr/local/zevenet/www/zlbcertfile.pem
fi

if [ $REM_BACKUPS -eq 1 ]
then
	echo "Deleting backups"
    rm -fr /usr/local/zevenet/backups/*
fi


#Delete all except: zlb-*, iface management, global.conf and cherokee conf and ssl cert

mv ${CONF_DIR}/zencert* /tmp/
rm -fr ${CONF_DIR}
mv /tmp/zencert* $CONF_DIR

echo "Creating interface config file if_${if_mgmt}_conf"
mv $IF_CONF_TMP $IF_CONF
sed -i -E 's/status=.*$/status=up/' $IF_CONF

# set template
cp $GLOBALCONF_TPL ${CONF_DIR}/global.conf
cp $snmpdconfig_tpl $snmpdconfig_file
#~ cp $TEMPLATE_DIR/zevenet.cron ${CONF_DIR}/ ?????
cp $TEMPLATE_DIR/rbac ${CONF_DIR}/
cp $TEMPLATE_DIR/ipds ${CONF_DIR}/
cp $confhttp_tpl $confhttp
cp $zlb_start_tpl $zlb_start_script && chmod +x $zlb_start_script
cp $zlb_stop_tpl $zlb_stop_script && chmod +x $zlb_stop_script


echo "#make your own script in your favorite language, it will be called" > ${CONF_DIR}/zlb-start
echo "#at the end of the procedure /etc/init.d/zevenet start" >> ${CONF_DIR}/zlb-start
echo "#and replicated to the other node if zen cluster is running." >> ${CONF_DIR}/zlb-start

echo "#make your own script in your favorite language, it will be called" > ${CONF_DIR}/zlb-stop
echo "#at the end of the procedure /etc/init.d/zevenet stop" >> ${CONF_DIR}/zlb-stop
echo "#and replicated to the other node if zen cluster is running." >> ${CONF_DIR}/zlb-stop


if [ $HARD -eq 1 ]; then
	echo "Cleaning apt"
	rm -fr /etc/apt/sources.list
	apt-get update
	apt-get clean

	echo "Preparing the firt boot"
	if [ ! -f /etc/firstzlbboot ]; then
			touch /etc/firstzlbboot
	fi
fi


if [ $HW -eq 1 ]; then
	echo "Rewriting interface config file $IF_CONF"
	echo "status=up" > $IF_CONF
	echo "${if_mgmt};$IP_MANAGEMENT;255.255.255.0;192.168.100.5" >> $IF_CONF
fi


echo "Deleting the root's home"
rm -rf /root/.bash_history
rm -rf /root/* {.bashrc}

echo "Running zevenet process"
/etc/init.d/zevenet start
