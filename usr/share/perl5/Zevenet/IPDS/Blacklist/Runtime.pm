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

# The goal of this file is to keep the needed functions to apply actions to system
# related with the blacklist process: iptables, ipset, cron...

use strict;

use Zevenet::Core;
include 'Zevenet::IPDS::Blacklist::Core';

# &setBLRunList ( $listName );
sub setBLRunList
{
	my $listName = shift;

	my $ipset = &getGlobalConfiguration( 'ipset' );
	my $output;

	# Maximum number of sources in the list
	my $maxelem = &getBLSourceNumber( $listName );

	# ipset create the list with a minimum value of 64
	if ( $maxelem < 64 )
	{
		$maxelem = 64;
	}

	# looking for 2 power for maxelem
	else
	{
		# exponent = log2( maxelem )
		my $exponent = log ( $maxelem ) / log ( 2 );

		# the maxelem is not 2 power
		if ( $exponent - ( int $exponent ) > 0 )
		{
			# take a expoenent greater
			$maxelem = 2**( int $exponent + 1 );
		}

		# the maxelem was 2 power
		# else
		# maxelem = 2^n
	}

	#~ if ( &getBLIpsetStatus ( $listName ) eq 'down' )
	{
		&zenlog( "Creating ipset table", "info", "IPDS" );
		$output = system (
			   "$ipset create -exist $listName hash:net maxelem $maxelem >/dev/null 2>&1" );
	}

	if ( !$output )
	{
		&zenlog( "Refreshing list $listName", "info", "IPDS" );
		$output = &setBLRefreshList( $listName );

		&zenlog( "Error, refreshing list $listName", "error", "IPDS" ) if ( $output );
	}

	if ( &getBLParam( $listName, 'type' ) eq 'remote' )
	{
		&setBLCronTask( $listName );
	}

	return $output;
}

#  &setBLDestroyList ( $listName );
sub setBLDestroyList
{
	my $listName = shift;

	my $ipset = &getGlobalConfiguration( 'ipset' );
	my $output;

	# delete task from cron
	if ( &getBLParam( $listName, 'type' ) eq 'remote' )
	{
		&delBLCronTask( $listName );
	}

	# FIXME:  lunch consecutively this ipset command and below return error
	#~ if ( &getBLIpsetStatus ( $listName ) eq 'up' )
	#~ {
	&zenlog( "Destroying blacklist $listName", "info", "IPDS" );
	system ( "$ipset destroy $listName >/dev/null 2>&1" );

	#~ }

	return $output;
}

=begin nd
Function: setBLRefreshList

	Update IPs from a list.

Parameters:

	$listName

Returns:

	== 0	- successful
	!= 0	- error

=cut

sub setBLRefreshList
{
	my ( $listName ) = @_;

	my @ipList = @{ &getBLIpList( $listName ) };
	my $output;
	my $ipset     = &getGlobalConfiguration( 'ipset' );
	my $source_re = &getValidFormat( 'blacklists_source' );

	&zenlog( "refreshing '$listName'... ", "info", "IPDS" );
	$output = system ( "$ipset flush $listName >/dev/null 2>&1" );

	if ( !$output )
	{
		require Tie::File;
		require Zevenet::Lock;

		my $tmp_list = "/tmp/tmp_blacklist.txt";
		&ztielock( \my @list_tmp, $tmp_list );

		grep ( s/($source_re)/add $listName $1/, @ipList );
		my $touch = &getGlobalConfiguration( 'touch' );

		system ( "$touch $tmp_list >/dev/null 2>&1" );

		@list_tmp = @ipList;
		untie @list_tmp;

		system ( "$ipset restore < $tmp_list >/dev/null 2>&1" );

		unlink $tmp_list;
	}

	if ( $output )
	{
		&zenlog( "Error refreshing '$listName'.", "error", "IPDS" );
	}

	return $output;
}

=begin nd
Function: setBLRefreshAllLists

	Check if config file data and list directories are coherent
	Refresh all lists, locals and remotes.

Parameters: None.

Returns:

	0	- successful
	!=0	- error in some list

=cut

sub setBLRefreshAllLists
{
	my $output;
	my @lists = &getBLRuleList;

	# update lists
	foreach my $listName ( @lists )
	{
		# Download the remote lists
		if ( &getBLParam( $listName, 'type' ) eq 'remote' )
		{
			&setBLDownloadRemoteList( $listName );
		}

		# Refresh list if is running
		if ( &getBLIpsetStatus( $listName ) eq 'up' )
		{
			&setBLRefreshList( $listName );
		}
		&zenlog( "The preload list '$listName' was updated.", "info", "IPDS" );
	}

	return $output;
}

