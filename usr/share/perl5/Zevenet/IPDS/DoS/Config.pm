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
use warnings;

use Config::Tiny;
include 'Zevenet::IPDS::DoS::Core';

=begin nd
Function: getDOSInitialParams

	Get a struct with the parameters of a DoS rule

Parameters:
	rule	 - Rule name

Returns:
	Hash ref - Parameters for the rule

=cut

sub getDOSInitialParams
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $rule = shift;

	# get ssh port
	include 'Zevenet::System::SSH';

	my %initial = (
		 'bogustcpflags' => { 'farms' => '', 'status' => 'down', 'type' => 'farm' },
		 'limitconns' =>
		   { 'farms' => '', 'status' => 'down', 'limit_conns' => 20, 'type' => 'farm' },
		 'limitrst' => {
						 'farms'       => '',
						 'limit'       => 10,
						 'status'      => 'down',
						 'limit_burst' => 5,
						 'type'        => 'farm'
		 },
		 'limitsec' => {
						 'farms'       => '',
						 'limit'       => 20,
						 'status'      => 'down',
						 'limit_burst' => 15,
						 'type'        => 'farm'
		 },
	);

	return $initial{ $rule };
}

=begin nd
Function: initDOSModule

	Create configuration files and run all needed commands requested to DoS module

Parameters:
	None - .

Returns:
	None - .

=cut

sub initDOSModule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $confFile   = &getGlobalConfiguration( 'dosConf' );
	my $dosConfDir = &getGlobalConfiguration( 'dosConfDir' );
	my $output;

	if ( !-e $confFile )
	{
		# create dos directory if it doesn't exist
		if ( !-d $dosConfDir )
		{
			my $mkdir = &getGlobalConfiguration( 'mkdir' );
			$output = &logAndRun( "$mkdir -p $dosConfDir" );
			&zenlog( "Created ipds configuration directory: $dosConfDir", "info", "IPDS" );
		}

		# create file conf if doesn't exist
		if ( !$output )
		{
			my $touch = &getGlobalConfiguration( 'touch' );
			&zenlog( "Created DoS configuration directory: $dosConfDir", "info", "IPDS" );
			$output = &logAndRun( "$touch $confFile" );
			if ( $output )
			{
				&zenlog( "Error, creating DoS configuration directory: $dosConfDir",
						 "error", "IPDS" );
			}
			else
			{
				&zenlog( "Created dos configuration file: $confFile", "info", "IPDS" );
			}
		}
	}

	return $output;
}

=begin nd
Function: getDOSInitialParams

	Change a value in conf file

Parameters:
	rule	 - Rule name
	parameter	 - Parameter to change
	value	 - Value for the parameter

Returns:
	none - .

=cut

sub setDOSParam
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $name  = shift;
	my $param = shift;
	my $value = shift;

	include 'Zevenet::IPDS::DoS::Actions';

	#Stop related rules
	my $status = &getDOSStatusRule( $name );
	&runDOSStopByRule( $name )
	  if (     ( $param eq "status" )
		   and ( $value eq "down" )
		   and ( $status eq "up" ) );

	my $confFile   = &getGlobalConfiguration( 'dosConf' );
	my $lock       = &setDOSLockConfigFile();
	my $fileHandle = Config::Tiny->read( $confFile );
	$fileHandle = Config::Tiny->read( $confFile );

	if ( 'farms-add' eq $param )
	{
		if ( $fileHandle->{ $name }->{ 'farms' } !~ /(^| )$value( |$)/ )
		{
			my $farmList = $fileHandle->{ $name }->{ 'farms' };
			$fileHandle->{ $name }->{ 'farms' } = "$farmList $value";
		}
	}
	elsif ( 'farms-del' eq $param )
	{
		$fileHandle->{ $name }->{ 'farms' } =~ s/(^| )$value( |$)/ /;
	}
	else
	{
		$fileHandle->{ $name }->{ $param } = $value;
	}

	$fileHandle->write( $confFile );
	&setDOSUnlockConfigFile( $lock );

	&runDOSStartByRule( $name )
	  if ( !( ( $param eq "status" ) and ( $value eq "down" ) ) );
}

=begin nd
Function: getDOSInitialParams

	Create a DoS rule in the config file

Parameters:
	name	 - Rule name
	rule	 - key that identify the DoS rule type

Returns:
	Integer - Error code. 0 on success or other value on failure

=cut

sub createDOSRule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $ruleName = shift;
	my $rule     = shift;
	my $params;

	my $confFile   = &getGlobalConfiguration( 'dosConf' );
	my $fileHandle = Config::Tiny->read( $confFile );

	$params = &getDOSInitialParams( $rule );
	if ( !$params )
	{
		&zenlog( "Error, saving $ruleName rule.", "error", "IPDS" );
		return -2;
	}

	my $lock = &setDOSLockConfigFile();
	$fileHandle = Config::Tiny->read( $confFile );

	if ( exists $fileHandle->{ $ruleName } )
	{
		close $lock;
		&zenlog( "$ruleName rule already exists.", "warning", "IPDS" );
		return -1;
	}

	$fileHandle->{ $ruleName } = $params;
	$fileHandle->{ $ruleName }->{ 'rule' } = $rule;
	if ( $params->{ 'type' } eq 'farm' )
	{
		$fileHandle->{ $ruleName }->{ 'rule' } = $rule;
		$fileHandle->{ $ruleName }->{ 'name' } = $ruleName;
	}
	$fileHandle->write( $confFile );
	close $lock;

	&zenlog( "$ruleName rule created successfully.", "info", "IPDS" );
	return 0;
}

=begin nd
Function: deleteDOSRule

	Delete a DoS rule from the config file

Parameters:
	rule	 - Rule name

Returns:
	none - .

=cut

sub deleteDOSRule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $name = shift;

	my $confFile = &getGlobalConfiguration( 'dosConf' );

	my $lock       = setDOSLockConfigFile();
	my $fileHandle = Config::Tiny->read( $confFile );
	$fileHandle = Config::Tiny->read( $confFile );

	if ( !exists $fileHandle->{ $name } )
	{
		close $lock;
		&zenlog( "$name rule doesn't exist.", "warning", "IPDS" );
		return -1;
	}

	delete $fileHandle->{ $name };
	$fileHandle->write( $confFile );
	close $lock;

	return 0;
}

1;

