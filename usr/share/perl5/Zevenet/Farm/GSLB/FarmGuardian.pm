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

my $configdir = &getGlobalConfiguration( 'configdir' );

require Zevenet::FarmGuardian;
require Zevenet::Farm::Core;
require Tie::File;

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

sub getGSLBCommandInExtmonFormat    # ( $cmd, $port )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $cmd, $port ) = @_;

	my $libexec_dir = &getGlobalConfiguration( 'libexec_dir' );
	my @aux         = split ( ' ', $cmd );
	my $newCmd      = "\"$libexec_dir/$aux[0]\"";
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

sub getGSLBFarmGuardianParams    # ( farmName, $service )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname, $service ) = @_;

	require Zevenet::FarmGuardian;

	my $fg = &getFGFarm( $fname, $service );
	if ( $fg )
	{
		my $fg_obj = &getFGObject( $fg );
		return ( $fg_obj->{ interval }, $fg_obj->{ command } );
	}

	# not fg found
	return ( "", "" );
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

sub setGSLBFarmGuardianParams    # ( farmName, service, param, value );
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname, $service, $param, $value ) = @_;

	# bugfix
	$param = 'interval' if ( $param eq 'time' );

	my @file;
	my $flagSvc = 0;
	my $err     = -1;

	include 'Zevenet::Farm::GSLB::Service';

	my $port = &getGSLBFarmVS( $fname, $service, 'dpc' );

	tie @file, 'Tie::File', "$configdir\/$fname\_gslb.cfg\/etc\/config";

	foreach my $line ( @file )
	{
		# Begin service block
		if ( $line =~ /\s${service}_fg_$port =>/ )
		{
			$flagSvc = 1;
		}

		# End service block
		elsif ( $flagSvc && $line =~ /^\t\}/ )
		{
			&zenlog( "GSLB FarmGuardian has corrupt fileconf", "error", "GSLB" );
		}
		elsif ( $flagSvc && $line =~ /$param/ )
		{
			# change interval time
			if ( $line =~ /interval =/ )
			{
				$line =~ s/interval =.*,/interval = $value,/;
				$err = 0;
				last;
			}

			# change cmd
			elsif ( $line =~ /cmd = / )
			{
				my $cmd = &getGSLBCommandInExtmonFormat( $value, $port );
				$line =~ s/cmd =.*,/cmd = \[$cmd\],/;
				$err = 0;
				last;
			}
		}

		# change timeout if we are changing interval. timeout = interval / 2
		elsif ( $line =~ /timeout =/ && $flagSvc && $param =~ /interval =/ )
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

sub setGSLBDeleteFarmGuardian    # ( $fname, $service )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname, $service ) = @_;

	my $err     = -1;
	my $index   = 0;
	my $flagSvc = 0;

	tie my @file, 'Tie::File', "$configdir\/$fname\_gslb.cfg\/etc\/config";

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

	if ( $flagSvc )
	{
		splice @file, $start_i, $end_i - $start_i + 1;
	}

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

sub getGSLBFarmFGStatus    # ( fname, service )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname, $service ) = @_;

	require Zevenet::FarmGuardian;

	my $fg = &getFGFarm( $fname, $service );

	return ( $fg ) ? "true" : "false";
}

=begin nd
Function: enableGSLBFarmGuardian

	Enable or disable a service farmguardian in gslb farms

Parameters:
	farmname - Farm name
	service - Service name
	option - The options are "true" to enable fg or "false" to disable fg

Returns:
	Integer - Error code: 0 on success or -1 on failure

=cut

