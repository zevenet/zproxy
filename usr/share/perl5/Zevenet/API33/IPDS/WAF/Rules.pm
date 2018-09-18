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

include 'Zevenet::IPDS::WAF::Core';
include 'Zevenet::API33::IPDS::WAF::Structs';

#  POST /ipds/waf/<set>/rules
sub create_waf_rule
{
	my $json_obj = shift;
	my $set      = shift;
	my $err;

	include 'Zevenet::IPDS::WAF::Config';
	my $desc = "Create a rule in the set $set";
	my $params;

	# check if the set exists
	if ( ! &existWAFSet( $set ) )
	{
		my $msg = "The WAF set $set does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( ! exists $json_obj->{ edition_mode }
		or $json_obj->{ edition_mode } !~ /^(?:copy|raw|helper)$/ )
	{
		my $msg = "The parameter edition_mode is missing";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
	elsif ( $json_obj->{ edition_mode } eq 'copy' )
	{
		$params = {
			"copy_from" => { 'required' => 'true', 'valid_format' => 'waf_rule_id' },
			"edition_mode" => { 'required' => 'true' },
		};
	}
	elsif ( $json_obj->{ edition_mode } eq 'raw' )
	{
		$params = {
			"rule_string" => { 'required' => 'true' },
			"edition_mode" => { 'required' => 'true' },
		};
	}
	else
	{
		$params = {
			"rule_struct" => { 'required' => 'true' },
			"edition_mode" => { 'required' => 'true' },
			# ?????? definir los parametros de entrada
		};
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	if ( $json_obj->{ edition_mode } eq 'copy' )
	{
		# check if the source of the copy exists
		unless ( &existWAFRuleId( $json_obj->{ copy_from } ) )
		{
			my $msg = "The WAF rule $json_obj->{ copy_from } does not exist";
			return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
		}

		# Copy
		$err = &copyWAFRule( $set, $json_obj->{ copy_from } );
	}
	elsif ( $json_obj->{ edition_mode } eq 'raw' )
	{
		my @rule_aux = split ( '\n', $json_obj->{rule_string} );
		$err = &createWAFRule( $set, \@rule_aux );
	}
	else
	{
		# create a rule
		$err = &createWAFRule( $set, $json_obj->{ rule_struct });
	}

	if ( $err )
	{
		return &httpErrorResponse( code => 400, desc => $desc, msg => $err );
	}

	# if has been created properly, the rule id is the last in the config file
	my $rule = &getWAFRuleLast( $set );

	include 'Zevenet::Cluster';
	#~ &runZClusterRemoteManager( 'rbac_user', 'update', $user );

	my $msg    = "Settings were changed successful.";
	my $output = &getZapiWAFRule( $rule );
	my $body   = { description => $desc, params => $output, message => $msg };

	&httpResponse( { code => 200, body => $body } );
}

#  PUT /ipds/waf/<set>/rules/<id>
sub modify_waf_rule
{

}

#  DELETE /ipds/waf/<set>/rules/<id>
sub delete_waf_rule
{
	my $set      = shift;
	my $id      = shift;
	my $err;

	include 'Zevenet::IPDS::WAF::Config';
	my $desc = "Delete the rule $id from the set $set";

	# check if the set exists
	if ( ! &existWAFSet( $set ) )
	{
		my $msg = "The WAF set $set does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}
	elsif ( &getWAFSetByRuleId( $id ) ne $set )
	{
		my $msg = "The rule $id is not in the set $set";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( &deleteWAFRule( $set, $id ) )
	{
		my $msg = "Deleting the rule $id";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	include 'Zevenet::Cluster';
	#~ &runZClusterRemoteManager( 'rbac_user', 'update', $user );

	my $msg    = "The rule $id has been deleted properly";
	my $body   = { description => $desc, message => $msg };

	&httpResponse( { code => 200, body => $body } );
}

1;
