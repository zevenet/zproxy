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


use warnings;
use strict;


_dns:

#**
#  @api {get} /system/dns Request dns
#  @apiGroup SYSTEM
#  @apiDescription Get description of dns
#  @apiName GetDns
#  @apiVersion 3.0.0
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
#  @apiVersion 3.0.0
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

_ssh:

#**
#  @api {get} /system/ssh Request ssh
#  @apiGroup SYSTEM
#  @apiDescription Get description of ssh
#  @apiName GetSsh
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Get ssh",
#   "params" : {
#      "listen" : "*",
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
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess	{Number}	port		Port where listen ssh server.
# @apiSuccess	{string}		listen	IP where is listening the ssh server. Use '*' character to listen in all IPs
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
	my $sshIp = $json_obj->{ 'listen' } if ( exists $json_obj->{ 'listen' } );

	$errormsg = &getValidOptParams( $json_obj, \@allowParams );
	if ( !$errormsg )
	{
		if ( !&getValidFormat( "port", $json_obj->{ 'port' } ) )
		{
			$errormsg = "Port hasn't a correct format.";
		}
		else
		{
			# check if listen exists
			if ( exists $json_obj->{ 'listen' } && $json_obj->{ 'listen' } ne '*' )
			{
				my $flag;
				foreach my $iface ( @{ &getActiveInterfaceList() } )
				{
					if ( $sshIp eq $iface->{ addr } )
					{
						$flag = 1;
						if ( $iface->{ vini } ne '' )    # discard virtual interfaces
						{
							$errormsg = "Virtual interface canot be configurate as http interface.";
						}
						last;
					}
				}
				$errormsg = "Ip $json_obj->{ 'listen' } not found in system." if ( !$flag );
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
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

_snmp:

#**
#  @api {get} /system/snmp Request snmp
#  @apiGroup SYSTEM
#  @apiDescription Get description of snmp
#  @apiName GetSnmp
#  @apiVersion 3.0.0
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
	$snmp{ 'status' } = &getSnmpdStatus();
	
	
	&httpResponse(
		   { code => 200, body => { description => $description, params => \%snmp } } );
}

#####Documentation of POST snmp####
#**
#  @api {post} /system/snmp Modify the snmp server settings
#  @apiGroup SYSTEM
#  @apiName PostSnmp
#  @apiDescription Modify snmp server settings
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess	{string}		status		Enable or disable snmp service. The options are true or false.
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
		#~ # check if listen exists
		#~ if ( exists $json_obj->{ 'ip' } && $json_obj->{ 'ip' } ne '*'
				#~ && !$errormsg )
		#~ {
			#~ my $flag;
			#~ foreach my $iface ( @{ &getActiveInterfaceList() } )
			#~ {
				#~ if ( $json_obj->{ 'ip' } eq $iface->{ addr } )
				#~ {
					#~ $flag = 1;
					#~ if ( $iface->{ vini } ne '' )    # discard virtual interfaces
					#~ {
						#~ $errormsg = "Virtual interface canot be configurate as http interface.";
					#~ }
					#~ else
					#~ {
						#~ $interface = $iface;
					#~ }
					#~ last;
				#~ }
			#~ }
			#~ $errormsg = "Ip $json_obj->{ 'ip' } not found in system." if ( !$flag );
		#~ }
		
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

_license:
# DOWNLOAD
# GET /system/license
#~ sub get_license
#~ {
	#~ my $description = "Get license";
	#~ my $licenseFile = &getGlobalConfiguration( 'licenseFile' );
	#~ open ( my $license_fh, '<', "$licenseFile" );
	#~ if ( $license_fh )
	#~ {
		#~ my $cgi = &getCGI();
		#~ print $cgi->header(
							#~ -type            => 'application/x-download',
							#~ -attachment      => 'license',
							#~ 'Content-length' => -s "$licenseFile",
		#~ );
		#~ binmode $license_fh;
		#~ print while <$license_fh>;
		#~ close $license_fh;
		#~ exit;
	#~ }
	#~ else
	#~ {
		#~ my $errormsg = "Don't find license.";
		#~ my $body =
		  #~ { description => $description, error => "true", message => $errormsg };
		#~ &httpResponse( { code => 404, body => $body } );
	#~ }
#~ }

#**
#  @api {get} /system/license Request license
#  @apiGroup SYSTEM
#  @apiDescription Get license
#  @apiName GetLicense
#  @apiVersion 3.0.0
#
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/license
#
#@apiSampleRequest off
#**
# show license
sub get_license
{
	my $format = shift;
	my $description = "Get license";
	my $file;

	if ( $format eq 'txt' )
	{
		my $licenseFile = &getGlobalConfiguration( 'licenseFileTxt' );
		open ( my $license_fh, '<', "$licenseFile" );
		$file .= $_ while ( <$license_fh> );
		# Close this particular file.
		close $license_fh;
		&httpResponse({ code => 200, body => $file, type => 'text/plain' });
	}
	elsif ( $format eq 'html' )
	{
		my $licenseFile = &getGlobalConfiguration( 'licenseFileHtml' );
		open ( my $license_fh, '<', "$licenseFile" );
		$file .= $_ while ( <$license_fh> );
		# Close this particular file.
		close $license_fh;
		&httpResponse({ code => 200, body => $file, type => 'text/html' });
	}
	else
	{
		my $errormsg = "Not found license.";
		my $body =
		  { description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 404, body => $body } );
	}
}

_ntp:

#**
#  @api {get} /system/ntp Request ntp
#  @apiGroup SYSTEM
#  @apiDescription Get description of ntp
#  @apiName GetNtp
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Get ntp",
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
	my $description = "Get ntp";
	my $ntp         = &getGlobalConfiguration( 'ntp' );

	&httpResponse(
			 { code => 200, body => { description => $description, params => { "server" => $ntp } } } );
}

