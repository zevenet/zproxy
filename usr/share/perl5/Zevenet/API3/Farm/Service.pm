#!/usr/bin/perl
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

# POST

sub new_farm_service    # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	my $description = "New service";

	# Check if the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	my $type = &getFarmType( $farmname );

	# validate farm profile
	if ( $type eq "gslb" && eval { require Zevenet::API3::Farm::GSLB; } )
	{
		&new_gslb_farm_service( $json_obj, $farmname );
	}
	elsif ( $type !~ /(?:https?)/ )
	{
		my $errormsg = "The farm profile $type does not support services.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# HTTP profile
	require Zevenet::Farm::Base;
	require Zevenet::Farm::HTTP::Service;

	# validate new service name
	if ( $json_obj->{ id } eq '' )
	{
		&zenlog(
			"ZAPI error, trying to create a new service in farm $farmname, invalid service name."
		);

		my $errormsg = "Invalid service, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	my $result = &setFarmHTTPNewService( $farmname, $json_obj->{ id } );

	# check if a service with such name already exists
	if ( $result == 1 )
	{
		&zenlog(
			"ZAPI error, trying to create a new service in farm $farmname, the service $json_obj->{id} already exists."
		);

		my $errormsg = "Service named " . $json_obj->{ id } . " already exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# check if the service name was empty
	if ( $result == 2 )
	{
		&zenlog(
			"ZAPI error, trying to create a new service in farm $farmname, new service $json_obj->{id} can't be empty."
		);

		my $errormsg = "New service can't be empty.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# check if the service name has invalid characters
	if ( $result == 3 )
	{
		&zenlog(
			"ZAPI error, trying to create a new service in farm $farmname, the service name $json_obj->{id} is not valid, only allowed numbers,letters and hyphens."
		);

		my $errormsg =
		  "Service name is not valid, only allowed numbers, letters and hyphens.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# no error found, return successful response
	&zenlog(
		"ZAPI success, a new service has been created in farm $farmname with id $json_obj->{id}."
	);

	my $body = {
				 description => $description,
				 params      => { id => $json_obj->{ id } },
	};

	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		require Zevenet::Farm::Action;

		&setFarmRestart( $farmname );
		$body->{ status } = 'needed restart';
	}

	&httpResponse( { code => 201, body => $body } );
}

# GET

#GET /farms/<name>/services/<service>
sub farm_services
{
	my ( $farmname, $servicename ) = @_;

	require Zevenet::Farm::Config;
	require Zevenet::Farm::HTTP::Service;

	my $description = "Get services of a farm";
	my $service;

	# Check if the farm exists
	if ( &getFarmFile( $farmname ) eq '-1' )
	{
		my $errormsg = "The farmname $farmname does not exist.";
		my $body = {
				description => $description,
				error => "true",
				message => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $type = &getFarmType( $farmname );

	# check the farm type is supported
	if ( $type !~ /http/i )
	{
		my $errormsg = "This functionality only is available for HTTP farms.";
		my $body = {
				description => $description,
				error => "true",
				message => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	my @services = &getHTTPFarmServices( $farmname );

	# check if the service is available
	if ( ! grep ( /^$servicename$/, @services ) )
	{
		my $errormsg = "The required service does not exist.";
		my $body = {
				description => $description,
				error => "true",
				message => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# no error found, return successful response
	my $service = &getServiceStruct ( $farmname, $servicename );

	foreach my $be ( @{ $service->{backends} } )
	{
		$be->{status} = "up" if $be->{status} eq "undefined";
	}

	my $body = {
				 description => $description,
				 services    	=> $service,
	};

	&httpResponse({ code => 200, body => $body });
}

# PUT

sub modify_services # ( $json_obj, $farmname, $service )
{
	my ( $json_obj, $farmname, $service ) = @_;

	require Zevenet::Farm::Base;
	require Zevenet::Farm::Config;
	require Zevenet::Farm::Service;

	my $description = "Modify service";
	my $output_params;
	my $errormsg;

	# validate FARM NAME
	if ( &getFarmFile( $farmname ) == -1 )
	{
		my $errormsg = "The farmname $farmname does not exist.";

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	# validate FARM TYPE
	my $type = &getFarmType( $farmname );

	unless ( $type eq 'gslb' || $type eq 'http' || $type eq 'https' )
	{
		my $errormsg = "The $type farm profile does not support services.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# validate SERVICE
	my @services = &getFarmServices($farmname);
	my $found_service = grep { $service eq $_ } @services;

	if ( !$found_service )
	{
		my $errormsg = "Could not find the requested service.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $error = "false";

	# check if the farm profile gslb is supported
	if ( $type eq "gslb" && eval { require Zevenet::API3::Farm::GSLB; } )
	{
		$output_params = modify_gslb_service( $json_obj, $farmname, $service );
	}
	else
	{
		&zenlog(
			"ZAPI error, farm profile $type not supported."
		);

		$errormsg = "Farm profile not supported";

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( exists ( $json_obj->{ vhost } ) )
	{
		&setFarmVS( $farmname, $service, "vs", $json_obj->{ vhost } );
	}

	if ( exists ( $json_obj->{ urlp } ) )
	{
		&setFarmVS( $farmname, $service, "urlp", $json_obj->{ urlp } );
	}

	my $redirecttype = &getFarmVS( $farmname, $service, "redirecttype" );

	if ( exists ( $json_obj->{ redirect } ) )
	{
		my $redirect = $json_obj->{ redirect };

		if ( $redirect =~ /^http\:\/\//i || $redirect =~ /^https:\/\//i || $redirect eq '' )
		{
			&setFarmVS( $farmname, $service, "redirect", $redirect );
		}
		else
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the service $service in a farm $farmname, invalid redirect."
			);
		}
	}

	my $redirect = &getFarmVS( $farmname, $service, "redirect" );

	if ( exists ( $json_obj->{ redirecttype } ) )
	{
		my $redirecttype = $json_obj->{ redirecttype };

		if ( $redirecttype eq "default" )
		{
			&setFarmVS( $farmname, $service, "redirect", $redirect );
		}
		elsif ( $redirecttype eq "append" )
		{
			&setFarmVS( $farmname, $service, "redirectappend", $redirect );
		}
		elsif ( exists $json_obj->{ redirect } && $json_obj->{ redirect } )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the service $service in a farm $farmname, invalid redirecttype."
			);
		}
	}

	if ( exists ( $json_obj->{ persistence } ) )
	{
		if ( $json_obj->{ persistence } =~ /^|IP|BASIC|URL|PARM|COOKIE|HEADER$/ )
		{
			my $session = $json_obj->{ persistence };
			$session = 'nothing' if $session eq "";

			my $status = &setFarmVS( $farmname, $service, "session", $session );

			if ( $status != 0 )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the service $service in a farm $farmname, it's not possible to change the persistence parameter."
				);
			}
		}
	}

	if ( exists ( $json_obj->{ ttl } ) )
	{
		if ( $json_obj->{ ttl } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the service $service in a farm $farmname, invalid ttl, can't be blank."
			);
		}
		elsif ( $json_obj->{ ttl } =~ /^\d+/ )
		{
			my $status = &setFarmVS( $farmname, $service, "ttl", "$json_obj->{ttl}" );
			if ( $status != 0 )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the service $service in a farm $farmname, it's not possible to change the ttl parameter."
				);
			}
		}
		else
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the service $service in a farm $farmname, invalid ttl, must be numeric."
			);
		}
	}

	if ( exists ( $json_obj->{ sessionid } ) )
	{
		&setFarmVS( $farmname, $service, "sessionid", $json_obj->{ sessionid } );
	}

	if ( exists ( $json_obj->{ leastresp } ) )
	{
		if ( $json_obj->{ leastresp } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the service $service in a farm $farmname, invalid leastresp, can't be blank."
			);
		}
		elsif ( $json_obj->{ leastresp } =~ /^true|false$/ )
		{
			if ( ( $json_obj->{ leastresp } eq "true" ) )
			{
				&setFarmVS( $farmname, $service, "dynscale", $json_obj->{ leastresp } );
			}
			elsif ( ( $json_obj->{ leastresp } eq "false" ) )
			{
				&setFarmVS( $farmname, $service, "dynscale", "" );
			}
		}
		else
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the service $service in a farm $farmname, invalid leastresp."
			);
		}
	}

	if ( exists ( $json_obj->{ cookieinsert } ) )
	{
		if ( $json_obj->{ cookieinsert } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the service $service in a farm $farmname, invalid cookieinsert, can't be blank."
			);
		}
		elsif ( $json_obj->{ cookieinsert } =~ /^true|false$/ )
		{
			if ( ( $json_obj->{ cookieinsert } eq "true" ) )
			{
				&setFarmVS( $farmname, $service, "cookieins", $json_obj->{ cookieinsert } );
			}
			elsif ( ( $json_obj->{ cookieinsert } eq "false" ) )
			{
				&setFarmVS( $farmname, $service, "cookieins", "" );
			}
		}
		else
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the service $service in a farm $farmname, invalid cookieinsert."
			);
		}
	}

	my $cookieins_status = &getHTTPFarmVS ($farmname,$service, 'cookieins');
	if ( $json_obj->{ cookieinsert } eq "true"  || $cookieins_status eq 'true' )
	{
		if ( exists ( $json_obj->{ cookiedomain } ) )
		{
			&setFarmVS( $farmname, $service, "cookieins-domain", $json_obj->{ cookiedomain } );
		}

		if ( exists ( $json_obj->{ cookiename } ) )
		{
			&setFarmVS( $farmname, $service, "cookieins-name", $json_obj->{ cookiename } );
		}

		if ( exists ( $json_obj->{ cookiepath } ) )
		{
			&setFarmVS( $farmname, $service, "cookieins-path", $json_obj->{ cookiepath } );
		}

		if ( exists ( $json_obj->{ cookiettl } ) )
		{
			if ( $json_obj->{ cookiettl } =~ /^$/ )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid cookiettl, can't be blank."
				);
			}
			else
			{
				&setFarmVS( $farmname, $service, "cookieins-ttlc", $json_obj->{ cookiettl } );
			}
		}
	}

	if ( exists ( $json_obj->{ httpsb } ) )
	{
		if ( $json_obj->{ httpsb } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the service $service in a farm $farmname, invalid httpsb, can't be blank."
			);
		}
		elsif ( $json_obj->{ httpsb } =~ /^true|false$/ )
		{
			if ( ( $json_obj->{ httpsb } eq "true" ) )
			{
				&setFarmVS( $farmname, $service, "httpsbackend", $json_obj->{ httpsb } );
			}
			elsif ( ( $json_obj->{ httpsb } eq "false" ) )
			{
				&setFarmVS( $farmname, $service, "httpsbackend", "" );
			}
		}
		else
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the service $service in a farm $farmname, invalid httpsb."
			);
		}
	}

	# check errors modifying service settings
	if ( $error eq "true" )
	{
		&zenlog(
			"ZAPI error, trying to modify the zones in a farm $farmname, it's not possible to modify the service $service."
		);

		$errormsg = "Errors found trying to modify farm $farmname";

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# no error found, return succesful response
	$output_params = &getHTTPServiceStruct( $farmname, $service );

	&zenlog(
		"ZAPI success, some parameters have been changed in service $service in farm $farmname."
	);

	my $body = {
		description => "Modify service $service in farm $farmname",
		params      => $output_params,
	};

	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		require Zevenet::Farm::Action;

		&setFarmRestart( $farmname );
		$body->{ status } = 'needed restart';
		$body->{ info } = "There're changes that need to be applied, stop and start farm to apply them!";
	}

	&httpResponse({ code => 200, body => $body });
}

