#!/usr/bin/perl

#~ use strict;
#~ use warnings;

use Sys::Hostname;

require '/usr/local/zenloadbalancer/config/global.conf';
require "/usr/local/zenloadbalancer/www/functions_ext.cgi";

my $DEBUG = 0;
my $filecluster = &getGlobalConfiguration('filecluster');
my $pidof = &getGlobalConfiguration('pidof');


## Cluster configured

if ( ! -e $filecluster )
{
	# cluster not configured
	print "Not configured\n" if $DEBUG;
	exit 2;
}

#get cluster's members data
my ( undef, $cl_lip, undef, $cl_rip ) = &getClusterConfigMembers( hostname(), $filecluster );
my ( undef, $clstatus ) = &getClusterConfigTypeStatus( $filecluster );

if ( $clstatus ne 'UP' )
{
	# cluster not configured
	print "Not configured\n" if $DEBUG;
	exit 2;
}


## ZenLatency

# local zenlatency
my $zlatency_local = `$pidof -x ucarp`;
my $lat_loc_stat = $?;
chomp $zlatency_local;
# remote zenlatency
my $zlatency_remote =
  `ssh -o \"ConnectTimeout=5\" -o \"StrictHostKeyChecking=no\" root\@$cl_rip \"pidof -x ucarp \" 2>&1`;
my $lat_rem_stat = $?;
chomp $zlatency_remote;

my $zlatency_ok = ( !$lat_loc_stat && !$lat_rem_stat && $zlatency_local && $zlatency_remote );

if ( !$zlatency_ok ){
	print "Latency NO OK\n" if $DEBUG;
	exit 1;
}

## Cluster interface

my $ip_bin = &getGlobalConfiguration('ip_bin');
my ( $vipcl ) = &getClusterConfigVipInterface( $filecluster );
my $vip_loc_stat = $?;
# local
my $vip_local = grep ( / $vipcl\//, `$ip_bin addr list`);
# remote
my $vip_remote = grep ( / $vipcl\//,
  `ssh -o \"ConnectTimeout=5\" -o \"StrictHostKeyChecking=no\" root\@$cl_rip \"$ip_bin addr list\" `);
my $vip_rem_stat = $?;
# ^ == xor
my $vip_ok = (!$vip_rem_stat && !$vip_loc_stat) && &xor_op( $vip_local, $vip_remote );

if ( !$vip_ok ){
	print "vip NO OK\n" if $DEBUG;
	exit 1;
}

# ZenInotify

# local zeninotify
my $zenino_local = grep ( //, `$pidof -x zeninotify.pl`);
my $zenino_loc_stat = $?;
# local zeninotify
my $zenino_remote = grep ( //,
  `ssh -o \"ConnectTimeout=5\" -o \"StrictHostKeyChecking=no\" root\@$cl_rip "pidof -x zeninotify.pl" `);
my $zenino_rem_stat = $?;

my $zenino_loc_ok = (!$zenino_loc_stat) && $zenino_local;
my $zenino_rem_ok = (!$zenino_rem_stat) && $zenino_remote;

## Check all
my $master_local = ($vip_local && $zenino_local);
my $master_remote = ($vip_remote && $zenino_remote);
my $same_node = &xor_op( $master_local, $master_remote );

if ( ($master_local && !$zenino_loc_ok) || ($master_remote && !$zenino_rem_ok) ){
	print "zenino NO OK\n" if $DEBUG;
	exit 1;
}

if ( $zlatency_ok && $vip_ok && $same_node )
{
	# all ok
	print "Master\n" if $master_local;
	print "Slave\n" if $master_remote;
	system("grep RSS /proc/$$/status") if $DEBUG;
	exit 0;
}

if ( $same_node )
{
	if ( $master_local )
	{
		print "Master\n" if $DEBUG;
	}
	elsif ( $master_remote )
	{
		my $maintenance = grep ( /-k 100/, `ps aux | grep $ucarp`);

		if ( $maintenance )
		{
			print "Maintenance\n" if $DEBUG;
		}
		else
		{
			print "Slave\n" if $DEBUG;
		}
	}
}
else
{
	print "Error\n" if $DEBUG;
}

if ( $DEBUG )
{
	print "cl_lip:$cl_lip\n";
	print "cl_rip:$cl_rip\n";
	print "clstatus:$clstatus\n";
	print "zlatency_local:$zlatency_local\n";
	print "zlatency_remote:$zlatency_remote\n";
	print "zlatency_ok:$zlatency_ok\n";
	print "vipcl:$vipcl\n";
	print "vip_local:$vip_local\n";
	print "vip_remote:$vip_remote\n";
	print "vip_ok:$vip_ok\n";
	print "zenino_local:$zenino_local\n";
	print "zenino_remote:$zenino_remote\n";
	print "zenino_ok:$zenino_ok\n";
	print "master_local:$master_local\n";
	print "master_remote:$master_remote\n";
	print "same_node:$same_node\n";
	system("grep RSS /proc/$$/status");
}
print "Exit Error\n" if $DEBUG;
exit 1;

sub xor_op
{
	my ( $a, $b ) = @_;

	return ( ( $a && ! $b ) || ( ! $a && $b ) );
}

#get cluster's members from config file
sub getClusterConfigMembers
{
	my $members_line = -1;
	my $cl_lhost;    # cluster local host
	my $cl_lip;      # cluster local ip
	my $cl_rhost;    # cluster remote host
	my $cl_rip;      # cluster remote ip

	# get MEMBERS line from cluster configuration file
	# Example:
	# MEMBERS:hostname1:ip1:hostname2:ip2
	open FR, "$filecluster";
	foreach ( <FR> )
	{
		if ( $_ =~ /^MEMBERS/ )
		{
			chomp ( $members_line = $_ );
			last;
		}
	}
	close FR;

	#split members line
	( $cl_lhost, $cl_lip, $cl_rhost, $cl_rip ) =
	  ( split ( ":", $members_line ) )[1 .. 4];

	if ( $cl_rhost eq hostname() )
	{
		( $cl_rhost, $cl_rip, $cl_lhost, $cl_lip ) =
		  ( $cl_lhost, $cl_lip, $cl_rhost, $cl_rip );
	}

	return ( $cl_lhost, $cl_lip, $cl_rhost, $cl_rip );
}

#get cluster type and cluster status
sub getClusterConfigTypeStatus
{
	my $line;

	# pick line TYPECLUSTER from cluster configuration line
	# Examples:
	# TYPECLUSTER:hostname1-hostname2:UP
	# TYPECLUSTER:equal:UP
	open FR, "$filecluster";
	foreach ( <FR> )
	{
		if ( $_ =~ /^TYPECLUSTER/ )
		{
			chomp ( $line = $_ );
			last;
		}
	}
	close FR;

	return ( split ( ":", $line ) )[1 .. 2];
}

#get data of cluster's Virtual IP
sub getClusterConfigVipInterface
{
	my $cluster_ip_line;

	# get IPCLUSTER line from cluster configuration file
	# Example:
	# IPCLUSTER:10.0.0.10:eth0:0
	open FR, "$filecluster";
	foreach ( <FR> )
	{
		if ( $_ =~ /^IPCLUSTER/ )
		{
			chomp ( $cluster_ip_line = $_ );
			last;
		}
	}
	close FR;

	# split ip and device info
	my @cl_VIPdata = split ( ":", $cluster_ip_line );

	# ( ip, virtual interface)
	return ( $cl_VIPdata[1], $cl_VIPdata[2] . ":" . $cl_VIPdata[3] );
}
