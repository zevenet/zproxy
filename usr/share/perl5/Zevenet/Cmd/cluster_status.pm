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
use warnings;
use Zevenet::Config;
use Zevenet::SystemInfo;
include 'Zevenet::Cluster';

my $DEBUG = 0;

## Cluster not configured

my $cl_status = &getZClusterStatus();
unless ( $cl_status )
{
	# cluster not configured
	print "Not configured\n" if $DEBUG;
	exit 2;
}

## Cluster configured

my $cl_conf    = &getZClusterConfig();
my $localhost  = getHostname();
my $remotehost = &getZClusterRemoteHost();

# n: ka, zi, ct, role
my $local_n  = &getZClusterNodeStatusInfo();
my $remote_n = &getZClusterNodeStatusInfo( $cl_conf->{ $remotehost }->{ ip } );

## VRRP protocol instance

my $vrrp_local_rc  = $local_n->{ ka };
my $vrrp_remote_rc = $remote_n->{ ka };
my $vrrp_ok        = ( !$vrrp_local_rc && !$vrrp_remote_rc );

unless ( $vrrp_ok )
{
	if ( $DEBUG )
	{
		print "VRRP NO OK\n" if $DEBUG;
		&zdebug();
	}

	exit 1;
}

# Sync daemon

my $sync_local_rc  = $local_n->{ zi };
my $sync_remote_rc = $remote_n->{ zi };

my $sync_local_ok  = ( $sync_local_rc == 0 );
my $sync_remote_ok = ( $sync_remote_rc == 0 );

## Check all
my $master_local  = ( $sync_local_ok  && $local_n->{ role } eq 'master' );
my $master_remote = ( $sync_remote_ok && $remote_n->{ role } eq 'master' );

my $one_master = &xor_op( $master_local, $master_remote );

if (    ( $master_local && !$sync_local_ok )
	 || ( $master_remote && !$sync_remote_ok )
	 || ( $sync_local_ok && $sync_remote_ok ) )
{
	if ( $DEBUG )
	{
		&zdebug();
		print "Sync NO OK\n";
	}

	exit 1;
}

if ( $vrrp_ok && $one_master )
{
	# all ok
	print "Master\n"                      if $master_local;
	print "Slave\n"                       if $master_remote;
	system ( "grep RSS /proc/$$/status" ) if $DEBUG;
	exit 0;
}

if ( $one_master )
{
	print "$local_n->{ role }\n" if $DEBUG;
}
else
{
	print "Error\n" if $DEBUG;
}

if ( $DEBUG )
{
	&zdebug();
}

print "Exit Error\n" if $DEBUG;
exit 1;

sub xor_op
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $a, $b ) = @_;

	return ( ( $a && !$b ) || ( !$a && $b ) );
}

sub zdebug
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	print "cl_status:$cl_status\n";
	print "localhost:$localhost\n";
	print "remotehost:$remotehost\n";
	print "vrrp_local_rc:$vrrp_local_rc\n";
	print "vrrp_remote_rc:$vrrp_remote_rc\n";
	print "vrrp_ok:$vrrp_ok\n";
	print "sync_local_rc:$sync_local_rc\n"   if defined $sync_local_rc;
	print "sync_remote_rc:$sync_remote_rc\n" if defined $sync_remote_rc;
	print "master_local:$master_local\n"     if defined $master_local;
	print "master_remote:$master_remote\n"   if defined $master_remote;
	print "one_master:$one_master\n"         if defined $one_master;
	system ( "grep RSS /proc/$$/status" );
}

