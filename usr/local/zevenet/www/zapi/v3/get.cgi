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

# libs
require "/usr/local/zenloadbalancer/www/functions_ext.cgi";
require "/usr/local/zenloadbalancer/www/farms_functions.cgi";
# ....

require "/usr/local/zenloadbalancer/www/zapi/v3/get_http.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/get_gslb.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/get_l4.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/get_datalink.cgi";

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

		$status = "needed restart" if $status eq 'up' && ! &getFarmLock($name);

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

# GET /farms/LSLBFARM
sub farms_lslb # ()
{
	my @out;
	my @files = &getFarmList();

	foreach my $file ( @files )
	{
		my $name   = &getFarmName( $file );
		my $type   = &getFarmType( $name );
		next unless $type =~ /^(?:http|https|l4xnat)$/;
		my $status = &getFarmStatus( $name );
		my $vip    = &getFarmVip( 'vip', $name );
		my $port   = &getFarmVip( 'vipp', $name );

		$status = "needed restart" if $status eq 'up' && ! &getFarmLock($name);

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
				description => "List LSLB farms",
				params      => \@out,
	};

	# Success
	&httpResponse({ code => 200, body => $body });
}

# GET /farms/GSLBFARM
sub farms_gslb # ()
{
	my @out;
	my @files = &getFarmList();

	foreach my $file ( @files )
	{
		my $name   = &getFarmName( $file );
		my $type   = &getFarmType( $name );
		next unless $type eq 'gslb';
		my $status = &getFarmStatus( $name );
		my $vip    = &getFarmVip( 'vip', $name );
		my $port   = &getFarmVip( 'vipp', $name );

		$status = "needed restart" if $status eq 'up' && ! &getFarmLock($name);

		push @out,
		  {
			farmname => $name,
			#~ profile  => $type,
			status   => $status,
			vip      => $vip,
			vport    => $port
		  };
	}

	my $body = {
				description => "List GSLB farms",
				params      => \@out,
	};

	# Success
	&httpResponse({ code => 200, body => $body });
}

# GET /farms/DATALINKFARM
sub farms_dslb # ()
{
	my @out;
	my @files = &getFarmList();

	foreach my $file ( @files )
	{
		my $name   = &getFarmName( $file );
		my $type   = &getFarmType( $name );
		next unless $type eq 'datalink';
		my $status = &getFarmStatus( $name );
		my $vip    = &getFarmVip( 'vip', $name );
		my $iface  = &getFarmVip( 'vipp', $name );

		push @out,
		  {
			farmname => $name,
			#~ profile  => $type,
			status   => $status,
			vip      => $vip,
			interface => $iface
		  };
	}

	my $body = {
				description => "List DSLB farms",
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
			$be->{ 'priority' } = $be->{ 'priority' }? $be->{ 'priority' }+0: undef;
			$be->{ 'weight' } = $be->{ 'weight' }? $be->{ 'weight' }+0: undef;

			push @backends,
			  {
				id       => $be->{ 'id' } + 0,
				ip       => $be->{ 'vip' },
				port     => $be->{ 'vport' },
				priority => $be->{ 'priority' },
				weight   => $be->{ 'weight' },
				status   => $be->{ 'status' },
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
			$l_serv[3] = ($l_serv[3]) ? $l_serv[3]+0: undef;
			$l_serv[4] = ($l_serv[4]) ? $l_serv[4]+0: undef;
			$l_serv[5] = $l_serv[5] + 0;

			if ( $l_serv[1] ne "0.0.0.0" )
			{
				push @backends,
				  {
					id        => $l_serv[0],
					ip        => $l_serv[1],
					interface => $l_serv[2],
					weight    => $l_serv[3],
					priority  => $l_serv[4]
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

	my $backendstatus;
	my $description = "List service backends";

	# Check that the farm exists
	if ( &getFarmFile( $farmname ) eq '-1' )
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

	if ( $type eq 'http' || $type eq 'https' )
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
			my $id          = $subbe[1] + 0;
			my $maintenance = &getFarmBackendMaintenance( $farmname, $id, $service );

			if ( $maintenance != 0 )
			{
				$backendstatus = "up";
			}
			else
			{
				$backendstatus = "maintenance";
			}

			my $ip   = $subbe[3];
			my $port = $subbe[5] + 0;
			my $tout = $subbe[7];
			my $prio = $subbe[9];

			$tout = $tout eq '-' ? undef: $tout+0;
			$prio = $prio eq '-' ? undef: $prio+0;

			push @backends,
			  {
				id      => $id,
				status  => $backendstatus,
				ip      => $ip,
				port    => $port,
				timeout => $tout,
				weight  => $prio,
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

			$subbe[0] =~ s/^primary$/1/;
			$subbe[0] =~ s/^secondary$/2/;

			push @backends,
			  {
				id => $subbe[0]+0,
				ip => $subbe[1],
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
