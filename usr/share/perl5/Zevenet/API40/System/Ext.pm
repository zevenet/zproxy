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

sub set_factory_reset
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $json_obj = shift;
	my $desc     = "Apply a factory reset";

	my $params = {
				   "interface" => {
									'non_blank' => 'true',
									'required'  => 'true',
				   },
				   "remove_backups" => {
										 'values'    => ["true", "false"],
										 'non_blank' => 'true',
				   },
				   "force" => {
								'values'    => ["true", "false"],
								'non_blank' => 'true',
				   },
	};

	require Zevenet::Net::Interface;

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	## The interface must be of NIC type and it has to be configured
	my $if_ref = &getInterfaceConfig( $json_obj->{ interface } );
	if ( $if_ref->{ type } ne 'nic' )
	{
		my $msg = "The interface has to be of type NIC.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
	elsif ( !$if_ref->{ addr } )
	{
		my $msg = "The interface has to be configured.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	unless ( exists $json_obj->{ force } and $json_obj->{ force } eq 'true' )
	{
		my $msg =
		  "While the execution of the factory reset process, the system will be restarted. "
		  . "When the process will finish, the load balancer will be accesible by the ip $if_ref->{addr}. "
		  . "If you are agree, execute again sending the parameter 'force'";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $remove_backups =
	  ( $json_obj->{ remove_backups } eq 'true' ) ? 'remove-backups' : '';
	require Zevenet::System;
	if (
		 &applyFactoryReset( $json_obj->{ interface }, $json_obj->{ remove_backups } ) )
	{
		my $msg = "Some error occurred applying the factory reset.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# The process will die before than here

	my $msg =
	  "The factroy reset was applied properly. The session will be lost. Please, try again in a while";
	my $body = { description => $desc, message => $msg };
	&httpResponse( { code => 200, body => $body } );
}

# GET /system/packages
sub get_packages_info
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	include 'Zevenet::Apt';

	my $desc   = "Zevenet packages list info";
	my $params = {};

	my $output = &getAPTUpdatesList();

	return &httpResponse(
				 { code => 200, body => { description => $desc, params => $output } } );
}

# POST /system/packages/offline
sub upload_iso_offline
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	include 'Zevenet::Apt';

	my $upload_filehandle = shift;

	my $desc = "Upload a offline iso";

	if ( !$upload_filehandle )
	{
		my $msg = "It's necessary to add a data binary file.";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
	my $error = &uploadAPTIsoOffline( $upload_filehandle );
	if ( $error == 1 )
	{
		my $msg = "Error uploading the file.";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
	elsif ( $error == 2 )
	{
		my $msg = "The ISO is not valid.";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $msg = "The ISO was uploaded properly.";
	my $body = { description => $desc, message => $msg };

	&httpResponse( { code => 200, body => $body } );
}

1;
