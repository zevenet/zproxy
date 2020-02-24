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

sub include;

=begin nd
Function: setConntrackdConfig

	Apply ZCluster configuration to Conntrackd configuration file

Parameters:
	none - .

Returns:
	none - .

Bugs:

See Also:
	zcluster-manager, zapi/v3/cluster.cgi, <enableZCluster>
=cut

sub setConntrackdConfig
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	include 'Zevenet::Cluster';
	require Zevenet::SystemInfo;

	&zenlog( "Setting conntrackd configuration file", "info", "CLUSTER" );

	my $zcl_conf        = &getZClusterConfig();
	my $conntrackd_conf = &getGlobalConfiguration( 'conntrackd_conf' );

	open my $ct_file, '>', $conntrackd_conf;

	if ( !$ct_file )
	{
		&zenlog( "Could not open file $conntrackd_conf: $!", "warning", "CLUSTER" );
		return 1;
	}

	my $localhost      = &getHostname();
	my $remotehost     = &getZClusterRemoteHost();
	my $systemd_policy = '';

	# Check conntrackd version
	my $dpkg_query           = &getGlobalConfiguration( "dpkg_query" );
	my $connt_version_string = &logAndGet( "$dpkg_query --show conntrackd" );
	$connt_version_string =~ /:([0-9\.]+)/;
	$connt_version_string = $1;
	my @ct_version = split ( /\./, $connt_version_string );
	@ct_version = map { $_ + 0 } @ct_version;

	# WARNING: make sure the version of conntrackd is at least 1.4.4
	# WARNING: from conntrackd 1.4.4 the policy Systemd is required
	my $mayor_v = 1;
	my $minor_v = 4;
	my $patch_v = 4;

	if (
		    $ct_version[0] > $mayor_v
		 || ( $ct_version[0] == $mayor_v && $ct_version[1] > $minor_v )
		 || (    $ct_version[0] == $mayor_v
			  && $ct_version[1] == $minor_v
			  && $ct_version[2] > $patch_v )
		 || (    $ct_version[0] == $mayor_v
			  && $ct_version[1] == $minor_v
			  && $ct_version[2] == $patch_v )
	  )
	{
		$systemd_policy = "\n\tSystemd on\n";
	}

	my $ct_conf = "Sync {
\tMode FTFW {
\t\tDisableExternalCache Off
\t\tCommitTimeout 1800
\t\tPurgeTimeout 5
\t}

\tUDP {
\t\tIPv4_address $zcl_conf->{ $localhost }->{ ip }
\t\tIPv4_Destination_Address $zcl_conf->{ $remotehost }->{ ip }
\t\tPort 12000
\t\tInterface $zcl_conf->{_}->{ interface }
\t\tSndSocketBuffer 1249280
\t\tRcvSocketBuffer 1249280
\t\tChecksum on
\t}
}

General {
\tNice -20
\tHashSize 32768
\tHashLimit 131072
\tLogFile on
\tSyslog on
\tLockFile /var/lock/conntrack.lock
\tUNIX {
\t\tPath /var/run/conntrackd.ctl
\t\tBacklog 20
\t}
\tNetlinkBufferSize 2097152
\tNetlinkBufferSizeMaxGrowth 33554432
$systemd_policy
\tFilter From Kernelspace {
\t\tProtocol Accept {
\t\t\tTCP
\t\t\tUDP
\t\t\tICMP # This requires a Linux kernel >= 2.6.31
\t\t}
\t}
}

";

	print { $ct_file } "$ct_conf";

	close $ct_file;

	return 0;
}

=begin nd
Function: startConntrackd

	Start conntrackd service

Parameters:
	none - .

Returns:
	none - .

Bugs:

See Also:
	<enableZCluster>
=cut

sub startConntrackd
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	&zenlog( "Starting conntrackd", "info", "CLUSTER" );
	return &logAndRun( "/etc/init.d/conntrackd start" );
}

=begin nd
Function: stopConntrackd

	Stop conntrackd service

Parameters:
	none - .

Returns:
	none - .

Bugs:

See Also:
	<enableZCluster>, <disableZCluster>
=cut

sub stopConntrackd
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	&zenlog( "Stopping conntrackd", "info", "CLUSTER" );
	&logAndRun( "/etc/init.d/conntrackd stop" );

	if ( &getConntrackdRunning() )
	{
		&zenlog( "Forcing conntrackd to stop", "info", "CLUSTER" );
		&logAndRun( "pkill conntrackd" );
	}

	return 0;
}

=begin nd
Function: getConntrackdRunning

	Get if the the conntrackd service is running.

Parameters:
	none - .

Returns:
	Scalar - Boolean. TRUE if conntrackd is running, FALSE otherwise.

Bugs:

See Also:
	zcluster-manager, <stopConntrackd>, <enableZCluster>, <disableZCluster>, <getZCusterStatusInfo>
=cut

sub getConntrackdRunning
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	return ( &logAndRunCheck( "pgrep conntrackd" ) == 0 );
}

1;
