#!/usr/bin/perl

###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This library is free software; you can redistribute it and/or modify it
#     under the terms of the GNU Lesser General Public License as published
#     by the Free Software Foundation; either version 2.1 of the License, or
#     (at your option) any later version.
#
#     This library is distributed in the hope that it will be useful, but
#     WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
#     General Public License for more details.
#
#     You should have received a copy of the GNU Lesser General Public License
#     along with this library; if not, write to the Free Software Foundation,
#     Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
###############################################################################

#~ use strict;
use Config::Tiny;
use Tie::File;

require "/usr/local/zenloadbalancer/www/Plugins/ipds.cgi";
require "/usr/local/zenloadbalancer/www/farms_functions.cgi";
require "/usr/local/zenloadbalancer/www/functions_ext.cgi";
require "/usr/local/zenloadbalancer/www/check_functions.cgi";

#~ use warnings;
#~ use strict;

my $blacklistsPath = &getGlobalConfiguration( 'blacklistsPath' );
my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );

actions:

#  &getBLLoadList ( $listName );
sub getBLLoadList
{
	my $listName = shift;
	my $ipset    = &getGlobalConfiguration( 'ipset' );
	my $output   = system ( "$ipset list $listName 2>/dev/null" );

	return $output;
}

# &setBLRunList ( $listName );
sub setBLRunList
{
	my $listName = shift;
	my $ipset    = &getGlobalConfiguration( 'ipset' );
	my $output;

	if ( system ( "$ipset -L $listName 2>/dev/null" ) )
	{
		$output = system ( "$ipset create $listName hash:net 2>/dev/null" );
		&zenlog( "Creating ipset table" );
	}

	# Discomment to download the remote list  whe is applied
	# if ( !$output && &getBLParam( $listName, 'location' ) eq 'remote' )
	# {
	# $output = &setBLDownloadRemoteList ( $listName ) ;
	# &zenlog ( "Downloading remote list" );
	# }

	if ( !$output )
	{
		$output = &setBLRefreshList( $listName );
		&zenlog( "Setting refreshing list" );
	}

	if ( &getBLParam( $listName, 'location' ) eq 'remote' )
	{
		&setBLCronTask( $listName );
	}

	return $output;
}

#  &setBLDestroyList ( $listName );
sub setBLDestroyList
{
	my $listName = shift;
	my $ipset    = &getGlobalConfiguration( 'ipset' );
	my $output;

	# delete task from cron
	if ( &getBLParam( $listName, 'location' ) eq 'remote' )
	{
		&delBLCronTask( $listName );
	}

	if ( !system ( "$ipset -L $listName 2>/dev/null" ) )
	{
		&zenlog( "Destroying list" );
		$output = system ( "$ipset destroy $listName 2>/dev/null" );
	}

	return $output;
}

=begin nd
        Function: setBLStart

        Enable all blacklists rules

        Parameters:
				
        Returns:

=cut

#  &setBLStart
sub setBLStart
{
	my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
	my $ipset          = &getGlobalConfiguration( 'ipset' );
	my $touch          = &getGlobalConfiguration( 'touch' );
	my @rules          = @{ &getBLRules() };
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
	&setBLAddPreloadLists();

	my $allLists = Config::Tiny->read( $blacklistsConf );

	# load lists
	foreach my $list ( keys %{ $allLists } )
	{
		my @farms = @{ &getBLParam( $list, "farms" ) };
		if ( @farms )
		{
			&setBLRunList( $list );
		}

		# create cmd  for all farms where are applied the list
		foreach my $farm ( @farms )
		{
			&zenlog( "Creating rules for the list $list and farm $farm." );
			&setBLCreateRule( $farm, $list );
		}
	}
}

=begin nd
        Function: setBLStop

        Disable all blacklists rules
        
        Parameters:
				
        Returns:

=cut