#####Documentation of POST ntp####
#**
#  @api {post} /system/ntp Modify the ntp server settings
#  @apiGroup SYSTEM
#  @apiName PostSnmp
#  @apiDescription Modify ntp server settings
#  @apiVersion 3.0.0
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
		if ( !&getValidFormat( "ntp", $json_obj->{ 'server' } ) )
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

_http:

#**
#  @api {get} /system/http Request http
#  @apiGroup SYSTEM
#  @apiDescription Get description of http
#  @apiName GetHttp
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Get http",
#   "params" : {
#      "interface" : {
#         "dev" : "eth0",
#         "ip" : "192.168.100.240"
#      },
#      "port" : "443"
#   }
#}
#
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/http
#
#@apiSampleRequest off
#**
# GET /system/http
sub get_http
{
	my $description       = "Get http";
	my $httpIp            = &getHttpServerIp();
	my $allInterfaces_aux = &getActiveInterfaceList();
	my @interfaces;
	my $interface;

	# add all interfaces
	push @interfaces, { 'dev' => '*', 'ip' => '*' };

	foreach my $iface ( @{ $allInterfaces_aux } )
	{
		push @interfaces, { 'dev' => $iface->{ 'dev' }, 'ip' => $iface->{ 'addr' } };
		if ( $iface->{ 'addr' } eq $httpIp )
		{
			$interface = { 'dev' => $iface->{ 'dev' }, 'ip' => $iface->{ 'addr' } };
		}
	}

	# http is enabled in all interfaces
	$interface = '*' if ( !$interface );

	my $http;
	$http->{ 'port' } = &getHttpServerPort;

	#~ $http->{ 'availableInterfaces' } = \@interfaces;
	$http->{ 'ip' } = $interface;

	&httpResponse(
			{ code => 200, body => { description => $description, params => $http } } );
}

