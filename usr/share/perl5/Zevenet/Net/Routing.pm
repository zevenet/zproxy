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
use Config::Tiny;
require Zevenet::File;
require Zevenet::Net::Route;

my $routes_dir   = &getGlobalConfiguration( 'configdir' ) . "/routes";
my $rules_conf   = "$routes_dir/rules.conf";
my $isolate_conf = "$routes_dir/isolate.conf";
my $lock_rules   = "route_rules";
my $lock_isolate = "route_isolate";

my $ip_bin = &getGlobalConfiguration( 'ip_bin' );

=begin nd
Function: getRoutingTableFile

	It returns the routing table config file path

Parameters:
	table - table name

Returns:
	String - path to the table config file

=cut

sub getRoutingTableFile
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $table = shift;
	return "$routes_dir/$table.conf";
}

=begin nd
Function: getRoutingTableLock

	It returns the file used to lock a routing table

Parameters:
	table - table name

Returns:
	String - file name used to lock the table

=cut

sub getRoutingTableLock
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $table = shift;
	return "routing_$table";
}

################## rules #######################
################################################

=begin nd
Function: getRoutingRulesExists

	check a route rule exists by its 'id'

Parameters:
	rule id - rule unique identifier

Returns:
	Integer - it returns 1 if the rule already exists or 0 if it does not exist

=cut

sub getRoutingRulesExists
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $id = shift;
	return 0 if !-f $rules_conf;

	my $fh = Config::Tiny->read( $rules_conf );

	return ( exists $fh->{ $id } ) ? 1 : 0;
}

=begin nd
Function: getRoutingRulesConf

	Get the routing rule by its 'id'. it returns all the configuration parameters from the config file

Parameters:
	rule id - rule unique identifier

Returns:
	Hash ref - object with the parameters got from the rule config file

=cut

sub getRoutingRulesConf
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $id = shift;

	my $fh = Config::Tiny->read( $rules_conf );

	return $fh->{ $id };
}

=begin nd
Function: listRoutingRulesConf

	It returns a list of the routing rules from the configuration file, they are
	the rules that the user created.

Parameters:
	none - .

Returns:
	Array ref - list of routing rules

=cut

sub listRoutingRulesConf
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	return [] if !-f $rules_conf;

	my @rules = ();
	my $fh    = Config::Tiny->read( $rules_conf );

	foreach my $r ( keys %{ $fh } )
	{
		push @rules, $fh->{ $r };
	}

	return \@rules;
}

=begin nd
Function: genRoutingId

	Generate an ID for routing rules and table entries.

Parameters:
	none - .

Returns:
	Integer - Returns an ID greater than 0 or 0 if there was an error

=cut

sub genRoutingId
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $file      = shift;
	my $max_index = 1024;
	my $id        = 0;
	my $fh        = Config::Tiny->read( $file );

	for ( ; $max_index > 0 ; $max_index-- )
	{
		if ( !exists $fh->{ $max_index } )
		{
			$id = $max_index;
			last;
		}
	}

	return $id;
}

=begin nd
Function: createRoutingRulesConf

	It adds a new rule to the configuration file.

Parameters:
	none - .
		"priority": 32759,
		"from": "2.2.4.0/24",
		"table": "table_eth2.4"

Returns:
	Integer - 0 on success or other value on failure

=cut

sub createRoutingRulesConf
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $in = shift;

	require Zevenet::Net::Route;

	&createFile( $rules_conf ) if ( !-f $rules_conf );

	&lockResource( $lock_rules, 'l' );
	my $fh = Config::Tiny->read( $rules_conf );

	my @params = ( 'priority', 'id', 'from', 'type', 'not', 'table' );
	my $conf;
	foreach my $p ( @params )
	{
		$conf->{ $p } = $in->{ $p };
	}

	if ( !$conf->{ id } )
	{
		&lockResource( $lock_rules, 'ud' );
		&zenlog( "Error getting an ID for the rule", "error", "net" );
		return 1;
	}

	$fh->{ $conf->{ id } } = $conf;
	$fh->write( $rules_conf );

	&zenlog( "The routing rule '$conf->{id}' was created properly", "info", "net" );
	&zenlog( "Params: " . Dumper( $conf ), "debug2", "net" );

	&lockResource( $lock_rules, 'ud' );

	return 0;
}

