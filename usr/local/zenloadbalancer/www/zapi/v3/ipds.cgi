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
	my %listHash;
	my $errormsg;

	if ( !&getBLExists( $listName ) )
	{
		my @ipList;
		my $index = 0;
		foreach my $source ( @{ &getBLParam( $listName, 'source' ) } )
		{
			push @ipList, { id => $index++, source => $source };
		}
		%listHash = (
					  name     => $listName,
					  sources => \@ipList,
					  farms    => &getBLParam( $listName, 'farms' ),
					  policy     => &getBLParam( $listName, 'policy' ),
					  type => &getBLParam( $listName, 'type' ),
					  preload => &getBLParam( $listName, 'preload' )
		);
		if ( &getBLParam( $listName, 'type' ) eq 'remote' )
		{
			$listHash{ 'url' }     = &getBLParam( $listName, 'url' );
			$listHash{ 'status' }  = &getBLParam( $listName, 'status' );
		}
		&httpResponse(
			  { code => 200, body => { description => $description, params => \%listHash } }
		);
	}
	else
	{
		$errormsg = "Requested list doesn't exist.";
		my $body =
		  { description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 400, body => $body } );
	}

	return \%listHash;
}

#####Documentation of POST BL list####
#**
#  @api {post} /ipds/blacklists/<listname> Create a new black list
#  @apiGroup IPDS
#  @apiName PostBlacklistsList
#  @apiDescription Create a new black list
#  @apiVersion 3.0.0
#
#
# @apiSuccess   {String}	policy		The list will be white or black. The options are: allow or deny (default)
# @apiSuccess	{string}	type	Specify where the list is keep it. The options are: local or remote.
# @apiSuccess	{string}	url			when list is in remote type, it's rry add url where is keep it.
# @apiSuccess	{number}	refresh	time to refresh the remote list.
#
#
#@apiSuccessExample Success-Response:
#{
#   "description" : "Post list newList",
#   "params" : {
#      "farms" : [],
#      "type" : "local",
#      "name" : "newList",
#      "sources" : [],
#      "policy" : "deny"
#   }
#}
#
# @apiExample {curl} Example Usage:
#		curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#		-d '{"policy":"deny", "type":"local"}'  https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/blacklists/newList
#
# @apiSampleRequest off
#
#**
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

