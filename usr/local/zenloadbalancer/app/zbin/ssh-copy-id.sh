#!/usr/bin/expect -f

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
