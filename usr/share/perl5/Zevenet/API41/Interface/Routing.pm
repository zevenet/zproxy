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
			from      => $r->{ from },
			table    => $r->{ table },
			id       => $r->{ id } + 0,
			type     => $r->{ type },
		  };
		$list->[-1]->{ not } = 'true' if ( exists $r->{ not } );
	}
	return $list // [];
}

sub listOutRoutes
{
	my $table = shift;
	my $list;

	foreach my $r ( @{ &listRoutingTable($table) } )
	{
		my $type = $r->{ type } // 'system';
		push @{ $list },
		  {
			id       => $r->{ id } + 0,
			raw     => $r->{ raw },
			type	=> $type,
		  };
	}
	return $list // [];
}

#  GET /routing/rules
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

#  POST /routing/rules
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
		"from" => {
			'valid_format' => 'ipv4v6',  ## ??? añadir segmento red
			'non_blank'    => 'true',
			'required'     => 'true',
			'format_msg' =>
			  "It is the source address IP or the source networking net that will be routed to the table 'table'",
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

	require Zevenet::Net::Route;
	if ( !&getRoutingTableExists($json_obj->{table}) )
	{
		my $msg = "The table '$json_obj->{table} does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# check if already exists an equal rule
	if( &isRule( $json_obj ) )
	{
		my $msg = "A rule with this configuration already exists";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
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

#  DELETE /routing/rules/<id>
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

# GET /routing/rules/tables
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

# GET /routing/tables/<id_table>
sub get_routing_table
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $table = shift;
	require Zevenet::Net::Route;

	my $desc = "Get the routing table $table";

	if ( !&getRoutingTableExists($table) )
	{
		my $msg = "The table '$table does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $list = &listOutRoutes($table);
	my $body = {
				 description => $desc,
				 params      => $list,
	};

	return &httpResponse( { code => 200, body => $body } );
}





#  POST /routing/tables/<id_table>/routes
sub create_routing_entry
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $table = shift;

	my $desc = "Create a routing entry in the table '$table'";

	my $params = {
		"raw" => {
			'required' => 'true',
			'non_blank' => 'true',
			'format_msg' =>
			  "It is the command line parameters to create an 'ip route' entry",
		},
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	require Zevenet::Net::Route;
	if ( !&getRoutingTableExists($table) )
	{
		my $msg = "The table '$table' does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# check if already exists an equal route
	if( &isRoute( $json_obj->{raw} ) )
	{
		my $msg = "A route with this configuration already exists";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( $json_obj->{raw} =~ /table\s+(\w+)/ )
	{
		my $t = $1;
		if ($t ne $table )
		{
			my $msg = "The input command is not in the requested table '$table'";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	$json_obj->{raw} = &sanitazeRouteCmd($json_obj->{raw}, $table);

	my $err = &createRoutingCustom( $table, $json_obj );
	if ( $err )
	{
		my $msg = "Error, creating a new routing rule.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $list = &listOutRoutes($table);
	return
	  &httpResponse(
					 {
					   code => 200,
					   body => { description => $desc, params => $list }
					 }
	  );
}

#  DELETE /routing/tables/<id_table>/routes/<id_route>
sub delete_routing_entry
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $table = shift;
	my $route_id = shift;

	my $desc = "Delete the routing entry '$route_id' from the table '$table'";

	if ( !&getRoutingTableExists($table) )
	{
		my $msg = "The table '$table' does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( !&getRoutingCustomExists( $table, $route_id ) )
	{
		my $msg = "The route entry '$route_id' does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $error = &delRoutingCustom( $table, $route_id );
	if ( $error )
	{
		my $msg = "Error, deleting the rule '$route_id'.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $msg = "The routing rule '$route_id' has been deleted successfully.";
	my $body = {
				 description => $desc,
				 message     => $msg,
	};

	return &httpResponse( { code => 200, body => $body } );
}



# POST /routing/isolate
sub set_routing_isolate
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $json_obj = shift;
	require Zevenet::Net::Route;

	my $desc = "Modify the interfaces visibility";

	my $params = {
		"interface" => {
			'required' => 'true',
			'non_blank' => 'true',
			'format_msg' =>
			  "It is the interface that will not be included in other route tables",
		},
		"action" => {
			'required' => 'true',
			'non_blank' => 'true',
			'values' => ['set','unset'],
			'format_msg' =>
			  "Action to apply: 'set' to not incluid the interface in the route tables of the other interfaces; 'unset' to incluid this interface in the route table of the other interfaces.",
		},
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# if
	require Zevenet::Net::Validate;
	if ( !&ifexist ($json_obj->{interface}) )
	{
		my $msg = "The interface '$json_obj->{interface}' does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# if
	my $if_ref = &getInterfaceConfig( $json_obj->{ interface } );
	unless ( $if_ref )
	{
		my $msg = "The interface has to be configured";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# configured
	my $status = ($json_obj->{action} eq 'set') ? "true" : "false";
	my $err = &setRoutingIsolate( $if_ref,$status );
	if ( $err )
	{
		my $msg = "There was an error setting the isolate feature";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $body = {
				 description => $desc,
				 message      => "The action was applied successfully",
	};

	return &httpResponse( { code => 200, body => $body } );
}

1;