#####Documentation of POST http####
#**
#  @api {post} /system/http Modify the parameters to connect with http server
#  @apiGroup SYSTEM
#  @apiName PostHttp
#  @apiDescription Modify http server settings
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess	{string}			ip			this ip has to exist in some interface. This interface can't be virtual. Set '*' character if you want to listen in all available interfaces
# @apiSuccess	{number}		port		port to connect with http service
#
#
#
# @apiSuccessExample Success-Response:
#{
#	"description" : "Post http",
#	"params" : {
#		"ip" : "192.168.6.32",
#		"port" : "444"
#	}
#}
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"ip":"192.168.6.32", "port":"444"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/http
#
# @apiSampleRequest off
#
#**
# POST /system/http
sub set_http
{
	my $json_obj    = shift;
	my $description = "Post http";
	my $errormsg;
	my @allowParams = ( "ip", "port" );
	my $httpIp = $json_obj->{ 'ip' } if ( exists $json_obj->{ 'ip' } );

	$errormsg = &getValidOptParams( $json_obj, \@allowParams );
	if ( !$errormsg )
	{
		if ( !&getValidFormat( "port", $json_obj->{ 'port' } ) )
		{
			$errormsg = "Port hasn't a correct format.";
		}
		else
		{
			if ( exists $json_obj->{ 'ip' } )
			{
				if ( $json_obj->{ 'ip' } ne '*' )
				{
					my $flag;
					foreach my $iface ( @{ &getActiveInterfaceList() } )
					{
						if ( $httpIp eq $iface->{ addr } )
						{
							$flag = 1;
							if ( $iface->{ vini } ne '' )    # discard virtual interfaces
							{
								$errormsg = "Virtual interface canot be configurate as http interface.";
							}
							last;
						}
					}
					$errormsg = "Ip not found in system." if ( !$flag );
				}
			}
			if ( !$errormsg )
			{
				&setHttpServerPort( $json_obj->{ 'port' } ) if ( exists $json_obj->{ 'port' } );
				&setHttpServerIp( $httpIp ) if ( exists $json_obj->{ 'ip' } );
				&httpResponse(
					{ code => 200, body => { description => $description, params => $json_obj } } );
			}
		}
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

_logs:
#**
#  @api {get} /system/backup Request existent backups
#  @apiGroup SYSTEM
#  @apiDescription Get existent backups
#  @apiName GetBackup
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Get backups",
#   "params" : [
#      {
#         "date" : "Fri Nov 18 11:24:13 2016",
#         "file" : "back_2"
#      },
#      {
#         "date" : "Fri Nov 18 12:40:06 2016",
#         "file" : "back_1"
#      },
#      {
#         "date" : "Thu Nov 17 18:14:47 2016",
#         "file" : "first_conf"
#      }
#   ]
#}
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/backup
#
#@apiSampleRequest off
#**
#	GET	/system/backup
sub get_logs
{
	my $description = "Get logs";
	my $backups = &getLogs;

	&httpResponse(
		 { code => 200, body => { description => $description, params => $backups } } );
}

#**
#  @api {get} /system/logs/LOG 	Dowload a log file
#  @apiGroup SYSTEM
#  @apiDescription Download a log file
#  @apiParam {String} log  file to download
#  @apiName GetLogsDownload
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{{TODO}}
#
#@apiExample {curl} Example Usage:
#	curl -o <PATH/FILE.tar.gz> --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/logs/LOG
#
#@apiSampleRequest off
#**
#	GET	/system/logs/LOG
sub download_logs
{
	my $logFile      = shift;
	my $description = "Download a log file";
	my $errormsg    = "$logFile was download successful.";
	my $logPath = &getGlobalConfiguration( 'logdir') . "/$logFile";

	if ( ! -f $logPath )
	{
		$errormsg = "Not found $logFile file.";
		my $body =
		  { description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 404, body => $body } );
	}
	else
	{
# Download function ends communication if itself finishes successful. It is not necessary send "200 OK" msg
		$errormsg = &downloadLog( $logFile );
		if ( $errormsg )
		{
			$errormsg = "Error, downloading backup.";
		}
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 404, body => $body } );
}

_users:

#**
#  @api {get} /system/users Request existent users
#  @apiGroup SYSTEM
#  @apiDescription Get existent users
#  @apiName GetUsers
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Get users",
#   "params" : [
#      {
#         "status" : "true",
#         "user" : "root"
#      },
#      {
#         "status" : "true",
#         "user" : "zapi"
#      }
#   ]
#}
#
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/users
#
#@apiSampleRequest off
#**
#	GET	/system/users
sub get_all_users
{
	my $description = "Get users";
	my $zapiStatus = &getZAPI( "status", "" );
	my @users = ( { "user"=>"root", "status"=>"true" }, { "user"=>"zapi","status"=>"$zapiStatus" } );
	
	&httpResponse(
		  { code => 200, body => { description => $description, params => \@users } } );
}

