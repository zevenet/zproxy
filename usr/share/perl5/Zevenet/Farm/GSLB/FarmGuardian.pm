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

use strict;

my $configdir = &getGlobalConfiguration('configdir');

=begin nd
Function: getGSLBCommandInExtmonFormat

	Transform command with farm guardian format to command with extmon format,
	this function is used to show the command in GUI.

Parameters:
	cmd - command with farm guardian format
	port - port where service is checking

Returns:
	String - command with extmon format
                
See Also:
	changeCmdToFGFormat
                
More info:
	Farmguardian Fotmat: bin -x option...
	Extmon Format: "bin", "-x", "option"...
                
=cut
sub getGSLBCommandInExtmonFormat	# ( $cmd, $port )
{
	my ( $cmd, $port ) = @_;

	my $libexec_dir = &getGlobalConfiguration ( 'libexec_dir' );
	my @aux = split ( ' ', $cmd );
	my $newCmd = "\"$libexec_dir/$aux[0]\"";
	my $stringArg;
	my $flag;

	splice @aux, 0, 1;

	foreach my $word ( @aux )
	{
		# Argument is between ""
		if ( $word =~ /^".+"$/ )
		{
			$word =~ s/^"//;
			$word =~ s/"$//;
		}

		# finish a string
		if ( $word =~ /\"$/ && $flag )
		{
			$flag = 0;
			chop $word;
			$word = "$stringArg $word";
		}

		# part of a string
		elsif ( $flag )
		{
			$stringArg .= " $word";
			next;
		}

		# begin a string
		elsif ( $word =~ /^"\w/ )
		{
			$flag = 1;
			$word =~ s/^.//;
			$stringArg = $word;
			next;
		}

		if ( $word eq 'PORT' )
		{
			$word = $port;
		}

		$word =~ s/HOST/%%ITEM%%/;
		if ( !$flag )
		{
			$newCmd .= ", \"$word\"";
		}
	}
	$newCmd =~ s/^, //;

	return $newCmd;
}

=begin nd
Function: getGSLBCommandInFGFormat

	Transform command with extmon format to command with fg format,
	this function is used to show the command in GUI.

Parameters:
	cmd - command with extmon format
	port - port where service is checking

Returns:
	newCmd  - command with farm guardian format
                
See Also:
	changeCmdToExtmonFormat
                
More info:
	Farmguardian Fotmat: bin -x option...
	Extmon Format: "bin", "-x", "option"...
			
=cut
sub getGSLBCommandInFGFormat	# ( $cmd, $port )
{
	my ( $cmd, $port ) = @_;

	my $libexec_dir = &getGlobalConfiguration ( 'libexec_dir' );
	my @aux = split ( ', ', $cmd );
	my $newCmd = $aux[0];
	my $flagPort;

	splice @aux, 0, 1;

	$newCmd =~ s/$libexec_dir\///;
	$newCmd =~ s/^"(.+)"$/$1/;

	foreach my $word ( @aux )
	{
		if ( $word =~ '-p' )
		{
			$flagPort = 1;
		}

		# dns only can check one port
		if ( $flagPort && $word =~ /^"$port"$/ )
		{
			$word     = "PORT";
			$flagPort = 0;
		}

		# change HOST param from FG to %%ITEM%% from extmon
		$word =~ s/%%ITEM%%/HOST/;

		# remove " only if $word isn't a string
		if ( $word !~ / / )
		{
			$word =~ s/^"(.+)"$/$1/;
		}
		$newCmd .= " $word";
	}
	return $newCmd;
}

=begin nd
Function: getGSLBFarmGuardianParams

	Get farmguardian configuration

Parameters:
	farmname - Farm name
	service - Service name

Returns:         
	@output = ( time, cmd ), "time" is interval time to repeat cmd and "cmd" is command to check backend
	
FIXME:
	Change output to a hash

=cut
sub getGSLBFarmGuardianParams # ( farmName, $service )
{
	my ( $fname, $service ) = @_;

	require Zevenet::Farm::Config;

	my $port = &getFarmVS( $fname, $service, "dpc" );
	my $ftype = &getFarmType( $fname );
	my $cmd;
	my $time;
	my $flagSvc = 0;

	require Tie::File;
	tie my @file, 'Tie::File', "$configdir\/$fname\_$ftype.cfg\/etc\/config";

	foreach my $line ( @file )
	{
		# Begin service block
		if ( $line =~ /^\t$service.+ =>/ )
		{
			$flagSvc = 1;
		}
		elsif ( $flagSvc )
		{
			# get interval time
			if ( $line =~ /interval = (\d+),/ )
			{
				$time = $1;
				next;
			}

			# get cmd
			elsif ( $line =~ /cmd = \[(.+)\],/ )
			{
				$cmd = $1;
				$cmd = getGSLBCommandInFGFormat( $cmd, $port );
				next;
			}
		}
		if ( $flagSvc && $line =~ /\t}/ )
		{
			last;
		}
	}

	# $cmd it's initialized "1" for avoid systasis error
	if ( $cmd eq "1" )
	{
		$cmd = "";
	}

	my @config;
	push @config, $time, $cmd;
	untie @file;

	return @config;
}

=begin nd
Function: setGSLBFarmGuardianParams

	Change gslb farm guardian parameters

Parameters:
	farmname - Farm name
	service - Service name
	param - Parameter to change. The availabe parameters are: "cmd" farm guardian command and "time" time between checks
	value - Value for the param

Returns:
	Integer - Error code: 0 on success or -1 on failure

=cut
sub setGSLBFarmGuardianParams	# ( farmName, service, param, value );
{
	my ( $fname, $service, $param, $value ) = @_;
	my $ftype = &getFarmType( $fname );
	my @file;
	my $flagSvc = 0;
	my $err     = -1;
	my $port = &getGSLBFarmVS ($fname,$service, 'dpc');

	tie @file, 'Tie::File', "$configdir\/$fname\_$ftype.cfg\/etc\/config";

	foreach my $line ( @file )
	{
		# Begin service block
		if ( $line =~ /${service}_fg_$port =>/ )
		{
			$flagSvc = 1;
		}

		# End service block
		elsif ( $flagSvc && $line =~ /^\t\}/ )
		{
			&zenlog( "GSLB FarmGuardian has corrupt fileconf", "Error" );
		}
		elsif ( $flagSvc && $line =~ /$param/ )
		{
			# change interval time
			if ( $line =~ /interval/ )
			{
				$line =~ s/interval =.*,/interval = $value,/;
				$err = 0;
				next;
			}

			# change cmd
			elsif ( $line =~ /cmd/ )
			{
				my $cmd = &getGSLBCommandInExtmonFormat( $value, $port );
				$line =~ s/cmd =.*,/cmd = \[$cmd\],/;
				$err = 0;
				last;
			}
		}

		# change timeout if we are changing interval. timeout = interval / 2
		elsif ( $line =~ /timeout =/ && $flagSvc && $param =~ /interval/ )
		{
			my $timeout = int ( $value / 2 );
			$line =~ s/timeout =.*,/timeout = $timeout,/;
			$err = 0;
			last;
		}

	}
	untie @file;

	return $err;
}

