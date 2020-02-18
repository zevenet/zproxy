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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $file_path = shift;

	if ( !-f $file_path )
	{
		open my $fi, '>', $file_path;
		&zenlog( "Could not open file $file_path: $!", "error", "SYSTEM" ) if !$fi;
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $file_path  = shift;
	my $config_ref = shift;

	if ( !-f $file_path )
	{
		&zenlog( "Could not find $file_path.", "error", "SYSTEM" );
		return;
	}

	if ( ref $config_ref ne 'Config::Tiny' )
	{
		&zenlog( "Ilegal configuration argument.", "error", "SYSTEM" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $remote_ip_address = shift;

	return '' if !$remote_ip_address;

	require NetAddr::IP;
	require Zevenet::Net::Interface;

	my $subnet_interface;
	my @interface_list = @{ &getConfigInterfaceList() };

	# getting the input ip range
	foreach my $ifa ( @interface_list )
	{
		if ( $ifa->{ addr } eq $remote_ip_address )
		{
			# the ip is a local interface with routing
			if ( $ifa->{ vini } eq '' )
			{
				$subnet_interface = $ifa;
			}

			# the ip is a local virtual interface
			else
			{
				my $parent = &getParentInterfaceName( $ifa->{ name } );
				$subnet_interface = &getInterfaceConfig( $parent );
			}

			last;

		}
	}

# The interface has not been found in any local interface. Looking for if it is reacheable for some interface
	if ( !$subnet_interface )
	{
		my $remote_ip = NetAddr::IP->new( $remote_ip_address );
		for my $iface ( @interface_list )
		{
			next if $iface->{ vini } ne '';
			next if $iface->{ status } ne 'up';

			my $network = NetAddr::IP->new( $iface->{ addr }, $iface->{ mask } );

			if ( $remote_ip->within( $network ) )
			{
				$subnet_interface = $iface;
			}
		}

		return if ( !$subnet_interface );
	}

	# getting the output source address
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
				last;
			}
		}
	}
	else
	{
		$output_interface = $subnet_interface;
	}

	if ( $output_interface->{ status } ne "up" )
	{
		return;
	}

	return $output_interface;
}

=begin nd
Function: setFloatingSourceAddr

	It sets the masquerade IP of an l4xnat farm. If it receives a backend struct, it
	applies the IP to masquerade the connection when it is going to this backend,
	else it configures a default IP to masquerade the connections that are going to
	backends that haven't got theirs masquerade IP.

Parameters:
	farm - Struct with the farm configuration
	server - Struct with the backend configuration. This value is optional.

Returns:
	Integer - 0 on success or another value on failure

See Also:

=cut

sub setFloatingSourceAddr
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $farm      = shift;
	my $server    = shift;                                    # optional
	my $configdir = &getGlobalConfiguration( 'configdir' );
	my $out_if    = 0;
	my $srcaddr   = qq();

	require Zevenet::Nft;
	require Zevenet::Net::Validate;
	require Zevenet::Net::Interface;
	require Zevenet::Farm::Core;
	require Zevenet::Farm::L4xNAT::Config;    # Currently, only for L4
	require Zevenet::Farm::L4xNAT::Action;

	my $farm_if_name = &getInterfaceByIp( $farm->{ vip } );
	my $farm_if      = &getInterfaceConfig( $farm_if_name );

	my $configdir     = &getGlobalConfiguration( 'configdir' );
	my $farm_filename = &getFarmFile( $farm->{ name } );
	my $farm_file     = "$configdir/$farm_filename";

	# Backend source address
	if ( defined $server && $server->{ ip } )
	{
		my $net =
		  &getNetValidate( $farm->{ vip }, $farm_if->{ mask }, $server->{ ip } );

		# delete if the backend is not accesible now for the floating ip
		my $srcaddr = "";
		if ( !$net )
		{
			$out_if = &getFloatInterfaceForAddress( $server->{ ip } );
			$srcaddr = ( $out_if ) ? $out_if->{ addr } : "";
		}

		return 0 if ( !exists $server->{ sourceip } and $srcaddr eq "" );
		return 0
		  if ( exists $server->{ sourceip } and $server->{ sourceip } eq $srcaddr );
		return 0 if ( $farm->{ sourceip } eq $srcaddr );

		my $err = &sendL4NlbCmd(
			{
			   method => "PUT",
			   farm   => $farm->{ name },
			   file   => "$farm_file",
			   body =>
				 qq({"farms" : [ { "name" : "$farm->{ name }", "backends" : [ { "name" : "bck$server->{ id }", "source-addr" : "$srcaddr" } ] } ] })
			}
		);
		return $err;
	}

	# Farm source address
	if ( !$out_if && $farm->{ vip } )
	{
		$out_if = &getFloatInterfaceForAddress( $farm->{ vip } );
	}

	if ( !$out_if )
	{
		return 0;
	}

	$srcaddr = $out_if->{ addr };
	return 0 if ( $farm->{ sourceip } eq $srcaddr );

	return
	  &sendL4NlbCmd(
		{
		   farm   => $farm->{ name },
		   method => "PUT",
		   file   => "$farm_file",
		   body =>
			 qq({"farms" : [ { "name" : "$farm->{ name }", "source-addr" : "$srcaddr" } ] })
		}
	  );
}

sub get_floating_struct
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $floating ) = @_;

	require Zevenet::Net::Interface;

	# Interfaces
	my $output;
	my @ifaces            = @{ &getSystemInterfaceList() };
	my $floatfile         = &getGlobalConfiguration( 'floatfile' );
	my $float_ifaces_conf = &getConfigTiny( $floatfile );

	include 'Zevenet::Alias';
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
					floating_alias    => $alias->{ $floating_interface },
					interface         => $iface->{ name },
					floating_ip       => $floating_ip,
					interface_virtual => $floating_interface,
		};

		last;
	}

	return $output;
}

sub get_floating_list_struct
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Net::Interface;

	# Interfaces
	my @output;
	my @ifaces            = @{ &getSystemInterfaceList() };
	my $floatfile         = &getGlobalConfiguration( 'floatfile' );
	my $float_ifaces_conf = &getConfigTiny( $floatfile );

	include 'Zevenet::Alias';
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
			floating_alias    => $alias->{ $floating_interface },
			interface         => $iface->{ name },
			floating_ip       => $floating_ip,
			interface_virtual => $floating_interface,
		  };

	}

	return \@output;
}

1;
