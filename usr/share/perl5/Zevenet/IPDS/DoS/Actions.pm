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
use Tie::File;

use Zevenet::Core;
use Zevenet::IPDS::Core;
use Zevenet::Farm;



actions:
actions_module:

=begin nd
        Function: runDOSStartModule

        Boot all DoS rules-

        Parameters:
				
        Returns:
				== 0	- Successful
             != 0	- Number of rules didn't boot

=cut

sub runDOSStartModule
{
	require Zevenet::IPDS::DoS::DoS;

	my $confFile = &getGlobalConfiguration( 'dosConf' );
	my $output;

	&zenlog( "Booting dos system... " );
	&setDOSCreateFileConf();

	if ( -e $confFile )
	{		
		my $fileHandle = Config::Tiny->read( $confFile );
		foreach my $ruleName ( keys %{ $fileHandle } )
		{
			if ( $fileHandle->{ $ruleName }->{ 'type' } eq 'farm' )
			{
				my $farmList = $fileHandle->{ $ruleName }->{ 'farms' };
				my @farms = split ( ' ', $farmList );
				foreach my $farmName ( @farms )
				{
					# run rules of running farms
					if ( &getFarmBootStatus( $farmName ) eq 'up' )
					{
						if ( &setDOSRunRule( $ruleName, $farmName ) != 0 )
						{
							&zenlog ("Error running the rule $ruleName in the farm $farmName.");
						}
					}
				}
			}
			elsif ( $fileHandle->{ $ruleName }->{ 'type' } eq 'system' )
			{
				if ( $fileHandle->{ $ruleName }->{ 'status' } eq "up" )
				{
					if ( &setDOSRunRule( $ruleName, 'status' ) != 0 )
					{
						&zenlog ("Error, running the rule $ruleName.");
					}
				}
			}
		}
	}
	
	# This block is a bugfix. When ssh_brute_force rule doesn't show the port
	if ( ! &setDOSParam ( 'ssh_brute_force', 'port' ) )
	{
		my $sshconf = &getSsh();
		my $port    = $sshconf->{ 'port' };
		&setDOSParam ( 'ssh_brute_force', 'port', $port);
	}
	
	return $output;
}

=begin nd
        Function: runDOStopModule

        Stop all DoS rules

        Parameters:
				
        Returns:
			== 0	- Successful
            != 0	- Number of rules didn't Stop

=cut

sub runDOStopModule
{
	my $output   = 0;
	my $confFile = &getGlobalConfiguration( 'dosConf' );

	if ( -e $confFile )
	{
		my $fileHandle = Config::Tiny->read( $confFile );
		foreach my $rule ( keys %{ $fileHandle } )
		{
			# Applied to farm
			if ( $fileHandle->{ $rule }->{ 'type' } eq "farm" )
			{
				if ( $fileHandle->{ $rule }->{ 'farms' } )
				{
					my $farmList = $fileHandle->{ $rule }->{ 'farms' };
					my @farms = split ( ' ', $farmList );
					foreach my $farmName ( @farms )
					{
						$output++ if ( &setDOSStopRule( $rule, $farmName ) != 0 );
					}
				}
			}

			# Applied to balancer
			elsif ( $fileHandle->{ $rule }->{ 'type' } eq 'system' )
			{
				if ( $fileHandle->{ $rule }->{ 'status' } eq 'up' )
				{
					$output++ if ( &setDOSStopRule( $rule ) != 0 );
				}
			}
		}
	}
	return $output;
}


=begin nd
Function: runDOSRestartModule

	Stop the module	

Parameters:
				
Returns:

=cut

# this function has to remove the tmp directory /tmp/IPDS/<module> and stop all rules in /tmp/IPDS/<module> directory
sub runDOSRestartModule
{
	&runDOStopModule;
	&runDOStartModule;
}

actions_by_rule:

=begin nd
Function: runDOSStartByRule

	Start the runtime of a DOS rule and link with all farm that are using this rule.

Parameters:
	Rule - Rule name
				
Returns:
	integer - 0 on success or other value on failure
	
=cut

sub runDOSStartByRule
{
	my ( $ruleName ) = @_;
	my $error=0;
	my @farms = @{ &getDOSParam( $ruleName, 'farms' ) };
	
	foreach my $farmName ( @farms )
	{
		# run rules of running farms
		if ( &getFarmBootStatus( $farmName ) eq 'up' )
		{
			if ( &setDOSRunRule( $ruleName, $farmName ) != 0 )
			{
				&zenlog ("Error running the rule $ruleName in the farm $farmName.");
			}
		}
	}
	
	return $error;
}

=begin nd
Function: runDOSStopByRule

	Stop the runtime of a DOS rule  and unlink with all farm that are using this rule.

Parameters:
	Rule - Rule name
				
Returns:
	integer - 0 on success or other value on failure
	
=cut

sub runDOSStopByRule
{
	my ( $ruleName ) = @_;
	my $error=0;

	return if ( &getDOSStatusRule() eq 'down' );
	
	foreach my $farmName ( @{ &getDOSParam( $ruleName, 'farms' ) } )
	{
		if ( &setDOSStopRule( $ruleName, $farmName ) != 0 )
		{
			&zenlog ("Error stopping the rule $ruleName in the farm $farmName.");
		}
	}
	
	return $error;
}

=begin nd
Function: runDOSRestartByRule

	Restart the runtime of a DOS rule.
	It is useful when a the rule will be modified.

Parameters:
	Rule - Rule name
				
Returns:
	integer - 0 on success or other value on failure
	
=cut

sub runDOSRestartByRule
{
	my ( $rule ) = @_;

	my $error = &runDOSStopByRule( $rule );

	if ( !$error )
	{
		$error = &runDOSStartByRule( $rule );
	}

	return $error;
}

=begin nd
Function: runDOSStart

	Start the runtime of a DOS rule and link with a farm that are using this rule.

Parameters:
	Rule - Rule name
	Farmanme - Farm name
				
Returns:
	integer - 0 on success or other value on failure
	
=cut

sub runDOSStart
{
	my ( $rule, $farm ) = @_;
	my $error=&setDOSRunRule( $rule, $farm );
	return $error;
}

=begin nd
Function: runDOSStop

	Stop the runtime of a DOS rule and link with a farm that are using this rule.

Parameters:
	Rule - Rule name
	Farmname - Farm name
				
Returns:
	integer - 0 on success or other value on failure
	
=cut

sub runDOSStop
{
	my ( $rule, $farm ) = @_;
	my $error=&setDOSStopRule( $rule, $farm );
	return $error;
}

=begin nd
Function: runDOSRestart

	Restart the runtime of a DOS rule with a farm.

Parameters:
	Rule - Rule name
	Farmname - Farm name
				
Returns:
	integer - 0 on success or other value on failure
	
=cut

sub runDOSrestart
{
	my ( $rule, $farm ) = @_;

	my $error = &runDOSStop( $rule, $farm );

	if ( !$error )
	{
		$error = &runDOSStart( $rule, $farm );
	}

	return $error;
}

1;
