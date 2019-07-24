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

my $routes_dir = &getGlobalConfiguration( 'configdir' ) . "/routes";
my $rules_conf = "$routes_dir/rules.conf";
my $lock_rules = "route_rules";

my $ip_bin     = &getGlobalConfiguration( 'ip_bin' );

sub getRoutingTableFile
{
	my $table = shift;
	return "$routes_dir/$table.conf";
}

sub getRoutingTableLock
{
	my $table = shift;
	return "routing_$table";
}

################## rules #######################
################################################

sub getRoutingRulesExists
{
	my $id = shift;
	return 0 if !-f $rules_conf;

	my $fh = Config::Tiny->read( $rules_conf );

	return ( exists $fh->{ $id } ) ? 1 : 0;
}

sub getRoutingRulesConf
{
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
	my $file = shift;
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
	my $in = shift;

	require Zevenet::Net::Route;

	&createFile( $rules_conf ) if ( !-f $rules_conf );

	&lockResource( $lock_rules, 'l' );
	my $fh = Config::Tiny->read( $rules_conf );

	my @params = ('priority', 'id', 'from', 'type', 'not', 'table');
	my $conf;
	foreach my $p (@params)
	{
		$conf->{$p} = $in->{$p};
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

sub delRoutingConfById
{
	my $id = shift;
	my $file = shift;
	my $lf = shift; # lock file

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


sub delRoutingRules
{
	my $id = shift;

	my $conf  = &getRoutingRulesConf( $id );
	my $error = &setRule( 'del', $conf );
	$error = &delRoutingConfById( $id, $rules_conf, $lock_rules ) if ( !$error );

	return $error;
}


sub createRoutingRules
{
	my $conf = shift;

	$conf->{ type } = 'user';
	$conf->{ id }   = &genRoutingId($rules_conf);
	$conf->{ priority } = &genRoutingRulesPrio('user') if ( !exists $conf->{ priority } );
	my $err = &setRule( 'add', $conf );
	$err = &createRoutingRulesConf( $conf ) if ( !$err );

	return $err;
}

sub applyRoutingAllRules
{
	my $err = 0;

	my $rules = &listRoutingConfRules();
	foreach my $r ( @{ $rules } )
	{
		$err = &setRule( "add", $r );
	}

	return $err;
}

sub initRoutingModule
{
	mkdir $routes_dir if ( !-d $routes_dir );
	&createFile( $rules_conf ) if ( !-f $rules_conf );

	&applyRoutingAllRules();

	# The routes are been applied when the iface is link up
}

sub setRoutingIsolate
{
	my $if_ref = shift;
	my $status = shift; # true|false
	my $lock_if = "/tmp/if_isolate.lock";

	# set conf
	&lockResource( $lock_if, "l" );

	require Zevenet::Net::Interface;
	$if_ref->{isolate} = $status;
	my $err = &setInterfaceConfig( $if_ref ); # returns 1 on success

	if ($err)
	{
		$err = 0;
		my $if_ref = &getInterfaceConfig( $if_ref->{ name } );

		# del route
		$err = &dellocalnet( $if_ref );
		&zenlog ("Error deleting routes") if ($err);

		# apply new conf
		my $err2 = &applyRoutes( "local", $if_ref, $if_ref->{ gateway } );
		&zenlog ("Error applying routes") if ($err2);

		$err += $err2;
	}

	#Release lock file
	&lockResource( $lock_if, "ud" );

	return $err;
}



sub listRoutingTableCustom
{
	my $table = shift;
	my $file = &getRoutingTableFile($table);

	return [] if !-f $file;

	my @list = ();
	my $fh    = Config::Tiny->read( $file );

	foreach my $r ( keys %{ $fh } )
	{
		push @list, $fh->{$r};
	}

	return \@list;
}


sub listRoutingTableSys
{
	my $table = shift;

	my $list = &logAndGet ("$ip_bin -j -p route list table $table");

	# ???? parsing json

	return $list;
}



sub listRoutingTable
{
	my $list = [];
	my $list = &listRoutingTableCustom();

	# push @{$list}, &listRoutingTableSys(); # add ?????

	return $list;
}

sub getRoutingCustomExists
{
	my $table = shift;
	my $route_id = shift;

	my $file = &getRoutingTableFile($table);
	return 0 if !-f $file;

	my $fh    = Config::Tiny->read( $file );

	return (exists $fh->{$route_id})? 1:0;
}




sub buildRouteCmd
{
	#~ ?????
}

sub createRoutingCustom
{
	my $table = shift;
	my $input = shift;

	my @params = ('id', 'raw', 'type');

	my $lock_rules = &getRoutingTableLock($table);
	&lockResource( $lock_rules, 'l' );

	$input->{raw} = &buildRouteCmd() if (!exists $input->{raw});

	my $err = &setRoute( 'add', $input->{raw} );

	if (!$err)
	{
		my $file = &getRoutingTableFile($table);
		&createFile($file) if (!-f $file);

		$input->{id} = &genRoutingId($file);
		$input->{type} = 'user';

		my $fh = Config::Tiny->read( $file );

		my $conf;
		foreach my $p (@params)
		{
			$conf->{$p} = $input->{$p};
		}

		if ( !$conf->{ id } )
		{
			&lockResource( $lock_rules, 'ud' );
			&zenlog( "Error getting an ID for the route", "error", "net" );
			return 1;
		}

		$fh->{ $conf->{ id } } = $conf;
		$fh->write( $file );

		&zenlog( "The routing entry '$conf->{id}' was created properly", "info", "net" );
		&zenlog( "Params: " . Dumper( $conf ), "debug2", "net" );
	}

	&lockResource( $lock_rules, 'ud' );
	return $err;
}


sub getRoutingTableConf
{
	my $table = shift;
	my $id = shift;

	my $file = &getRoutingTableFile($table);
	my $fh = Config::Tiny->read( $file );

	return $fh->{ $id };
}

sub delRoutingCustom
{
	my $table = shift;
	my $route_id = shift;

	my $conf = &getRoutingTableConf($table, $route_id);
	return 1 if( &setRoute('del', $conf->{raw}));

	my $file = &getRoutingTableFile($table);
	my $lock_f = &getRoutingTableLock($table);
	return &delRoutingConfById($route_id, $file, $lock_f);
}


sub setRoute
{
	my $action = shift;
	my $cmd_params = shift;
	my $ipv = shift //'';

	my $exist = &isRoute( $cmd_params, $ipv );

	if ( ($exist and $action eq 'add') or
		( !$exist and $action eq 'del' ) )
	{
		return 0;
	}

	$ipv = "-$ipv" if ($ipv ne '');
	my $cmd = "$ip_bin $ipv route $action $cmd_params";

	return &logAndRun($cmd);
}

# take data from config file and apply it to the system
sub applyRoutingCustom
{
	my $action = shift;
	my $table = shift;
	my $err = 0;

	my $list = &listRoutingTableCustom($table);

	foreach my $it (@{$list})
	{
		$err += &setRoute($action, $it->{raw});
	}

	return $err;
}

sub sanitazeRouteCmd
{
	my $cmd = shift;
	my $table = shift;

	&zenlog ("Sanitazing route cmd: $cmd","debug2","net");
	if ($cmd !~ /table/)
	{
		$cmd .= " table $table";
		&zenlog ("Adding table: $cmd","debug2","net");
	}
	if ($cmd =~ s/\s*ip\s+(-4|-6)?\s*route\s+\w+\s+//)
	{
		&zenlog ("Removing bin: $cmd","debug2","net");
	}

	return $cmd;
}


1;
