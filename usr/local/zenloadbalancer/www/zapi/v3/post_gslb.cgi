#!/usr/bin/perl -w

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

#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -d '{"id":"zone123.com"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB/zones
#
#
#####Documentation of POST ZONES GSLB####
#**
#  @api {post} /farms/<farmname>/zones Create a new zone in a gslb Farm
#  @apiGroup Farm Create
#  @apiName PostZoneGSLB
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Create a new zone in a given gslb Farm
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {String}        id                     Zone's name.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "New zone zone1",
#   "params" : [
#      {
#         "id" : "myzone.com"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"id":"myzone.com"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmGSLB/zones
#
# @apiSampleRequest off
#
#**

sub new_farm_zone # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	my $zone = $json_obj->{ id };

	if ( $farmname =~ /^$/ )
	{
		&zenlog(
			 "ZAPI error, trying to create a new zone in farm $farmname, invalid farm name."
		);

		# Error
		my $errormsg = "Invalid farm name, please insert a valid value.";
		my $body = {
					 description => "New zone",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
	
	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 ) {
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => "New zone",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	if ( $json_obj->{ id } =~ /^$/ )
	{
		&zenlog(
			 "ZAPI error, trying to create a new zone in farm $farmname, invalid zone name."
		);

		# Error
		my $errormsg = "Invalid zone name, please insert a valid value.";
		my $body = {
					 description => "New zone " . $json_obj->{ id },
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( $json_obj->{ id } !~ /.*\..*/ )
	{
		&zenlog(
			"Wrong zone name. The name has to be like zonename.com, zonename.net, etc. The zone $zone can't be created"
		);

		# Error
		my $errormsg =
		  "Invalid zone name, please insert a valid value like zonename.com, zonename.net, etc. The zone $zone can't be created.";
		my $body = {
								   description => "New zone " . $json_obj->{ id },
								   error       => "true",
								   message     => $errormsg
								 };

		&httpResponse({ code => 400, body => $body });
	}

	my $result = &setGSLBFarmNewZone( $farmname, $json_obj->{ id } );
	if ( $result eq "0" )
	{
		&zenlog(
			"ZAPI success, a new zone has been created in farm $farmname with id $json_obj->{id}."
		);

		# Success
		&runFarmReload( $farmname );

		my $body = {
					 description => "New zone " . $json_obj->{ id },
					 params      => { id => $json_obj->{ id } },
		};

		&httpResponse({ code => 201, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to create a new zone in farm $farmname with id $json_obj->{id}, it's not possible to create the zone."
		);

		# Error
		my $errormsg = "It's not possible to create the zone " . $json_obj->{ id };
		my $body = {
								   description => "New zone " . $json_obj->{ id },
								   error       => "true",
								   message     => $errormsg
								 };

		&httpResponse({ code => 400, body => $body });
	}
}

#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -d '{"zone":"zone123","rname":"resource1","ttl":"10","type":"NS","rdata":"1.1.1.1"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB/zoneresources
#
#
#####Documentation of POST RESOURCES GSLB####
#**
#  @api {post} /farms/<farmname>/zoneresources Create a new resource of a zone in a gslb Farm
#  @apiGroup Farm Create
#  @apiName PostZoneResourceGSLB
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Create a new resource of a zone in a given gslb Farm
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {String}        rname                     Resource's name.
# @apiSuccess   {rdata}         rdata                   It’s the real data needed by the record type.
# @apiSuccess   {Number}        ttl                     The Time to Live value for the current record.
# @apiSuccess   {String}        type                    DNS record type. The options are: NS, A, CNAME and DYNA.
# @apiSuccess   {String}        zone                    It's the zone where the resource will be created.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "New zone resource resource2",
#   "params" : [
#      {
#         "rname" : "resource2",
#         "rdata" : "192.168.0.9",
#         "ttl" : "10",
#         "type" : "NS",
#         "zone" : "zone1.com"
#      }
#   ]
#}
#
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"rname":"resource2", "rdata":"192.168.0.9", "ttl":"10", "type":"NS",
#       "zone":"zone1.com"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmGSLB/zoneresources
#
# @apiSampleRequest off
#
#**

sub new_farm_zoneresource # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	if ( $farmname =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to create a new resource in zone $json_obj->{zone} in farm $farmname, invalid farm name."
		);

		# Error
		my $errormsg = "Invalid farm name, please insert a valid value.";
		my $body = {
					 description => "New zone resource",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
	
	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => "New zone resource",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	if ( !exists ( $json_obj->{ rname } ) )
	{
		&zenlog(
			"ZAPI error, trying to create a new resource in zone $json_obj->{zone} in farm $farmname, the parameter zone resource name (rname) doesn't exist."
		);

		# Error
		my $errormsg =
		  "The parameter zone resource name (rname) doesn't exist, please insert a valid value.";
		my $body = {
					 description => "New zone resource " . $json_obj->{ rname },
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( !exists ( $json_obj->{ rdata } ) )
	{
		&zenlog(
			"ZAPI error, trying to create a new resource in zone $json_obj->{zone} in farm $farmname, the parameter zone resource server (rdata) doesn't exist."
		);

		# Error
		my $errormsg =
		  "The parameter zone resource server (rdata) doesn't exist, please insert a valid value.";
		my $body = {
					 description => "New zone resource " . $json_obj->{ rname },
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( !exists ( $json_obj->{ ttl } ) )
	{
		&zenlog(
			"ZAPI error, trying to create a new resource in zone $json_obj->{zone} in farm $farmname, the parameter time to live value (ttl) doesn't exist."
		);

		# Error
		my $errormsg =
		  "The parameter time to live value (ttl) doesn't exist, please insert a valid value.";
		my $body = {
					 description => "New zone resource " . $json_obj->{ rname },
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( !exists ( $json_obj->{ type } ) )
	{
		&zenlog(
			"ZAPI error, trying to create a new resource in zone $json_obj->{zone} in farm $farmname, the parameter DNS record type (type) doesn't exist."
		);

		# Error
		my $errormsg =
		  "The parameter DNS record type (type) doesn't exist, please insert a valid value.";
		my $body = {
					 description => "New zone resource " . $json_obj->{ rname },
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( $json_obj->{ rname } =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to create a new resource in zone $json_obj->{zone} in farm $farmname, invalid zone resource name (rname)."
		);

		# Error
		my $errormsg =
		  "Invalid zone resource name (rname), please insert a valid value.";
		my $body = {
					 description => "New zone resource " . $json_obj->{ rname },
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( $json_obj->{ rdata } =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to create a new resource in zone $json_obj->{zone} in farm $farmname, invalid zone resource server (rdata)."
		);

		# Error
		my $errormsg =
		  "Invalid zone resource server (rdata), please insert a valid value.";
		my $body = {
					 description => "New zone resource " . $json_obj->{ rname },
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( $json_obj->{ ttl } =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to create a new resource in zone $json_obj->{zone} in farm $farmname, invalid time to live value (ttl)."
		);

		# Error
		my $errormsg = "Invalid time to live value (ttl), please insert a valid value.";
		my $body = {
					 description => "New zone resource " . $json_obj->{ rname },
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( $json_obj->{ type } =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to create a new resource in zone $json_obj->{zone} in farm $farmname, invalid DNS record type (type)."
		);

		# Error
		my $errormsg = "Invalid DNS record type (type), please insert a valid value.";
		my $body = {
					 description => "New zone resource " . $json_obj->{ rname },
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	$status = &setFarmZoneResource(
									"",
									$json_obj->{ rname },
									$json_obj->{ ttl },
									$json_obj->{ type },
									$json_obj->{ rdata },
									$farmname,
									$json_obj->{ zone }
	);

	if ( $status != -1 )
	{
		&zenlog(
			"ZAPI success, a new resource has been created in zone $json_obj->{zone} in farm $farmname."
		);

		# Success
		&runFarmReload( $farmname );

		my $body = {
					 description => "New zone resource " . $json_obj->{ rname },
					 params      => {
								 rname => $json_obj->{ rname },
								 zone  => $json_obj->{ zone },
								 ttl   => $json_obj->{ ttl },
								 type  => $json_obj->{ type },
								 rdata => $json_obj->{ rdata },
					 },
		};

		&httpResponse({ code => 201, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to create a new resource in zone $json_obj->{zone} in farm $farmname, it's not possible to create a new resource."
		);

		# Error
		my $errormsg =
		  "It's not possible to create a new resource in the zone $json_obj->{zone} in farm $farmname.";
		my $body = {
					 description => "New zone resource " . $json_obj->{ rname },
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

1;
