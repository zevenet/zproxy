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

# PUT /farms/FarmL4/farmguardian
#
# L4XNAT:
#
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"fgtimecheck":"5","fgscript":"eyy","fgenabled":"true","fglog":"true"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/L4FARM/fg
#
# HTTP/HTTPS
#
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"fgtimecheck":"5","fgscript":"eyy","fgenabled":"true","fglog":"false","service":"sev1"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmHTTP/fg
#
#
#####Documentation of PUT FARMGUARDIAN####
#**
#  @api {put} /farms/<farmname>/fg Modify the parameters of the farm guardian in a Farm
#  @apiGroup Farm Guardian
#  @apiName PutFarmFG
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Modify the parameters of the farm guardian in a Farm with l4xnat profile
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {Number}                fgtimecheck     The farm guardian will check each 'timetocheck' seconds.
# @apiSuccess   {String}                fgscript        The command that farm guardian will check.
# @apiSuccess   {String}                fgenabled       Enabled the use of farm guardian. The options are: true and false.
# @apiSuccess   {String}                fglog           Enabled the use of logs in farm guardian. The options are: true and false.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify farm L4FARM",
#   "params" : [
#      {
#         "fglog" : "true"
#      },
#      {
#         "fgenabled" : "true"
#      },
#      {
#         "fgscript" : "Command of Farm Guardian"
#      },
#      {
#         "fgtimecheck" : "5"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"fgtimecheck":"5","fgscript":"Command of Farm Guardian",
#       "fgenabled":"true","fglog":"true"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/L4FARM/fg
#
# @apiSampleRequest off
#
#**
#####Documentation of PUT FARMGUARDIAN SERVICE####
#**
#  @api {put} /farms/<farmname>/fg Modify the parameters of the farm guardian in a Service
#  @apiGroup Farm Guardian
#  @apiName PutFarmFGS
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Modify the parameters of the farm guardian in a Service http|https
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {Number}                fgtimecheck     The farm guardian will check each 'timetocheck' seconds.
# @apiSuccess   {String}                fgscript                The command that farm guardian will check.
# @apiSuccess   {String}                fgenabled       Enabled the use of farm guardian.
# @apiSuccess   {String}                fglog           Enabled the use of logs in farm guardian.
# @apiSuccess   {String}                service         The Service's name which farm guardian will be modified.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify farm FarmHTTP",
#   "params" : [
#      {
#         "fglog" : "true"
#      },
#      {
#         "fgenabled" : "true"
#      },
#      {
#         "fgscript" : "Command of Farm Guardian"
#      },
#      {
#         "fgtimecheck" : "5"
#      }
#      {
#         "service" : "service1"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"fgtimecheck":"5","fgscript":"Command of Farm Guardian","fgenabled":"true",
#       "fglog":"true","service":"service1"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmHTTP/fg
#
# @apiSampleRequest off
#
#**

