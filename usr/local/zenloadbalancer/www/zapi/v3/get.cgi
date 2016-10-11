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

require "/usr/local/zenloadbalancer/www/zapi/v3/get_http.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/get_gslb.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/get_l4.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/get_datalink.cgi";

#**
#  @api {get} /farms Request farms list
#  @apiGroup Farm Get
#  @apiDescription Get the list of all Farms
#  @apiName GetFarmList
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "List farms",
#   "params" : [
#      {
#         "farmname" : "newfarmGSLB55",
#         "profile" : "gslb",
#         "status" : "up"
#      }
#   ]
#}
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms
#
#@apiSampleRequest off
#**
#GET /farms
sub farms # ()
{
	my @out;
	my @files = &getFarmList();

	foreach my $file ( @files )
	{
		my $name   = &getFarmName( $file );
		my $type   = &getFarmType( $name );
		my $status = &getFarmStatus( $name );
		my $vip    = &getFarmVip( 'vip', $name );
		my $port   = &getFarmVip( 'vipp', $name );

		push @out,
		  {
			farmname => $name,
			profile  => $type,
			status   => $status,
			vip      => $vip,
			vport    => $port
		  };
	}

	my $body = {
				description => "List farms",
				params      => \@out,
	};

	# Success
	&httpResponse({ code => 200, body => $body });
}

#GET /farms/<name>
sub farms_name # ( $farmname )
{
	my $farmname = shift;
	
	use Switch;

	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exist.";
		my $body = {
				description => "Get farm",
				error => "true",
				message => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}
	
	my $type = &getFarmType( $farmname );

	switch ( $type )
	{
		case /http.*/   { &farms_name_http( $farmname ) }
		case /gslb/     { &farms_name_gslb( $farmname ) }
		case /l4xnat/   { &farms_name_l4( $farmname ) }
		case /datalink/ { &farms_name_datalink( $farmname ) }
	}
}

1;
