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
use feature 'state';

require Zevenet::Core;
require Zevenet::Net::Core;
require Zevenet::Net::Route;
require Zevenet::Net::Interface;

sub getDHCPServiceFile
{
	my $name = shift;
	return "/etc/network/interfaces.d/if_${name}_conf";
}

sub enableDHCP
{
	my $if_ref = shift;
	my $err    = 1;

	# logic for enable the service
	my $if_file = &getDHCPServiceFile( $if_ref->{ name } );
	open ( my $fh, '>', $if_file );
	if ( !$fh )
	{
		&zenlog( "The file $if_file could not be openned", "error", "net" );
		return 1;
	}
	print $fh "
auto $if_ref->{name}
allow-hotplug $if_ref->{name}
iface $if_ref->{name} inet dhcp";
	close $fh;

	# save
	$if_ref->{ 'dhcp' } = 'true';
	$err = 0 if ( &setInterfaceConfig( $if_ref ) );

	# load the interface to reload the ip, gw and netmask
	$err = &restartDHCPService();

	return $err;
}

sub disableDHCP
{
	my $if_ref = shift;
	my $err    = 0;

	# logic for enable the service
	my $if_file = &getDHCPServiceFile( $if_ref->{ name } );
	if ( -f $if_file )
	{
		unlink $if_file;
	}

	$if_ref->{ 'dhcp' } = 'false';
	$err = 0 if ( &setInterfaceConfig( $if_ref ) );

	# try to preserve the ip, gw and netmask
	$err = &restartDHCPService();

	return $err;
}

sub restartDHCPService
{
	my $srv = &getGlobalConfiguration( 'networking_service' );
	return &logAndRun( "$srv restart" );
}

1;