=begin nd
Function: delRoutingConfById

	delete an element of a tiny file using its 'key'

Parameters:
	key - id in the tiny file
	file - file from delete the item
	lock file - file used to lock the file resource

Returns:
	Integer - 0 on success or 1 on failure

=cut

sub delRoutingConfById
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $id   = shift;
	my $file = shift;
	my $lf   = shift;    # lock file

	&createFile( $file ) if ( !-f $file );

	&lockResource( $lf, 'l' );
	my $fh = Config::Tiny->read( $file );

	if ( !exists $fh->{ $id } )
	{
		&lockResource( $lf, 'ud' );
		&zenlog( "Error deleting the id '$id', it was not found", "error", "net" );
		return 1;
	}

	delete $fh->{ $id };
	$fh->write( $file );

	&zenlog( "The routing rule '$id' was deleted properly", "info", "net" );

	&lockResource( $lf, 'ud' );
	return 0;
}

=begin nd
Function: delRoutingRules

	Delete a routing rule. From the system and the config file

Parameters:
	id rule - unique indentifier of the routing rule

Returns:
	Integer - 0 on success or 1 on failure

=cut

sub delRoutingRules
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $id = shift;

	my $conf = &getRoutingRulesConf( $id );
	my $error = &setRule( 'del', $conf );
	$error = &delRoutingConfById( $id, $rules_conf, $lock_rules ) if ( !$error );

	return $error;
}

=begin nd
Function: createRoutingRules

	Create a routing rule. It is created in the config file and apply it to the system

Parameters:
	config - Object with the configuration of the rule. The possible keys are: 'priority', 'from', 'not', 'table'

Returns:
	Integer - It returns the rule id of the rule has been created, or 0 on failure

=cut

sub createRoutingRules
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $conf = shift;

	$conf->{ type }     = 'user';
	$conf->{ id }       = &genRoutingId( $rules_conf );
	$conf->{ priority } = &genRoutingRulesPrio( 'user' )
	  if ( !exists $conf->{ priority } );
	my $err = &setRule( 'add', $conf );
	$err = &createRoutingRulesConf( $conf ) if ( !$err );

	return ( $err ) ? 0 : $conf->{ id };
}

=begin nd
Function: modifyRoutingRules

	Modify a routing rule. It is modified in the config file (using the function createRoutingRulesConf)
	and apply the route in the system (using the function createRoutingRulesConf)

Parameters:
	id - It is the routing rule ID that is going to be modified
	config - Object with the configuration of the rule. The possible keys are: 'priority', 'from', 'not', 'table'

Returns:
	Integer - It returns 0 on success or another value on failure

=cut

sub modifyRoutingRules
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $id     = shift;
	my $params = shift;

	# delete
	my $old_conf = &getRoutingRulesConf( $id );
	my $err = &setRule( 'del', $old_conf );

	if ( !$err )
	{
		# overwrite conf
		$err = &setRule( 'add', $params );
		$err = &createRoutingRulesConf( $params ) if ( !$err );
	}

	# if there is an error, revert route
	&setRule( 'add', $old_conf ) if ( $err );

	return $err;
}

=begin nd
Function: updateRoutingRules

	It gets the configuration of a routing rule and update the struct with new
	values. It does not write any information in the config file.


Parameters:
	id - It is the routing rule ID that is going to be modified
	config - Object with the new values to overwrite in the config struct. The possible keys are: 'priority', 'from', 'not', 'table'

Returns:
	hash ref - It is the rule struct upated with the new values

=cut

sub updateRoutingRules
{
	my $id         = shift;
	my $new_values = shift;

	my $old_conf = &getRoutingRulesConf( $id );

	my $new_conf;
	foreach my $p ( keys %{ $old_conf } )
	{
		$new_conf->{ $p } = $new_values->{ $p } // $old_conf->{ $p };
	}

	return $new_conf;
}

