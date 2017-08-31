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

# The goal of this file is keep the needed functions to apply start, stop or
# restart actions to blacklist rules

use strict;

use Zevenet::IPDS::Blacklist::Runtime;
use Zevenet::Farm::Base;

my $blacklistsPath = &getGlobalConfiguration( 'blacklistsPath' );
my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );

actions:
actions_module:

=begin nd
Function: runBLStartModule

	Enable all blacklists rules

Parameters: None.

Returns: None.
=cut

sub runBLStartModule
{
	my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
	my $ipset          = &getGlobalConfiguration( 'ipset' );
	my $touch          = &getGlobalConfiguration( 'touch' );
	my $blacklistsPath = &getGlobalConfiguration( 'blacklistsPath' );

	if ( !-d $blacklistsPath )
	{
		system ( &getGlobalConfiguration( 'mkdir' ) . " -p $blacklistsPath" );
		&zenlog( "Created $blacklistsPath directory." );
	}

	# create list config if doesn't exist
	if ( !-e $blacklistsConf )
	{
		system ( "$touch $blacklistsConf" );
		&zenlog( "Created $blacklistsConf file." );
	}

	# load preload lists
	#~ &setBLAddPreloadLists();

	my $allLists = Config::Tiny->read( $blacklistsConf );

	# load lists
	foreach my $list ( keys %{ $allLists } )
	{
		my $farms = &getBLParam( $list, "farms" );
		next if ( !$farms );

		my @farms = @{ $farms };

		# create cmd  for all farms where are applied the list and  they are running
		foreach my $farm ( @farms )
		{
			if ( &getFarmBootStatus( $farm ) eq 'up' )
			{
				if ( &getBLStatus( $list ) eq "down" )
				{
					# load in memory the list
					&setBLRunList( $list );
				}
				&zenlog( "Creating rules for the list $list and farm $farm." );
				&setBLCreateRule( $farm, $list );
			}
		}
	}
}

=begin nd
Function: runBLStopModule

	Disable all blacklists rules

Parameters:

Returns:

=cut

sub runBLStopModule
{
	my $error;

	foreach my $typelist ( 'blacklist', 'whitelist' )
	{
		my $chain = &getIPDSChain( $typelist );
		my $cmd   = &getGlobalConfiguration( 'iptables' ) . " --table raw -F $chain";
		&iptSystem( $cmd );
	}

	# destroy lists
	my $ipset = &getGlobalConfiguration( 'ipset' );
	my @lists = `$ipset list -name`;
	foreach my $rule ( @lists )
	{
		chomp ($rule);
		&setBLDestroyList( $rule );
	}

	return $error;
}

=begin nd
Function: runBLRestartModule

	Stop the module	

Parameters:
				
Returns:

=cut

sub runBLRestartModule
{
	&runBLStopModule;
	&runBLStartModule;
}

=begin nd
Function: runBLStartByRule

	Start the runtime of a blacklist rule and link with all farm that are using this rule.

Parameters:
	Rule - Rule name
				
Returns:
	integer - 0 on success or other value on failure
	
=cut

sub runBLStartByRule
{
	my ( $ruleName ) = @_;
	my $error = 0;
	my @farms = @{ &getBLParam( $ruleName, 'farms' ) };

	foreach my $farmName ( @farms )
	{
		if ( &runBLStart( $ruleName, $farmName ) != 0 )
		{
			&zenlog( "Error running the rule $ruleName in the farm $farmName." );
		}
	}

	return $error;
}

=begin nd
Function: runBLStopByRule

	Stop the runtime of a blacklist rule  and unlink with all farm that are using this rule.

Parameters:
	Rule - Rule name
				
Returns:
	integer - 0 on success or other value on failure
	
=cut

sub runBLStopByRule
{
	my ( $ruleName ) = @_;
	my $error = 0;

	my $ipset = &getGlobalConfiguration( 'ipset' );

	return if ( &getBLStatus() eq 'down' );

	foreach my $farmName ( @{ &getBLParam( $ruleName, 'farms' ) } )
	{
		if ( &runBLStop( $ruleName, $farmName ) != 0 )
		{
			&zenlog( "Error stopping the rule $ruleName in the farm $farmName." );
		}
	}

	return $error;
}

=begin nd
Function: runBLRestartByRule

	Restart the runtime of a blacklist rule.
	It is useful when a the rule will be modified.

Parameters:
	Rule - Rule name
				
Returns:
	integer - 0 on success or other value on failure
	
=cut

sub runBLRestartByRule
{
	my ( $rule ) = @_;

	my $error = &runBLStopByRule( $rule );

	if ( !$error )
	{
		$error = &runBLStartByRule( $rule );
	}

	return $error;
}

=begin nd
Function: runBLStart

	Start the runtime of a blacklist rule and link with a farm that are using this rule.

Parameters:
	Rule - Rule name
	Farmanme - Farm name
				
Returns:
	integer - 0 on success or other value on failure
	
=cut

sub runBLStart
{
	my ( $list, $farm ) = @_;
	my $error;

	# the rule is already running
	if ( grep ( / BL_$farm /, @{ &getBLRunningRules() } ) )
	{
		return $error;
	}

	if ( &getFarmBootStatus( $farm ) eq 'up' )
	{
		if ( &getBLStatus( $list ) eq "down" )
		{
			# load in memory the list
			$error = &setBLRunList( $list );
		}
		if ( !$error )
		{
			&zenlog( "Creating rules for the list $list and farm $farm." );
			$error = &setBLCreateRule( $farm, $list );
		}
	}

	return $error;
}

=begin nd
Function: runBLStop

	Stop the runtime of a blacklist rule and link with a farm that are using this rule.

Parameters:
	Rule - Rule name
	Farmname - Farm name
				
Returns:
	integer - 0 on success or other value on failure
	
=cut

sub runBLStop
{
	my ( $rule, $farm ) = @_;

	&setBLDeleteRule( $farm, $rule );

	if ( !&getBLListNoUsed( $rule ) )
	{
		if ( &getBLStatus( $rule ) eq 'up' )
		{
			&setBLDestroyList( $rule );
		}
	}

	#~ return $error;
}

=begin nd
Function: runBLRestart

	Restart the runtime of a blacklist rule with a farm.

Parameters:
	Rule - Rule name
	Farmname - Farm name
				
Returns:
	integer - 0 on success or other value on failure
	
=cut

sub runBLrestart
{
	my ( $rule, $farm ) = @_;

	my $error = &runBLStop( $rule, $farm );

	if ( !$error )
	{
		$error = &runBLStart( $rule, $farm );
	}

	return $error;
}

1;
