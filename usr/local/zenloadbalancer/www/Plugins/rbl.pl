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
require "/usr/local/zenloadbalancer/config/global.conf";


#~ ------ lists -------

# The lists will be always created and updated although these aren't used at the moment
# When a list is applied to a farm, a ip rule will be created with port and ip where farm is working.


=begin nd
        Function: getRBLGeolocationLists

        This function return all geolocation lists available or 
        the source list of ones of this

        Parameters:
        
				country		- this param is optional, with this param, the function return the 
										source list of lan segment for a counry
				
        Returns:

                array ref	- availabe counrties or source list
                
                
=cut
# if funtcion recive country, 	return the country list
# else 									return all country lists availabes
# &getRBLGeolocationLists ( country );
sub getRBLGeolocationLists
{
	my $countryList = shift;
	my $rblGeolocation = &getGlobalConfiguration( 'rblGeolocation' );
	my @geoLists;
	my @geoListsAux;
	my $output; 
		
	opendir ( DIR, "$rblGeolocation/" );
	my @geoLists = readdir ( DIR );
	closedir ( DIR );
	
	foreach my $list ( @geoLists )
	{
		if ( $list =~ s/.txt$// )
		{
			push @geoListsAux, $list;
		}
	}
	
	$output = \@geoListsAux;
	
	if ( defined $countryList )
	{
		my $fileName = "$rblGeolocation/$countryList.txt" ;
		
		if ( -e $fileName )
		{
			tie my @list, 'Tie::File', $fileName;
			@geoListsAux = @list;
			untie @list;
			$output = \@geoListsAux;
		}
		else
		{
			$output = -1;
		}
	}
	
	return $output;
}


=begin nd
        Function: setRBLCreateLocalList

        create a new local list. 
        Add:	new section to local_lists.conf with list configuration
        Create: ipset list
				list.txt	- where it saves IPs

        Parameters:
        
				$listName 	
				$type		- allow / deny	
				
        Returns:

                == 0	- successful
                != 0	- error
                
=cut
#	&setRBLCreateLocalList ( $listName, $type );
sub setRBLCreateLocalList
{
	my ( $listName, $type ) = @_;
	my $output;

	my $rblLocalConf  = &getGlobalConfiguration( 'rblLocalConf' );
	my $touch         = &getGlobalConfiguration( 'touch' );
	my $ipset         = &getGlobalConfiguration( 'ipset' );
	my $rblConfPath   = &getGlobalConfiguration( 'rblConfPath' );

	# create local_lists.conf if it doesn't exit
	if ( !-e $rblLocalConf )
	{
		system ( "$touch $rblLocalConf" );
		&zenlog( "Created $rblLocalConf file." );
	}

	# check if a list exists with same name
	my $fileHandle = Config::Tiny->read( $rblLocalConf );
	if ( &getRBLListLocalitation ( $listName ) != -1 )
	{
		&zenlog( "'$listName' list just exists" );
		return -1;
	}

	if ( $type ne 'deny' && $type ne 'allow' )
	{
		&zenlog(
			"Parameter 'type' only accpet 'allow | deny', in 'setRBLCreateLocalList' function."
		);
		$output = -1;
	}

	else
	{
		# add section to local lists conf
		my %aux = ( 'farms' => "", 'type' => "$type", 'action' => "" );
		if ( $type eq 'deny' )
		{
			$aux{ 'action' } = "DROP";
		}
		else
		{
			$aux{ 'action' } = "ACCEPT";
		}
		$fileHandle->{ $listName } = \%aux;
		$fileHandle->write( $rblLocalConf );

		#~ # create list.txt
		system ( "$touch $rblConfPath/${type}_lists/$listName.txt" );

		# create ipset rule
		my $output = system ( "$ipset create $listName hash:net" );
		&zenlog( "'$listName' list was created successful" );
	}

	return $output;
}

=begin nd
        Function: setRBLCreateLocalList

        create a new local list. 
        Add:	new section to local_lists.conf with list configuration
        Create: ipset list
				list.txt	- where it saves IPs

        Parameters:
        
				$listName 	
				$type		- allow / deny	
				
        Returns:

                == 0	- successful
                != 0	- error
                
=cut
#	&setRBLCreateGeolocationList ( $country, $type,  );
sub setRBLCreateGeolocationList
{
	my ( $listName, $type ) = @_;
	my $output;

	my $rblGeolocationConf  = &getGlobalConfiguration( 'rblGeolocationConf' );
	my $touch         = &getGlobalConfiguration( 'touch' );
	my $ipset         = &getGlobalConfiguration( 'ipset' );
	my $rblConfPath   = &getGlobalConfiguration( 'rblConfPath' );

	# create local_lists.conf if it doesn't exit
	if ( !-e $rblGeolocationConf )
	{
		system ( "$touch $rblGeolocationConf" );
		&zenlog( "Created $rblGeolocationConf file." );
	}

	# check if a list exists with same name
	my $fileHandle = Config::Tiny->read( $rblGeolocationConf );
	if ( &getRBLListLocalitation ( $listName ) != -1 )
	{
		&zenlog( "'$listName' list just exists" );
		return -1;
	}

	if ( $type ne 'deny' && $type ne 'allow' )
	{
		&zenlog(
			"Parameter 'type' only accpet 'allow | deny', in 'setRBLCreateLocalList' function."
		);
		$output = -1;
	}

	else
	{
		# add section to local lists conf
		my %aux = ( 'farms' => "", 'type' => "$type", 'action' => "" );
		if ( $type eq 'deny' )
		{
			$aux{ 'action' } = "DROP";
		}
		else
		{
			$aux{ 'action' } = "ACCEPT";
		}
		$fileHandle->{ $listName } = \%aux;
		$fileHandle->write( $rblGeolocationConf );

		# create ipset rule
		my $output = system ( "$ipset create $listName hash:net" );
		# fill list
		&setRBLRefreshList( $listName );
		
		&zenlog( "'$listName' list was created successful" );
	}

	return $output;
}





=begin nd
        Function: setRBLCreateRemoteList

        create a new remote
		Add:	new section to remote_lists.conf with list configuration
        Create: ipset list
        
        Remote lists will always be deny list
				
        Parameters:
        
				$listName 	
				url		- url where there is a IP list 
				type	- deny / allow 
				
        Returns:

                == 0	- successful
                != 0	- error
                
=cut

# &setRBLCreateRemoteList ( $name, $type, $url );
sub setRBLCreateRemoteList
{
	my ( $name, $type, $url ) = @_;
	my $output = -1;

	my $rblRemoteConf = &getGlobalConfiguration( 'rblRemoteConf' );
	my $touch         = &getGlobalConfiguration( 'touch' );
	my $ipset         = &getGlobalConfiguration( 'ipset' );

	if ( $type ne 'allow' && $type ne 'deny' )
	{
		return -1;
	}

	if ( !-e $rblRemoteConf )
	{
		system ( "$touch $rblRemoteConf" );
		&zenlog( "Created $rblRemoteConf file." );
	}

	my $fileHandle = Config::Tiny->read( $rblRemoteConf );
	if ( exists $fileHandle->{ $name } || exists $fileLocal->{ $name } )
	{
		&zenlog( "'$name' list just exists." );
	}
	else
	{

		$fileHandle->{ $name }->{ 'url' }    = $url;
		$fileHandle->{ $name }->{ 'status' } = "up";
		$fileHandle->{ $name }->{ 'farms' }  = "";
		$fileHandle->{ $name }->{ 'type' }   = $type;
		$fileHandle->write( $rblRemoteConf );
		$output = system ( "$ipset create $name hash:net" );
		if ( !$output )
		{
			$output = &setRBLRefreshList( $name );
		}
		&zenlog( "'$name' list was created successful." );
	}

	return $output;
}

=begin nd
        Function: setRBLDeleteList

        delete a list:
			ipset, local_lists | remote_lists and list file

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

	my $rblLocalConf  = &getGlobalConfiguration( 'rblLocalConf' );
	my $rblLocalConf  = &getGlobalConfiguration( 'rblGeolocationConf' );
	my $rblRemoteConf = &getGlobalConfiguration( 'rblRemoteConf' );
	my $ipset         = &getGlobalConfiguration( 'ipset' );
	my $rblConfPath   = &getGlobalConfiguration( 'rblConfPath' );
	my @farms         = &getFarmNameList;

	foreach my $farmName ( @farms )
	{
		my @rules = &getIptList( $farmName, 'raw', 'PREROUTING' );
		if ( grep /.+match-set $listName src .+RBL_$farmName/, @rules )
		{
			&zenlog( "Deleting $listName rules for farm $farmName" );
			my $error = &setRBLDeleteRule( $farmName, $listName );
			$output++ if ( $error != 0 );
		}
	}

	if ( !$output )
	{
		my $loc = &getRBLListLocalitation( $listName );

		# local list
		if ( $loc eq 'local' )
		{
			$fileHandle = Config::Tiny->read( $rblLocalConf );
			my $type = $fileHandle->{ $listName }->{ 'type' };

			# delete the list file
			system ( "rm $rblConfPath/${type}_lists/$listName.txt" );

			# delete from config file
			delete $fileHandle->{ $listName };
			$fileHandle->write( $rblLocalConf );
		}

		# local list
		elsif ( $loc eq 'geolocation' )
		{
			$fileHandle = Config::Tiny->read( $rblGeolocationConf );
			# delete from config file
			delete $fileHandle->{ $listName };
			$fileHandle->write( $rblGeolocationConf );
		}

		# remote list
		elsif ( $loc eq 'remote' )
		{
			$fileHandle = Config::Tiny->read( $rblRemoteConf );
			delete $fileHandle->{ $listName };
			$fileHandle->write( $rblRemoteConf );
		}

		# list doesn't find
		else
		{
			return -1;
		}
		$output = system ( "$ipset destroy $listName" );
		if ( $output != 0 )
		{
			&zenlog( "Error deleting list '$listName'." );
			$output = -1;
		}
		else
		{
			&zenlog( "List '$listName' was deleted successful." );
		}
	}

	return $output;
}

