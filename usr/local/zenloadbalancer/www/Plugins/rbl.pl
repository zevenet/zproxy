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

require "/usr/local/zenloadbalancer/www/Plugins/ipds.pl";
require "/usr/local/zenloadbalancer/www/farms_functions.cgi";
require "/usr/local/zenloadbalancer/www/functions_ext.cgi";


actions:

#  &getRBLLoadList ( $listName );
sub getRBLLoadList
{
	my $listName = shift;
	my $ipset = &getGlobalConfiguration( 'ipset' );
	my $output = system ( "$ipset list $listName" );

	return $output;
}


# &setRBLRunList ( $listName );
sub setRBLRunList
{
	my $listName = shift;
	my $ipset = &getGlobalConfiguration( 'ipset' );
	my $output;
	$output = system ( "$ipset create $listName hash:net" );
	
	if ( !$output && &getRBLListParam( $listName, 'location' ) eq 'remote' )
	{
		$output = &setRBLDownloadRemoteList ( $listName ) ;
	}
	if ( !$output )
	{
		$output = &setRBLRefreshList ( $listName );
	}
	
	return $output;
}


#  &setRBLDestroyList ( $listName );
sub setRBLDestroyList
{
	my $listName = shift;
	my $ipset = &getGlobalConfiguration( 'ipset' );
	my $output = system ( "$ipset destroy $listName" );

	return $output;
}


=begin nd
        Function: setRBLStart

        Enable all rbl rules

        Parameters:
				
        Returns:

=cut
#  &setRBLStart
sub setRBLStart
{
	my $rblConf = &getGlobalConfiguration( 'rblConf' );
	my $ipset = &getGlobalConfiguration( 'ipset' );
	my @rules = @{ &getRBLRules () };

	# create list config if doesn't exist
	if ( !-e $rblConf )
	{
		system ( "$touch $rblConf" );
		&zenlog( "Created $rblConf file." );
	}

	# load preload lists
	&setRBLAddPreloadLists();
	
	my $allLists = Config::Tiny->read( $rblConf );

	# load lists
	foreach my $list ( keys %{ $allLists } )
	{
		my @farms = @{ &getRBLListParam ( $list, "farms" ) };
		if ( @farms )
		{
			&setRBLRunList ( $list );
		}
		# create cmd  for all farms where are applied the list
		foreach my $farm ( @farms )
		{
			&zenlog ("Creating rules for list ·$list and farm $farm.");
			&setRBLCreateRule  ( $farm, $list );
		}
	}
}


=begin nd
        Function: setRBLStop

        Disable all rbl rules
        
        Parameters:
				
        Returns:

=cut
# &setRBLStop
sub setRBLStop 
{
	my @rules = @{ &getRBLRules () };
	my $rbl_list = &getValidFormat('rbl_list');
	my $farm_name = &getValidFormat('farm_name');
	
	foreach my $rule ( @rules )
	{
		if ( $rule =~ /^(\d+) .+match-set $rbl_list src .+RBL_$farm_name/ )
		{
			my $cmd =
				&getGlobalConfiguration( 'iptables' ) . " --table raw -D PREROUTING $1";
			&iptSystem( $cmd );
		}
	}
	
	&setRBLDestroyList ( $listName );
	
}


=begin nd
        Function: setRBLCreateRule

        block / accept connections from a ip list for a determinate farm.

        Parameters:
				farmName - farm where rules will be applied
				list	 - ip list name
				action	 - list type: deny / allow
				
        Returns:
				$cmd	- Command
                -1		- error

=cut
# &setRBLCreateRule ( $farmName, $list );
sub setRBLCreateRule
{
	my ( $farmName, $listName ) = @_;
	my $add;
	my $cmd;
	my $output;
	my $logMsg = "[Blocked by RBL rule]";
	my $action = &getRBLListParam( $listName, 'type' );
	
	if ( $action eq "allow" )
	{
		$add    = "-I";

	}
	elsif ( $action eq "deny" )
	{
		$add    = "-A";
	}
	else
	{
		$output = -1;
		&zenlog( "Bad parameter 'action' in 'setRBLCreateIptableCmd' function." );
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

# 		iptables -A PREROUTING -t raw -m set --match-set wl_2 src -d 192.168.100.242 -p tcp --dport 80 -j DROP -m comment --comment "RBL_farmname"
		$cmd = &getGlobalConfiguration( 'iptables' )
		  . " $add PREROUTING -t raw -m set --match-set $listName src $farmOpt -m comment --comment \"RBL_$farmName\"";
	}

	if ( $action eq "deny" )
	{	
		$output = &setIPDSDropAndLog ( $cmd, $logMsg ); 
	}
	else
	{
		$output = &iptSystem( "$cmd -j ACCEPT" );
	}
	
	if ( !$output )
	{
		&zenlog( "List '$listName' was applied to farm '$farmName'." );
	}

	return $output;
}


