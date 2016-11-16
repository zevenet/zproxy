#!/usr/bin/perl 

##############################################################################
#
#     This file is part of the Zen Load Balancer Enterprise Edition software
#     package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This file cannot be distributed, released in public domain and/or for
#     commercial purposes.
#
###############################################################################

require "/usr/local/zenloadbalancer/www/system_functions.cgi";
require "/usr/local/zenloadbalancer/www/snmp_functions.cgi";

require "/usr/local/zenloadbalancer/www/Plugins/notifications.cgi";

dns:

#**
#  @api {get} /system/dns Request dns
#  @apiGroup SYSTEM
#  @apiDescription Get description of dns
#  @apiName GetDns
#  @apiVersion 3.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Post dns",
#   "params" : {
#      "primary" : "192.168.0.5",
#      "secundary" : "8.8.8.8"
#   }
#}
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/dns
#
#@apiSampleRequest off
#**
# GET /system/dns
sub get_dns
{
	my $description = "Get dns";
	my $dns         = &getDns();

	&httpResponse(
			 { code => 200, body => { description => $description, params => $dns } } );
}

#####Documentation of POST dns####
#**
#  @api {post} /system/dns Modify the dns
#  @apiGroup SYSTEM
#  @apiName PostDns
#  @apiDescription Modify primary and secondary dns
#  @apiVersion 3.0
#
#
# @apiSuccess	{string}	primary			DNS IP
# @apiSuccess	{string}	secondary		DNS IP
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Post dns",
#   "params" : {
#      "primary" : "8.8.4.4",
#      "secundary" : "8.8.8.8"
#   }
#}
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"secondary":"8.8.8.8","primary":"8.8.4.4"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/dns
#
# @apiSampleRequest off
#
#**
#  POST /system/dns
sub set_dns
{
	my $json_obj    = shift;
	my $description = "Post dns";
	my $errormsg;
	my @allowParams = ( "primary", "secondary" );

	$errormsg = &getValidOptParams( $json_obj, \@allowParams );
	if ( !$errormsg )
	{
		foreach my $key ( keys %{ $json_obj } )
		{
			if ( !&getValidFormat( 'dns_nameserver', $json_obj->{ $key } ) )
			{
				$errormsg = "Please, insert a nameserver correct.";
				last;
			}
		}
		if ( !$errormsg )
		{
			foreach my $key ( keys %{ $json_obj } )
			{
				$errormsg = &setDns( $key, $json_obj->{ $key } );
				last if ( $errormsg );
			}
			if ( !$errormsg )
			{
				my $dns = &getDns();
				&httpResponse(
						 { code => 200, body => { description => $description, params => $dns } } );
			}
			else
			{
				$errormsg = "There was a error modifying dns.";
			}
		}
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

ssh:

#**
#  @api {get} /system/ssh Request ssh
#  @apiGroup SYSTEM
#  @apiDescription Get description of ssh
#  @apiName GetSsh
#  @apiVersion 3.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Get ssh",
#   "params" : {
#      "listen" : "0.0.0.0",
#      "port" : "22"
#   }
#}
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/ssh
#
#@apiSampleRequest off
#**
# GET /system/ssh
sub get_ssh
{
	my $description = "Get ssh";
	my $ssh         = &getSsh();

	&httpResponse(
			 { code => 200, body => { description => $description, params => $ssh } } );
}

#####Documentation of POST ssh####
#**
#  @api {post} /system/ssh Modify the ssh settings
#  @apiGroup SYSTEM
#  @apiName PostSsh
#  @apiDescription Modify the port and ip mask where is listening ssh server
#  @apiVersion 3.0
#
#
#
# @apiSuccess	{Number}	port		Port where listen ssh server.
# @apiSuccess	{string}	listen		Mask of allowed IPs. Available IP version 4 and version 6.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Post ssh",
#   "params" : {
#      "listen" : "192.2.0.5",
#      "port" : "25"
#   }
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"port":"25","listen":"192.2.0.5"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/ssh
#
# @apiSampleRequest off
#
#**
#  POST /system/ssh
sub set_ssh
{
	my $json_obj    = shift;
	my $description = "Post ssh";
	my $errormsg;
	my @allowParams = ( "port", "listen" );

	$errormsg = &getValidOptParams( $json_obj, \@allowParams );
	if ( !$errormsg )
	{
		# Check key format
		foreach my $key ( keys %{ $json_obj } )
		{
			if ( !&getValidFormat( "ssh_$key", $json_obj->{ $key } ) )
			{
				$errormsg = "$key hasn't a correct format.";
				last;
			}
		}
		if ( !$errormsg )
		{
			$errormsg = &setSsh( $json_obj );
			if ( !$errormsg )
			{
				my $dns = &getSsh();
				&httpResponse(
						 { code => 200, body => { description => $description, params => $dns } } );
			}
			else
			{
				$errormsg = "There was a error modifying ssh.";
			}
		}
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

snmp:

#**
#  @api {get} /system/snmp Request snmp
#  @apiGroup SYSTEM
#  @apiDescription Get description of snmp
#  @apiName GetSnmp
#  @apiVersion 3.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Get snmp",
#   "params" : {
#      "community" : "public",
#      "ip" : "192.168.100.241",
#      "port" : "161",
#      "scope" : "0.0.0.0/0",
#      "status" : "true"
#   }
#}
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/snmp
#
#@apiSampleRequest off
#**
# GET /system/snmp
sub get_snmp
{
	my $description = "Get snmp";
	my %snmp        = %{ &getSnmpdConfig() };
	$snmp{ status } = &getSnmpdStatus();

	&httpResponse(
		   { code => 200, body => { description => $description, params => \%snmp } } );
}

#####Documentation of POST snmp####
#**
#  @api {post} /system/snmp Modify the snmp server settings
#  @apiGroup SYSTEM
#  @apiName PostSnmp
#  @apiDescription Modify snmp server settings
#  @apiVersion 3.0
#
#
#
# @apiSuccess	{string}		status		Enabled or disable snmp service. The options are true or false.
# @apiSuccess	{Number}	port			Port where listen snmp server.
# @apiSuccess	{scope}		ip				snmp ip
# @apiSuccess	{string}		scope		snmp scope
# @apiSuccess	{string}		community 	Id to access to a device stats.
#
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Post snmp",
#   "params" : {
#      "community" : "public",
#      "ip" : "192.168.100.240",
#      "port" : "656",
#      "scope" : "0.0.0.0/0",
#      "status" : "true"
#   }
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"status":"true", "port":"656"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/snmp
#
# @apiSampleRequest off
#
#**
#  POST /system/snmp
sub set_snmp
{
	my $json_obj    = shift;
	my $description = "Post snmp";
	my $errormsg;
	my @allowParams = ( "port", "status", "ip", "community", "scope" );

	$errormsg = &getValidOptParams( $json_obj, \@allowParams );
	if ( !$errormsg )
	{
		# Check key format
		foreach my $key ( keys %{ $json_obj } )
		{
			if ( !&getValidFormat( "snmp_$key", $json_obj->{ $key } ) )
			{
				$errormsg = "$key hasn't a correct format.";
				last;
			}
		}
		if ( !$errormsg )
		{
			my $status = $json_obj->{ 'status' };
			delete $json_obj->{ 'status' };
			my $snmp = &getSnmpdConfig();
			foreach my $key ( keys %{ $json_obj } )
			{
				$snmp->{ $key } = $json_obj->{ $key };
			}
			$errormsg = &setSnmpdConfig( $snmp );
			if ( !$errormsg )
			{
				if ( !$status && &getSnmpdStatus() eq 'true' )
				{
					&setSnmpdStatus( 'false' );    # stopping snmp
					&setSnmpdStatus( 'true' );     # starting snmp
				}
				elsif ( $status eq 'true' && &getSnmpdStatus() eq 'false' )
				{
					&setSnmpdStatus( 'true' );     # starting snmp
				}
				elsif ( $status eq 'false' && &getSnmpdStatus() eq 'true' )
				{
					&setSnmpdStatus( 'false' );    # stopping snmp
				}
				if ( !$errormsg )
				{
					$snmp->{ status } = &getSnmpdStatus();

					&httpResponse(
							{ code => 200, body => { description => $description, params => $snmp } } );
				}
			}
			else
			{
				$errormsg = "There was a error modifying ssh.";
			}
		}
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

license:

#**
#  @api {get} /system/license Request license
#  @apiGroup SYSTEM
#  @apiDescription Get license
#  @apiName GetLicense
#  @apiVersion 3.0
#
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/license
#
#@apiSampleRequest off
#**
# GET /system/license
sub get_license
{
	my $description = "Get license";
	my $licenseFile = &getGlobalConfiguration( 'licenseFile' );

	open ( my $license_fh, '<', "$licenseFile" );

	if ( $license_fh )
	{
		my $cgi = &getCGI();
		print $cgi->header(
							-type            => 'application/x-download',
							-attachment      => 'license',
							'Content-length' => -s "$licenseFile",
		);

		binmode $license_fh;
		print while <$license_fh>;
		close $license_fh;
		exit;
	}
	else
	{
		my $errormsg = "Don't find license.";
		my $body =
		  { description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 404, body => $body } );
	}
}

ntp:

#**
#  @api {get} /system/ntp Request ntp
#  @apiGroup SYSTEM
#  @apiDescription Get description of ntp
#  @apiName GetSnmp
#  @apiVersion 3.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Get snmp",
#   "params" : "pool.ntp.or"
#}
#
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/ntp
#
#@apiSampleRequest off
#**
# GET /system/ntp
sub get_ntp
{
	my $description = "Get snmp";
	my $ntp         = &getGlobalConfiguration( 'ntp' );

	&httpResponse(
			 { code => 200, body => { description => $description, params => $ntp } } );
}

#####Documentation of POST ntp####
#**
#  @api {post} /system/ntp Modify the ntp server settings
#  @apiGroup SYSTEM
#  @apiName PostSnmp
#  @apiDescription Modify ntp server settings
#  @apiVersion 3.0
#
#
#
# @apiSuccess	{string}		server		server where is allocated ntp service
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Post ntp",
#   "params" : "pool.ntp.org"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"status":"true", "port":"656"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/ntp
#
# @apiSampleRequest off
#
#**
#  POST /system/ntp
sub set_ntp
{
	my $json_obj    = shift;
	my $description = "Post ntp";
	my $errormsg;
	my @allowParams = ( "server" );

	$errormsg = &getValidOptParams( $json_obj, \@allowParams );
	if ( !$errormsg )
	{
		if ( !&getValidFormat( "ntp", $json_obj->{ $key } ) )
		{
			$errormsg = "NTP hasn't a correct format.";
		}
		else
		{
			$errormsg = &setGlobalConfiguration( 'ntp', $json_obj->{ 'server' } );

			if ( !$errormsg )
			{
				my $ntp = &getGlobalConfiguration( 'ntp' );
				&httpResponse(
						 { code => 200, body => { description => $description, params => $ntp } } );
			}
			else
			{
				$errormsg = "There was a error modifying ntp.";
			}
		}
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

notifications:

#**
#  @api {get} /system/notifications/methods/METHOD Request method info
#  @apiGroup SYSTEM
#  @apiDescription Get description of method to send notifications
#  @apiName GetNotificationsMethods
#  @apiParam {String} method  type of method to send notifications. Only email available.
#  @apiVersion 3.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Get notifications email methods",
#   "params" : {
#      "from" : "",
#      "method" : "email",
#      "password" : "******",
#      "server" : "smtp.foo.bar",
#      "tls" : "true",
#      "to" : "admin@mail.com",
#      "user" : "user@mail.com"
#   }
#}
#
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/notifications/methods/email
#
#@apiSampleRequest off
#**
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

#####Documentation of POST notification methods####
#**
#  @api {post} /system/notifications/methods/METHOD Modify the notification methods
#  @apiGroup SYSTEM
#  @apiName PostNotificationsMethods
#  @apiParam {String} method  type method to send notifications. Only email available.
#  @apiDescription Modify notification methods
#  @apiVersion 3.0
#
#
# @apiSuccess	{string}		server		SMTP server
# @apiSuccess	{string}		user			user for the SMTP server
# @apiSuccess	{string}		password		Password for the SMTP server
# @apiSuccess	{string}		from		origin email direction
# @apiSuccess	{string}		to				destine email direction
# @apiSuccess	{boolean}	tls			Define if TLS
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Set notifications email methods",
#   "params" : {
#      "password" : "password",
#      "server" : "smtp.foo.bar",
#      "tls" : "true",
#      "to" : "admin@mail.com",
#      "user" : "user@mail.com"
#   }
#}
#
#
# @apiExample {curl} Example Usage:
#		curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#		-d '{"tls":"true","server":"smtp.foo.bar","user":"user@mail.com", "password":"password", "to":"admin@mail.com"}'
#		https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/notifications/methods/email
#
# @apiSampleRequest off
#
#**
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

#**
#  @api {get} /system/notifications/alerts Request status of all alerts
#  @apiGroup SYSTEM
#  @apiDescription Get if alert status is enabled or disabled
#  @apiName GetNotificationsAlertsStatus
#  @apiVersion 3.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Get notifications alert status",
#   "params" : [
#      {
#         "alert" : "backends",
#         "status" : "enabled"
#      },
#      {
#         "alert" : "cluster",
#         "status" : "disabled"
#      }
#   ]
#}
#
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/notifications/alerts
#
#@apiSampleRequest off
#**
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

#**
#  @api {get} /system/notifications/alerts/ALERT Request alert info
#  @apiGroup SYSTEM
#  @apiDescription Get description of alert to send notifications
#  @apiName GetNotificationsAlerts
#  @apiParam {String} alert  type of alert to send notifications. Options are: backends or cluster
#  @apiVersion 3.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Get notifications alert backends settings",
#   "params" : {
#      "avoidFlappingTime" : "4",
#      "prefix" : "[Backend notifications]",
#      "status" : "enabled"
#   }
#}
#
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/notifications/alerts/backends
#
#@apiSampleRequest off
#**
# GET /system/notifications/alerts/ALERT
sub get_notif_alert
{
	my $alert       = shift;
	my $description = "Get notifications alert $alert settings";
	my $param       = &getNotifAlert( $alert );

	&httpResponse(
		   { code => 200, body => { description => $description, params => $param } } );
}

#####Documentation of POST notification alerts####
#**
#  @api {post} /system/notifications/alerts/ALERT Modify alert settings
#  @apiGroup SYSTEM
#  @apiName PostNotificationsAlerts
#  @apiParam {String} alert  type alert to configure. Value can be backends or cluster.
#  @apiDescription Modify alert settings
#  @apiVersion 3.0
#
#
#
# @apiSuccess	{number}	flapTime		During this time doesn't send notification if there are service flaps. Not available in cluster notifications
# @apiSuccess	{string}		prefix			Prefix to add to the mail subject
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Set notifications alert backends",
#   "params" : {
#      "flapTime" : 4,
#      "prefix" : "[Backend notifications]"
#   }
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#		  -d '{"flapTime":4,"prefix":"[Backend notifications]"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/notifications/alerts/backends
#
# @apiSampleRequest off
#
#**
#  POST /system/notifications/alerts/ALERT
sub set_notif_alert
{
	my $json_obj    = shift;
	my $alert       = shift;
	my $description = "Set notifications alert $alert";

	my @allowParams = ( "flapTime", "prefix" );
	my $errormsg = &getValidOptParams( $json_obj, \@allowParams );
	if ( !$errormsg )
	{
		if ( !&getValidFormat( 'notif_time', $json_obj->{ 'flapTime' } ) )
		{
			$errormsg = "Error, it's necessary add a valid action.";
		}
		elsif ( exists $json_obj->{ 'flapTime' } && $alert eq 'cluster' )
		{
			$errormsg = "Avoid flapping time is not configurable in cluster alerts.";
		}
		else
		{
			my $params;
			$params->{ 'PrefixSubject' } = $json_obj->{ 'prefix' }
			  if ( $json_obj->{ 'prefix' } );
			$params->{ 'SwitchTime' } = $json_obj->{ 'flapTime' }
			  if ( $json_obj->{ 'flapTime' } );
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

#####Documentation of POST notification alerts status####
#**
#  @api {post} /system/notifications/alerts/ALERT/action Modify alert status
#  @apiGroup SYSTEM
#  @apiName PostNotificationsAlertsActions
#  @apiParam {String} alert  type alert to configure. Value can be backends or cluster.
#  @apiDescription Modify alert status
#  @apiVersion 3.0
#
#
#
# @apiSuccess	{string}		action		Enable or disable this type of alert. Options: enable or disable
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Set notifications alert backends actions",
#   "params" : {
#      "action" : "enabled"
#   }
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#		  -d '{"action":"enabled"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/notifications/alerts/backends/actions
#
# @apiSampleRequest off
#
#**
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
				$errormsg = "$alert just is $json_obj->{action}.";
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

1;