=begin nd
        Function: setRBLLocalListConfig

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

# &setRBLLocalListConfig ( $name , $key,  $value, $opt )
sub setRBLLocalListConfig
{
	my ( $name, $key, $value, $opt ) = @_;
	my $output;

	my $rblLocalConf = &getGlobalConfiguration( 'rblLocalConf' );
	my $fileHandle   = Config::Tiny->read( $rblLocalConf );

	# change name of url
	if ( 'name' eq $key )
	{
		my @listNames = &getRBLListNames;
		if ( grep ( /$value/, @listNames ) )
		{
			&zenlog( "List '$value' just exists." );
			$output = -1;
		}
		else
		{
			# get conf
			my @farmList = @{ &getRBLListParam( $name, 'farms' ) };
			my $ipList   = &getRBLIpList( $name );
			my $type     = $fileHandle->{ $name }->{ 'type' };

			# crete new list
			$output = &setRBLCreateLocalList( $value, $type );
			$output = &setRBLListParam( $value, 'list', $ipList );

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
		$output = &setRBLListParam( $name, 'list', $ipList );

		# apply rules to farms
		foreach my $farm ( @farmList )
		{
			$output = &setRBLCreateRule( $farm, $name );
		}
		return $output;
	}
	elsif ( 'list' eq $key )
	{
		&setRBLAddToList( $name, $value );
		&setRBLRefreshList( $name );
	}
	elsif ( 'farms' eq $key )
	{
		if ( $opt eq 'del' )
		{
			$fileHandle->{ $name }->{ $key } =~ s/(^| )$value( |$)/ /;
		}
		elsif ( $opt eq 'add' )
		{
			if ( $fileHandle->{ $name }->{ $key } !~ /(^| )$value( |$)/ )
			{
				my $farmList = $fileHandle->{ $name }->{ $key };
				$fileHandle->{ $name }->{ $key } = "$farmList $value";
			}
		}
		else
		{
			&zenlog(
				"Parameter 'farm' only accept 'add / del' options, in 'setRBLLocalListConfig' function."
			);
			$output = -1;
		}
	}
	else
	{
		&zenlog(
				 "Wrong parameter '$key' for key in 'setRBLLocalListConfig' function." );
		$output = -1;
	}
	$fileHandle->write( $rblLocalConf );

	return $output;
}


=begin nd
        Function: setRBLGeolocationListConfig

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

# &setRBLGeolocationListConfig ( $name , $key,  $value, $opt )
sub setRBLGeolocationListConfig
{
	my ( $name, $key, $value, $opt ) = @_;
	my $output;

	my $rblGeolocationConf = &getGlobalConfiguration( 'rblGeolocationConf' );
	my $fileHandle   = Config::Tiny->read( $rblGeolocationConf );

	if ( 'type' eq $key )
	{
		# get configuration
		my @farmList = @{ &getRBLListParam( $name, 'farms' ) };
		if ( $key eq 'deny' )
		{
			$fileHandle->{$name}->{'type'}=$key;
			$fileHandle->{$name}->{'action'}='DROP';
		}
		elsif ( $key eq 'allow' )
		{
			$fileHandle->{$name}->{'type'}=$key;
			$fileHandle->{$name}->{'action'}='ACCEPT';
		 }
		$fileHandle->write( $rblGeolocationConf );

		# apply rules to farms
		foreach my $farm ( @farmList )
		{
			&setRBLDeleteRule ( $farm, $name );
			$output = &setRBLCreateRule( $farm, $name );
		}
		return $output;
	}
	elsif ( 'farms' eq $key )
	{
		if ( $opt eq 'del' )
		{
			$fileHandle->{ $name }->{ $key } =~ s/(^| )$value( |$)/ /;
		}
		elsif ( $opt eq 'add' )
		{
			if ( $fileHandle->{ $name }->{ $key } !~ /(^| )$value( |$)/ )
			{
				my $farmList = $fileHandle->{ $name }->{ $key };
				$fileHandle->{ $name }->{ $key } = "$farmList $value";
			}
		}
		else
		{
			&zenlog(
				"Parameter 'farm' only accept 'add / del' options, in 'setRBLGeolocationListConfig' function."
			);
			$output = -1;
		}
		$fileHandle->write( $rblGeolocationConf );
	}
	else
	{
		&zenlog(
				 "Wrong parameter '$key' for key in 'setRBLGeolocationListConfig' function." );
		$output = -1;
	}

	return $output;
}

=begin nd
        Function: setRBLRemoteListConfig

				Modificate remote config file 

        Parameters:
        
				name	- list name
				key		- field to modificate
				value	- value for the field
				opt		- add / del		when key = farms

        Returns:
                0	- successful
                !=0	- error
                
=cut

# &setRBLRemoteListConfig ( $name , $key,  $value, $opt )
sub setRBLRemoteListConfig
{
	my ( $name, $key, $value, $opt ) = @_;
	my $output = 0;

	my $rblRemoteConf = &getGlobalConfiguration( 'rblRemoteConf' );
	my $fileHandle    = Config::Tiny->read( $rblRemoteConf );

	# change list name
	if ( 'name' eq $key )
	{
		my @farmList = @{ &getRBLListParam( $name, 'farms' ) };
		my $url      = $fileHandle->{ $name }->{ 'url' };
		my $type     = $fileHandle->{ $name }->{ 'type' };
		$output = &setRBLDeleteList( $name );
		$output = &setRBLCreateRemoteList( $value, $type, $url );
		foreach my $farm ( @farmList )
		{
			&setRBLCreateRule( $farm, $value );
		}
		return $output;
	}
	elsif ( 'farms' eq $key )
	{
		if ( $opt eq 'del' )
		{
			$fileHandle->{ $name }->{ $key } =~ s/(^| )$value( |$)/ /;
		}
		elsif ( $opt eq 'add' )
		{
			my $farmList = $fileHandle->{ $name }->{ $key };
			$fileHandle->{ $name }->{ $key } = "$farmList $value";
		}
		else
		{
			&zenlog(
				"Parameter 'farm' only accept 'add / del' options, in 'setRBLRemoteListConfig' function."
			);
			$output = -1;
		}
	}
	elsif ( 'status' eq $key
			&& ( $value ne 'up' && $value ne 'down' && $value ne 'dis' ) )
	{
		&zenlog(
			  "Wrong parameter 'value' to 'status' in 'setRBLRemoteListConfig' function." );
		$output = -1;
	}
	elsif ( 'status' eq $key )
	{
		$fileHandle->{ $name }->{ $key } = $value;
	}
	elsif ( 'type' eq $key )
	{
		my $url = $fileHandle->{ $name }->{ 'url' };
		my @farmList = @{ &getRBLListParam( $name, 'farms' ) };

		# delete list and all rules applied to farms
		$output = &setRBLDeleteList( $name );

		# crete new list
		$output = &setRBLCreateRemoteList( $name, $value, $url );

		# apply rules to farms
		foreach my $farm ( @farmList )
		{
			$output = &setRBLCreateRule( $farm, $name );
		}
		return $output;
	}
	elsif ( 'url' eq $key )
	{
		$fileHandle->{ $name }->{ $key } = $value;
		&setRBLRefreshList( $name );
	}
	else
	{
		&zenlog( "Wrong parameter 'key' in 'setRBLRemoteListConfig' function." );
		$output = -1;
	}
	$fileHandle->write( $rblRemoteConf );

	return $output;
}

=begin nd
        Function: setRBLListParam

				Modificate list config 

        Parameters:
        
				name	- section name
				key		- field to modificate
					- name	-> list name
					- farm	-> add or delete a asociated farm
					- url	-> modificate url ( only remote lists )
					- status-> modificate list status ( only remote lists )
					- list  -> modificate ip list ( only local lists )
					
				value	- value for the field
				opt		- add / del		when key = farm 

        Returns:
                0	- successful
                !=0	- error
                
=cut

# &setRBLListParam ( $listName, $key,  $value, $opt )
sub setRBLListParam
{
	my ( $listName, $key, $value, $opt ) = @_;
	my $output;
	my $file = &getRBLListLocalitation( $listName );
	my $fileHandle;

	if ( $file eq "local" )
	{
		$output = &setRBLLocalListConfig( $listName, $key, $value, $opt );
	}
	elsif ( $file eq "remote" )
	{
		$output = &setRBLRemoteListConfig( $listName, $key, $value, $opt );
	}
	elsif ( $file eq "geolocation" )
	{
		$output = &setRBLGeolocationListConfig( $listName, $key, $value, $opt );
	}
	else
	{
		$output = -1;
	}

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
				opt		- add / del		when key = farm 

        Returns:
                0	- successful
                !=0	- error
                
=cut	

# &getRBLListParam ( $listName, $key )
sub getRBLListParam
{
	my ( $listName, $key ) = @_;
	my $output;
	my $file = &getRBLListLocalitation( $listName );
	my $fileHandle;

	my $rblGeolocationConf  = &getGlobalConfiguration( 'rblGeolocationConf' );
	my $rblLocalConf  = &getGlobalConfiguration( 'rblLocalConf' );
	my $rblGeolocationConf  = &getGlobalConfiguration( 'rblGeolocationConf' );
	my $rblRemoteConf = &getGlobalConfiguration( 'rblRemoteConf' );

	if ( $key eq 'list' )
	{
		$output = &getRBLIpList( $listName );
	}
	elsif ( $file eq "local" )
	{
		$fileHandle = Config::Tiny->read( $rblLocalConf );
	}
	elsif ( $file eq "remote" )
	{
		$fileHandle = Config::Tiny->read( $rblRemoteConf );
	}
	elsif ( $file eq "geolocation" )
	{
		$fileHandle = Config::Tiny->read( $rblGeolocationConf );
	}
	else
	{
		&zenlog( "List '$listName' doesn't exist." );
		$output = -1;
	}

	if ( !$output )
	{
		$output = $fileHandle->{ $listName }->{ $key };
		if ( $key eq 'farms' )
		{
			my @farm = split ( ' ', $output );
			$output = \@farm;
		}
	}
	return $output;
}

=begin nd
        Function: getRBLListLocalitation

				get: local if the list is created by user
					 remote if the list is accesed through url

        Parameters:

				listName	

        Returns:

                local | remote | geolocation
                !=0	- error
                
=cut

# &getRBLListLocalitation ( $listName );
sub getRBLListLocalitation
{
	my ( $listName ) = @_;
	my $output = -1;

	my $rblLocalConf  = &getGlobalConfiguration( 'rblLocalConf' );
	my $rblRemoteConf = &getGlobalConfiguration( 'rblRemoteConf' );
	my $rblGeolocationConf = &getGlobalConfiguration( 'rblGeolocationConf' );

	my $fileLocal  = Config::Tiny->read( $rblLocalConf );
	my $fileRemote = Config::Tiny->read( $rblRemoteConf );
	my $fileGeolocation = Config::Tiny->read( $rblGeolocationConf );

	if ( exists $fileLocal->{ $listName } )
	{
		$output = "local";
	}
	elsif ( exists $fileRemote->{ $listName } )
	{
		$output = "remote";
	}
	elsif ( exists $fileGeolocation->{ $listName } ) 
	{
		$output = "geolocation";
	}
	else
	{
		$output = -1;
		&zenlog( "List '$listName' doesn't exist" );
	}

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
	my $ipListRef    = &getRBLIpList( $listName );
	my @ipList       = @{ $ipListRef };
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
        Function: getRBLListNames

        get all lists active

        Parameters:
        
        Returns:

                undef		- error
				@listNames	- all lists active
                
=cut

# &getRBLListNames
sub getRBLListNames
{
	my @listNames;
	my $ipset = &getGlobalConfiguration( 'ipset' );

	my @cmd = `$ipset list`;

	foreach my $line ( @cmd )
	{
		if ( $line =~ /Name: (.+)$/ )
		{
			push @listNames, $1;
		}
	}

	return \@listNames;
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

	my $rblLocalConf  = &getGlobalConfiguration( 'rblLocalConf' );
	my $rblRemoteConf = &getGlobalConfiguration( 'rblRemoteConf' );
	my $rblConfPath   = &getGlobalConfiguration( 'rblConfPath' );

	my $from          = &getRBLListLocalitation( $listName );
	my $source_format = &getValidFormat( 'rbl_source' );

	if ( $from eq 'remote' )
	{
		$fileHandle = Config::Tiny->read( $rblRemoteConf );

		my @ipList;

		if ( $fileHandle->{ $listName }->{ 'status' } ne 'dis' )
		{
			my $url = $fileHandle->{ $listName }->{ 'url' };
			my @web = `curl \"$url\"`;

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
				$fileHandle->{ $listName }->{ 'status' } = "down";
				&zenlog( "$url marked down" );
			}
			else
			{
				$fileHandle->{ $listName }->{ 'status' } = "up";
			}
		}
		$fileHandle->write( $rblRemoteConf );
		$output = \@ipList;
	}

	elsif ( $from eq 'local' )
	{
		$fileHandle = Config::Tiny->read( $rblLocalConf );
		my $type     = $fileHandle->{ $listName }->{ 'type' };
		my $fileList = "$rblConfPath/${type}_lists/$listName.txt";

		tie my @list, 'Tie::File', $fileList;
		@ipList = @list;
		untie @list;

		# ip list format wrong
		# get only correct format lines
		@ipList = grep ( /($source_format)/, @ipList );
		$output = \@ipList;
	}

	elsif ( $from eq 'geolocation' )
	{
		my $GeolocationPath  = &getGlobalConfiguration( 'rblGeolocation' );
		my $fileList = "$GeolocationPath/$listName.txt";
		
		tie my @list, 'Tie::File', $fileList;
		@ipList = @list;
		untie @list;

		# ip list format wrong
		# get only correct format lines
		@ipList = grep ( /($source_format)/, @ipList );
		$output = \@ipList;
	}


	return $output;
}


## NOT USED
=begin nd
        Function: getRBLCheckLocalLists

        Check if all local lists have list.txt where IPs are kept 

        Parameters:
        
        Returns:

                != 0 	- error
				==0 	- all lists active
                
=cut
#~ sub getRBLCheckLocalLists
#~ {
	#~ my $fileHandle = Config::Tiny->read( $rblLocalConf );
	#~ my %listConf   = %{ $fileHandle };
	#~ my $whLists    = 0;
	#~ my $blLists    = 0;

	#~ my $rblConfPath = &getGlobalConfiguration( 'rblConfPath' );

	#~ # check local config file and list directory are agree.
	#~ foreach my $listName ( keys %listConf )
	#~ {
		#~ if ( $fileHandle->{ $listName }->{ 'type' } eq 'allow' )
		#~ {
			#~ $whLists++;
		#~ }
		#~ else
		#~ {
			#~ $blLists++;
		#~ }
	#~ }

	#~ # check directory
	#~ $whListsTxt = `ls $rblConfPath/allow_lists/*.txt | wc -l`;
	#~ chop ( $whListsTxt );
	#~ $blListsTxt = `ls $rblConfPath/deny_lists/*.txt | wc -l`;
	#~ chop ( $blListsTxt );

	#compare both
	#~ if ( scalar $whListsTxt != $whLists )
	#~ {
		#~ &zenlog( "Configurations and number of allow lists don't agree." );
		#~ $output = -1;
	#~ }
	#~ if ( scalar $blListsTxt != $blLists )
	#~ {
		#~ &zenlog( "Configurations and number of deny lists don't agree." );
		#~ $output = -1;
	#~ }
#~ }



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
	my @lists = @{ &getRBLListNames };
	my $err;

	# update lists
	foreach my $listName ( @lists )
	{
		# get ip list
		my $ipList = &getRBLIpList( $listName );
		if ( $ipList == -1 )
		{
			$output++;
			&zenlog( "Error getting ip list for '$listName' list." );
			next;
		}

		# refresh list
		$err = &setRBLRefreshList( $listName );
		if ( $err != 0 )
		{
			$output++;
			&zenlog( "Error refreshing '$listName' list." );
		}
	}

	return $output;
}

#~ --------
#~ farms -> modificate iptables
#~ --------

=begin nd
        Function: setRBLCreateIptableCmd

        block / accept connections from a ip list for a determinate farm.

        Parameters:
				farmName - farm where rules will be applied
				list	 - ip list name
				action	 - list type: deny / allow
				
        Returns:
				$cmd	- Command
                -1		- error

=cut

# &setRBLCreateIptableCmd ( $farmName, $list, $action );
sub setRBLCreateIptableCmd
{
	my ( $farmName, $list, $action ) = @_;
	my $add;
	my $output;

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
		$output = &getGlobalConfiguration( 'iptables' )
		  . " $add PREROUTING -t raw -m set --match-set $list src $farmOpt -m comment --comment \"RBL_$farmName\"";
	}

	return $output;
}

