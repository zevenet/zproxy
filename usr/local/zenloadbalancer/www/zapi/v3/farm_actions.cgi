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
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -d '{"action":"stop"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmTCP/actions
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
#        -d '{"action":"stop"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmTCP/actions
#
# @apiSampleRequest off
#
#**

#~ use no warnings;
use warnings;
use strict;


sub farm_actions # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	my $description = "Farm actions";
	my $action;

	# calidate FARM NAME
	if ( &getFarmFile( $farmname ) == -1 )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 404, body => $body });
	}

	# Check input errors
	if ( $json_obj->{ action } =~ /^(?:stop|start|restart)$/ )
	{
		$action = $json_obj->{ action };
	}
	else
	{
		&zenlog( "ZAPI error, trying to set an action." );

		my $errormsg = "Invalid action; the possible actions are stop, start and restart";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
	
	# Functions
	if ( $action eq "stop" )
	{
		my $status = &runFarmStop( $farmname, "true" );

		if ( $status != 0 )
		{
			my $errormsg = "Error trying to set the action stop in farm $farmname.";
			&zenlog( $errormsg );

			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse({ code => 400, body => $body });
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
			my $errormsg = "Error trying to set the action start in farm $farmname.";
			&zenlog( $errormsg );

			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse({ code => 400, body => $body });
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
			my $errormsg = "Error trying to stop the farm in the action restart in farm $farmname.";
			&zenlog( $errormsg );

			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse({ code => 400, body => $body });
		}

		$status = &runFarmStart( $farmname, "true" );

		if ( $status == 0 )
		{
			my $type = &getFarmType( $farmname );

			if ( $type eq "http" || $type eq "https" )
			{
				&setFarmHttpBackendStatus( $farmname );
			}

			&setFarmNoRestart( $farmname );
			&zenlog(
				   "ZAPI success, the action restart has been established in farm $farmname." );
		}
		else
		{
			my $errormsg = "ZAPI error, trying to start the farm in the action restart in farm $farmname.";
			&zenlog( $errormsg );

			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse({ code => 400, body => $body });
		}
	}

	# Print params
	# Success
	my $body = {
				 description => "Set a new action in $farmname",
				 params      => { action => $json_obj->{ action } },
	};

	&httpResponse({ code => 200, body => $body });
}

# POST maintenance
#
# curl --tlsv1  -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: 2bJUdMSHyAhsDYeHJnVHqw7kgN3lPl7gNoWyIej4gjkjpkmPDP9mAU5uUmRg4IHtT" -d '{"action":"up", "service":"service1", "id":"1"}' https://46.101.46.14:444/zapi/v3/zapi.cgi/farms/FarmHTTP/maintenance
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
#        -d '{"action":"up", "service":"service1", "id":"0"}'
#       https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmHTTP/maintenance
#
# @apiSampleRequest off
#
#**

sub service_backend_maintenance # ( $json_obj, $farmname, $service, $backend_id )
{
	my $json_obj   = shift;
	my $farmname   = shift;
	my $service    = shift;
	my $backend_id = shift;

	my $description = "Set service backend status";

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
	if ( &getFarmType( $farmname ) !~ /^(?:http|https)$/ )
	{
		# Error
		my $errormsg = "Only HTTP farm profile supports this feature.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# validate SERVICE
	{
		my @services = &getFarmServices($farmname);
		my $found_service;

		foreach my $service_name ( @services )
		{
			if ( $service eq $service_name )
			{
				$found_service = 1;
				last;
			}
		}

		if ( !$found_service )
		{
			# Error
			my $errormsg = "Could not find the requested service.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 404, body => $body });
		}
	}

	# validate BACKEND
	my $be;
	{
		my $backendsvs = &getFarmVS( $farmname, $service, "backends" );
		my @be_list = split ( "\n", $backendsvs );

		foreach my $be_line ( @be_list )
		{
			my @current_be = split ( " ", $be_line );

			if ( $current_be[1] == $backend_id )
			{
				$be = {
						id       => $current_be[1],
						ip       => $current_be[3],
						port     => $current_be[5],
						timeout  => $current_be[7],
						priority => $current_be[9],
				};

				last;
			}
		}

		if ( !$be )
		{
			# Error
			my $errormsg = "Could not find a service backend with such id.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse({ code => 404, body => $body });
		}
	}

	# validate STATUS
	if ( $json_obj->{ action } eq "maintenance" )
	{
		my $status = &setFarmBackendMaintenance( $farmname, $backend_id, $service );

		&zenlog(
			"Changing status to maintenance of backend $backend_id in service $service in farm $farmname"
		);

		if ( $? ne 0 )
		{
			my $errormsg = "Errors found trying to change status backend to maintenance";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}
	elsif ( $json_obj->{ action } eq "up" )
	{
		my $status = &setFarmBackendNoMaintenance( $farmname, $backend_id, $service );

		&zenlog(
			 "Changing status to up of backend $backend_id in service $service in farm $farmname" );

		if ( $? ne 0 )
		{
			my $errormsg = "Errors found trying to change status backend to up";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}
	else
	{
		my $errormsg = "Invalid action; the possible actions are up and maintenance";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# Success
	my $body = {
				 description => $description,
				 params      => { action => $json_obj->{ action } },
	};

	&httpResponse({ code => 200, body => $body });
}

sub backend_maintenance # ( $json_obj, $farmname, $backend_id )
{
	my $json_obj   = shift;
	my $farmname   = shift;
	my $backend_id = shift;

	my $description = "Set backend status";

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
	unless ( &getFarmType( $farmname ) eq 'l4xnat' )
	{
		# Error
		my $errormsg = "Only L4xNAT farm profile supports this feature.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	#~ my $l4_farm = &getL4FarmStruct( $farmname );

	# validate BACKEND
	my @backends = &getFarmServers( $farmname );
	my $backend_line = $backends[$backend_id];

	if ( !$backend_line )
	{
		# Error
		my $errormsg = "Could not find a backend with such id.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 404, body => $body });
	}

	# validate STATUS
	if ( $json_obj->{ action } eq "maintenance" )
	{
		my $status = &setFarmBackendMaintenance( $farmname, $backend_id );

		&zenlog(
			"Changing status to maintenance of backend $backend_id in farm $farmname"
		);

		if ( $? ne 0 )
		{
			my $errormsg = "Errors found trying to change status backend to maintenance";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}
	elsif ( $json_obj->{ action } eq "up" )
	{
		my $status = &setFarmBackendNoMaintenance( $farmname, $backend_id );

		&zenlog(
			 "Changing status to up of backend $backend_id in farm $farmname" );

		if ( $? ne 0 )
		{
			my $errormsg = "Errors found trying to change status backend to up";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}
	else
	{
		my $errormsg = "Invalid action; the possible actions are up and maintenance";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# Success
	my $body = {
				 description => $description,
				 params      => { action => $json_obj->{ action } },
	};

	&httpResponse({ code => 200, body => $body });
}

1;
