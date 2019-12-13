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

include 'Zevenet::Notify';

# GET /system/notifications/methods/METHOD
sub get_notif_methods
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $key = shift;

	my $desc = "Get notifications email methods";
	$key = 'Smtp' if ( $key eq 'email' );

	my $methods = &getNotifSendersSmtp();

	return &httpResponse(
				{ code => 200, body => { description => $desc, params => $methods } } );
}

#  POST /system/notifications/methods/METHOD
sub set_notif_methods
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $key      = shift;

	my $desc = "Set notifications email methods";
	$key = 'Smtp' if ( $key eq 'email' );

	if ( $key ne 'Smtp' )
	{
		my $msg = "Such notification method is not supported.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $params = {
				   "user"     => {},
				   "password" => {},
				   "server"   => {},
				   "from"     => {},
				   "to"       => {},
				   "tls"      => {
							  'valid_format' => 'boolean',
							  'non_blank'    => 'true',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	my $error = &setNotifSenders( $key, $json_obj );
	if ( $error )
	{
		my $msg = "There was a error modifying $key.";
	}

	return &httpResponse(
			   { code => 200, body => { description => $desc, params => $json_obj } } );
}

# GET /system/notifications/alerts
sub get_notif_alert_status
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $desc = "Get notifications alert status";
	my @output;

	my $status = &getNotifData( 'alerts', 'Backend', 'Status' );
	$status = 'disabled' if ( $status eq 'off' );
	$status = 'enabled'  if ( $status eq 'on' );
	push @output, { 'alert' => 'backends', 'status' => $status };

	$status = &getNotifData( 'alerts', 'Cluster', 'Status' );
	$status = 'disabled' if ( $status eq 'off' );
	$status = 'enabled'  if ( $status eq 'on' );
	push @output, { 'alert' => 'cluster', 'status' => $status };

	return &httpResponse(
				{ code => 200, body => { description => $desc, params => \@output } } );
}

# GET /system/notifications/alerts/ALERT
sub get_notif_alert
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $alert = shift;

	my $desc  = "Get notifications alert $alert settings";
	my $param = &getNotifAlert( $alert );

	return &httpResponse(
				  { code => 200, body => { description => $desc, params => $param } } );
}

#  POST /system/notifications/alerts/ALERT
sub set_notif_alert
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $alert    = shift;

	my $desc = "Set notifications alert $alert";

	my $params = {
				   "prefix" => {
								 'regex' => '[\w-]+',
				   },
	};

	if ( $alert eq 'backends' )
	{
		$params->{ "avoidflappingtime" } = {
											 'valid_format' => 'notif_time',
											 'non_blank'    => 'true',
		};
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	my $args;
	$args->{ 'PrefixSubject' } = $json_obj->{ 'prefix' }
	  if ( exists $json_obj->{ 'prefix' } );
	$args->{ 'SwitchTime' } = $json_obj->{ 'avoidflappingtime' }
	  if ( $json_obj->{ 'avoidflappingtime' } );

	my $error = &setNotifAlerts( $alert, $args );
	if ( $error )
	{
		my $msg = "There was a error modifiying $alert.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	return &httpResponse(
			   { code => 200, body => { description => $desc, params => $json_obj } } );
}

#  POST /system/notifications/alerts/ALERT/actions
sub set_notif_alert_actions
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $alert    = shift;

	my $desc = "Set notifications alert $alert actions";

	my $params = {
				   "action" => {
								 'values'    => ['enable', 'disable'],
								 'non_blank' => 'true',
								 'required'  => 'true',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	my $error = &setNotifAlertsAction( $alert, $json_obj->{ 'action' } );
	if ( $error eq '-2' )
	{
		my $msg = "$alert is already $json_obj->{action}.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
	elsif ( $error )
	{
		my $msg = "There was a error in $alert action.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $status = "";
	$status = &getNotifData( 'alerts', 'Backend', 'Status' )
	  if ( $alert eq "backends" );
	$status = &getNotifData( 'alerts', 'Cluster', 'Status' )
	  if ( $alert eq "cluster" );
	$status = 'disabled' if ( $status eq 'off' );
	$status = 'enabled'  if ( $status eq 'on' );

	my $response_obj = $json_obj;
	$response_obj->{ status } = $status;

	return &httpResponse(
		   { code => 200, body => { description => $desc, params => $response_obj } } );
}

sub send_test_mail
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	my $desc = "Send test mail";

	my $params = {
				   "action" => {
								 'values'    => ['test'],
								 'non_blank' => 'true',
								 'required'  => 'true',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	my $error = &sendTestMail();
	if ( $error )
	{
		my $msg = "Test mail sent but it hasn't reached the destination.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $msg = "Test mail sent successfully.";
	my $body = { description => $desc, success => "true", message => $msg };

	return &httpResponse( { code => 200, body => $body } );
}

1;
