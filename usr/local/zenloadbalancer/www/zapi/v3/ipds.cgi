#!/usr/bin/perl 

##############################################################################
#
#     This file is part of the Zen Load Balancer Enterprise Edition software
#     package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This file cannot be distributed, released in public domain and/or for
#     commercial purposes.
#
###############################################################################

require "/usr/local/zenloadbalancer/www/Plugins/blacklists.cgi";
require "/usr/local/zenloadbalancer/www/Plugins/dos.cgi";

use warnings;
use strict;

blacklists:

# GET /ipds/blacklists
sub get_blacklists_all_lists
{
	my $listNames   = &getBLExists();
	my $description = "Get black lists";
	my @lists;
	foreach my $list ( @{ $listNames } )
	{
		my %listHash = (
						 name     => $list,
						 farms    => &getBLParam( $list, 'farms' ),
						 policy     => &getBLParam( $list, 'policy' ),
						 type => &getBLParam( $list, "type" ),
						 preload => &getBLParam( $list, "preload" )
		);
		push @lists, \%listHash;
	}

	&httpResponse(
		  { code => 200, body => { description => $description, params => \@lists } } );
}


#GET /ipds/blacklists/<listname>
sub get_blacklists_list
{
	my $listName    = shift;
	my $description = "Get list $listName";
	my $errormsg;
	
	if ( !&getBLExists( $listName ) )
	{
		my $listHash = &getBLzapi ( $listName );
		
		&httpResponse(
			  { code => 200, body => { description => $description, params => $listHash } }
		);
	}
	else
	{
		$errormsg = "Requested list doesn't exist.";
		my $body =
		  { description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 400, body => $body } );
	}

}

