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
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my $file_path = shift;

	if ( ! -f $file_path )
	{
		open my $fi, '>', $file_path;
		&zenlog("Could not open file $file_path: $!", "error", "SYSTEM") if ! $fi;
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
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my $file_path  = shift;
	my $config_ref = shift;

	if ( ! -f $file_path )
	{
		&zenlog("Could not find $file_path.", "error", "SYSTEM");
		return;
	}

	if ( ref $config_ref ne 'Config::Tiny' )
	{
		&zenlog("Ilegal configuration argument.", "error", "SYSTEM");
		return;
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
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
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

sub getFloatingMasqParams
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my ( $farm, $server ) = @_;

	my $out_if = &getFloatInterfaceForAddress( $$server{ vip } );

	if ( ! $out_if )
	{
		$out_if = &getFloatInterfaceForAddress( $$farm{ vip } );
	}

	return "--jump SNAT --to-source $out_if->{ addr } ";
}

sub getFloatingSnatParams
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my ( $server ) = @_;

	my $float_if = &getFloatInterfaceForAddress( $$server{ vip } );

	return "--jump SNAT --to-source $float_if->{ addr }";
}

sub get_floating_struct
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my ( $floating ) = @_;

	require Zevenet::Alias;
	require Zevenet::Net::Interface;

	# Interfaces
	my $output;
	my @ifaces            = @{ &getSystemInterfaceList() };
	my $floatfile         = &getGlobalConfiguration( 'floatfile' );
	my $float_ifaces_conf = &getConfigTiny( $floatfile );

	my $alias = &getAlias( 'interface' );

	for my $iface ( @ifaces )
	{
		next unless $iface->{ ip_v } == 4 || $iface->{ ip_v } == 6;
		next if $iface->{ type } eq 'virtual';
		next unless $iface->{ name } eq $floating;

		my $floating_ip        = undef;
		my $floating_interface = undef;

		unless ( $iface->{ addr } )
		{
			my $msg = "This interface has no address configured";
			return &httpErrorResponse( code => 400, msg => $msg );
		}

		$floating_ip = undef;

		if ( $float_ifaces_conf->{ _ }->{ $iface->{ name } } )
		{
			$floating_interface = $float_ifaces_conf->{ _ }->{ $iface->{ name } };
			my $if_ref = &getInterfaceConfig( $floating_interface );
			$floating_ip = $if_ref->{ addr };
		}

		$output = {
					alias             => $alias->{ $iface->{ name } },
					interface         => $iface->{ name },
					floating_ip       => $floating_ip,
					floating_alias    => $alias->{ $floating_interface },
					interface_virtual => $floating_interface,
		};

		last;
	}

	return $output;
}

sub get_floating_list_struct
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	require Zevenet::Alias;
	require Zevenet::Net::Interface;

	# Interfaces
	my @output;
	my @ifaces            = @{ &getSystemInterfaceList() };
	my $floatfile         = &getGlobalConfiguration( 'floatfile' );
	my $float_ifaces_conf = &getConfigTiny( $floatfile );

	my $alias = &getAlias( 'interface' );

	for my $iface ( @ifaces )
	{
		next unless $iface->{ ip_v } == 4 || $iface->{ ip_v } == 6;
		next if $iface->{ type } eq 'virtual';
		next unless $iface->{ addr };

		my $floating_ip        = undef;
		my $floating_interface = undef;

		if ( $float_ifaces_conf->{ _ }->{ $iface->{ name } } )
		{
			$floating_interface = $float_ifaces_conf->{ _ }->{ $iface->{ name } };
			my $if_ref = &getInterfaceConfig( $floating_interface );
			$floating_ip = $if_ref->{ addr };
		}

		push @output,
		  {
			alias             => $alias->{ $iface->{ name } },
			interface         => $iface->{ name },
			floating_ip       => $floating_ip,
			floating_alias    => $alias->{ $floating_interface },
			interface_virtual => $floating_interface,
		  };
	}

	return \@output;
}

1;
