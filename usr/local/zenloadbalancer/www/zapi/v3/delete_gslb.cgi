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
# curl --tlsv1 -k -X DELETE -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB/zones/myzone.com
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
#  @apiVersion 3.0.0
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
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmGSLB/zones/myzone.com
#
# @apiSampleRequest off
#
#**

sub delete_zone # ( $farmname, $zone )
{
	my ( $farmname, $zone ) = @_;

	if ( $farmname =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to delete the zone $zone in farm $farmname, invalid farm name."
		);

		# Error
		my $errormsg = "Invalid farm name, please insert a valid value.";
		my $body = {
					 description => "Delete zone",
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
					 description => "Delete zone",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	if ( $zone =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to delete the zone $zone in farm $farmname, invalid zone name."
		);

		# Error
		my $errormsg = "Invalid zone name, please insert a valid value.";
		my $output = {
					   description => "Delete zone",
					   error       => "true",
					   message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	&setGSLBFarmDeleteZone( $farmname, $zone );

	if ( $? eq 0 )
	{
		&zenlog( "ZAPI success, the zone $zone in farm $farmname has been deleted." );

		# Success
		&runFarmReload( $farmname );

		my $message = "The zone $zone in farm $farmname has been deleted.";
		my $body = {
								   description => "Delete zone $zone in farm $farmname.",
								   success     => "true",
								   message     => $message
								 };

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to delete the zone $zone in farm $farmname, the zone hasn't been deleted."
		);

		# Error
		my $errormsg = "Zone $zone in farm $farmname hasn't been deleted.";
		my $body = {
					 description => "Delete zone $zone in farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

#
# curl --tlsv1 -k -X DELETE -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB/zones/myzone.com/resources/0
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
#  @apiVersion 3.0.0
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
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmGSLB/zones/myzone.com/resources/2
#
# @apiSampleRequest off
#
#**

sub delete_zone_resource # ( $farmname, $zone, $resource )
{
	my ( $farmname, $zone, $resource ) = @_;

	my $description = "Delete zone resource";

	# validate FARM NAME
	if ( &getFarmFile( $farmname ) == -1 )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# validate FARM TYPE
	if ( &getFarmType( $farmname ) ne 'gslb' )
	{
		my $errormsg = "Only GSLB profile is supported for this request.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# validate ZONE
	if ( ! scalar grep { $_ eq $zone } &getFarmZones( $farmname ) )
	{
		&zenlog(
			"ZAPI error, trying to delete the resource $resource in zone $zone in farm $farmname, invalid zone name."
		);

		# Error
		my $errormsg = "Invalid zone name, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $backendsvs = &getFarmVS( $farmname, $zone, "resources" );
	my @be = split ( "\n", $backendsvs );
	my ( $resource_line ) = grep { /;index_$resource$/ } @be;

	# validate RESOURCE
	if ( ! $resource_line )
	{
		&zenlog(
			"ZAPI error, trying to delete the resource $resource in zone $zone in farm $farmname, invalid resource id."
		);

		# Error
		my $errormsg = "Invalid resource id, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $status = &remFarmZoneResource( $resource, $farmname, $zone );

	if ( $status != -1 )
	{
		&zenlog(
			"ZAPI success, the resource $resource in zone $zone in farm $farmname has been deleted."
		);

		# Success
		&runFarmReload( $farmname );
		#~ my $message = "The resource with id $resource in the zone $zone of the farm $farmnamehas been deleted.";
		my $message = "Resource removed";
		my $body = {
					 description => $description,
					 success     => "true",
					 message     => $message,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to delete the resource $resource in zone $zone in farm $farmname, it's not possible to delete the resource."
		);

		# Error
		my $errormsg =
		  "It's not possible to delete the resource with id $resource in the zone $zone of the farm $farmname.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
}

1;
