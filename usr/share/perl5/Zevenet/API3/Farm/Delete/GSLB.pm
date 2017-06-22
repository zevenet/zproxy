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

# DELETE /farms/<farmname>/zones/<zonename> Delete a zone of a  gslb Farm
sub delete_zone # ( $farmname, $zone )
{
	my ( $farmname, $zone ) = @_;

	if ( $farmname =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to delete the zone $zone in farm $farmname, invalid farm name."
		);

		# Error
		my $errormsg = "Invalid farm name, please insert a valid value.";
		my $body = {
					 description => "Delete zone",
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
					 description => "Delete zone",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	if ( $zone =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to delete the zone $zone in farm $farmname, invalid zone name."
		);

		# Error
		my $errormsg = "Invalid zone name, please insert a valid value.";
		my $body = {
					   description => "Delete zone",
					   error       => "true",
					   message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	&setGSLBFarmDeleteZone( $farmname, $zone );

	if ( $? eq 0 )
	{
		&zenlog( "ZAPI success, the zone $zone in farm $farmname has been deleted." );

		# Success
		if ( &getFarmStatus( $farmname ) eq 'up' )
		{
			&runFarmReload( $farmname );
			&runZClusterRemoteManager( 'farm', 'restart', $farmname );
		}

		my $message = "The zone $zone in farm $farmname has been deleted.";
		my $body = {
								   description => "Delete zone $zone in farm $farmname.",
								   success     => "true",
								   message     => $message
								 };

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to delete the zone $zone in farm $farmname, the zone hasn't been deleted."
		);

		# Error
		my $errormsg = "Zone $zone in farm $farmname hasn't been deleted.";
		my $body = {
					 description => "Delete zone $zone in farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

#  @api {delete} /farms/<farmname>/zones/<zonename>/resources/<resourceid> Delete a resource of a Zone
sub delete_zone_resource # ( $farmname, $zone, $resource )
{
	my ( $farmname, $zone, $resource ) = @_;

	my $description = "Delete zone resource";

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
	if ( &getFarmType( $farmname ) ne 'gslb' )
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
	if ( ! scalar grep { $_ eq $zone } &getFarmZones( $farmname ) )
	{
		&zenlog(
			"ZAPI error, trying to delete the resource $resource in zone $zone in farm $farmname, invalid zone name."
		);

		# Error
		my $errormsg = "Invalid zone name, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $backendsvs = &getFarmVS( $farmname, $zone, "resources" );
	my @be = split ( "\n", $backendsvs );
	my ( $resource_line ) = grep { /;index_$resource$/ } @be;

	# validate RESOURCE
	if ( ! $resource_line )
	{
		&zenlog(
			"ZAPI error, trying to delete the resource $resource in zone $zone in farm $farmname, invalid resource id."
		);

		# Error
		my $errormsg = "Invalid resource id, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $status = &remFarmZoneResource( $resource, $farmname, $zone );

	if ( $status != -1 )
	{
		&zenlog(
			"ZAPI success, the resource $resource in zone $zone in farm $farmname has been deleted."
		);

		# Success
		if ( &getFarmStatus( $farmname ) eq 'up' )
		{
			&runFarmReload( $farmname );
			&runZClusterRemoteManager( 'farm', 'restart', $farmname );
		}

		#~ my $message = "The resource with id $resource in the zone $zone of the farm $farmnamehas been deleted.";
		my $message = "Resource removed";
		my $body = {
					 description => $description,
					 success     => "true",
					 message     => $message,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to delete the resource $resource in zone $zone in farm $farmname, it's not possible to delete the resource."
		);

		# Error
		my $errormsg =
		  "It's not possible to delete the resource with id $resource in the zone $zone of the farm $farmname.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
}

1;