#####Documentation of PUT black list####
#**
#  @api {put} /ipds/blacklists/<listname> Modify a black list
#  @apiGroup IPDS
#  @apiName PutBlacklistsList
#  @apiParam {String} listname  BL list name, unique ID.
#  @apiDescription Modify the params in a BL list
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess	{String}	name	The new list name.
# @apiSuccess   {String}	policy	The list will be white or black. The options are: allow or deny.
# @apiSuccess	{source}		list	Replace sources ( IP's or network segment ) from list. Only local lists.
# @apiSuccess	{string}	url		Change url where are allocated sources. Only remote lists.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Put list list",
#   "params" : {
#      "farms" : [],
#      "type" : "local",
#      "name" : "newNameList",
#      "sources" : [
#         {
#            "id" : 0,
#            "source" : "192.168.100.240"
#         },
#         {
#            "id" : 1,
#            "source" : "21.5.6.4"
#         }
#      ],
#      "policy" : "allow"
#   }
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"policy":"allow","list":["192.168.100.240","21.5.6.4"],
#       "name":"newNameList"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/blacklists/list
#
# @apiSampleRequest off
#
#**
#  PUT /ipds/blacklists/<listname>
sub set_blacklists_list
{
	my $json_obj    = shift;
	my $listName    = shift;
	my $description = "Modify list $listName.";
	my $errormsg;

	my @allowParams =
	  ( "policy", "url", "source", "name", "min", "hour", "dom", "month", "dow" );

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
	
	elsif ( &getBLParam( $listName, 'type' ) eq 'preload' )
	{
		$errormsg = &getValidOptParams( $json_obj, [ "policy" ] );
		$errormsg = "In preload lists only is allow to change the policy" if ( $errormsg );
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
			if (
				 (
				      exists $json_obj->{ 'url' }
				   || exists $json_obj->{ 'min' }
				   || exists $json_obj->{ 'hour' }
				   || exists $json_obj->{ 'dom' }
				   || exists $json_obj->{ 'month' }
				   || exists $json_obj->{ 'dow' }
				 )
				 && $type ne 'remote'
			  )
			{
				$errormsg = "Time options and url only are available in remote lists.";
			}

			# Sources only is used in local lists
			elsif ( exists $json_obj->{ 'source' }
					&& $type ne 'local' )
			{
				$errormsg = "Source parameter only is available in local lists.";
			}
			else
			{
				my $cronFlag;
				foreach my $key ( keys %{ $json_obj } )
				{
					# add only the sources with a correct format
					# no correct format sources are ignored
					if ( $key eq 'source' )
					{
						my $source_format = &getValidFormat( 'blacklists_source' );
						my $noPush = grep ( !/$source_format)/, @{ $json_obj->{ 'name' } } );

						# error
						&zenlog( "$noPush sources couldn't be added" ) if ( $noPush );
					}

					# set params
					$errormsg = &setBLParam( $listName, $key, $json_obj->{ $key } );
					$errormsg = "Error, modifying $key in $listName." if ( $errormsg );

					# once changed list, update de list name
					if ( $key eq 'name' )
					{
						$listName = $json_obj->{ 'name' };
					}

					# rewrite cron task if exists some of the next keys
					$cronFlag = 1
					  if (    $key eq "min"
						   || $key eq "hour"
						   || $key eq "month"
						   || $key eq "dow"
						   || $key eq "dom" );

					# not continue if there was a error
					last if ( $errormsg );
				}

				if ( $cronFlag && @{ &getBLParam( $listName, 'farms' ) } )
				{
					&setBLCronTask( $listName );
				}

				# all successful
				my $listHash = &getBLParam( $listName );
				
				my $body = { description => $description, params => $listHash };
				&httpResponse({ code => 200, body => $body } );
				# almost one parameter couldn't be changed
				#~ $errormsg = "Error, modifying $listName.";
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

#####Documentation of DELETE BL list####
#**
#  @api {delete} /ipds/blacklists/<listname> Delete a Farm
#  @apiGroup IPDS
#  @apiName DeleteBlacklistsList
#  @apiParam {String} listname	black list name, unique ID.
#  @apiDescription Delete a given black list
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Delete farm FarmHTTP",
#   "message" : "The Farm FarmHTTP has been deleted.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/blacklists/listname
#
# @apiSampleRequest off
#
#**
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
	else
	{
		$errormsg = &setBLDeleteList( $listName );
		if ( !$errormsg )
		{
			$errormsg = "The list $listName has been deleted successful.";
			my $body = {
						 description => $description,
						 successful  => "true",
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

sub update_remote_blacklists
{
	my $json_obj    = shift;
	my $listName    = shift;
	my $description = "Update a remote list";

	my @allowParams = ( "action" );
	my $errormsg = &getValidOptParams( $json_obj, \@allowParams );
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
			my $statusUpd = &getBLParam( $listName, 'status' );
			&httpResponse(
				{ code => 200, body => { description => $description, update => $statusUpd } } );
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

#**
#  @api {get} /ipds/blacklists/<listname>/sources Request the sources of a list
#  @apiGroup IPDS
#  @apiDescription Get the sources of a list
#  @apiName GetBlacklistsSource
#  @apiParam {String} listname  black list name, unique ID.
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "blacklists sources",
#   "params" : [
#      {
#         "farms" : [
#            "gslbFarm",
#            "httpFarm"
#         ],
#         "ips" : [
#            {
#               "id" : 0,
#               "source" : "17.63.203.20"
#            },
#            {
#               "id" : 1,
#               "source" : "21.5.6.4"
#            }
#         ],
#         "name" : "blackList",
#         "policy" : "deny"
#      }
#   ]
#}
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/blacklists/<listname>/sources
#
#@apiSampleRequest off
#**
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

#####Documentation of POST a source to a list####
#**
#  @api {post} /ipds/blacklists/<listname>/sources Create a new source for a list
#  @apiGroup IPDS
#  @apiName PostBlacklistsSource
#  @apiParam {String} listname  Black list name, unique ID.
#  @apiDescription Add a source to a specific list
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {String}	source		New IP or net segment to add to a list.
#
#
#
#@apiSuccessExample Success-Response:
#{
#   "description" : "Post a source in a list",
#   "params" : [
#      "192.168.100.240",
#      "21.5.6.4",
#      "16.31.0.223"
#   ]
#}
#
# @apiExample {curl} Example Usage:
#		curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#		-d '{"source":"16.31.0.223"}'  https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/blacklists/sources
#
# @apiSampleRequest off
#
#**
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

#####Documentation of PUT a source of a black list####
#**
#  @api {put} /ipds/blacklists/<listname>/sources/<id> Modify a source of a black list
#  @apiGroup IPDS
#  @apiName PutBlacklistsSource
#  @apiParam	{String}	listname	Black list name, unique ID.
#  @apiParam	{number}	id			Source ID to modificate.
#  @apiDescription Modify a source of a Black list
#  @apiVersion 3.0.0
#
#
#  @apiSuccess	{String}	source		IP or net segment to modificate in a black list.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Put a source of a list",
#   "params" : [
#      "192.168.100.240",
#      "10.12.55.3"
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"source":"10.12.55.3" https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/blacklists/sources/1
#
# @apiSampleRequest off
#
#**
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

#####Documentation of DELETE a source of a black list####
#**
#  @api {delete} /ipds/blacklists/<listname>/sources/<id>	Delete a source from a black list
#  @apiGroup IPDS
#  @apiName DeleteBlacklistsSource
#  @apiParam	{String}	listname	Black list name, unique ID.
#  @apiParam	{number}	id			Source ID to delete.
#  @apiDescription Delete a source of alist
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Delete source from 'listName'",
#   "message" : "Source 1 has been deleted.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/blacklists/list/sources/1
#
# @apiSampleRequest off
#
#**
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

#####Documentation of POST enable a list in a farm####
#**
#  @api {post} /farms/<farmname>/ipds/blacklists	Enable a list in a farm
#  @apiGroup IPDS
#  @apiName PostBlacklistsListToFarm
#  @apiParam {String} farmname	farm name, unique ID.
#  @apiDescription Add a list rule to a farm
#  @apiVersion 3.0.0
#
#
# @apiSuccess   {String}	list		Existing black list.
#
#@apiSuccessExample Success-Response:
#{
#   "description" : "Apply a list to a farm",
#   "error" : "true",
#   "message" : "blackList just is applied to prueba."
#}
#
#
# @apiExample {curl} Example Usage:
#		curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#		-d '{"list":"blackList"}'  https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/dns/ipds/blacklists
#
# @apiSampleRequest off
#
#**
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

#####Documentation of DELETE disable a list in a farm####
#**
#  @api {delete} /farms/<farmname>/ipds/blacklists/<listname>	Delete a black rule from a farm
#  @apiGroup IPDS
#  @apiName DeleteBlacklistsFromFarm
#  @apiParam	{String}	farmname	farm name, unique ID.
#  @apiParam	{String}	listname	black list name, unique ID.
#  @apiDescription Delete a given black list from a farm
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Delete list listName form farm dns",
#   "message" : "List listName was removed successful from farm dns.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/dns/ipds/blacklists/listName
#
# @apiSampleRequest off
#
#**
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

sub get_dos_rules
{
	my $description = "Get DoS settings.";
		
	my $body = { description => $description, params => 
		{
		"farm"=>[ 
				{ 'rule'=>'limitsec', 'description'=>'Connection limit per seconds.'},
				{ 'rule'=>'limitrst', 'description'=>'Total connections limit per source IP.'},
				{ 'rule'=>'bogustcpflags', 'description'=>'Check bogus TCP flags.'},
				{ 'rule'=>'limitconns', 'description'=>'Limit RST request per second.'},
			],
		"system"=>[ 
				{ 'rule' => 'sshbruteforce', 'description' => 'SSH brute force.' },
				{ 'rule' => 'dropicmp', 'description' => 'Drop icmp packets' },
			]
		}
	};
	&httpResponse( { code => 200, body => $body } );
	
}


#**
#  @api {get} /ipds/dos Request dos settings
#  @apiGroup IPDS
#  @apiDescription Get dos configuraton.
#  @apiName GetDos
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Get DoS settings.",
#   "params" : {
#      "farms" : "testFarm gslbFarm",
#      "ssh_bruteForce" : "down"
#   }
#}
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/dos
#
#@apiSampleRequest off
#**
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

#**
#  @api {get} /ipds/dos/RULE Request dos rule settings
#  @apiGroup IPDS
#  @apiDescription Get dos configuraton.for a rule
#  @apiName GetDos
#  @apiVersion 3.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Get DoS example_rule settings",
#   "params" : {
#      "farms" : "",
#      "rule" : "LIMITSEC",
#      "limit" : "2",
#      "limit_burst" : "2"
#   }
#}
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/dos/RULE
#
#@apiSampleRequest off
#**
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

#**
#  @api {put} /ipds/dos/RULE Modify dos settings
#  @apiGroup IPDS
#  @apiName PutDosSettings
#  @apiDescription Modify the params to DoS
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess	{String}	rule		identify a DoS rule. The options are: ssh_bruteforce
# @apiSuccess   {String}	status	enable or disable a DoS option.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Put DoS settings",
#   "params" : {
#      "farms" : "httpFarm gslbFarm",
#      "ssh_bruteForce" : "down"
#   }
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"rule":"ssh_bruteForce","status":"down"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/dos
#
# @apiSampleRequest off
#
#**
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

#**
#  @api {get} /farms/<farmname>/ipds/dos Request DoS status of a farm
#  @apiGroup IPDS
#  @apiDescription Get DoS status of a farm
#  @apiName GetBlacklistsList
#  @apiParam {String} farmname  farm name, unique ID.
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Get status DoS gslbFarm.",
#   "params" : ???
#}
#
#
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/<farmname>/ipds/dos
#
#@apiSampleRequest off
#**
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

#####Documentation of POST dos to farm####
#**
#  @api {post} /farms/<farmname>/ipds/dos	Add dos to a farm
#  @apiGroup IPDS
#  @apiName PostDosToFarm
#  @apiParam {String} farmname	farm name, unique ID.
#  @apiDescription Add dos protection to a farm
#  @apiVersion 3.0.0
#
#
#
#@apiSuccessExample Success-Response:
#{
#   "description" : "Post DoS to httpFarm.",
#   "params" : "up"
#}
#
#
# @apiExample {curl} Example Usage:
#		curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#		-d '{"rule":"NEWNOSYN"}'  https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/<farmname>/ipds/dos
#
# @apiSampleRequest off
#
#**
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
			my $output;

			# check output
			my $fileHandle  = Config::Tiny->read( $confFile );
			my $farmsString = $fileHandle->{ $name }->{ 'farms' };

			if ( $farmsString =~ /( |^)$farmName( |$)/ )
			{
				$errormsg = "$name was enabled successful in $farmName.";
				&httpResponse(
					{
					   code => 200,
					   body => { description => $description, params => $output, message => $errormsg }
					}
				);
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg, };
	&httpResponse( { code => 400, body => $body } );
}

#####Documentation of DELETE dos from a farm####
#**
#  @api {delete} /farms/<farmname>/ipds/dos	Delete dos rules from a farm
#  @apiGroup IPDS
#  @apiName DeleteDosFromFarm
#  @apiParam	{String}	farmname	farm name, unique ID.
#  @apiDescription Delete dos rules from a farm.
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Delete DoS form farm prueba",
#   "message" : "DoS was desactived successful from farm prueba.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/<farmname>/ipds/dos/KEY
#
# @apiSampleRequest off
#
#**
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
			my $confFile    = &getGlobalConfiguration( 'dosConf' );
			my $fileHandle  = Config::Tiny->read( $confFile );
			my $farmsString = $fileHandle->{ $name }->{ 'farms' };

			if ( $farmsString !~ /( |^)$farmName( |$)/ )
			{
				$errormsg = "$name was disabled in $farmName successful.";
				&httpResponse(
					{
					   code => 200,
					   body => { description => $description, success => "true", message => $errormsg }
					}
				);
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg, };
	&httpResponse( { code => 400, body => $body } );
}

1;

