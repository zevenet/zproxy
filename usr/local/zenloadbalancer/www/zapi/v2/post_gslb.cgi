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
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"id":"zone123.com"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB/zones
#
#
#####Documentation of POST ZONES GSLB####
#**
#  @api {post} /farms/<farmname>/zones Create a new zone in a gslb Farm
#  @apiGroup Farm Create
#  @apiName PostZoneGSLB
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Create a new zone in a given gslb Farm
#  @apiVersion 2.0.0
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
#       -u zapi:<password> -d '{"id":"myzone.com"}' https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/FarmGSLB/zones
#
# @apiSampleRequest off
#
#**

sub new_farm_zone()
{

	$farmname = @_[0];

	my $out_p = [];

	use CGI;
	use JSON;

	my $q        = CGI->new;
	my $json     = JSON->new;
	my $data     = $q->param( 'POSTDATA' );
	my $json_obj = $json->decode( $data );
	my $zone     = $json_obj->{ id };

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );

	if ( $farmname =~ /^$/ )
	{
		&logfile(
			 "ZAPI error, trying to create a new zone in farm $farmname, invalid farm name."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode(
								 {
								   description => "New zone",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}
	
	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 ) {
		# Error
		print $q->header(
		-type=> 'text/plain',
		-charset=> 'utf-8',
		-status=> '404 Not Found'
		);
		$errormsg = "The farmname $farmname does not exists.";
		my $output = $j->encode({
				description => "New zone",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}

	if ( $json_obj->{ id } =~ /^$/ )
	{
		&logfile(
			 "ZAPI error, trying to create a new zone in farm $farmname, invalid zone name."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "Invalid zone name, please insert a valid value.";
		my $output = $j->encode(
								 {
								   description => "New zone " . $json_obj->{ id },
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}

	if ( $json_obj->{ id } !~ /.*\..*/ )
	{
		&logfile(
			"Wrong zone name. The name has to be like zonename.com, zonename.net, etc. The zone $zone can't be created"
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg =
		  "Invalid zone name, please insert a valid value like zonename.com, zonename.net, etc. The zone $zone can't be created.";
		my $output = $j->encode(
								 {
								   description => "New zone " . $json_obj->{ id },
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}

	my $result = &setGSLBFarmNewZone( $farmname, $json_obj->{ id } );
	if ( $result eq "0" )
	{
		&logfile(
			"ZAPI success, a new zone has been created in farm $farmname with id $json_obj->{id}."
		);

		# Success
		&runFarmReload( $farmname );
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '201 Created'
		);
		push $out_p, { id => $json_obj->{ id } };

		my $j = JSON::XS->new->utf8->pretty( 1 );
		$j->canonical( $enabled );
		my $output = $j->encode(
								 {
								   description => "New zone " . $json_obj->{ id },
								   params      => $out_p
								 }
		);
		print $output;

	}
	else
	{
		&logfile(
			"ZAPI error, trying to create a new zone in farm $farmname with id $json_obj->{id}, it's not possible to create the zone."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "It's not possible to create the zone " . $json_obj->{ id };
		my $output = $j->encode(
								 {
								   description => "New zone " . $json_obj->{ id },
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}

}

#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"zone":"zone123","rname":"resource1","ttl":"10","type":"NS","rdata":"1.1.1.1"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB/zoneresources
#
#
#####Documentation of POST RESOURCES GSLB####
#**
#  @api {post} /farms/<farmname>/zoneresources Create a new resource of a zone in a gslb Farm
#  @apiGroup Farm Create
#  @apiName PostZoneResourceGSLB
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Create a new resource of a zone in a given gslb Farm
#  @apiVersion 2.0.0
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
#       -u zapi:<password> -d '{"rname":"resource2", "rdata":"192.168.0.9", "ttl":"10", "type":"NS",
#       "zone":"zone1.com"}' https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/FarmGSLB/zoneresources
#
# @apiSampleRequest off
#
#**

sub new_farm_zoneresource()
{

	$farmname = @_[0];

	my $out_p = [];

	use CGI;
	use JSON;

	my $q        = CGI->new;
	my $json     = JSON->new;
	my $data     = $q->param( 'POSTDATA' );
	my $json_obj = $json->decode( $data );

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );

	if ( $farmname =~ /^$/ )
	{
		&logfile(
			"ZAPI error, trying to create a new resource in zone $json_obj->{zone} in farm $farmname, invalid farm name."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode(
								 {
								   description => "New zone resource",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}
	
	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 ) {
		# Error
		print $q->header(
		-type=> 'text/plain',
		-charset=> 'utf-8',
		-status=> '404 Not Found'
		);
		$errormsg = "The farmname $farmname does not exists.";
		my $output = $j->encode({
				description => "New zone resource",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}

	if ( !exists ( $json_obj->{ rname } ) )
	{
		&logfile(
			"ZAPI error, trying to create a new resource in zone $json_obj->{zone} in farm $farmname, the parameter zone resource name (rname) doesn't exist."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg =
		  "The parameter zone resource name (rname) doesn't exist, please insert a valid value.";
		my $output = $j->encode(
							  {
								description => "New zone resource " . $json_obj->{ rname },
								error       => "true",
								message     => $errormsg
							  }
		);
		print $output;
		exit;
	}

	if ( !exists ( $json_obj->{ rdata } ) )
	{
		&logfile(
			"ZAPI error, trying to create a new resource in zone $json_obj->{zone} in farm $farmname, the parameter zone resource server (rdata) doesn't exist."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg =
		  "The parameter zone resource server (rdata) doesn't exist, please insert a valid value.";
		my $output = $j->encode(
							  {
								description => "New zone resource " . $json_obj->{ rname },
								error       => "true",
								message     => $errormsg
							  }
		);
		print $output;
		exit;
	}

	if ( !exists ( $json_obj->{ ttl } ) )
	{
		&logfile(
			"ZAPI error, trying to create a new resource in zone $json_obj->{zone} in farm $farmname, the parameter time to live value (ttl) doesn't exist."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg =
		  "The parameter time to live value (ttl) doesn't exist, please insert a valid value.";
		my $output = $j->encode(
							  {
								description => "New zone resource " . $json_obj->{ rname },
								error       => "true",
								message     => $errormsg
							  }
		);
		print $output;
		exit;
	}

	if ( !exists ( $json_obj->{ type } ) )
	{
		&logfile(
			"ZAPI error, trying to create a new resource in zone $json_obj->{zone} in farm $farmname, the parameter DNS record type (type) doesn't exist."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg =
		  "The parameter DNS record type (type) doesn't exist, please insert a valid value.";
		my $output = $j->encode(
							  {
								description => "New zone resource " . $json_obj->{ rname },
								error       => "true",
								message     => $errormsg
							  }
		);
		print $output;
		exit;
	}

	if ( $json_obj->{ rname } =~ /^$/ )
	{
		&logfile(
			"ZAPI error, trying to create a new resource in zone $json_obj->{zone} in farm $farmname, invalid zone resource name (rname)."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "Invalid zone resource name (rname), please insert a valid value.";
		my $output = $j->encode(
							  {
								description => "New zone resource " . $json_obj->{ rname },
								error       => "true",
								message     => $errormsg
							  }
		);
		print $output;
		exit;
	}

	if ( $json_obj->{ rdata } =~ /^$/ )
	{
		&logfile(
			"ZAPI error, trying to create a new resource in zone $json_obj->{zone} in farm $farmname, invalid zone resource server (rdata)."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg =
		  "Invalid zone resource server (rdata), please insert a valid value.";
		my $output = $j->encode(
							  {
								description => "New zone resource " . $json_obj->{ rname },
								error       => "true",
								message     => $errormsg
							  }
		);
		print $output;
		exit;
	}

	if ( $json_obj->{ ttl } =~ /^$/ )
	{
		&logfile(
			"ZAPI error, trying to create a new resource in zone $json_obj->{zone} in farm $farmname, invalid time to live value (ttl)."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "Invalid time to live value (ttl), please insert a valid value.";
		my $output = $j->encode(
							  {
								description => "New zone resource " . $json_obj->{ rname },
								error       => "true",
								message     => $errormsg
							  }
		);
		print $output;
		exit;
	}

	if ( $json_obj->{ type } =~ /^$/ )
	{
		&logfile(
			"ZAPI error, trying to create a new resource in zone $json_obj->{zone} in farm $farmname, invalid DNS record type (type)."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "Invalid DNS record type (type), please insert a valid value.";
		my $output = $j->encode(
							  {
								description => "New zone resource " . $json_obj->{ rname },
								error       => "true",
								message     => $errormsg
							  }
		);
		print $output;
		exit;
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
		&logfile(
			"ZAPI success, a new resource has been created in zone $json_obj->{zone} in farm $farmname."
		);

		# Success
		&runFarmReload( $farmname );
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '201 Created'
		);
		push $out_p,
		  {
			rname => $json_obj->{ rname },
			zone  =>,
			$json_obj->{ zone },
			ttl   => $json_obj->{ ttl },
			type  => $json_obj->{ type },
			rdata => $json_obj->{ rdata }
		  };

		my $j = JSON::XS->new->utf8->pretty( 1 );
		$j->canonical( $enabled );
		my $output = $j->encode(
							  {
								description => "New zone resource " . $json_obj->{ rname },
								params      => $out_p
							  }
		);
		print $output;

	}
	else
	{
		&logfile(
			"ZAPI error, trying to create a new resource in zone $json_obj->{zone} in farm $farmname, it's not possible to create a new resource."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg =
		  "It's not possible to create a new resource in the zone $json_obj->{zone} in farm $farmname.";
		my $output = $j->encode(
							  {
								description => "New zone resource " . $json_obj->{ rname },
								error       => "true",
								message     => $errormsg
							  }
		);
		print $output;
		exit;
	}
}

1