=begin nd
Function: setGSLBDeleteFarmGuardian

	Delete Farm Guardian configuration from a gslb farm configuration

Parameters:
	farmname - Farm name
	service - Service name

Returns:
	Integer - Error code: 0 on success or -1 on failure
	
=cut
sub setGSLBDeleteFarmGuardian	# ( $fname, $service )
{
	my ( $fname, $service ) = @_;
	my $ftype   = &getFarmType( $fname );
	my $err     = -1;
	my $index   = 0;
	my $flagSvc = 0;

	tie my @file, 'Tie::File', "$configdir\/$fname\_$ftype.cfg\/etc\/config";

	my $start_i;
	my $end_i;

	foreach my $line ( @file )
	{
		# Begin service block
		if ( $line =~ /^\t${service}_fg_.+ =>/ )
		{
			$flagSvc = 1;
			$start_i = $index;
		}
		if ( $flagSvc )
		{
			if ( $line =~ /^\t}/ )
			{
				$err   = 0;
				$end_i = $index;
				last;
			}
		}
		$index++;
	}
	splice @file, $start_i, $end_i - $start_i + 1;
	untie @file;

	return $err;
}

=begin nd
Function: getGSLBFarmFGStatus

	Reading farmguardian status for a GSLB service

Parameters:
	farmname - Farm name
	service - Service name

Returns:
	Scalar - "true" if fg is enabled, "false" if fg is disable or -1 on failure

=cut
sub getGSLBFarmFGStatus	# ( fname, service )
{
	my ( $fname, $service ) = @_;

	my $ftype  = &getFarmType( $fname );
	my $output = -1;

	use Tie::File;

	# select all ports used in plugins
	opendir ( DIR, "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/" );
	my @pluginlist = readdir ( DIR );
	closedir ( DIR );

	foreach my $plugin ( @pluginlist )
	{
		if ( $plugin !~ /^\./ )
		{
			my @fileconf = ();

			tie @fileconf, 'Tie::File',
			  "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/$plugin";

			# looking for in plugins
			foreach my $line ( @fileconf )
			{
				# find service
				if ( $line =~ /$service =>/ )
				{
					$output = 0;
				}

				# find line with status
				if ( !$output && $line =~ /service_types/ )
				{
					# if service_type point to tpc_port, fg is down
					if ( $line =~ /service_types = tcp_\d+/ )
					{
						$output = "false";
					}

					# if service_type point to fg, fg is up
					elsif ( $line =~ /service_types = ${service}_fg_\d+/ )
					{
						$output = "true";
					}
					else
					{
						# file corrupt
						$output = -1;
					}
					last;
				}

				# didn't find
				if ( !$output && $line =~ /\}/ )
				{
					$output = -1;
					last;
				}
			}
			untie @fileconf;
		}
	}
	return $output;
}

=begin nd
Function: enableGSLBFarmGuardian

	Enable or disable a service farmguardian in gslb farms

Parameters:
	farmname - Farm name
	service - Service name
	option - The options are "up" to enable fg or "down" to disable fg

Returns:
	Integer - Error code: 0 on success or -1 on failure
	
=cut
sub enableGSLBFarmGuardian	# ( $fname, $service, $option )
{
	my ( $fname, $service, $option ) = @_;

	my $ftype  = &getFarmType( $fname );
	my $output = -1;

	use Tie::File;

	# select all ports used in plugins
	opendir ( DIR, "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/" );
	my @pluginlist = readdir ( DIR );
	closedir ( DIR );
	foreach my $plugin ( @pluginlist )
	{
		if ( $plugin !~ /^\./ )
		{
			my @fileconf = ();

			tie @fileconf, 'Tie::File',
			  "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/$plugin";

			foreach my $line ( @fileconf )
			{
				if ( $line =~ /$service =>/ )
				{
					$output = 1;
				}
				if ( $output == 1 )
				{
					if ( $option =~ /true/ && $line =~ /service_types = tcp_(\d+)/ )
					{
						$line   = "\t\tservice_types = ${service}_fg_$1";
						$output = 0;
						last;
					}
					elsif ( $option =~ /false/ && $line =~ /service_types = ${service}_fg_(\d+)/ )
					{
						$line   = "\t\tservice_types = tcp_$1";
						$output = 0;
						last;
					}
				}
			}

			untie @fileconf;
		}
	}
	return $output;
}

1;