#**
#  @api {get} /system/users/zapi		Request zapi settings
#  @apiGroup SYSTEM
#  @apiDescription Get the zapi settings
#  @apiName GetUsersZapi
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Zapi user configuration.",
#   "params" : {
#      "key" : "root",
#      "status" : "true"
#   }
#}
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/users/zapi
#
#@apiSampleRequest off
#**
#	GET	/system/users/zapi
sub get_user
{
	my $user        = shift;
	my $description = "Zapi user configuration.";
	my $errormsg;

	if ( $user ne 'zapi' )
	{
		$errormsg = "Actually only is available information about 'zapi' user";
	}
	else
	{
		my $zapi->{ 'key' } = &getZAPI( "keyzapi", "" );
		$zapi->{ 'status' } = &getZAPI( "status", "" );
		&httpResponse(
				{ code => 200, body => { description => $description, params => $zapi } } );
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 404, body => $body } );
}

#####Documentation of POST zapi configuration####
#**
#  @api {post} /system/users/zapi Modify the zapi parameters
#  @apiGroup SYSTEM
#  @apiName PostUsersZapi
#  @apiDescription Modify zapi settings
#  @apiVersion 3.0.0
#
#
# @apiSuccess	{string}			key			key to connect with zapi
# @apiSuccess	{string}			newpassword			new password for the zapi user
# @apiSuccess	{string}			status			enable or disable the zapi. The options are: enable or disable
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Zapi user settings.",
#   "message" : "Settings was changed successful.",
#   "params" : {
#      "key" : "yPh2vM20SyQudI9azEuPoHVB3lt35FqSTLSdDC7hYB98fIUH44GIQaurQeYoI8y6j",
#      "newpassword" : "brla23v",
#      "status" : "enable"
#   }
#}
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#         -d '{"key":"randomkey","newpassword":"brla23v","status":"enable"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/users/zapi
#
# @apiSampleRequest off
#
#**
# POST /system/users/zapi
sub set_user_zapi
{
	my $json_obj    = shift;
	my $description = "Zapi user settings.";

	#~ my @requiredParams = ( "key", "status", "password", "newpassword" );
	my @requiredParams = ( "key", "status", "newpassword" );
	my $errormsg;

	$errormsg = &getValidOptParams( $json_obj, \@requiredParams );
	if ( !$errormsg )
	{
		if ( !&getValidFormat( "zapi_key", $json_obj->{ 'key' } ) )
		{ 
			$errormsg = "Error, character incorrect in key zapi.";
		}
		elsif ( !&getValidFormat( "zapi_password", $json_obj->{ 'newpassword' } ) )
		{
			$errormsg = "Error, character incorrect in password zapi.";
		}
		elsif ( !&getValidFormat( "zapi_status", $json_obj->{ 'status' } ) )
		{
			$errormsg = "Error, character incorrect in status zapi.";
		}
		else
		{
			if (    $json_obj->{ 'status' } eq 'enable'
				 && &getZAPI( "status", "" ) eq 'false' )
			{
				&setZAPI( "enable" );
			}
			elsif (    $json_obj->{ 'status' } eq 'disable'
					&& &getZAPI( "status", "" ) eq 'true' )
			{
				&setZAPI( "disable" );
			}
			if ( exists $json_obj->{ 'key' } )
			{
				&setZAPI( 'key', $json_obj->{ 'key' } );
			}

			&changePassword( 'zapi',
							 $json_obj->{ 'newpassword' },
							 $json_obj->{ 'newpassword' } )
			  if ( exists $json_obj->{ 'newpassword' } );

			$errormsg = "Settings was changed successful.";
			&httpResponse(
				 {
				   code => 200,
				   body =>
					 { description => $description, params => $json_obj, message => $errormsg }
				 }
			);
		}
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

#####Documentation of POST user configuration####
#**
#  @api {post} /system/users/zapi Modify the user password
#  @apiGroup SYSTEM
#  @apiName PostUsersZapi
#  @apiDescription Modify user password
#  @apiVersion 3.0.0
#
#
# @apiSuccess	{string}			newpassword		new password for the user
# @apiSuccess	{string}			password				current password for the user
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "User settings.",
#   "message" : "Settings was changed succesful.",
#   "params" : {
#      "newpassword" : "passwd12e",
#      "password" : "admin"
#   }
#}
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#         -d '{"newpassword" : "passwd12e", "password" : "admin"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/users/root
#
# @apiSampleRequest off
#
#**
# POST /system/users/root
sub set_user
{
	my $json_obj       = shift;
	my $user           = shift;
	my $description    = "User settings.";
	my @requiredParams = ( "password", "newpassword" );
	my $errormsg;

	$errormsg = &getValidReqParams( $json_obj, \@requiredParams, \@requiredParams );
	if ( !$errormsg )
	{
		if ( $user ne 'root' )
		{
			$errormsg =
			  "Error, actually only is available to change password in root user.";
		}
		else
		{
			if ( !&getValidFormat( 'password', $json_obj->{ 'newpassword' } ) )
			{
				$errormsg = "Error, character incorrect in password.";
			}
			elsif ( !&checkValidUser( $user, $json_obj->{ 'password' } ) )
			{
				$errormsg = "Error, invalid current password.";
			}
			else
			{
				$errormsg = &changePassword( $user,
											 $json_obj->{ 'newpassword' },
											 $json_obj->{ 'newpassword' } );
				if ( $errormsg )
				{
					$errormsg = "Error, changing $user password.";
				}
				else
				{
					$errormsg = "Settings was changed succesful.";
					&httpResponse(
						 {
						   code => 200,
						   body =>
							 { description => $description, params => $json_obj, message => $errormsg }
						 }
					);
				}
			}
		}
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

_backup:

#**
#  @api {get} /system/backup Request existent backups
#  @apiGroup SYSTEM
#  @apiDescription Get existent backups
#  @apiName GetBackup
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Get backups",
#   "params" : [
#      {
#         "date" : "Fri Nov 18 11:24:13 2016",
#         "file" : "back_2"
#      },
#      {
#         "date" : "Fri Nov 18 12:40:06 2016",
#         "file" : "back_1"
#      },
#      {
#         "date" : "Thu Nov 17 18:14:47 2016",
#         "file" : "first_conf"
#      }
#   ]
#}
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/backup
#
#@apiSampleRequest off
#**
#	GET	/system/backup
sub get_backup
{
	my $description = "Get backups";

	my $backups = &getBackup;

	&httpResponse(
		 { code => 200, body => { description => $description, params => $backups } } );
}

#####Documentation of POST backup####
#**
#  @api {post} /system/backup Create a backup of configuration files
#  @apiGroup SYSTEM
#  @apiName PostBackup
#  @apiDescription Create a backup of configuration files
#  @apiVersion 3.0.0
#
#
# @apiSuccess	{string}			name			name for backup
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Create a backups",
#   "message" : "Backup zen_bak was created successful.",
#   "params" : "zen_bak"
#}
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"name":"zen_bak"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/backup
#
# @apiSampleRequest off
#
#**
#	POST  /system/backup
sub create_backup
{
	my $json_obj       = shift;
	my $description    = "Create a backups";
	my @requiredParams = ( "name" );
	my $errormsg;

	$errormsg = getValidReqParams( $json_obj, \@requiredParams );
	if ( &getExistsBackup( $json_obj->{ 'name' } ) )
	{
		$errormsg = "A backup just exists with this name.";
	}
	elsif ( !&getValidFormat( 'backup', $json_obj->{ 'name' } ) )
	{
		$errormsg = "The backup name has invalid characters.";
	}
	else
	{
		$errormsg = &createBackup( $json_obj->{ 'name' } );
		if ( !$errormsg )
		{
			$errormsg = "Backup $json_obj->{ 'name' } was created successful.";
			my $body = {
						 description => $description,
						 params      => $json_obj->{ 'name' },
						 message     => $errormsg
			};
			&httpResponse( { code => 200, body => $body } );
		}
		else
		{
			$errormsg = "Error creating backup.";
		}
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

#**
#  @api {get} /system/backup/BACKUP Download a backup
#  @apiGroup SYSTEM
#  @apiDescription Download a backup
#  @apiName GetBackupDownload
#  @apiParam {String} backup  Backup name to download
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{{TODO}}
#
#@apiExample {curl} Example Usage:
#	curl -o <PATH/FILE.tar.gz> --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/backup/BACKUP
#
#@apiSampleRequest off
#**
#	GET	/system/backup/BACKUP
sub download_backup
{
	my $backup      = shift;
	my $description = "Download a backup";
	my $errormsg    = "$backup was download successful.";

	if ( !&getExistsBackup( $backup ) )
	{
		$errormsg = "Not found $backup backup.";
		my $body =
		  { description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 404, body => $body } );
	}
	else
	{
# Download function ends communication if itself finishes successful. It is not necessary send "200 OK" msg
		$errormsg = &downloadBackup( $backup );
		if ( $errormsg )
		{
			$errormsg = "Error, downloading backup.";
		}
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 404, body => $body } );
}

#####Documentation of PUT snmp####
#**
#  @api {post} /system/backup/BACKUP Upload a zen backup
#  @apiGroup SYSTEM
#  @apiName PutBackup
#  @apiDescription Upload a backup
#  @apiParam {String} backup  Name to save the backup
#  @apiVersion 3.0.0
#
#
# @apiSuccess	{string}		data-binary 	backup file to upload
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Upload a backup",
#   "message" : "Backup backup_1 was created successful.",
#   "params" : "backup_1"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: text/plain' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        --data-binary @/opt/backup.tar.gz https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/backup/BACKUP
#
# @apiSampleRequest off
#
#**
# curl -kis -X PUT -H "ZAPI_KEY: 2bJUd" --tcp-nodelay -H 'Content-Type: text/gzip' https://192.168.101.20:444/zapi/v3/zapi.cgi/system/backup/backup_1 --data-binary @/opt/backup.tar.gz
#	PUT	/system/backup/BACKUP
sub upload_backup
{
	my $upload_filehandle = shift;
	my $name              = shift;

	my $description = "Upload a backup";
	my $errormsg;

	if ( !$upload_filehandle || !$name )
	{
		$errormsg = "It's necessary add a data binary file.";
	}
	elsif ( &getExistsBackup( $name ) )
	{
		$errormsg = "Backup just exists with this name.";
	}
	elsif ( !&getValidFormat( 'backup', $name ) )
	{
		$errormsg = "The backup name has invalid characters.";
	}
	else
	{
		$errormsg = &uploadBackup( $name, $upload_filehandle );
		if ( !$errormsg )
		{
			$errormsg = "Backup $name was created successful.";
			my $body =
			  { description => $description, params => $name, message => $errormsg };
			&httpResponse( { code => 200, body => $body } );
		}
		else
		{
			$errormsg = "Error creating backup.";
		}
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

#####Documentation of DELETE a backup####
#**
#  @api {delete} /system/backup/BACKUP	Delete a backup from zen balancer
#  @apiGroup SYSTEM
#  @apiName DeleteBackup
#  @apiParam	{String}	Backup	Backup name
#  @apiDescription Delete a backup from balancer
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Delete backup backup_1'",
#   "message" : "The list backup_1 has been deleted successful.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/backup/BACKUP
#
# @apiSampleRequest off
#
#**
#	DELETE /system/backup/BACKUP
sub del_backup
{
	my $backup = shift;
	my $errormsg;
	my $description = "Delete backup $backup'";

	if ( !&getExistsBackup( $backup ) )
	{
		$errormsg = "$backup doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}
	else
	{
		$errormsg = &deleteBackup( $backup );
		if ( !$errormsg )
		{
			$errormsg = "The list $backup has been deleted successful.";
			my $body = {
						 description => $description,
						 success     => "true",
						 message     => $errormsg,
			};
			&httpResponse( { code => 200, body => $body } );
		}
		else
		{
			$errormsg = "There was a error deleting list $backup.";
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg,
	};
	&httpResponse( { code => 400, body => $body } );
}

#####Documentation of POST apply a backup to the system####
#**
#  @api {post} /system/backup/BACKUP/action Apply a backup to the system
#  @apiGroup SYSTEM
#  @apiName PostBackupAction
#  @apiParam {String} backup  Backup name to apply to system
#  @apiDescription Apply a backup to the system
#  @apiVersion 3.0.0
#
#
# @apiSuccess	{string}		action		The action param only has the option: apply.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Apply a backup to the system",
#   "params" : {
#      "action" : "apply"
#   }
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#		  -d '{"action":"apply"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/backup/BACKUP/action
#
# @apiSampleRequest off
#
#**
#	POST /system/backup/BACKUP/actions
sub apply_backup
{
	my $json_obj    = shift;
	my $backup      = shift;
	my $description = "Apply a backup to the system";

	my @allowParams = ( "action" );
	my $errormsg = &getValidOptParams( $json_obj, \@allowParams );
	if ( !$errormsg )
	{
		if ( !&getExistsBackup( $backup ) )
		{
			$errormsg = "Not found $backup backup.";
			my $body =
			  { description => $description, error => "true", message => $errormsg };
			&httpResponse( { code => 404, body => $body } );
		}
		elsif ( !&getValidFormat( 'backup_action', $json_obj->{ 'action' } ) )
		{
			$errormsg = "Error, it's necessary add a valid action";
		}
		else
		{
			$errormsg = &applyBackup( $backup );
			if ( !$errormsg )
			{
				&httpResponse(
					{ code => 200, body => { description => $description, params => $json_obj } } );
			}
			else
			{
				$errormsg = "There was a error applying the backup.";
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

_notifications:

#**
#  @api {get} /system/notifications/methods/METHOD Request method info
#  @apiGroup SYSTEM
#  @apiDescription Get description of method to send notifications
#  @apiName GetNotificationsMethods
#  @apiParam {String} method  type of method to send notifications. Only email available.
#  @apiVersion 3.0.0
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
#  @apiDescription Modify notification methods. Remember enable mail sends from less secure applications if it is necessary
#  @apiVersion 3.0.0
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
#  @apiVersion 3.0.0
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
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Get notifications alert backends settings",
#   "params" : {
#      "avoidflappingtime" : "4",
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
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess	{number}	avoidflappingtime		During this time doesn't send notification if there are service flaps. Not available in cluster notifications
# @apiSuccess	{string}		prefix			Prefix to add to the mail subject
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Set notifications alert backends",
#   "params" : {
#      "avoidflappingtime" : 4,
#      "prefix" : "[Backend notifications]"
#   }
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#		  -d '{"avoidflappingtime":4,"prefix":"[Backend notifications]"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/system/notifications/alerts/backends
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
			  if ( $json_obj->{ 'prefix' } );
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

#####Documentation of POST notification alerts status####
#**
#  @api {post} /system/notifications/alerts/ALERT/action Modify alert status
#  @apiGroup SYSTEM
#  @apiName PostNotificationsAlertsActions
#  @apiParam {String} alert  type alert to configure. Value can be backends or cluster.
#  @apiDescription Modify alert status
#  @apiVersion 3.0.0
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
#      "action" : "enable"
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
				$errormsg = "Test mail sended successful.";
				&httpResponse(
					{ code => 200, body => { description => $description, success => "true", message => $errormsg } } );
			}
			else
			{
				$errormsg = "Test mail sended but it hasn't reached the destination.";
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
	
}



sub get_supportsave
{
	my $description = "Get supportsave file";
	my @ss_output = `/usr/local/zenloadbalancer/app/zbin/supportsave 2>&1`;

	# get the last "word" from the first line
	my $first_line = shift @ss_output;
	my $last_word = ( split ( ' ', $first_line ) )[-1];

	my $ss_path = $last_word;
	my ( undef, $ss_filename ) = split ( '/tmp', $ss_path );

	open ( my $ss_fh, '<', $ss_path );

	if ( -f $ss_path && $ss_fh )
	{
		my $cgi = &getCGI();
		print $cgi->header(
							-type            => 'application/x-download',
							-attachment      => $ss_filename,
							'Content-length' => -s $ss_path,
		);

		binmode $ss_fh;
		print while <$ss_fh>;
		close $ss_fh;
		unlink $ss_path;
		exit;
	}
	else
	{
		# Error
		my $errormsg = "Error getting a supportsave file";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 400, body => $body } );
	}
}


# GET /system/version
sub get_version
{
	my $description = "Get version";
	
	my $hostnameBin = &getGlobalConfiguration( 'hostname' );
	my $uname = &getGlobalConfiguration( 'uname' );
	
	my $zevenet		= &getGlobalConfiguration( 'version' );
	my $kernel			= `$uname -r`;
	chop $kernel;
	my $hostname  	= `$hostnameBin`;
	chop $hostname;

	&httpResponse(
		{ 	code => 200, body => { description => $description, 
				params => { 
					'kernel_version' => $kernel, 
					'zevenet_version' => $zevenet, 
					'hostname' => $hostname,  
				} } 
		}
	);
}




1;
