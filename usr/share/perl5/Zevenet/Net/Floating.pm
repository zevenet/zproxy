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

=begin nd
Function: getConfigTiny

	Get a Config::Tiny object from a file name.

Parameters:
	file_path - Path to file.

Returns:
	scalar - reference to Config::Tiny object, or undef on failure.

See Also:

=cut
sub getConfigTiny
{
	my $file_path = shift;

	if ( ! -f $file_path )
	{
		open my $fi, '>', $file_path;
		&zenlog("Could not open file $file_path: $!") if ! $fi;
		close $fi;
	}

	require Config::Tiny;

	# returns object on success or undef on error.
	return Config::Tiny->read( $file_path );
}

=begin nd
Function: setConfigTiny

	Store a Config::Tiny object in a file.

Parameters:
	file_path - Path to file.
	config_ref - Config::Tiny object reference.

Returns:
	boolean - true on success, or undef on failure.

See Also:

=cut
sub setConfigTiny
{
	my $file_path  = shift;
	my $config_ref = shift;

	if ( ! -f $file_path )
	{
		&zenlog("Could not find $file_path: $!");
		return undef;
	}

	if ( ref $config_ref ne 'Config::Tiny' )
	{
		&zenlog("Ilegal configuration argument.");
		return undef;
	}

	require Config::Tiny;

	# returns true on success or undef on error,
	return $config_ref->write( $file_path );
}

=begin nd
Function: getFloatInterfaceForAddress

	Get floating interface or output interface

Parameters:
	remote_ip_address - .

Returns:
	scalar - Name of output .

See Also:

=cut
# get floating interface or output interface
sub getFloatInterfaceForAddress
{
	my $remote_ip_address = shift;

	require NetAddr::IP;
	require Zevenet::Net::Interface;

	my $subnet_interface;
	my @interface_list = @{ &getConfigInterfaceList() };
	my $remote_ip      = NetAddr::IP->new( $remote_ip_address );

	# find interface in range
	for my $iface ( @interface_list )
	{
		next if $iface->{ vini } ne '';

		my $network = NetAddr::IP->new( $iface->{ addr }, $iface->{ mask } );

		if ( $remote_ip->within( $network ) )
		{
			$subnet_interface = $iface;
		}
	}

	if ( ! $subnet_interface )
	{
		return;
	}

	my $output_interface;

	if ( $subnet_interface->{ float } )
	{
		# find floating interface
		for my $iface ( @interface_list )
		{
			next if $iface->{ vini } eq '';

			if ( $iface->{ name } eq $subnet_interface->{ float } )
			{
				$output_interface = $iface;
			}
		}
	}
	else
	{
		$output_interface = $subnet_interface;
	}

	return $output_interface;
}

1;
