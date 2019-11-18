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

#GET /rbac/ldap
sub get_rbac_ldap
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $desc = "List the LDAP settings";
	my $ldap = &getLDAPZapiOut();

	return &httpResponse(
				   { code => 200, body => { description => $desc, params => $ldap } } );
}

#  POST /rbac/ldap
sub set_rbac_ldap
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	my $desc = "Set the LDAP settings";

	my $params = {
		"host" => {
					'doc' => 'it is the LDAP URL or the server IP',
		},
		"port" => {
			'valid_format' => 'port',
			'doc' =>
			  'it is the port where the LDAP server is listening. This filed is skipt if the host is a URL or overwrite the port',
		},
		"bind_dn" => {
			'doc' =>
			  'it is the LDAP admin user used to modify manage. It is not necessary if the LDAP can be queried anonimously',
		},
		"bind_password" => {
							 'doc' => 'it is the password for the admin user',
		},
		"base_dn" => {
					   'doc' => 'it is used to get an user based on some attribute',
		},
		"filter" => {
					  'doc' => 'it is the base used to look for the user in the LDAP',
		},
		"version" => {
					   'valid_format' => [1, 2, 3],
					   'doc'          => 'it is the LDAP version used by the server',
		},
		"scope" => {
			'values' => ["base", "sub", "one"],
			'doc' => 'the search scope, can be base, one or sub, defaults to sub',
		},
		"timeout" => {
					   'valid_format' => 'natural_num',
					   'doc'          => 'timeout of the LDAP query to the server',
		},
	};

	# Check if it exists
	if ( &getRBACUserExists( $json_obj->{ 'name' } ) )
	{
		my $msg = "$json_obj->{ 'name' } already exists.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	$json_obj = &getLDAPZapiIn( $json_obj );

	# check result and return success or failure
	if ( !&setLDAP( $json_obj ) )
	{
		my $out = &getLDAPZapiOut();
		my $msg = "LDAP configuration was set properly";
		my $body = {
					 description => $desc,
					 params      => $out,
					 message     => $msg,
		};
		return &httpResponse( { code => 201, body => $body } );
	}

	my $msg = "There was an error configuring the LDAP service";
	return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
}

# POST /rbac/ldap/actions
sub set_rbac_ldap_actions
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	my $desc = "Set the LDAP settings";

	my $params = {
				   "action" => {
								 'values' => ["test"],
								 'doc'    => 'it is the LDAP version used by the server',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	if ( &testLDAP() )
	{
		my $msg = "The connection with the server was successful";
		my $body = {
					 description => $desc,
					 message     => $msg,
		};
		return &httpResponse( { code => 200, body => $body } );
	}

	my $msg = "It could not connect with the server";
	return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
}

# translate params:
sub getLDAPZapiOut
{
	my $ldap = &getLDAP();
	my $out  = $ldap;

	$out->{ bind_dn } = $ldap->{ binddn };
	delete $ldap->{ binddn };

	$out->{ bind_password } = $ldap->{ bindpw };
	delete $ldap->{ bindpw };

	$out->{ base_dn } = $ldap->{ basedn };
	delete $ldap->{ basedn };

	return $out;
}

# translate params:
sub getLDAPZapiIn
{
	my $json_obj = shift;
	my $out      = $json_obj;

	if ( exists $out->{ bind_dn } )
	{
		$out->{ binddn } = $out->{ bind_dn };
		delete $out->{ bind_dn };
	}

	if ( exists $out->{ bind_password } )
	{
		$out->{ bindpw } = $out->{ bind_password };
		delete $out->{ bind_password };
	}

	if ( exists $out->{ base_dn } )
	{
		$out->{ basedn } = $out->{ base_dn };
		delete $out->{ base_dn };
	}

	return $out;
}

1;