=begin nd
        Function: setRBLDeleteRule

        Delete a iptables rule 

        Parameters:
				farmName - farm where rules will be applied
				list	 - ip list name
				
        Returns:
				== 0	- successful
                != 0	- error

=cut
# &setRBLDeleteRule ( $farmName, $listName )
sub setRBLDeleteRule
{
	my ( $farmName, $listName ) = @_;
	my $output = -1;

	# Get line number
	my @rules = &getIptList( $farmName, 'raw', 'PREROUTING' );
	@rules = grep ( /^(\d+) .+match-set $listName src .+RBL_$farmName/, @rules);

	my $lineNum = 0;
	$size = scalar @rules -1;
	for ( $size; $size >= 0; $size-- )
	{
		if ( $rules[ $size ] =~ /^(\d+) / )
		{
			$lineNum = $1;
			$output = 0;
			# Delete
			#	iptables -D PREROUTING -t raw 3
			my $cmd = &getGlobalConfiguration( 'iptables' ) . " --table raw -D PREROUTING $lineNum";
			&iptSystem( $cmd );
		}
	}

	if ( ! grep ( /^(\d+) .+match-set $listName src .+RBL_$farmName/, @rules) )
	{
		&zenlog( "Error deleting '$farmName' from the list '$listName'." );		
	}
	return $output;
}


# setRBLApplyToFarm ( $farmName, $list );
sub setRBLApplyToFarm 
{
	my ( $farmName, $listName ) =  @_;
	my $output;
	
	if ( !@{ &getRBLListParam ( $listName, 'farms' ) } )
	{
		$output = &setRBLRunList ( $listName );
	}
	if ( ! $output )
	{
		$output = &setRBLCreateRule ( $farmName, $listName ); 
	}
	if ( ! $output )
	{
		$output = &setRBLListParam( $listName, 'farms-add', $farmName );
	}
	return $output;
 }


# &setRBLRemFromFarm ( $farmName, $listName );
sub setRBLRemFromFarm 
{	
	my ( $farmName, $listName ) =  @_;
	my $output = &setRBLDeleteRule ( $farmName, $listName ); 
	if ( ! $output )
	{
		$output = &setRBLListParam( $listName, 'farms-del', $farmName );
	}

	# delete list if it isn't used
	if ( ! @{ &getRBLListParam ( $listName, 'farms' ) } )
	{
		&setRBLDestroyList ( $listName );
	}

	return $output;
 }



# -------------------
lists:
# The lists will be always created and updated although these aren't used at the moment
# When a list is applied to a farm, a ip rule will be created with port and ip where farm is working.
# -------------------

=begin nd
        Function: setRBLPreloadLists

        This function return all preload lists available or 
        the source list of ones of this

        Parameters:
        
				country		- this param is optional, with this param, the function return the 
										source list of lan segment for a counry
				
        Returns:

                array ref	- availabe counrties or source list
                
