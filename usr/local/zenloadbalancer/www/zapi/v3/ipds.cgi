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
require "/usr/local/zenloadbalancer/www/Plugins/ddos.cgi";

use warnings;
use strict;

blacklists:

#**
#  @api {get} /ipds/blacklists Request all black lists
#  @apiGroup IPDS
#  @apiDescription Get description of all blackl lists
#  @apiName GetAllBlacklistsLists
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "black lists",
#   "lists" : [
#      {
#         "farms" : [
#            "gslbFarm",
#            "dnsFarm"
#         ],
#         "ips" : [
#            {
#               "id" : 0,
#               "source" : "192.168.100.240"
#            },
#            {
#               "id" : 1,
#               "source" : "21.5.6.4"
#            }
#         ],
#         "location" : "local",
#         "name" : "blackList",
#         "type" : "deny"
#      },
#      {
#         "farms" : [],
#         "ips" : [
#               "id" : 0,
#               "source" : "1.155.63.14"
#		  ],
#         "location" : "local",
#         "name" : "whiteList",
#         "type" : "allow"
#      }
#   ]
#}
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/blacklists
#
#@apiSampleRequest off
#**
# GET /ipds/blacklists
sub get_blacklists_all_lists
{
	my $listNames   = &getBLExists();
	my $description = "Get black lists";
	my @lists;
	foreach my $list ( @{ $listNames } )
	{
		my %listHash = (
						 list     => $list,
						 farms    => &getBLParam( $list, 'farms' ),
						 type     => &getBLParam( $list, 'type' ),
						 location => &getBLParam( $list, "location" )
		);
		if ( &getBLParam( $list, 'preload' ) eq 'true' )
		{
			$listHash{ 'preload' } = 'true';
		}
		push @lists, \%listHash;
	}

	&httpResponse(
		  { code => 200, body => { description => $description, params => \@lists } } );
}

