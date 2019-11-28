#!/usr/bin/perl

use strict;
use warnings;
use Config::Tiny;
use Zevenet::Net::Interface;

# get a list of all network interfaces detected in the system.
my @ifaces = &getInterfaceList();
foreach my $iface ( @ifaces )
{
	# get config file of interface
	my $cfg_file = &getInterfaceConfigFile( $iface );

	# open config file of the interface if exist
	if ( -f $cfg_file )
	{
		my $iface_cfg = Config::Tiny->read( $cfg_file );

		# get the system mac
		my $iface_hash_ref = &getSystemInterface( $iface );

		# if the mac are different, the mac is deleted from the configuration file
		$iface_cfg->{ $iface }->{ mac } = ""
		  if ( $iface_hash_ref->{ mac } ne $iface_cfg->{ $iface }->{ mac } );
		$iface_cfg->write( $cfg_file );
	}
}
