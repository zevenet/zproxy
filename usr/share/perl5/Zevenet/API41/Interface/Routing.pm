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
include 'Zevenet::Net::Routing';

sub listOutRules
{
	my $list;
	foreach my $r ( @{ &listRoutingRules() } )
	{
		push @{ $list },
		  {
			priority => $r->{ priority } + 0,
			src      => $r->{ src },
			table    => $r->{ table },
			src_cdir => $r->{ srclen } + 0,
			id       => $r->{ id } + 0,
			type     => $r->{ type },
		  };
		$list->[-1]->{ not } = 'true' if ( exists $r->{ not } );
	}
	return $list // [];
}

sub list_routing_rules    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $desc = "List routing rules";
	my $list = &listOutRules();

	my $body = {
				 description => $desc,
				 params      => $list // [],
	};

	return &httpResponse( { code => 200, body => $body } );
}

#  POST /interfaces/routing/rules
sub create_routing_rule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	my $desc = "Create a routing rule";

	my $min_prio = &getGlobalConfiguration( 'routingRulePrioUserMin' );
	my $max_prio = &getGlobalConfiguration( 'routingRulePrioUserMax' );

	my $params = {
		"priority" => {
			'non_blank' => 'true',
			'interval'  => "$min_prio,$max_prio",
			'format_msg' =>
			  "It is the priority which the rule will be executed. Minor value of priority is going to be executed before",
		},
		"src" => {
			'valid_format' => 'ipv4v6',
			'non_blank'    => 'true',
			'required'     => 'true',
			'format_msg' =>
			  "It is the source address IP (v4 or v6). If it matches, the packet will be routed using the table 'table'",
		},
		"src_cdir" => {
				 'interval' => "1,128",
				 'format_msg' =>
				   "It is the length of the bit mask used in the src 'param' for matching.",
		},
		"table" => {
			'non_blank' => 'true',
			'required'  => 'true',
			'format_msg' =>
			  "It is the tabled used to route the packet if it matches with the src[/src_cdir]",
		},
		"not" => {
			'values' => ['true', 'false'],
			'format_msg' =>
			  "It is the 'not' logical operator. It is used with the src[/src_cdir] to negate its result",
		},
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# ????  check table exists

	# translate params
	if ( exists $json_obj->{ src_cdir } )
	{
		$json_obj->{ srclen } = $json_obj->{ src_cdir };
		delete $json_obj->{ src_cdir };
	}

	my $err = &createRoutingRules( $json_obj );
	if ( $err )
	{
		my $msg = "Error, creating a new routing rule.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $list = &listOutRules();
	return
	  &httpResponse(
					 {
					   code => 200,
					   body => { description => $desc, params => $list }
					 }
	  );
}

#  DELETE /interfaces/routing/rules/<id>
sub delete_routing_rule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $id = shift;

	my $desc = "Delete the routing rule '$id'";

	if ( !&getRoutingRulesExists( $id ) )
	{
		my $msg = "The rule id '$id' does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $error = &delRoutingRules( $id );
	if ( $error )
	{
		my $msg = "Error, deleting the rule '$id'.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $msg = "The routing rule '$id' has been deleted successfully.";
	my $body = {
				 description => $desc,
				 message     => $msg,
	};

	return &httpResponse( { code => 200, body => $body } );
}

###### routing tables

# GET /interfaces/routing/rules/tables
sub list_routing_tables
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	require Zevenet::Net::Route;

	my $desc = "List routing tables";
	my @list = &listRoutingTables();

	my $body = {
				 description => $desc,
				 params      => \@list,
	};

	return &httpResponse( { code => 200, body => $body } );
}

1;
