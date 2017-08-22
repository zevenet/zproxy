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

#  PUT /farms/<farmname>/fg Modify the parameters of the farm guardian in a Farm
#  PUT /farms/<farmname>/fg Modify the parameters of the farm guardian in a Service
sub modify_farmguardian    # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	require Zevenet::Farm::Core;
	require Zevenet::Farm::Base;

	my $description = "Modify farm guardian";
	my $type = &getFarmType( $farmname );
	my $service = $json_obj->{'service'};
	delete $json_obj->{'service'};

	#~ my @fgKeys = ( "fg_time", "fg_log", "fg_enabled", "fg_type" );

	# validate FARM NAME
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

	# validate FARM TYPE
	unless ( $type eq 'l4xnat' || $type =~ /^https?$/ || $type eq 'gslb' )
	{
		my $errormsg = "Farm guardian is not supported for the requested farm profile.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 400, body => $body } );
	}

	# check if no service is declared for l4xnat farms
	if ( $type eq 'l4xnat' && $service )
	{
		my $errormsg = "L4xNAT profile farms do not have services.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 400, body => $body } );
	}

	# make service variable empty for l4xnat functions
	$service = '' if $type eq "l4xnat";

	# check if the service exists for http farms
	if ( $type =~ /^https?$/ )
	{
		require Zevenet::Farm::HTTP::Service;

		if ( !grep( /^$service$/, &getHTTPFarmServices( $farmname ) ) )
		{
			my $errormsg = "Invalid service name, please insert a valid value.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};
			&httpResponse( { code => 404, body => $body } );
		}
	}

	# check farmguardian time interval
	if ( exists ( $json_obj->{ fgtimecheck } ) && ! &getValidFormat( 'fg_time', $json_obj->{ fgtimecheck } ) )
	{
		my $errormsg = "Invalid format, please insert a valid fgtimecheck.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 400, body => $body } );
	}
	# check farmguardian command
	elsif ( exists ( $json_obj->{ fgscript } ) && $json_obj->{ fgscript } eq '' )
	{
		my $errormsg = "Invalid fgscript, can't be blank.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 400, body => $body } );
	}
	# check farmguardian enabled
	elsif ( exists ( $json_obj->{ fgenabled } ) && ! &getValidFormat( 'fg_enabled', $json_obj->{ fgenabled } ) )
	{
		my $errormsg = "Invalid format, please insert a valid fgenabled.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 400, body => $body } );
	}
	# check farmguardian log
	elsif ( exists ( $json_obj->{ fglog } ) && ! &getValidFormat( 'fg_log', $json_obj->{ fglog } ) )
	{
		my $errormsg = "Invalid format, please insert a valid fglog.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 400, body => $body } );
	}

	my @allowParams = ( "fgtimecheck", "fgscript", "fglog", "fgenabled" );

	# check optional parameters
	if ( my $errormsg = &getValidOptParams( $json_obj, \@allowParams ) )
	{
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 400, body => $body } );
	}

	if ( $type eq 'gslb' && eval { require Zevenet::API3::Farm::GSLB; } )
	{
		&modify_gslb_farmguardian( $json_obj, $farmname, $service );
	}
	else
	{
		my $errormsg = "Farm guardian is not supported for the requested farm profile.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 400, body => $body } );
	}

	# HTTP or L4xNAT
	require Zevenet::FarmGuardian;

	# get current farmguardian configuration
	my @fgconfig = &getFarmGuardianConf( $farmname, $service );

	chomp @fgconfig;
	my (undef, $timetocheck, $check_script, $usefarmguardian, $farmguardianlog) = @fgconfig;

	$timetocheck += 0;
	$timetocheck = 5 if ! $timetocheck;

	$check_script =~ s/\"/\'/g;

	# update current configuration with new settings
	if ( exists $json_obj->{ fgtimecheck } ) {
		$timetocheck = $json_obj->{ fgtimecheck };
		$timetocheck = $timetocheck + 0;
	}
	if ( exists $json_obj->{ fgscript } ) {
		$check_script = $json_obj->{ fgscript }; # FIXME: Make safe script string
	}
	if ( exists $json_obj->{ fgenabled } ) {
		$usefarmguardian = $json_obj->{ fgenabled };
	}
	if ( exists $json_obj->{ fglog } ) {
		$farmguardianlog = $json_obj->{ fglog };
	}

	# apply new farmguardian configuration
	&runFarmGuardianStop( $farmname, $service );
	&runFarmGuardianRemove( $farmname, $service );

	my $status =
	&runFarmGuardianCreate( $farmname, $timetocheck, $check_script,
							$usefarmguardian, $farmguardianlog, $service );

	# check for errors setting farmguardian
	if ( $status == -1 )
	{
		my $errormsg = "Error, trying to modify the farm guardian in a farm $farmname, it's not possible to create the FarmGuardian configuration file.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 400, body => $body } );
	}

	# run farmguardian if enabled and the farm running
	if ( &getFarmStatus( $farmname ) eq 'up' && $usefarmguardian eq 'true' )
	{
		if ( &runFarmGuardianStart( $farmname, $service ) == -1 )
		{
			my $errormsg = "Error, trying to modify the farm guardian in a farm $farmname, an error ocurred while starting the FarmGuardian service.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};
			&httpResponse( { code => 400, body => $body } );
		}
	}

	# no error found, return successful response
	my $errormsg = "Success, some parameters have been changed in farm guardian in farm $farmname.";
	my $body = {
				 description => $description,
				 params      => $json_obj,
				 message     => $errormsg,
	};

	&httpResponse( { code => 200, body => $body } );
}

1;