=begin nd
Function: setBLDownloadRemoteList

	Download a list from url and keep it in file

Parameters:

	listName

Returns:

=cut

sub setBLDownloadRemoteList
{
	my ( $listName ) = @_;

	require Tie::File;
	require Zevenet::Validate;
	include 'Zevenet::IPDS::Blacklist::Config';

	my $url = &getBLParam( $listName, 'url' );
	my $timeout = 10;
	my $error;

	&zenlog( "Downloading $listName...", "info", "IPDS" );

	# if ( $fileHandle->{ $listName }->{ 'update_status' } ne 'dis' )

	# Not direct standard output to null, this output is used for web variable
	my @web           = `curl --connect-timeout $timeout \"$url\" 2>/dev/null`;
	my $source_format = &getValidFormat( 'blacklists_source' );

	my @ipList;

	foreach my $line ( @web )
	{
		if ( $line =~ /($source_format)/ )
		{
			push @ipList, $1;
		}
	}

	# set URL down if it doesn't have any ip
	if ( !@ipList )
	{
		&setBLParam( $listName, 'update_status', 'down' );
		&zenlog( "Failed downloading $listName from url '$url'. Not found any source.", "error", "IPDS" );
		$error = 1;
	}
	else
	{
		my $path     = &getGlobalConfiguration( 'blacklistsPath' );
		my $fileList = "$path/$listName.txt";

		require Zevenet::Lock;
		&ztielock( \my @list, $fileList );
		@list = @ipList;
		untie @list;

		&setBLParam( $listName, 'update_status', 'up' );
		&zenlog( "$listName was downloaded successful.", "info", "IPDS" );
	}

	return $error;
}

=begin nd
Function: setBLCreateRule

	Block / accept connections from a ip list for a determinate farm.

Parameters:

	farmName - farm where rules will be applied
	name	 - ip list name

Returns:

	$cmd	- Command
	-1		- error

=cut

sub setBLCreateRule
{
	my ( $farmName, $listName ) = @_;

	require Zevenet::Farm::Base;
	require Zevenet::Netfilter;
	include 'Zevenet::IPDS::Core';

	my $add;
	my $cmd;
	my $output;
	my $chain;
	my @tables;
	my $action = &getBLParam( $listName, 'policy' );

	if ( &getBLIpsetStatus( $listName ) eq "down" )
	{
		# load in memory the list
		&setBLRunList( $listName );
	}

	#~ my $logMsg = "[Blocked by blacklists $listName in farm $farmName]";
	my $logMsg = &createLogMsg( "BL", $listName, $farmName );

	if ( $action eq "allow" )
	{
		$chain = &getIPDSChain( "whitelist" );
		@tables = ( 'raw', 'mangle' );
	}
	elsif ( $action eq "deny" )
	{
		$chain  = &getIPDSChain( "blacklist" );
		@tables = ( 'raw' );
	}
	else
	{
		&zenlog(
				"The parameter 'action' isn't valid in function 'setBLCreateIptableCmd'.", "warning", "IPDS" );
		return -1;
	}

	$add = '-I';

	my @match;
	my $type       = &getFarmType( $farmName );
	my $protocol   = &getFarmProto( $farmName );
	my $protocolL4 = &getFarmProto( $farmName );
	my $vip        = &getFarmVip( 'vip', $farmName );
	my $vport      = &getFarmVip( 'vipp', $farmName );

	# no farm
	# blank chain
	if ( $type eq 'l4xnat' )
	{
		require Zevenet::Farm::L4xNAT::Validate;

		# all ports
		if ( $vport eq '*' )
		{
			push @match, "-d $vip --protocol tcp";
		}

		# l4 farm multiport
		elsif ( &ismport( $vport ) eq "true" )
		{
			push @match, "-d $vip --protocol tcp -m multiport --dports $vport";
		}

		# unique port
		else
		{
			push @match, "-d $vip --protocol tcp --dport $vport";
			push @match, "-d $vip --protocol udp --dport $vport";
		}
	}

	# farm using tcp and udp protocol
	elsif ( $type eq 'gslb' )
	{
		push @match, "-d $vip --protocol tcp --dport $vport";
		push @match, "-d $vip --protocol udp --dport $vport";
	}

	# http farms
	elsif ( $type =~ /http/ )
	{
		push @match, "-d $vip --protocol tcp --dport $vport";
	}

	#~ #not valid datlink farms
	elsif ( $type eq 'datalink' )
	{
	push @match, "-d $vip";
	}

	foreach my $farmOpt (@match)
	{
		foreach my $table (@tables	)
		{

# iptables -A PREROUTING -t raw -m set --match-set wl_2 src -d 192.168.100.242 -p tcp --dport 80 -j DROP -m comment --comment "BL,rulename,farmname"
			$cmd = &getGlobalConfiguration( 'iptables' )
			  . " $add $chain -t $table -m set --match-set $listName src $farmOpt -m comment --comment \"BL,$listName,$farmName\"";

			if ( $action eq "deny" )
			{
				# check inside of function
				$output = &setIPDSDropAndLog( $cmd, $logMsg );
			}
			else
			{
				# the rule already exists
				if ( !&getIPDSRuleExists( $cmd ) )
				{
					$output = &iptSystem( "$cmd -j ACCEPT" );
				}
			}

			if ( !$output )
			{
				&zenlog( "List '$listName' was applied successful to the farm '$farmName'.", "info", "IPDS" );
			}
		}
	}

	return $output;
}