=begin nd
Function: applyRoutingAllRules

	Apply to the system all rules from the config file. Useful to run rules when zevenet is started

Parameters:
	none - .

Returns:
	Integer - 0 on success or 1 on failure

=cut

sub applyRoutingAllRules
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $err = 0;

	my $rules = &listRoutingRulesConf();
	foreach my $r ( @{ $rules } )
	{
		$err = &setRule( "add", $r );
	}

	return $err;
}

=begin nd
Function: initRoutingModule

	Manage the run of the routing module. First, it creates the requested config
	directories, next, it applies the rules to the system

Parameters:
	none - .

Returns:
	none - .

=cut

sub initRoutingModule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	mkdir $routes_dir if ( !-d $routes_dir );
	&createFile( $rules_conf ) if ( !-f $rules_conf );

	&applyRoutingAllRules();

	# The routes are been applied when the iface is link up
}

=begin nd
Function: getRoutingIsolateTables

	It returns a list of the interfaces and info about if they are managed in a routing table

Parameters:
	table - table name to ckeck

Returns:
	array ref - it is the list of interface with information about if it is managed in the table

=cut

sub getRoutingIsolateTables
{
	my $table  = shift;
	my @ifaces = ();

	my @tables;
	require Zevenet::Net::Interface;

	foreach my $if ( &getLinkNameList() )
	{
		next if "table_$if" eq $table;      # does not add the same interface
		next if $if eq 'lo';                # does not add the lo interface
		next if $if eq 'cl_maintenance';    # does not add the cluster interface

		my $iface;
		@tables = &getRoutingIsolate( $if );
		$iface->{ interface } = $if;
		$iface->{ unmanaged } = ( grep ( /^$table$/, @tables ) ) ? 'true' : 'false';
		push @ifaces, $iface;
	}

	return @ifaces;
}

=begin nd
Function: getRoutingIsolate

	It returns a list of the tables names where the interface is deleted. These
	tables have not a route to reach the interface

Parameters:
	interface - interface

Returns:
	array ref - it is the list of tables where the interface is deleted

=cut

sub getRoutingIsolate
{
	my $iface  = shift;
	my @tables = ();

	return () if ( !-f $isolate_conf );

	my $fh = Config::Tiny->read( $isolate_conf );
	if ( exists $fh->{ $iface }->{ table } and $fh->{ $iface }->{ table } =~ /\S/ )
	{
		@tables = split ( ' ', $fh->{ $iface }->{ table } );
	}

	return @tables;
}

=begin nd
Function: setRoutingIsolate

	Enable or disable the interface will be accesible from the others interfaces routing tables.
	This function writes in the config file and reload the routes in the system

Parameters:
	interface - interface name is going to be deleted from the table
	table - the table where the interface route is going to be deleted
	action - This parameter can have the value 'add' the entry in the configuration file
		and delete the interface from the table; 'del' to delete the entry from the
		configuration file and set the interface rotue in the table

Returns:
	none - .

=cut

sub setRoutingIsolate
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $interface = shift;
	my $table     = shift;
	my $action    = shift;

	# set conf
	&lockResource( $lock_isolate, "l" );

	&writeRoutingIsolateConf( $interface, $table, $action );

	&reloadRoutingTable( $interface );

	#Release lock file
	&lockResource( $lock_isolate, "ud" );
}

=begin nd
Function: writeRoutingIsolateConf

	It writes in the configuration file option set from the API. Delete to remove
	the entry from the configuration file and allow the visibility of the interface;
	or 'add' to add the entry to de config file and does not allow the visibility
	of the interface from the table

Parameters:
	interface - interface name is going to be deleted from the table
	table - the table where the interface route is going to be deleted
	action - This parameter can have the value 'add' the entry in the configuration file
		and delete the interface from the table; 'del' to delete the entry from the
		configuration file and set the interface rotue in the table

Returns:
	none - .

=cut

