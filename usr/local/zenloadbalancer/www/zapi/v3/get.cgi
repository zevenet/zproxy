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

require "/usr/local/zenloadbalancer/www/zapi/v3/get_tcp.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/get_http.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/get_gslb.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/get_l4.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/get_datalink.cgi";

#**
#  @api {get} /farms Request farms list
#  @apiGroup Farm Get
#  @apiDescription Get the list of all Farms
#  @apiName GetFarmList
#  @apiVersion 2.1.0
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
#	-u zapi:<password> https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms
#
#@apiSampleRequest off
#**
#GET /farms
sub farms # ()
{
	my $out   = [];
	my @files = &getFarmList();

	foreach my $file ( @files )
	{
		my $name   = &getFarmName( $file );
		my $type   = &getFarmType( $name );
		my $status = &getFarmStatus( $name );
		my $vip    = &getFarmVip( $name );
		my $port   = &getFarmPort( $name );

		# FIXME: Add ip and port
		push $out,
		  {
			farmname => $name,
			profile  => $type,
			status   => $status,
			vip      => $vip,
			vport    => $port
		  };
	}

	# Success
	&httpResponse(
				   {
					 code => 200,
					 body      => {
							   description => "List farms",
							   params      => $out
					 }
				   }
	);
}

#GET /farms/<name>
sub farms_name()
{
	
	use Switch;
	use CGI;
	my $q = CGI->new;
	my $j = JSON::XS->new->utf8->pretty(1);
	$j->canonical([$enabled]);

	# Check that the farm exists
	if ( &getFarmFile( $1 ) == -1 ) {
		# Error
		print $q->header(
		-type=> 'text/plain',
		-charset=> 'utf-8',
		-status=> '404 Not Found',
		'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg = "The farmname $1 does not exist.";
		my $output = $j->encode({
				description => "Get farm",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}
	
	my $type = &getFarmType( $1 );

	switch ( $type )
	{
		case /tcp|udp/  { &farms_name_tcp() }
		case /http.*/   { &farms_name_http() }
		case /gslb/     { &farms_name_gslb() }
		case /l4xnat/   { &farms_name_l4() }
		case /datalink/ { &farms_name_datalink() }

	}
}

1