=cut
# &getRBLPreloadLists;
sub setRBLAddPreloadLists
{
	my $rblLocalPreload = &getGlobalConfiguration( 'rblLocalPreload' );
	my $rblRemotePreload = &getGlobalConfiguration( 'rblRemotePreload' );
	my $rblConf = &getGlobalConfiguration( 'rblConf' );
	my $rblListsPath =  &getGlobalConfiguration( 'rblListsPath' );
		
	# Local preload lists
	opendir ( DIR, "$rblLocalPreload/" );
	my @preloadLists = readdir ( DIR );
	closedir ( DIR );
	
	my $fileHandle = Config::Tiny->read( $rblConf );
	foreach my $list ( @preloadLists )
	{
		if ( $list =~ s/.txt$// )
		{
			# save lists
			if( ! exists $fileHandle->{ $list } )
			{
				my $listHash;
				$listHash->{ 'location' } = 'local';
				$listHash->{ 'preload' } = 'true';
	
				&setRBLCreateList ( $list, $listHash );
				&zenlog( "The preload list '$list' was created." ); 
			
				system ( "cp $rblLocalPreload/$list.txt $rblListsPath/$list.txt" );
				&zenlog( "The preload list '$list' was created." ); 
			}
			elsif ( $fileHandle->{ $list }->{ 'preload' } eq 'true' )
			{
				system ( "cp $rblLocalPreload/$list.txt $rblListsPath/$list.txt" );
				&zenlog( "The preload list '$list' was updated." ); 
			}
			else
			{
				&zenlog( "The preload list '$list' cannot load it because exists other list with same name." ); 
			}
		}
	}
		
	my $remoteFile = Config::Tiny->read( $rblRemotePreload );
	# Remote preload lists
	foreach my $list ( keys %{ $remoteFile } )
	{
		if ( ! exists $fileHandle->{ $list } )
		{
			my $listHash;
			$listHash->{ 'url' } = $remoteFile->{ $list }->{ 'url' };
			$listHash->{ 'location' } = $remoteFile->{ $list }->{ 'remote' };
			$listHash->{ 'preload' } = $remoteFile->{ $list }->{ 'preload' };

			&setRBLCreateList ( $list, $listHash );
			&zenlog( "The preload list '$list' was created." ); 
		}
		
		# Download lists and load it
		&setRBLDownloadRemoteList ( $list );
		&zenlog( "The preload list '$list' was update." ); 
	}
	
}


# $listParams = \ %paramsRef;
# &setRBLCreateList ( $listName, $paramsRef );
sub setRBLCreateList
{
	my $listName = shift;
	my $listParams = shift;
	my $def_refresh = 60*24;	# time for refresh (min)
	my $def_type = 'deny';
	my $def_preload = 'false';
	my $output;

	my $rblConf = &getGlobalConfiguration( 'rblConf' );
	my $rblListsPath   = &getGlobalConfiguration( 'rblListsPath' );
	my $touch         = &getGlobalConfiguration( 'touch' );
	my $location = $listParams->{ 'location' };
	
	if ( ! -e $rblConf )
	{
		$output = system ( "$touch $rblConf" );
		&zenlog ( "Created rbl configuration file." );
	}
	
	if ( $listParams->{ 'location' } eq 'remote' && ! exists $listParams->{ 'url' } )
	{
		&zenlog ( "Remote lists need url" );
		return -1;
	}	

	# share params
	my $fileHandle = Config::Tiny->read( $rblConf );
	$fileHandle->{ $listName }->{ 'location' } = $listParams->{ 'location' };
	$fileHandle->{ $listName }->{ 'farms' } = "";
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
	$fileHandle->write( $rblConf );
	
	# specific to remote lists
	if ( $location eq 'remote' )
	{
		&setRBLListParam ( $listName, 'url', $listParams->{ 'url' } );
		$def_refresh = $listParams->{'refresh'} 	if ( exists $listParams->{'refresh'} );
		&setRBLListParam ( $listName, 'refresh', $def_refresh );
		&setRBLDownloadRemoteList ( $listName );
	}
	# specific to local lists
	elsif ( $location eq 'local' )
	{
		$output = system ( "$touch $rblListsPath/$listName.txt" );
	}
	
	if ( ! $output )
	{
		&zenlog( "'$listName' list was created successful" );
	}

	return $output;
}


=begin nd
        Function: setRBLDeleteList

        delete a list from iptables, ipset and configuration file
			

        Parameters:
        
				$listName	- List to delete
        
        Returns:

                ==0	- successful
				!=0 - error
                
=cut
# &setRBLDeleteList ( $listName )
sub setRBLDeleteList
{
	my ( $listName ) = @_;
	my $fileHandle;
	my $output;
	my $error; 
	
	my $rblConf  = &getGlobalConfiguration( 'rblConf' );
	my $rblListsPath   = &getGlobalConfiguration( 'rblListsPath' );
	my $ipset         = &getGlobalConfiguration( 'ipset' );
	my @farms         = &getRBLListParam ( $listName, 'farms' );

	# delete associated farms
	foreach my $farmName ( @farms )
	{
		&setRBLDeleteRule ( $farmName, $listName )
	}

	if ( &getRBLListParam( $listName, 'preload' ) eq 'false' )
	{
		# delete from config file
		$fileHandle = Config::Tiny->read( $rblConf );
		delete $fileHandle->{ $listName };
		$fileHandle->write( $rblConf );
	
		system ( "rm $rblListsPath/$listName.txt" );
	}

	# delete list from ipset
	$output = &setRBLDestroyList ( $listName );
	if ( $output != 0 )
	{
		&zenlog( "Error  deleting list '$listName'." );
		$output = -1;
	}
	else
	{
		&zenlog( "List '$listName' was deleted successful." );
	}

	return $output;
}

=begin nd
        Function: setRBLListParam

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
# &setRBLListParam ( $name , $key,  $value )
sub setRBLListParam
{
	my ( $name, $key, $value ) = @_;
	my $output;

	my $rblConf = &getGlobalConfiguration( 'rblConf' );
	my $fileHandle   = Config::Tiny->read( $rblConf );

	# change name of the list
	if ( 'name' eq $key )
	{
		my @listNames = keys %{ $fileHandle };
		if ( ! &getRBLExists ( $listName ) )
		{
			&zenlog( "List '$value' just exists." );
			$output = -1;
		}
		else
		{
			# get conf
			my @farmList = @{ &getRBLListParam( $name, 'farms' ) };
			my $ipList   = &getRBLListParam( $name, 'sources' );
			my $hashParams;
			$hashParams->{ 'type' } = &getRBLListParam( $name, 'type' ) ;
			$hashParams->{ 'location' } = &getRBLListParam( $name, 'location' ) ;
			if ( &getRBLListParam( $name, 'location' ) eq 'remote' )
			{
				$hashParams->{ 'url' } = &getRBLListParam( $name, 'url' );
				$hashParams->{ 'refresh' } = &getRBLListParam( $name, 'refresh' );
			}

			# crete new list
			$output = &setRBLCreateLocalList( $value, \%hashParams );
			$output = &setRBLListParam( $value, 'sources', $ipList );

			# delete list and all rules applied to farms
			$output = &setRBLDeleteList( $name );

			# apply rules to farms
			foreach my $farm ( @farmList )
			{
				&setRBLCreateRule( $farm, $value );
			}
			return $output;
		}
	}
	elsif ( 'type' eq $key )
	{
		# get configuration
		my @farmList = @{ &getRBLListParam( $name, 'farms' ) };
		my $ipList = &getRBLIpList( $name );

		# delete list and all rules applied to farms
		$output = &setRBLDeleteList( $name );

		# crete new list
		$output = &setRBLCreateLocalList( $name, $value );
		$output = &setRBLListParam( $name, 'sources', $ipList );

		# apply rules to farms
		foreach my $farm ( @farmList )
		{
			$output = &setRBLCreateRule( $farm, $name );
		}
		return $output;
	}
	elsif ( 'sources' eq $key )
	{
		# only can be modificated local lists not preloaded
		if ( &getRBLListParam( $listName, 'location' ) eq 'local' && &getRBLListParam( $listName, 'preload' ) eq 'false' )
		{
			&setRBLAddToList( $name, $value );
			&setRBLRefreshList( $name );
		}
	}
	elsif ( 'farms-add' eq $key )
	{
		if ( $fileHandle->{ $name }->{ $key } !~ /(^| )$value( |$)/ )
		{
			my $farmList = $fileHandle->{ $name }->{ 'farms' };
			$fileHandle->{ $name }->{ 'farms' } = "$farmList $value";
		}
	}
	elsif ( 'farms-del' eq $key )
	{
		$fileHandle->{ $name }->{ 'farms' } =~ s/(^| )$value( |$)/ /;
	}
	elsif ( 'status' eq $key
			&& ( $value ne 'up' && $value ne 'down' && $value ne 'dis' ) )
	{
		&zenlog(
			  "Wrong parameter 'value' to 'status' in 'setRBLRemoteListConfig' function." );
		$output = -1;
	}
	# other value  of the file conf
	else
	{
		$fileHandle->{ $name }->{ $key } = $value;
	}
	$fileHandle->write( $rblConf );

	return $output;
}


=begin nd
        Function: getRBLListParam

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
# &getRBLListParam ( $listName, $key )
sub getRBLListParam
{
	my ( $listName, $key ) = @_;
	my $output;
	my $fileHandle;

	my $rblConf = &getGlobalConfiguration( 'rblConf' );
	$fileHandle = Config::Tiny->read( $rblConf );
	
	if ( ! $key ) 
	{
		$output = $fileHandle->{ $listName };
		$output->{ 'list' } =  $listName;
		$output->{ 'sources' } = &getRBLIpList( $listName );
	}
	elsif ( $key eq 'sources' )
	{
		$output = &getRBLIpList( $listName );
	}
	else 
	{
		if ( exists $fileHandle->{ $listName } )
		{
			$output = $fileHandle->{ $listName }->{ $key };
			if ( $key eq 'farms' )
			{
				my @aux = split( ' ', $output );
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
        Function: getRBLExists

		get if a list exists o all available lists

        Parameters:

				listName	-	return 0 if list exists
				no param	-	return a ref array of all available lists

        Returns:

                0   - list exists
                -1  - list doesn't exist
                
=cut
# &getRBLExists ( $listName );
sub getRBLExists
{
	my $listName = shift;
	my $output = -1;
	my $rblConf = &getGlobalConfiguration( 'rblConf' );
	my $fileHandle = Config::Tiny->read( $rblConf );
	my @aux;
	
	if ( $listName )
	{
		$output = 0 if ( exists $fileHandle->{ $listName } );
	}
	else
	{
		@aux = keys %{ $fileHandle };
		$output = \@aux;
	}
	
	return $output;
}


=begin nd
        Function: getRBLIpList

		Download a list from url and keep it in file

        Parameters:
        
                listName 

        Returns:
                
=cut
# &setRBLDownloadRemoteList ( $listName );
sub setRBLDownloadRemoteList
{
	my ( $listName ) = @_;
	my $url = &getRBLListParam ( $listName, 'url' ); 
	
	# if ( $fileHandle->{ $listName }->{ 'status' } ne 'dis' )
	my @web = `curl \"$url\"`;
	my $source_format = &getValidFormat( 'rbl_source' );

	foreach my $line ( @web )
	{
		if ( $line =~ /($source_format)/ )
		{
			push @ipList, $1;
		}
	}
	# set URL down if it doesn't have any ip
	if ( ! @ipList )
	{
		&setRBLListParam ( $listName, 'status', 'down' );
		&zenlog( "$url marked down" );
	}
	else
	{
		my $path = &getGlobalConfiguration ( 'rblListsPath' );
		my $fileList = "$path/$listName.txt";
		tie my @list, 'Tie::File', $fileList;
		@list = @ipList;
		untie @list;
		&setRBLListParam ( $listName, 'status', 'up' );
	}
	
}


=begin nd
        Function: getRBLIpList

				get list of IPs from a local or remote list

        Parameters:
        
                listName - local listname / remote url, where find list of IPs

        Returns:
                -1		 	- error
                \@ipList	- successful
                
=cut
# &getRBLIpList ( $listName )
sub getRBLIpList
{
	my ( $listName ) = @_;
	my @ipList;
	my $output = -1;
	my $fileHandle;

	my $rblPath   = &getGlobalConfiguration( 'rblListsPath' );
	my $source_format = &getValidFormat( 'rbl_source' );

	#~ my $fileList = "$PreloadPath/$listName.txt";
	
	tie my @list, 'Tie::File', "$rblPath/$listName.txt";
	@ipList = @list;
	untie @list;

	# ip list format wrong
	# get only correct format lines
	@ipList = grep ( /($source_format)/, @ipList );
	$output = \@ipList;

	return $output;
}


=begin nd
        Function: setRBLRefreshList

        Update IPs from a list

        Parameters:
        
				$listName 	
				
        Returns:

                == 0	- successful
                != 0	- error
                
=cut
#	&setRBLRefreshList ( $listName )
sub setRBLRefreshList
{
	my ( $listName ) = @_;
	my @ipList = @{ &getRBLIpList( $listName ) };
	my $output;
	my $ipset = &getGlobalConfiguration( 'ipset' );

	&zenlog( "refreshing '$listName'... " );
	$ouput = system ( "$ipset flush $listName" );
	if ( !$output )
	{
		foreach my $ip ( @ipList )
		{
			$output = system ( "$ipset add $listName $ip" );
		}
	}
	return $output;
}


=begin nd
        Function: setRBLRefreshAllLists

				Check if config file data and list directories are coherent
				Refresh all lists, locals and remotes.
				
        Parameters:
        
        Returns:
                0	- successful
                !=0	- error in some list 
                
=cut				
# &setRBLRefreshAllLists
sub setRBLRefreshAllLists
{
	my $output;
	my @lists = @{ &getRBLExists };

	# update lists
	foreach my $listName ( @lists )
	{
		# Download the remote lists 
		if ( &getRBLListParam ( $listName, 'location' ) eq 'remote' )
		{
			&setRBLDownloadRemoteList ( $listName );
		}
		# Refresh list if is running 
		if ( &getRBLLoadList ( $listName ) )
		{
			&setRBLRefreshList ( $listName );
		}
		&zenlog( "The preload list '$list' was update." ); 
	}
	return $output;
}


=begin nd
        Function: setRBLAddToList

		Change ip list for a list

        Parameters:
				listName
				listRef	 - ref to ip list
				
        Returns:

=cut			
# &setRBLAddToList  ( $listName, \@ipList );
sub setRBLAddToList
{
	my ( $listName, $listRef ) = @_;
	my $rblPath = &getGlobalConfiguration( 'rblListsPath' );
	my $source_format = &getValidFormat ('rbl_source');
	my @ipList = grep ( /$source_format/,	@{ $listRef } );

	tie my @list, 'Tie::File', "$rblListsPath/$listName.txt";
	@list = @ipList;
	untie @list;
	&zenlog( "IPs of '$listName' was modificated." );
}


=begin nd
        Function: setRBLDeleteSource

        Delete a source from a list

        Parameters:
				list	- ip list name
				id		- line to delete
				
        Returns:

=cut
# &setRBLDeleteSource  ( $listName, $id );
sub setRBLDeleteSource
{
	my ( $listName, $id ) = @_;
	my $type = &getRBLListParam( $listName, 'type' );

	my $ipset       = &getGlobalConfiguration( 'ipset' );
	my $rblConfPath = &getGlobalConfiguration( 'rblConfPath' );

	tie my @list, 'Tie::File', "$rblListsPath/$listName.txt";
	my $source = splice @list, $id, 1;
	untie @list;

	my $err;
	if ( @{ &getRBLListParam( $listName, 'farms' ) } )
	{
		$err = system ( "$ipset del $listName $source" );
	}
	&zenlog( "$source deleted from $listName" ) if ( !$err );

	return $err;
}


=begin nd
        Function: setRBLAddSource

        Add a source from a list

        Parameters:
				list	- ip list name
				source	- new source to add
				
        Returns:

=cut
# &setRBLAddSource  ( $listName, $source );
sub setRBLAddSource
{
	my ( $listName, $source ) = @_;
	my $type = &getRBLListParam( $listName, 'type' );

	my $ipset       = &getGlobalConfiguration( 'ipset' );
	my $rblConfPath = &getGlobalConfiguration( 'rblConfPath' );

	my $ipset       = &getGlobalConfiguration( 'ipset' );
	my $rblConfPath = &getGlobalConfiguration( 'rblConfPath' );

	tie my @list, 'Tie::File', "$rblListsPath/$listName.txt";
	push @list, $source;
	untie @list;

	my $error;
	if ( @{ &getRBLListParam( $listName, 'farms' ) } )
	{
		$error = system ( "$ipset add $listName $source" );
	}
	&zenlog( "$source added to $listName" ) if ( ! $error );
	return $error;
}


=begin nd
        Function: setRBLModifSource

        Modify a source from a list

        Parameters:
				list	- ip list name
				id		- line to modificate
				source	- new value
				
        Returns:

=cut
# &setRBLModifSource  ( $listName, $id, $source );
sub setRBLModifSource
{
	my ( $listName, $id, $source ) = @_;
	my $type        = &getRBLListParam( $listName, 'type' );
	my $ipset       = &getGlobalConfiguration( 'ipset' );
	my $rblConfPath = &getGlobalConfiguration( 'rblConfPath' );

	my $err;

	tie my @list, 'Tie::File', "$rblListsPath/$listName.txt";
	my $oldSource = splice @list, $id, 1, $source;
	untie @list;

	if ( @{ &getRBLListParam( $listName, 'farms' ) } )
	{
		$err = system ( "$ipset del $listName $oldSource" );
		$err = system ( "$ipset add $listName $source" ) if ( !$err );
	}
	&zenlog( "$oldSource was modificated to $source in $listName list" )
	  if ( !$err );

	return $err;
}



#~ --------
farms:		
# modificate iptables
#~ --------

=begin nd
        Function: getRBLRules

        list all RBL applied rules

        Parameters:
				
        Returns:
				@array  - RBL applied rules 
				== 0	- error

=cut
# &getRBLRules
sub getRBLRules
{
	my @rlbRules;

	my @farms = &getFarmNameList;
	foreach my $farmName ( @farms )
	{
		my @rules = &getIptList( $farmName, 'raw', 'PREROUTING' );

		my $lineNum = 0;
		foreach my $rule ( @rules )
		{
			if ( $rule =~ /RBL_/ )
			{
				push @rlbRules, $rule;
			}
		}
	}
	return \@rlbRules;
}

1;
