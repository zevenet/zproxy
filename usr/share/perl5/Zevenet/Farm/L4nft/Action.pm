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

=begin nd
Function: runL4FarmRestart

	Restart a l4xnat farm

Parameters:
	farmname - Farm name
	changes - This field lets to do the changes without stop the farm. The possible values are: "", blank for stop and start the farm, or "hot" for not stop the farm before run it

Returns:
	Integer - Error code: 0 on success or other value on failure

=cut

sub runL4FarmRestart    # ($farm_name,$writeconf,$type)
{
	my ( $farm_name, $writeconf, $type ) = @_;

	my $algorithm   = &getL4FarmParam( 'alg', $farm_name );
	my $fbootstatus = &getL4FarmParam( 'status', $farm_name );
	my $output      = 0;
	my $pidfile     = "/var/run/l4sd.pid";

	if (    $algorithm eq "leastconn"
		 && $fbootstatus eq "up"
		 && $writeconf eq "false"
		 && $type eq "hot"
		 && -e "$pidfile" )
	{
		open FILE, "<$pidfile";
		my $pid = <FILE>;
		close FILE;

		kill USR1 => $pid;
		$output = $?;    # FIXME
	}
	else
	{
		&_runL4FarmStop( $farm_name, $writeconf );
		$output = &_runL4FarmStart( $farm_name, $writeconf );
	}

	return $output;
}


=begin nd
Function: _runL4FarmStart

	Run a l4xnat farm

Parameters:
	farmname - Farm name
	writeconf - write this change in configuration status "true" or omit it "false"

Returns:
	Integer - return 0 on success or different of 0 on failure

FIXME:
	delete writeconf parameter. It is obsolet

=cut

sub _runL4FarmStart    # ($farm_name, $writeconf)
{
	my $farm_name = shift;    # input
#	my $writeconf = shift;    # input

#	require Zevenet::Net::Util;
#	require Zevenet::Netfilter;
	require Zevenet::Farm::Core;

	&zlog( "Starting farm $farm_name" ) if &debug == 2;

	my $status = 0;           # output

	&zenlog( "_runL4FarmStart << farm_name:$farm_name" )
	  if &debug;

#	my $fileconf = &getFarmFile( $farm_file );
	my $pid = &runNLBStart();
	if ( $pid <= 0 ) {
		return -1;
	}

	$status = &runNLBFarmStart( $farm_name );
	if ( $status <= 0 ) {
		return $status;
	}


#	# prio only apply rules to one server
#	if ( $server_prio && $$farm{ lbalg } eq 'prio' )
#	{
#		system ( "echo 10 > /proc/sys/net/netfilter/nf_conntrack_udp_timeout_stream" );
#		system ( "echo 5 > /proc/sys/net/netfilter/nf_conntrack_udp_timeout" );
#	}

	# Enable IP forwarding
	&setIpForward( 'true' );


	return $status;
}

=begin nd
Function: _runL4FarmStop

	Stop a l4xnat farm

Parameters:
	farmname - Farm name
	writeconf - write this change in configuration status "true" or omit it "false"

Returns:
	Integer - return 0 on success or other value on failure

=cut

sub _runL4FarmStop    # ($farm_name)
{
	my ( $farm_name ) = @_;

	#require Zevenet::Net::Util;
	require Zevenet::Farm::Core;

	&zlog( "Stopping farm $farm_name" ) if &debug > 2;

	my $farm_filename = &getFarmFile( $farm_name );
	my $status;       # output

	# Disable active l4xnat file
	my $pid = &getNLBPid();
	if ( $pid <= 0 ) {
		return -1;
	}

	&runNLBFarmStop( $farm_name );

	# Reload conntrack modules
#	if ( $$farm{ vproto } =~ /sip|ftp/ )
#	{
#		&loadL4Modules( $$farm{ vproto } );
#	}

	return $status;
}

=begin nd
Function: setL4NewFarmName

	Function that renames a farm

Parameters:
	newfarmname - New farm name
	farmname - Farm name

Returns:
	Array - Each line has the next format: ";server;ip;port;mark;weight;priority;status"

