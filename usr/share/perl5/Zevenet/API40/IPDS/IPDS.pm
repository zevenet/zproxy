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

use Zevenet::API40::HTTP;
include 'Zevenet::IPDS::Setup';

# GET /ipds$
sub get_ipds_rules_list
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	include 'Zevenet::IPDS::Core';

	my $desc = "List the available IPDS rules.";

	return &httpResponse(
		   { code => 200, body => { description => $desc, params => &getIPDSRules } } );
}

# GET /ipds/package$
sub get_ipds_package
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $desc   = "zevenet-ipds package status info";
	my $params = {};

	require Zevenet::Log;

	my $output = &getIpdsPackageStatus();

	# 0 if success (installed and updated) 1 updates available 2 not installed,
	$params->{ status } = "Installed and updated" if ( $output == 0 );
	$params->{ status } = "Updates available"     if ( $output == 1 );
	$params->{ status } = "Not installed"         if ( $output == 2 );

	#Error in getIpdsPackageStatus
	return
	  &httpErrorResponse(
						  {
							code => 400,
							desc => $desc,
							msg  => "Error obtaining the status of zevenet-ipds package"
						  }
	  ) if ( !exists $params->{ status } );

	#Obtain last update ruleset date
	if ( $output == 0 || $output == 1 )
	{
		my $error  = 0;
		my $output = &getIpdsRulesetDate();
		if ( defined $output && $output =~ s/^(\d\d)(\d\d)(\d\d).*/$3\-$2\-20$1/ )
		{
			$params->{ ruleset_date } = $output;
		}
		else
		{
			return
			  &httpErrorResponse(
								  {
									code => 400,
									desc => $desc,
									msg  => "Error obtaining the update date of the ruleset"
								  }
			  );
		}
	}

	#Obtain schedule
	my $output = &getIpdsSchedule();
	if ( defined $output )
	{
		$params->{ scheduled } =
		  "$output->{mode}, each day $output->{frequency} at $output->{time}->{hour}:"
		  . sprintf ( "%02d", $output->{ time }->{ minute } )
		  if ( $output->{ mode } ne "" && $output->{ mode } ne "daily" );
		$params->{ scheduled } =
		  "$output->{mode} at $output->{time}->{hour}:"
		  . sprintf ( "%02d", $output->{ time }->{ minute } )
		  if ( $output->{ mode } eq "daily" and $output->{ frequency } == 0 );
		$params->{ scheduled } =
		    "$output->{mode} from $output->{time}->{hour}:"
		  . sprintf ( "%02d", $output->{ time }->{ minute } )
		  . " to 23:00 each $output->{frequency} hours"
		  if ( $output->{ mode } eq "daily" and $output->{ frequency } != 0 );
		$params->{ scheduled } = "none" if ( $output->{ mode } eq "" );
		$params->{ mode }      = $output->{ mode };
		$params->{ frequency } = 0;
		$params->{ frequency } = $output->{ frequency } + 0
		  if ( $output->{ frequency } ne "" );
		$params->{ time }->{ hour }   = $output->{ time }->{ hour } + 0;
		$params->{ time }->{ minute } = $output->{ time }->{ minute } + 0;
		$params->{ mode } = "disabled" if ( !length $output->{ mode } );
	}
	else
	{
		return
		  &httpErrorResponse(
							  {
								code => 400,
								desc => $desc,
								msg  => "Error obtaining IPDS package instalation schedule"
							  }
		  );
	}
	return &httpResponse(
				 { code => 200, body => { description => $desc, params => $params } } );
}

