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
Function: genRoutingRulesId

	Generate an ID for routing rules.

Parameters:
	none - .

Returns:
	Integer - Returns an ID greater than 0 or 0 if there was an error

=cut

sub genRoutingRulesId
{
	my $max_index = 1024;
	my $id        = 0;
	my $fh        = Config::Tiny->read( $rules_conf );

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
		"src": "2.2.4.0",
		"srclen": 24,
		"table": "table_eth2.4"

Returns:
	Integer - 0 on success or other value on failure

=cut

sub createRoutingRulesConf
{
	my $conf = shift;

	require Zevenet::Net::Route;

	&createFile( $rules_conf ) if ( !-f $rules_conf );

	&lockResource( $lock_rules, 'l' );
	my $fh = Config::Tiny->read( $rules_conf );

	$conf->{ type } = "user";
	$conf->{ id }   = &genRoutingRulesId();

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

sub delRoutingRulesConf
{
	my $id = shift;

	&createFile( $rules_conf ) if ( !-f $rules_conf );

	&lockResource( $lock_rules, 'l' );
	my $fh = Config::Tiny->read( $rules_conf );

	if ( !exists $fh->{ $id } )
	{
		&lockResource( $lock_rules, 'ud' );
		&zenlog( "Error deleting the id '$id', it was not found", "error", "net" );
		return 1;
	}

	delete $fh->{ $id };
	$fh->write( $rules_conf );

	&zenlog( "The routing rule '$id' was deleted properly", "info", "net" );

	&lockResource( $lock_rules, 'ud' );
	return 0;
}

sub delRoutingRulesSys
{
	my $conf = shift;

	# check if it is running
	return 0 if !&checkRoutingRulesRunning( $conf );

	$conf->{ action } = 'del';
	my $err = &applyRoutingRules( $conf );

	return $err;
}

sub delRoutingRules
{
	my $id = shift;

	my $conf  = &getRoutingRulesConf( $id );
	my $error = &delRoutingRulesSys( $conf );
	$error = &delRoutingRulesConf( $id ) if ( !$error );

	return $error;
}

sub checkRoutingRulesRunning
{
	my $conf = shift;

	$conf->{ action } = 'list';
	my $cmd = &buildRoutingRuleCmd( $conf );
	my $out = `$cmd`;
	my $err = ( $out eq '' ) ? 0 : 1;

	&zenlog( "Checking if the rule '$conf->{id}' is applied in the system ($err)",
			 "debug", "net" );
	&zenlog( "checking ip rule cmd: $cmd", "debug2", "net" );
	&zenlog( "out: >$out<",                "debug2", "net" );

	return $err;
}

sub createRoutingRules
{
	my $conf = shift;

	$conf->{ priority } = &genRoutingRulesPrio('user') if ( !exists $conf->{ priority } );
	my $err = &applyRoutingRules( $conf );
	$err = &createRoutingRulesConf( $conf ) if ( !$err );

	return $err;
}

sub buildRoutingRuleCmd
{
	my $conf = shift;
	my $cmd  = "$ip_bin rule";

	# ip rule { add | del } [ not ] [ from IP/NETMASK ] TABLE_ID
	$cmd .= " $conf->{action}";
	$cmd .= " priority $conf->{priority}" if ( exists $conf->{priority} and $conf->{priority} =~ /\d/ );
	$cmd .= " not" if ( exists $conf->{ not } and $conf->{ not } eq 'true' );
	$cmd .= " from $conf->{src}";
	$cmd .= "/$conf->{srclen}"
	  if ( exists $conf->{ srclen } and $conf->{ srclen } );
	$cmd .= " lookup $conf->{table}";

	return $cmd;
}

sub applyRoutingRules
{
	my $conf = shift;
	my $err  = 0;

	$conf->{ action } = 'add' if ( !exists $conf->{ action } );

	my $cmd = &buildRoutingRuleCmd( $conf );
	$err = &logAndRun( $cmd );

	if ( $err )
	{
		if ( exists $conf->{ id } )
		{
			&zenlog( "The routing rule '$conf->{id}' could not be applied", "error",
					 "net" );
		}
		else
		{
			&zenlog( "The rule could not be applied", "error", "net" );
		}
	}

	return $err;
}

sub applyRoutingAllRules
{
	my $err = 0;

	my $rules = &listRoutingConfRules();
	foreach my $r ( @{ $rules } )
	{
		$err = &applyRoutingRules( $r );
	}

	return $err;
}

sub initRoutingModule
{
	mkdir $routes_dir if ( !-d $routes_dir );
	&createFile( $rules_conf ) if ( !-f $rules_conf );

	&applyRoutingAllRules();
}

1;
