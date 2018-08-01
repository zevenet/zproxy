#!/usr/bin/perl

use strict;
use warnings;
use Zevenet::Log;

if ( $ARGV[0] =~ /^$/ ){
	exit 1;
}

my $iface=$ARGV[0];
my $gateway;

if ($iface =~ /^$/ )
{
	&zenlog("Network config called without interface arg...");
	exit 1;
}

use Zevenet::Config;
use Zevenet::Net;

&zenlog("Call to Network config through netplugd... for $iface");
use strict;
my $if_ref = &getInterfaceConfig($iface);

#if interface is not configured in UP mode then exit.
if ($if_ref->{ status } ne 'up' ){
	&zenlog("Interface $iface is not configured to be started");
	exit 1;
	}

&upIf($if_ref);
#if nic is used for global gw the apply global routes
if (&getGlobalConfiguration('defaultgwif') eq $if_ref->{ dev }){
	&zenlog("Applying default GW for table main");
	$gateway=&getGlobalConfiguration('defaultgw');
	&applyRoutes('global',$if_ref,$gateway);
	}
#finally apply local routes
&applyRoutes('local',$if_ref);


#Now apply static routes if apply, they are saved in routing.conf
use Zevenet::Config('getGlobalConfiguration');
my $configdir = &getGlobalConfiguration('configdir');
##Apply static rules and routes
use Config::Tiny;
my $config = Config::Tiny->read("$configdir/routing.conf");


my $parameter = "";
foreach my $section (keys %{$config}) {
&zenlog( "[$section]");
	#what about rules? they are not deleted after a link down.
	foreach my $parameter (keys %{$config->{$section}}) {
		if ( $section eq "table_$iface" ){
			&zenlog( "$parameter = $config->{$section}->{$parameter}\n" );
			my $run_route = `ip route $config->{$section}->{$parameter} table $section 2>&1`;
			if ($run_route !~ /^$/){
				&zenlog("Error message: $run_route");
				&zenlog("Route: ip route $config->{$section}->{$parameter} table $section not applied properly");
			}

		}else{
		if ( $config->{$section}->{$parameter} =~ / dev $iface / ){
			&zenlog( "$parameter = $config->{$section}->{$parameter}\n" );
			my $run_route = `ip route $config->{$section}->{$parameter} table $section 2>&1`;
			if ($run_route !~ /^$/){
				&zenlog("Error message: $run_route");
		        	&zenlog("Route: ip route $config->{$section}->{$parameter} table $section not applied properly");
				}


			}

		}
	}
}