=cut

sub setL4NewFarmName    # ($farm_name,$new_farm_name)
{
	my ( $farm_name, $new_farm_name ) = @_;

}


=begin nd
Function: runNLBStart

	Launch the nftlb daemon and create the PID file. Do
	nothing if already is launched.

Parameters:
	none

Returns:
	Integer - return PID on success or <= 0 on failure

=cut

sub runNLBStart		# ()
{
	my $piddir = &getGlobalConfiguration( 'piddir' );
	my $nftlbd = &getGlobalConfiguration( 'zbindir' ) . "/nftlbd";
	my $pidof = &getGlobalConfiguration( 'pidof' );
	my $nlbpidfile = "$piddir/nftlb.pid";
	my $nlbpid = &getNLBPid( );

	if ( $nlbpid eq "-1" )
	{
		&logAndRun( "$nftlbd start" );
		$nlbpid = `$pidof nftlb`;

		if ( $nlbpid eq "") {
			return -1;
		}

		open FO, ">$nlbpidfile";
		print FO "$nlbpid";
		close FO;
	}

	return $nlbpid;
}


=begin nd
Function: runNLBStop

	Stop the nftlb daemon. Do nothing if is already stopped.

Parameters:
	none

Returns:
	Integer - return PID on success or <= 0 on failure

=cut

sub runNLBStop		# ()
{
	my $piddir = &getGlobalConfiguration( 'piddir' );
	my $nftlbd = &getGlobalConfiguration( 'zbindir' ) . "/nftlbd";
	my $pidof = &getGlobalConfiguration( 'pidof' );
	my $nlbpidfile = "$piddir/nftlb.pid";
	my $nlbpid = &getNLBPid( );

	if ( $nlbpid ne "-1" )
	{
		&logAndRun( "$nftlbd stop" );
	}

	return $nlbpid;
}


=begin nd
Function: runNLBFarmStart

	Start a new farm in nftlb

Parameters:
	farm_name - farm name to be started

Returns:
	Integer - 0 on success or -1 on failure

=cut

sub runNLBFarmStart		# ($farm_name)
{
	my ( $farm_name ) = @_;

	require Zevenet::Farm::Core;
	require Zevenet::Farm::L4xNAT::Config;

	my $farmfile = &getFarmFile( $farm_name );
	my $nlbpid = &getNLBPid( );

	if ( $nlbpid eq "-1" ) {
		return -1;
	}

	my $out = &httpNLBRequest( { farm => $farm_name, configfile => "$configdir/$farmfile", method => "POST", uri => "/farms", body =>  qq(\@$configdir/$farmfile)  } );
	if ( $out != 0 )
	{
		return $out;
	}
	&setL4FarmParam( 'status', "up", $farm_name );

	return $out;
}

=begin nd
Function: runNLBFarmStop

	Start a new farm in nftlb

Parameters:
	farm_name - farm name to be started

Returns:
	Integer - 0 on success or -1 on failure

=cut

sub runNLBFarmStop		# ($farm_name)
{
	my ( $farm_name ) = @_;

	require Zevenet::Farm::Core;

	my $farmfile = &getFarmFile( $farm_name );
	my $nlbpid = &getNLBPid( );

	if ( $nlbpid eq "-1" ) {
		return -1;
	}

	my $out = &setL4FarmParam( 'status', "down", $farm_name );

	return $out;
}

=begin nd
Function: getNLBPid

	Return the nftlb pid

Parameters:
	none

Returns:
	Integer - PID if successful or -1 on failure

=cut

sub getNLBPid
{
	my ( $farm_name ) = @_;
	my $piddir = &getGlobalConfiguration( 'piddir' );
	my $nlbpidfile = "$piddir/nftlb.pid";
	my $nlbpid = -1;

	if ( ! -f "$nlbpidfile" ) {
		return -1;
	}

	open FI, "<$nlbpidfile";
	$nlbpid = <FI>;
	close FI;

	if ( $nlbpid eq "") {
		return -1;
	}
	
	return $nlbpid;
}


1;
