#!/bin/bash
confdir="/usr/local/zenloadbalancer/config"
name="Name"
sw=0


echo "Checking \"Name\" Directive in HTTP profiles"
cd $confdir
for file in `ls -1 *_pound.cfg`; do
	grep -P "^Name\t.+" $file 1>/dev/null
	if [ ! $? -eq 0 ]
	then
		sw=1
		#capture the farmname
		fname=`echo $file | cut -d"_" -f1`
		echo "	Upgrading 4.2 http directives for farm $fname in file $file"
			sed -i "/^Group/ a$name\t\t$fname" $file
	fi

done
cd - > /dev/null

if [ $sw -eq 0 ]
then
	echo "	Nothing to do"
fi
exit 0
