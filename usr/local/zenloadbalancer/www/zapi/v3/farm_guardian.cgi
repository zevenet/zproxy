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
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -d '{"fgtimecheck":"5","fgscript":"eyy","fgenabled":"true","fglog":"true"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/L4FARM/fg
#
# HTTP/HTTPS
#
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -d '{"fgtimecheck":"5","fgscript":"eyy","fgenabled":"true","fglog":"false","service":"sev1"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmHTTP/fg
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
# @apiSuccess   {String}                fglog           Enabled the use of logs in farm guardian. The options are: true and false. This option is not let it in gslb farms
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
#        -d '{"fgtimecheck":"5","fgscript":"Command of Farm Guardian",
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
#        -d '{"fgtimecheck":"5","fgscript":"Command of Farm Guardian","fgenabled":"true",
#       "fglog":"true","service":"service1"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmHTTP/fg
#
# @apiSampleRequest off
#
#**

#~ use no warnings;
use warnings;
use strict;


sub modify_farmguardian    # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	my $description = "Modify farm guardian";
	my $error       = "false";
	my $needRestart;
	my $errormsg;
	my $type = &getFarmType( $farmname );
	my $service = $json_obj->{'service'};
	delete $json_obj->{'service'};

	my @allowParams = ( "fgtimecheck", "fgscript", "fglog", "fgenabled" );
	
	# validate FARM NAME
	if ( &getFarmFile( $farmname ) == -1 )
	{
		$errormsg = "The farmname $farmname does not exists.";
		my $body = { description => $description, error       => "true", message     => $errormsg };
		&httpResponse( { code => 404, body => $body } );
	}
	# validate FARM TYPE
	elsif ( !&getValidFormat( 'fg_type', $type ) )
	{
		$errormsg = "Farm guardian is not supported for the requested farm profile.";
		my $body = { description => $description, error       => "true", message     => $errormsg };
		&httpResponse( { code => 400, body => $body } );
	}
	# validate no service in l4xnat
	elsif ( $service && $type eq 'l4xnat' )
	{
		$errormsg = "Farm guardian not use services in l4xnat farms.";
		my $body = { description => $description, error       => "true", message     => $errormsg };
		&httpResponse( { code => 400, body => $body } );
	}
	# validate exist service for http(s) farms
	elsif ( ! grep( /^$service$/, &getFarmServices( $farmname ) ) && $type =~ /(?:http|https)/ )
	{
		$errormsg = "Invalid service name, please insert a valid value.";
		my $body = { description => $description, error       => "true", message     => $errormsg };
		&httpResponse( { code => 404, body => $body } );
	}
	# validate exist service for gslb farms
	elsif ( ! grep( /^$service$/, &getGSLBFarmServices( $farmname ) ) && $type =~ /gslb/ )
	{
		$errormsg = "Invalid service name, please insert a valid value.";
		my $body = { description => $description, error       => "true", message     => $errormsg };
		&httpResponse( { code => 404, body => $body } );
	}

	my @fgKeys = ( "fg_time", "fg_log", "fg_enabled", "fg_type" );

	# check Params 
	if ( exists ( $json_obj->{ fgtimecheck } ) && ! &getValidFormat( 'fg_time', $json_obj->{ fgtimecheck } ) )
	{
		$errormsg = "Invalid format, please insert a valid fgtimecheck.";
	}
	elsif ( exists ( $json_obj->{ fgscript } ) && $json_obj->{ fgscript } =~ /^$/  )
	{
		$errormsg = "Invalid fgscript, can't be blank.";
	}
	elsif ( exists ( $json_obj->{ fgenabled } ) && ! &getValidFormat( 'fg_enabled', $json_obj->{ fgenabled } ) )
	{
		$errormsg = "Invalid format, please insert a valid fgenabled.";
	}
	elsif ( exists ( $json_obj->{ fglog } ) && ! &getValidFormat( 'fg_log', $json_obj->{ fglog } ) )
	{
		$errormsg = "Invalid format, please insert a valid fglog.";
	}

	if ( ! $errormsg )
	{
		$errormsg = &getValidOptParams( $json_obj, \@allowParams );
	}
	if ( ! $errormsg )
	{
		if ( $type eq 'gslb' )
		{
			if ( exists ( $json_obj->{ fglog } ) )
			{
				$errormsg = "fglog isn't a correct param for gslb farms.";
			}
			else
			{
				# local variables
				my $fgStatus = &getGSLBFarmFGStatus( $farmname, $service );
				my ( $fgTime, $fgCmd ) = &getGSLBFarmGuardianParams( $farmname, $service );
		
				# Change check script
				if ( exists $json_obj->{ fgscript } ) 
				{
					if ( &setGSLBFarmGuardianParams( $farmname, $service, 'cmd', $json_obj->{ fgscript } ) == -1 )
					{
						$errormsg = "error, trying to modify farm guardian script in farm $farmname, service $service";
					}
				}
				# Change check time
				if ( ! $errormsg && exists $json_obj->{ fgtimecheck } )
				{
					if ( &setGSLBFarmGuardianParams( $farmname, $service, 'interval', $json_obj->{ fgtimecheck } ) == -1 )
					{
						$errormsg = "Error, found trying to enable farm guardian check time in farm $farmname, service $service";
					}
				}
				if ( ! $errormsg && exists $json_obj->{ fgenabled } )
				{
					# enable farmguardian
					if (  ( $json_obj->{ fgenabled } eq 'true' && $fgStatus eq 'false' ) )
					{
						if ( $fgCmd )
						{
							$errormsg = &enableGSLBFarmGuardian( $farmname, $service, 'true' );
							if ( $errormsg )
							{
								$errormsg = "Error, trying to enable farm guardian in farm $farmname, service $service.";
							}
						}
						else
						{
							$errormsg = "Error, it's necesary add a check script to enable farm guardian";
						}
					}
				
					# disable farmguardian
					elsif ( $json_obj->{ fgenabled } eq 'false' && $fgStatus eq 'true' )
					{
						$errormsg = &enableGSLBFarmGuardian( $farmname, $service, 'false' );
						if ( $errormsg )
						{
							$errormsg = "ZAPI error, trying to disable farm guardian in farm $farmname, service $service";
						}
					}
				}
				# if not error, the farm needs restart
				if ( ! $errormsg )
				{
					$json_obj->{ 'status' } = "need restart";
				}
			}
		}
		# https(s) and l4xnat
		else
		{
			my @fgconfig;
	
			if ( $type eq "l4xnat" )
			{
				@fgconfig = &getFarmGuardianConf( $farmname, "" );
			}
			elsif ( $type eq "http" || $type eq "https" )
			{
				@fgconfig = &getFarmGuardianConf( $farmname, $service );
			}
			my $timetocheck  = $fgconfig[1] + 0;
			my $check_script = $fgconfig[2];
			$check_script =~ s/\n//g;
			$check_script =~ s/\"/\'/g;
			my $usefarmguardian = $fgconfig[3];
			$usefarmguardian =~ s/\n//g;
			my $farmguardianlog = $fgconfig[4];

			if ( exists ( $json_obj->{ fgtimecheck } ) )
			{
				$timetocheck = $json_obj->{ fgtimecheck };
				$timetocheck = $timetocheck + 0;
			}
			if ( exists ( $json_obj->{ fgscript } ) )
			{
				$check_script = uri_unescape( $json_obj->{ fgscript } );
			}
			if ( exists ( $json_obj->{ fgenabled } ) )
			{
				$usefarmguardian = $json_obj->{ fgenabled };
			}
			if ( exists ( $json_obj->{ fglog } ) )
			{
				$farmguardianlog = $json_obj->{ fglog };
			}

			if ( $type eq "l4xnat" )
			{
				&runFarmGuardianStop( $farmname, "" );
				my $status =
				&runFarmGuardianCreate( $farmname, $timetocheck, $check_script,
										$usefarmguardian, $farmguardianlog, "" );
				if ( $status != -1 )
				{
					if ( $usefarmguardian eq "true" && &runFarmGuardianStart( $farmname, "" ) )
					{
						$errormsg = "Error, trying to modify the farm guardian in a farm $farmname, an error ocurred while starting the FarmGuardian service.";
					}
				}
				else
				{
					$errormsg = "Error, trying to modify the farm guardian in a farm $farmname, it's not possible to create the FarmGuardian configuration file.";
				}
			}

			elsif ( $type eq "http" || $type eq "https" )
			{
				&runFarmGuardianStop( $farmname, $service );
				my $status =
				&runFarmGuardianCreate( $farmname, $timetocheck, $check_script,
										$usefarmguardian, $farmguardianlog, $service );
				if ( $status != -1 )
				{
					if ( $usefarmguardian eq "true" )
					{
						if ( &runFarmGuardianStart( $farmname, $service ) == -1 )
						{
							$errormsg = "Error, trying to modify the farm guardian in a farm $farmname, an error ocurred while starting the FarmGuardian service.";
						}
					}
				}
				else
				{
					$errormsg = "Error, trying to modify the farm guardian in a farm $farmname, it's not possible to create the FarmGuardian configuration file.";
				}
			}

		}
	}
		
	if ( ! $errormsg )
	{
		$errormsg = "Success, some parameters have been changed in farm guardian in farm $farmname.";
		my $body = { description => $description, params =>$json_obj, message     => $errormsg };
		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		my $body = { description => $description, error       => "true", message     => $errormsg };
		&httpResponse( { code => 400, body => $body } );
	}
}


1;