# POST /ipds/package/actions$
sub set_ipds_package
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $dpkg_bin = &getGlobalConfiguration( 'dpkg_bin' );
	my $desc     = "Execute an action over the zevenet-ipds package";
	my $outParam = {};
	my $msg      = "";

	my $params = {
				   action => {
							   required   => "true",
							   non_blank  => "true",
							   values     => ["upgrade", "schedule"],
							   format_msg => "Invalid value for action parameter"
				   },
				   mode      => { required => "false" },
				   frequency => { required => "false" },
				   time      => { required => "false" },
	};

	#Check input format for schedule
	if ( $json_obj->{ action } eq "schedule" )
	{
		$params->{ mode } = {
							  required  => "true",
							  non_blank => "true",
							  values => ["hour", "daily", "weekly", "monthly", "disabled"],
							  format_msg => "Invalid value for mode parameter",
		};

		if ( $json_obj->{ mode } eq "daily" )
		{
			$params->{ frequency } = {
							required   => "true",
							non_blank  => "true",
							interval   => "0,23",
							format_msg => "Invalid value for frequency parameter in daily mode",
			};
			$params->{ time } = {
								  required  => "true",
								  non_blank => "true",
								  ref       => "hash",
			};
		}
		elsif ( $json_obj->{ mode } eq "weekly" )
		{
			$params->{ frequency } = {
						   required   => "true",
						   non_blank  => "true",
						   interval   => "1,7",
						   format_msg => "Invalid value for frequency parameter in weekly mode",
			};
			$params->{ time } = {
								  required  => "true",
								  non_blank => "true",
								  ref       => "hash",
			};
		}
		elsif ( $json_obj->{ mode } eq "monthly" )
		{
			$params->{ frequency } = {
						  required   => "true",
						  non_blank  => "true",
						  interval   => "1,31",
						  format_msg => "Invalid value for frequency parameter in monthly mode",
			};
			$params->{ time } = {
								  required  => "true",
								  non_blank => "true",
								  ref       => "hash",
			};
		}
	}

	require Zevenet::Validate;

	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );

	return &httpErrorResponse( { code => 400, desc => $desc, msg => $error_msg } )
	  if ( $error_msg );

	#Check time parameter -> {hour, minute }
	if ( $json_obj->{ action } eq "schedule" && $json_obj->{ mode } ne "disabled" )
	{
		my $params = {
					   hour => {
								 required   => "true",
								 non_blank  => "true",
								 interval   => "0,23",
								 format_msg => "Invalid hour value"
					   },
					   minute => {
								   required   => "true",
								   non_blank  => "true",
								   interval   => "00,59",
								   format_msg => "Invalid minute value"
					   },
		};
		$error_msg = &checkZAPIParams( $json_obj->{ time }, $params, $desc );

		return &httpErrorResponse( { code => 400, desc => $desc, msg => $error_msg } )
		  if ( $error_msg );
		$outParam = {
					  'mode'      => $json_obj->{ mode },
					  'frequency' => $json_obj->{ frequency } + 0,
					  'time'      => {
								  'hour'   => $json_obj->{ time }->{ hour } + 0,
								  'minute' => $json_obj->{ time }->{ minute } + 0
					  },
		};
		$outParam->{ scheduled } =
		  "$json_obj->{mode}, each day $json_obj->{frequency} at $json_obj->{time}->{hour}:"
		  . sprintf ( "%02d", $json_obj->{ time }->{ minute } )
		  if ( $json_obj->{ mode } ne "" && $json_obj->{ mode } ne "daily" );
		$outParam->{ scheduled } =
		  "$json_obj->{mode} at $json_obj->{time}->{hour}:"
		  . sprintf ( "%02d", $json_obj->{ time }->{ minute } )
		  if ( $json_obj->{ mode } eq "daily" and $json_obj->{ frequency } == 0 );
		$outParam->{ scheduled } =
		    "$json_obj->{mode} from $json_obj->{time}->{hour}:"
		  . sprintf ( "%02d", $json_obj->{ time }->{ minute } )
		  . " to 23:00 each $json_obj->{frequency} hours"
		  if ( $json_obj->{ mode } eq "daily" and $json_obj->{ frequency } != 0 );
		$outParam->{ scheduled } = "none" if ( $json_obj->{ mode } eq "" );
	}
	elsif (    $json_obj->{ action } eq "schedule"
			&& $json_obj->{ mode } eq "disabled" )
	{
		$outParam = {
					  frequency => 0,
					  mode      => "disabled",
					  scheduled => "none",
					  time      => { hour => 0, minute => 0, },
		};
	}

	my $error = &runIpdsUpgrade( $json_obj );

	$msg = "IPDS Package is already in the latest version"
	  unless ( defined $error );

	if ( $error && $json_obj->{ mode } eq "disabled" )
	{
		$msg =
		  "Error disabling the IPDS package upgrade schedule, It is already disabled";
		return &httpErrorResponse( { code => 400, desc => $desc, msg => $msg } );
	}

	if ( $error )
	{
		$msg = "A problem occurred when trying to $json_obj->{ action }";
		return &httpErrorResponse( { code => 400, desc => $desc, msg => $msg } );
	}

	if ( $json_obj->{ action } eq "upgrade" )
	{
		my $date = &getIpdsRulesetDate();
		$date =~ s/^(\d\d)(\d\d)(\d\d).*/$3\-$2\-20$1/;
		$outParam = { 'ruleset_date' => $date };
	}

	# Set Status
	my $status = &getIpdsPackageStatus();

	# 0 if success (installed and updated) 1 updates available 2 not installed,
	$outParam->{ status } = "Installed and updated" if ( $status == 0 );
	$outParam->{ status } = "Updates available"     if ( $status == 1 );
	$outParam->{ status } = "Not installed"         if ( $status == 2 );
	$outParam->{ msg }    = $msg                    if ( length $msg );

	return &httpResponse(
					  { code => 200, body => { params => $outParam, desc => $desc } } );
}

1;
