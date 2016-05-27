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
# curl --tlsv1 -k -X DELETE -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB/zones/myzone.com
#
#
#####Documentation of DELETE ZONE####
#**
#  @api {delete} /farms/<farmname>/zones/<zonename> Delete a zone of a  gslb Farm
#  @apiGroup Farm Delete
#  @apiName DeleteZone
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {String} zonename  Zone name, unique ID.
#  @apiDescription Delete a given zone of a gslb Farm
#  @apiVersion 2.1.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Delete zone myzone.com in farm FarmGSLB",
#   "message" : "The zone myzone.com in farm FarmGSLB has been deleted.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> https://<zenlb_server>:444/zapi/v2.1/zapi.cgi/farms/FarmGSLB/zones/myzone.com
#
# @apiSampleRequest off
#
#**

sub delete_zone()
{

	my ( $farmname, $zone ) = @_;

	use CGI;
	my $q = CGI->new;

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );

	if ( $farmname =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to delete the zone $zone in farm $farmname, invalid farm name."
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
								   description => "Delete zone",
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
				description => "Delete zone",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}

	if ( $zone =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to delete the zone $zone in farm $farmname, invalid zone name."
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
								   description => "Delete zone",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}

	&setGSLBFarmDeleteZone( $farmname, $zone );

	if ( $? eq 0 )
	{
		&zenlog( "ZAPI success, the zone $zone in farm $farmname has been deleted." );

		# Success
		&runFarmReload( $farmname );
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '200 OK'
		);

		my $j = JSON::XS->new->utf8->pretty( 1 );
		$j->canonical( $enabled );

		$message = "The zone $zone in farm $farmname has been deleted.";
		my $output = $j->encode(
								 {
								   description => "Delete zone $zone in farm $farmname.",
								   success     => "true",
								   message     => $message
								 }
		);
		print $output;

	}
	else
	{
		&zenlog(
			"ZAPI error, trying to delete the zone $zone in farm $farmname, the zone hasn't been deleted."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "Zone $zone in farm $farmname hasn't been deleted.";
		my $output = $j->encode(
								 {
								   description => "Delete zone $zone in farm $farmname",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}
}

#
# curl --tlsv1 -k -X DELETE -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB/zones/myzone.com/resources/0
#
#
#####Documentation of DELETE RESOURCE in a ZONE####
#**
#  @api {delete} /farms/<farmname>/zones/<zonename>/resources/<resourceid> Delete a resource of a Zone
#  @apiGroup Farm Delete
#  @apiName DeleteResource
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {String} zonename  Zone name, unique ID.
#  @apiParam {Number} resourceid  Resource ID, unique ID.
#  @apiDescription Delete a given resource in a zone of a gslb Farm
#  @apiVersion 2.1.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Delete resource with ID 2 in the zone my zone.com of the farm FarmGSLB.",
#   "message" : "The resource with ID 2 in the zone myzone.com of the farm FarmGSLB has been deleted.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> https://<zenlb_server>:444/zapi/v2.1/zapi.cgi/farms/FarmGSLB/zones/myzone.com/resources/2
#
# @apiSampleRequest off
#
#**

sub delete_zone_resource()
{

	my ( $farmname, $zone, $id_server ) = @_;

	use CGI;
	my $q = CGI->new;

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );

	if ( $farmname =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to delete the resource $id_server in zone $zone in farm $farmname, invalid farm name."
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
								   description => "Delete zone resource",
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
				description => "Delete zone resource",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}

	if ( $zone =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to delete the resource $id_server in zone $zone in farm $farmname, invalid zone name."
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
								   description => "Delete zone resource",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}

	if ( $id_server =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to delete the resource $id_server in zone $zone in farm $farmname, invalid resource id."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "Invalid resource id, please insert a valid value.";
		my $output = $j->encode(
								 {
								   description => "Delete zone resource",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}

	$status = &remFarmZoneResource( $id_server, $farmname, $zone );
	if ( $status != -1 )
	{
		&zenlog(
			"ZAPI success, the resource $id_server in zone $zone in farm $farmname has been deleted."
		);

		# Success
		&runFarmReload( $farmname );
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '200 OK'
		);

		my $j = JSON::XS->new->utf8->pretty( 1 );
		$j->canonical( $enabled );

		$message =
		  "The resource with id $id_server in the zone $zone of the farm $farmnamehas been deleted.";
		my $output = $j->encode(
			{
			   description =>
				 "Delete resource with id $id_server in the zone $zone of the farm $farmname.",
			   success => "true",
			   message => $message
			}
		);
		print $output;

	}
	else
	{
		&zenlog(
			"ZAPI error, trying to delete the resource $id_server in zone $zone in farm $farmname, it's not possible to delete the resource."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg =
		  "It's not possible to delete the resource with id $id_server in the zone $zone of the farm $farmname.";
		my $output = $j->encode(
			{
			   description =>
				 "Delete resource with id $id_server in the zone $zone of the farm $farmname.",
			   error   => "true",
			   message => $errormsg
			}
		);
		print $output;
		exit;

	}
}

1