# &setBLStop
sub setBLStop
{
	my @rules           = @{ &getBLRules() };
	my $blacklists_list = &getValidFormat( 'blacklists_list' );
	my $farm_name       = &getValidFormat( 'farm_name' );

	my @allLists;

	foreach my $rule ( @rules )
	{

		if ( $rule =~ /^(\d+) .+match-set ($blacklists_list) src .+BL_$farm_name/ )
		{
			my $list = $2;
			my $cmd =
			  &getGlobalConfiguration( 'iptables' ) . " --table raw -D PREROUTING $1";
			&iptSystem( $cmd );

			# note the list to delete it late
			push @allLists, $list if ( !grep ( /^$list$/, @allLists ) );
		}

	}

	foreach my $listName ( @allLists )
	{
		&setBLDestroyList( $listName );
	}

}

=begin nd
        Function: setBLCreateRule

        block / accept connections from a ip list for a determinate farm.

        Parameters:
				farmName - farm where rules will be applied
				list	 - ip list name
				action	 - list type: deny / allow
				
        Returns:
				$cmd	- Command
                -1		- error

=cut

# &setBLCreateRule ( $farmName, $list );
sub setBLCreateRule
{
	my ( $farmName, $listName ) = @_;
	my $add;
	my $cmd;
	my $output;
	my $logMsg = "[Blocked by BL rule]";
	my $action = &getBLParam( $listName, 'type' );

	if ( $action eq "allow" )
	{
		$add = "-I";

	}
	elsif ( $action eq "deny" )
	{
		$add = "-A";
	}
	else
	{
		$output = -1;
		&zenlog(
				"The parameter 'action' isn't valid in function 'setBLCreateIptableCmd'." );
	}

	if ( !$output )
	{
		# -d farmIP, -p PROTOCOL --dport farmPORT
		my $vip   = &getFarmVip( 'vip',  $farmName );
		my $vport = &getFarmVip( 'vipp', $farmName );
		my $farmOpt  = "-d $vip";
		my $protocol = &getFarmProto( $farmName );

		if ( $protocol =~ /UDP/i || $protocol =~ /TFTP/i || $protocol =~ /SIP/i )
		{
			$protocol = 'udp';
			$farmOpt  = "$farmOpt -p $protocol --dport $vport";
		}

		if ( $protocol =~ /TCP/i || $protocol =~ /FTP/i )
		{
			$protocol = 'tcp';
			$farmOpt  = "$farmOpt -p $protocol --dport $vport";
		}

# 		iptables -A PREROUTING -t raw -m set --match-set wl_2 src -d 192.168.100.242 -p tcp --dport 80 -j DROP -m comment --comment "BL_farmname"
		$cmd = &getGlobalConfiguration( 'iptables' )
		  . " $add PREROUTING -t raw -m set --match-set $listName src $farmOpt -m comment --comment \"BL_$farmName\"";
	}

	if ( $action eq "deny" )
	{
		$output = &setIPDSDropAndLog( $cmd, $logMsg );
	}
	else
	{
		$output = &iptSystem( "$cmd -j ACCEPT" );
	}

	if ( !$output )
	{
		&zenlog( "List '$listName' was applied successful to the farm '$farmName'." );
	}

	return $output;
}

=begin nd
        Function: setBLDeleteRule

        Delete a iptables rule 

        Parameters:
				farmName - farm where rules will be applied
				list	 - ip list name
				
        Returns:
				== 0	- successful
                != 0	- error

=cut

# &setBLDeleteRule ( $farmName, $listName )
sub setBLDeleteRule
{
	my ( $farmName, $listName ) = @_;
	my $output;

	# Get line number
	my @rules = &getIptList( $farmName, 'raw', 'PREROUTING' );
	@rules = grep ( /^(\d+) .+match-set $listName src .+BL_$farmName/, @rules );

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
			  &getGlobalConfiguration( 'iptables' ) . " --table raw -D PREROUTING $lineNum";
			&iptSystem( $cmd );
		}
	}

	# check if proccess was successful:
	@rules = &getIptList( $farmName, 'raw', 'PREROUTING' );
	if ( grep ( /^(\d+) .+match-set $listName src .+BL_$farmName/, @rules ) )
	{
		&zenlog( "Error, deleting '$farmName' from the list '$listName'." );
		$output = -1;
	}

	return $output;
}