=begin nd
        Function: setRBLCreateRule

        block / accept connections from a ip list for a determinate farm.

        Parameters:
				farmName - farm where rules will be applied
				list	 - ip list name
				
        Returns:
				== 0	- successful
                != 0	- error

=cut

# setRBLCreateRule  ( $farmName, $listName );
sub setRBLCreateRule
{
	my ( $farmName, $listName ) = @_;
	my $output;

	# create cmd
	my $action = &getRBLListParam( $listName, 'type' );

	my $cmd = &setRBLCreateIptableCmd( $farmName, $listName, $action );
	my $logMsg = "[Blocked by RBL rule]";

	if ( $action eq "deny" )
	{	
		$output = &setIPDSDropAndLog ( $cmd, $logMsg ); 
	}
	else
	{
		$output = &iptSystem( "$cmd -j ACCEPT" );
	}

	# mod configuration file
	if ( !$output )
	{
		&setRBLListParam( $listName, 'farms', $farmName, 'add' );
		&zenlog( "List '$listName' was applied to farm '$farmName'." );
	}

	return $output;
}

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
	my $output;

	# Get line number
	my @rules = &getIptList( $farmName, 'raw', 'PREROUTING' );

	my $lineNum = 0;
	foreach my $rule ( @rules )
	{
		if ( $rule =~ /^(\d+) .+match-set $listName src .+RBL_$farmName/ )
		{
			$lineNum = $1;
		}
	}
	if ( !$lineNum )
	{
		&zenlog( "Don't find rule for farm '$farmName' and list '$listName'." );
		return -1;
	}

	# Delete
	#	iptables -D PREROUTING -t raw 3
	my $cmd =
	  &getGlobalConfiguration( 'iptables' ) . " --table raw -D PREROUTING $lineNum";
	$output = &iptSystem( $cmd );

	# mod config file
	if ( !$output )
	{
		$output = &setRBLListParam( $listName, 'farms', $farmName, 'del' );
		if ( $output != 0 )
		{
			&zenlog( "Error deleting rule for farm '$farmName' and list '$listName'." );
		}
		else
		{
			&zenlog( "'$listName' rbl rule was deleted" );
		}
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
	my $rblConfPath = &getGlobalConfiguration( 'rblConfPath' );

	my $type = &getRBLListParam( $listName, 'type' );
	tie my @list, 'Tie::File', "$rblConfPath/${type}_lists/$listName.txt";
	@list = @{ $listRef };
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

	tie my @list, 'Tie::File', "$rblConfPath/${type}_lists/$listName.txt";
	my $source = splice @list, $id, 1;
	untie @list;

	my $err = system ( "$ipset del $listName $source" );
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

	tie my @list, 'Tie::File', "$rblConfPath/${type}_lists/$listName.txt";
	push @list, $source;
	untie @list;

	my $err = system ( "$ipset add $listName $source" );
	&zenlog( "$source added to $listName" ) if ( !$error );
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

	tie my @list, 'Tie::File', "$rblConfPath/${type}_lists/$listName.txt";
	my $oldSource = splice @list, $id, 1, $source;
	untie @list;

	$err = system ( "$ipset del $listName $oldSource" );
	$err = system ( "$ipset add $listName $source" ) if ( !$err );
	&zenlog( "$oldSource was modificated to $source in $listName list" )
	  if ( !$err );

	return $err;
}


