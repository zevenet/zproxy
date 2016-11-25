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

require "/usr/local/zenloadbalancer/www/Plugins/rbl.cgi";
require "/usr/local/zenloadbalancer/www/Plugins/ddos.cgi";

#~ use warnings;
#~ use strict;

rbl:

#**
#  @api {get} /ipds/rbl Request all rbl lists
#  @apiGroup IPDS
#  @apiDescription Get description of all rbl lists
#  @apiName GetAllRblLists
#  @apiVersion 3.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "rbl lists",
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
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/rbl
#
#@apiSampleRequest off
#**
# GET /ipds/rbl
sub get_rbl_all_lists
{
	my $listNames   = &getRBLExists();
	my $description = "Get rbl lists";
	my @lists;
	foreach my $list ( @{ $listNames } )
	{
		my %listHash = (
						 list     => $list,
						 farms    => &getRBLListParam( $list, 'farms' ),
						 type     => &getRBLListParam( $list, 'type' ),
						 location => &getRBLListParam( $list, "location" )
		);
		if ( &getRBLListParam( $list, 'preload' ) eq 'true' )
		{
			$listHash{ 'preload' } = 'true';
		}
		push @lists, \%listHash;
	}

	&httpResponse(
		  { code => 200, body => { description => $description, params => \@lists } } );
}

#**
#  @api {get} /ipds/rbl/<listname> Request a rbl list
#  @apiGroup IPDS
#  @apiDescription Get a rbl list description
#  @apiName GetRblList
#  @apiParam {String} listname  Rbl list name, unique ID.
#  @apiVersion 3.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "rbl lists",
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
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/rbl/<listname>
#
#@apiSampleRequest off
#**
#GET /ipds/rbl/<listname>
sub get_rbl_list
{
	my $listName    = shift;
	my $description = "Get list $listName";
	my %listHash;
	my $errormsg;

	if ( ! &getRBLExists( $listName ) )
	{
		my @ipList;
		my $index = 0;
		foreach my $source ( @{ &getRBLListParam( $listName, 'sources' ) } )
		{
			push @ipList, { id => $index++, source => $source };
		}
		%listHash = (
					  name     => $listName,
					  sources  => \@ipList,
					  farms    => &getRBLListParam( $listName, 'farms' ),
					  type     => &getRBLListParam( $listName, 'type' ),
					  location => &getRBLListParam( $listName, 'location' )
		);
		if ( &getRBLListParam( $listName, 'preload' ) eq 'true' )
		{
			$listHash{ 'preload' } = 'true';
		}
		if ( &getRBLListParam( $listName, 'url' ) )
		{
			$listHash{ 'url' }     = &getRBLListParam( $listName, 'url' );
			$listHash{ 'status' }  = &getRBLListParam( $listName, 'status' );
			$listHash{ 'refresh' } = &getRBLListParam( $listName, 'refresh' );
		}
		&httpResponse(
			{ code => 200, body => { description => $description, params => \%listHash } }
		);
	}
	else
	{
		$errormsg = "Requested list doesn't exist.";
		my $body = { description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 400, body => $body } );
	}

	return \%listHash;
}