# setBLApplyToFarm ( $farmName, $list );
sub setBLApplyToFarm
{
	my ( $farmName, $listName ) = @_;
	my $output;

	if ( !@{ &getBLParam( $listName, 'farms' ) } )
	{
		$output = &setBLRunList( $listName );
	}

	if ( !$output )
	{
		$output = &setBLCreateRule( $farmName, $listName );
	}

	if ( !$output )
	{
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
		$output = &setBLParam( $listName, 'farms-del', $farmName );
	}

	# delete list if it isn't used. This has to be the last call.
	if ( !$output && !@{ &getBLParam( $listName, 'farms' ) } )
	{
		&setBLDestroyList( $listName );
	}

	return $output;
}

# -------------------
lists:

# The lists will be always created and updated although these aren't used at the moment
# When a list is applied to a farm, a ip rule will be created with port and ip where farm is working.
# -------------------

=begin nd
        Function: setBLPreloadLists

        This function return all preload lists available or 
        the source list of ones of this

        Parameters:
        
				country		- this param is optional, with this param, the function return the 
										source list of lan segment for a counry
				
        Returns:

                array ref	- availabe counrties or source list
                
=cut

# &getBLPreloadLists;
sub setBLAddPreloadLists
{
	my $blacklistsLocalPreload =
	  &getGlobalConfiguration( 'blacklistsLocalPreload' );
	my $blacklistsRemotePreload =
	  &getGlobalConfiguration( 'blacklistsRemotePreload' );
	my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
	my $blacklistsPath = &getGlobalConfiguration( 'blacklistsPath' );

	# Local preload lists
	opendir ( DIR, "$blacklistsLocalPreload/" );
	my @preloadLists = readdir ( DIR );
	closedir ( DIR );

	my $fileHandle = Config::Tiny->read( $blacklistsConf );
	foreach my $list ( @preloadLists )
	{
		if ( $list =~ s/.txt$// )
		{
			# save lists
			if ( !exists $fileHandle->{ $list } )
			{
				my $listHash;
				$listHash->{ 'location' } = 'local';
				$listHash->{ 'preload' }  = 'true';

				&setBLCreateList( $list, $listHash );
				&zenlog( "The preload list '$list' was created." );

				system ( "cp $blacklistsLocalPreload/$list.txt $blacklistsPath/$list.txt" );
				&zenlog( "The preload list '$list' was created." );
			}
			elsif ( $fileHandle->{ $list }->{ 'preload' } eq 'true' )
			{
				system ( "cp $blacklistsLocalPreload/$list.txt $blacklistsPath/$list.txt" );
				&zenlog( "The preload list '$list' was updated." );
			}
			else
			{
				&zenlog(
					"The preload list '$list' can't be loaded because other list exists with the same name."
				);
			}
		}
	}

	my $remoteFile = Config::Tiny->read( $blacklistsRemotePreload );

	# Remote preload lists
	foreach my $list ( keys %{ $remoteFile } )
	{
		# list don't exist. Download
		if ( !exists $fileHandle->{ $list } )
		{
			my $listHash;
			$listHash->{ 'url' }      = $remoteFile->{ $list }->{ 'url' };
			$listHash->{ 'location' } = 'remote';
			$listHash->{ 'preload' }  = 'true';

			&setBLCreateList( $list, $listHash );
			&zenlog( "The preload list '$list' was created." );
		}

		# list exists like preload. Update settings
		elsif ( &getBLParam( $list, 'preload' ) eq 'true' )
		{
			&zenlog( "Update list $list" );
			&setBLParam( $list, 'url', $remoteFile->{ $list }->{ 'url' } );

			# Download lists if not exists
			if ( !-f "$blacklistsPath/$list.txt" )
			{
				&setBLDownloadRemoteList( $list );
			}
			&zenlog( "The preload list '$list' was updated." );
		}

		# list exists like NO preload
		else
		{
			&zenlog(
				"The preload list '$list' can't be loaded because other list exists with the same name."
			);
		}

	}

}

# $listParams = \ %paramsRef;
# &setBLCreateList ( $listName, $paramsRef );
sub setBLCreateList
{
	my $listName    = shift;
	my $listParams  = shift;
	my $def_type    = 'deny';
	my $def_preload = 'false';
	my $output;

	my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
	my $blacklistsPath = &getGlobalConfiguration( 'blacklistsPath' );
	my $touch          = &getGlobalConfiguration( 'touch' );
	my $location       = $listParams->{ 'location' };

	if ( !-e $blacklistsConf )
	{
		$output = system ( "$touch $blacklistsConf" );
		&zenlog( "blacklists configuration file was created." );
	}

	if ( $listParams->{ 'location' } eq 'remote' && !exists $listParams->{ 'url' } )
	{
		&zenlog( "Remote lists need a url" );
		return -1;
	}

	# share params
	my $fileHandle = Config::Tiny->read( $blacklistsConf );
	$fileHandle->{ $listName }->{ 'location' } = $listParams->{ 'location' };
	$fileHandle->{ $listName }->{ 'farms' }    = "";
	if ( exists $listParams->{ 'preload' } )
	{
		$fileHandle->{ $listName }->{ 'preload' } = $listParams->{ 'preload' };
	}
	else
	{
		$fileHandle->{ $listName }->{ 'preload' } = $def_preload;
	}
	if ( exists $listParams->{ 'type' } )
	{
		$fileHandle->{ $listName }->{ 'type' } = $listParams->{ 'type' };
	}
	else
	{
		$fileHandle->{ $listName }->{ 'type' } = $def_type;
	}

	if ( $listParams->{ 'type' } eq 'allow' )
	{
		$fileHandle->{ $listName }->{ 'action' } = "ACCEPT";
	}
	else
	{
		$fileHandle->{ $listName }->{ 'action' } = "DROP";
	}
	$fileHandle->write( $blacklistsConf );

	# specific to remote lists
	if ( $location eq 'remote' )
	{
		&setBLParam( $listName, 'url', $listParams->{ 'url' } );
		&setBLParam( $listName, 'min', $listParams->{ 'min' } )
		  if ( exists $listParams->{ 'min' } );
		&setBLParam( $listName, 'hour', $listParams->{ 'hour' } )
		  if ( exists $listParams->{ 'hour' } );
		&setBLParam( $listName, 'dom', $listParams->{ 'dom' } )
		  if ( exists $listParams->{ 'dom' } );
		&setBLParam( $listName, 'month', $listParams->{ 'month' } )
		  if ( exists $listParams->{ 'month' } );
		&setBLParam( $listName, 'dow', $listParams->{ 'dow' } )
		  if ( exists $listParams->{ 'dow' } );

		#~ &setBLDownloadRemoteList ( $listName );
	}

	# specific to local lists
	elsif ( $location eq 'local' )
	{
		$output = system ( "$touch $blacklistsPath/$listName.txt" );
	}

	if ( !$output )
	{
		&zenlog( "'$listName' list was created successful" );
	}

	return $output;
}

=begin nd
        Function: setBLDeleteList

        delete a list from iptables, ipset and configuration file
			

        Parameters:
        
				$listName	- List to delete
        
        Returns:

                ==0	- successful
				!=0 - error
                
=cut

# &setBLDeleteList ( $listName )
sub setBLDeleteList
{
	my ( $listName ) = @_;
	my $fileHandle;
	my $output;
	my $error;

	my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
	my $blacklistsPath = &getGlobalConfiguration( 'blacklistsPath' );
	my $ipset          = &getGlobalConfiguration( 'ipset' );
	my @farms          = &getBLParam( $listName, 'farms' );

	# delete associated farms
	foreach my $farmName ( @farms )
	{
		$output = &setBLDeleteRule( $farmName, $listName );
		last if $output;
	}

	if ( !$output && &getBLParam( $listName, 'preload' ) eq 'false' )
	{
		# delete from config file
		$fileHandle = Config::Tiny->read( $blacklistsConf );
		delete $fileHandle->{ $listName };
		$fileHandle->write( $blacklistsConf );

		if ( -f "$blacklistsPath/$listName.txt" )
		{
			$output = system ( "rm $blacklistsPath/$listName.txt" );
		}
	}

	# delete list from ipset
	$output = &setBLDestroyList( $listName );
	if ( $output != 0 )
	{
		&zenlog( "Error deleting the list '$listName'." );

		#~ $output = 0;
	}
	else
	{
		&zenlog( "List '$listName' was deleted successful." );
	}

	return $output;
}

=begin nd
        Function: setBLParam

				Modificate local config file 

        Parameters:
        
				name	- section name
				key		- field to modificate
				value	- value for the field
				opt		- add / del		when key = farms

        Returns:
                0	- successful
                !=0	- error
                
=cut

# &setBLParam ( $name , $key,  $value )
sub setBLParam
{
	my ( $name, $key, $value ) = @_;
	my $output;

	# get conf
	my $location       = &getBLParam( $name, 'location' );
	my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
	my $fileHandle     = Config::Tiny->read( $blacklistsConf );
	my $conf           = $fileHandle->{ $name };
	my @farmList       = @{ &getBLParam( $name, 'farms' ) };
	my $ipList         = &getBLParam( $name, 'sources' );

	# change name of the list
	if ( 'list' eq $key )
	{
		my @listNames = keys %{ $fileHandle };
		if ( !&getBLExists( $name ) )
		{
			&zenlog( "List '$value' just exists." );
			$output = -1;
		}
		else
		{
			# delete list and all rules applied to the farms
			$output = &setBLDeleteList( $name );

			# crete new list
			$output = &setBLCreateList( $value, $conf ) if ( !$output );
			$output = &setBLParam( $value, 'sources', $ipList ) if ( !$output );

			# apply rules to farms
			if ( !$output )
			{
				foreach my $farm ( @farmList )
				{
					&setBLCreateRule( $farm, $value );
				}
			}
			return $output;
		}
	}
	elsif ( 'type' eq $key )
	{
		$conf->{ 'type' } = $value;
		$fileHandle->write( $blacklistsConf );

		# delete list and all rules applied to farms
		$output = &setBLDeleteList( $name );

		# crete new list
		$output = &setBLCreateList( $name, $conf );
		$output = &setBLParam( $name, 'sources', $ipList );

		&zenlog ("??? farm:$_") for (@farmList);

		# apply rules to farms
		foreach my $farm ( @farmList )
		{
			&setBLDeleteRule ( $farm, $name );
			$output = &setBLCreateRule( $farm, $name );
			$output = &setBLParam( $name, 'farms-add', $farm );
		}
		return $output;
	}
	elsif ( 'sources' eq $key )
	{
		# only can be modificated local lists not preloaded
		if (    $conf->{ 'location' } eq 'local'
			 && $conf->{ 'preload' } eq 'false' )
		{
			$output = &setBLAddToList( $name, $value );
			$output = &setBLRefreshList( $name ) if ( !$output );
		}
	}
	elsif ( 'farms-add' eq $key )
	{
		if ( $conf->{ $key } !~ /(^| )$value( |$)/ )
		{
			my $farmList = $fileHandle->{ $name }->{ 'farms' };
			$fileHandle->{ $name }->{ 'farms' } = "$farmList $value";
			$fileHandle->write( $blacklistsConf );
		}
	}
	elsif ( 'farms-del' eq $key )
	{
		$fileHandle->{ $name }->{ 'farms' } =~ s/(^| )$value( |$)/ /;
		$fileHandle->write( $blacklistsConf );
	}
	elsif ( 'status' eq $key
			&& ( $value ne 'up' && $value ne 'down' && $value ne 'dis' ) )
	{
		&zenlog(
			 "Wrong parameter 'value' for 'status' key in 'setBLRemoteListConfig' function."
		);
		$output = -1;
	}

	# other value  of the file conf
	else
	{
		$fileHandle->{ $name }->{ $key } = $value;
		$fileHandle->write( $blacklistsConf );
	}

	return $output;
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
					- status-> modificate list status ( only remote lists )
					- list  -> modificate ip list ( only local lists )
					
				value	- value for the field

        Returns:
                0	- successful
                !=0	- error
                
=cut

# &getBLParam ( $listName, $key )
sub getBLParam
{
	my ( $listName, $key ) = @_;
	my $output;
	my $fileHandle;

	my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
	$fileHandle = Config::Tiny->read( $blacklistsConf );

	if ( !$key )
	{
		$output                = $fileHandle->{ $listName };
		$output->{ 'list' }    = $listName;
		$output->{ 'sources' } = &getBLIpList( $listName );
	}
	elsif ( $key eq 'sources' )
	{
		$output = &getBLIpList( $listName );
	}
	else
	{
		if ( exists $fileHandle->{ $listName } )
		{
			$output = $fileHandle->{ $listName }->{ $key };
			if ( $key eq 'farms' )
			{
				my @aux = split ( ' ', $output );
				$output = \@aux;
			}
		}

		# don't exist that list
		else
		{
			&zenlog( "List '$listName' doesn't exist." );
			$output = -1;
		}
	}
	return $output;
}

=begin nd
        Function: getBLExists

		get if a list exists o all available lists

        Parameters:

				listName	-	return 0 if list exists
				no param	-	return a ref array of all available lists

        Returns:

                0   - list exists
                -1  - list doesn't exist
                
=cut

# &getBLExists ( $listName );
sub getBLExists
{
	my $listName       = shift;
	my $output         = -1;
	my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
	my $fileHandle     = Config::Tiny->read( $blacklistsConf );
	my @aux;

	if ( $listName )
	{
		$output = 0 if ( exists $fileHandle->{ $listName } );
	}
	else
	{
		@aux    = keys %{ $fileHandle };
		$output = \@aux;
	}

	return $output;
}

=begin nd
        Function: getBLIpList

		Download a list from url and keep it in file

        Parameters:
        
                listName 

        Returns:
                
=cut

# &setBLDownloadRemoteList ( $listName );
sub setBLDownloadRemoteList
{
	my ( $listName ) = @_;
	my $url = &getBLParam( $listName, 'url' );
	my $timeout = 10;

	&zenlog( "Downloading $listName..." );

	# if ( $fileHandle->{ $listName }->{ 'status' } ne 'dis' )
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
		&setBLParam( $listName, 'status', 'down' );
		&zenlog( "$url was marked as down" );
	}
	else
	{
		my $path     = &getGlobalConfiguration( 'blacklistsPath' );
		my $fileList = "$path/$listName.txt";
		tie my @list, 'Tie::File', $fileList;
		@list = @ipList;
		untie @list;
		&setBLParam( $listName, 'status', 'up' );
		&zenlog( "$listName was download" );
	}

}

=begin nd
        Function: setBLRefreshList

        Update IPs from a list

        Parameters:
        
				$listName 	
				
        Returns:

                == 0	- successful
                != 0	- error
                
=cut

#	&setBLRefreshList ( $listName )
sub setBLRefreshList
{
	my ( $listName ) = @_;
	my @ipList = @{ &getBLIpList( $listName ) };
	my $output;
	my $ipset     = &getGlobalConfiguration( 'ipset' );
	my $source_re = &getValidFormat( 'blacklists_source' );

	&zenlog( "refreshing '$listName'... " );
	$output = system ( "$ipset flush $listName 2>/dev/null" );

	#~ if ( !$output )
	#~ {
	#~ foreach my $ip ( @ipList )
	#~ {
	#~ $output = system ( "$ipset add $listName $ip 2>/dev/null" );
	#~ if ( $output  )
	#~ {
	#~ &zenlog ( "Error, adding $ip source" );
	#~ last;
	#~ }
	#~ }
	#~ }

	if ( !$output )
	{
		grep ( s/($source_re)/add $listName $1/, @ipList );

		my $tmp_list = "/tmp/tmp_blacklist.txt";
		my $touch    = &getGlobalConfiguration( 'touch' );
		system ( "$touch $tmp_list 2>/dev/null" );
		tie my @list_tmp, 'Tie::File', $tmp_list;
		@list_tmp = @ipList;
		untie @list_tmp;

		system ( "$ipset restore < $tmp_list 2>/dev/null" );

		my $rm = &getGlobalConfiguration( 'rm' );
		system ( "$rm $tmp_list" );
	}

	&zenlog( "refreshed '$listName'." );
	return $output;
}

=begin nd
        Function: setBLRefreshAllLists

				Check if config file data and list directories are coherent
				Refresh all lists, locals and remotes.
				
        Parameters:
        
        Returns:
                0	- successful
                !=0	- error in some list 
                
=cut				

# &setBLRefreshAllLists
sub setBLRefreshAllLists
{
	my $output;
	my @lists = @{ &getBLExists };

	# update lists
	foreach my $listName ( @lists )
	{
		# Download the remote lists
		if ( &getBLParam( $listName, 'location' ) eq 'remote' )
		{
			&setBLDownloadRemoteList( $listName );
		}

		# Refresh list if is running
		if ( &getBLLoadList( $listName ) )
		{
			&setBLRefreshList( $listName );
		}
		&zenlog( "The preload list '$listName' was update." );
	}
	return $output;
}

=begin nd
        Function: getBLIpList

				get list of IPs from a local or remote list

        Parameters:
        
                listName - local listname / remote url, where find list of IPs

        Returns:
                -1		 	- error
                \@ipList	- successful
                
=cut

# &getBLIpList ( $listName )
sub getBLIpList
{
	my ( $listName ) = @_;
	my @ipList;
	my $output = -1;
	my $fileHandle;

	my $blacklistsPath = &getGlobalConfiguration( 'blacklistsPath' );
	my $source_format  = &getValidFormat( 'blacklists_source' );

	#~ my $fileList = "$PreloadPath/$listName.txt";

	tie my @list, 'Tie::File', "$blacklistsPath/$listName.txt";
	@ipList = @list;
	untie @list;

	# ip list format wrong
	# get only correct format lines
	@ipList = grep ( /($source_format)/, @ipList );
	$output = \@ipList;

	return $output;
}

=begin nd
        Function: setBLAddToList

		Change ip list for a list

        Parameters:
				listName
				listRef	 - ref to ip list
				
        Returns:

=cut			

# &setBLAddToList  ( $listName, \@ipList );
sub setBLAddToList
{
	my ( $listName, $listRef ) = @_;
	my $blacklistsPath = &getGlobalConfiguration( 'blacklistsPath' );
	my $source_format  = &getValidFormat( 'blacklists_source' );
	my @ipList         = grep ( /$source_format/, @{ $listRef } );
	my $output         = -1;

	if ( -f "$blacklistsPath/$listName.txt" )
	{
		tie my @list, 'Tie::File', "$blacklistsPath/$listName.txt";
		@list = @ipList;
		untie @list;
		&zenlog( "IPs of '$listName' was modificated." );
		$output = 0;
	}
	return $output;
}

=begin nd
        Function: setBrefreshLDeleteSource

        Delete a source from a list

        Parameters:
				list	- ip list name
				id		- line to delete
				
        Returns:

=cut

# &setBLDeleteSource  ( $listName, $id );
sub setBLDeleteSource
{
	my ( $listName, $id ) = @_;
	my $type = &getBLParam( $listName, 'type' );

	my $ipset          = &getGlobalConfiguration( 'ipset' );
	my $blacklistsPath = &getGlobalConfiguration( 'blacklistsPath' );

	tie my @list, 'Tie::File', "$blacklistsPath/$listName.txt";
	my $source = splice @list, $id, 1;
	untie @list;

	my $err;
	if ( @{ &getBLParam( $listName, 'farms' ) } )
	{
		$err = system ( "$ipset del $listName $source 2>/dev/null" );
	}
	&zenlog( "$source was deleted from $listName" ) if ( !$err );

	return $err;
}

=begin nd
        Function: setBLAddSource

        Add a source from a list

        Parameters:
				list	- ip list name
				source	- new source to add
				
        Returns:

=cut

# &setBLAddSource  ( $listName, $source );
sub setBLAddSource
{
	my ( $listName, $source ) = @_;
	my $type = &getBLParam( $listName, 'type' );

	my $ipset          = &getGlobalConfiguration( 'ipset' );
	my $blacklistsPath = &getGlobalConfiguration( 'blacklistsPath' );

	tie my @list, 'Tie::File', "$blacklistsPath/$listName.txt";
	push @list, $source;
	untie @list;

	my $error;
	if ( @{ &getBLParam( $listName, 'farms' ) } )
	{
		$error = system ( "$ipset add $listName $source 2>/dev/null" );
	}
	&zenlog( "$source was added to $listName" ) if ( !$error );
	return $error;
}

=begin nd
        Function: setBLModifSource

        Modify a source from a list

        Parameters:
				list	- ip list name
				id		- line to modificate
				source	- new value
				
        Returns:

=cut

# &setBLModifSource  ( $listName, $id, $source );
sub setBLModifSource
{
	my ( $listName, $id, $source ) = @_;
	my $type           = &getBLParam( $listName, 'type' );
	my $ipset          = &getGlobalConfiguration( 'ipset' );
	my $blacklistsPath = &getGlobalConfiguration( 'blacklistsPath' );
	my $err;

	tie my @list, 'Tie::File', "$blacklistsPath/$listName.txt";
	my $oldSource = splice @list, $id, 1, $source;
	untie @list;

	if ( @{ &getBLParam( $listName, 'farms' ) } )
	{
		$err = system ( "$ipset del $listName $oldSource 2>/dev/null" );
		$err = system ( "$ipset add $listName $source 2>/dev/null" ) if ( !$err );
	}
	&zenlog( "$oldSource was replaced for $source in the list $listName" )
	  if ( !$err );

	return $err;
}

#~ --------
farms:

# modificate iptables
#~ --------

=begin nd
        Function: getBLRules

        list all BL applied rules

        Parameters:
				
        Returns:
				@array  - BL applied rules 
				== 0	- error

=cut

# &getBLRules
sub getBLRules
{
	my @rlbRules;

	my @farms = &getFarmNameList;
	foreach my $farmName ( @farms )
	{
		my @rules = &getIptList( $farmName, 'raw', 'PREROUTING' );

		my $lineNum = 0;
		foreach my $rule ( @rules )
		{
			if ( $rule =~ /BL_/ )
			{
				push @rlbRules, $rule;
			}
		}
	}
	return \@rlbRules;
}

# &setBLCronTask ( $list );
sub setBLCronTask
{
	my ( $listName ) = @_;
	my $time;

	# default values
	$time->{ 'min' }   = '0';
	$time->{ 'hour' }  = '0';
	$time->{ 'dom' }   = '*';
	$time->{ 'month' } = '*';
	$time->{ 'dow' }   = '1';

	$time->{ 'min' } = &getBLParam( $listName, 'min' )
	  if ( &getBLParam( $listName, 'min' ) );
	$time->{ 'hour' } = &getBLParam( $listName, 'hour' )
	  if ( &getBLParam( $listName, 'hour' ) );
	$time->{ 'dom' } = &getBLParam( $listName, 'dom' )
	  if ( &getBLParam( $listName, 'dom' ) );
	$time->{ 'month' } = &getBLParam( $listName, 'month' )
	  if ( &getBLParam( $listName, 'month' ) );
	$time->{ 'dow' } = &getBLParam( $listName, 'dow' )
	  if ( &getBLParam( $listName, 'dow' ) );

	my $blacklistsCronFile = &getGlobalConfiguration( 'blacklistsCronFile' );

	# 0 0 * * 1	root	/usr/local/zenloadbalancer/app/zenrrd/zenrrd.pl &>/dev/null
	my $cmd =
	  "$time->{ 'min' } $time->{ 'hour' } $time->{ 'dom' } $time->{ 'month' } $time->{ 'dow' }\t"
	  . "root\t/usr/local/zenloadbalancer/www/Plugins/ipds/blacklists/updateRemoteList.pl $listName &>/dev/null";

	tie my @list, 'Tie::File', $blacklistsCronFile;

	# just exists this line, replace it
	if ( grep ( s/.* $listName .*/$cmd/, @list ) )
	{
		&zenlog( "update cron task for list $listName" );
	}
	else
	{
		push @list, $cmd;
	}
	untie @list;

	&zenlog( "Create a cron task for the list $listName" );
}

sub delBLCronTask
{
	my $listName           = shift;
	my $blacklistsCronFile = &getGlobalConfiguration( 'blacklistsCronFile' );

	tie my @list, 'Tie::File', $blacklistsCronFile;

	foreach my $line ( @list )
	{
		if ( $line =~ /\s$listName\s/ )
		{
			splice @list, $line, 1;
			last;
		}
	}

	untie @list;

	&zenlog( "Delete the task associated to the list $listName" );
}

sub getBLCronTask
{
	my $listName       = shift;
	my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );

	my $file = Config::Tiny->read( $blacklistsConf );
	my %conf = %{ $file->{ $listname } };

	return \%conf;
}

1;

