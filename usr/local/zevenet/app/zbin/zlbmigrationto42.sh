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

confdir="/usr/local/zevenet/config"
name="Name"
sw=0

echo "Checking \"Name\" Directive in HTTP profiles"
cd $confdir
for file in `ls -1 *_pound.cfg 2>/dev/null`; do
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

exit 0
