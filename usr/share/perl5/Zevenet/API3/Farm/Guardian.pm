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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;

	require Zevenet::Farm::Core;
	require Zevenet::FarmGuardian;

	my $description = "Modify farm guardian";
	my $error       = "false";
	my $needRestart;
	my $errormsg;
	my $type    = &getFarmType( $farmname );
	my $service = $json_obj->{ 'service' };
	delete $json_obj->{ 'service' };

	my @allowParams = ( "fgtimecheck", "fgscript", "fglog", "fgenabled" );

	include 'Zevenet::Farm::GSLB::Service';
	require Zevenet::Farm::HTTP::Service;

	# validate FARM NAME
	if ( !&getFarmExists( $farmname ) )
	{
		$errormsg = "The farmname $farmname does not exist.";
		my $body =
		  { description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 404, body => $body } );
	}

	# validate FARM TYPE
	elsif ( !&getValidFormat( 'fg_type', $type ) )
	{
		$errormsg = "Farm guardian is not supported for the requested farm profile.";
		my $body =
		  { description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 400, body => $body } );
	}

	# validate no service in l4xnat
	elsif ( $service && $type eq 'l4xnat' )
	{
		$errormsg = "Farm guardian not use services in l4xnat farms.";
		my $body =
		  { description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 400, body => $body } );
	}

	# validate exist service for http(s) farms
	elsif ( $type =~ /(?:http|https)/
			&& !grep ( /^$service$/, &getHTTPFarmServices( $farmname ) ) )
	{
		$errormsg = "Invalid service name, please insert a valid value.";
		my $body =
		  { description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 404, body => $body } );
	}

	# validate exist service for gslb farms
	elsif ( $type =~ /gslb/
			&& !grep ( /^$service$/, &getGSLBFarmServices( $farmname ) ) )
	{
		$errormsg = "Invalid service name, please insert a valid value.";
		my $body =
		  { description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 404, body => $body } );
	}

	my @fgKeys = ( "fg_time", "fg_log", "fg_enabled", "fg_type" );

	# check Params
	if ( exists ( $json_obj->{ fgtimecheck } )
		 && !&getValidFormat( 'fg_time', $json_obj->{ fgtimecheck } ) )
	{
		$errormsg = "Invalid format, please insert a valid fgtimecheck.";
	}
	elsif ( exists ( $json_obj->{ fgscript } ) && $json_obj->{ fgscript } =~ /^$/ )
	{
		$errormsg = "Invalid fgscript, can't be blank.";
	}
	elsif ( exists ( $json_obj->{ fgenabled } )
			&& !&getValidFormat( 'fg_enabled', $json_obj->{ fgenabled } ) )
	{
		$errormsg = "Invalid format, please insert a valid fgenabled.";
	}
	elsif ( exists ( $json_obj->{ fglog } )
			&& !&getValidFormat( 'fg_log', $json_obj->{ fglog } ) )
	{
		$errormsg = "Invalid format, please insert a valid fglog.";
	}

	if ( !$errormsg )
	{
		$errormsg = &getValidOptParams( $json_obj, \@allowParams );
	}

	my $fg = &getFGFarm( $farmname, $service );
	if ( $fg )
	{
		my $num_farms = scalar @{ &getFGObject( $fg )->{ farms } };
		if ( $num_farms > 1 )
		{
			my $errormsg =
			  "Farm guardian $fg is used for several farms, modify it from API 3.2 or later";
			my $body =
			  { description => $description, error => "true", message => $errormsg };
			&httpResponse( { code => 400, body => $body } );
		}
	}

	if ( !$errormsg )
	{
		if ( $type eq 'gslb' )
		{
			include 'Zevenet::Farm::GSLB::FarmGuardian';

			# Change check script
			my $fgStatus =
			  ( exists $json_obj->{ fgenabled } )
			  ? $json_obj->{ fgenabled }
			  : &getGSLBFarmFGStatus( $farmname, $service );
			my ( $fgTime, $fgCmd ) = &getGSLBFarmGuardianParams( $farmname, $service );

			$fgTime = $json_obj->{ fgtimecheck } if ( exists $json_obj->{ fgtimecheck } );
			$fgCmd  = $json_obj->{ fgscript }    if ( exists $json_obj->{ fgscript } );

			&runFarmGuardianRemove( $farmname, $service );
			&runFarmGuardianCreate( $farmname, $fgTime, $fgCmd,
									$fgStatus, 'false', $service );

			# no error found, return successful response
			( $fgTime, $fgCmd ) = &getGSLBFarmGuardianParams( $farmname, $service );
			$fgStatus = &getGSLBFarmFGStatus( $farmname, $service );
		}

		# https(s) and l4xnat
		else
		{
			my @fgconfig;

			if ( $type eq "l4xnat" )
			{
				@fgconfig = &getFarmGuardianConf( $farmname, "" );
			}
			elsif ( $type eq "http" || $type eq "https" )
			{
				@fgconfig = &getFarmGuardianConf( $farmname, $service );
			}

			my $timetocheck;
			$timetocheck = $fgconfig[1] + 0 if defined $fgconfig[1];
			$timetocheck = 5 if ( !$timetocheck );

			my $check_script = ( defined $fgconfig[2] ) ? $fgconfig[2] : "";
			$check_script =~ s/\n//g;
			$check_script =~ s/\"/\'/g;

			my $usefarmguardian = ( defined $fgconfig[3] ) ? $fgconfig[3] : "";
			$usefarmguardian =~ s/\n//g;

			my $farmguardianlog = ( defined $fgconfig[4] ) ? $fgconfig[4] : "";

			if ( exists ( $json_obj->{ fgtimecheck } ) )
			{
				$timetocheck = $json_obj->{ fgtimecheck };
				$timetocheck = $timetocheck + 0;
			}

			if ( exists ( $json_obj->{ fgscript } ) )
			{
				# FIXME: Make safe script string
				$check_script = $json_obj->{ fgscript };
			}

			if ( exists ( $json_obj->{ fgenabled } ) )
			{
				$usefarmguardian = $json_obj->{ fgenabled };
			}

			if ( exists ( $json_obj->{ fglog } ) )
			{
				$farmguardianlog = $json_obj->{ fglog };
			}

			if ( $type eq "l4xnat" )
			{
				&runFarmGuardianStop( $farmname, "" );
				&runFarmGuardianRemove( $farmname, "" );
				my $status =
				  &runFarmGuardianCreate( $farmname, $timetocheck, $check_script,
										  $usefarmguardian, $farmguardianlog, "" );
				if ( $status )
				{
					$errormsg =
					  "Error, trying to modify the farm guardian in a farm $farmname, it's not possible to create the FarmGuardian configuration file.";
				}
			}

			elsif ( $type eq "http" || $type eq "https" )
			{
				&runFarmGuardianStop( $farmname, $service );
				&runFarmGuardianRemove( $farmname, $service );
				my $status =
				  &runFarmGuardianCreate( $farmname, $timetocheck, $check_script,
										  $usefarmguardian, $farmguardianlog, $service );
				if ( $status != -1 )
				{
					if ( $usefarmguardian eq "true" )
					{
						if ( &runFarmGuardianStart( $farmname, $service ) == -1 )
						{
							$errormsg =
							  "Error, trying to modify the farm guardian in a farm $farmname, an error ocurred while starting the FarmGuardian service.";
						}
					}
				}
				else
				{
					$errormsg =
					  "Error, trying to modify the farm guardian in a farm $farmname, it's not possible to create the FarmGuardian configuration file.";
				}
			}
		}
	}

	if ( !$errormsg )
	{
		$errormsg =
		  "Success, some parameters have been changed in farm guardian in farm $farmname.";
		my $body =
		  { description => $description, params => $json_obj, message => $errormsg };

		require Zevenet::Farm::Base;

		if ( $type eq "gslb" && &getFarmStatus( $farmname ) eq 'up' )
		{
			require Zevenet::Farm::Action;

			&setFarmRestart( $farmname );
			$body->{ status } = 'needed restart';
		}

		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		my $body =
		  { description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 400, body => $body } );
	}
}

1;