#  POST /ipds/blacklists
sub add_blacklists_list
{
	my $json_obj = shift;
	my $errormsg;
	my $listParams;
	my $listName    = $json_obj->{ 'name' };
	my $description = "Create a blacklist.";

	my @requiredParams = ( "name", "type" );
	my @optionalParams = ( "policy", "url" );

	$errormsg = &getValidReqParams( $json_obj, \@requiredParams, \@optionalParams );

	# $errormsg == 0, no error
	if ( !$errormsg )
	{
		# A list with this name just exist
		if ( &getBLExists( $listName ) != -1 )
		{
			$errormsg = "A list with name '$listName' just exists.";
		}

		# Check key format
		foreach my $key ( keys %$json_obj )
		{
			if ( !&getValidFormat( "blacklists_$key", $json_obj->{ $key } ) )
			{
				$errormsg = "$key hasn't a correct format.";
				last;
			}
		}
		if ( !$errormsg )
		{
			if ( !$errormsg && exists $json_obj->{ 'url' } )
			{
				if ( $json_obj->{ 'type' } ne 'remote' )
				{
					$errormsg = "Url only is available in remote lists.";
				}
				else
				{
					$listParams->{ 'url' } = $json_obj->{ 'url' };
				}
			}
			else
			{
				if ( $json_obj->{ 'type' } eq 'remote' )
				{
					$errormsg = "It's necessary to add the url where is allocated the list.";
				}
			}

			if ( !$errormsg )
			{
				$listParams->{ 'type' } = $json_obj->{ 'type' };
				$listParams->{ 'policy' }     = $json_obj->{ 'policy' }
				  if ( exists $json_obj->{ 'policy' } );

				if ( &setBLCreateList( $listName, $listParams ) )
				{
					$errormsg = "Error, creating a new list.";
				}

				# All successful
				else
				{
					my $listHash = &getBLParam( $listName );
					delete $listHash->{ 'source' };
					#~ delete $listHash->{ 'preload' };
					&httpResponse(
								{
								  code => 200,
								  body => { description => "Post list $listName", params => $listHash }
								}
					);
				}
			}
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg,
	};
	&httpResponse( { code => 400, body => $body } );
}

#  PUT /ipds/blacklists/<listname>
sub set_blacklists_list
{
	my $json_obj    = shift;
	my $listName    = shift;
	my $description = "Modify list $listName.";
	my $errormsg;

	# remove time hash and add its param to common configuration hash
	foreach my $timeParameters ( ( 'period', 'unit', 'hour', 'minutes' ) )
	{
		if ( exists $json_obj->{ 'time' }->{ $timeParameters } )
		{
			$json_obj->{ $timeParameters } = $json_obj->{ 'time' }->{ $timeParameters };
		}
	} 	
	delete $json_obj->{ 'time' };
	
	my @allowParams =
	  ( "policy", "url", "source", "name", "minutes", "hour", "day", "frequency", "frequency_type", "period", "unit" );

	if ( &getBLExists( $listName ) == -1 )
	{
		$errormsg = "The list '$listName' doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}
	
	elsif ( &getBLParam( $listName, 'preload' ) eq 'true' )
	{
		$errormsg = &getValidOptParams( $json_obj, [ "policy" ] );
		$errormsg = "In preload lists only is allowed to change the policy" if ( $errormsg );
	}

	my $type = &getBLParam( $listName, 'type' );
	$errormsg = &getValidOptParams( $json_obj, \@allowParams );
	if ( !$errormsg )
	{
		# Check key format
		foreach my $key ( keys %{ $json_obj } )
		{
			next if ( $key eq 'source' );
			if ( !&getValidFormat( "blacklists_$key", $json_obj->{ $key } ) )
			{
				$errormsg = "$key hasn't a correct format.";
				last;
			}
		}
		if ( !$errormsg )
		{
			# Cron params and url only is used in remote lists
			if ( $type ne 'remote' )
			{
				if ( grep ( /^(url|minutes|hour|day|frequency|frequency_type|period|unit)$/ , keys %{ $json_obj } ) )
				#~ if ( ! &getValidOptParams( $json_obj, [ "url", "minutes", "hour", "day", "frequency", "frequency_type", "period", "unit" ] ) )
				{ 
					$errormsg = "Error, trying to change a remote list parameter in a local list.";
				}
			}

			# Sources only is used in local lists
			if ( exists $json_obj->{ 'sources' }
					&& $type ne 'local' )
			{
				$errormsg = "Source parameter only is available in local lists.";
			}
			if ( !$errormsg )
			{
				my $cronFlag;
				
				# if there is a new update time configuration to remote lists, delete old configuration
				#checking available configurations
				if ( grep ( /^(minutes|hour|day|frequency|frequency_type|period|unit)$/ , keys %{ $json_obj } ) )
				{				
					$json_obj->{ 'frequency' } 	||=&getBLParam ( $listName, "frequency" );
					
					if ( $json_obj->{ 'frequency' } eq 'daily' )
					{
						$json_obj->{ 'frequency_type' }	||= &getBLParam ( $listName, "frequency_type" );
						if ( $json_obj->{ 'frequency_type' } eq 'period' )
						{
							$json_obj->{ 'period' } =&getBLParam ( $listName, "period" ) if ( ! exists $json_obj->{ 'period' } );
							$json_obj->{ 'unit' } 	=&getBLParam ( $listName, "unit" ) if ( ! exists $json_obj->{ 'unit' } );
							foreach my $timeParam ( "period", "unit" )
							{
								if ( ! &getValidFormat( "blacklists_$timeParam", $json_obj->{ $timeParam } ) || $json_obj->{ $timeParam } eq '' )
								{
									$errormsg = "$timeParam parameter missing to $json_obj->{ frequency } configuration.";
									last; 	
								}
							}
							if ( ! $errormsg )
							{
								&delBLParam ( $listName, $_ ) for ( "minutes", "hour", "day" );
								# rewrite cron task if exists some of the next keys
								$cronFlag = 1;
							}
						}
						elsif ( $json_obj->{ 'frequency_type' } eq 'exact' )
						{
							$json_obj->{ 'minutes' } =&getBLParam ( $listName, "minutes" ) if ( ! exists $json_obj->{ 'minutes' } );
							$json_obj->{ 'hour' } 		=&getBLParam ( $listName, "hour" ) if ( ! exists $json_obj->{ 'hour' } );
							foreach my $timeParam ( "minutes", "hour" )
							{
								if ( ! &getValidFormat( "blacklists_$timeParam", $json_obj->{ $timeParam } ) || $json_obj->{ $timeParam } eq '' )
								{
									$errormsg = "$timeParam parameter missing to $json_obj->{ frequency } configuration.";
									last;
								}
							}
							if ( ! $errormsg )
							{
								&delBLParam ( $listName, $_ ) for ( "unit", "period", "day" );
								# rewrite cron task if exists some of the next keys
								$cronFlag = 1;
							}
						}
						else
						{
							$errormsg = "It's neccessary indicate frequency type for daily frequency.";
						}
					}
					elsif ( $json_obj->{ 'frequency' } eq 'weekly'  )
					{
						$json_obj->{ 'minutes' } =&getBLParam ( $listName, "minutes" ) if ( ! exists $json_obj->{ 'minutes' } ); 
						$json_obj->{ 'hour' } 		=&getBLParam ( $listName, "hour" ) if ( ! exists $json_obj->{ 'hour' } );
						$json_obj->{ 'day' } 		=&getBLParam ( $listName, "day" ) if ( ! exists $json_obj->{ 'day' } );
						foreach my $timeParam ( "minutes", "hour", "day" )
						{
							if ( ! &getValidFormat( "blacklists_$timeParam", $json_obj->{ $timeParam } ) || $json_obj->{ $timeParam } eq '' )
							{
								$errormsg = "$timeParam parameter missing to $json_obj->{ frequency } configuration.";
								last;
							}
						}
						if ( ! &getValidFormat ('weekdays', $json_obj->{ 'day' }) )
						{
							$errormsg = "Error value of day parameter in $json_obj->{ 'frequency' } frequency."; 
						}
						if ( ! $errormsg )
						{
							&delBLParam ( $listName, $_ ) for ( "frequency_type", "period", "unit" );
							# rewrite cron task if exists some of the next keys
							$cronFlag = 1;
						}
					}
					elsif ( $json_obj->{ 'frequency' } eq 'monthly' )
					{
						$json_obj->{ 'minutes' }=&getBLParam ( $listName, "minutes" ) if ( ! exists $json_obj->{ 'minutes' } );
						$json_obj->{ 'hour' } 	=&getBLParam ( $listName, "hour" ) if ( ! exists $json_obj->{ 'hour' } );
						$json_obj->{ 'day' }	=&getBLParam ( $listName, "day" ) + 0 if ( ! exists $json_obj->{ 'day' } );  # number format
						# check if exists all paramameters
						foreach my $timeParam ( "hour","minutes", "day" )
						{
							if ( ! &getValidFormat( "blacklists_$timeParam", $json_obj->{ $timeParam } ) || $json_obj->{ $timeParam } eq '' )
							{
								$errormsg = "$timeParam parameter missing to $json_obj->{ frequency } configuration.";
								last;
							}
						}
						if ( ! &getValidFormat ('day_of_month', $json_obj->{ 'day' }) )
						{
							$errormsg = "Error value of day parameter in $json_obj->{ 'frequency' } frequency."; 
						}
						if ( ! $errormsg )
						{
							&delBLParam ( $listName, $_ ) for ( "unit", "period", "frequency_type" );
							# rewrite cron task if exists some of the next keys
							$cronFlag = 1;
						}
					}
					else
					{
						$errormsg = "Error with update configuration parameters.";
					}
				}

				if ( !$errormsg )
				{
					my $source_format = &getValidFormat( 'blacklists_source' );
					
					foreach my $key ( keys %{ $json_obj } )
					{
						# add only the sources with a correct format
						# no correct format sources are ignored
						if ( $key eq 'sources' )
						{
							my $noPush = grep ( !/^$source_format$/, @{ $json_obj->{ 'sources' } } );
	
							# error
							&zenlog( "$noPush sources couldn't be added" ) if ( $noPush );
						}
						# set params
						$errormsg = &setBLParam( $listName, $key, $json_obj->{ $key } );
	
						# once changed list, update de list name
						if ( $key eq 'name' )
						{
							$listName = $json_obj->{ 'name' };
						}
	
						# not continue if there was a error
						if ( $errormsg )
						{
							$errormsg = "Error, modifying $key in $listName.";
							last;
						}
					}

					if ( !$errormsg )
					{
						if ( $cronFlag && @{ &getBLParam( $listName, 'farms' ) } )
						{
							&setBLCronTask( $listName );
						}
			
						# all successful
						my $listHash = &getBLzapi( $listName );
						delete $listHash->{ 'sources' };
						delete $listHash->{ 'farms' };
						
						my $body = { description => $description, params => $listHash };
						&httpResponse({ code => 200, body => $body } );
					}
				}
			}
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg,
	};
	&httpResponse( { code => 400, body => $body } );
}

#  DELETE /ipds/blacklists/<listname> Delete a Farm
sub del_blacklists_list
{
	my $listName    = shift;
	my $description = "Delete list '$listName'",

	my $errormsg = &getBLExists( $listName );
	if ( $errormsg == -1 )
	{
		$errormsg = "$listName doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( @{ &getBLParam ($listName, 'farms' ) }  )
	{
		$errormsg = "Delete this list from all farms before than delete it.";
	}
	else
	{
		$errormsg = &setBLDeleteList( $listName );
		if ( !$errormsg )
		{
			$errormsg = "The list $listName has been deleted successful.";
			my $body = {
						 description => $description,
						 success  => "true",
						 message     => $errormsg,
			};
			&httpResponse( { code => 200, body => $body } );
		}
		else
		{
			$errormsg = "Error, deleting the list $listName.";
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg,
	};
	&httpResponse( { code => 400, body => $body } );
}

# POST /ipds/blacklists/BLACKLIST/actions 	update a remote blacklist
sub update_remote_blacklists
{
	my $json_obj    = shift;
	my $listName    = shift;
	my $description = "Update a remote list";


	my $errormsg = &getBLExists( $listName );
	if ( $errormsg == -1 )
	{
		$errormsg = "$listName doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( &getBLParam ( $listName, 'type' ) ne 'remote' )
	{
		$errormsg = "Error, only remote lists can be updated.";
	}
	else
	{
		my @allowParams = ( "action" );
		$errormsg = &getValidOptParams( $json_obj, \@allowParams );
		if ( !$errormsg )
		{
			if ( $json_obj->{ 'action' } ne "update" )
			{
				$errormsg = "Error, the action available is 'update'.";
				my $body =
				{ description => $description, error => "true", message => $errormsg };
				&httpResponse( { code => 404, body => $body } );
			}
			else
			{
				&setBLDownloadRemoteList( $listName );
				if ( @{ &getBLParam( $listName, 'farms' ) } )
				{
					&setBLRefreshList( $listName );
				}
				my $statusUpd = &getBLParam( $listName, 'update_status' );
				&httpResponse(
					{ code => 200, body => { description => $description, update => $statusUpd } } );
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

#GET /ipds/blacklists/<listname>/sources
sub get_blacklists_source
{
	my $listName    = shift;
	my $description = "Get $listName sources";
	my %listHash;
	my $err = &getBLExists( $listName );

	if ( $err == 0 )
	{
		my @ipList;
		my $index = 0;
		foreach my $source ( @{ &getBLParam( $listName, 'source' ) } )
		{
			push @ipList, { id => $index++, source => $source };
		}

		&httpResponse(
					   {
						 code => 200,
						 body => { description => $description, params => \@ipList }
					   }
		);
	}
	else
	{
		my $errormsg = "Requested list doesn't exist.";
		my $body = {
					 description => "$description",
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}

	return \%listHash;
}

#  POST /ipds/blacklists/<listname>/sources
sub add_blacklists_source
{
	my $json_obj = shift;
	my $listName = shift;
	my $errormsg;
	my $description    = "Post source to $listName.";
	my @requiredParams = ( "source" );
	my @optionalParams;

	if ( &getBLExists( $listName ) == -1 )
	{
		$errormsg = "$listName doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}
	else
	{
		$errormsg = &getValidReqParams( $json_obj, \@requiredParams, \@optionalParams );
		if ( !$errormsg )
		{
			if ( !&getValidFormat( 'blacklists_source', $json_obj->{ 'source' } ) )
			{
				$errormsg = "It's necessary to introduce a correct source.";
			}
			elsif (
				  grep ( /^$json_obj->{'source'}$/, @{ &getBLParam( $listName, 'source' ) } ) )
			{
				$errormsg = "$json_obj->{'source'} just exists in the list.";
			}
			else
			{
				$errormsg = &setBLAddSource( $listName, $json_obj->{ 'source' } );
				if ( !$errormsg )
				{
					my @ipList;
					my $index = 0;
					foreach my $source ( @{ &getBLParam( $listName, 'source' ) } )
					{
						push @ipList, { id => $index++, source => $source };
					}

					$errormsg = "Added $json_obj->{'source'} successful.";
					my $body = {
								 description => $description,
								 params      => \@ipList,
								 message     => $errormsg,
					};
					&httpResponse( { code => 200, body => $body } );
				}
				else
				{
					$errormsg = "Error, adding source to $listName.";
				}
			}
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg,
	};
	&httpResponse( { code => 400, body => $body } );
}

#  PUT /ipds/blacklists/<listname>/sources/<id>
sub set_blacklists_source
{
	my $json_obj    = shift;
	my $listName    = shift;
	my $id          = shift;
	my $description = "Put source into $listName";
	my $errormsg;
	my @allowParams = ( "source" );

	# check list exists
	if ( &getBLExists( $listName ) == -1 )
	{
		$errormsg = "$listName not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}

	# check source id exists
	elsif ( @{ &getBLParam( $listName, 'source' ) } <= $id )
	{
		$errormsg = "Source id $id not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}
	else
	{
		$errormsg = &getValidOptParams( $json_obj, \@allowParams );
		if ( !$errormsg )
		{
			if ( !&getValidFormat( 'blacklists_source', $json_obj->{ 'source' } ) )
			{
				$errormsg = "Wrong source format.";
			}
			elsif ( &setBLModifSource( $listName, $id, $json_obj->{ 'source' } ) != 0 )
			{
				$errormsg = "Error, putting the source to the list.";
			}
			else
			{
				my $source = &getBLParam( $listName, 'source' );
				my $body = {
							 description => $description,
							 params      => $source
				};
				&httpResponse( { code => 200, body => $body } );
			}
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg,
	};
	&httpResponse( { code => 400, body => $body } );
}

#  DELETE /ipds/blacklists/<listname>/sources/<id>	Delete a source from a black list
sub del_blacklists_source
{
	my $listName = shift;
	my $id       = shift;
	my $errormsg;
	my $description = "Delete source from the list $listName";

	if ( &getBLExists( $listName ) == -1 )
	{
		$errormsg = "$listName doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( @{ &getBLParam( $listName, 'source' ) } <= $id )
	{
		$errormsg = "ID $id doesn't exist in the list $listName.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}
	else
	{
		if ( &setBLDeleteSource( $listName, $id ) != 0 )
		{
			$errormsg = "Error deleting source $id";
		}
		else
		{
			my $errormsg = "Source $id has been deleted successful.";
			my $body = {
						 description => $description,
						 success     => "true",
						 message     => $errormsg,
			};
			&httpResponse( { code => 200, body => $body } );
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg,
	};
	&httpResponse( { code => 400, body => $body } );
}

#  POST /farms/<farmname>/ipds/blacklists
sub add_blacklists_to_farm
{
	my $json_obj = shift;
	my $farmName = shift;
	my $listName = $json_obj->{ 'name' };
	my $errormsg;
	my $description = "Apply a list to a farm";

	$errormsg = &getValidReqParams( $json_obj, ["name"] );
	if ( !$errormsg )
	{
		if ( &getFarmFile( $farmName ) eq "-1" )
		{
			$errormsg = "$farmName doesn't exist.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};
			&httpResponse( { code => 404, body => $body } );
		}
		elsif ( &getBLExists( $listName ) == -1 )
		{
			$errormsg = "$listName doesn't exist.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};
			&httpResponse( { code => 404, body => $body } );
		}
		else
		{
			if ( grep ( /^$farmName$/, @{ &getBLParam( $listName, 'farms' ) } ) )
			{
				$errormsg = "$listName just is applied to $farmName.";
			}
			else
			{
				$errormsg = &setBLApplyToFarm( $farmName, $listName );
				if ( !$errormsg )
				{
					my $errormsg = "List $listName was applied successful to the farm $farmName.";
					my $body = {
								 description => $description,
								 succes      => "true",
								 message     => $errormsg
					};
					&httpResponse( { code => 200, body => $body } );
				}
				else
				{
					$errormsg = "Error, applying $listName to $farmName";
				}
			}
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg
	};
	&httpResponse( { code => 400, body => $body } );
}

# DELETE /farms/<farmname>/ipds/blacklists/<listname>
sub del_blacklists_from_farm
{
	my $farmName = shift;
	my $listName = shift;
	my $errormsg;
	my $description = "Delete a list form a farm";

	if ( &getFarmFile( $farmName ) eq '-1' )
	{
		$errormsg = "$farmName doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( &getBLExists( $listName ) == -1 )
	{
		$errormsg = "$listName doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( !grep ( /^$farmName$/, @{ &getBLParam( $listName, 'farms' ) } ) )
	{
		$errormsg = "Not found a rule associated to $listName and $farmName.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	else
	{
		$errormsg = &setBLRemFromFarm( $farmName, $listName );
		if ( !$errormsg )
		{
			$errormsg = "List $listName was removed successful from the farm $farmName.";
			my $body = {
						 description => $description,
						 success     => "true",
						 message     => $errormsg,
			};
			&httpResponse( { code => 200, body => $body } );
		}
		else
		{
			$errormsg = "Error, removing $listName from $farmName.";
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg
	};
	&httpResponse( { code => 400, body => $body } );
}

dos:

# GET /ipds/dos/rules
sub get_dos_rules
{
	my $description = "Get DoS settings.";
		
	my $body = { description => $description, params => 
		{
		"farm"=>[ 
				{ 'rule'=>'limitsec', 'description'=>'Connection limit per seconds.'},
				{ 'rule'=>'limitconns', 'description'=>'Total connections limit per source IP.'},
				{ 'rule'=>'bogustcpflags', 'description'=>'Check bogus TCP flags.'},
				{ 'rule'=>'limitrst', 'description'=>'Limit RST request per second.'},
			],
		"system"=>[ 
				{ 'rule' => 'sshbruteforce', 'description' => 'SSH brute force.' },
				{ 'rule' => 'dropicmp', 'description' => 'Drop icmp packets' },
			]
		}
	};
	&httpResponse( { code => 200, body => $body } );
	
}


#GET /ipds/dos
sub get_dos
{
	my $confFile = &getGlobalConfiguration( 'dosConf' );
	my $description = "Get DoS settings.";

	my $fileHandle = Config::Tiny->read( $confFile );
	my %rules = %{ $fileHandle };
	my @output;

	foreach my $rule ( keys %rules )
	{
		my $aux = &getDOSParam( $rule );
		push @output, $aux;
	}
	
	my $body = { description => $description, params => \@output };
	&httpResponse( { code => 200, body => $body } );
}

#  POST /ipds/dos
sub create_dos_rule
{
	my $json_obj       = shift;
	my $description    = "Post a DoS rule";
	my $rule            = $json_obj->{ 'rule' };
	my @requiredParams = ( "name", "rule" );
	my $confFile       = &getGlobalConfiguration( 'dosConf' );

	my $errormsg = &getValidReqParams( $json_obj, \@requiredParams );
	if ( !$errormsg )
	{
		if ( &getDOSExists( $json_obj->{ 'name' } ) eq "0" )
		{
			$errormsg = "$json_obj->{ 'name' } already exists.";
		}
		elsif ( !&getValidFormat( 'dos_name', $json_obj->{ 'name' } ) )
		{
			$errormsg = "rule name hasn't a correct format.";
		}
		elsif ( !&getValidFormat( "dos_rule_farm", $json_obj->{ 'rule' } ) )
		{
			$errormsg = "ID rule isn't correct.";
		}
		else
		{
			$errormsg = &createDOSRule( $json_obj->{ 'name' }, $rule );
			if ( $errormsg )
			{
				$errormsg = "There was a error enabling DoS in $json_obj->{ 'name' }.";
			}
			else
			{
				my $output = &getDOSParam( $json_obj->{ 'name' } );
				&httpResponse(
							   {
								 code => 200,
								 body => { description => $description, params => $output }
							   }
				);
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg, };
	&httpResponse( { code => 400, body => $body } );
}

#GET /ipds/dos/RULE
sub get_dos_rule
{
	my $name        = shift;
	my $description = "Get DoS $name settings";
	my $refRule     = &getDOSParam( $name );
	my $output;
	
	if ( ref ( $refRule ) eq 'HASH' )
	{
		$output = &getDOSParam( $name );
		# successful
		my $body = { description => $description, params => $refRule, };
		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		$output = "$name doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $output
		};
		&httpResponse( { code => 404, body => $body } );
	}
}

#PUT /ipds/dos/<rule>
sub set_dos_rule
{
	my $json_obj    = shift;
	my $name        = shift;
	my $description = "Put DoS rule settings";
	my @requiredParams;
	my $errormsg;

	if ( &getDOSExists( $name ) )
	{
		$errormsg = "$name not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	else
	{
		# Get allowed params for a determinated rule
		my $rule = &getDOSParam( $name, 'rule' );
		my %hashRuleConf = %{ &getDOSInitialParams( $rule ) };

		# delete 'type' key
		delete $hashRuleConf{ 'type' };

		# delete 'key' key
		delete $hashRuleConf{ 'rule' };

		# delete 'farms' key
		if ( exists $hashRuleConf{ 'farms' } )
		{
			delete $hashRuleConf{ 'farms' };
		}

		# not allow change ssh port. To change it call PUT /system/ssh
		if ( $name eq 'ssh_brute_force' )
		{
			delete $hashRuleConf{ 'port' };
		}

		@requiredParams = keys %hashRuleConf;
		$errormsg = &getValidOptParams( $json_obj, \@requiredParams );
		if ( !$errormsg )
		{
			# check input format
			foreach my $param ( keys %{ $json_obj } )
			{
				if ( !&getValidFormat( "dos_$param", $json_obj->{ $param } ) )
				{
					$errormsg = "Error, $param format is wrong.";
					last;
				}
			}

			# output
			if ( !$errormsg )
			{
				foreach my $param ( keys %{ $json_obj } )
				{
					&setDOSParam( $name, $param, $json_obj->{ $param } );
				}
				if ( !$errormsg )
				{
					my $refRule = &getDOSParam( $name );
					&httpResponse(
						{
						   code => 200,
						   body => { description => $description, success => "true", params => $refRule }
						}
					);
				}
			}
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg
	};
	&httpResponse( { code => 400, body => $body } );
}

# DELETE /ipds/dos/RULE
sub del_dos_rule
{
	#~ my $json_obj = shift;
	my $name = shift;
	my $errormsg;
	my $description = "Delete DoS rule";

	if ( &getDOSExists( $name ) == -1 )
	{
		$errormsg = "$name not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( &getDOSParam( $name, 'type' ) eq 'system' )
	{
		$errormsg =
		  "Error, system rules not is possible to delete it, try to disable it.";
	}
	elsif ( @{ &getDOSParam( $name, 'farms' ) } )
	{
		$errormsg = "Error, disable this rule from all farms before than delete it.";
	}
	else
	{
		&deleteDOSRule( $name );
		$errormsg = "Deleted $name successful.";
		my $body = {
					 description => $description,
					 success     => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 200, body => $body } );
	}

	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg
	};
	&httpResponse( { code => 400, body => $body } );
}

#  GET /farms/<farmname>/ipds/dos
sub get_dos_farm
{
	my $farmName = shift;
	my $confFile = &getGlobalConfiguration( 'dosConf' );
	my @output;
	my $description = "Get status DoS $farmName.";

	if ( -e $confFile )
	{
		my $fileHandle = Config::Tiny->read( $confFile );

		foreach my $ruleName ( keys %{ $fileHandle } )
		{
			if ( $fileHandle->{ $ruleName }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
			{
				push @output, $ruleName;
			}
		}
	}

	my $body = { description => $description, params => \@output };
	&httpResponse( { code => 200, body => $body } );
}

#  POST /farms/<farmname>/ipds/dos
sub add_dos_to_farm
{
	my $json_obj    = shift;
	my $farmName    = shift;
	my $description = "Post a DoS rule to a farm";
	my $name        = $json_obj->{ 'name' };
	my $errormsg;

	my $confFile = &getGlobalConfiguration( 'dosConf' );
	my $output   = "down";

	if ( &getFarmFile( $farmName ) eq '-1' )
	{
		$errormsg = "$farmName doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( &getDOSExists( $name ) == -1 )
	{
		$errormsg = "$name not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( &getDOSParam( $name, 'type' ) eq 'system' )
	{
		$errormsg = "system rules not is possible apply to farm.";
	}
	else
	{
		my $fileHandle = Config::Tiny->read( $confFile );
		if ( $fileHandle->{ $name }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
		{
			$errormsg = "This rule already is enabled in $farmName.";
		}
		else
		{
			&setDOSCreateRule( $name, $farmName );

			my $confFile = &getGlobalConfiguration( 'dosConf' );
			
			# check output
			my $output = &getDOSParam ( $name );
			if ( grep ( /^$farmName$/, @{ $output->{ 'farms' } } ) )
			{
				$errormsg = "$name was enabled successful in $farmName.";
				&httpResponse(
					{
					   code => 200,
					   body => { description => $description, params => $output, message => $errormsg }
					}
				);
			}
			else
			{
				$errormsg = "Error, enabling $name rule.";
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg, };
	&httpResponse( { code => 400, body => $body } );
}

# DELETE /farms/<farmname>/ipds/dos/<ruleName>
sub del_dos_from_farm
{
	my $farmName    = shift;
	my $name        = shift;
	my $description = "Delete DoS rule from a farm";
	my $errormsg;

	my $confFile = &getGlobalConfiguration( 'dosConf' );

	if ( &getFarmFile( $farmName ) eq "-1" )
	{
		$errormsg = "$farmName doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( &getDOSExists( $name ) == -1 )
	{
		$errormsg = "$name not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( &getDOSParam( $name, 'type' ) eq 'system' )
	{
		$errormsg = "system rules not is possible delete from a farm.";
	}
	else
	{
		my $fileHandle = Config::Tiny->read( $confFile );
		if ( $fileHandle->{ $name }->{ 'farms' } !~ /( |^)$farmName( |$)/ )
		{
			$errormsg = "This rule no is enabled in $farmName.";
		}
		else
		{
			&setDOSDeleteRule( $name, $farmName );

			# check output
			my $output = &getDOSParam ( $name );
			if ( ! grep ( /^$farmName$/, @{ $output->{ 'farms' } } ) )
			{
				$errormsg = "$name was disabled in $farmName successful.";
				&httpResponse(
					{
					   code => 200,
					   body => { description => $description, success => "true", message => $errormsg }
					}
				);
			}
			else
			{
				$errormsg = "Error, disabling $name rule.";
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg, };
	&httpResponse( { code => 400, body => $body } );
}

1;