=begin nd
Function: setBLDeleteRule

	Delete a iptables rule.

Parameters:

	farmName - farm where rules will be applied
	list	 - ip list name

Returns:

	== 0	- successful
	!= 0	- error

=cut

sub setBLDeleteRule
{
	my ( $farmName, $listName ) = @_;

	require Zevenet::Netfilter;
	include 'Zevenet::IPDS::Core';

	my $chain  = 'blacklist';
	my @tables = ( 'raw' );
	if ( &getBLParam( $listName, 'policy' ) eq "allow" )
	{
		$chain = "whitelist";
		@tables = ( 'raw', 'mangle' );
	}

	$chain = &getIPDSChain( $chain );
	my $output;

	foreach my $table ( @tables )
	{
		# Get line number
		my @rules = &getIptListV4( $table, $chain );
		@rules =
		  grep ( /^(\d+) .+match-set $listName src .+BL,$listName,$farmName/, @rules );

		my $lineNum = 0;
		my $size    = scalar @rules - 1;
		my $cmd;
		for ( ; $size >= 0 ; $size-- )
		{
			if ( $rules[$size] =~ /^(\d+) / )
			{
				$lineNum = $1;

				# Delete
				#	iptables -D PREROUTING -t raw 3
				$cmd =
				  &getGlobalConfiguration( 'iptables' ) . " --table $table -D $chain $lineNum";
				&iptSystem( $cmd );
			}
		}
	}

	# delete list if it isn't used. This has to be the last call.
	if ( !&getBLListNoUsed( $listName ) )
	{
		&setBLDestroyList( $listName );
	}

	return $output;
}

sub delBLCronTask
{
	my $listName = shift;

	require Tie::File;

	my $blacklistsCronFile = &getGlobalConfiguration( 'blacklistsCronFile' );
	my $index              = 0;

	require Zevenet::Lock;
	&ztielock( \my @list, $blacklistsCronFile );

	foreach my $line ( @list )
	{
		if ( $line =~ /\s$listName\s/ )
		{
			splice @list, $index, 1;
			last;
		}
		$index++;
	}

	untie @list;

	my $cron_service = &getGlobalConfiguration( 'cron_service' );
	&logAndRun( "$cron_service restart" );

	&zenlog( "Deleted the task associated to the list $listName", "info", "IPDS" );
}