sub writeRoutingIsolateConf
{
	my $interface = shift;
	my $table     = shift;
	my $action    = shift;

	&createFile( $isolate_conf ) if ( !-f $isolate_conf );

	my $fh = Config::Tiny->read( $isolate_conf );

	if ( $table eq '*' and $action eq 'add' )
	{
		$fh->{ $interface }->{ table } = '*';
	}
	elsif (     $action eq 'add'
			and $fh->{ $interface }->{ table } !~ /(^| )$table( |$)/ )
	{
		$fh->{ $interface }->{ table } .= " $table";
	}
	elsif ( $table eq '*' and $action eq 'del' )
	{
		$fh->{ $interface }->{ table } = '';
	}
	elsif ( $action eq 'del' )
	{
		$fh->{ $interface }->{ table } =~ s/(^| )$table( |$)/ /;
	}

	$fh->write( $isolate_conf );

	&zenlog( "The table '$table' was modified properly", "info", "net" );
}

=begin nd
Function: reloadRoutingTable

	It reloads the routing entries (in the system) of a routing table of a interface

Parameters:
	interface - interface name

Returns:
	Integer - 0 on success or another value on failure

=cut

sub reloadRoutingTable
{
	my $if_name = shift;

	my $err = 0;

	require Zevenet::Net::Interface;
	my $if_ref = &getInterfaceConfig( $if_name );

	# del route
	$err = &dellocalnet( $if_ref );
	&zenlog( "Error deleting routes" ) if ( $err );

	# apply new conf
	my $err2 = &applyRoutes( "local", $if_ref, $if_ref->{ gateway } );
	&zenlog( "Error applying routes" ) if ( $err2 );

	$err += $err2;

	return $err;
}

=begin nd
Function: listRoutingTableCustom

	List all routing entries of a table that were created by the user

Parameters:
	table - table name

Returns:
	Array ref - list of the routing entries

=cut

sub listRoutingTableCustom
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $table = shift;
	my $file  = &getRoutingTableFile( $table );

	return [] if !-f $file;

	my @list = ();
	my $fh   = Config::Tiny->read( $file );

	foreach my $r ( keys %{ $fh } )
	{
		push @list, $fh->{ $r };
	}

	return \@list;
}

=begin nd
Function: listRoutingTableSys

	List all the system routing entries of a table. The entries were created by the user are not returned.

Parameters:
	table - table name

Returns:
	Array ref - list of the routing entries

=cut

sub listRoutingTableSys
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $table = shift;

#~ my $data = &logAndGet ("$ip_bin -j route list table $table"); # there is a bug with ip route json

	my $data = &logAndGet( "$ip_bin route list table $table", 'array' );

	my $routeparams = &getGlobalConfiguration( "routeparams" );

	# filter data
	my @routes = ();
	foreach my $cmd ( @{ $data } )
	{
		# it is not a system rule
		next if ( $cmd !~ /$routeparams/ );

		my $r = {};
		$r->{ type } = 'system';
		$r->{ raw }  = "$cmd table $table";

		&splitRoutingCmd( $r );

		push @routes, $r;
	}

	return \@routes;
}

=begin nd
Function: delRoutingDependIface

	Delete all routes, rules and isolate infor that have dependence on a interface

Parameters:
	interface - name of the interface

Returns:
	Integer - 0 on success or another value on failure

=cut

sub delRoutingDependIface
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $iface = shift;

	&zenlog( "Deleting the routes that are depending on '$iface'", 'info', 'net' );
	my $rule_list = &listRoutingDependIface( $iface );
	foreach my $rule ( @{ $rule_list } )
	{
		my $err = &setRoute( 'del', $rule->{ raw } );
		return 1 if $err;

		my $file   = &getRoutingTableFile( $rule->{ table } );
		my $lock_f = &getRoutingTableLock( $rule->{ table } );
		$err = &delRoutingConfById( $rule->{ id }, $file, $lock_f );
		return 1 if $err;
	}

	# the rules were removed from the system when the interface was set down
	my $file = &getRoutingTableFile( "table_$iface" );
	unlink $file;

	&zenlog( "Deleting the rules that are depending on '$iface'", 'info', 'net' );
	$rule_list = &listRoutingRulesConf();
	foreach my $rule ( @{ $rule_list } )
	{
		if ( $rule->{ table } eq "table_$iface" )
		{
			&delRoutingRules( $rule->{ id } );
		}
	}

	&zenlog( "Deleting unmanage information about '$iface'", 'info', 'net' );
	if ( -f $isolate_conf )
	{
		&lockResource( $lock_isolate, "l" );
		my $fh = Config::Tiny->read( $isolate_conf );
		foreach my $if ( keys %{ $fh } )
		{
			$fh->{ $if }->{ table } =~ s/(^| )table_$iface( |$)/ /;
		}
		delete $fh->{ $iface };
		$fh->write( $isolate_conf );
		&lockResource( $lock_isolate, "ud" );
	}

	return 0;
}

