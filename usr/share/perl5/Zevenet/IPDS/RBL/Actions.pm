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
use Tie::File;

use Zevenet::Core;
use Zevenet::Debug;
use Zevenet::IPDS::Core;

# rbl configuration path
my $rblPath = &getGlobalConfiguration( 'configdir' ) . "/ipds/rbl";
my $rblConfigFile = "$rblPath/rbl.conf";
my $preloadedDomainsFile = "$rblPath/preloaded_domains.conf";
my $userDomainsFile = "$rblPath/user_domains.conf";


actions:
actions_module:

=begin nd
Function: runRBLStartModule

	Boot the RBL module

Parameters:
				
Returns:

=cut

# this function has to create the tmp directory /tmp/IPDS/<module> and start all rules applied to UP farms.
# when start a module load the blocked sources from logs
sub runRBLStartModule
{
	require Zevenet::IPDS::RBL::RBL;

	# create config directory if it doesn't exist and config file
	my $error = &setRBLCreateDirectory();

	# Run all rules
	foreach my $rule ( &getRBLRuleList() )
	{
		&runRBLStartByRule( $rule );
	}

}

=begin nd
Function: runRBLStopModule

	Stop the module

Parameters:
				
Returns:

=cut

# this function has to remove the tmp directory /tmp/IPDS/<module> and stop all rules in /tmp/IPDS/<module> directory
sub runRBLStopModule
{

	# stop all rules
	foreach my $rule ( &getRBLRuleList() )
	{
		&runRBLStopByRule( $rule );
	}

}

=begin nd
Function: runRBLRestartModule

	Restart the module

Parameters:
				
Returns:

=cut

# this function has to remove the tmp directory /tmp/IPDS/<module> and stop all rules in /tmp/IPDS/<module> directory
sub runRBLRestartModule
{
	# Get RBL rules
	foreach my $rule ( &getRBLRuleList() )
	{
		&runRBLStopByRule( $rule );
		&runRBLStartByRule( $rule );
	}
}

actions_by_rule:

=begin nd
Function: runRBLStartByRule

	Start the runtime of a RBL rule and link with all farm that are using this rule.

Parameters:
	Rule - Rule name
				
Returns:
	integer - 0 on success or other value on failure
	
=cut

sub runRBLStartByRule
{
	my ( $rule ) = @_;
	my $error=0;
	my @farms = @{ &getRBLObjectRuleParam( $rule, 'farms' ) };
	
	if ( !@farms )
	{
		#~ &zenlog( "RBL rule \"$rule\" has not any farm linked" );
		return -1;
	}
	
	my $flag=0;
	foreach my $farmname ( @farms )
	{
		&runRBLStart( $rule, $farmname );
	}

	return $error;
}

=begin nd
Function: runRBLStopByRule

	Stop the runtime of a RBL rule  and unlink with all farm that are using this rule.

Parameters:
	Rule - Rule name
				
Returns:
	integer - 0 on success or other value on failure
	
=cut

sub runRBLStopByRule
{
	my ( $rule ) = @_;
	my $error=0;

	# remove all iptables rules
	foreach my $farmname ( @{ &getRBLObjectRuleParam( $rule, 'farms' ) } )
	{
		$error = &runRBLStop( $rule, $farmname );
	}

	return $error;
}

=begin nd
Function: runRBLRestartByRule

	Restart the runtime of a RBL rule.
	It is useful when a the rule will be modified.

Parameters:
	Rule - Rule name
				
Returns:
	integer - 0 on success or other value on failure
	
=cut

sub runRBLRestartByRule
{
	my ( $rule ) = @_;

	my $error = &runRBLStopByRule( $rule );

	if ( !$error )
	{
		$error = &runRBLStartByRule( $rule );
	}

	return $error;
}

=begin nd
Function: runRBLStart

	Start the runtime of a RBL rule and link with a farm that are using this rule.

Parameters:
	Rule - Rule name
	Farmanme - Farm name
				
Returns:
	integer - 0 on success or other value on failure
	
=cut

sub runRBLStart
{
	my ( $rule, $farm ) = @_;
	my $error=0;

	# to start a rule the farm has to be up
	if ( &getFarmBootStatus( $farm ) ne 'up' )
	{
		return -1;
	}
	
	# not run if the farm is not applied to the rule
	if ( !grep ( /^$farm$/, @{ &getRBLObjectRuleParam( $rule, 'farms' ) } ) )
	{
		return -1;
	}
		
	# to start a RBL rule it is necessary that the rule has almost one domain
	if ( !@{ &getRBLObjectRuleParam($rule, 'domains') } )
	{
		#~ &zenlog ( "RBL rule, $rule, was not started because doesn't have any domain." );
		return -1;
	}
	
	# if the process is not running, start it
	if ( &getRBLStatusRule( $rule ) eq "down" )
	{
		$error = &runRBLStartPacketbl( $rule );
	}
	
	# if all is success link with the farm
	if ( ! $error )
	{
		$error = &runRBLIptablesRule( $rule, $farm, 'insert' );
	}
	
	return $error;
}

=begin nd
Function: runRBLStop

	Stop the runtime of a RBL rule and link with a farm that are using this rule.

Parameters:
	Rule - Rule name
	Farmname - Farm name
				
Returns:
	integer - 0 on success or other value on failure
	
=cut

sub runRBLStop
{
	my ( $rule, $farm ) = @_;
	my $error=0;

	# remove all iptables rules
	if ( &getFarmStatus( $farm ) eq 'up' )
	{
		&runRBLIptablesRule( $rule, $farm, 'delete' );
	}

	# if are not another farm using this rule, the rule is stopped
	if ( !&getRBLRunningFarmList( $rule ) )
	{
		&runRBLStopPacketbl( $rule );
	}

	return $error;
}

=begin nd
Function: runRBLRestart

	Restart the runtime of a RBL rule with a farm.

Parameters:
	Rule - Rule name
	Farmname - Farm name
				
Returns:
	integer - 0 on success or other value on failure
	
=cut

sub runRBLRestart
{
	my ( $rule, $farm ) = @_;

	my $error = &runRBLStop( $rule, $farm );

	if ( !$error )
	{
		$error = &runRBLStart( $rule, $farm );
	}

	return $error;
}

1;