# DELETE

# DELETE /farms/<farmname>/services/<servicename> Delete a service of a Farm
sub delete_service # ( $farmname, $service )
{
	my ( $farmname, $service ) = @_;

	my $description = "Delete service";

	# Check if the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# check the farm type is supported
	my $type = &getFarmType( $farmname );
	
	if ( $type eq "gslb" && eval { require Zevenet::API3::Farm::GSLB; } )
	{
		delete_gslb_service( $farmname, $service );
	}
	elsif ( $type !~ /(?:https?)/ )
	{
		my $errormsg = "The farm profile $type does not support services.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	require Zevenet::Farm::Base;
	require Zevenet::Farm::HTTP::Service;

	# Check that the provided service is configured in the farm
	my @services = &getHTTPFarmServices($farmname);
	my $found = 0;

	foreach my $farmservice (@services)
	{
		if ($service eq $farmservice)
		{
			$found = 1;
			last;
		}
	}

	if ( $found == 0 )
	{
		my $errormsg = "Invalid service name, please insert a valid value.";
		my $body = {
				description => $description,
				error => "true",
				message => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	my $return = &deleteFarmService( $farmname, $service );

	# check if the service is in use
	if ( $return == -2 )
	{
		&zenlog(
				 "ZAPI error, the service $service in farm $farmname hasn't been deleted. The service is used by a zone." );

		my $message = "The service $service in farm $farmname hasn't been deleted. The service is used by a zone.";
		my $body = {
					 description => "Delete service $service in farm $farmname.",
					 error       => "true",
					 message     => $message
		};

		&httpResponse({ code => 400, body => $body });
	}

	# check if the service could not be deleted
	if ( $return != 0 )
	{
		&zenlog(
			"ZAPI error, trying to delete the service $service in farm $farmname, the service hasn't been deleted."
		);

		my $errormsg = "Service $service in farm $farmname hasn't been deleted.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# no errors found, returning successful response
	&zenlog(
			 "ZAPI success, the service $service in farm $farmname has been deleted." );

	my $message = "The service $service in farm $farmname has been deleted.";
	my $body = {
				 description => $description,
				 success     => "true",
				 message     => $message
	};

	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		require Zevenet::Farm::Action;

		$body->{ status } = "needed restart";
		&setFarmRestart( $farmname );
	}

	&httpResponse({ code => 200, body => $body });
}

1;
