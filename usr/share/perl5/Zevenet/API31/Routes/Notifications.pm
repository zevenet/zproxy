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

my $q = getCGI();


if ( $q->path_info =~ qr{^/system/notifications} )
{
	require Zevenet::API31::System::Notification;

	my $alert_re  = &getValidFormat( 'notif_alert' );
	my $method_re = &getValidFormat( 'notif_method' );

	#  GET notification methods
	GET qr{^/system/notifications/methods/($method_re)$} => \&get_notif_methods;

	#  POST notification methods
	POST qr{^/system/notifications/methods/($method_re)$} => \&set_notif_methods;

	#  GET notification alert status
	GET qr{^/system/notifications/alerts$} => \&get_notif_alert_status;

	#  GET notification alerts
	GET qr{^/system/notifications/alerts/($alert_re)$} => \&get_notif_alert;

	#  POST notification alerts
	POST qr{^/system/notifications/alerts/($alert_re)$} => \&set_notif_alert;

	#  POST notification alert actions
	POST qr{^/system/notifications/alerts/($alert_re)/actions$} => \&set_notif_alert_actions;

	#  POST  notifications test
	POST qr{^/system/notifications/methods/email/actions$} => \&send_test_mail;
}

1;
