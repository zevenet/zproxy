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

# PUT /farms/FarmHTTP
#
#

sub modify_farm # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;
	
	# Check that the farm exists
	if ( &getFarmFile( $farmname ) eq '-1' )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => "Modify farm",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $type = &getFarmType( $farmname );

	if ( $type eq "http" || $type eq "https" )
	{
		require "/usr/local/zenloadbalancer/www/zapi/v3/put_http.cgi";
		&modify_http_farm( $json_obj, $farmname );
	}

	if ( $type eq "l4xnat" )
	{
		require "/usr/local/zenloadbalancer/www/zapi/v3/put_l4.cgi";
		&modify_l4xnat_farm( $json_obj, $farmname );
	}

	if ( $type eq "datalink" )
	{
		require "/usr/local/zenloadbalancer/www/zapi/v3/put_datalink.cgi";
		&modify_datalink_farm( $json_obj, $farmname );
	}

	if ( $type eq "gslb" )
	{
		require "/usr/local/zenloadbalancer/www/zapi/v3/put_gslb.cgi";
		&modify_gslb_farm( $json_obj, $farmname );
	}
}

sub modify_backends #( $json_obj, $farmname, $id_server )
{
	my ( $json_obj, $farmname, $id_server ) = @_;

	my $description = "Modify backend";

	# Check that the farm exists
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

	my $error;
	my $type = &getFarmType( $farmname );

	if ( $type eq "l4xnat" )
	{
		# Params
		my $l4_farm = &getL4FarmStruct( $farmname );
		my $backend;

		for my $be ( @{ $l4_farm->{'servers'} } )
		{
			if ( $be->{'id'} eq $id_server )
			{
				$backend = $be;
			}
		}

		if ( ! $backend )
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

		if ( exists ( $json_obj->{ ip } ) )
		{
			if ( $json_obj->{ ip } && &getValidFormat('IPv4_addr', $json_obj->{ ip } ) )
			{
				$backend->{ vip } = $json_obj->{ ip };
			}
			else
			{
				$error = "true";
				&zenlog(
						 "Error trying to modify the backend in the farm $farmname, invalid IP." );
			}
		}

		if ( !$error && exists ( $json_obj->{ port } ) )
		{
			if ( &isValidPortNumber( $json_obj->{ port } ) eq 'true' || $json_obj->{ port } == undef )
			{
				$backend->{ vport } = $json_obj->{ port };
			}
			else
			{
				$error = "true";
				&zenlog(
					  "Error trying to modify the backend in the farm $farmname, invalid port number."
				);
			}
		}

		if ( !$error && exists ( $json_obj->{ weight } ) )
		{
			if ( $json_obj->{ weight } =~ /^\d*[1-9]$/ || $json_obj->{ weight } == undef ) # 1 or higher
			{
				$backend->{ weight } = $json_obj->{ weight };
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid weight."
				);
			}
		}

		if ( !$error && exists ( $json_obj->{ priority } ) )
		{
			if ( $json_obj->{ priority } =~ /^\d$/ || $json_obj->{ priority } == undef ) # (0-9)
			{
				$backend->{ priority } = $json_obj->{ priority };
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the backends in the farm $farmname, invalid priority."
				);
			}
		}

		if ( !$error && exists ( $json_obj->{ max_conns } ) )
		{
			if ( $json_obj->{ max_conns } =~ /^\d+$/ ) # (0 or higher)
			{
				$backend->{ max_conns } = $json_obj->{ max_conns };
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the connection limit in the farm $farmname, invalid value."
				);
			}
		}

		if ( !$error )
		{
			my $status = &setL4FarmServer(
										   $backend->{ id },
										   $backend->{ vip },
										   $backend->{ vport },
										   $backend->{ weight },
										   $backend->{ priority },
										   $farmname,
										   $backend->{ max_conns },
			);

			if ( $status == -1 )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the backends in a farm $farmname, it's not possible to modify the backend with ip $json_obj->{ip}."
				);
			}
		}
	}
	elsif ( $type eq "datalink" )
	{
		my @run = &getFarmServers( $farmname );
		my $serv_values = $run[$id_server];
		my $be;

		if ( ! $serv_values )
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

		( undef, $be->{ip}, $be->{interface}, $be->{weight}, $be->{priority}, $be->{status} ) = split ( ";", $serv_values );

		# Functions
		if ( exists ( $json_obj->{ ip } ) )
		{
			if ( $json_obj->{ ip } && &getValidFormat('IPv4_addr', $json_obj->{ ip } ) )
			{
				$be->{ ip } = $json_obj->{ ip };
			}
			else
			{
				$error = "true";
				&zenlog(
					 "ZAPI error, trying to modify the backends in the farm $farmname, invalid IP." );
			}
		}

		if ( !$error && exists ( $json_obj->{ interface } ) )
		{
			my $valid_interface;

			for my $iface ( @{ &getActiveInterfaceList() } )
			{
				next if $iface->{ vini }; # discard virtual interfaces
				next if !$iface->{ addr }; # discard interfaces without address

				if ( $iface->{ name } eq $json_obj->{ interface } )
				{
					$valid_interface = 'true';
				}
			}

			if ( $valid_interface )
			{
				$be->{ interface } = $json_obj->{ interface };
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the backends in the farm $farmname, invalid interface."
				);
			}
		}

		if ( !$error && exists ( $json_obj->{ weight } ) )
		{
			if ( $json_obj->{ weight } =~ &getValidFormat('natural_num') || $json_obj->{ weight } == undef ) # 1 or higher
			{
				$be->{ weight } = $json_obj->{ weight };
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the backends in the farm $farmname, invalid weight."
				);
			}
		}

		if ( !$error && exists ( $json_obj->{ priority } ) )
		{
			if ( $json_obj->{ priority } =~ /^[1-9]$/ || $json_obj->{ priority } == undef ) # (1-9)
			{
				$be->{ priority } = $json_obj->{ priority };
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the backends in the farm $farmname, invalid priority."
				);
			}
		}

		if ( !$error )
		{
			my $status =
			  &setFarmServer( $id_server,
							  $be->{ ip },
							  $be->{ interface },
							  "",
							  $be->{ weight },
							  $be->{ priority },
							  "", $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the backends in the farm $farmname, it's not possible to modify the backend with IP $json_obj->{ip} and interface $json_obj->{interface}."
				);
			}
		}
	}
	else
	{
		# Error
		my $errormsg = "The $type farm profile has backends only in services.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# Print params
	if ( !$error )
	{
		&zenlog(
			"ZAPI success, some parameters have been changed in the backend $id_server in farm $farmname."
		);

		# Success
		my $message = "Backend modified";
		my $body = {
					 description => $description,
					 params      => $json_obj,
					 message => $message,
		};

		if ( &getFarmStatus( $farmname ) eq 'up' )
		{
			&runZClusterRemoteManager( 'farm', 'restart', $farmname );
		}

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"Error trying to modify the backend in the farm $farmname, it's not possible to modify the backend."
		);

		# Error
		my $errormsg = "Errors found trying to modify farm $farmname";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub modify_service_backends #( $json_obj, $farmname, $service, $id_server )
{
	my ( $json_obj, $farmname, $service, $id_server ) = @_;

	my $description = "Modify service backend";

	# Check that the farm exists
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

	my $error;
	my $type = &getFarmType( $farmname );

	if ( $type eq "http" || $type eq "https" )
	{
		# validate SERVICE
		{
			my @services = &getFarmServices($farmname);
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
		}

		# validate BACKEND
		my $be;
		{
			my $backendsvs = &getFarmVS( $farmname, $service, "backends" );
			my @be_list = split ( "\n", $backendsvs );

			foreach my $be_line ( @be_list )
			{
				my @current_be = split ( " ", $be_line );

				if ( $current_be[1] == $id_server )
				{
					$current_be[7] = undef if $current_be[7] eq '-';
					$current_be[9] = undef if $current_be[9] eq '-';

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

		# Functions
		if ( exists ( $json_obj->{ ip } ) )
		{
			if ( $json_obj->{ ip } && &getValidFormat('IPv4_addr', $json_obj->{ ip } ) )
			{
				$be->{ ip } = $json_obj->{ ip };
			}
			else
			{
				$error = "true";
				&zenlog(
					 "ZAPI error, trying to modify the backends in a farm $farmname, invalid IP." );
			}
		}

		if ( !$error && exists ( $json_obj->{ port } ) )
		{
			if ( &isValidPortNumber( $json_obj->{ port } ) eq 'true' )
			{
				$be->{ port } = $json_obj->{ port };
			}
			else
			{
				$error = "true";
				&zenlog(
					  "ZAPI error, trying to modify the backends in a farm $farmname, invalid port."
				);
			}
		}

		if ( !$error && exists ( $json_obj->{ weight } ) )
		{
			if ( $json_obj->{ weight } =~ /^[1-9]$/ )
			{
				$be->{ priority } = $json_obj->{ weight };
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid weight."
				);
			}
		}

		if ( !$error && exists ( $json_obj->{ timeout } ) )
		{
			if ( $json_obj->{ timeout } eq '' || ( $json_obj->{ timeout } =~ /^\d+$/ && $json_obj->{ timeout } != 0 ) )
			{
				$be->{ timeout } = $json_obj->{ timeout };
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid timeout."
				);
			}
		}

		if ( !$error )
		{
			my $status = &setFarmServer(
										 $id_server,       $be->{ ip },
										 $be->{ port },    "",
										 "",               $be->{ priority },
										 $be->{ timeout }, $farmname,
										 $service
			);

			if ( $status == -1 )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the backends in a farm $farmname, it's not possible to modify the backend with IP $json_obj->{ip} in service $service."
				);
			}
			else
			{
				&setFarmRestart( $farmname );
			}
		}
	}
	elsif ( $type eq "gslb" )
	{
		# validate SERVICE
		{
			my @services = &getGSLBFarmServices($farmname);
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
		}

		# validate BACKEND
		my $be;
		my $backend_id = $id_server;
		{
			my $backendsvs = &getFarmVS( $farmname, $service, "backends" );
			my @be_list = split ( "\n", $backendsvs );

			# convert backend_id for prio algorithm
			my $algorithm = &getFarmVS( $farmname, $service, "algorithm" );
			if ( $algorithm eq 'prio' )
			{
				$backend_id = 'primary' if $id_server == 1;
				$backend_id = 'secondary' if $id_server == 2;
			}

			foreach my $be_line ( @be_list )
			{
				$be_line =~ s/^\s+//;
				next if !$be_line;

				my @current_be = split ( " => ", $be_line );

				if ( $current_be[0] == $backend_id )
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

		my $lb = &getFarmVS( $farmname, $service, "algorithm" );

		# Functions
		if ( exists ( $json_obj->{ ip } ) )
		{
			if ( $json_obj->{ ip } && &getValidFormat('IPv4_addr', $json_obj->{ ip } ) )
			{
				$be->{ ip } = $json_obj->{ ip };
			}
			else
			{
				$error = "true";
				&zenlog(
					 "ZAPI error, trying to modify the backends in a farm $farmname, invalid IP." );
			}
		}

		if ( !$error )
		{
			my $status =
			  &setGSLBFarmNewBackend( $farmname, $service, $lb, $backend_id, $json_obj->{ ip } );

			if ( $status == -1 )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the backends in a farm $farmname, it's not possible to modify the backend with IP $json_obj->{ip} in service $service."
				);
			}
			else
			{
				&setFarmRestart( $farmname );
			}
		}
	}
	else
	{
		# Error
		my $errormsg = "The $type farm profile does not support services.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# Print params
	if ( !$error )
	{
		&zenlog(
			"ZAPI success, some parameters have been changed in the backend $id_server in service $service in farm $farmname."
		);

		# Success
		# Get farm status. If farm is down the restart is not required.
		my $body = {
					 description => $description,
					 params      => $json_obj,
					 message     => "Backend modified",
		};

		if ( &getFarmStatus( $farmname ) eq "up" )
		{
			$body->{ status } = 'needed restart';
			$body->{ info } =
			  "There're changes that need to be applied, stop and start farm to apply them!";
		}

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to modify the backends in a farm $farmname, it's not possible to modify the backend."
		);

		# Error
		my $errormsg = "Errors found trying to modify farm $farmname";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}


sub modify_services # ( $json_obj, $farmname, $service )
{
	my ( $json_obj, $farmname, $service ) = @_;

	my $output_params;
	my $description = "Modify service";
	my $errormsg;

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

		&httpResponse( { code => 404, body => $body } );
	}

	# validate FARM TYPE
	my $type = &getFarmType( $farmname );
	unless ( $type eq 'gslb' || $type eq 'http' || $type eq 'https' )
	{
		# Error
		my $errormsg = "The $type farm profile does not support services.";
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
	}

	my $error = "false";

	if ( $type eq "http" || $type eq "https" )
	{
		# Functions
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
			my $redirect = uri_unescape( $json_obj->{ redirect } );

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

		#~ &zenlog("farmname:$farmname service:$service cookiedomain:$json_obj->{ cookiedomain } cookiename:$json_obj->{ cookiename } cookiepath:$json_obj->{ cookiepath } cookieinsert: $json_obj->{ cookieinsert } cookiettl:$json_obj->{ cookiettl }");

		if ( $json_obj->{ cookieinsert } eq "true" )
		{
			if ( exists ( $json_obj->{ cookiedomain } ) )
			{
				#~ &zenlog("farmname:$farmname service:$service cookiedomain:$json_obj->{ cookiedomain }");
				&setFarmVS( $farmname, $service, "cookieins-domain", $json_obj->{ cookiedomain } );
			}

			if ( exists ( $json_obj->{ cookiename } ) )
			{
				#~ &zenlog("farmname:$farmname service:$service cookiename:$json_obj->{ cookiename }");
				&setFarmVS( $farmname, $service, "cookieins-name", $json_obj->{ cookiename } );
			}

			if ( exists ( $json_obj->{ cookiepath } ) )
			{
				#~ &zenlog("farmname:$farmname service:$service cookiepath:$json_obj->{ cookiepath }");
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

		$output_params = &getHttpFarmService( $farmname, $service );
	}

	if ( $type eq "gslb" )
	{
		# Functions
		if ( $json_obj->{ deftcpport } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the service $service in a farm $farmname, invalid deftcpport, can't be blank."
			);
		}
		if ( $error eq "false" )
		{
			# change to number format
			$json_obj->{ deftcpport } += 0;
			
			&setFarmVS( $farmname, $service, "dpc", $json_obj->{ deftcpport } );
			if ( $? eq 0 )
			{
				&runFarmReload( $farmname );
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the service $service in a farm $farmname, it's not possible to change the deftcpport parameter."
				);
			}
		}

		# FIXME: Read gslb configuration instead of returning input
		$output_params = $json_obj;
	}

	# Print params
	if ( $error ne "true" )
	{
		&zenlog(
			"ZAPI success, some parameters have been changed in service $service in farm $farmname."
		);

		# Success
		my $body = {
			description => "Modify service $service in farm $farmname",
			params      => $output_params,
		};

		if ( &getFarmStatus( $farmname ) eq 'up' )
		{
			&setFarmRestart( $farmname );
			$body->{ status } = 'needed restart';
			$body->{ info } = "There're changes that need to be applied, stop and start farm to apply them!";
		}
		
		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to modify the zones in a farm $farmname, it's not possible to modify the service $service."
		);

		# Error
		$errormsg = "Errors found trying to modify farm $farmname";

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub move_services
{
	my ( $json_obj, $farmname, $service ) = @_;

	my $errormsg;
	my @services = &getFarmServices( $farmname );
	my $services_num = scalar @services;
	my $description = "Move service";
	my $moveservice;

	# validate FARM NAME
	if ( &getFarmFile( $farmname ) == -1 ) {
		# Error
		$errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}
	elsif ( ! grep ( /^$service$/, @services ) )
	{
		$errormsg = "$service not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse({ code => 404, body => $body });
	}

	# Move services
	else
	{
		$errormsg = &getValidOptParams( $json_obj, ["position"] );

		if ( !$errormsg )
		{
			if ( !&getValidFormat( 'service_position', $json_obj->{ 'position' } ) )
			{
				$errormsg = "Error in service position format.";
			}
			else
			{
				my $srv_position = &getFarmVSI( $farmname, $service );
				if ( $srv_position == $json_obj->{ 'position' } )
				{
					$errormsg = "The service already is in required position.";
				}
				elsif ( $services_num <= $json_obj->{ 'position' } )
				{
					$errormsg = "The required position is bigger than number of services.";
				}

				# select action
				elsif ( $srv_position > $json_obj->{ 'position' } )
				{
					$moveservice = "up";
				}
				else
				{
					$moveservice = "down";
				}

				if ( !$errormsg )
				{
					# stopping farm
					my $farm_status = &getFarmStatus( $farmname );
					if ( $farm_status eq 'up' )
					{
						if ( &runFarmStop( $farmname, "true" ) != 0 )
						{
							$errormsg = "Error stopping the farm.";
						}
						else
						{
							&zenlog( "Farm stopped successful." );
						}
					}
					if ( !$errormsg )
					{
						# move service until required position
						while ( $srv_position != $json_obj->{ 'position' } )
						{
							#change configuration file
							&moveServiceFarmStatus( $farmname, $moveservice, $service );
							&moveService( $farmname, $moveservice, $service );

							$srv_position = &getFarmVSI( $farmname, $service );
						}

						# start farm if his status was up
						if ( $farm_status eq 'up' )
						{
							if ( &runFarmStart( $farmname, "true" ) == 0 )
							{
								&setFarmHttpBackendStatus( $farmname );
								&zenlog( "$service was moved successful." );
							}
							else
							{
								$errormsg = "The $farmname farm hasn't been restarted";
							}
						}

						if ( !$errormsg )
						{
							$errormsg = "$service was moved successful.";

							if ( &getFarmStatus( $farmname ) eq 'up' )
							{
								&runFarmReload( $farmname );
								&runZClusterRemoteManager( 'farm', 'restart', $farmname );
							}

							my $body =
							  { description => $description, params => $json_obj, message => $errormsg, };
							&httpResponse( { code => 200, body => $body } );
						}
					}
				}
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

1;
