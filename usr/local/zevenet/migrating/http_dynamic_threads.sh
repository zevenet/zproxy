#!/bin/bash

# Migrate HTTP farms to dynamic thread model, without tcmalloc
for i in $(find /usr/local/zevenet/config/ -name "*pound.cfg");
do
	if [[ `grep -c ThreadModel $i` == '0' ]]; then
		echo Migrating $i
		sed -i -e 's/Threads\t\t[0-9]*$/ThreadModel\tdynamic/' $i
	fi
done
