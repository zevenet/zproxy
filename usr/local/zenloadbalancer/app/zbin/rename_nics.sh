#!/bin/bash

NETFILE="/etc/udev/rules.d/70-persistent-net.rules"
if_list=`ip -o link | awk '{print $2}' | grep -v lo | grep -v cl | sed 's/://g'`


for i in $if_list
do
	echo "Stopping $i"
	ip link set $i down
	echo "Renaming $i to ${i}_t"
	ip link set $i name ${i}_t

done

for i in $if_list
do

	#obtain current mac for this if
	mac=`ip link show ${i}_t  | awk '/ether/ {print $2}'`
	echo "MAC for $i is $mac"
	new_name=`grep -i $mac $NETFILE | awk '{print $6}' | cut -d"\"" -f 2`
	echo "Changing old name $i to new name $new_name"
	ip link set ${i}_t name $new_name 
	ip link set $new_name up
	#read -p "Press any key to continue"
	#echo ""
	
	
done