=begin nd
Function: updateRoutingVirtualIfaces

	This function replace a virtual interface from all routing tables where is being used
	as source.
	If the new interface IP is 'undef'. The routes where the virtual interface appears will be
	deleted.

Parameters:
	interface - name of the interface where the virtual IP appends
	old ip - IP that will be deleted from the routes
	new ip - New IP for the virtual interface

Returns:
	none - .

=cut

sub updateRoutingVirtualIfaces
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $parent_name = shift;
	my $old_ip      = shift;
	my $new_ip      = shift;

	&zenlog( "Refresing rules for ip '$old_ip'", 'info', 'net' );
	&zenlog( "new ip '$new_ip'", 'info', 'net' ) if ( defined $new_ip );

	my $list = &listRoutingDependIface( $parent_name );
	foreach my $rule ( @{ $list } )
	{
		next unless ( $old_ip eq $rule->{ source } );

		my $new_rule;
		if ( defined $new_ip and $new_ip ne '' )
		{
			my $new_rule = $rule;
			$new_rule->{ source } = $new_ip;
			$new_rule->{ raw } = &buildRouteCmd( $new_rule->{ table }, $new_rule );
		}
		my $err = &delRoutingCustom( $rule->{ table }, $rule->{ id } );

		if ( defined $new_rule )
		{
			$err = &createRoutingCustom( $rule->{ table }, $new_rule );
		}

		&zenlog( "There was an error changing the routes for the virtual IP $old_ip",
				 "error", "net" )
		  if $err;
	}
}

=begin nd
Function: applyRoutingTableByIface

	It applies to an interface table all the routes created by the user for that table

Parameters:
	table - name of the table
	interface - name of the interface

Returns:
	Integer - 0 on success or another value on failure

=cut

sub applyRoutingTableByIface
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $table = shift;
	my $iface = shift;

	my $err = 0;
	foreach my $rule ( @{ &listRoutingTableCustom( $table ) } )
	{
		if ( $rule->{ interface } eq $iface )
		{
			$err = &setRoute( 'add', $rule->{ raw } );
			return $err if $err;
		}
	}

	return $err;
}

=begin nd
Function: listRoutingDependIface

	It returns a list of custom rules that are dependent of an interface

Parameters:
	interface - name of the interface

Returns:
	Array ref - List of rules, each item is a hash with the routes parameters

=cut

sub listRoutingDependIface
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $iface = shift;
	my @list  = ();

	foreach my $table ( &listRoutingTablesNames() )
	{
		my $ruleList = &listRoutingTableCustom( $table );
		foreach my $rule ( @{ $ruleList } )
		{
			if ( $rule->{ interface } eq $iface )
			{
				$rule->{ table } = $table;
				push @list, $rule;
			}
		}
	}

	return \@list;
}

=begin nd
Function: listRoutingTable

	It returns a list of rules (rules objects) of a routing table.
	This list contains all the custom and system routes

Parameters:
	table - name of the table

Returns:
	Array ref - List of rules, each item is a hash with the routes parameters

=cut

sub listRoutingTable
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $table = shift;

	my $list   = &listRoutingTableCustom( $table );
	my @routes = @{ $list };

	my $sys = &listRoutingTableSys( $table );
	push @routes, @{ $sys };

	return \@routes;
}

=begin nd
Function: getRoutingCustomExists

	It checks if a route id already exists.

