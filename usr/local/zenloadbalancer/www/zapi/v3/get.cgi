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

#GET /farms/<name>/backends
sub backends
{
	my $farmname = shift;

	my $description = "List backends";

	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exist.";
		my $body = {
				description => $description,
				error => "true",
				message => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $type = &getFarmType( $farmname );

	if ( $type eq 'l4xnat' )
	{
		my $l4_farm = &getL4FarmStruct( $farmname );
		my @backends;

		for my $be ( @{ $l4_farm->{ 'servers' } } )
		{
			$be->{ 'vport' } = $be->{ 'vport' } eq '' ? undef : $be->{ 'vport' } + 0;

			push @backends,
			  {
				id       => $be->{ 'id' } + 0,
				ip       => $be->{ 'vip' },
				port     => $be->{ 'vport' },
				priority => $be->{ 'priority' } + 0,
				weight   => $be->{ 'weight' } + 0,
			  };
		}

		my $body = {
					description => $description,
					params      => \@backends,
		};

		# Success
		&httpResponse({ code => 200, body => $body });
	}
	elsif ( $type eq 'datalink' )
	{
		my @backends;
		my @run = &getFarmServers( $farmname );

		foreach my $l_servers ( @run )
		{
			my @l_serv = split ( ";", $l_servers );

			$l_serv[0] = $l_serv[0] + 0;
			$l_serv[3] = $l_serv[3] + 0;
			$l_serv[4] = $l_serv[4] + 0;
			$l_serv[5] = $l_serv[5] + 0;

			if ( $l_serv[1] ne "0.0.0.0" )
			{
				push @backends,
				  {
					id        => $l_serv[0],
					ip        => $l_serv[1],
					interface => @l_serv[2],
					weight    => @l_serv[3],
					priority  => @l_serv[4]
				  };
			}
		}

		my $body = {
					 description => $description,
					 params      => \@backends,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		# Error
		my $errormsg = "The farm $farmname with profile $type does not support this request.";
		my $body = {
				description => $description,
				error => "true",
				message => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

#GET /farms/<name>/services/<service>/backends
sub service_backends
{
	my ( $farmname, $service ) = @_;

	my $description = "List service backends";

	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exist.";
		my $body = {
				description => $description,
				error => "true",
				message => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $type = &getFarmType( $farmname );

	if ( $type eq 'http' || $type eq 'http' )
	{
		my @services_list = split ' ', &getFarmVS( $farmname );

		unless ( grep { $service eq $_ } @services_list )
		{
			# Error
			my $errormsg = "The service $service does not exist.";
			my $body = {
					description => $description,
					error => "true",
					message => $errormsg
			};

			&httpResponse({ code => 404, body => $body });
		}

		my @be         = split ( "\n", &getFarmVS( $farmname, $service, "backends" ) );
		my @backends;

		foreach my $subl ( @be )
		{
			my @subbe       = split ( "\ ", $subl );
			my $id          = @subbe[1] + 0;
			my $maintenance = &getFarmBackendMaintenance( $farmname, $id, $service );

			if ( $maintenance != 0 )
			{
				$backendstatus = "up";
			}
			else
			{
				$backendstatus = "maintenance";
			}

			my $ip   = @subbe[3];
			my $port = @subbe[5] + 0;
			my $tout = @subbe[7];
			my $prio = @subbe[9];

			$tout = $tout eq '-' ? undef: $tout+0;
			$prio = $prio eq '-' ? undef: $prio+0;

			push @backends,
			  {
				id            => $id,
				backendstatus => $backendstatus,
				ip            => $ip,
				port          => $port,
				timeout       => $tout,
				weight        => $prio,
			  };
		}

		my $body = {
					description => $description,
					params      => \@backends,
		};

		# Success
		&httpResponse({ code => 200, body => $body });
	}
	elsif ( $type eq 'gslb' )
	{
		my @services_list = &getGSLBFarmServices( $farmname );

		unless ( grep { $service eq $_ } @services_list )
		{
			# Error
			my $errormsg = "The service $service does not exist.";
			my $body = {
					description => $description,
					error => "true",
					message => $errormsg
			};

			&httpResponse({ code => 404, body => $body });
		}

		my @be = split ( "\n", &getFarmVS( $farmname, $service, "backends" ) );
		my @backends;

		foreach my $subline ( @be )
		{
			$subline =~ s/^\s+//;
			if ( $subline =~ /^$/ )
			{
				next;
			}

			my @subbe = split ( " => ", $subline );

			push @backends,
			  {
				id => @subbe[0],
				ip => @subbe[1],
			  };
		}

		my $body = {
					 description => $description,
					 params      => \@backends,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		# Error
		my $errormsg = "The farm $farmname with profile $type does not support this request.";
		my $body = {
				description => $description,
				error => "true",
				message => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

1;
