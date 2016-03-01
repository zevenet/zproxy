###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This library is free software; you can redistribute it and/or modify it
#     under the terms of the GNU Lesser General Public License as published
#     by the Free Software Foundation; either version 2.1 of the License, or
#     (at your option) any later version.
#
#     This library is distributed in the hope that it will be useful, but
#     WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
#     General Public License for more details.
#
#     You should have received a copy of the GNU Lesser General Public License
#     along with this library; if not, write to the Free Software Foundation,
#     Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
###############################################################################

#insert info in log file
sub logfile    # ($string)
{
	my $string = shift;

	my $date = `date`;
	$date =~ s/\n//g;
	open FO, ">> $logfile";
	print FO
	  "$date - $ENV{'SERVER_NAME'} - $ENV{'REMOTE_ADDR'} - $ENV{'REMOTE_USER'} - $string\n";
	close FO;
}

#function that insert info through syslog
#
#&zenlog($priority,$text);
#
#examples
#&zenlog("info","This is test.");
#&zenlog("err","Some errors happended.");
#&zenlog("debug","testing debug mode");
#
sub zenlog    # ($string,$type,$level)
{
	my $type   = shift;    # type   = type of message
	my $string = shift;    # string = message

	openlog( "zenlog", 'pid', 'local0' );    #open syslog

	if ( $type eq "info" || $type eq "notice" )
	{                                        #info and notice priorities
		syslog( $type, "(priority: " . $type . ") -> " . $string );
	}
	elsif ( $type eq "err" || $type eq "warning" )
	{                                        #warning and err priorities
		syslog(
				$type,
				"(priority: "
				  . $type
				  . ", process ID: "
				  . $$
				  . ", ERRNO output: %m, last state value: "
				  . $? . ") -> "
				  . $string
		);
	}
	elsif ( $type eq "crit" || $type eq "alert" || $type eq "emerg" )
	{    #crit, alert and emerg priorities
		syslog(
				$type,
				"(priority: "
				  . $type
				  . " HIGH PRIORITY, process ID: "
				  . $$
				  . ", ERRNO output: %m, last state value: "
				  . $? . ") -> "
				  . $string
		);
	}
	elsif ( $type eq "debug" )
	{    #debug priority
		syslog(
				$type,
				"(priority: "
				  . $type
				  . ", process ID: "
				  . $$
				  . ", real user id of process: "
				  . $<
				  . ", effective user id of process: "
				  . $>
				  . ", ERRNO output: %m, last state value: "
				  . $?
				  . ", list of command line args: "
				  . @ARGV
				  . ", perl executable name: "
				  . $^X . ") -> "
				  . $string
		);
	}
	else
	{    #other cases
		syslog( $type, "(priority: " . $type . ") ->" . $string );
	}

	closelog();    #close syslog
}

#open file with lock
#
#&openlock(filehandle, $mode, $expr);
#&openlock($filehanlde, $mode);
#
#examples
#&openlock(FILE,"<$fichero");
#&openlock(FILE,">>","output.txt");
#
sub openlock    # ($filehandle,$mode,$expr)
{
	my ( $filehandle, $mode, $expr ) = @_;    #parameters

	if ( $expr ne "" )
	{                                         #3 parameters
		if ( $mode =~ /</ )
		{                                     #only reading
			open ( $filehandle, $mode, $expr )
			  || die "some problems happened reading the file $expr\n";
			flock $filehandle, LOCK_SH
			  ; #other scripts with LOCK_SH can read the file. Writing scripts with LOCK_EX will be locked
		}
		elsif ( $mode =~ />/ )
		{       #only writing
			open ( $filehandle, $mode, $expr )
			  || die "some problems happened writing the file $expr\n";
			flock $filehandle, LOCK_EX;    #other scripts cannot open the file
		}
	}
	else
	{                                      #2 parameters
		if ( $mode =~ /</ )
		{                                  #only reading
			open ( $filehandle, $mode )
			  || die "some problems happened reading the filehandle $filehanlde\n";
			flock $filehandle, LOCK_SH
			  ; #other scripts with LOCK_SH can read the file. Writing scripts with LOCK_EX will be locked
		}
		elsif ( $mode =~ />/ )
		{       #only writing
			open ( $filehandle, $mode )
			  || die "some problems happened writing the filehandle $filehandle\n";
			flock $filehandle, LOCK_EX;    #other scripts cannot open the file
		}
	}
}

#close file with lock
#
#&closelock($filehandle);
#
#examples
#&closelock(FILE);
#
sub closelock    # ($filehandle)
{
	my $filehandle = shift;

	close ( $filehandle )
	  || warn
	  "some problems happened closing the filehandle $filehandle";    #close file
}

#tie aperture with lock
#
#@array = &tielock($file);
#
#examples
#@myarray = &tielock("test.dat");
#@array = &tielock($filename);
#
sub tielock    # ()
{
	my $file = shift;    #parameters

	$o = tie my @array, "Tie::File", $file;
	$o->flock;

	return @array;
}

#untie close file with lock
#
#&untielock(@array);
#
#examples
#&untielock(@myarray);
#
sub untielock    # (@array)
{
	@array = @_;

	untie @array;
}

# log and run the command string input parameter returning execution error code
sub logAndRun
{
	my $command = shift;    # command string to log and run
	my $return_code;

	my $program = ( split '/', $0 )[-1];
	$program = "$ENV{'SCRIPT_NAME'}" if $program eq '-e';
	$program .= ' ';

	#	&logfile( (caller (2))[3] . ' >>> ' . (caller (1))[3]);
	&logfile( $program . "running: $command" );    # log
	system ( "$command >/dev/null 2>&1" );         # run
	$return_code = $?;

	if ( $return_code )
	{
		&logfile( "last command failed!" );        # show in logs if failed
	}

	# returning error code from execution
	return $return_code;
}

# example of caller usage
sub zlog
{
	my @message = shift;

	#my ($package,		# 0
	#$filename,		# 1
	#$line,          # 2
	#$subroutine,    # 3
	#$hasargs,       # 4
	#$wantarray,     # 5
	#$evaltext,      # 6
	#$is_require,    # 7
	#$hints,         # 8
	#$bitmask,       # 9
	#$hinthash       # 10
	#) = caller (1);	 # arg = number of suroutines back in the stack trace

	use Data::Dumper;
	&logfile(   '>>> '
			  . ( caller ( 3 ) )[3] . ' >>> '
			  . ( caller ( 2 ) )[3] . ' >>> '
			  . ( caller ( 1 ) )[3]
			  . " => @message" );

	return;
}

sub print_mem
{
	my $mem_string = `grep RSS /proc/$$/status`;
	chomp ( $mem_string );
	print ( "$mem_string >> @_\n" );
	return;
}

sub debug { return 0 }

# do not remove this
1;