#####Documentation of POST RBL list####
#**
#  @api {post} /ipds/rbl/<listname> Create a new rbl list
#  @apiGroup IPDS
#  @apiName PostRblList
#  @apiDescription Create a new rbl list
#  @apiVersion 3.0
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
#		-d '{"type":"deny", "location":"local"}'  https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/rbl/newList
#
# @apiSampleRequest off
#
#**
#  POST /ipds/rbl
sub add_rbl_list
{
	my $json_obj = shift;
	my $errormsg;
	my $listParams;
	my $listName    = $json_obj->{ 'list' };
	my $description = "Add list '$listName'";

	my @requiredParams = ( "list", "location" );
	my @optionalParams = ( "type", "url", "refresh" );

	$errormsg =
	  &getValidReqParams( $json_obj, \@requiredParams, \@optionalParams );
	# $errormsg == 0, no error
	if ( !$errormsg )
	{
		# A list with this name just exist
		if ( &getRBLExists( $listName ) != -1 )
		{
			$errormsg = "A list with name '$listName' just exists.";
		}

		# Check key format
		foreach my $key ( keys %$json_obj )
		{
			if ( ! &getValidFormat( "rbl_$key", $json_obj->{ $key } ) )
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

				if ( &setRBLCreateList( $listName, $listParams ) )
				{
					$errormsg = "Error, creating a new list.";
				}

				# All successful
				else
				{
					my $listHash = &getRBLListParam( $listName );
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

#####Documentation of PUT rbl list####
#**
#  @api {put} /ipds/rbl/<listname> Modify a rbl list
#  @apiGroup IPDS
#  @apiName PutRblList
#  @apiParam {String} listname  RBL list name, unique ID.
#  @apiDescription Modify the params in a RBL list
#  @apiVersion 3.0
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
#       "name":"newNameList"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/rbl/list
#
# @apiSampleRequest off
#
#**
#  PUT /ipds/rbl/<listname>
sub set_rbl_list
{
	my $json_obj    = shift;
	my $listName    = shift;
	my $description = "Modify list $listName.";
	my $errormsg;

	my @allowParams = ( "type", "url", "refresh", "sources","list" );

	if ( &getRBLExists( $listName ) == -1 )
	{
		$errormsg = "The list '$listName' doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}

	my $location = &getRBLListParam( $listName, 'location' );
	$errormsg = &getValidOptParams( $json_obj, \@allowParams );
	if ( !$errormsg )
	{
		# Check key format
		foreach my $key ( keys %{ $json_obj } )
		{
			if ( ! &getValidFormat( "rbl_$key", $json_obj->{ $key } ) )
			{
				$errormsg = "$key hasn't a correct format.";
				last;
			}
		}
		if ( !$errormsg )
		{
			# Refresh and url only is used in remote lists
			if ( ( exists $json_obj->{ 'refresh' } || exists $json_obj->{ 'url' } )
				 && $location ne 'remote' )
			{
				$errormsg = "Refresh time and url only are available in remote lists.";
			}
			# Sources only is used in local lists 
			elsif ( exists $json_obj->{ 'sources' }
					&& $location ne 'local' )
			{
				$errormsg = "Sources parameter only is available in local lists.";
			}
			else
			{
				foreach my $key ( keys %{ $json_obj } )
				{
					# add only the sources with a correct format
					# no correct format sources are ignored
					if ( $key eq 'sources' )
					{
						my $source_format = &getValidFormat( 'rbl_source' );
						my $noPush = grep ( !/$source_format)/, @{ $json_obj->{ 'list' } } );
						# error
						&zenlog( "$noPush sources couldn't be added" ) if ( $noPush );
					}

					# set params 
					$errormsg = &setRBLListParam( $listName, $key, $json_obj->{ $key } );
					$errormsg = "Error, modifying $key in $listName." if ( $errormsg );
					
					# once changed list, update de list name
					if ( $key eq 'list' )
					{
						$listName = $json_obj->{ 'list' };
					}
					
					# not continue if there was a error
					last if ( $errormsg );
				}
				if ( !$errormsg )
				{
					# all successful
					my $listHash = &getRBLListParam( $listName );
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

#####Documentation of DELETE RBL list####
#**
#  @api {delete} /ipds/rbl/<listname> Delete a Farm
#  @apiGroup IPDS
#  @apiName DeleteRblList
#  @apiParam {String} listname	rbl list name, unique ID.
#  @apiDescription Delete a given rbl list
#  @apiVersion 3.0
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
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/rbl/listname
#
# @apiSampleRequest off
#
#**
sub del_rbl_list
{
	my $listName = shift;
	my $description = "Delete list '$listName'",

	my $errormsg = &getRBLExists( $listName );
	if ( $errormsg == -1 )
	{
		$errormsg = "$listName doesn't exist.";
		my $body = {
			description => $description,  error => "true", message => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}
	else
	{
		$errormsg = &setRBLDeleteList( $listName );
		if ( !$errormsg )
		{
			$errormsg = "The list $listName has been deleted successful.";
			my $body = {
				description => $description, successful => "true", message => $errormsg,
			};
			&httpResponse( { code => 200, body => $body } );
		}
		else
		{
			$errormsg = "Error, deleting the list $listName.";
		}
	}
	my $body = {
		description => $description,  error => "true", message => $errormsg,
	};
	&httpResponse( { code => 400, body => $body } );
}

#**
#  @api {get} /ipds/rbl/<listname> Request the sources of a list
#  @apiGroup IPDS
#  @apiDescription Get the sources of a list
#  @apiName GetRblSource
#  @apiParam {String} listname  Rbl list name, unique ID.
#  @apiVersion 3.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "rbl sources",
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
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/rbl/<listname>/source
#
#@apiSampleRequest off
#**
#GET /ipds/rbl/<listname>/source
sub get_rbl_source
{
	my $listName    = shift;
	my $description = "Get $listName sources";
	my %listHash;
	my $err = &getRBLExists( $listName );

	if ( $err == 0 )
	{
		my @ipList;
		my $index = 0;
		foreach my $source ( @{ &getRBLListParam( $listName, 'sources' ) } )
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
#  @api {post} /ipds/rbl/<listname>/source Create a new source for a list
#  @apiGroup IPDS
#  @apiName PostRblSource
#  @apiParam {String} listname  Rbl list name, unique ID.
#  @apiDescription Add a source to a specific list
#  @apiVersion 3.0
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
#		-d '{"source":"16.31.0.223"}'  https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/rbl/source
#
# @apiSampleRequest off
#
#**
#  POST /ipds/rbl/<listname>/source
sub add_rbl_source
{
	my $json_obj = shift;
	my $listName = shift;
	my $errormsg;
	my $description    = "Post source to $listName.";
	my @requiredParams = ( "source" );
	my @optionalParams;

	if ( &getRBLExists( $listName ) == -1 )
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
		$errormsg =
		  &getValidReqParams( $json_obj, \@requiredParams, \@optionalParams );
		if ( !$errormsg )
		{
			if ( ! &getValidFormat( 'rbl_source', $json_obj->{ 'source' } )  )
			{
				$errormsg = "It's necessary to introduce a correct source.";
			}
			elsif (
					grep ( /^$json_obj->{'source'}$/,
						   @{ &getRBLListParam( $listName, 'sources' ) } ) )
			{
				$errormsg = "$json_obj->{'source'} just exists in the list.";
			}
			else
			{
				$errormsg = &setRBLAddSource( $listName, $json_obj->{ 'source' } );
				if ( !$errormsg )
				{
					my @ipList;
					my $index = 0;
					foreach my $source ( @{ &getRBLListParam( $listName, 'sources' ) } )
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

#####Documentation of PUT a source of a RBL list####
#**
#  @api {put} /ipds/rbl/<listname>/source/<id> Modify a source of a rbl list
#  @apiGroup IPDS
#  @apiName PutRblSource
#  @apiParam	{String}	listname	RBL list name, unique ID.
#  @apiParam	{number}	id			Source ID to modificate.
#  @apiDescription Modify a source of a RBL list
#  @apiVersion 3.0
#
#
#  @apiSuccess	{String}	source		IP or net segment to modificate in a rbl list.
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
#        -d '{"source":"10.12.55.3" https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/rbl/source/1
#
# @apiSampleRequest off
#
#**
#  PUT /ipds/rbl/<listname>/source/<id>
sub set_rbl_source
{
	my $json_obj    = shift;
	my $listName    = shift;
	my $id          = shift;
	my $description = "Put source into $listName";
	my $errormsg;
	my @allowParams = ( "source" );

	# check list exists
	if ( &getRBLExists( $listName ) == -1 )
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
	elsif ( @{ &getRBLListParam( $listName, 'sources' ) } <= $id )
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
			if ( ! &getValidFormat( 'rbl_source', $json_obj->{ 'source' } ) )
			{
				$errormsg = "Wrong source format.";
			}
			elsif ( &setRBLModifSource( $listName, $id, $json_obj->{ 'source' } ) != 0 )
			{
				$errormsg = "Error, putting the source to the list.";
			}
			else
			{
				my $sources = &getRBLListParam( $listName, 'sources' );
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

#####Documentation of DELETE a source of a RBL list####
#**
#  @api {delete} /ipds/rbl/<listname>/source/<id>	Delete a source from a rbl list
#  @apiGroup IPDS
#  @apiName DeleteRblSource
#  @apiParam	{String}	listname	rbl list name, unique ID.
#  @apiParam	{number}	id			Source ID to delete.
#  @apiDescription Delete a source of alist
#  @apiVersion 3.0
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
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/rbl/list/source/1
#
# @apiSampleRequest off
#
#**
sub del_rbl_source
{
	my $listName = shift;
	my $id       = shift;
	my $errormsg;
	my $description = "Delete source from the list $listName";

	if ( &getRBLExists( $listName ) == -1 )
	{
		$errormsg = "$listName doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( @{ &getRBLListParam( $listName, 'sources' ) } <= $id )
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
		if ( &setRBLDeleteSource( $listName, $id ) != 0 )
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
#  @api {post} /farms/<farmname>/ipds/rbl	Enable a list in a farm
#  @apiGroup IPDS
#  @apiName PostRblListToFarm
#  @apiParam {String} farmname	farm name, unique ID.
#  @apiDescription Add a list rule to a farm
#  @apiVersion 3.0
#
#
# @apiSuccess   {String}	list		Existing rbl list.
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
#		-d '{"list":"blackList"}'  https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/dns/ipds/rbl
#
# @apiSampleRequest off
#
#**
#  POST /farms/<farmname>/ipds/rbl
sub add_rbl_to_farm
{
	my $json_obj = shift;
	my $farmName = shift;
	my $listName = $json_obj->{ 'list' };
	my $errormsg;
	my $description = "Apply a list to a farm";

	if ( &getFarmFile( $farmName ) == -1 )
	{
		$errormsg = "$farmName doesn't exist.";
		my $body = {
			description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( &getRBLExists( $listName ) == -1 )
	{
		$errormsg = "$listName doesn't exist.";
		my $body = {
			description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 404, body => $body } );
	}
	else
	{
		if ( grep ( /^$farmName$/, @{ &getRBLListParam( $listName, 'farms' ) } ) )
		{
			$errormsg = "$listName just is applied to $farmName.";
		}
		else
		{
			$errormsg = &setRBLApplyToFarm( $farmName, $listName );
			if ( !$errormsg )
			{
				my $errormsg = "List $listName was applied successful to the farm $farmName.";
				my $body = {
					description => $description, succes => "true", message => $errormsg };
				&httpResponse( { code => 200, body => $body } );
			}
			else
			{
				$errormsg = "Error, applying $listName to $farmName";
			}
		}
	}
	my $body = {
			description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

#####Documentation of DELETE disable a list in a farm####
#**
#  @api {delete} /farms/<farmname>/ipds/rbl/<listname>	Delete a rbl rule from a farm
#  @apiGroup IPDS
#  @apiName DeleteRblListFromFarm
#  @apiParam	{String}	farmname	farm name, unique ID.
#  @apiParam	{String}	listname	rbl list name, unique ID.
#  @apiDescription Delete a given rbl list from a farm
#  @apiVersion 3.0
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
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/dns/ipds/rbl/listName
#
# @apiSampleRequest off
#
#**
# DELETE /farms/<farmname>/ipds/rbl/<listname>
sub del_rbl_from_farm
{
	my $farmName = shift;
	my $listName = shift;
	my $errormsg;
	my $description = "Delete a list form a farm";

	if ( &getFarmFile( $farmName ) == -1 )
	{
		$errormsg = "$farmName doesn't exist.";
		my $body = {
			description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( &getRBLExists( $listName ) == -1 )
	{
		$errormsg = "$listName doesn't exist.";
		my $body = {
			description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( ! grep( /^$farmName$/, @{ &getRBLListParam( $listName, 'farms' ) } ) )
	{
		$errormsg = "Not found a rule associated to $listName and $farmName.";
		my $body = {
			description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 404, body => $body } );
	}
	else
	{
		$errormsg = &setRBLRemFromFarm( $farmName, $listName );
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
			description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

ddos:

#**
#  @api {get} /ipds/ddos Request ddos settings
#  @apiGroup IPDS
#  @apiDescription Get ddos configuraton.
#  @apiName GetDdos
#  @apiVersion 3.0
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

	if ( -e $confFile )
	{
		my $fileHandle = Config::Tiny->read( $confFile );
		foreach my $key ( keys %{ $fileHandle } )
		{
			# get status of all rules enabled
			if (    $fileHandle->{ $key }->{ 'status' } =~ /up/
				 || $fileHandle->{ $key }->{ 'farms' } )

			  # get status only balancer rules
			  #~ if ( $fileHandle->{ $key }->{'status'} =~ /up/ )
			{
				push @output, $key;
			}
		}
	}

	my $body = {
				 description => "Get DDoS settings.",
				 params      => \@output
	};

	&httpResponse( { code => 200, body => $body } );
}

# ???
sub get_ddos_key
{
	my $key = shift;

	my $output = &getDDOSParam( $key );

	# not exit this key
	if ( !$output )
	{
		my $errormsg = "$key isn't a valid ID DDoS rule";
		my $body = {
					 description => "Get DDoS $key settings",
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 400, body => $body } );
	}

	# successful
	else
	{
		my $body = {
					 description => "$key settings.",
					 params      => $output,
		};
		&httpResponse( { code => 200, body => $body } );
	}

}

#**
#  @api {put} /ipds/ddos Modify ddos settings
#  @apiGroup IPDS
#  @apiName PutDdosSettings
#  @apiDescription Modify the params to DDoS
#  @apiVersion 3.0
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
sub set_ddos
{
	my $json_obj = shift;
	my $key      = $json_obj->{ 'id' };
	my $errormsg;

	if ( $key eq 'DROPICMP' )
	{
		if ( $json_obj->{ 'status' } eq 'up' )
		{
			&setDDOSCreateRule( $key );
		}
		elsif ( $json_obj->{ 'status' } eq 'down' )
		{
			&setDDOSDeleteRule( $key );
		}
	}

	elsif ( $key eq 'SSHBRUTEFORCE' )
	{
		&setDDOSParam( $key, 'time', $json_obj->{ 'time' } )
		  if ( exists $json_obj->{ 'time' } );
		&setDDOSParam( $key, 'hits', $json_obj->{ 'hits' } )
		  if ( exists $json_obj->{ 'hits' } );
		&setDDOSParam( $key, 'port', $json_obj->{ 'port' } )
		  if ( exists $json_obj->{ 'port' } );

		&setDDOSCreateRule( $key ) if ( $json_obj->{ 'status' } eq 'up' );
		&setDDOSDeleteRule( $key ) if ( $json_obj->{ 'status' } eq 'down' );
	}

	elsif ( $key eq 'PORTSCANNING' )
	{
		&setDDOSParam( $key, 'blTime', $json_obj->{ 'blTime' } )
		  if ( exists $json_obj->{ 'blTime' } );
		&setDDOSParam( $key, 'time', $json_obj->{ 'time' } )
		  if ( exists $json_obj->{ 'time' } );
		&setDDOSParam( $key, 'hits', $json_obj->{ 'hits' } )
		  if ( exists $json_obj->{ 'hits' } );
		&setDDOSParam( $key, 'portScan', $json_obj->{ 'portScan' } )
		  if ( exists $json_obj->{ 'portScan' } );

		&setDDOSCreateRule( $key ) if ( $json_obj->{ 'status' } eq 'up' );
		&setDDOSDeleteRule( $key ) if ( $json_obj->{ 'status' } eq 'down' );
	}

	elsif ( $key eq 'SYNPROXY' )
	{
		&setDDOSParam( $key, 'mss', $json_obj->{ 'mss' } )
		  if ( exists $json_obj->{ 'mss' } );
		&setDDOSParam( $key, 'scale', $json_obj->{ 'scale' } )
		  if ( exists $json_obj->{ 'scale' } );
	}

	elsif ( $key eq 'LIMITSEC' )
	{
		&setDDOSParam( $key, 'limit', $json_obj->{ 'limit' } )
		  if ( exists $json_obj->{ 'limit' } );
		&setDDOSParam( $key, 'limitBurst', $json_obj->{ 'limitBurst' } )
		  if ( exists $json_obj->{ 'limitBurst' } );
	}

	elsif ( $key eq 'LIMITRST' )
	{
		&setDDOSParam( $key, 'limit', $json_obj->{ 'limit' } )
		  if ( exists $json_obj->{ 'limit' } );
		&setDDOSParam( $key, 'limitBurst', $json_obj->{ 'limitBurst' } )
		  if ( exists $json_obj->{ 'limitBurst' } );
	}

	elsif ( $key eq 'LIMITCONNS' )
	{
		&setDDOSParam( $key, 'limitConns', $json_obj->{ 'limitConns' } )
		  if ( exists $json_obj->{ 'limitConns' } );
	}

	else
	{
		$errormsg = "Wrong param ID";
	}

	# output
	if ( $errormsg )
	{
		my $body = {
					 description => "Put DDoS settings",
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 400, body => $body } );
	}

	else
	{
		&httpResponse(
			   {
				 code => 200,
				 bdy  => { description => "Put DDoS $key settings", "successful" => "true" }
			   }
		);
	}

}

#**
#  @api {get} /farms/<farmname>/ipds/ddos Request DDoS status of a farm
#  @apiGroup IPDS
#  @apiDescription Get DDoS status of a farm
#  @apiName GetRblList
#  @apiParam {String} farmname  farm name, unique ID.
#  @apiVersion 3.0
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

	my $body = {
				 description => "Get status DDoS $farmName.",
				 params      => \@output
	};

	&httpResponse( { code => 200, body => $body } );

}

#####Documentation of POST ddos to farm####
#**
#  @api {post} /farms/<farmname>/ipds/ddos	Add ddos to a farm
#  @apiGroup IPDS
#  @apiName PostDdosToFarm
#  @apiParam {String} farmname	farm name, unique ID.
#  @apiDescription Add ddos protection to a farm
#  @apiVersion 3.0
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
	my $json_obj = shift;
	my $farmName = shift;
	my $key      = $json_obj->{ 'id' };
	my $errormsg;
	my @vaildKeys = (
		'INVALID', 'BLOCKSPOOFED', 'LIMITCONNS', 'LIMITSEC',    # all farms
		'DROPFRAGMENTS', 'NEWNOSYN', 'SYNWITHMSS',    # farms based in TCP protcol
		'BOGUSTCPFLAGS', 'LIMITRST', 'SYNPROXY'
	);

	my $confFile = &getGlobalConfiguration( 'ddosConf' );
	my $output   = "down";

	system ( &getGlobalConfiguration( 'ddosConf' ) . " $confFile" )
	  if ( !-e $confFile );
	if ( !grep ( /^$key$/, @vaildKeys ) )
	{
		$errormsg = "Key $key is not a valid value.";
	}
	elsif ( grep ( /$farmName/, &getFarmList() ) )
	{
		my $fileHandle = Config::Tiny->read( $confFile );
		if ( $fileHandle->{ $key }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
		{
			$errormsg = "Just is enabled DDoS in $farmName.";
		}
		else
		{
			&setDDOSCreateRule( $key, $farmName );

			my $confFile = &getGlobalConfiguration( 'ddosConf' );
			my $output;

			# check output
			my $fileHandle  = Config::Tiny->read( $confFile );
			my $farmsString = $fileHandle->{ $key }->{ 'farms' };

			if ( $farmsString =~ /( |^)$farmName( |$)/ )
			{
				$output = 'up';
				&httpResponse(
						  {
							code => 200,
							body => { description => "Post DDoS to $farmName.", params => $output }
						  }
				);
			}
			else
			{
				$errormsg = "There was a error enabling DDoS in $farmName.";
			}
		}
	}
	else
	{
		$errormsg = "$farmName doesn't exist";
	}

	if ( $errormsg )
	{
		my $body = {
					 description => "Post DDoS to $farmName",
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse( { code => 400, body => $body } );
	}

}

#####Documentation of DELETE ddos from a farm####
#**
#  @api {delete} /farms/<farmname>/ipds/ddos	Delete ddos rules from a farm
#  @apiGroup IPDS
#  @apiName DeleteDdosFromFarm
#  @apiParam	{String}	farmname	farm name, unique ID.
#  @apiDescription Delete ddos rules from a farm.
#  @apiVersion 3.0
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
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/<farmname>/ipds/ddos
#
# @apiSampleRequest off
#
#**
# DELETE /farms/<farmname>/ipds/ddos/<id>
sub del_ddos_from_farm
{
	my $farmName = shift;
	my $key      = shift;
	my $confFile = &getGlobalConfiguration( 'ddosConf' );
	my $errormsg;

	my @vaildKeys = (
		'INVALID', 'BLOCKSPOOFED', 'LIMITCONNS', 'LIMITSEC',    # all farms
		'DROPFRAGMENTS', 'NEWNOSYN', 'SYNWITHMSS',    # farms based in TCP protcol
		'BOGUSTCPFLAGS', 'LIMITRST', 'SYNPROXY'
	);

	if ( !grep ( /^$key$/, @vaildKeys ) )
	{
		$errormsg = "Key $key is not a valid value.";
	}
	elsif ( -e $confFile )
	{
		my $fileHandle  = Config::Tiny->read( $confFile );
		my $farmsString = $fileHandle->{ $key }->{ 'farms' };
		$errormsg = "DDoS for $farmName just is disable."
		  if ( $farmsString !~ /( |^)$farmName( |$)/ );
	}
	else
	{
		$errormsg = "DDoS for $farmName just is disable.";
	}

	if ( !$errormsg )
	{
		if ( grep ( /$farmName/, &getFarmList ) )
		{
			&setDDOSDeleteRule( $key, $farmName );

			my $errormsg = "DDoS was desactived successful from farm $farmName.";

			my $body = {
						 description => "Delete DDoS form farm $farmName",
						 success     => "true",
						 message     => $errormsg,
			};

			&httpResponse( { code => 200, body => $body } );
		}
		else
		{
			$errormsg = "$farmName doesn't exist";
		}
	}

	if ( $errormsg )
	{
		my $body = {
					 description => "Delete DDoS form farm $farmName",
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse( { code => 400, body => $body } );
	}

}

1;

