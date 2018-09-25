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

use Zevenet::API32::HTTP;


include 'Zevenet::Notify';

# GET /system/notifications/methods/METHOD
sub get_notif_methods
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
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
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my $json_obj = shift;
	my $key      = shift;

	my $desc = "Set notifications email methods";
	$key = 'Smtp' if ( $key eq 'email' );

	if ( $key ne 'Smtp' )
	{
		my $msg = "Such notification method is not supported.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my @allowParams = ( "user", "server", "password", "from", "to", "tls" );
	my $msg = &getValidOptParams( $json_obj, \@allowParams );
	if ( $msg )
	{
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( !&getValidFormat( "notif_tls", $json_obj->{ 'tls' } ) )
	{
		my $msg = "TLS only can be true or false.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

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
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
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
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my $alert = shift;

	my $desc = "Get notifications alert $alert settings";
	my $param       = &getNotifAlert( $alert );

	return &httpResponse(
		   { code => 200, body => { description => $desc, params => $param } } );
}

#  POST /system/notifications/alerts/ALERT
sub set_notif_alert
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my $json_obj = shift;
	my $alert    = shift;

	my $desc = "Set notifications alert $alert";

	my @allowParams = ( "avoidflappingtime", "prefix" );
	my $param_msg = &getValidOptParams( $json_obj, \@allowParams );

	if ( $param_msg )
	{
		return &httpErrorResponse( code => 400, desc => $desc, msg => $param_msg );
	}

	if ( !&getValidFormat( 'notif_time', $json_obj->{ 'avoidflappingtime' } ) )
	{
		my $msg = "Error, it's necessary add a valid action.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
	elsif ( exists $json_obj->{ 'avoidflappingtime' } && $alert eq 'cluster' )
	{
		my $msg = "Avoid flapping time is not configurable in cluster alerts.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $params;
	$params->{ 'PrefixSubject' } = $json_obj->{ 'prefix' }            if ( exists $json_obj->{ 'prefix' } );
	$params->{ 'SwitchTime' }    = $json_obj->{ 'avoidflappingtime' } if ( $json_obj->{ 'avoidflappingtime' } );

	my $error = &setNotifAlerts( $alert, $params );
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
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my $json_obj = shift;
	my $alert    = shift;

	my $desc = "Set notifications alert $alert actions";

	my @allowParams = ( "action" );
	my $param_msg = &getValidOptParams( $json_obj, \@allowParams );
	if ( $param_msg )
	{
		return &httpErrorResponse( code => 400, desc => $desc, msg => $param_msg );
	}

	if ( !&getValidFormat( 'notif_action', $json_obj->{ 'action' } ) )
	{
		my $msg = "Error, it's necessary add a valid action";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

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

	return &httpResponse(
			   { code => 200, body => { description => $desc, params => $json_obj } } );
}

sub send_test_mail
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my $json_obj = shift;

	my $desc        = "Send test mail";

	my @allowParams = ( "action" );
	my $param_msg = &getValidOptParams( $json_obj, \@allowParams );
	if ( $param_msg )
	{
		return &httpErrorResponse( code => 400, desc => $desc, msg => $param_msg );
	}

	if ( $json_obj->{ 'action' } ne "test" )
	{
		my $msg = "Error, it's necessary add a valid action";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $error = &sendTestMail();
	if ( $error )
	{
		my $msg = "Test mail sent but it hasn't reached the destination.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $msg = "Test mail sent successful.";
	my $body = { description => $desc, success => "true", message => $msg };

	return &httpResponse( { code => 200, body => $body } );
}

1;
