#!/usr/bin/perl
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

use Sys::Syslog;                          #use of syslog
use Sys::Syslog qw(:standard :macros);    #standard functions for Syslog

# Get the program name for zenlog
my $run_cmd_name = ( split '/', $0 )[-1];
$run_cmd_name = ( split '/', "$ENV{'SCRIPT_NAME'}" )[-1] if $run_cmd_name eq '-e';
$run_cmd_name = ( split '/', $^X )[-1] if ! $run_cmd_name;

=begin nd
Function: zenlog

	Write logs through syslog

	Usage:

		&zenlog($text, $priority);

	Examples:

		&zenlog("This is test.", "info");
		&zenlog("Some errors happended.", "err");
		&zenlog("testing debug mode", "debug");

Parameters:
	string - String to be written in log.
	type   - Log level.

Returns:
	none - .
=cut
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

=begin nd
Function: openlock

	Open file with lock

	Usage:

		$filehandle = &openlock($mode, $expr);
		$filehandle = &openlock($mode);

	Examples:

		$filehandle = &openlock(">>","output.txt");
		$filehandle = &openlock("<$fichero");

Parameters:
	mode - Mode used to open the file.
	expr - Path of file if 3 arguments open is used.

Returns:
	scalar - File handler.

Bugs:
	Not used yet.
=cut
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

=begin nd
Function: closelock

	Close file with lock

	Usage:

		&closelock($filehandle);

	Examples:

		&closelock(FILE);

Parameters:
	filehandle - reference to file handler.

Returns:
	none - .

Bugs:
	Not used yet.
=cut
sub closelock    # ($filehandle)
{
	my $filehandle = shift;

	close ( $filehandle )
	  || warn
	  "some problems happened closing the filehandle $filehandle";    #close file
}

=begin nd
Function: tielock

	tie aperture with lock

	Usage:

		$handleArray = &tielock($file);

	Examples:

		$handleArray = &tielock("test.dat");
		$handleArray = &tielock($filename);

Parameters:
	file_name - Path to File.

Returns:
	scalar - Reference to the array with the content of the file.

Bugs:
	Not used yet.
=cut
sub tielock    # ($file_name)
{
	my $file_name = shift;    #parameters

	$o = tie my @array, "Tie::File", $file_name;
	$o->flock;

	return \@array;
}

=begin nd
Function: untielock

	Untie close file with lock

	Usage:

		&untielock($array);

	Examples:

		&untielock($myarray);

Parameters:
	array - Reference to array.

Returns:
	none - .

Bugs:
	Not used yet.
=cut
sub untielock    # (@array)
{
	my $array = shift;

	untie @{ $array };
}

=begin nd
Function: logAndRun

	Log and run the command string input parameter returning execution error code.

Parameters:
	command - String with the command to be run.

Returns:
	integer - ERRNO or return code returned by the command.

See Also:
	Widely used.
=cut
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

=begin nd
Function: zlog

	Log some call stack information with an optional message.

	This function is only used for debugging pourposes.

Parameters:
	message - Optional message to be printed with the stack information.

Returns:
	none - .
=cut
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

	#~ use Data::Dumper;
	&zenlog(   '>>> '
			 . ( caller ( 3 ) )[3] . ' >>> '
			 . ( caller ( 2 ) )[3] . ' >>> '
			 . ( caller ( 1 ) )[3]
			 . " => @message" );

	return;
}

=begin nd
Function: getMemoryUsage

	Get the resident memory usage of the current perl process.

Parameters:
	none - .

Returns:
	scalar - String with the memory usage.

See Also:
	Used in zapi.cgi
=cut
sub getMemoryUsage
{
	my $mem_string = `grep RSS /proc/$$/status`;

	chomp ( $mem_string );
	$mem_string =~ s/:.\s+/: /;

	return $mem_string;
}

=begin nd
Function: debug

	Get debugging level.

Parameters:
	none - .

Returns:
	integer - Debugging level.

Bugs:
	The debugging level should be stored as a variable.

See Also:
	Widely used.
=cut
sub debug { return 0 }

=begin nd
Function: indexOfElementInArray

	Get the index of the first position where an element if found in an array.

Parameters:
	searched_element - Element to search.
	array_ref        - Reference to the array to be searched.

Returns:
	integer - Zero or higher if the element was found. -1 if the element was not found. -2 if no array reference was received.

See Also:
	Zapi v3: <new_bond>
=cut
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

=begin nd
Function: getGlobalConfiguration

	Set the value of a configuration variable.

Parameters:
	parameter - Name of the global configuration variable. Optional.

Returns:
	scalar - Value of the configuration variable when a variable name is passed as an argument.
	scalar - Hash reference to all global configuration variables when no argument is passed.

See Also:
	Widely used.
=cut
sub getGlobalConfiguration
{
	my $parameter = shift;

	my $global_conf_filepath = "/usr/local/zenloadbalancer/config/global.conf";

	open ( my $global_conf_file, '<', $global_conf_filepath );

	if ( !$global_conf_file )
	{
		my $msg = "Could not open $global_conf_filepath: $!";

		&zenlog( $msg );
		die $msg;
	}

	my $global_conf;

	for my $conf_line ( <$global_conf_file> )
	{
		next if $conf_line !~ /^\$/;

		#~ print "$conf_line"; # DEBUG

		# capture
		$conf_line =~ /\$(\w+)\s*=\s*(?:"(.*)"|\'(.*)\');\s*$/;

		my $var_name  = $1;
		my $var_value = $2;

		my $has_var = 1;

		# replace every variable used in the $var_value by its content
		while ( $has_var )
		{
			if ( $var_value =~ /\$(\w+)/ )
			{
				my $found_var_name = $1;

#~ print "'$var_name' \t => \t '$var_value'\n"; # DEBUG
#~ print "\t\t found_var_name:$found_var_name \t => \t $global_conf->{ $found_var_name }\n"; # DEBUG

				$var_value =~ s/\$$found_var_name/$global_conf->{ $found_var_name }/;

				#~ print "'$var_name' \t => \t '$var_value'\n"; # DEBUG
			}
			else
			{
				$has_var = 0;
			}
		}

		#~ print "'$var_name' \t => \t '$var_value'\n"; # DEBUG

		$global_conf->{ $var_name } = $var_value;
	}

	close $global_conf_file;

	return eval { $global_conf->{ $parameter } } if $parameter;

	return $global_conf;
}

=begin nd
Function: setGlobalConfiguration

	Set a value to a configuration variable

Parameters:
	param - Configuration variable name.
	value - New value to be set on the configuration variable.

Returns:
	scalar - 0 on success, or -1 if the variable was not found.

Bugs:
	Control file handling errors.

See Also:
	<applySnmpChanges>

	Zapi v3: <set_ntp>
=cut
sub setGlobalConfiguration		# ( parameter, value )
{
	my ( $param, $value ) = @_;
	my $global_conf_file = &getGlobalConfiguration ( 'globalcfg' );
	my $output = -1;
	
	tie my @global_hf, 'Tie::File', $global_conf_file;
	foreach my $line ( @global_hf )
	{
		if ( $line=~ /^\$$param\s*=/ )
		{
			$line = "\$$param = \"$value\";";
			$output = 0;
		}
	}
	untie @gloabl_hf;
	
	return $output;
}

1;