Parameters:
	table - name of the table
	route id - id of the route

Returns:
	Integer - 1 if the ID exists or 0 if it does not

=cut

sub getRoutingCustomExists
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $table    = shift;
	my $route_id = shift;

	my $file = &getRoutingTableFile( $table );
	return 0 if !-f $file;

	my $fh = Config::Tiny->read( $file );

	return ( exists $fh->{ $route_id } ) ? 1 : 0;
}

=begin nd
Function: buildRouteCmd

	It builds a command using the conf parameters of a route entry.

Parameters:
	table - name of the table where set the route
	route conf - hash reference with the routing parameters. The possible parameters are:
		"to" is the destination IP or networking segment
		"interface" is the interface used to take out the packet
		"source" is the IP used as source when the packet is going out
		"via" is the IP of the next routing item
		"mtu" is the maximum trasmition unit
		"priority" is the priority for the routing entry in the table

Returns:
	String - String with the command

=cut

sub buildRouteCmd
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $table = shift;
	my $param = shift;
	my $cmd   = "";

	$cmd .= "$param->{to} " if ( exists $param->{ to } and $param->{ to } ne '' );
	$cmd .= "dev $param->{interface} "
	  if ( exists $param->{ interface } and $param->{ interface } ne '' );
	$cmd .= "src $param->{source} "
	  if ( exists $param->{ source } and $param->{ source } ne '' );
	$cmd .= "via $param->{via} "
	  if ( exists $param->{ via } and $param->{ via } ne '' );
	$cmd .= "mtu $param->{mtu} "
	  if ( exists $param->{ mtu } and $param->{ mtu } ne '' );
	$cmd .= "metric $param->{priority} "
	  if ( exists $param->{ priority } and $param->{ priority } ne '' );
	$cmd .= "table $table " if ( $cmd ne "" );

	return $cmd;
}

=begin nd
Function: writeRoutingConf

	It save the route conf in the config file

Parameters:
	table - name of the table where set the route
	route conf - hash reference with the routing parameters. The possible parameters are:
		"to" is the destination IP or networking segment
		"interface" is the interface used to take out the packet
		"source" is the IP used as source when the packet is going out
		"via" is the IP of the next routing item
		"mtu" is the maximum trasmition unit
		"priority" is the priority for the routing entry in the table

Returns:
	none - .

=cut

sub writeRoutingConf
{
	my ( $table, $input ) = @_;

	my @params =
	  ( 'id', 'raw', 'type', 'to', 'interface', 'via', 'source', 'priority' );

	my $file = &getRoutingTableFile( $table );
	&createFile( $file ) if ( !-f $file );

	my $fh = Config::Tiny->read( $file );

	my $conf;
	foreach my $p ( @params )
	{
		$conf->{ $p } = $input->{ $p };
	}

	$fh->{ $conf->{ id } } = $conf;
	$fh->write( $file );

	&zenlog( "The routing entry '$conf->{id}' was created properly", "info",
			 "net" );
	&zenlog( "Params: " . Dumper( $conf ), "debug2", "net" );
}

=begin nd
Function: createRoutingCustom

	It creates a new route for a table. It applies in the system and before write
	the conf in the config file (using the function "writeRoutingConf")

Parameters:
	table - name of the table where set the route
	route conf - hash reference with the routing parameters. The possible parameters are:
		"to" is the destination IP or networking segment
		"interface" is the interface used to take out the packet
		"source" is the IP used as source when the packet is going out
		"via" is the IP of the next routing item
		"mtu" is the maximum trasmition unit
		"priority" is the priority for the routing entry in the table

Returns:
	Integer - returns the ID of the route on success or 0 on failure

=cut

sub createRoutingCustom
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $table = shift;
	my $input = shift;

	my $lock_rules = &getRoutingTableLock( $table );
	&lockResource( $lock_rules, 'l' );

	my $err = &setRoute( 'add', $input->{ raw } );
	my $id = 0;

	if ( !$err )
	{
		my $file = &getRoutingTableFile( $table );
		$input->{ id }   = &genRoutingId( $file );
		$input->{ type } = 'user';

		if ( !$input->{ id } )
		{
			&zenlog( "Error getting an ID for the route", "error", "net" );
		}
		else
		{
			$id = $input->{ id };
			&writeRoutingConf( $table, $input );
		}
	}

	&lockResource( $lock_rules, 'ud' );
	return $id;
}

