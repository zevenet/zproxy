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

use Zevenet::API40::HTTP;

sub delete_interface_floating    # ( $floating )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $floating = shift;

	include 'Zevenet::Net::Floating';
	require Zevenet::Farm::Config;

	my $desc              = "Remove floating interface";
	my $floatfile         = &getGlobalConfiguration( 'floatfile' );
	my $float_ifaces_conf = &getConfigTiny( $floatfile );

	# validate BOND
	unless ( $float_ifaces_conf->{ _ }->{ $floating } )
	{
		my $msg = "Floating interface not found";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	eval {
		delete $float_ifaces_conf->{ _ }->{ $floating };

		&setConfigTiny( $floatfile, $float_ifaces_conf ) or die;
		&reloadFarmsSourceAddress();
	};

	if ( $@ )
	{
		&zenlog( "Module failed: $@", "error", "net" );
		my $msg = "The floating interface could not be removed";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	include 'Zevenet::Cluster';

	# force sync to make sure the configuration is updated
	if ( &getZClusterRunning() && &getZClusterNodeStatus() eq 'master' )
	{
		# force sync to make sure the configuration is updated
		my $configdir = &getGlobalConfiguration( 'configdir' );
		&zenlog( "Syncing $configdir", "info", "NETWORK" );
		&runSync( $configdir );

		&runZClusterRemoteManager( 'interface', 'float-update' );
	}

	my $message = "The floating interface has been removed.";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $message,
	};

	return &httpResponse( { code => 200, body => $body } );
}

# address or interface
sub modify_interface_floating    # ( $json_obj, $floating )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj  = shift;
	my $interface = shift;

	require Zevenet::Net::Interface;
	require Zevenet::Farm::Config;
	include 'Zevenet::Net::Floating';

	my $desc = "Modify floating interface";

	my $if_ref = &getInterfaceConfig( $interface );

	unless ( $if_ref )
	{
		my $msg = "Floating interface not found";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my @virt = ();
	foreach my $if_virt ( @{ &get_virtual_list_struct() } )
	{
		push @virt, $if_virt->{ ip } if $if_virt->{ parent } eq $interface;
	}

	my $params = {
				   "floating_ip" => {
									  'values'    => \@virt,
									  'non_blank' => 'true',
									  'required'  => 'true',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	$if_ref = undef;

	if ( exists $json_obj->{ floating_ip } )
	{
		# validate ADDRESS format
		require Zevenet::Validate;

		my @interfaces = &getInterfaceTypeList( 'virtual' );
		( $if_ref ) = grep {
			     $json_obj->{ floating_ip } eq $_->{ addr }
			  && $_->{ parent } eq $interface
		} @interfaces;

		# validate ADDRESS in system
		unless ( $if_ref )
		{
			my $msg = "Virtual interface with such address not found";
			return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
		}
	}

	eval {
		my $floatfile         = &getGlobalConfiguration( 'floatfile' );
		my $float_ifaces_conf = &getConfigTiny( $floatfile );

		$float_ifaces_conf->{ _ }->{ $interface } = $if_ref->{ name };

		&setConfigTiny( $floatfile, $float_ifaces_conf ) or die;
		&reloadFarmsSourceAddress();
	};

	if ( $@ )
	{
		&zenlog( "Module failed: $@", "error", "net" );
		my $msg = "Floating interface modification failed";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	include 'Zevenet::Cluster';

	if ( &getZClusterRunning() && &getZClusterNodeStatus() eq 'master' )
	{
		# force sync to make sure the configuration is updated
		my $configdir = &getGlobalConfiguration( 'configdir' );
		&zenlog( "Syncing $configdir", "info", "NETWORK" );
		&runSync( $configdir );

		&runZClusterRemoteManager( 'interface', 'float-update' );
	}

	my $message = "Floating interface modification done";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $message
	};

	return &httpResponse( { code => 200, body => $body } );
}

sub get_interfaces_floating
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	include 'Zevenet::Net::Floating';

	my $desc   = "List floating interfaces";
	my $output = &get_floating_list_struct();

	my $body = {
				 description => $desc,
				 params      => $output,
	};

	return &httpResponse( { code => 200, body => $body } );
}

sub get_floating
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $floating = shift;

	include 'Zevenet::Net::Floating';

	my $desc   = "Show floating interface";
	my $output = &get_floating_struct( $floating );

	my $body = {
				 description => $desc,
				 params      => $output,
	};

	return &httpResponse( { code => 200, body => $body } );
}

1;
