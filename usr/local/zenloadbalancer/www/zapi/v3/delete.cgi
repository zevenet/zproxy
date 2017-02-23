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

use strict;

# DELETE /farms/FARMNAME
sub delete_farm # ( $farmname )
{
	my $farmname = shift;

	if ( $farmname =~ /^$/ )
	{
		&zenlog(
				  "ZAPI error, trying to delete the farm $farmname, invalid farm name." );

		# Error
		my $errormsg = "Invalid farm name, please insert a valid value.";
		my $body = {
					 description => "Delete farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	my $newffile = &getFarmFile( $farmname );
	if ( $newffile == -1 )
	{
		&zenlog(
			 "ZAPI error, trying to delete the farm $farmname, the farm name doesn't exist."
		);

		# Error
		my $errormsg = "The farm $farmname doesn't exist, try another name.";
		my $body = {
					 description => "Delete farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		&runFarmStop( $farmname, "true" );
		&runZClusterRemoteManager( 'farm', 'stop', $farmname );
	}

	my $stat = &runFarmDelete( $farmname );

	if ( $stat == 0 )
	{
		&zenlog( "ZAPI success, the farm $farmname has been deleted." );

		# Success
		&runZClusterRemoteManager( 'farm', 'delete', $farmname );

		my $message = "The Farm $farmname has been deleted.";
		my $body = {
					 description => "Delete farm $farmname",
					 success     => "true",
					 message     => $message
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to delete the farm $farmname, the farm hasn't been deleted."
		);

		# Error
		my $errormsg = "The Farm $farmname hasn't been deleted";
		my $body = {
					 description => "Delete farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}


# DELETE /farms/<farmname>/services/<servicename> Delete a service of a Farm
sub delete_service # ( $farmname, $service )
{
	my ( $farmname, $service ) = @_;

	if ( $farmname =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to delete the service $service in farm $farmname, invalid farm name."
		);

		# Error
		my $errormsg = "Invalid farm name, please insert a valid value.";
		my $body = {
					 description => "Delete service",
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
					 description => "Delete service",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	if ( $service =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to delete the service $service in farm $farmname, invalid service name."
		);

		# Error
		my $errormsg = "Invalid service name, please insert a valid value.";
		
		my $body = {
					   description => "Delete service",
					   error       => "true",
					   message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	my $type = &getFarmType( $farmname );
	
	# Check that the provided service is configured in the farm
	my @services;
	if ($type eq "gslb")
	{
		@services = &getGSLBFarmServices($farmname);
	}
	else
	{
		@services = &getFarmServices($farmname);
	}

	my $found = 0;
	foreach my $farmservice (@services)
	{
		#print "service: $farmservice";
		if ($service eq $farmservice)
		{
			$found = 1;
			last;
		}
	}

	if ($found == 0)
	{
		# Error
		my $errormsg = "Invalid service name, please insert a valid value.";
		my $body = {
				description => "Delete service",
				error => "true",
				message => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
	
	my $return;
	if ( $type eq "http" || $type eq "https" )
	{
		$return = &deleteFarmService( $farmname, $service );
	}
	elsif ( $type eq "gslb" )
	{
		$return = &setGSLBFarmDeleteService( $farmname, $service );
	}

	if ( $return == -2 )
	{
		&zenlog(
				 "ZAPI error, the service $service in farm $farmname hasn't been deleted. The service is used by a zone." );

		# Error
		my $message = "The service $service in farm $farmname hasn't been deleted. The service is used by a zone.";
		my $body = {
					 description => "Delete service $service in farm $farmname.",
					 error       => "true",
					 message     => $message
		};

		&httpResponse({ code => 400, body => $body });
	}
	elsif ( $return == 0 )
	{
		&zenlog(
				 "ZAPI success, the service $service in farm $farmname has been deleted." );

		# Success
		my $message = "The service $service in farm $farmname has been deleted.";
		my $body = {
					 description => "Delete service $service in farm $farmname.",
					 success     => "true",
					 message     => $message
		};

		if ( &getFarmStatus( $farmname ) eq 'up' )
		{
			$body->{ status } = "needed restart";
			&setFarmRestart( $farmname );
		}

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to delete the service $service in farm $farmname, the service hasn't been deleted."
		);

		# Error
		my $errormsg = "Service $service in farm $farmname hasn't been deleted.";
		my $body = {
					 description => "Delete service $service in farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

# DELETE /farms/<farmname>/backends/<backendid> Delete a backend of a Farm
sub delete_backend # ( $farmname, $id_server )
{
	my ( $farmname, $id_server ) = @_;

	my $description = "Delete backend";

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
	my $type = &getFarmType( $farmname );
	unless ( $type eq 'l4xnat' || $type eq 'datalink' )
	{
		# Error
		my $errormsg = "The $type farm profile has backends only in services.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	my @backends = &getFarmServers( $farmname );
	my $backend_line = $backends[$id_server];

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

	my $status = &runFarmServerDelete( $id_server, $farmname );

	if ( $status != -1 )
	{
		&zenlog(
			   "ZAPI success, the backend $id_server in farm $farmname has been deleted." );

		# Success
		&runZClusterRemoteManager( 'farm', 'restart', $farmname );

		#~ my $message = "The backend with ID $id_server of the $farmname farm has been deleted.";
		my $message = "Backend removed";

		my $body = {
					 description => $description,
					 success     => "true",
					 message     => $message
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to delete the backend $id_server in farm $farmname, it's not possible to delete the backend."
		);

		# Error
		my $errormsg =
		  "It's not possible to delete the backend with ID $id_server of the $farmname farm.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}


#  DELETE /farms/<farmname>/services/<servicename>/backends/<backendid> Delete a backend of a Service
sub delete_service_backend # ( $farmname, $service, $id_server )
{
	my ( $farmname, $service, $id_server ) = @_;

	my $description = "Delete service backend";

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
	my $type = &getFarmType( $farmname );
	unless ( $type eq 'http' || $type eq 'https' || $type eq 'gslb' )
	{
		# Error
		my $errormsg = "The $type farm profile has backends only in services.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# validate SERVICE
	{
		my @services;

		if ($type eq "gslb")
		{
			@services = &getGSLBFarmServices($farmname);
		}
		else
		{
			@services = &getFarmServices($farmname);
		}

		my $found_service = grep { $service eq $_ } @services;

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

		# validate ALGORITHM
		if ( &getFarmVS( $farmname, $service, "algorithm" ) eq 'prio' )
		{
			&zenlog(
				 "ZAPI error, this service algorithm does not support removing backends." );

			# Error
			my $errormsg = "This service algorithm does not support removing backends.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		# check if the backend id is available
		my @backends = split ( "\n", &getFarmVS( $farmname, $service, "backends" ) );
		my $be_found;

		if ( $type eq "gslb" )
		{
			$be_found = grep( /\s*$id_server\s=>\s/, @backends);
		}
		else
		{
			$be_found = grep { (split ( " ", $_ ))[1] == $id_server } @backends;
		}

		unless ( $be_found )
		{
			my $errormsg = "Could not find the requested backend.";
			my $body = {
						description => $description,
						error       => "true",
						message     => $errormsg
			};
	
			&httpResponse({ code => 404, body => $body });
		}
	}

	my $status;

	if ( $type eq "http" || $type eq "https" )
	{
		$status = &runFarmServerDelete( $id_server, $farmname, $service );
	}
	if ( $type eq "gslb" )
	{
		$status = &remFarmServiceBackend( $id_server, $farmname, $service );
	}

	if ( $status != -1 )
	{
		&zenlog(
			"ZAPI success, the backend $id_server in service $service in farm $farmname has been deleted."
		);

		# Success
		&setFarmRestart( $farmname );
		#~ my $message = "The backend with ID $id_server in the service $service of the farm $farmname has been deleted.";
		my $message = "Backend removed";
		my $body = {
					 description => $description,
					 success     => "true",
					 message     => $message,
		};

		if ( &getFarmStatus( $farmname ) eq 'up' )
		{
			$body->{ status } = "needed restart";
			&setFarmRestart( $farmname );
		}

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to delete the backend $id_server in service $service in farm $farmname, it's not possible to delete the backend."
		);

		# Error
		my $errormsg =
		  "Could not find the backend with ID $id_server of the $farmname farm.";
		my $body = {
			   description => $description,
			   error   => "true",
			   message => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}
}

1;
