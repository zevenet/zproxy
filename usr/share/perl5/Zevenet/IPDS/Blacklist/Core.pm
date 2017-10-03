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

# The goal of this file is to keep the needed functions to get information about
# the blacklist process: configuration, runtime...

use strict;
use Config::Tiny;
use Zevenet::Core;
use Zevenet::Debug;

my $blacklistsPath = &getGlobalConfiguration( 'blacklistsPath' );
my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );

=begin nd
Function: getBLExists

	Get if a list exists o all available lists

Parameters:

	listName	-	return 0 if list exists
	no param	-	return a ref array of all available lists

Returns:

	1   - list exists
	0  - list doesn't exist
=cut

sub getBLExists
{
	my $listName = shift;

	my $output         = 0;
	my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
	my $fileHandle     = Config::Tiny->read( $blacklistsConf );

	if ( $listName )
	{
		$output = 1 if ( exists $fileHandle->{ $listName } );
	}

	return $output;
}

#  &getBLIpsetStatus ( $listName );
sub getBLIpsetStatus
{
	my $listName = shift;

	my $ipset  = &getGlobalConfiguration( 'ipset' );
	my $output = system ( "$ipset list $listName -name >/dev/null 2>&1" );

	if ( $output )
	{
		$output = 'down';
	}
	else
	{
		$output = 'up';
	}

	return $output;
}

#  &getBLStatus ( $listName );
sub getBLStatus
{
	my $listName = shift;

	my $output = &getBLParam( $listName, 'status' );
	$output = "down" if ( !$output );

	return $output;
}

# return 0 if the list has not iptable rules applied
#  else return the number of farms that are using the list
# $lists = &getListNoUsed ();
sub getBLListNoUsed
{
	my $blacklist = shift;
	my $ipset     = &getGlobalConfiguration( 'ipset' );

	#~ require Zevenet::Validate;
	my $matchs = 0;
	my @cmd    = `$ipset -L -terse $blacklist 2>/dev/null`;

	foreach my $line ( @cmd )
	{
		if ( $line =~ /References: (\d+)/ )
		{
			$matchs = $1;
			last;
		}
	}

	return $matchs;
}

=begin nd
Function: getBLParam

	Get list config

Parameters:

	name	- section name
	key		- field to modificate
		- name	-> list name
		- farm	-> add or delete a asociated farm
		- url	-> modificate url ( only remote lists )
		- update_status-> modificate list status ( only remote lists )
		- list  -> modificate ip list ( only local lists )

	value	- value for the field

Returns:

	0	- successful
	!=0	- error

=cut

sub getBLParam
{
	my ( $listName, $key ) = @_;

	my $output;
	my $fileHandle;

	my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
	$fileHandle = Config::Tiny->read( $blacklistsConf );
	my @aux = ();

	if ( !$key )
	{
		$output               = $fileHandle->{ $listName };
		$output->{ 'name' }   = $listName;
		$output->{ 'source' } = &getBLIpList( $listName );
		@aux                  = split ( ' ', $fileHandle->{ $listName }->{ 'farms' } );
		$output->{ 'farms' }  = \@aux;
	}
	elsif ( $key eq 'source' )
	{
		$output = &getBLIpList( $listName );
	}
	elsif ( $key eq 'farms' )
	{
		my $farm_string = $fileHandle->{ $listName }->{ $key };
		if ( $fileHandle->{ $listName }->{ $key } )
		{
			@aux = split ( ' ', $farm_string );
		}
		$output = \@aux;
	}
	else
	{
		$output = $fileHandle->{ $listName }->{ $key };
	}

	return $output;
}

=begin nd
Function: getBLFarmApplied

	Return a list with all rules where the farm is applied

Parameters:
	Farmname -  Farm name
				
Returns:
	Array - list of BL rules
	
=cut

sub getBLFarmApplied
{
	my $farmname = shift;

	my @rules;

	foreach my $rule ( @{ &getBLRuleList() } )
	{
		if ( grep ( /^$farmname$/, @{ &getBLParam( $rule, 'farms' ) } ) )
		{
			push @rules, $rule;
		}
	}
	return @rules;
}

=begin nd
Function: getBLRunningRules

	List all running BL rules.

Parameters: None.

Returns:

	@array  - BL applied rules
	== 0	- error

=cut

