###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2016 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
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

sub setConntrackdConfig
{
	&zenlog("Setting conntrackd configuration file");
	
	my $zcl_conf = &getZClusterConfig();
	my $conntrackd_conf = &getGlobalConfiguration('conntrackd_conf');

	open my $ct_file, '>', $conntrackd_conf;

	if ( ! $ct_file )
	{
		&zenlog("Could not open file $conntrackd_conf: $!");
		return 1;
	}

	my $localhost = &getHostname();
	my $remotehost = &getZClusterRemoteHost();

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
\tNetlinkBufferSizeMaxGrowth 8388608

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

sub startConntrackd
{
	&zenlog("Starting conntrackd");
	return system("/etc/init.d/conntrackd start ");
}

sub stopConntrackd
{
	&zenlog("Stopping conntrackd");
	system("/etc/init.d/conntrackd stop");

	if ( getConntrackdRunning() )
	{
		&zenlog("Forcing conntrackd to stop");
		system("pkill conntrackd >/dev/null 2>&1");
	}

	return 0;
}

sub getConntrackdRunning
{
	return ( system( "pgrep conntrackd >/dev/null" ) == 0 );
}

1;
