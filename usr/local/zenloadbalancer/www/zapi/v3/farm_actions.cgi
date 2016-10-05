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

# POST action
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"action":"stop"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmTCP/actions
#
#
#
#####Documentation of ACTIONS####
#**
#  @api {post} /farms/<farmname>/actions Set an action in a Farm
#  @apiGroup Farm Actions
#  @apiName PostActions
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Set a given action in a Farm
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {String}        action                  Set the action desired. The actions are: stop, start and restart.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Set a new action in FarmTCP",
#   "params" : [
#      {
#         "action" : "stop"
#      }
#   ]
#}
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"action":"stop"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmTCP/actions
#
# @apiSampleRequest off
#
#**

sub actions # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	my $error  = "false";
	my $action = "false";

	# Check input errors
	if ( $json_obj->{ action } =~ /^stop|start|restart$/ )
	{
		$action = $json_obj->{ action };
	}
	else
	{
		&zenlog( "ZAPI error, trying to set an action." );

		my $errormsg = "Invalid action; the possible actions are stop, start and restart";
		my $body = {
					 description => "Farm actions",
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
					 description => "Farm actions",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# Functions
	if ( $action eq "stop" )
	{
		my $status = &runFarmStop( $farmname, "true" );
		if ( $status != 0 )
		{
			$error = "true";
			&zenlog( "ZAPI error, trying to set the action stop in farm $farmname." );
		}
		else
		{
			&zenlog(
					  "ZAPI success, the action stop has been established in farm $farmname." );
		}
	}

	if ( $action eq "start" )
	{
		my $status = &runFarmStart( $farmname, "true" );
		if ( $status != 0 )
		{
			$error = "true";
			&zenlog( "ZAPI error, trying to set the action start in farm $farmname." );
		}
		else
		{
			&zenlog(
					 "ZAPI success, the action start has been established in farm $farmname." );
		}
	}

	if ( $action eq "restart" )
	{
		my $status = &runFarmStop( $farmname, "true" );
		if ( $status != 0 )
		{
			$error = "true";
			&zenlog(
				  "ZAPI error, trying to stop the farm in the action restart in farm $farmname."
			);
		}
		my $status = &runFarmStart( $farmname, "true" );
		if ( $status == 0 )
		{
			my $type = &getFarmType( $farmname );
			if ( $type eq "http" || $type eq "http" )
			{
				&setFarmHttpBackendStatus( $farmname );
			}
			&setFarmNoRestart( $farmname );
			&zenlog(
				   "ZAPI success, the action restart has been established in farm $farmname." );
		}
		else
		{
			$error = "true";
			&zenlog(
				 "ZAPI error, trying to start the farm in the action restart in farm $farmname."
			);
		}
	}

	# Print params
	if ( $error ne "true" )
	{
		# Success
		my $body = {
					 description => "Set a new action in $farmname",
					 params      => { action => $json_obj->{ action } },
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		# Error
		my $errormsg =
		  "Errors found trying to execute the action $json_obj->{action} in farm $farmname";
		my $body = {
					 description => "Set a new action in $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

# POST maintenance
#
# curl --tlsv1  -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: 2bJUdMSHyAhsDYeHJnVHqw7kgN3lPl7gNoWyIej4gjkjpkmPDP9mAU5uUmRg4IHtT" -u zapi:admin -d '{"action":"up", "service":"service1", "id":"1"}' https://46.101.46.14:444/zapi/v3/zapi.cgi/farms/FarmHTTP/maintenance
#
#
#####Documentation of MAINTENANCE####
#**
#  @api {post} /farms/<farmname>/maintenance Set an action in a backend of http|https farm
#  @apiGroup Farm Actions
#  @apiName PostMaintenance
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Set a given action in a backend of a HTTP farm
#  @apiVersion 3.0.0
#
#
# @apiSuccess   {String}        action                  Set the action desired. The actions are: up and maintenance.
# @apiSuccess   {String}        service                 The service where the backend belongs.
# @apiSuccess   {Number}        id                      Backend ID, unique ID.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Set an action in  backend 1 in service service1 in farm FarmHTTP",
#   "params" : [
#      {
#         "action" : "up",
#         "id" : "0",
#         "service" : "service1"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"action":"up", "service":"service1", "id":"0"}'
#       https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmHTTP/maintenance
#
# @apiSampleRequest off
#
#**

sub maintenance # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	my $error  = "false";
	my $action = "false";

	# Check input errors
	if ( $json_obj->{ action } =~ /^up|maintenance$/ )
	{
		$action = $json_obj->{ action };
	}
	else
	{
		my $errormsg = "Invalid action; the possible actions are up and maintenance";
		my $body = {
					 description => "Set a backend status in farm $farmname",
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
					 description => "Set backend Farm status",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	if ( $json_obj->{ service } =~ /^$/ )
	{
		my $errormsg = "Invalid service; please, enter a active service";
		my $body = {
					 description => "Set a backend status in farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
	elsif ( $json_obj->{ service } =~ /^\w+$/ )
	{
		$service = $json_obj->{ service };
	}
	else
	{
		my $errormsg = "Invalid service; please, enter a active service";
		my $body = {
					 description => "Set a backend status in farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( $json_obj->{ id } =~ /^$/ )
	{
		my $errormsg = "Invalid id; please, enter a active id of backend";
		my $body = {
					 description => "Set a backend status in farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
	elsif ( $json_obj->{ id } =~ /^\d+$/ )
	{
		$id = $json_obj->{ id };
	}
	else
	{
		my $errormsg = "Invalid id; id value must be numeric";
		my $body = {
					 description => "Set a backend status in farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( $action eq "maintenance" )
	{
		$status = &setFarmBackendMaintenance( $farmname, $id, $service );
		&zenlog(
			"Changing status to maintenance of backend $id in service $service in farm $farmname"
		);

		if ( $? ne 0 )
		{
			my $errormsg = "Errors found trying to change status backend to maintenance";
			my $body = {
						 description => "Set a backend status in farm $farmname",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}
	elsif ( $action eq "up" )
	{
		&setFarmBackendNoMaintenance( $farmname, $id, $service );
		&zenlog(
			 "Changing status to up of backend $id in service $service in farm $farmname" );

		if ( $? ne 0 )
		{
			my $errormsg = "Errors found trying to change status backend to up";
			my $body = {
									   description => "Set a backend status in farm $farmname",
									   error       => "true",
									   message     => $errormsg
									 };

			&httpResponse({ code => 400, body => $body });
		}
	}

	# Print params
	if ( $error ne "true" )
	{
		# Success
		my $body = {
					description =>
					  "Set an action in  backend $id in service $service in farm $farmname",
					params => {
								action  => $json_obj->{ action },
								service => $json_obj->{ service },
								id      => $json_obj->{ id },
					},
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{

		# Error
		my $errormsg =
		  "Errors found trying to change status of backend $id in service $service in farm $farmname";
		my $body = {
					description =>
					  "Set an action in  backend $id in service $service in farm $farmname",
					error   => "true",
					message => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

1;
