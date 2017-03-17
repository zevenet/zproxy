#!/usr/bin/expect -f
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

set password [lindex $argv 0];
# remove password from argument list
set argv [lreplace $argv 0 0];

spawn ssh-copy-id $argv
expect {
	"*?(yes/no)\?" { send -- "yes\r"; exp_continue }
	"*?assword:*" {
		send -- "$password\r"
		send -- "\r"
		exp_continue
	}
	eof { exit 1 }
	timeout { exit 1 }
	"Now try*\r" { exit 0 }
	"already exist on the remote system." { exit 0 }
}

exit 0
