###############################################################################
#
#    Zevenet Software License
#    This file is part of the Zevenet Load Balancer software package.
#
#    Copyright (C) 2014-today ZEVENET SL, Sevilla (Spain)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

use strict;

use Zevenet::Farm::Core;

# POST /farms/<farmname>/actions Set an action in a Farm
sub farm_actions    # ( $json_obj, $farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;

	my $description = "Farm actions";
	my $action;

	# calidate FARM NAME
	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse( { code => 404, body => $body } );
	}

	# Check input errors
	if ( $json_obj->{ action } =~ /^(?:stop|start|restart)$/ )
	{
		$action = $json_obj->{ action };
	}
	else
	{
		&zenlog( "Error trying to set an action.", "error", "ZAPI" );

		my $errormsg =
		  "Invalid action; the possible actions are stop, start and restart";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# Functions
	require Zevenet::Farm::Action;
	if ( $action eq "stop" )
	{
		my $status = &runFarmStop( $farmname, "true" );

		if ( $status != 0 )
		{
			my $errormsg = "Error trying to set the action stop in farm $farmname.";
			&zenlog( $errormsg, "error", "ZAPI" );

			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse( { code => 400, body => $body } );
		}
		else
		{
			&zenlog( "Success, the action stop has been established in farm $farmname.",
					 "info", "ZAPI" );

			include 'Zevenet::Cluster';
			&runZClusterRemoteManager( 'farm', 'stop', $farmname );
		}
	}

	if ( $action eq "start" )
	{
		my $status = &runFarmStart( $farmname, "true" );

		if ( $status != 0 )
		{
			my $errormsg = "Error trying to set the action start in farm $farmname.";
			&zenlog( $errormsg, "error", "ZAPI" );

			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse( { code => 400, body => $body } );
		}
		else
		{
			&zenlog( "Success, the action start has been established in farm $farmname.",
					 "info", "ZAPI" );

			include 'Zevenet::Cluster';
			&runZClusterRemoteManager( 'farm', 'start', $farmname );
		}

	}

	if ( $action eq "restart" )
	{
		my $status = &runFarmStop( $farmname, "true" );

		if ( $status != 0 )
		{
			my $errormsg =
			  "Error trying to stop the farm in the action restart in farm $farmname.";
			&zenlog( $errormsg, "error", "ZAPI" );

			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse( { code => 400, body => $body } );
		}

		$status = &runFarmStart( $farmname, "true" );

		if ( $status == 0 )
		{
			my $type = &getFarmType( $farmname );

			if ( $type eq "http" || $type eq "https" )
			{
				&setHTTPFarmBackendStatus( $farmname );
			}

			&setFarmNoRestart( $farmname );
			&zenlog( "Success, the action restart has been established in farm $farmname.",
					 "info", "ZAPI" );

			include 'Zevenet::Cluster';
			&runZClusterRemoteManager( 'farm', 'restart', $farmname );
		}
		else
		{
			my $errormsg =
			  "Error trying to start the farm in the action restart in farm $farmname.";
			&zenlog( $errormsg, "error", "ZAPI" );

			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse( { code => 400, body => $body } );
		}
	}

	# Print params
	# Success
	my $body = {
				 description => "Set a new action in $farmname",
				 params      => { action => $json_obj->{ action } },
	};

	&httpResponse( { code => 200, body => $body } );
}

# POST /farms/<farmname>/maintenance Set an action in a backend of http|https farm
sub service_backend_maintenance # ( $json_obj, $farmname, $service, $backend_id )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj   = shift;
	my $farmname   = shift;
	my $service    = shift;
	my $backend_id = shift;

	my $description = "Set service backend status";

	# validate FARM NAME
	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
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

		&httpResponse( { code => 404, body => $body } );
	}

	# validate SERVICE
	{
		require Zevenet::Farm::HTTP::Service;

		my @services = &getHTTPFarmServices( $farmname );
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

			&httpResponse( { code => 404, body => $body } );
		}
	}

	# validate BACKEND
	my $be;
	{
		require Zevenet::Farm::Config;

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

			&httpResponse( { code => 404, body => $body } );
		}
	}

	# Not allow modificate the maintenance status if the farm needs to restart
	require Zevenet::Farm::Action;
	if ( &getFarmRestartStatus( $farmname ) )
	{
		# Error
		my $errormsg = "The farm needs to be restarted before to apply this action.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse( { code => 400, body => $body } );
	}

	require Zevenet::Farm::Backend::Maintenance;

	# validate STATUS
	if ( $json_obj->{ action } eq "maintenance" )
	{
		my $status =
		  &setFarmBackendMaintenance( $farmname, $backend_id, "drain", $service );

		&zenlog(
			"Changing status to maintenance of backend $backend_id in service $service in farm $farmname",
			"info", "ZAPI"
		);

		if ( $? ne 0 )
		{
			my $errormsg = "Errors found trying to change status backend to maintenance";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}
	}
	elsif ( $json_obj->{ action } eq "up" )
	{
		my $status = &setFarmBackendNoMaintenance( $farmname, $backend_id, $service );

		&zenlog(
			"Changing status to up of backend $backend_id in service $service in farm $farmname",
			"info", "ZAPI"
		);

		if ( $? ne 0 )
		{
			my $errormsg = "Errors found trying to change status backend to up";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
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

		&httpResponse( { code => 400, body => $body } );
	}

	# Success
	my $body = {
				 description => $description,
				 params      => { action => $json_obj->{ action } },
	};

	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		include 'Zevenet::Cluster';
		&runZClusterRemoteManager( 'farm', 'restart', $farmname );
	}

	&httpResponse( { code => 200, body => $body } );
}

# PUT backend in maintenance
sub backend_maintenance    # ( $json_obj, $farmname, $backend_id )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj   = shift;
	my $farmname   = shift;
	my $backend_id = shift;

	my $description = "Set backend status";

	# validate FARM NAME
	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
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

		&httpResponse( { code => 404, body => $body } );
	}

	# validate BACKEND
	require Zevenet::Farm::L4xNAT::Backend;

	my $exists = defined ( @{ &getL4FarmServers( $farmname ) }[$backend_id] );

	if ( !$exists )
	{
		# Error
		my $errormsg = "Could not find a backend with such id.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse( { code => 404, body => $body } );
	}

	# validate STATUS
	if ( $json_obj->{ action } eq "maintenance" )
	{
		my $status = &setFarmBackendMaintenance( $farmname, $backend_id, "drain" );

		&zenlog(
				 "Changing status to maintenance of backend $backend_id in farm $farmname",
				 "info", "ZAPI" );

		if ( $status != 0 )
		{
			my $errormsg = "Errors found trying to change status backend to maintenance";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}
	}
	elsif ( $json_obj->{ action } eq "up" )
	{
		my $status = &setFarmBackendNoMaintenance( $farmname, $backend_id );

		&zenlog( "Changing status to up of backend $backend_id in farm $farmname",
				 "info", "ZAPI" );

		if ( $status != 0 )
		{
			my $errormsg = "Errors found trying to change status backend to up";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
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

		&httpResponse( { code => 400, body => $body } );
	}

	# Success
	my $body = {
				 description => $description,
				 params      => { action => $json_obj->{ action } },
	};

	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		include 'Zevenet::Cluster';
		&runZClusterRemoteManager( 'farm', 'restart', $farmname );
	}

	&httpResponse( { code => 200, body => $body } );
}

1;
