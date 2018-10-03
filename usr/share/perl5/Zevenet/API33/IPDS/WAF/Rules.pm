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
include 'Zevenet::API33::IPDS::WAF::Structs';

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
		'value'       => "string",
		'action'    => allow|block|redirect|pass|deny,
		'http_code' => numero,
		'execute' => "string",
		'log'       => boolean|"",
		'audit_log' => boolean|"",
		'log_data'  => "string",
		'set_var'    => [ "strings" ],
		'skip'       => "string",
		'skip_after' => "string",
	}

=cut

sub get_waf_rule
{
	my $set = shift;
	my $id  = shift;
	my $err;

	my $desc = "Get the WAF set $set";

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
	my $json_obj = shift;
	my $set      = shift;
	my $err;

	include 'Zevenet::IPDS::WAF::Config';
	my $desc = "Create a rule in the set $set";
	my $params;

	# check if the set exists
	if ( !&existWAFSet( $set ) )
	{
		my $msg = "The WAF set $set does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( !exists $json_obj->{ type }
		 or $json_obj->{ type } !~ /^(?:action|rule|custom|copy_rule|marker)$/ )
	{
		my $msg = "The parameter 'type' is missing";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
	elsif ( $json_obj->{ type } eq 'copy_rule' )
	{
		$params = {
				   "copy_from" => { 'required' => 'true', 'valid_format' => 'waf_rule_id' },
				   "type"      => { 'required' => 'true' },
		};
	}
	elsif ( $json_obj->{ type } eq 'custom' )
	{
		$params = {
					"raw"  => { 'required' => 'true', 'non_blank' => 'true' },
					"type" => { 'required' => 'true' },
		};
	}
	elsif ( $json_obj->{ type } eq 'marker' )
	{
		$params = {
					"mark" => { 'required' => 'true', 'non_blank' => 'true' },
					"type" => { 'required' => 'true' },
		};
	}

	# rule or action
	else
	{
		$params = &getWafRuleModel( $json_obj->{ type } );

# to create a new rule it is necessary to send the fields: value, variables or operators
		$params->{ variables }->{ required } = 'true';
		$params->{ operator }->{ required }  = 'true';
		$params->{ value }->{ required }     = 'true';
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	if ( $json_obj->{ type } eq 'copy_rule' )
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
	elsif ( $json_obj->{ type } eq 'custom' )
	{
		my @rule_aux = split ( '\n', $json_obj->{ raw } );
		$err = &setWAFSetRaw( $set, \@rule_aux );
	}
	elsif ( $json_obj->{ type } eq 'marker' )
	{
		### create marker
		$err = &createWAFMark( $set, $json_obj->{ mark } );
	}

	# rule and action
	else
	{
		my $rule = &getWAFRulesStruct( $json_obj->{ type } );
		$err = &translateWafInputs( $json_obj, $rule );

		if ( $err )
		{
			return &httpErrorResponse( code => 400, desc => $desc, msg => $err );
		}

		# create a rule
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

	&httpResponse( { code => 201, body => $body } );
}

#  PUT /ipds/waf/<set>/rules/<id>
sub modify_waf_rule
{
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
	elsif ( $rule->{ type } eq 'marker' )
	{
		$params = { "mark" => { 'required' => 'true', 'non_blank' => 'true' }, };
	}
	else
	{
		$params = &getWafRuleModel( $rule->{ type } );
		delete $params->{ type };
		my $err = &translateWafInputs( $json_obj, $rule );

		if ( $err )
		{
			return &httpErrorResponse( code => 400, desc => $desc, msg => $err );
		}
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# modify a rule
	my $err;

	if ( exists $json_obj->{ raw } )
	{
		$err = &setWAFSetRaw( $set, $json_obj->{ raw }, $id );
	}
	elsif ( exists $json_obj->{ mark } )
	{
		$err = &setWAFMark( $set, $id, $json_obj->{ mark } );
	}
	else
	{
		$err = &setWAFRule( $set, $id, $rule );
	}

	if ( $err )
	{
		my $msg = "Modifying the rule $id";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $err );
	}

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_waf', 'reload_rule', $set );

	my $msg          = "Settings were changed successful.";
	my $rule_updated = &getWAFRule( $set, $id );
	my $outRule      = &getZapiWAFRule( $rule_updated );
	my $body         = { description => $desc, params => $outRule };

	return &httpResponse( { code => 200, body => $body } );
}

#  DELETE /ipds/waf/<set>/rules/<id>
sub delete_waf_rule
{
	my $set = shift;
	my $id  = shift;
	my $err;

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
		my $msg = "Deleting the rule $id";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_waf', 'reload_rule', $set );

	my $msg = "The rule $id has been deleted properly";
	my $body = { description => $desc, message => $msg };

	&httpResponse( { code => 200, body => $body } );
}

sub move_waf_rule
{
	my $json_obj = shift;
	my $set      = shift;
	my $id       = shift;
	my $err;

	include 'Zevenet::IPDS::WAF::Config';
	my $desc = "Move a rule in the set $set";
	my $params;

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
	my $error_msg = &checkZAPIParams( $json_obj, $params );
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

	&httpResponse( { code => 200, body => $body } );
}

sub getWafRuleModel
{
	my $type = shift;
	my $out;

	$out = {
			 'type'            => { 'regexp'       => '(?:rule|action)' },
			 'rule_id'         => { 'valid_format' => 'waf_rule_id' },
			 'description'     => {},
			 'tag'             => {},
			 'severity'        => { 'valid_format' => 'waf_severity' },
			 'phase'           => { 'valid_format' => 'waf_phase' },
			 'transformations' => {},
			 'multi_match'     => { 'valid_format' => 'boolean' },
			 'capture'         => { 'valid_format' => 'boolean' },
			 'action'          => { 'valid_format' => 'waf_action' },
			 'http_code'       => { 'valid_format' => 'http_code' },
			 'execute'         => {},
			 'log'             => { 'valid_format' => 'waf_log' },
			 'auditory'        => { 'valid_format' => 'waf_audit_log' },
			 'log_data'        => {},
			 'set_var'         => {},
			 'skip'            => { 'valid_format' => 'waf_skip' },
			 'skip_after'      => { 'valid_format' => 'waf_skip_after' },
	};

	if ( $type eq 'rule' )
	{
		$out->{ variables } = { 'non_blank' => 'true' };
		$out->{ operator }  = { 'non_blank' => 'true' };
		$out->{ value }     = { 'non_blank' => 'true' };
	}

	return $out;
}

sub translateWafInputs
{
	my $json_obj = shift;
	my $rule     = shift;

	if ( exists $json_obj->{ log } )
	{
		$rule->{ log }    = '';
		$rule->{ no_log } = '';

		if    ( $json_obj->{ log } eq 'true' )  { $rule->{ log }    = 'true'; }
		elsif ( $json_obj->{ log } eq 'false' ) { $rule->{ no_log } = 'true'; }
	}
	if ( exists $json_obj->{ auditory } )
	{
		$rule->{ audit_log }    = '';
		$rule->{ no_audit_log } = '';

		if ( $json_obj->{ auditory } eq 'true' ) { $rule->{ audit_log } = 'true'; }
		elsif ( $json_obj->{ auditory } eq 'false' )
		{
			$rule->{ no_audit_log } = 'true';
		}
	}

	if ( exists $json_obj->{ transformations } )
	{
		my @transf = &getWafTransformations();
		foreach my $tr ( @{ $json_obj->{ transformations } } )
		{
			if ( !grep ( /^$tr$/, @transf ) )
			{
				return "The transformation $tr is not recognized.";
			}
		}
		$rule->{ transformations } = $json_obj->{ transformations };
	}

	if ( exists $json_obj->{ operator } )
	{
		my $oper = &getWafOperators();
		if ( !exists $oper->{ $json_obj->{ operator } } )
		{
			return "The operator $json_obj->{ operator } is not recognized.";
		}

		$rule->{ operator } = $oper->{ $json_obj->{ operator } };
	}

	$rule->{ rule_id } = $json_obj->{ rule_id }
	  if ( exists $json_obj->{ rule_id } );
	$rule->{ description } = $json_obj->{ description }
	  if ( exists $json_obj->{ description } );
	$rule->{ tag } = $json_obj->{ tag } if ( exists $json_obj->{ tag } );
	$rule->{ severity } = $json_obj->{ severity }
	  if ( exists $json_obj->{ severity } );
	$rule->{ phase } = $json_obj->{ phase } if ( exists $json_obj->{ phase } );
	$rule->{ value } = $json_obj->{ value }
	  if ( exists $json_obj->{ value } );
	$rule->{ variables } = $json_obj->{ variables }
	  if ( exists $json_obj->{ variables } );
	$rule->{ multi_match } = $json_obj->{ multi_match }
	  if ( exists $json_obj->{ multi_match } );
	$rule->{ capture } = $json_obj->{ capture }
	  if ( exists $json_obj->{ capture } );
	$rule->{ action } = $json_obj->{ action } if ( exists $json_obj->{ action } );
	$rule->{ http_code } = $json_obj->{ http_code }
	  if ( exists $json_obj->{ http_code } );
	$rule->{ execute } = $json_obj->{ execute }
	  if ( exists $json_obj->{ execute } );
	$rule->{ log_data } = $json_obj->{ log_data }
	  if ( exists $json_obj->{ log_data } );
	$rule->{ set_var } = $json_obj->{ set_var }
	  if ( exists $json_obj->{ set_var } );
	$rule->{ skip } = $json_obj->{ skip } if ( exists $json_obj->{ skip } );
	$rule->{ skip_after } = $json_obj->{ skip_after }
	  if ( exists $json_obj->{ skip_after } );

	return undef;
}

#  POST /ipds/waf/<set>/rules/<id>/chain
sub create_waf_rule_chain
{
	my $json_obj   = shift;
	my $set        = shift;
	my $rule_index = shift;
	my $err;

	include 'Zevenet::IPDS::WAF::Config';
	my $desc = "Create a chain in the rule $rule_index for the set $set";
	my $params;
	my $rule_chain_st;

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

	if ( !exists $json_obj->{ type }
		 or $json_obj->{ type } !~ /^(?:rule|custom|copy_rule)$/ )
	{
		my $msg = "The parameter 'type' is missing";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
	elsif ( $json_obj->{ type } eq 'copy_rule' )
	{
		$params = {
				   "copy_from" => { 'required' => 'true', 'valid_format' => 'waf_rule_id' },
				   "type"      => { 'required' => 'true' },
		};
	}
	elsif ( $json_obj->{ type } eq 'custom' )
	{
		$params = {
					"raw"  => { 'required' => 'true', 'non_blank' => 'true' },
					"type" => { 'required' => 'true' },
		};
	}

	# rule or action
	else
	{
		$params = &getWafRuleModel( 'rule' );

		#the phase must be same than the father rule
		delete $params->{ phase };
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	if ( $json_obj->{ type } eq 'copy_rule' )
	{
		# check if the source of the copy exists
		unless ( &existWAFRuleId( $json_obj->{ copy_from } ) )
		{
			my $msg = "The WAF rule $json_obj->{ copy_from } does not exist";
			return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
		}

		# Copy
		$rule_chain_st = &getWAFRuleById( $json_obj->{ copy_from } );
	}
	elsif ( $json_obj->{ type } eq 'custom' )
	{
		my @rule_aux = split ( '\n', $json_obj->{ raw } );
		$rule_chain_st = &parseWAFRule( \@rule_aux );
	}

	# rule and action
	else
	{
		$rule_chain_st = &getWAFRulesStruct( $json_obj->{ type } );
		$err = &translateWafInputs( $json_obj, $rule_chain_st );
	}
	if ( $err )
	{
		return &httpErrorResponse( code => 400, desc => $desc, msg => $err );
	}

	# create a rule
	$params->{ phase } = $rule_st->{ phase };
	push @{ $rule_st->{ chain } }, $rule_chain_st;
	&zenlog( "????" );
	&zenlog( Dumper $rule_st);
	$err = &setWAFRule( $set, $rule_index, $rule_st );
	if ( $err )
	{
		return &httpErrorResponse( code => 400, desc => $desc, msg => $err );
	}

	# if has been created properly, the rule id is the last in the config file
	my $rule_out = &getWAFRule( $set, $rule_index );

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_waf', 'reload_rule', $set );

	my $msg    = "Settings were changed successful.";
	my $output = &getZapiWAFRule( $rule_out );
	my $body   = { description => $desc, params => $output, message => $msg };

	&httpResponse( { code => 201, body => $body } );
}

#  PUT /ipds/waf/<set>/rules/<id>/chain/index
sub modify_waf_rule_chain
{
	my $json_obj    = shift;
	my $set         = shift;
	my $rule_index  = shift;
	my $chain_index = shift;
	my $rule_st;
	my $chain_st;

	include 'Zevenet::IPDS::WAF::Config';
	my $desc = "Modify the chain $chain_index in rule $rule_index for the set $set";

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

	unless ( $rule_st->{ chain }->[$chain_index] )
	{
		my $msg = "Requested chain $chain_index has not been found.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $params;
	if ( exists $json_obj->{ raw } )
	{
		$params = { "raw" => { 'required' => 'true', 'non_blank' => 'true' }, };
		$chain_st = &parseWAFRule( $json_obj->{ raw } );
		unless ( $chain_st->{ type } eq 'rule' )
		{
			my $msg = "The WAF sentence could not be detect as type rule.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}
	else
	{
		$params = &getWafRuleModel( $rule_st->{ type } );
		delete $params->{ type };
		my $err = &translateWafInputs( $json_obj, $rule_st );
		if ( $err )
		{
			return &httpErrorResponse( code => 400, desc => $desc, msg => $err );
		}
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# modify a rule
	my $err;
	my $chain_ref = $rule_st->{ chain }->[$chain_index];
	foreach my $key ( keys %{ $chain_st } )
	{
		$chain_ref = $chain_st->{ $key };
	}
	$err = &setWAFRule( $set, $rule_index, $rule_st );
	if ( $err )
	{
		my $msg = "Modifying the rule $rule_index";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $err );
	}

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_waf', 'reload_rule', $set );

	my $msg          = "Settings were changed successful.";
	my $rule_updated = &getWAFRule( $set, $rule_index );
	my $outRule      = &getZapiWAFRule( $rule_updated );
	my $body         = { description => $desc, params => $outRule };

	return &httpResponse( { code => 200, body => $body } );
}

#  DELETE /ipds/waf/<set>/rules/<id>/chain/index
sub delete_waf_rule_chain
{
	my $set         = shift;
	my $id          = shift;
	my $chain_index = shift;
	my $err;

	include 'Zevenet::IPDS::WAF::Config';
	my $desc = "Delete the chain $chain_index from rule $id for the set $set";

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

	unless ( $rule->{ chain }->[$chain_index] )
	{
		my $msg = "The chain $chain_index has not been found";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( &deleteWAFRule( $set, $id, $chain_index ) )
	{
		my $msg = "Deleting the chain $chain_index";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_waf', 'reload_rule', $set );

	my $msg = "The chain $chain_index has been deleted properly";
	my $body = { description => $desc, message => $msg };

	&httpResponse( { code => 200, body => $body } );
}

1;
