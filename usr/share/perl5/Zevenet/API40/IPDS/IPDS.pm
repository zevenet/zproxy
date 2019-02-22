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

use Zevenet::API40::HTTP;
include "Zevenet::IPDS::Setup";

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
		if ( defined $output && $output =~ s/(\d\d)(\d\d)(\d\d)/$1\-$2\-20$3/ )
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
		  . sprintf ( "%02d", $output->{ time }->{ minutes } )
		  if ( $output->{ mode } ne "" && $output->{ mode } ne "daily" );
		$params->{ scheduled } =
		  "$output->{mode} at $output->{time}->{hour}:"
		  . sprintf ( "%02d", $output->{ time }->{ minutes } )
		  if ( $output->{ mode } eq "daily" and $output->{ frequency } == 0 );
		$params->{ scheduled } =
		    "$output->{mode} from $output->{time}->{hour}:"
		  . sprintf ( "%02d", $output->{ time }->{ minutes } )
		  . " each $output->{frequency} hours"
		  if ( $output->{ mode } eq "daily" and $output->{ frequency } != 0 );
		$params->{ scheduled } = "none" if ( $output->{ mode } eq "" );
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

# PUT /ipds/package/actions$
sub set_ipds_package
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $dpkg_bin = &getGlobalConfiguration( 'dpkg_bin' );
	my $desc     = "Execute an action over the zevenet-ipds package";
	my $msg      = "";

	my $params = {
		action => {
					required   => "true",
					non_blank  => "true",
					values     => ["upgrade", "schedule"],
					format_msg => "Invalid value for action parameter"
		},

	};

	#Check input format for schedule
	if ( $json_obj->{ action } eq "schedule" )
	{
		$params->{ mode } = {
							  required  => "true",
							  non_blank => "true",
							  values => ["hour", "daily", "weekly", "monthly", "disable"],
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
		}
		elsif ( $json_obj->{ mode } eq "weekly" )
		{
			$params->{ frequency } = {
						   required   => "true",
						   non_blank  => "true",
						   interval   => "1,7",
						   format_msg => "Invalid value for frequency parameter in weekly mode",
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
		}
		if ( $json_obj->{ mode } ne "disable" )
		{
			$params->{ time } = {
								  required  => "true",
								  non_blank => "true",
			};
		}
	}

	# When action is wrong, there could be other fields
	elsif ( $json_obj->{ action } ne "upgrade" )
	{
		$params->{ mode }      = { required => "false", };
		$params->{ frequency } = { required => "false", };
		$params->{ frequency } = { required => "false", };
	}

	require Zevenet::Validate;

	my $error_msg = &checkZAPIParams( $json_obj, $params );

	return &httpErrorResponse( { code => 400, desc => $desc, msg => $error_msg } )
	  if ( $error_msg );

	#Check time parameter -> {hour, minutes }
	if ( ref $json_obj->{ time } && $json_obj->{ action } eq "schedule" )
	{
		my $params = {
					   hour => {
								 required   => "true",
								 non_blank  => "true",
								 interval   => "0,23",
								 format_msg => "Invalid hour value"
					   },
					   minutes => {
									required   => "true",
									non_blank  => "true",
									interval   => "00,59",
									format_msg => "Invalid minutes value"
					   },
		};
		$error_msg = &checkZAPIParams( $json_obj->{ time }, $params );

		return &httpErrorResponse( { code => 400, desc => $desc, msg => $error_msg } )
		  if ( $error_msg );
		$msg =
		  "IPDS upgrade $json_obj->{ mode } $json_obj->{ action } successfully done";
	}

	# Is not a reference, so it's wrong
	elsif (    $json_obj->{ action } eq "schedule"
			&& $json_obj->{ mode } ne "disable" )
	{
		$error_msg =
		  "Invalid value for time parameter. Please, try with: minutes, hour";
		return &httpErrorResponse( { code => 400, desc => $desc, msg => $error_msg } )
		  if ( $error_msg );
	}
	else
	{
		$msg = "IPDS package action successfully done";
	}

	my $error = &runIpdsUpgrade( $json_obj );
	if ( $error && $json_obj->{ mode } eq "disable" )
	{
		$msg =
		  "Error disabling the IPDS package upgrade schedule, It is already disable";
		return &httpErrorResponse( { code => 400, desc => $desc, msg => $msg } );
	}

	if ( $error )
	{
		$msg = "A problem occurred when trying to $json_obj->{ action }";
		return &httpErrorResponse( { code => 400, desc => $desc, msg => $msg } );
	}

	return &httpResponse( { code => 200, body => { desc => $desc, msg => $msg } } );
}

1;
