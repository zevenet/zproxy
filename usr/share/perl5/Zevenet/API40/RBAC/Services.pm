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

include 'Zevenet::RBAC::LDAP';

#GET /rbac/services
sub get_rbac_services
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $desc   = "List the status of the authentication services";
	my $params = &getZapiRbacServices();

	return &httpResponse(
				 { code => 200, body => { description => $desc, params => $params } } );
}

#  POST /rbac/services
sub set_rbac_services
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	my $desc = "Modify the configuration to login using the system users";

	my $params = {
		"ldap" => {
			  'doc' => 'it enables or disables the user authentication using a LDAP server',
			  'values' => ['true', 'false'],
		},
		"local" => {
					 'doc'    => 'it enables or disables the log in using the system users',
					 'values' => ['true', 'false'],
		},
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	my @services = ( 'local', 'ldap' );
	foreach my $service ( @services )
	{
		if ( exists $json_obj->{ $service } )
		{
			if ( &setRBACServiceEnabled( $service, $json_obj->{ $service } ) )
			{
				my $msg = "There was an error configuring the RBAC $service service";
				return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}
		}
	}
	my $params = &getZapiRbacServices();
	return &httpResponse(
				 { code => 200, body => { description => $desc, params => $params } } );
}

sub getZapiRbacServices
{
	my @services = ( 'local', 'ldap' );
	my %out;
	foreach my $service ( @services )
	{
		$out{ $service } = &getRBACServiceEnabled( $service );
	}
	return \%out;
}

1;