=begin nd
Function: modifyRoutingCustom

	It modifies a route. It removes the old rule and applies the new one in the system.
	After update de config file (using the function "writeRoutingConf")

Parameters:
	table - name of the table where set the route
	route conf - hash reference with the routing parameters. The possible parameters are:
		"to" is the destination IP or networking segment
		"interface" is the interface used to take out the packet
		"source" is the IP used as source when the packet is going out
		"via" is the IP of the next routing item
		"mtu" is the maximum trasmition unit
		"priority" is the priority for the routing entry in the table

Returns:
	Integer - 0 on success or another value on failure

=cut

sub modifyRoutingCustom
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $table    = shift;
	my $route_id = shift;
	my $new_conf = shift;

	my $lock_rules = &getRoutingTableLock( $table );
	&lockResource( $lock_rules, 'l' );

	#delete
	my $old_conf = &getRoutingTableConf( $table, $route_id );
	&setRoute( 'del', $old_conf->{ raw } );

	my $err = &setRoute( 'add', $new_conf->{ raw } );
	if ( !$err )
	{
		# save conf
		&writeRoutingConf( $table, $new_conf );
	}
	else
	{
		&setRoute( 'add', $old_conf->{ raw } );
	}

	&lockResource( $lock_rules, 'ud' );
	return $err;
}

=begin nd
Function: splitRoutingCmd

	It parser a routing command line and it creates an struct with the data parsed from command

	The command is passed in a hash reference, with the key 'raw'. This hash will be update with the parsed values.
	The hash after this function will look like:

	{
		"raw"  is the routing command line
		"to" is the destination IP or networking segment
		"interface" is the interface used to take out the packet
		"source" is the IP used as source when the packet is going out
		"via" is the IP of the next routing item
		"priority" is the priority for the routing entry in the table
	}

Parameters:
	routing conf - It is a hash that has to contains the key 'raw'. This hash will be update with the get values

Returns:
	none - .

=cut

sub splitRoutingCmd
{
	my $r   = $_[0];
	my $cmd = $r->{ raw };

	# reset values
	$r->{ to }        = '';
	$r->{ via }       = '';
	$r->{ source }    = '';
	$r->{ interface } = '';

	if ( $cmd =~ /^(\S+)/ )
	{
		$r->{ to } = $1;
	}

	if ( $cmd =~ /via\s(\S+)/ )
	{
		$r->{ via } = $1;
	}

	if ( $cmd =~ /src\s(\S+)/ )
	{
		$r->{ source } = $1;
	}

	if ( $cmd =~ /dev\s(\S+)/ )
	{
		$r->{ interface } = $1;
	}

	if ( $cmd =~ /(?:metric|preference)\s(\S+)/ )
	{
		$r->{ priority } = $1;
	}

	$_[0] = $r;
}

=begin nd
Function: updateRoutingParams

	It returns a route updated with new parameters that are been modified.
	It gets the route conf from the table configuration file and it returns the struct overwriting
	the parameters that have been modified, it does not do any conf write.

Parameters:
	table - name of the table where set the route
	route conf - hash reference with the routing parameters. The possible parameters are:
		"to" is the destination IP or networking segment
		"interface" is the interface used to take out the packet
		"source" is the IP used as source when the packet is going out
		"via" is the IP of the next routing item
		"mtu" is the maximum trasmition unit
		"priority" is the priority for the routing entry in the table

Returns:
	Hash ref - Route struct with the configuration updated

=cut

sub updateRoutingParams
{
	my $table      = shift;
	my $route_id   = shift;
	my $new_values = shift;

	my $old_conf = &getRoutingTableConf( $table, $route_id );

	my $new_conf;
	foreach my $p ( keys %{ $old_conf } )
	{
		$new_conf->{ $p } = $new_values->{ $p } // $old_conf->{ $p };
	}

	return $new_conf;
}