=begin nd
        Function: setRBLStart

        Enable all rbl rules

        Parameters:
				
        Returns:

=cut
# &setRBLStart
sub setRBLStart
{
	my $rblRemoteConf = &getGlobalConfiguration( 'rblRemoteConf' );
	my $rblLocalConf = &getGlobalConfiguration( 'rblLocalConf' );
	my $rblLocalConf = &getGlobalConfiguration( 'rblGeolocationConf' );
	my $ipset = &getGlobalConfiguration( 'ipset' );
	my @rules = @{ &getRBLRules () };

	my $remLists = Config::Tiny->read( $rblRemoteConf );
	# load remote lists
	foreach my $list ( keys %{ $remLists } )
	{
		my $output = system ( "$ipset create $list hash:net" );
		my @farms = @{ &getRBLListParam ( $list, "farms" ) };
		foreach my $farm ( @farms )
		{
			if ( ! grep ( /^.+match-set $list src .+RBL_$farm/, @rules ) )
			{
				# create cmd
				my $action = &getRBLListParam( $list, 'type' );
			
				my $cmd = &setRBLCreateIptableCmd( $farm, $list, $action );
				$output = &iptSystem( $cmd );
			}
		}
	}

	my $localLists = Config::Tiny->read( $rblLocalConf );
	# load local lists
	foreach my $list ( keys %{ $localLists } )
	{
		my $output = system ( "$ipset create $list hash:net" );
		my @farms = @{ &getRBLListParam ( $list, "farms" ) };
		foreach my $farm ( @farms )
		{
			if ( ! grep ( /^.+match-set $list src .+RBL_$farm/, @rules ) )
			{
				# create cmd
				my $action = &getRBLListParam( $list, 'type' );
				
				my $cmd = &setRBLCreateIptableCmd( $farm, $list, $action );
				$output = &iptSystem( $cmd );

			}
		}
	}
	
	my $geolocationLists = Config::Tiny->read( $geolocationConf );
	# load geolocation lists
	foreach my $list ( keys %{ $geolocationLists } )
	{
		my $output = system ( "$ipset create $list hash:net" );
		my @farms = @{ &getRBLListParam ( $list, "farms" ) };
		foreach my $farm ( @farms )
		{
			if ( ! grep ( /^.+match-set $list src .+RBL_$farm/, @rules ) )
			{
				# create cmd
				my $action = &getRBLListParam( $list, 'type' );
				
				my $cmd = &setRBLCreateIptableCmd( $farm, $list, $action );
				$output = &iptSystem( $cmd );

			}
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
	my $rbl_list = &getValidFormat('rbl_list_name');
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
	
}


1;