sub modify_farmguardian()
{

	$farmname = @_[0];

	my $out_p = [];

	use CGI;
	use JSON;
	use URI::Escape;

	my $q        = CGI->new;
	my $json     = JSON->new;
	my $data     = $q->param( 'PUTDATA' );
	my $json_obj = $json->decode( $data );

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );
	if ( $farmname =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to modify the farm guardian in a farm $farmname, invalid farmname, can't be blank."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode(
								 {
								   description => "Modify farm guardian",
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
		-status=> '404 Not Found',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg = "The farmname $farmname does not exists.";
		my $output = $j->encode({
				description => "Modify farm guardian",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}

	my $type = &getFarmType( $farmname );
	$error = "false";

	if ( exists ( $json_obj->{ service } ) )
	{
		if ( $json_obj->{ service } =~ /^$/ )
		{
			&zenlog(
				"ZAPI error, trying to modify the farm guardian in a farm $farmname, invalid service, can't be blank."
			);
			$error = "true";
		} else {
		
			# Check that the provided service is configured in the farm
			my @services;
			if ($type eq "gslb"){
				@services = &getGSLBFarmServices($farmname);
			} else {
				@services = &getFarmServices($farmname);
			}
			
			my $found = 0;
			foreach $farmservice (@services) {
				#print "service: $farmservice";
				if ($json_obj->{service} eq $farmservice) {
					$found = 1;
					break;
				}
			}
			if ($found eq 0){
				
				# Error
				print $q->header(
				-type=> 'text/plain',
				-charset=> 'utf-8',
				-status=> '400 Bad Request',
					  'Access-Control-Allow-Origin'  => '*'
				);
				$errormsg = "Invalid service name, please insert a valid value.";
				my $output = $j->encode({
						description => "Modify farm guardian",
						error => "true",
						message => $errormsg
				});
				print $output;
				exit;
				
			} else {
				$service = $json_obj->{ service };
			}
		}
	}

	if ( $type eq "l4xnat" )
	{
		@fgconfig = &getFarmGuardianConf( $farmname, "" );
	}
	elsif ( $type eq "http" || $type eq "https" )
	{
		@fgconfig = &getFarmGuardianConf( $farmname, $service );
	}
	my $timetocheck = @fgconfig[1];
	$timetocheck = $timetocheck + 0;
	my $check_script = @fgconfig[2];
	$check_script =~ s/\n//g;
	$check_script =~ s/\"/\'/g;
	my $usefarmguardian = @fgconfig[3];
	$usefarmguardian =~ s/\n//g;
	my $farmguardianlog = @fgconfig[4];

	if ( exists ( $json_obj->{ fgtimecheck } ) )
	{
		if ( $json_obj->{ fgtimecheck } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the farm guardian in a farm $farmname, invalid fgtimecheck, can't be blank."
			);
		}
		$timetocheck = $json_obj->{ fgtimecheck };
		$timetocheck = $timetocheck + 0;
	}

	if ( exists ( $json_obj->{ fgscript } ) )
	{
		if ( $json_obj->{ fgscript } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the farm guardian in a farm $farmname, invalid fgscript, can't be blank."
			);
		}
		$check_script = uri_unescape( $json_obj->{ fgscript } );
	}

	if ( exists ( $json_obj->{ fgenabled } ) )
	{
		if ( $json_obj->{ fgenabled } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the farm guardian in a farm $farmname, invalid fgenabled, can't be blank."
			);
		}
		$usefarmguardian = $json_obj->{ fgenabled };
	}

	if ( exists ( $json_obj->{ fglog } ) )
	{
		if ( $json_obj{ fglog } )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the farm guardian in a farm $farmname, invalid fglog, can't be blank."
			);
		}
		$farmguardianlog = $json_obj->{ fglog };
	}

	if ( $type eq "l4xnat" )
	{
		&runFarmGuardianStop( $farmname, "" );
		$status =
		  &runFarmGuardianCreate( $farmname, $timetocheck, $check_script,
								  $usefarmguardian, $farmguardianlog, "" );
		if ( $status != -1 )
		{
			if ( $usefarmguardian eq "true" )
			{
				$status = &runFarmGuardianStart( $farmname, "" );
				if ( $status == -1 )
				{
					$error = "true";
					&zenlog(
						"ZAPI error, trying to modify the farm guardian in a farm $farmname, an error ocurred while starting the FarmGuardian service."
					);
				}
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the farm guardian in a farm $farmname, the parameter usefarmguardian must be true."
				);
			}
		}
		else
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the farm guardian in a farm $farmname, it's not possible to create the FarmGuardian configuration file."
			);
		}

	}
	elsif ( $type eq "http" || $type eq "https" )
	{
		&runFarmGuardianStop( $farmname, $service );
		$status =
		  &runFarmGuardianCreate( $farmname, $timetocheck, $check_script,
								  $usefarmguardian, $farmguardianlog, $service );
		if ( $status != -1 )
		{
			if ( $usefarmguardian eq "true" )
			{
				$status = &runFarmGuardianStart( $farmname, $service );
				if ( $status == -1 )
				{
					&zenlog(
						"ZAPI error, trying to modify the farm guardian in a farm $farmname, an error ocurred while starting the FarmGuardian service."
					);
					$error = "true";
				}
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the farm guardian in a farm $farmname, the parameter usefarmguardian must be true."
				);
			}
		}
		else
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the farm guardian in a farm $farmname, it's not possible to create the FarmGuardian configuration file."
			);
		}

	}

	# Print params
	if ( $error ne "true" )
	{
		&zenlog(
			"ZAPI success, some parameters have been changed in farm guardian in farm $farmname."
		);

		# Success
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '200 OK',
					  'Access-Control-Allow-Origin'  => '*'
		);

		foreach $key ( keys %$json_obj )
		{
			push $out_p, { $key => $json_obj->{ $key } };
		}

		my $j = JSON::XS->new->utf8->pretty( 1 );
		$j->canonical( $enabled );
		my $output = $j->encode(
								 {
								   description => "Modify farm $farmname",
								   params      => $out_p
								 }
		);
		print $output;

	}
	else
	{
		&zenlog(
			"ZAPI error, trying to modify the farm guardian in a farm $farmname, it's not possible to modify the farm guardian."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg = "Errors found trying to modify farm $farmname";
		my $output = $j->encode(
								 {
								   description => "Modify farm $farmname",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;

	}

}

1
