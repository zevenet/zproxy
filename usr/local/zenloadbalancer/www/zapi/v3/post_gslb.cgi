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

# POST /farms/<farmname>/zones Create a new zone in a gslb Farm
sub new_farm_zone # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	my $zone = $json_obj->{ id };

	if ( $farmname =~ /^$/ )
	{
		&zenlog(
			 "ZAPI error, trying to create a new zone in farm $farmname, invalid farm name."
		);

		# Error
		my $errormsg = "Invalid farm name, please insert a valid value.";
		my $body = {
					 description => "New zone",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
	
	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 ) {
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => "New zone",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	if ( $json_obj->{ id } =~ /^$/ )
	{
		&zenlog(
			 "ZAPI error, trying to create a new zone in farm $farmname, invalid zone name."
		);

		# Error
		my $errormsg = "Invalid zone name, please insert a valid value.";
		my $body = {
					 description => "New zone " . $json_obj->{ id },
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( $json_obj->{ id } !~ /.*\..*/ )
	{
		&zenlog(
			"Wrong zone name. The name has to be like zonename.com, zonename.net, etc. The zone $zone can't be created"
		);

		# Error
		my $errormsg =
		  "Invalid zone name, please insert a valid value like zonename.com, zonename.net, etc. The zone $zone can't be created.";
		my $body = {
								   description => "New zone " . $json_obj->{ id },
								   error       => "true",
								   message     => $errormsg
								 };

		&httpResponse({ code => 400, body => $body });
	}

	my $result = &setGSLBFarmNewZone( $farmname, $json_obj->{ id } );
	if ( $result eq "0" )
	{
		&zenlog(
			"ZAPI success, a new zone has been created in farm $farmname with id $json_obj->{id}."
		);

		# Success
		if ( &getFarmStatus( $farmname ) eq 'up' )
		{
			&runFarmReload( $farmname );
			&runZClusterRemoteManager( 'farm', 'restart', $farmname );
		}

		my $body = {
					 description => "New zone " . $json_obj->{ id },
					 params      => { id => $json_obj->{ id } },
		};

		&httpResponse({ code => 201, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to create a new zone in farm $farmname with id $json_obj->{id}, it's not possible to create the zone."
		);

		# Error
		my $errormsg = "It's not possible to create the zone " . $json_obj->{ id };
		my $body = {
								   description => "New zone " . $json_obj->{ id },
								   error       => "true",
								   message     => $errormsg
								 };

		&httpResponse({ code => 400, body => $body });
	}
}

# POST /farms/<farmname>/zoneresources Create a new resource of a zone in a gslb Farm
sub new_farm_zone_resource # ( $json_obj, $farmname, $zone )
{
	my $json_obj = shift;
	my $farmname = shift;
	my $zone     = shift;

	my $description = "New zone resource";
	my $default_ttl = '';

	# validate FARM NAME
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

	# validate FARM TYPE
	unless ( &getFarmType( $farmname ) eq 'gslb' )
	{
		my $errormsg = "Only GSLB profile is supported for this request.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# validate ZONE
	unless ( grep { $_ eq $zone } &getFarmZones( $farmname ) )
	{
		my $errormsg = "Could not find the requested zone.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# validate RESOURCE NAME exist
	if ( grep { $_->{ rname } eq $json_obj->{ rname } } @{ &getGSLBResources ( $farmname, $zone ) } )
	{
		&zenlog(
			"ZAPI error, trying to create a new resource in zone $zone in farm $farmname, the parameter zone resource already exists."
		);

		# Error
		my $errormsg =
		  "The parameter zone resource name (rname) already exists, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# validate RESOURCE NAME
	unless ( $json_obj->{ rname } && &getValidFormat( 'resource_name', $json_obj->{ rname } ) )
	{
		&zenlog(
			"ZAPI error, trying to create a new resource in zone $zone in farm $farmname, the parameter zone resource name (rname) doesn't exist."
		);

		# Error
		my $errormsg =
		  "The parameter zone resource name (rname) doesn't exist, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# validate RESOURCE TTL
	$json_obj->{ ttl } = $default_ttl if ! exists $json_obj->{ ttl };

	unless ( $json_obj->{ ttl } eq '' || ( &getValidFormat( 'resource_ttl', $json_obj->{ ttl } ) && $json_obj->{ ttl } != 0 ) ) # (1second-1year)
	{
		&zenlog(
			"ZAPI error, trying to create a new resource in zone $zone in farm $farmname, the parameter time to live value (ttl) doesn't exist."
		);

		# Error
		my $errormsg =
		  "The parameter time to live value (ttl) doesn't exist, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# validate RESOURCE TYPE
	unless ( &getValidFormat( 'resource_type', $json_obj->{ type } ) )
	{
		&zenlog(
			"ZAPI error, trying to create a new resource in zone $zone in farm $farmname, the parameter DNS record type (type) doesn't exist."
		);

		# Error
		my $errormsg =
		  "The parameter DNS record type (type) doesn't exist, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# validate RESOURCE DATA
	unless ( ! grep ( /$json_obj->{ rdata }/, &getGSLBFarmServices ( $farmname ) && $json_obj->{ type } eq 'DYNA' ) && 
						&getValidFormat( "resource_data_$json_obj->{ type }", $json_obj->{ rdata } ) )
	{
		my $errormsg = "If you choose $json_obj->{ type } type, ";
		
		$errormsg .= "RDATA must be a valid IPv4 address," 							if ( $json_obj->{ type } eq "A" );
		$errormsg .= "RDATA must be a valid IPv6 address,"							if ( $json_obj->{ type } eq "AAAA" );
		$errormsg .= "RDATA format is not valid,"									if ( $json_obj->{ type } eq "NS" );
		$errormsg .= "RDATA must be a valid format ( foo.bar.com ),"				if ( $json_obj->{ type } eq "CNAME" );
		$errormsg .= "RDATA must be a valid service,"								if ( $json_obj->{ type } eq 'DYNA' );
		$errormsg .= "RDATA must be a valid format ( mail.example.com ),"			if ( $json_obj->{ type } eq 'MX' );
		$errormsg .= "RDATA must be a valid format ( 10 60 5060 host.example.com )," if ( $json_obj->{ type } eq 'SRV' );
		$errormsg .= "RDATA must be a valid format ( foo.bar.com ),"				if ( $json_obj->{ type } eq 'PTR' );
		# TXT and NAPTR input let all characters
		
		$errormsg .= " $json_obj->{ rname } not added to zone $zone";
		&zenlog( $errormsg );

		# Error
		$errormsg =
		  "The parameter zone resource server (rdata) doesn't correct format, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	my $status = &setFarmZoneResource(
									   "",
									   $json_obj->{ rname },
									   $json_obj->{ ttl },
									   $json_obj->{ type },
									   $json_obj->{ rdata },
									   $farmname,
									   $zone,
	);

	if ( $status != -1 )
	{
		&zenlog(
			"ZAPI success, a new resource has been created in zone $zone in farm $farmname."
		);

		# Success
		if ( &getFarmStatus( $farmname ) eq 'up' )
		{
			&runFarmReload( $farmname );
			&runZClusterRemoteManager( 'farm', 'restart', $farmname );
		}

		$json_obj->{ ttl } = undef if ! $json_obj->{ ttl };

		my $message = "Resource added";
		my $body = {
					 description => $description,
					 params      => {
								 rname => $json_obj->{ rname },
								 zone  => $zone,
								 ttl   => $json_obj->{ ttl },
								 type  => $json_obj->{ type },
								 rdata => $json_obj->{ rdata },
					 },
					 message => $message,
		};
		my $checkConf = &getGSLBCheckConf  ( $farmname );
		 if ( $checkConf =~ /^(.+?)\s/ )
		 {
			 $checkConf = "The resource $1 gslb farm break the configuration. Please check the configuration";
			 $body->{ params }->{ warning }  =  $checkConf;
		 }

		&httpResponse({ code => 201, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to create a new resource in zone $zone in farm $farmname, it's not possible to create a new resource."
		);

		# Error
		my $errormsg =
		  "It's not possible to create a new resource in the zone $zone in farm $farmname.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

1;