sub enableGSLBFarmGuardian    # ( $fname, $service, $option )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname, $service, $option ) = @_;

	my $output = -1;
	my $port;

	require Tie::File;

	# select all ports used in plugins
	opendir ( DIR, "$configdir\/$fname\_gslb.cfg\/etc\/plugins\/" );
	my @pluginlist = readdir ( DIR );
	closedir ( DIR );

	foreach my $plugin ( @pluginlist )
	{
		if ( $plugin !~ /^\./ )
		{
			my @fileconf = ();

			tie @fileconf, 'Tie::File',
			  "$configdir\/$fname\_gslb.cfg\/etc\/plugins\/$plugin";

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
						$port   = $1;
						$line   = "\t\tservice_types = ${service}_fg_$port";
						$output = 0;
						last;
					}
					elsif ( $option =~ /false/ && $line =~ /service_types = ${service}_fg_(\d+)/ )
					{
						$port   = $1;
						$line   = "\t\tservice_types = tcp_$port";
						$output = 0;
						last;
					}
				}
			}

			untie @fileconf;
		}
	}

	include 'Zevenet::Farm::GSLB::Validate';
	my $n_used = &getGSLBCheckPort( $fname, $port );
	if ( !$output )
	{
		# create default check if this does not exist
		if ( $option =~ /false/ and $n_used == 1 )
		{
			include 'Zevenet::Farm::GSLB::Service';
			$output = &addGSLBDefCheck( $fname, $port );
		}

		# no other service is using it, delete it
		elsif ( $option =~ /true/ and $n_used == 0 )
		{
			include 'Zevenet::Farm::GSLB::Config';
			$output = &setGSLBRemoveTcpPort( $fname, $port );
		}

		return 3 if ( $output );
	}

	return $output;
}

sub createGSLBFg
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fg_name, $farm, $srv ) = @_;

	my $fg_st = &getFGObject( $fg_name );

	# get port
	include 'Zevenet::Farm::GSLB::Service';
	my $port = &getGSLBFarmVS( $farm, $srv, 'dpc' );

	my $cmd      = $fg_st->{ command };
	my $interval = $fg_st->{ interval } // 6;
	my $timeout  = 3;
	{
		# it is the recommended value
		use integer;
		$timeout = $fg_st->{ interval } / 2;
	}

# force to gslb timeout will be same than check timeout, to avoid problems when it is not defined
	if ( $cmd =~ / -t\s+(\d+)/ )
	{
		$timeout = $1;
	}
	$cmd = &getGSLBCommandInExtmonFormat( $cmd, $port );

	# apply conf
	my $newFG =
	    "\t${srv}_fg_$port => {\n"
	  . "\t\tplugin = extmon,\n"
	  . "\t\tdirect = true,\n"
	  . "\t\tinterval = $interval,\n"
	  . "\t\ttimeout = $timeout,\n"
	  . "\t\tcmd = [$cmd],\n" . "\t}\n";

	# create the new port configuration
	require Zevenet::File;
	my $ffile = &getFarmFile( $farm );
	my $err = &insertFileWithPattern( "$configdir/$ffile/etc/config", [$newFG],
									  "service_types => \\{", 'after' );

	return $err;
}

sub linkGSLBFg    # ( $fg_name, $farm, $srv );
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fg_name, $farm, $srv ) = @_;
	my $err = 0;

	$err = &createGSLBFg( $fg_name, $farm, $srv );
	return 1 if ( $err );

	$err = &enableGSLBFarmGuardian( $farm, $srv, 'true' );

	if ( $err )
	{
		#~ &setGSLBDeleteFarmGuardian( $farm, $srv );
		return 2;
	}

# the gslb fg is put in the start process, then, it is necessary to restart the farm
	require Zevenet::Farm::Action;
	&setFarmRestart( $farm );

	return $err;
}

sub unlinkGSLBFg
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname, $service ) = @_;

	my $out = &setGSLBDeleteFarmGuardian( $fname, $service );

	$out += &enableGSLBFarmGuardian( $fname, $service, 'false' );

	return 1 if ( $out );

	if ( !$out )
	{
		require Zevenet::Farm::Action;
		&setFarmRestart( $fname );
	}

	return $out;
}

sub updateGSLBFg
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $fg_name = shift;

	my $fg_st = &getFGObject( $fg_name );
	my $farm;
	my $srv;
	my $err = 0;

	foreach my $f ( @{ $fg_st->{ farms } } )
	{
		if ( $f =~ /^([^_]+)_(.+)/ )
		{
			$farm = $1;
			$srv  = $2;
		}
		else
		{
			next;
		}

		next if ( &getFarmType( $farm ) ne 'gslb' );

		$err += &unlinkGSLBFg( $farm, $srv );
		$err += &linkGSLBFg( $fg_name, $farm, $srv );
	}

	return $err;
}

1;

