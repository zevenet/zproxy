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

use Sys::Syslog;                          #use of syslog
use Sys::Syslog qw(:standard :macros);    #standard functions for Syslog

# Get the program name for zenlog
my $run_cmd_name = ( split '/', $0 )[-1];
$run_cmd_name = ( split '/', "$ENV{'SCRIPT_NAME'}" )[-1] if $run_cmd_name eq '-e';
$run_cmd_name = ( split '/', $^X )[-1] if ! $run_cmd_name;

#function that insert info through syslog
#
#&zenlog($text, $priority);
#
#examples
#&zenlog("This is test.", "info");
#&zenlog("Some errors happended.", "err");
#&zenlog("testing debug mode", "debug");
#
sub zenlog    # ($string, $type)
{
	my $string = shift;            # string = message
	my $type = shift // 'info';    # type   = log level (Default: info))

	# Get the program name
	my $program = $run_cmd_name;

	openlog( $program, 'pid', 'local0' );    #open syslog

	my @lines = split /\n/, $string;

	foreach my $line ( @lines )
	{
		syslog( $type, "(" . uc ( $type ) . ") " . $line );
	}

	closelog();                              #close syslog
}

#open file with lock
#
# $filehandle = &openlock($mode, $expr);
# $filehandle = &openlock($mode);
#
#examples
# $filehandle = &openlock(">>","output.txt");
# $filehandle = &openlock("<$fichero");
#
sub openlock    # ($mode,$expr)
{
	my ( $mode, $expr ) = @_;    #parameters
	my $filehandle;

	if ( $expr ne "" )
	{                            #3 parameters
		if ( $mode =~ /</ )
		{                        #only reading
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
			  || die "some problems happened reading the filehandle $filehandle\n";
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
	return $filehandle;
}

#close file with lock
#
# &closelock($filehandle);
#
#examples
# &closelock(FILE);
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
# $handleArray = &tielock($file);
#
#examples
# $handleArray = &tielock("test.dat");
# $handleArray = &tielock($filename);
#
sub tielock    # ($file_name)
{
	my $file_name = shift;    #parameters

	$o = tie my @array, "Tie::File", $file_name;
	$o->flock;

	return \@array;
}

#untie close file with lock
#
# &untielock($array);
#
#examples
# &untielock($myarray);
#
sub untielock    # (@array)
{
	$array = shift;

	untie @{ $array };
}

# log and run the command string input parameter returning execution error code
sub logAndRun    # ($command)
{
	my $command = shift;    # command string to log and run
	my $return_code;
	my @cmd_output;

	my $program = ( split '/', $0 )[-1];
	$program = "$ENV{'SCRIPT_NAME'}" if $program eq '-e';
	$program .= ' ';

	# &zenlog( (caller (2))[3] . ' >>> ' . (caller (1))[3]);
	&zenlog( $program . "running: $command" );    # log

	if ( &debug )
	{
		@cmd_output = `$command 2>&1`;            # run
	}
	else
	{
		system ( "$command >/dev/null 2>&1" );    # run
	}

	$return_code = $?;

	if ( $return_code )
	{
		&zenlog( "last command failed!" );        # show in logs if failed
		&zenlog( "@cmd_output" ) if &debug;
	}

	# returning error code from execution
	return $return_code;
}

# example of caller usage
sub zlog                                          # (@message)
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
	&zenlog(   '>>> '
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

# find index of an array element
sub indexOfElementInArray
{
	my $searched_element = shift;
	my $array_ref = shift;

	if ( ref $array_ref ne 'ARRAY' )
	{
		return -2;
	}
	
	my @arrayOfElements = @{ $array_ref };
	my $index = 0;
	
	for my $list_element ( @arrayOfElements )
	{
		if ( $list_element eq $searched_element )
		{
			last;
		}

		$index++;
	}

	# if $index is greater than the last element index
	if ( $index > $#arrayOfElements )
	{
		# return an invalid index
		$index = -1;
	}

	return $index;
}

1;
