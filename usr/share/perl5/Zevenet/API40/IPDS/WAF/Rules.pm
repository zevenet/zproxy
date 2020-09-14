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
include 'Zevenet::IPDS::WAF::Parser';
include 'Zevenet::API40::IPDS::WAF::Structs';

=begin nd
Object: sets

	Los sets son conjuntos de directivas. Aparte tienen un conjunto de
	directivas globales que se usaran como parametros de configuracion globales
	- lista de directivas globales
	- lista de directivas

example:
	{
		global = {
			SecRequestBodyAccess => 'true',
			SecRequestBodyLimit => '',
			SecResponseBodyAccess => 'true',
			SecResponseBodyLimit => '',
			SecRuleEngine => 'onlyLog',
			SecLog => 'true',
			SecAuditLog => 'false',
		}
		directivas = [
			{},
			{},
			...
		]
	}

=cut

=begin nd
Object: directivas

	Hay varios tipos de "directivas":
	- rules
	- actions
	- markers
	- custom

example:


=cut

=begin nd
Object: rules

	Hay tres formas de crear una regla:
	- copy ( a traves del id de regla )
	- raw
	- helper

example:
	{
		'rule_id'     => numero,
		'description' => "string",
		'tag'         => [ "strings", ... ],
		'severity'    => numero,
		'phase'           => 1|2|3|4|5|request|response|logging,
		'variables'       => [ "strings", ... ],
		'transformations' => [ "strings" ],	# debe match en la lista
		'multi_match' => boolean,
		'operator'    => "string",			# debe match en la lista
		'capture'     => boolean,
		'operating'       => "string",
		'action'    => allow|block|redirect|pass|deny,
		'http_code' => numero,
		'execute' => "string",
		'log'       => boolean|"",
		'audit_log' => boolean|"",
		'log_data'  => "string",
		'set_variable'    => [ "strings" ],
		'skip'       => "string",
		'skip_after' => "string",
	}

=cut