sub getBLRunningRules
{
	require Zevenet::IPDS::Core;

	my @blRules;

	# look for blacklist rules
	my $blacklist_chain = &getIPDSChain( "blacklist" );
	my @rules           = &getIptListV4( 'raw', $blacklist_chain );
	my @blRules         = grep ( /BL_/, @rules );

	# look for whitelist rules
	$blacklist_chain = &getIPDSChain( "whitelist" );
	@rules           = &getIptListV4( 'raw', $blacklist_chain );
	@blRules         = grep ( /BL_/, @rules );

	return \@blRules;
}

=begin nd
Function: getBLRuleList

	Get an array with all BL rule names

Parameters:

Returns:
	Array - BL name list

=cut

sub getBLRuleList
{
	require Config::Tiny;
	my $fileHandle = Config::Tiny->read( $blacklistsConf );

	return keys %{ $fileHandle };
}

# &getBLlastUptdate ( list );
sub getBLlastUptdate
{
	my $listName = shift;

	my $date;
	my $listFile = &getGlobalConfiguration( 'blacklistsPath' ) . "/$listName.txt";
	my $stat     = &getGlobalConfiguration( 'stat' );

	# only update remote lists
	return -1 if ( &getBLParam( $listName, 'type' ) eq 'local' );

	# comand
	my $outCmd = `$stat -c %y $listFile`;

	# 2016-12-22 10:21:07.000000000 -0500
	if ( $outCmd =~ /^(.+)\./ )
	{
		$date = $1;
	}
	else
	{
		$date = -2;
	}

	return $date;
}

sub getBLzapi
{
	my $listName = shift;

	my %listHash;
	my @ipList;
	my $index = 0;

	foreach my $source ( @{ &getBLParam( $listName, 'source' ) } )
	{
		push @ipList, { id => $index++, source => $source };
	}

	%listHash = %{ &getBLParam( $listName ) };
	delete $listHash{ 'source' };
	$listHash{ 'sources' } = \@ipList;
	$listHash{ 'status' }  = &getBLStatus( $listName );
	$listHash{ 'farms' }   = &getBLParam( $listName, 'farms' );

	# day as a number type
	$listHash{ 'day' } += 0 if ( $listHash{ 'day' } =~ /^\d+$/ );

	# save hour, minute, period and unit parameters in 'time' hash
	my @timeParameters = ( 'period', 'unit', 'hour', 'minutes' );

	#~ $listHash{ 'time'};

	foreach my $param ( @timeParameters )
	{
		if ( exists $listHash{ $param } )
		{
			my $var = $listHash{ $param };
			$var += 0 if ( $var =~ /^\d+$/ );
			$listHash{ 'time' }->{ $param } = $var;
			delete $listHash{ $param };
		}
	}

	return \%listHash;
}

=begin nd
Function: getBLIpList

	Get list of IPs from a local or remote list.

Parameters:

	listName - local listname / remote url, where find list of IPs

Returns:

	-1		 	- error
	\@ipList	- successful

=cut

sub getBLIpList
{
	my ( $listName ) = @_;

	require Zevenet::Validate;

	my $output         = -1;
	my $blacklistsPath = &getGlobalConfiguration( 'blacklistsPath' );
	my $source_format  = &getValidFormat( 'blacklists_source' );

	# ip list format wrong
	# get only correct format lines
	open my $fh, '<', "$blacklistsPath/$listName.txt";
	chomp ( my @ipList = grep ( /($source_format)/, <$fh> ) );
	$output = \@ipList;
	close $fh;

	return $output;
}

=begin nd
	Function: getBLSourceNumber

        Get the number of sources from the source config file

        Parameters:
        list - list name
				
        Returns:
			integer - number of sources 

=cut

sub getBLSourceNumber
{
	my $list    = shift;
	my $wc      = &getGlobalConfiguration( "wc_bin" );
	my $sources = `$wc -l $blacklistsPath/$list.txt`;

	if ( $sources =~ /\s*(\d+)\s/ )
	{
		$sources = $1;
	}
	else
	{
		$sources = 0;
	}
	return $sources;
}

sub setBLLockConfigFile
{
	require Zevenet::Lock;

	my $lockfile = "/tmp/blacklist.lock";

	return &lockfile( $lockfile );
}

sub setBLUnlockConfigFile
{
	my $lock_fd = shift;

	require Zevenet::Lock;
	&unlockfile( $lock_fd );
}

1;
