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


require "/usr/local/zenloadbalancer/www/Plugins/rbl.pl";

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
#	-u zapi:<password> https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/rbl
#
#@apiSampleRequest off
#**
# GET /ipds/rbl
sub get_rbl_all_lists
{
	my $listNames = &getRBLListNames;
	my @lists;

	foreach my $list ( @{$listNames} )
	{
		my @ipList;
		my $index = 0;
		foreach my $source ( @{ &getRBLListParam ($list,'list') } )
		{
			push @ipList, { id => $index++, source => $source };
		}
		
		my %listHash = (
			name => $list,
			ips => \@ipList,
			farms => &getRBLListParam ($list,'farms'),
			type => &getRBLListParam ($list,'type'),
			location => &getRBLListLocalitation ( $list )
		);
		push @lists, \%listHash;
	}
	
	&httpResponse({ code => 200, body => { description => "Get rbl lists", params => \@lists} });
};


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
#	-u zapi:<password> https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/rbl/<listname>
#
#@apiSampleRequest off
#**
#GET /ipds/rbl/<listname>
sub get_rbl_list
{
	my $listName = shift;
	my $blockOut = shift;  # if ( $blockOut ) no httpResponse
	
	my %listHash;
	my $err = &getRBLListLocalitation ( $listName );

	if ( $err != '-1' )
	{
		my @ipList;
		my $index = 0;
		foreach my $source ( @{ &getRBLListParam ($listName,'list') } )
		{
			push @ipList, { id => $index++, source => $source };
		}
		
		%listHash = (
			name => $listName,
			sources => \@ipList,
			farms => &getRBLListParam ($listName,'farms'),
			type => &getRBLListParam ($listName,'type'),
			location => &getRBLListLocalitation ( $listName )
		);
		
		if ( $err eq 'remote' )
		{
			$listHash{'url'} = &getRBLListParam ($listName,'url');
			$listHash{'status'} = &getRBLListParam ($listName,'status');
		}
		
		if ( ! $blockOut )
		{
			&httpResponse({ code => 200, body => { description => "Get list $listName", params => \%listHash} });
		}
	}
	else
	{
		my $errormsg = "List request don't exist.";
		my $body = {
					   description => "Get rbl list '$listName'",
					   error       => "true",
					   message     => $errormsg,
		};

		if ( ! $blockOut )
		{
			&httpResponse({ code => 400, body => $body });
		}
	}
	return \%listHash;
};


# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"profile":"HTTP","vip":"178.62.126.152","vport":"12345","interface":"eth0"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/newfarmHTTP
#
# HTTP status code reference: http://www.restapitutorial.com/httpstatuscodes.html
#
#
#
#####Documentation of POST RBL list####
#**
#  @api {post} /ipds/rbl/<listname> Create a new rbl list
#  @apiGroup IPDS
#  @apiName PostRblList
#  @apiParam {String} listname  Rbl list name, unique ID.
#  @apiDescription Create a new rbl list 
#  @apiVersion 3.0
#
#
#
# @apiSuccess   {String}	type		The list will be white or black. The options are: allow or deny.
# @apiSuccess	{string}	location	Specify where the list is keep it. The options are: local or remote.
# @apiSuccess	{string}	url			when list is in remote location, it's necesary add url where is keep it.
#
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
#		-d '{"type":"deny", "location":"local"}' -u zapi:<password> https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/rbl/newList
#
# @apiSampleRequest off
#
#**
#  POST /ipds/rbl/<listname>
sub add_rbl_list
{
	my $json_obj = shift;
	my $listName = shift;
	
	my $errormsg;
	if ( ! &getValidFormat ( 'rbl_list_name', $listName ) )
	{
		$errormsg = "In list name only is allowed alphanumeric characters.";
	}
	
	if ( &getRBLListLocalitation ( $listName ) != -1 )
	{
		$errormsg = "A list with name '$listName' just exists";
	}
	
	if (! exists $json_obj->{'type'} )
	{
		$errormsg = "It's neccesary pass 'type' parameter";
	}
	
	if ( ! exists $json_obj->{'location'} )
	{
		$errormsg = "It's neccesary pass 'location' parameter";
	}
	
	if ( !$errormsg )
	{
		my $error;
		if ( $json_obj->{'location'} eq 'local' )
		{
			$error = &setRBLCreateLocalList ( $listName, $json_obj->{'type'} );
		}
		
		elsif ( $json_obj->{'location'} eq 'remote' )
		{
			if ( exists $json_obj->{'url'} )
			{
				$error = &setRBLCreateRemoteList ( $listName, $json_obj->{'type'}, $json_obj->{'url'} );
			}
			else
			{
				$errormsg = "It's neccesary add 'url' parameter in 'remote' lists";
			}
		}
		$errormsg = "There was a error creating a new list. Check the logs." if ( $error );
	}
	
	if ( !$errormsg )
	{
		my $listHash = &get_rbl_list ( $listName, 1 );
		&httpResponse({ code => 200, body => { description => "Post list $listName", params => $listHash} });
	}
	else
	{
		my $body = {
					   description => "Post list '$listName'",
					   error       => "true",
					   message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
};


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
#       -u zapi:<password> -d '{"type":"allow","list":["192.168.100.240","21.5.6.4"],
#       "name":"newNameList"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/rbl/list
#
# @apiSampleRequest off
#
#**
#  PUT /ipds/rbl/<listname>
sub set_rbl_list 
{
	my $json_obj = shift;
	my $listName = shift;

	my $err;
	my $flag;
	my $errormsg;
	
	if ( &getRBLListLocalitation ( $listName ) != -1 )
	{
		# delete all keys don't defined
		foreach my $key ( keys %{ $json_obj } )
		{
			if ( $key eq 'list' || $key eq 'status' || $key eq 'url' || $key eq 'type' )
			{
				if ( $key eq 'list' )
				{
					my @ipList = grep ( /((?:\d{1,3}\.){3}\d{1,3}(?:\/\d{1,2})?)/, @{$json_obj->{'list'}} );
					$json_obj->{'list'} = \@ipList;
				}
				$err = &setRBLListParam ( $listName, $key, $json_obj->{$key} );
			}
			# rename will done last
			if ($key eq 'name')
			{
				$flag = 1;
			}
		}
		
		if ( $flag )
		{
			$err = &setRBLListParam ( $listName, 'name', $json_obj->{'name'} ) if ( $listName ne $json_obj->{'name'} );
		}
	}
	else
	{
		$errormsg = "$listName don't exist.";
	}
	
	
	if ( !$err && !$errormsg )
	{
		$newListName = $listName;
		$newListName = $json_obj->{'name'} if ( exists $json_obj->{'name'} );
		
		my $listHash = &get_rbl_list ( $newListName, 1 );
		&httpResponse({ code => 200, body => { description => "Put list $listName", params => $listHash} });
	}
	else
	{
		$errormsg = "There was a error putting list $listName" if ( ! $errormsg );
		my $body = {
					   description => "Put list '$listName'",
					   error       => "true",
					   message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
	
};


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
#       -u zapi:<password> https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/rbl/listname
#
# @apiSampleRequest off
#
#**
sub del_rbl_list
{
	my $listName = shift;
	
	my $errormsg;
	my $err = &getRBLListLocalitation ( $listName );
	if ( $err != -1 )
	{
		$err = &setRBLDeleteList ( $listName );
	}
	else
	{
		$errormsg = "$listName don't exist.";	
	}
	
	if ( !$err )
	{
		$errormsg = "The list $listName has been deleted";
		
		my $body = {
			description => "Delete list '$listName'",
			success     => "true",
			message     => $errormsg,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		$errormsg = "There was a error deleting list $listName" if (!$errormsg);

		my $body = {
			description => "Delete list '$listName'",
			error       => "true",
			message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
	
};


#####Documentation of POST a RBL list source####
#**
#  @api {post} /ipds/rbl/<listname>/list Create a new rbl list source
#  @apiGroup IPDS
#  @apiName PostRblListSource
#  @apiParam {String} listname  Rbl list name, unique ID.
#  @apiDescription Add a source to specific list
#  @apiVersion 3.0
#
#
#
# @apiSuccess   {String}	source		New IP or net segment to add a list.
#
#
#
#@apiSuccessExample Success-Response:
#{
#   "description" : "Post source to list",
#   "params" : [
#      "192.168.100.240",
#      "21.5.6.4",
#      "16.31.0.223"
#   ]
#}
#
# @apiExample {curl} Example Usage:
#		curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>" 
#		-d '{"source":"16.31.0.223"}' -u zapi:<password> https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/rbl/list
#
# @apiSampleRequest off
#
#**
#  POST /ipds/rbl/<listname>/list
sub add_rbl_source 
{
	my $json_obj = shift;
	my $listName = shift;

	my $errormsg;
	
	if ( &getRBLListLocalitation ( $listName ) == -1 )
	{
		$errormsg = "$listName don't exist.";
	}
	
	if ( $json_obj->{'source'} !~ /((?:\d{1,3}\.){3}\d{1,3}(?:\/\d{1,2})?)/ )
	{
		$errormsg = "source format is incorrect.";
	}
	
	if ( grep ( /$json_obj->{'source'}/, @ { &getRBLListParam ( $listName, 'list' ) } ) ) 
	{
		$errormsg = "$json_obj->{'source'} just exist in $listName.";
	}
	
	if ( ! $errormsg )
	{
		$errormsg = &setRBLAddSource ( $listName, $json_obj->{'source'} );
		my $errormsg = "There was a error posting a new source in $listName." if ( $errormsg != 0 );
	}
	
	if ( !$errormsg )
	{
		&httpResponse({ code => 200, body => { description => "Post source to $listName.", params => &getRBLListParam ( $listName, 'list' ) } });
	}
	else
	{
		my $body = {
		   description => "Post source to $listName",
		   error       => "true",
		   message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
};


#####Documentation of PUT a RBL list source####
#**
#  @api {put} /ipds/rbl/<listname>/list/<id> Modify a source from a rbl list
#  @apiGroup IPDS
#  @apiName PutRblListSource
#  @apiParam	{String}	listname	RBL list name, unique ID.
#  @apiParam	{number}	id			Source ID to modificate.
#  @apiDescription Modify a source from a RBL list
#  @apiVersion 3.0
#
#
#  @apiSuccess	{String}	source		IP or net segment to modificate in a rbl list.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Post source to list",
#   "params" : [
#      "192.168.100.240",
#      "10.12.55.3"
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"source":"10.12.55.3" https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/rbl/list/1
#
# @apiSampleRequest off
#
#**
#  PUT /ipds/rbl/<listname>/list/<id>
sub set_rbl_source
{
	my $json_obj = shift;
	my $listName = shift;
	my $id = shift;

	my $errormsg;

	# check list exists and source is successful
	if ( &getRBLListLocalitation ( $listName ) == -1 )
	{
		$errormsg = "$listName don't found";
	}
		
	if ( !$errormsg )
	{
		if ( $json_obj->{'source'} !~ /((?:\d{1,3}\.){3}\d{1,3}(?:\/\d{1,2})?)/ )
		{
			$errormsg = "Wrong format to source.";
		}
		
		if ( &setRBLModifSource ( $listName, $id, $json_obj->{'source'} ) != 0 )
		{
			$errormsg = "There was a error putting a source in $listName.";
		}
	}
	
	if ( !$errormsg )
	{	
		&httpResponse({ code => 200, body => { description => "Post source to $listName", params => &getRBLListParam ( $listName, 'list' ) } });
	}
	else
	{
		my $body = {
		   description => "Put source to $listName",
		   error       => "true",
		   message     => $errormsg,
		};
		&httpResponse({ code => 400, body => $body });
	}
	
};


#####Documentation of DELETE a RBL list source####
#**
#  @api {delete} /ipds/rbl/<listname>/list/<id>	Delete a source from a rbl list
#  @apiGroup IPDS
#  @apiName DeleteRblList
#  @apiParam	{String}	listname	rbl list name, unique ID.
#  @apiParam	{number}	id			Source ID to delete.
#  @apiDescription Delete a given rbl list source
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
#       -u zapi:<password> https://<zenlb_server>:444/zapi/v3/zapi.cgi/ipds/rbl/list/list/1
#
# @apiSampleRequest off
#
#**
sub del_rbl_source
{
	my $listName = shift;
	my $id = shift;
	
	my $errormsg;
	
	if ( &getRBLListLocalitation ( $listName ) == -1 )
	{
		$errormsg = "$listName don't exist.";
	}
		
	if ( @{ &getRBLListParam ( $listName, 'list' ) } <= $id )
	{
		$errormsg = "ID $id don't exist in $listName.";
	}
		
	if ( !$errormsg )
	{
		if ( &setRBLDeleteSource ( $listName, $id ) != 0 )
		{
			$errormsg = "There was a error deleting source $id";
		}
	}
		
	if ( ! $errormsg )
	{
		my $errormsg = "Source $id has been deleted.";
		
		my $body = {
			description => "Delete source from '$listName'",
			success     => "true",
			message     => $errormsg,
		};
				
		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		my $body = {
			description => "Delete source from '$listName'",
			error       => "true",
			message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
};


#####Documentation of POST a RBL list source####
#**
#  @api {post} /farms/<farmname>/ipds/rbl	Create a new rbl rule to a farm
#  @apiGroup IPDS
#  @apiName PostRblListToFarm
#  @apiParam {String} farmname	farm name, unique ID.
#  @apiDescription Add a rbl rule to a farm
#  @apiVersion 3.0
#
#
#
# @apiSuccess   {String}	listname		Existing rbl list.
#
#
#
#@apiSuccessExample Success-Response:
#{
#   "description" : "Apply list listName to farm dns",
#   "message" : "List listName was applied successful to farm dns.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#		curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>" 
#		-d '{"listname":"listName"}' -u zapi:<password> https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/dns/ipds/rbl
#
# @apiSampleRequest off
#
#**
#  POST /farms/<farmname>/ipds/rbl
sub add_rbl_to_farm
{
	my $json_obj = shift;
	my $farmName = shift;
	
	my $err;
	my @rules = &getIptList( $farmName, 'raw', 'PREROUTING' );
	
	if ( &getRBLListLocalitation ( $json_obj->{'listname'} ) == -1 ||
		grep ( /^\s*(\d+).+match-set $json_obj->{'listname'} src .+RBL_$farmName/, @rules ) )
	{
		$err = 1;
	}
	else
	{
		$err = &setRBLCreateRule  ( $farmName, $json_obj->{'listname'} );
	}
	
	if ( !$err )
	{
		my $errormsg = "List $json_obj->{'listname'} was applied successful to farm $farmName.";
		
		my $body = {
			description => "Apply list $json_obj->{'listname'} to farm $farmName",
			success     => "true",
			message     => $errormsg,
		};
				
		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		my $errormsg = "There was a error applying $json_obj->{'listname'} to $farmName.";
		
		my $body = {
			description	 => "Apply list $json_obj->{'listname'} to farm $farmName",
			error	     => "true",
			message		 => $errormsg,
		};
		
		&httpResponse({ code => 400, body => $body });
	}
	
};


#####Documentation of DELETE a RBL rule for a farm####
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
#       -u zapi:<password> https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/dns/ipds/rbl/listName
#
# @apiSampleRequest off
#
#**
# DELETE /farms/<farmname>/ipds/rbl/<listname>
sub del_rbl_from_farm
{
	my $farmName = shift;
	my $listName = shift;
	
	my $err = &getRBLListLocalitation ( $listName );
	if ( $err != -1 )
	{
 		$err = &setRBLDeleteRule ( $farmName, $listName );
	}
	
	if ( !$err )
	{
		my $errormsg = "List $listName was removed successful from farm $farmName.";
		
		my $body = {
			description => "Delete list $listName form farm $farmName",
			success     => "true",
			message     => $errormsg,
		};
				
		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		my $errormsg = "There was a error removing $listName from $farmName.";
		
		my $body = {
			description	 => "Delete list $listName form farm $farmName",
			error	     => "true",
			message		 => $errormsg,
		};
		
		&httpResponse({ code => 400, body => $body });
	}
	
};


1;