sub get_waf_rule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $set = shift;
	my $id  = shift;

	my $desc = "Get the WAF rule $id of the set $set";

	unless ( &existWAFSet( $set ) )
	{
		my $msg = "Requested set $set does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $rule = &getWAFRule( $set, $id );
	unless ( $rule )
	{
		my $msg = "Requested rule $id has not been found.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	$rule = &getZapiWAFRule( $rule );
	my $body = { description => $desc, params => $rule };

	return &httpResponse( { code => 200, body => $body } );
}

#  POST /ipds/waf/<set>/rules
sub create_waf_rule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $set      = shift;
	my $err;

	include 'Zevenet::IPDS::WAF::Config';
	my $desc = "Create a rule in the set $set";
	my $type;

	# check if the set exists
	if ( !&existWAFSet( $set ) )
	{
		my $msg = "The WAF set $set does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $params = &getWafRuleParameters();
	$params->{ "mark" }      = { 'non_blank'    => 'true' };
	$params->{ "raw" }       = { 'non_blank'    => 'true' };
	$params->{ "copy_from" } = { 'valid_format' => 'waf_rule_id' };

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	if ( exists $json_obj->{ raw } )
	{
		if ( keys %$json_obj > 1 )
		{
			my $msg = "The field 'raw' can not be combined with another one.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		$type = 'custom';
		my @arr = split ( "\n", $json_obj->{ raw } );
		$json_obj->{ raw } = \@arr;
		$err = &setWAFSetRaw( $set, $json_obj->{ raw } );
	}
	elsif ( exists $json_obj->{ mark } )
	{
		if ( keys %$json_obj > 1 )
		{
			my $msg = "The field 'mark' can not be combined with another one.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
		$type = 'mark';
		### create marker
		$err = &createWAFMark( $set, $json_obj->{ mark } );

	}
	elsif ( exists $json_obj->{ copy_from } )
	{
		$type = 'copy';
		if ( keys %$json_obj > 1 )
		{
			my $msg = "The field 'copy_from' can not be combined with another one.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		# check if the source of the copy exists
		elsif ( !&existWAFRuleId( $json_obj->{ copy_from } ) )
		{
			my $msg = "The WAF rule $json_obj->{ copy_from } does not exist";
			return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
		}

		# Copy
		$err = &copyWAFRule( $set, $json_obj->{ copy_from } );
	}
	else
	{
		# rule and action
		$type = 'action';
		if ( exists $json_obj->{ rule_id } )
		{
			my $set_id = &getWAFSetByRuleId( $json_obj->{ rule_id } );
			if ( $set_id )
			{
				my $msg =
				  "The rule $json_obj->{ rule_id } already exists in the set '$set_id'.";
				return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}
		}

		my $rule = &getWAFRulesStruct( $type );
		$err = &translateWafRule( $json_obj, $rule );

		if ( $err )
		{
			return &httpErrorResponse( code => 400, desc => $desc, msg => $err );
		}

		# create a rule
		&updateWAFRule( $rule, $json_obj );
		$err = &createWAFRule( $set, $rule );
	}

	if ( $err )
	{
		return &httpErrorResponse( code => 400, desc => $desc, msg => $err );
	}

	# if has been created properly, the rule id is the last in the config file
	my $rule = &getWAFRuleLast( $set );
	unless ( $rule )
	{
		my $msg = "Error creating the rule";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
	my $msg    = "The rule was created properly.";
	my $output = &getZapiWAFRule( $rule );
	my $body   = { description => $desc, params => $output, message => $msg };

	return &httpResponse( { code => 201, body => $body } );
}

#  PUT /ipds/waf/<set>/rules/<id>
sub modify_waf_rule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $set      = shift;
	my $id       = shift;

	include 'Zevenet::IPDS::WAF::Config';
	my $desc = "Modify the rule $id from the set $set";

	# check if the set exists
	if ( !&existWAFSet( $set ) )
	{
		my $msg = "The WAF set $set does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $rule = &getWAFRule( $set, $id );
	unless ( $rule )
	{
		my $msg = "Requested rule $id has not been found.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $params;
	if ( exists $json_obj->{ raw } )
	{
		$params = { "raw" => { 'required' => 'true', 'non_blank' => 'true' }, };
	}
	elsif ( exists $json_obj->{ mark } )
	{
		$params = { "mark" => { 'required' => 'true', 'non_blank' => 'true' }, };
	}
	else
	{
		$params = &getWafRuleParameters();
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# modify a rule
	my $err;

	if ( exists $json_obj->{ raw } )
	{
		# change format to array
		my @arr = split ( "\n", $json_obj->{ raw } );
		$json_obj->{ raw } = \@arr;
		$err = &setWAFSetRaw( $set, $json_obj->{ raw }, $id );
	}
	elsif ( exists $json_obj->{ mark } )
	{
		$err = &setWAFMark( $set, $id, $json_obj->{ mark } );
	}
	else
	{
		$err = &translateWafRule( $json_obj, $rule );
		if ( $err )
		{
			return &httpErrorResponse( code => 400, desc => $desc, msg => $err );
		}

		if ( exists $json_obj->{ rule_id }
			 and $json_obj->{ rule_id } != $rule->{ rule_id } )
		{
			my $set_id = &getWAFSetByRuleId( $json_obj->{ rule_id } );
			if ( $set_id )
			{
				my $msg =
				  "The rule $json_obj->{ rule_id } already exists in the set '$set_id'.";
				return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}
		}

		&updateWAFRule( $rule, $json_obj );
		$err = &setWAFRule( $set, $id, $rule );
	}

	if ( $err )
	{
		return &httpErrorResponse( code => 400, desc => $desc, msg => $err );
	}

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_waf', 'reload_rule', $set );

	my $rule_updated = &getWAFRule( $set, $id );
	my $outRule      = &getZapiWAFRule( $rule_updated );
	my $body         = { description => $desc, params => $outRule };

	return &httpResponse( { code => 200, body => $body } );
}

#  DELETE /ipds/waf/<set>/rules/<id>
sub delete_waf_rule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $set = shift;
	my $id  = shift;

	include 'Zevenet::IPDS::WAF::Config';
	my $desc = "Delete the rule $id from the set $set";

	# check if the set exists
	if ( !&existWAFSet( $set ) )
	{
		my $msg = "The WAF set $set does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $rule = &getWAFRule( $set, $id );
	unless ( $rule )
	{
		my $msg = "The rule $id is not in the set $set";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( &deleteWAFRule( $set, $id ) )
	{
		my $msg = "There was an error deleting the rule $id";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_waf', 'reload_rule', $set );

	my $msg = "The rule $id has been deleted properly";
	my $body = { description => $desc, message => $msg };

	return &httpResponse( { code => 200, body => $body } );
}

#  POST /ipds/waf/<set>/rules/<id>/actions
sub move_waf_rule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $set      = shift;
	my $id       = shift;
	my $err;

	include 'Zevenet::IPDS::WAF::Config';
	my $desc = "Move a rule in the set $set";

	# check if the set exists
	if ( !&existWAFSet( $set ) )
	{
		my $msg = "The WAF set $set does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# check if the id exists
	my $set_st = &getWAFSet( $set );
	if ( $id >= scalar @{ $set_st->{ rules } } )
	{
		my $msg = "The rule $id does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $params =
	  { "position" =>
		{ 'required' => 'true', 'non_blank' => 'true', 'valid_format' => 'integer' },
	  };

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	$err = &moveWAFRule( $set, $id, $json_obj->{ position } );

	if ( $err )
	{
		my $msg = "Error moving the rule $id";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_waf', 'reload_rule', $set );

	my $msg =
	  "The rule was moved properly to the position $json_obj->{ position }.";
	my $body = { description => $desc, message => $msg };

	return &httpResponse( { code => 200, body => $body } );
}

#  POST /ipds/waf/<set>/rules/<id>/matches
sub create_waf_rule_match
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj   = shift;
	my $set        = shift;
	my $rule_index = shift;
	my $err;

	include 'Zevenet::IPDS::WAF::Config';
	my $desc = "Create a match in the rule $rule_index for the set $set";

	# check if the set exists
	if ( !&existWAFSet( $set ) )
	{
		my $msg = "The WAF set $set does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}
	my $rule_st = &getWAFRule( $set, $rule_index );
	unless ( $rule_st )
	{
		my $msg = "The rule $rule_index does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# get parameter for a match
	my $params = &getWafMatchParameters();

	# Check allowed parameters
	$err = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $err )
	  if ( $err );

	&translateWafMatch( $json_obj );

	$err = &createWAFMatch( $set, $rule_index, $rule_st, $json_obj )
	  ;    # this function returns the struct rule_st updated
	return &httpErrorResponse( code => 400, desc => $desc, msg => $err )
	  if ( defined $err );

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_waf', 'reload_rule', $set );

	my $msg = "The new match was created successfully.";
	$rule_st = &getWAFRule( $set, $rule_index );
	my $rule = &getZapiWAFRule( $rule_st );
	my $out  = $rule->{ matches }->[-1];
	$out->{ raw } = $rule->{ raw };

	my $body = {
				 description => $desc,
				 params      => $out,
				 message     => $msg
	};

	return &httpResponse( { code => 201, body => $body } );
}

#  PUT /ipds/waf/<set>/rules/<id>/matches/index
sub modify_waf_rule_match
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj    = shift;
	my $set         = shift;
	my $rule_index  = shift;
	my $chain_index = shift;
	my $rule_st;

	include 'Zevenet::IPDS::WAF::Config';
	my $desc = "Modify the match $chain_index in rule $rule_index for the set $set";

	# check if the set exists
	if ( !&existWAFSet( $set ) )
	{
		my $msg = "The WAF set $set does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	$rule_st = &getWAFRule( $set, $rule_index );
	unless ( $rule_st )
	{
		my $msg = "Requested rule $rule_index has not been found.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	unless ( &getWAFMatchExists( $rule_st, $chain_index ) )
	{
		my $msg = "The match $chain_index has not been found";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# get parameter for a chain
	my $params = &getWafMatchParameters();

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# modify a rule
	&translateWafMatch( $json_obj );

	$error_msg =
	  &setWAFMatch( $set, $rule_index, $chain_index, $rule_st, $json_obj );
	if ( $error_msg )
	{
		return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg );
	}

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_waf', 'reload_rule', $set );

	my $rule_updated = &getWAFRule( $set, $rule_index );
	my $outRule = &getZapiWAFRule( $rule_updated );

	my $out = $outRule->{ matches }->[$chain_index];
	$out->{ raw } = $outRule->{ raw };

	my $body = { description => $desc, params => $out };

	return &httpResponse( { code => 200, body => $body } );
}

#  DELETE /ipds/waf/<set>/rules/<id>/matches/<index>
sub delete_waf_rule_match
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $set         = shift;
	my $id          = shift;
	my $chain_index = shift;

	include 'Zevenet::IPDS::WAF::Config';
	my $desc = "Delete the match $chain_index from rule $id for the set $set";

	# check if the set exists
	if ( !&existWAFSet( $set ) )
	{
		my $msg = "The WAF set $set does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $rule = &getWAFRule( $set, $id );
	unless ( $rule )
	{
		my $msg = "The rule $id is not in the set $set";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	unless ( &getWAFMatchExists( $rule, $chain_index ) )
	{
		my $msg = "The match $chain_index has not been found";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $msg = &delWAFMatch( $set, $id, $chain_index, $rule );
	if ( $msg )
	{
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_waf', 'reload_rule', $set );

	my $rule_updated = &getWAFRule( $set, $id );
	my $out = &getZapiWAFRule( $rule_updated );

	$msg = "The match $chain_index has been deleted properly";
	my $body =
	  { description => $desc, message => $msg, params => { raw => $out->{ raw } } };

	return &httpResponse( { code => 200, body => $body } );
}

1;

