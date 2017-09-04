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
use Zevenet::IPDS::DoS::Core;

sub getDOSInitialParams
{
	my $rule = shift;

	# get ssh port
	require Zevenet::System::SSH;

	my $sshconf = &getSsh();
	my $port    = $sshconf->{ 'port' };

	my %initial = (
		'bogustcpflags' => { 'farms' => '', 'type'        => 'farm' },
		'limitconns'    => { 'farms' => '', 'limit_conns' => 20, 'type' => 'farm' },
		'limitrst' =>
		  { 'farms' => '', 'limit' => 10, 'limit_burst' => 5, 'type' => 'farm' },
		'limitsec' =>
		  { 'farms' => '', 'limit' => 20, 'limit_burst' => 15, 'type' => 'farm' },
		'dropicmp' => { 'status' => 'down', 'type' => 'system', 'name' => 'drop_icmp' },
		'sshbruteforce' => {
							 'status' => 'down',
							 'hits'   => 10,
							 'port'   => $port,
							 'time'   => 60,
							 'type'   => 'system',
							 'name'   => 'ssh_brute_force'
		},

		#					'NEWNOSYN' => { 'farms' => '' },
		#					'DROPFRAGMENTS' => { 'farms'  => '' },
		#					'INVALID'       => { 'farms'  => '' },
		#					'SYNPROXY'     => { 'farms' => '', 'mss' => 1460, 'scale' => 7 },
		#					'SYNWITHMSS'   => { 'farms' => '' },
		#					'PORTSCANNING' => {
		#										'farms'    => '',
		#										'portScan' => 15,
		#										'blTime'   => 500,
		#										'time'     => 100,
		#										'hits'     => 3,
		#					},
	);

	return $initial{ $rule };
}

sub setDOSCreateFileConf
{
	my $confFile   = &getGlobalConfiguration( 'dosConf' );
	my $dosConfDir = &getGlobalConfiguration( 'dosConfDir' );
	my $output;

	return 0 if ( -e $confFile );

	# create dos directory if it doesn't exist
	if ( !-d $dosConfDir )
	{
		$output = system ( &getGlobalConfiguration( 'mkdir' ) . " -p $dosConfDir" );
		&zenlog( "Created ipds configuration directory: $dosConfDir" );
	}

	# create file conf if doesn't exist
	if ( !$output )
	{
		&zenlog( "Created dos configuration directory: $dosConfDir" );
		$output = system ( &getGlobalConfiguration( 'touch' ) . " $confFile" );
		if ( $output )
		{
			&zenlog( "Error, creating dos configuration directory: $dosConfDir" );
		}
		else
		{
			&zenlog( "Created dos configuration file: $confFile" );
		}
	}

	if ( !$output )
	{
		#~ $output = &createDOSRule( 'drop_icmp', 'dropicmp' )		# Next version
		#~ if ( ! &getDOSExists( 'drop_icmp' ) );
		$output = &createDOSRule( 'ssh_brute_force', 'sshbruteforce' )
		  if ( !&getDOSExists( 'ssh_brute_force' ) );
	}
	else
	{
		&zenlog( "Error, creating dos configuration file: $confFile" );
	}

	return $output;
}

# &setDOSParam ($name,$param,$value)
sub setDOSParam
{
	my $name  = shift;
	my $param = shift;
	my $value = shift;

	require Zevenet::IPDS::DoS::Actions;
	
	#Stop related rules
	&runDOSStopByRule( $name );

	my $confFile   = &getGlobalConfiguration( 'dosConf' );
	my $fileHandle = Config::Tiny->read( $confFile );
	$fileHandle = Config::Tiny->read( $confFile );

	$fileHandle->{ $name }->{ $param } = $value;
	$fileHandle->write( $confFile );

	&runDOSStartByRule( $name );
}

# key is the rule identifier
# &createDOSRule( $rule, $rule );
sub createDOSRule
{
	my $ruleName = shift;
	my $rule     = shift;
	my $params;

	my $confFile   = &getGlobalConfiguration( 'dosConf' );
	my $fileHandle = Config::Tiny->read( $confFile );
	$fileHandle = Config::Tiny->read( $confFile );

	if ( exists $fileHandle->{ $ruleName } )
	{
		&zenlog( "$ruleName rule already exists." );
		return -1;
	}
	$params = &getDOSInitialParams( $rule );

	if ( !$params )
	{
		&zenlog( "Error, saving $ruleName rule." );
		return -2;
	}

	$fileHandle->{ $ruleName } = $params;
	$fileHandle->{ $ruleName }->{ 'rule' } = $rule;
	if ( $params->{ 'type' } eq 'farm' )
	{
		$fileHandle->{ $ruleName }->{ 'rule' } = $rule;
		$fileHandle->{ $ruleName }->{ 'name' } = $ruleName;
	}
	$fileHandle->write( $confFile );
	&zenlog( "$ruleName rule created successful." );

	return 0;
}

sub deleteDOSRule
{
	my $name = shift;

	my $confFile   = &getGlobalConfiguration( 'dosConf' );
	my $fileHandle = Config::Tiny->read( $confFile );
	$fileHandle = Config::Tiny->read( $confFile );

	if ( !exists $fileHandle->{ $name } )
	{
		&zenlog( "$name rule doesn't exist." );
		return -1;
	}

	delete $fileHandle->{ $name };
	$fileHandle->write( $confFile );

	return 0;
}

1;