=begin nd
Function: getRoutingTableConf

	It returns a struct with all the route configuration stored in the config file

Parameters:
	table - name of the table where getting the route
	route id - id of the route

Returns:
	Hash ref - It is an object with the route config

=cut

sub getRoutingTableConf
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $table = shift;
	my $id    = shift;

	my $file = &getRoutingTableFile( $table );
	my $fh   = Config::Tiny->read( $file );

	return $fh->{ $id };
}

=begin nd
Function: delRoutingCustom

	It deletes a route. It deletes it from the config file and from the system.

Parameters:
	table - name of the table where getting the route
	route id - id of the route

Returns:
	Integer - 0 on success or 1 on failure

=cut

sub delRoutingCustom
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $table    = shift;
	my $route_id = shift;

	my $conf = &getRoutingTableConf( $table, $route_id );
	return 1 if ( &setRoute( 'del', $conf->{ raw } ) );

	my $file   = &getRoutingTableFile( $table );
	my $lock_f = &getRoutingTableLock( $table );
	return &delRoutingConfById( $route_id, $file, $lock_f );
}

=begin nd
Function: setRoute

	It deletes a route. It deletes it from the config file and from the system.

Parameters:
	action - it is the action to apply to the route, 'add' to add it to the system or 'del' to remove it from the system
	route cmd - it is a string with the parameters of the route

Returns:
	Integer - 0 on success or another value on failure

=cut

sub setRoute
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $action     = shift;
	my $cmd_params = shift;
	my $ipv        = shift // '';

	my $exist = &isRoute( $cmd_params, $ipv );

	if (    ( $exist and $action eq 'add' )
		 or ( !$exist and $action eq 'del' ) )
	{
		&zenlog( "Does not found the route in the system: '$cmd_params'", "debug2" );
		return 0;
	}

	$ipv = "-$ipv" if ( $ipv ne '' );
	my $cmd = "$ip_bin $ipv route $action $cmd_params";

	return &logAndRun( $cmd );
}

=begin nd
Function: applyRoutingCustom

	It applies an action to all the routes of an interface table.
	First it gets the data from the conf files, after, it applies one by one in the system

Parameters:
	action - it is the action to apply to the route, 'add' to add it to the system or 'del' to remove it from the system
	table - name of the table

Returns:
	Integer - 0 on success or another value on failure

=cut

sub applyRoutingCustom
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $action = shift;
	my $table  = shift;
	my $err    = 0;

	my $list = &listRoutingTableCustom( $table );

	foreach my $it ( @{ $list } )
	{
		$err += &setRoute( $action, $it->{ raw } );
	}

	return $err;
}

=begin nd
Function: sanitazeRouteCmd

	It takes an input command line and cleanning y adding options to adapt it to the
	Zevenet routing module

Parameters:
	command - raw command line to apply in the system
	table - name of the table where the command is going to be set

Returns:
	String - Command line adapted to routing module

=cut

sub sanitazeRouteCmd
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $cmd   = shift;
	my $table = shift;

	&zenlog( "Sanitazing route cmd: $cmd", "debug2", "net" );
	my $routeparams = &getGlobalConfiguration( "routeparams" );
	if ( $cmd =~ s/$routeparams// )
	{
		# this is used to identify the rules are from system
		&zenlog( "Removing: window sizes", "debug2", "net" );
	}
	if ( $cmd !~ /table/ )
	{
		$cmd .= " table $table";
		&zenlog( "Adding table: $cmd", "debug2", "net" );
	}
	if ( $cmd =~ s/\s*ip\s+(-4|-6)?\s*route\s+\w+\s+// )
	{
		&zenlog( "Removing bin: $cmd", "debug2", "net" );
	}
	if ( $cmd !~ /(?:preference|metric)/ )
	{
		my $preference = &getGlobalConfiguration( "routingRoutePrio" );
		$cmd .= " preference $preference";
		&zenlog( "Adding a priority: $cmd", "debug2", "net" );
	}

	return $cmd;
}

1;
