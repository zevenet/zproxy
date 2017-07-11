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

use Zevenet::Farm::HTTP::Config;
use Zevenet::Farm::L4xNAT::Config;
use Zevenet::Farm::GSLB::Config;
use Zevenet::Farm::Datalink::Config;

=begin nd
Function: getFarmPort

	Returns farm port
	
Parameters:
	farmname - Farm name

Returns:
	Integer - port of farm or -1 on failure

Bugs:
	Only it is used by tcp farms
	DUPLICATE function. Use "getFarmVip" 
	for http profile, return error response

See Also:
	setFarmVirtualConf
=cut
sub getFarmPort    # ($farm_name)
{
	my $farm_name = shift;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &getHTTPFarmPort( $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$output = &getL4FarmVip( 'vipp', $farm_name );
	}

	if ( $farm_type eq "gslb" )
	{
		$output = &getGSLBFarmVip( 'vipp', $farm_name );
	}

	if ( $farm_type eq "datalink" )
	{
		$output = &getDatalinkFarmVip( 'vipp', $farm_name );
	}

	return $output;
}

=begin nd
Function: getFarmVip

	Returns farm vip or farm port

Parameters:
	tag - requested parameter. The options are "vip" for virtual ip or "vipp" for virtual port
	farmname - Farm name

Returns:
	Scalar - return vip or port of farm or -1 on failure

Bugs:
	WARNING: vipps parameter is only used in tcp farms. Soon this parameter will be obsolete.

See Also:
	setFarmVirtualConf
=cut
sub getFarmVip    # ($info,$farm_name)
{
	my ( $info, $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &getHTTPFarmVip( $info, $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$output = &getL4FarmVip( $info, $farm_name );
	}

	if ( $farm_type eq "datalink" )
	{
		$output = &getDatalinkFarmVip( $info, $farm_name );
	}

	if ( $farm_type eq "gslb" )
	{
		$output = &getGSLBFarmVip( $info, $farm_name );
	}

	return $output;
}

=begin nd
Function: getFarmStatus

	Return farm status checking if pid file exists
	 
Parameters:
	farmname - Farm name

Returns:
	String - "down", "up" or -1 on failure

NOTE:
	Generic function
		
=cut
sub getFarmStatus    # ($farm_name)
{
	my $farm_name = shift;

	my $output = -1;
	return $output if !defined ( $farm_name );    # farm name cannot be empty

	my $farm_type = &getFarmType( $farm_name );
	my $piddir = &getGlobalConfiguration('piddir');

	# for every farm type but datalink or l4xnat
	if ( $farm_type ne "datalink" && $farm_type ne "l4xnat" )
	{
		my $pid = &getFarmPid( $farm_name );
		my $running_pid;
		$running_pid = kill ( 0, $pid ) if $pid ne "-";

		if ( $pid ne "-" && $running_pid )
		{
			$output = "up";
		}
		else
		{
			if ( $pid ne "-" && !$running_pid )
			{
				unlink &getGSLBFarmPidFile( $farm_name ) if ( $farm_type eq 'gslb' );
				unlink "$piddir\/$farm_name\_pound.pid"  if ( $farm_type =~ /http/ );
			}

			$output = "down";
		}
	}
	else
	{
		# Only for datalink and l4xnat
		if ( -e "$piddir\/$farm_name\_$farm_type.pid" )
		{
			$output = "up";
		}
		else
		{
			$output = "down";
		}
	}

	return $output;
}

=begin nd
Function: getFarmPid

	Returns farm PID
		
Parameters:
	farmname - Farm name

Returns:
	Integer - return pid of farm, '-' if pid not exist or -1 on failure
			
=cut
sub getFarmPid    # ($farm_name)
{
	my $farm_name = shift;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &getHTTPFarmPid( $farm_name );
	}

	if ( $farm_type eq "gslb" )
	{
		$output = &getGSLBFarmPid( $farm_name );
	}

	return $output;
}

=begin nd
Function: getFarmLock

	Check if a farm is locked. A farm locked need to restart. 
		
Parameters:
	farmname - Farm name

Returns:
	Scalar - Return content of lock file if it is locked or -1 the farm is not locked

NOTE:
	Generic function
		
=cut
sub getFarmLock    # ($farm_name)
{
	my $farm_name = shift;
	my $output = -1;
	my $lockfile = "/tmp/$farm_name.lock";

	if ( -e "$lockfile" )
	{
		open my $fh, "$lockfile";
		read $fh, $output, 255;
		close $fh;
	}

	return $output;
}

=begin nd
Function: setFarmLock

	Set the lock status to "on" or "off"
	If the new status in "on" it's possible to set a message inside
		
Parameters:
	farmname - Farm name
	status - This parameter can value "on" or "off"
	message - Text for lock file

Returns:
	Integer - Always return 0
	
FIXME:
	always return 0

NOTE:
	Generic function
	
=cut
sub setFarmLock    # ($farm_name, $status, $msg)
{
	my ( $farm_name, $status, $msg ) = @_;
	my $output = 0;
	my $lockfile = "/tmp/$farm_name.lock";
	my $lockstatus = &getFarmLock( "$farm_name" );

	if ( $status eq "on" && $lockstatus == -1 )
	{
		open my $fh, ">$lockfile";
		print $fh "$msg";
		close $fh;
	}

	if ( $status eq "off" )
	{
		unlink ( "$lockfile" ) if -e "$lockfile";
	}

	return $output;
}

=begin nd
Function: getFarmBootStatus

	Return the farm status at boot zevenet
	 
Parameters:
	farmname - Farm name

Returns:
	scalar - return "down" if the farm not run at boot or "up" if the farm run at boot

=cut
sub getFarmBootStatus    # ($farm_name)
{
	my $farm_name = shift;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = "down";

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &getHTTPFarmBootStatus( $farm_name );
	}

	if ( $farm_type eq "gslb" )
	{
		$output = &getGSLBFarmBootStatus( $farm_name );
	}

	if ( $farm_type eq "datalink" )
	{
		$output = &getDatalinkFarmBootStatus( $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$output = &getL4FarmBootStatus( $farm_name );
	}

	return $output;
}

=begin nd
Function: getFarmProto

	Return basic transport protocol used by the farm protocol
		
Parameters:
	farmname - Farm name

Returns:
	String - "udp" or "tcp"
	
BUG:
	Gslb works with tcp protocol too
	
FIXME:
	Use getL4ProtocolTransportLayer to get l4xnat protocol
	
=cut
sub getFarmProto    # ($farm_name)
{
	my $farm_name = shift;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	if ( $farm_type eq "l4xnat" )
	{
		open FI, "<", "$configdir/$farm_filename";
		my $first = "true";
		while ( my $line = <FI> )
		{
			if ( $line ne "" && $first eq "true" )
			{
				$first = "false";
				my @line = split ( "\;", $line );
				$output = $line[1];
			}
		}
		close FI;
	}
	
	elsif ( $farm_type eq "gslb" )
	{
		$output = "UDP";
	}
	
	elsif ( $farm_type eq "http" )
	{
		$output = "TCP";
	}

	return $output;
}

1;