# &setBLCronTask ( $list );
sub setBLCronTask
{
	my ( $listName ) = @_;

	my $cronFormat =
	  { 'min' => '*', 'hour' => '*', 'dow' => '*', 'dom' => '*', 'month' => '*' };
	my $rblFormat;

	# get values
	$rblFormat->{ 'frequency' }      = &getBLParam( $listName, 'frequency' );
	$rblFormat->{ 'minutes' }        = &getBLParam( $listName, 'minutes' );
	$rblFormat->{ 'hour' }           = &getBLParam( $listName, 'hour' );
	$rblFormat->{ 'period' }         = &getBLParam( $listName, 'period' );
	$rblFormat->{ 'unit' }           = &getBLParam( $listName, 'unit' );
	$rblFormat->{ 'frequency_type' } = &getBLParam( $listName, 'frequency_type' );
	$rblFormat->{ 'day' }            = &getBLParam( $listName, 'day' );

	# change to cron format
	if (    $rblFormat->{ 'frequency' } eq 'daily'
		 && $rblFormat->{ 'frequency_type' } eq 'period' )
	{
		my $period = $rblFormat->{ 'period' };
		if ( $rblFormat->{ 'unit' } eq 'minutes' )
		{
			$cronFormat->{ 'min' } = "*/$rblFormat->{ 'period' }";
		}
		elsif ( $rblFormat->{ 'unit' } eq 'hours' )
		{
			$cronFormat->{ 'min' }  = '00';
			$cronFormat->{ 'hour' } = "*/$rblFormat->{ 'period' }";
		}
	}
	else
	{
		$cronFormat->{ 'hour' } = "$rblFormat->{ 'hour' }";
		$cronFormat->{ 'min' }  = "$rblFormat->{ 'minutes' }";

		# exact daily frencuncies only need these fields

		if ( $rblFormat->{ 'frequency' } eq 'weekly' )
		{
			my $day = $rblFormat->{ 'day' };

			if    ( $day eq 'monday' )    { $cronFormat->{ 'dow' } = '0' }
			elsif ( $day eq 'tuesday' )   { $cronFormat->{ 'dow' } = '1' }
			elsif ( $day eq 'wednesday' ) { $cronFormat->{ 'dow' } = '2' }
			elsif ( $day eq 'thursday' )  { $cronFormat->{ 'dow' } = '3' }
			elsif ( $day eq 'friday' )    { $cronFormat->{ 'dow' } = '4' }
			elsif ( $day eq 'saturday' )  { $cronFormat->{ 'dow' } = '5' }
			elsif ( $day eq 'sunday' )    { $cronFormat->{ 'dow' } = '6' }
		}
		elsif ( $rblFormat->{ 'frequency' } eq 'monthly' )
		{
			$cronFormat->{ 'dom' } = $rblFormat->{ 'day' };
		}
	}

	my $blacklistsCronFile = &getGlobalConfiguration( 'blacklistsCronFile' );

	# 0 0 * * 1	root	/usr/local/zevenet/app/zenrrd/zenrrd.pl & >/dev/null 2>&1
	my $cmd =
	  "$cronFormat->{ 'min' } $cronFormat->{ 'hour' } $cronFormat->{ 'dom' } $cronFormat->{ 'month' } $cronFormat->{ 'dow' }\t"
	  . "root\t/usr/local/zevenet/www/ipds/blacklists/updateRemoteList.pl $listName & >/dev/null 2>&1";
	&zenlog( "Added cron task: $cmd", "info", "IPDS" );

	require Zevenet::Lock;
	&ztielock( \my @list, $blacklistsCronFile );

	# this line already exists, replace it
	if ( grep ( s/.* $listName .*/$cmd/, @list ) )
	{
		&zenlog( "update cron task for list $listName", "info", "IPDS" );
	}
	else
	{
		push @list, $cmd;
	}
	untie @list;

	my $cron_service = &getGlobalConfiguration( 'cron_service' );
	&logAndRun( "$cron_service restart" );
	&zenlog( "Created a cron task for the list $listName", "info", "IPDS" );
}

# setBLApplyToFarm ( $farmName, $list );
sub setBLApplyToFarm
{
	my ( $farmName, $listName ) = @_;

	require Zevenet::Farm::Base;

	my $output;

	# run rule only if the farm is up and the rule is enabled
	if ( &getBLParam( $listName, 'status' ) ne 'down' )
	{
		if ( &getFarmStatus( $farmName ) eq 'up' )
		{
			# load de list if it is not been used
			if ( &getBLIpsetStatus( $listName ) eq 'down' )
			{
				$output = &setBLRunList( $listName );

				# if the list is remote and is not downloaded yet, downloaded it
				if ( &getBLParam( $listName, 'remote' ) )
				{
					&setBLDownloadRemoteList( $listName );
				}
			}

			# create iptable rule
			if ( !$output )
			{
				$output = &setBLCreateRule( $farmName, $listName );
			}
		}
	}

	if ( !$output )
	{
		include 'Zevenet::IPDS::Blacklist::Config';
		$output = &setBLParam( $listName, 'farms-add', $farmName );
	}

	return $output;
}

# &setBLRemFromFarm ( $farmName, $listName );
sub setBLRemFromFarm
{
	my ( $farmName, $listName ) = @_;

	my $output = &setBLDeleteRule( $farmName, $listName );

	if ( !$output )
	{
		include 'Zevenet::IPDS::Blacklist::Config';
		$output = &setBLParam( $listName, 'farms-del', $farmName );
	}

	# delete list if it isn't used. This has to be the last call.
	if ( !$output && !&getBLListNoUsed( $listName ) )
	{
		&setBLDestroyList( $listName );
	}

	return $output;
}

1;
