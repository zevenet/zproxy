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
use Zevenet::IPDS::Blacklist::Core;

# GET /ipds/blacklists
sub get_blacklists_all_lists
{
	require Config::Tiny;

	my $description    = "Get black lists";
	my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
	my %bl             = %{ Config::Tiny->read( $blacklistsConf ) };
	my @lists;
	delete $bl{ _ };

	my @active_lists = `ipset -L -name`;

	foreach my $list_name ( sort keys %bl )
	{
		my $bl_n  = $bl{ $list_name };
		my $bl_nf = $bl_n->{ farms };

		my %listHash = (
					   name   => $list_name,
					   farms  => $bl_nf ? split ( ' ', $bl_nf ) : [],
					   policy => $bl_n->{ policy },
					   type   => $bl_n->{ type },
					   status => ( grep ( /^$list_name$/, @active_lists ) ) ? "up" : "down",
					   preload => $bl_n->{ preload },
		);

		push @lists, \%listHash;
	}

	&httpResponse(
		  { code => 200, body => { description => $description, params => \@lists } } );
}

#GET /ipds/blacklists/<listname>
sub get_blacklists_list
{
	my $listName = shift;

	my $description = "Get list $listName";
	my $errormsg;

	if ( !&getBLExists( $listName ) )
	{
		my $listHash = &getBLzapi( $listName );

		&httpResponse(
			{ code => 200, body => { description => $description, params => $listHash } } );
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

	my @requiredParams = ( "name",   "type" );
	my @optionalParams = ( "policy", "url" );

	$errormsg = &getValidReqParams( $json_obj, \@requiredParams, \@optionalParams );

	# $errormsg == 0, no error
	if ( !$errormsg )
	{
		# A list already exists with this name
		if ( &getBLExists( $listName ) != -1 )
		{
			$errormsg = "A list already exists with name '$listName'.";
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
				require Zevenet::IPDS::Blacklist::Config;

				$listParams->{ 'type' }   = $json_obj->{ 'type' };
				$listParams->{ 'policy' } = $json_obj->{ 'policy' }
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
	my $json_obj = shift;
	my $listName = shift;

	my $description = "Modify list $listName.";
	my $errormsg;

	require Zevenet::IPDS::Blacklist::Config;

	# remove time hash and add its param to common configuration hash
	foreach my $timeParameters ( ( 'period', 'unit', 'hour', 'minutes' ) )
	{
		if ( exists $json_obj->{ 'time' }->{ $timeParameters } )
		{
			$json_obj->{ $timeParameters } = $json_obj->{ 'time' }->{ $timeParameters };
		}
	}
	delete $json_obj->{ 'time' };

	my @allowParams = (
						"policy",         "url",    "source", "name",
						"minutes",        "hour",   "day",    "frequency",
						"frequency_type", "period", "unit"
	);

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
		$errormsg = &getValidOptParams( $json_obj, ["policy"] );
		$errormsg = "In preload lists only is allowed to change the policy"
		  if ( $errormsg );
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
				if (
					 grep ( /^(url|minutes|hour|day|frequency|frequency_type|period|unit)$/,
							keys %{ $json_obj } )
				  )

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
				if (
					 grep ( /^(minutes|hour|day|frequency|frequency_type|period|unit)$/,
							keys %{ $json_obj } )
				  )
				{
					$json_obj->{ 'frequency' } ||= &getBLParam( $listName, "frequency" );

					if ( $json_obj->{ 'frequency' } eq 'daily' )
					{
						$json_obj->{ 'frequency_type' } ||= &getBLParam( $listName, "frequency_type" );

						if ( $json_obj->{ 'frequency_type' } eq 'period' )
						{
							$json_obj->{ 'period' } = &getBLParam( $listName, "period" )
							  if ( !exists $json_obj->{ 'period' } );

							$json_obj->{ 'unit' } = &getBLParam( $listName, "unit" )
							  if ( !exists $json_obj->{ 'unit' } );

							foreach my $timeParam ( "period", "unit" )
							{
								if (   !&getValidFormat( "blacklists_$timeParam", $json_obj->{ $timeParam } )
									 || $json_obj->{ $timeParam } eq '' )
								{
									$errormsg =
									  "$timeParam parameter missing to $json_obj->{ frequency } configuration.";
									last;
								}
							}

							if ( !$errormsg )
							{
								&delBLParam( $listName, $_ ) for ( "minutes", "hour", "day" );

								# rewrite cron task if exists some of the next keys
								$cronFlag = 1;
							}
						}
						elsif ( $json_obj->{ 'frequency_type' } eq 'exact' )
						{
							$json_obj->{ 'minutes' } = &getBLParam( $listName, "minutes" )
							  if ( !exists $json_obj->{ 'minutes' } );
							$json_obj->{ 'hour' } = &getBLParam( $listName, "hour" )
							  if ( !exists $json_obj->{ 'hour' } );

							foreach my $timeParam ( "minutes", "hour" )
							{
								if (   !&getValidFormat( "blacklists_$timeParam", $json_obj->{ $timeParam } )
									 || $json_obj->{ $timeParam } eq '' )
								{
									$errormsg =
									  "$timeParam parameter missing to $json_obj->{ frequency } configuration.";
									last;
								}
							}

							if ( !$errormsg )
							{
								&delBLParam( $listName, $_ ) for ( "unit", "period", "day" );

								# rewrite cron task if exists some of the next keys
								$cronFlag = 1;
							}
						}
						else
						{
							$errormsg = "It's neccessary indicate frequency type for daily frequency.";
						}
					}
					elsif ( $json_obj->{ 'frequency' } eq 'weekly' )
					{
						$json_obj->{ 'minutes' } = &getBLParam( $listName, "minutes" )
						  if ( !exists $json_obj->{ 'minutes' } );
						$json_obj->{ 'hour' } = &getBLParam( $listName, "hour" )
						  if ( !exists $json_obj->{ 'hour' } );
						$json_obj->{ 'day' } = &getBLParam( $listName, "day" )
						  if ( !exists $json_obj->{ 'day' } );

						foreach my $timeParam ( "minutes", "hour", "day" )
						{
							if (   !&getValidFormat( "blacklists_$timeParam", $json_obj->{ $timeParam } )
								 || $json_obj->{ $timeParam } eq '' )
							{
								$errormsg =
								  "$timeParam parameter missing to $json_obj->{ frequency } configuration.";
								last;
							}
						}

						if ( !&getValidFormat( 'weekdays', $json_obj->{ 'day' } ) )
						{
							$errormsg =
							  "Error value of day parameter in $json_obj->{ 'frequency' } frequency.";
						}

						if ( !$errormsg )
						{
							&delBLParam( $listName, $_ ) for ( "frequency_type", "period", "unit" );

							# rewrite cron task if exists some of the next keys
							$cronFlag = 1;
						}
					}
					elsif ( $json_obj->{ 'frequency' } eq 'monthly' )
					{
						$json_obj->{ 'minutes' } = &getBLParam( $listName, "minutes" )
						  if ( !exists $json_obj->{ 'minutes' } );
						$json_obj->{ 'hour' } = &getBLParam( $listName, "hour" )
						  if ( !exists $json_obj->{ 'hour' } );
						$json_obj->{ 'day' } = &getBLParam( $listName, "day" ) + 0
						  if ( !exists $json_obj->{ 'day' } );    # number format

						# check if exists all paramameters
						foreach my $timeParam ( "hour", "minutes", "day" )
						{
							if (   !&getValidFormat( "blacklists_$timeParam", $json_obj->{ $timeParam } )
								 || $json_obj->{ $timeParam } eq '' )
							{
								$errormsg =
								  "$timeParam parameter missing to $json_obj->{ frequency } configuration.";
								last;
							}
						}

						if ( !&getValidFormat( 'day_of_month', $json_obj->{ 'day' } ) )
						{
							$errormsg =
							  "Error value of day parameter in $json_obj->{ 'frequency' } frequency.";
						}

						if ( !$errormsg )
						{
							&delBLParam( $listName, $_ ) for ( "unit", "period", "frequency_type" );

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

						require Zevenet::Cluster;
						&runZClusterRemoteManager( 'ipds_bl', 'restart', $listName );

						&httpResponse( { code => 200, body => $body } );
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
	my $listName = shift;

	my $description = "Delete list '$listName'",
	  my $errormsg  = &getBLExists( $listName );

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
	elsif ( @{ &getBLParam( $listName, 'farms' ) } )
	{
		$errormsg = "Delete this list from all farms before than delete it.";
	}
	else
	{
		require Zevenet::IPDS::Blacklist::Config;
		$errormsg = &setBLDeleteList( $listName );

		if ( !$errormsg )
		{
			$errormsg = "The list $listName has been deleted successful.";
			my $body = {
						 description => $description,
						 success     => "true",
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

# POST /ipds/blacklists/BLACKLIST/actions
sub actions_blacklists
{
	my $json_obj = shift;
	my $listName = shift;

	my $description = "Apply a action to a blacklist";

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

	if ( $json_obj->{ 'action' } eq "update" )
	{
		&update_remote_blacklists( $listName );
		require Zevenet::Cluster;
		&runZClusterRemoteManager( 'ipds_bl', 'restart', $listName );
	}
	else
	{
		require Zevenet::IPDS::Blacklist::Actions;
		my $error;
		if ( $json_obj->{ action } eq 'start' )
		{
			$error = &runBLStartByRule( $listName );
		}
		elsif ( $json_obj->{ action } eq 'stop' )
		{
			$error = &runBLStopByRule( $listName );
		}
		elsif ( $json_obj->{ action } eq 'restart' )
		{
			$error = &runBLRestartByRule( $listName );
		}
		else
		{
			$errormsg = "The action has not a valid value";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};
			&httpResponse( { code => 400, body => $body } );
		}

		if ( $error )
		{
			&httpResponse(
						   {
							 code => 400,
							 body => {
									   description => $description,
									   error       => "true",
									   message     => "Error, applying the action to the blacklist."
							 }
						   }
			);
		}
		else
		{
			require Zevenet::Cluster;
			&runZClusterRemoteManager( 'ipds_bl', $json_obj->{ action }, $listName );
			&httpResponse(
						   {
							 code => 200,
							 body => {
									   description => $description,
									   success     => "true",
									   params      => $json_obj->{ action }
							 }
						   }
			);
		}
	}
}

# POST /ipds/blacklists/BLACKLIST/actions 	update a remote blacklist
sub update_remote_blacklists
{
	my $listName = shift;

	my $errormsg;
	my $description = "Update a remote list";
	if ( &getBLParam( $listName, 'type' ) ne 'remote' )
	{
		$errormsg = "Error, only remote lists can be updated.";
	}
	else
	{
		require Zevenet::IPDS::Blacklist::Runtime;
		$errormsg = &setBLDownloadRemoteList( $listName );
		my $statusUpd = &getBLParam( $listName, 'update_status' );

		if ( !$errormsg )
		{
			if ( @{ &getBLParam( $listName, 'farms' ) } )
			{
				&setBLRefreshList( $listName );
			}

			&httpResponse(
						   {
							 code => 200,
							 body => {
									   description => $description,
									   success     => "true",
									   params      => { "action" => "update" }
							 }
						   }
			);
		}
		else
		{
			$errormsg = $statusUpd;
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };

	&httpResponse( { code => 400, body => $body } );
}

#GET /ipds/blacklists/<listname>/sources
sub get_blacklists_source
{
	my $listName = shift;

	my $description = "Get $listName sources";
	my $err         = &getBLExists( $listName );
	my %listHash;

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
				$errormsg = "$json_obj->{'source'} already exists in the list.";
			}
			else
			{
# ipset not allow the input 0.0.0.0/0, if this source is set, replace it for 0.0.0.0/1 and 128.0.0.0/1
				if ( $json_obj->{ 'source' } eq '0.0.0.0/0' )
				{
					$errormsg =
					  "Error, the source $json_obj->{'source'} is not valid, for this action, use the list \"All\".";

					my $body = {
								 description => $description,
								 error       => "true",
								 message     => $errormsg,
					};

					&httpResponse( { code => 400, body => $body } );
				}
				else
				{
					require Zevenet::IPDS::Blacklist::Config;
					$errormsg = &setBLAddSource( $listName, $json_obj->{ 'source' } );
				}
				if ( !$errormsg )
				{
					my @ipList;
					my $index = 0;

					foreach my $source ( @{ &getBLParam( $listName, 'source' ) } )
					{
						push @ipList, { id => $index++, source => $source };
					}

					$errormsg = "Added $json_obj->{'source'} successful.";

					require Zevenet::Cluster;
					&runZClusterRemoteManager( 'ipds_bl', 'restart', $listName );

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
	my $json_obj = shift;
	my $listName = shift;
	my $id       = shift;

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
		require Zevenet::IPDS::Blacklist::Config;
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
				$errormsg = "Source $id has been modified successful.";
				my $body = {
							 description => $description,
							 message     => $errormsg,
							 params      => { "source" => $json_obj->{ 'source' }, 'id' => $id }
				};

				require Zevenet::Cluster;
				&runZClusterRemoteManager( 'ipds_bl', 'restart', $listName );

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
		require Zevenet::IPDS::Blacklist::Config;
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

			require Zevenet::Cluster;
			&runZClusterRemoteManager( 'ipds_bl', 'restart', $listName );

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

	my $listName    = $json_obj->{ 'name' };
	my $description = "Apply a rule to a farm";
	my $errormsg    = &getValidReqParams( $json_obj, ["name"] );

	if ( !$errormsg )
	{
		require Zevenet::Farm::Core;
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
				$errormsg = "$listName is already applied to $farmName.";
			}
			else
			{
				require Zevenet::IPDS::Blacklist::Runtime;
				$errormsg = &setBLApplyToFarm( $farmName, $listName );

				if ( !$errormsg )
				{
					my $errormsg =
					  "Blacklist rule $listName was applied successful to the farm $farmName.";
					my $body = {
								 description => $description,
								 success     => "true",
								 message     => $errormsg
					};

					require Zevenet::Cluster;
					&runZClusterRemoteManager( 'ipds_bl', 'start', $listName, $farmName );

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
	my $description = "Delete a rule from a farm";

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
		require Zevenet::IPDS::Blacklist::Runtime;
		$errormsg = &setBLRemFromFarm( $farmName, $listName );

		if ( !$errormsg )
		{
			$errormsg =
			  "Blacklist rule $listName was removed successful from the farm $farmName.";
			my $body = {
						 description => $description,
						 success     => "true",
						 message     => $errormsg,
			};

			require Zevenet::Cluster;
			&runZClusterRemoteManager( 'ipds_bl', 'stop', $listName, $farmName );

			&httpResponse( { code => 200, body => $body } );
		}
		else
		{
			$errormsg = "Error, removing $listName rule from $farmName.";
		}
	}

	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg
	};

	&httpResponse( { code => 400, body => $body } );
}

1;
