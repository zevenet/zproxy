#!/usr/bin/bash

if [ ! -f /var/run/keepalived.pid ]
then
	exit
fi


KA_PID=`cat /var/run/keepalived.pid`;
KA_DATA_FILE="/tmp/keepalived.data";
STATE=`kill -USR1 $KA_PID; cat $KA_DATA_FILE  | grep Wantstate | awk {'print $3'}`
state=`echo $STATE | sed -e 's/\(.*\)/\L\1/'`

CL_STATUS=`cat /usr/local/zevenet/node_status`;


if [[ "$state" != "$CL_STATUS" && "$state" == "backup" ]]
then
	logger "WARNING: running cluster transition to backup";
	/usr/local/zevenet/bin/zcluster-manager notify_backup
	exit 0

elif [[ "$state" != "$CL_STATUS" && "$state" == "master" ]]
then
	logger "WARNING: running cluster transition to master";
	/usr/local/zevenet/bin/zcluster-manager notify_master
	exit 0 

fi

exit 0