#**
#  @api {get} /ipds/blacklists/<listname> Request a black list
#  @apiGroup IPDS
#  @apiDescription Get a black list description
#  @apiName GetBlacklistsList
#  @apiParam {String} listname  Black list name, unique ID.
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "black lists",
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
#         "type" : "deny"
#      }
#   ]
#}
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/blacklists/<listname>
#
#@apiSampleRequest off
#**
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
		foreach my $source ( @{ &getBLParam( $listName, 'sources' ) } )
		{
			push @ipList, { id => $index++, source => $source };
		}
		%listHash = (
					  name     => $listName,
					  sources  => \@ipList,
					  farms    => &getBLParam( $listName, 'farms' ),
					  type     => &getBLParam( $listName, 'type' ),
					  location => &getBLParam( $listName, 'location' )
		);
		if ( &getBLParam( $listName, 'preload' ) eq 'true' )
		{
			$listHash{ 'preload' } = 'true';
		}
		if ( &getBLParam( $listName, 'url' ) )
		{
			$listHash{ 'url' }     = &getBLParam( $listName, 'url' );
			$listHash{ 'status' }  = &getBLParam( $listName, 'status' );
			$listHash{ 'refresh' } = &getBLParam( $listName, 'refresh' );
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
# @apiSuccess   {String}	type		The list will be white or black. The options are: allow or deny (default)
# @apiSuccess	{string}	location	Specify where the list is keep it. The options are: local or remote.
# @apiSuccess	{string}	url			when list is in remote location, it's rry add url where is keep it.
# @apiSuccess	{number}	refresh	time to refresh the remote list.
#
#
#@apiSuccessExample Success-Response:
#{
#   "description" : "Post list newList",
#   "params" : {
#      "farms" : [],
#      "location" : "local",
#      "name" : "newList",
#      "sources" : [],
#      "type" : "deny"
#   }
#}
#
# @apiExample {curl} Example Usage:
#		curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#		-d '{"type":"deny", "location":"local"}'  https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/blacklists/newList
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
	my $listName    = $json_obj->{ 'list' };
	my $description = "Create a blacklist.";

	my @requiredParams = ( "list", "location" );
	my @optionalParams = ( "type", "url" );

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
			# Check format list refresh
			if ( exists $json_obj->{ 'refresh' } )
			{
				if ( $json_obj->{ 'location' } ne 'remote' )
				{
					$errormsg = "Refresh time only is available in remote lists.";
				}
				else
				{
					$listParams->{ 'refresh' } = $json_obj->{ 'refresh' };
				}
			}
			if ( !$errormsg && exists $json_obj->{ 'url' } )
			{
				if ( $json_obj->{ 'location' } ne 'remote' )
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
				if ( $json_obj->{ 'location' } eq 'remote' )
				{
					$errormsg = "It's necessary to add the url where is allocated the list.";
				}
			}

			if ( !$errormsg )
			{
				$listParams->{ 'location' } = $json_obj->{ 'location' };
				$listParams->{ 'type' }     = $json_obj->{ 'type' }
				  if ( exists $json_obj->{ 'type' } );

				if ( &setBLCreateList( $listName, $listParams ) )
				{
					$errormsg = "Error, creating a new list.";
				}

				# All successful
				else
				{
					my $listHash = &getBLParam( $listName );
					delete $listHash->{ 'sources' };
					delete $listHash->{ 'preload' };
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
# @apiSuccess   {String}	type	The list will be white or black. The options are: allow or deny.
# @apiSuccess	{list}		list	Replace sources ( IP's or network segment ) from list. Only local lists.
# @apiSuccess	{string}	url		Change url where are allocated sources. Only remote lists.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Put list list",
#   "params" : {
#      "farms" : [],
#      "location" : "local",
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
#      "type" : "allow"
#   }
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"type":"allow","list":["192.168.100.240","21.5.6.4"],
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
	  ( "type", "url", "sources", "list", "min", "hour", "dom", "month", "dow" );

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

	my $location = &getBLParam( $listName, 'location' );
	$errormsg = &getValidOptParams( $json_obj, \@allowParams );
	if ( !$errormsg )
	{
		# Check key format
		foreach my $key ( keys %{ $json_obj } )
		{
			if ( !&getValidFormat( "blacklists_$key", $json_obj->{ $key } ) )
			{
				$errormsg = "$key hasn't a correct format.";
				last;
			}
		}
		if ( !$errormsg )
		{
			# Refresh and url only is used in remote lists
			if (
				 (
				      exists $json_obj->{ 'url' }
				   || exists $json_obj->{ 'min' }
				   || exists $json_obj->{ 'hour' }
				   || exists $json_obj->{ 'dom' }
				   || exists $json_obj->{ 'month' }
				   || exists $json_obj->{ 'dow' }
				 )
				 && $location ne 'remote'
			  )
			{
				$errormsg = "Time options and url only are available in remote lists.";
			}

			# Sources only is used in local lists
			elsif ( exists $json_obj->{ 'sources' }
					&& $location ne 'local' )
			{
				$errormsg = "Sources parameter only is available in local lists.";
			}
			else
			{
				my $cronFlag;
				foreach my $key ( keys %{ $json_obj } )
				{
					# add only the sources with a correct format
					# no correct format sources are ignored
					if ( $key eq 'sources' )
					{
						my $source_format = &getValidFormat( 'blacklists_source' );
						my $noPush = grep ( !/$source_format)/, @{ $json_obj->{ 'list' } } );

						# error
						&zenlog( "$noPush sources couldn't be added" ) if ( $noPush );
					}

					# set params
					$errormsg = &setBLParam( $listName, $key, $json_obj->{ $key } );
					$errormsg = "Error, modifying $key in $listName." if ( $errormsg );

					# once changed list, update de list name
					if ( $key eq 'list' )
					{
						$listName = $json_obj->{ 'list' };
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

				if ( !$errormsg )
				{
					# all successful
					my $listHash = &getBLParam( $listName );
					delete $listHash->{ 'action' };
					&httpResponse(
								   {
									 code => 200,
									 body => { description => $description, params => $listHash }
								   }
					);
				}
				else
				{
					# almost one parameter couldn't be changed
					$errormsg = "Error, modifying $listName.";
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
			&httpResponse(
				{ code => 200, body => { description => $description, params => $json_obj } } );
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

#**
#  @api {get} /ipds/blacklists/<listname> Request the sources of a list
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
#         "type" : "deny"
#      }
#   ]
#}
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/blacklists/<listname>/source
#
#@apiSampleRequest off
#**
#GET /ipds/blacklists/<listname>/source
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
		foreach my $source ( @{ &getBLParam( $listName, 'sources' ) } )
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
#  @api {post} /ipds/blacklists/<listname>/source Create a new source for a list
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
#		-d '{"source":"16.31.0.223"}'  https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/blacklists/source
#
# @apiSampleRequest off
#
#**
#  POST /ipds/blacklists/<listname>/source
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
				  grep ( /^$json_obj->{'source'}$/, @{ &getBLParam( $listName, 'sources' ) } ) )
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
					foreach my $source ( @{ &getBLParam( $listName, 'sources' ) } )
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
#  @api {put} /ipds/blacklists/<listname>/source/<id> Modify a source of a black list
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
#        -d '{"source":"10.12.55.3" https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/blacklists/source/1
#
# @apiSampleRequest off
#
#**
#  PUT /ipds/blacklists/<listname>/source/<id>
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
	elsif ( @{ &getBLParam( $listName, 'sources' ) } <= $id )
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
				my $sources = &getBLParam( $listName, 'sources' );
				my $body = {
							 description => $description,
							 params      => $sources
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
#  @api {delete} /ipds/blacklists/<listname>/source/<id>	Delete a source from a black list
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
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/blacklists/list/source/1
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
	elsif ( @{ &getBLParam( $listName, 'sources' ) } <= $id )
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
	my $listName = $json_obj->{ 'list' };
	my $errormsg;
	my $description = "Apply a list to a farm";

	$errormsg = &getValidReqParams( $json_obj, ["list"] );
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

	if ( &getFarmFile( $farmName ) == -1 )
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

ddos:

#**
#  @api {get} /ipds/ddos Request ddos settings
#  @apiGroup IPDS
#  @apiDescription Get ddos configuraton.
#  @apiName GetDdos
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Get DDoS settings.",
#   "params" : {
#      "farms" : "testFarm gslbFarm",
#      "ssh_bruteForce" : "down"
#   }
#}
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/ddos
#
#@apiSampleRequest off
#**
#GET /ipds/ddos
sub get_ddos
{
	my $confFile = &getGlobalConfiguration( 'ddosConf' );
	my @output;
	my $description = "Get DDoS settings.";

	my $fileHandle = Config::Tiny->read( $confFile );
	my $output;
	my @farmType;
	my @systemType;

	foreach my $key ( keys %{ $fileHandle } )
	{
		if ( $fileHandle->{ $key }->{ 'type' } eq 'farm' )
		{
			push @farmType, $fileHandle->{ $key };
		}
		elsif ( $fileHandle->{ $key }->{ 'type' } eq 'system' )
		{
			push @systemType, $fileHandle->{ $key };
		}
	}

	$output->{ 'farm' }   = \@farmType;
	$output->{ 'system' } = \@systemType;

	my $body = { description => $description, params => $output };
	&httpResponse( { code => 200, body => $body } );
}

#  POST /ipds/ddos
sub create_ddos_rule
{
	my $json_obj       = shift;
	my $description    = "Post a DDoS rule";
	my $key            = $json_obj->{ 'id' };
	my @requiredParams = ( "rule", "id" );
	my $confFile       = &getGlobalConfiguration( 'ddosConf' );

	my $errormsg = &getValidReqParams( $json_obj, \@requiredParams );
	if ( !$errormsg )
	{
		if ( &getDDOSExists( $json_obj->{ 'rule' } ) eq "0" )
		{
			$errormsg = "$json_obj->{ 'rule' } already exists.";
		}
		elsif ( !&getValidFormat( 'ddos_rule', $json_obj->{ 'rule' } ) )
		{
			$errormsg = "rule name hasn't a correct format.";
		}
		elsif ( !&getValidFormat( "ddos_key_farm", $json_obj->{ 'id' } ) )
		{
			$errormsg = "ID rule isn't correct.";
		}
		else
		{
			$errormsg = &createDDOSRule( $json_obj->{ 'rule' }, $key );
			if ( $errormsg )
			{
				$errormsg = "There was a error enabling DDoS in $json_obj->{ 'rule' }.";
			}
			else
			{
				my $output = &getDDOSParam( $json_obj->{ 'rule' } );
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
#  @api {get} /ipds/ddos/RULE Request ddos rule settings
#  @apiGroup IPDS
#  @apiDescription Get ddos configuraton.for a rule
#  @apiName GetDdos
#  @apiVersion 3.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Get DDoS example_rule settings",
#   "params" : {
#      "farms" : "",
#      "key" : "LIMITSEC",
#      "limit" : "2",
#      "limitBurst" : "2"
#   }
#}
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/ddos/RULE
#
#@apiSampleRequest off
#**
#GET /ipds/ddos/RULE
sub get_ddos_rule
{
	my $rule        = shift;
	my $description = "Get DDoS $rule settings";
	my $refRule     = &getDDOSParam( $rule );
	my $output;

	if ( ref ( $refRule ) eq 'HASH' )
	{
		# successful
		my $body = { description => $description, params => $refRule, };
		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		$output = "$rule doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $output
		};
		&httpResponse( { code => 404, body => $body } );
	}
}

#**
#  @api {put} /ipds/ddos/RULE Modify ddos settings
#  @apiGroup IPDS
#  @apiName PutDdosSettings
#  @apiDescription Modify the params to DDoS
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess	{String}	id		identify a DDoS rule. The options are: ssh_bruteforce
# @apiSuccess   {String}	status	enable or disable a DDoS option.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Put DDoS settings",
#   "params" : {
#      "farms" : "httpFarm gslbFarm",
#      "ssh_bruteForce" : "down"
#   }
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"id":"ssh_bruteForce","status":"down"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/ddos
#
# @apiSampleRequest off
#
#**
#PUT /ipds/ddos
sub set_ddos_rule
{
	my $json_obj    = shift;
	my $rule        = shift;
	my $description = "Put DDoS rule settings";
	my @requiredParams;
	my $errormsg;

	if ( &getDDOSExists( $rule ) )
	{
		$errormsg = "$rule not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	else
	{
		# Get allowed params for a determinated key
		my $key = &getDDOSParam( $rule, 'key' );
		my %hashRuleConf = %{ &getDDOSInitialParams( $key ) };

		# delete 'type' key
		delete $hashRuleConf{ 'type' };

		# delete 'key' key
		delete $hashRuleConf{ 'key' };

		# delete 'farms' key
		if ( exists $hashRuleConf{ 'farms' } )
		{
			delete $hashRuleConf{ 'farms' };
		}

		@requiredParams = keys %hashRuleConf;
		$errormsg = &getValidOptParams( $json_obj, \@requiredParams );
		if ( !$errormsg )
		{
			# check input format
			foreach my $param ( keys %{ $json_obj } )
			{
				if ( !&getValidFormat( "ddos_$param", $json_obj->{ $param } ) )
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
					&setDDOSParam( $rule, $param, $json_obj->{ $param } );
				}
				if ( !$errormsg )
				{
					my $refRule = &getDDOSParam( $rule );
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

# DELETE /ipds/ddos/RULE
sub del_ddos_rule
{
	#~ my $json_obj = shift;
	my $rule = shift;
	my $errormsg;
	my $description = "Delete DDoS rule";

	if ( &getDDOSExists( $rule ) == -1 )
	{
		$errormsg = "$rule not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( &getDDOSParam( $rule, 'type' ) eq 'system' )
	{
		$errormsg =
		  "Error, system rules not is possible to delete it, try to disable it.";
	}
	elsif ( &getDDOSParam( $rule, 'farms' ) )
	{
		$errormsg = "Error, disable this rule from all farms before than delete it.";
	}
	else
	{
		&deleteDDOSRule( $rule );
		$errormsg = "Deleted $rule successful.";
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
#  @api {get} /farms/<farmname>/ipds/ddos Request DDoS status of a farm
#  @apiGroup IPDS
#  @apiDescription Get DDoS status of a farm
#  @apiName GetBlacklistsList
#  @apiParam {String} farmname  farm name, unique ID.
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Get status DDoS gslbFarm.",
#   "params" : ???
#}
#
#
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/<farmname>/ipds/ddos
#
#@apiSampleRequest off
#**
#  GET /farms/<farmname>/ipds/ddos
sub get_ddos_farm
{
	my $farmName = shift;
	my $confFile = &getGlobalConfiguration( 'ddosConf' );
	my @output;
	my $description = "Get status DDoS $farmName.";

	if ( -e $confFile )
	{
		my $fileHandle = Config::Tiny->read( $confFile );

		foreach my $key ( keys %{ $fileHandle } )
		{
			if ( $fileHandle->{ $key }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
			{
				push @output, $key;
			}
		}
	}

	my $body = { description => $description, params => \@output };
	&httpResponse( { code => 200, body => $body } );
}

#####Documentation of POST ddos to farm####
#**
#  @api {post} /farms/<farmname>/ipds/ddos	Add ddos to a farm
#  @apiGroup IPDS
#  @apiName PostDdosToFarm
#  @apiParam {String} farmname	farm name, unique ID.
#  @apiDescription Add ddos protection to a farm
#  @apiVersion 3.0.0
#
#
#
#@apiSuccessExample Success-Response:
#{
#   "description" : "Post DDoS to httpFarm.",
#   "params" : "up"
#}
#
#
# @apiExample {curl} Example Usage:
#		curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#		-d '{"id":"NEWNOSYN"}'  https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/<farmname>/ipds/ddos
#
# @apiSampleRequest off
#
#**
#  POST /farms/<farmname>/ipds/ddos
sub add_ddos_to_farm
{
	my $json_obj    = shift;
	my $farmName    = shift;
	my $description = "Post a DDoS rule to a farm";
	my $rule        = $json_obj->{ 'rule' };
	my $errormsg;

	my $confFile = &getGlobalConfiguration( 'ddosConf' );
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
	elsif ( &getDDOSExists( $rule ) == -1 )
	{
		$errormsg = "$rule not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( &getDDOSParam( $rule, 'type' ) eq 'system' )
	{
		$errormsg = "system rules not is possible apply to farm.";
	}
	else
	{
		my $fileHandle = Config::Tiny->read( $confFile );
		if ( $fileHandle->{ $rule }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
		{
			$errormsg = "This rule already is enabled in $farmName.";
		}
		else
		{
			&setDDOSCreateRule( $rule, $farmName );

			my $confFile = &getGlobalConfiguration( 'ddosConf' );
			my $output;

			# check output
			my $fileHandle  = Config::Tiny->read( $confFile );
			my $farmsString = $fileHandle->{ $rule }->{ 'farms' };

			if ( $farmsString =~ /( |^)$farmName( |$)/ )
			{
				$errormsg = "$rule was enabled successful in $farmName.";
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

#####Documentation of DELETE ddos from a farm####
#**
#  @api {delete} /farms/<farmname>/ipds/ddos	Delete ddos rules from a farm
#  @apiGroup IPDS
#  @apiName DeleteDdosFromFarm
#  @apiParam	{String}	farmname	farm name, unique ID.
#  @apiDescription Delete ddos rules from a farm.
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Delete DDoS form farm prueba",
#   "message" : "DDoS was desactived successful from farm prueba.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/<farmname>/ipds/ddos/KEY
#
# @apiSampleRequest off
#
#**
# DELETE /farms/<farmname>/ipds/ddos/<id>
sub del_ddos_from_farm
{
	my $farmName    = shift;
	my $rule        = shift;
	my $description = "Delete DDoS rule from a farm";
	my $errormsg;

	my $confFile = &getGlobalConfiguration( 'ddosConf' );

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
	elsif ( &getDDOSExists( $rule ) == -1 )
	{
		$errormsg = "$rule not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( &getDDOSParam( $rule, 'type' ) eq 'system' )
	{
		$errormsg = "system rules not is possible delete from a farm.";
	}
	else
	{
		my $fileHandle = Config::Tiny->read( $confFile );
		if ( $fileHandle->{ $rule }->{ 'farms' } !~ /( |^)$farmName( |$)/ )
		{
			$errormsg = "This rule no is enabled in $farmName.";
		}
		else
		{
			&setDDOSDeleteRule( $rule, $farmName );

			# check output
			my $confFile    = &getGlobalConfiguration( 'ddosConf' );
			my $fileHandle  = Config::Tiny->read( $confFile );
			my $farmsString = $fileHandle->{ $rule }->{ 'farms' };

			if ( $farmsString !~ /( |^)$farmName( |$)/ )
			{
				$errormsg = "$rule was disabled in $farmName successful.";
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

