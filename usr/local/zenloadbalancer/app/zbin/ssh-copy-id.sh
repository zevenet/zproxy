#!/usr/bin/expect -f

set password [lindex $argv 0];
# remove password from argument list
set argv [lreplace $argv 0 0];

spawn ssh-copy-id $argv
expect {
	"password:" {
		send "$password\n"
	}
}
#expect eof
