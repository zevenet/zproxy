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

use Zevenet::Notify;

# GET /system/notifications/methods/METHOD
sub get_notif_methods
{
	my $key = shift;
	$key = 'Smtp' if ( $key eq 'email' );
	my $description = "Get notifications email methods";
	my $methods     = &getNotifSendersSmtp();

	&httpResponse(
		 { code => 200, body => { description => $description, params => $methods } } );
}

#  POST /system/notifications/methods/METHOD
sub set_notif_methods
{
	my $json_obj = shift;
	my $key      = shift;
	$key = 'Smtp' if ( $key eq 'email' );
	my $description = "Set notifications email methods";
	my $errormsg;
	my @allowParams;

	if ( $key eq 'Smtp' )
	{
		@allowParams = ( "user", "server", "password", "from", "to", "tls" );
		$errormsg = &getValidOptParams( $json_obj, \@allowParams );
		if ( !$errormsg )
		{
			if ( !&getValidFormat( "notif_tls", $json_obj->{ 'tls' } ) )
			{
				$errormsg = "TLS only can be true or false.";
			}
			else
			{
				$errormsg = &setNotifSenders( $key, $json_obj );
				if ( !$errormsg )
				{
					&httpResponse(
						{ code => 200, body => { description => $description, params => $json_obj } } );
				}
				else
				{
					$errormsg = "There was a error modifying $key.";
				}
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

# GET /system/notifications/alerts
sub get_notif_alert_status
{
	my $description = "Get notifications alert status";
	my @output;
	my $status = &getNotifData( 'alerts', 'Backend', 'Status' );
	$status = 'disabled' if ( $status eq 'off' );
	$status = 'enabled'  if ( $status eq 'on' );

	push @output, { 'alert' => 'backends', 'status' => $status };
	$status = &getNotifData( 'alerts', 'Cluster', 'Status' );
	$status = 'disabled' if ( $status eq 'off' );
	$status = 'enabled'  if ( $status eq 'on' );
	push @output, { 'alert' => 'cluster', 'status' => $status };

	&httpResponse(
		 { code => 200, body => { description => $description, params => \@output } } );
}

# GET /system/notifications/alerts/ALERT
sub get_notif_alert
{
	my $alert       = shift;
	my $description = "Get notifications alert $alert settings";
	my $param       = &getNotifAlert( $alert );

	&httpResponse(
		   { code => 200, body => { description => $description, params => $param } } );
}

#  POST /system/notifications/alerts/ALERT
sub set_notif_alert
{
	my $json_obj    = shift;
	my $alert       = shift;
	my $description = "Set notifications alert $alert";

	my @allowParams = ( "avoidflappingtime", "prefix" );
	my $errormsg = &getValidOptParams( $json_obj, \@allowParams );
	if ( !$errormsg )
	{
		if ( !&getValidFormat( 'notif_time', $json_obj->{ 'avoidflappingtime' } ) )
		{
			$errormsg = "Error, it's necessary add a valid action.";
		}
		elsif ( exists $json_obj->{ 'avoidflappingtime' } && $alert eq 'cluster' )
		{
			$errormsg = "Avoid flapping time is not configurable in cluster alerts.";
		}
		else
		{
			my $params;
			$params->{ 'PrefixSubject' } = $json_obj->{ 'prefix' }
			  if ( exists $json_obj->{ 'prefix' } );
			$params->{ 'SwitchTime' } = $json_obj->{ 'avoidflappingtime' }
			  if ( $json_obj->{ 'avoidflappingtime' } );
			$errormsg = &setNotifAlerts( $alert, $params );
			if ( !$errormsg )
			{
				&httpResponse(
					{ code => 200, body => { description => $description, params => $json_obj } } );
			}
			else
			{
				$errormsg = "There was a error modifiying $alert.";
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

#  POST /system/notifications/alerts/ALERT/actions
sub set_notif_alert_actions
{
	my $json_obj    = shift;
	my $alert       = shift;
	my $description = "Set notifications alert $alert actions";

	my @allowParams = ( "action" );
	my $errormsg = &getValidOptParams( $json_obj, \@allowParams );
	if ( !$errormsg )
	{
		if ( !&getValidFormat( 'notif_action', $json_obj->{ 'action' } ) )
		{
			$errormsg = "Error, it's necessary add a valid action";
		}
		else
		{
			$errormsg = &setNotifAlertsAction( $alert, $json_obj->{ 'action' } );
			if ( !$errormsg )
			{
				&httpResponse(
					{ code => 200, body => { description => $description, params => $json_obj } } );
			}
			elsif ( $errormsg == -2 )
			{
				$errormsg = "$alert is already $json_obj->{action}.";
			}
			else
			{
				$errormsg = "There was a error in $alert action.";
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

sub send_test_mail
{
	my $json_obj    = shift;
	my $description = "Send test mail";

	my @allowParams = ( "action" );
	my $errormsg = &getValidOptParams( $json_obj, \@allowParams );
	if ( !$errormsg )
	{
		if ( $json_obj->{ 'action' } ne "test" )
		{
			$errormsg = "Error, it's necessary add a valid action";
		}
		else
		{
			$errormsg = &sendTestMail;
			if ( ! $errormsg )
			{
				$errormsg = "Test mail sent successful.";
				&httpResponse(
					{ code => 200, body => { description => $description, success => "true", message => $errormsg } } );
			}
			else
			{
				$errormsg = "Test mail sent but it hasn't reached the destination.";
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
	
}

1;
