###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, based in Sevilla (Spain)
#
#     This library is free software; you can redistribute it and/or modify it
#     under the terms of the GNU Lesser General Public License as published
#     by the Free Software Foundation; either version 2.1 of the License, or
#     (at your option) any later version.
#
#     This library is distributed in the hope that it will be useful, but
#     WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
#     General Public License for more details.
#
#     You should have received a copy of the GNU Lesser General Public License
#     along with this library; if not, write to the Free Software Foundation,
#     Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
###############################################################################

### CONTROLLER HTTP/HTTPS FARM ###

#maintenance mode for servers
$actualservice = $service;

#Edit Global Parameters
if ( $action eq "editfarm-Parameters" )
{
	#Actual Parameters
	my $type                  = &getFarmType( $farmname );
	my $actualconnto          = &getFarmConnTO( $farmname );
	my $actualtimeout         = &getFarmTimeout( $farmname );
	my $actualalive           = &getFarmBlacklistTime( $farmname );
	my $actualhttpverb        = &getFarmHttpVerb( $farmname );
	my $actualclient          = &getFarmClientTimeout( $farmname );
	my $actualrewritelocation = &getFarmRewriteL( $farmname );
	my $actualciphers         = &getFarmCipherSet( $farmname );
	my $actualcipherc         = &getFarmCipherList( $farmname );
	chomp ( $actualciphers );
	my $actualvip   = &getFarmVip( "vip",  $farmname );
	my $actualvport = &getFarmVip( "vipp", $farmname );
	my @err414 = &getFarmErr( $farmname, "414" );
	my $actualerr414 = join ( "", @err414 );
	my @err500 = &getFarmErr( $farmname, "500" );
	my $actualerr500 = join ( "", @err500 );
	my @err501 = &getFarmErr( $farmname, "501" );
	my $actualerr501 = join ( "", @err501 );
	my @err503 = &getFarmErr( $farmname, "503" );
	my $actualerr503 = join ( "", @err503 );

	#change Farm's name
	if ( $farmname ne $newfarmname )
	{
		#Check if farmname has correct characters (letters, numbers and hyphens)
		#Check the farm's name change
		if ( &checkFarmnameOK( $newfarmname ) != 0 )
		{
			&errormsg(
					   "Farm name is not valid, only allowed numbers, letters and hyphens" );
		}

		#Check if the new farm's name alredy exists
		elsif ( &getFarmFile( $newfarmname ) != -1 )
		{
			&errormsg( "The farm $newfarmname already exists, try another name" );
		}
		else    # the new farm name is valid
		{
			# check if farm is running once for all controller
			my $farm_status = &getFarmStatus( $farmname );

			#Stop farm
			if ( $farm_status eq 'up' )
			{
				#Stop farm
				if ( &runFarmStop( $farmname, "true" ) == 0 )
				{
					&successmsg( "The Farm $farmname is now disabled" );
				}
			}

			#Change farm name in configuration file
			$fnchange = &setNewFarmName( $farmname, $newfarmname );

			# handle farm rename errors
			if ( $fnchange == -1 )
			{
				&errormsg(
					"The name of the Farm $farmname can't be modified, delete the farm and create a new one."
				);
			}
			elsif ( $fnchange == -2 )
			{
				&errormsg(
					 "The name of the Farm $farmname can't be modified, the new name can't be empty"
				);

				if ( $farm_status eq 'up' )
				{
					if ( &runFarmStart( $farmname, "true" ) == 0 )
					{
						&successmsg( "The Farm $farmname is now running" );
					}
					else
					{
						&errormsg(
							"The Farm $farmname isn't running, check if the IP address is up and the PORT is in use"
						);
					}
				}
			}
			else
			{
				&successmsg( "The Farm $farmname has been just renamed to $newfarmname" );
				$farmname = $newfarmname;

				if ( $farm_status eq 'up' )
				{
					#Start farm
					&runFarmStart( $farmname, "true" );
					{
						&successmsg( "The Farm $farmname is now running" );
					}
				}
			}
		}
		$action = "editfarm";
	}

	#change Vip and Vport
	if ( $actualvip ne $vip or $actualvport ne $vipp )
	{
		if ( &isnumber( $vipp ) eq 'false' || &isValidPortNumber( $vipp ) eq 'false' )
		{
			&errormsg( "Invalid Virtual Port value" );
			$error = 1;
		}
		if ( &checkport( $vip, $vipp ) eq 'true' )
		{
			&errormsg(
					   "Virtual Port $vipp in Virtual IP $vip is in use, select another port" );
			$error = 1;
		}
		if ( $error == 0 )
		{
			$status = &setFarmVirtualConf( $vip, $vipp, $farmname );
			if ( $status != -1 )
			{
				&setFarmRestart( $farmname );
				&successmsg(
					"Virtual IP and Virtual Port has been modified, the $farmname farm need be restarted"
				);
			}
			else
			{
				&errormsg(
						   "It's not possible to change the $farmname farm virtual IP and port" );
			}
		}
	}

	#Backend connection time out
	if ( $conntout ne $actualconnto )
	{
		$error = 0;
		if ( &isnumber( $conntout ) eq "false" )
		{
			&errormsg( "Invalid timeout $conntout value, it must be a numeric value" );
			$error = 1;
		}
		if ( $error == 0 )
		{
			$status = &setFarmConnTO( $conntout, $farmname );
			if ( $status != -1 )
			{
				&setFarmRestart( $farmname );
				&successmsg( "The timeout for $farmname farm has been modified" );
			}
			else
			{
				&errormsg( "It's not possible to change the $farmname farm timeout value" );
			}
		}
	}

	#Backend response timeout
	if ( $actualtimeout ne $resptout )
	{
		$error = 0;
		if ( &isnumber( $resptout ) eq "false" )
		{
			&errormsg( "Invalid timeout $resptout value, it must be a numeric value" );
			$error = 1;
		}
		if ( $error == 0 )
		{
			$status = &setFarmTimeout( $resptout, $farmname );
			if ( $status != -1 )
			{
				&setFarmRestart( $farmname );
				&successmsg( "The timeout for $farmname farm has been modified" );
			}
			else
			{
				&errormsg( "It's not possible to change the $farmname farm timeout value" );
			}
		}
	}

	#Frequency to check resurrected backends
	if ( $actualalive ne $checkalive )
	{
		$error = 0;
		if ( &isnumber( $checkalive ) eq "false" )
		{
			&errormsg( "Invalid alive time $checkalive value, it must be a numeric value" );
			$error = 1;
		}
		if ( $error == 0 )
		{
			$status = &setFarmBlacklistTime( $checkalive, $farmname );
			if ( $status != -1 )
			{
				&setFarmRestart( $farmname );
				&successmsg( "The alive time for $farmname farm has been modified" );
			}
			else
			{
				&errormsg( "It's not possible to change the $farmname farm alive time value" );
			}
		}
	}

	#Http verb
	if ( $actualhttpverb ne $httpverb )
	{
		$status = &setFarmHttpVerb( $httpverb, $farmname );
		if ( $status == 0 )
		{
			&setFarmRestart( $farmname );
			&successmsg( "The HTTP verb for $farmname farm has been modified" );
		}
		else
		{
			&errormsg( "It's not possible to change the $farmname farm HTTP verb" );
		}
	}

	#Client timeout
	if ( $actualclient ne $clienttout )
	{
		$error = 0;
		if ( &isnumber( $clienttout ) eq "false" )
		{
			&errormsg(
					   "Invalid client timeout $clienttout value, it must be a numeric value" );
			$error = 1;
		}
		if ( $error == 0 )
		{
			$status = &setFarmClientTimeout( $clienttout, $farmname );
			if ( $status == 0 )
			{
				&setFarmRestart( $farmname );
				&successmsg( "The client timeout for $farmname farm has been modified" );
			}
			else
			{
				&errormsg( "It's not possible to change the $farmname farm client timeout" );
			}
		}
	}

	#Rewrite location headers
	if ( $actualrewritelocation ne $rewritelocation )
	{
		&setFarmRewriteL( $farmname, $rewritelocation );
		&successmsg( "Rewrite Location modified for farm $farmname" );
		&setFarmRestart( $farmname );
	}

	#Farm listener
	if ( $type ne $farmlisten )
	{
		&warnmsg( "SSL Diffie Hellman 2048 keys are being generated, it might take some minutes ... <a href=\"https://www.zenloadbalancer.com/knowledge-base/misc/diffie-hellman-keys-generation-important/\" target=\"_blank\">Why is it important?</a>" ) if $farmlisten eq "https";
		&setFarmListen( $farmname, $farmlisten );
		&successmsg( "HTTP listener modified" );
		&setFarmRestart( $farmname );
	}

	#HTTPS Parameters
	if ( $type eq "https" && $farmlisten eq "https" )
	{
		#Solves a problem when farm listener is switched to https
		#Manage ciphers

		# if cipher set changed
		if ( $ciphers ne $actualciphers )
		{
			&setFarmCipherList( $farmname, $ciphers );

			&successmsg( "Ciphers changed for farm $farmname" );
			&setFarmRestart( $farmname );
			$cipherc = &getFarmCipherList();
		}

		# if cipher set did not change
		elsif ( $ciphers eq 'ciphercustom' )
		{
			if ( $actualcipherc ne $cipherc )
			{
				if ( $cipherc eq "" )
				{
					&errormsg( "There must be ciphers" );
				}
				else
				{
					&setFarmCipherList( $farmname, $ciphers, $cipherc );
					&successmsg( "Ciphers customized for farm $farmname" );
					&setFarmRestart( $farmname );
				}
			}
		}
	}

	#err414
	chomp ( $actualerr414 );
	chomp ( $err414 );
	if ( $actualerr414 ne $err414 )
	{
		$status = &setFarmErr( $farmname, $err414, "414" );
		if ( $status == 0 )
		{
			&setFarmRestart( $farmname );
			&successmsg( "The Err414 message for the $farmname farm has been modified" );
		}
		else
		{
			&errormsg( "The Err414 message for the $farmname farm hasn't been modified" );
		}
	}

	#err500
	chomp ( $actualerr500 );
	chomp ( $err500 );
	if ( $actualerr500 ne $err500 )
	{
		$status = &setFarmErr( $farmname, $err500, "500" );
		if ( $status == 0 )
		{
			&setFarmRestart( $farmname );
			&successmsg( "The Err500 message for the $farmname farm has been modified" );
		}
		else
		{
			&errormsg( "The Err500 message for the $farmname farm hasn't been modified" );
		}
	}

	#err501
	chomp ( $actualerr501 );
	chomp ( $err501 );
	if ( $actualerr501 ne $err501 )
	{
		$status = &setFarmErr( $farmname, $err501, "501" );
		if ( $status == 0 )
		{
			&setFarmRestart( $farmname );
			&successmsg( "The Err501 message for the $farmname farm has been modified" );
		}
		else
		{
			&errormsg( "The Err501 message for the $farmname farm hasn't been modified" );
		}
	}

	#err503
	chomp ( $actualerr503 );
	chomp ( $err503 );
	if ( $actualerr503 ne $err503 )
	{
		$status = &setFarmErr( $farmname, $err503, "503" );
		if ( $status == 0 )
		{
			&setFarmRestart( $farmname );
			&successmsg( "The Err503 message for the $farmname farm has been modified" );
		}
		else
		{
			&errormsg( "The Err503 message for the $farmname farm hasn't been modified" );
		}
	}
}

#Manage Certificate of SNI List

#Add a certificate to SNI List
if ( $action eq "editfarm-httpscert" )
{
	$status = &setFarmCertificateSNI( $certname, $farmname );
	if ( $status == 0 )
	{
		&setFarmRestart( $farmname );
		&successmsg(
			"Certificate is changed to $certname on farm $farmname, you need restart the farm to apply"
		);
	}
	else
	{
		&errormsg(
			"It's not possible to add the certificate with name $certname for the $farmname farm"
		);
	}
}

#Delete a certificate of SNI List
if ( $action eq "editfarm-deletecert" )
{
	$status = &setFarmDeleteCertSNI( $certname, $farmname );
	if ( $status == 0 )
	{
		&successmsg(
				  "The selected certificate $certname has been deleted from the SNI list" );
		&setFarmRestart( $farmname );
	}
	else
	{
		if ( $status == -1 )
		{
			&errormsg(
				"It isn't possible to delete the selected certificate $certname from the SNI list"
			);
		}
		if ( $status == 1 )
		{
			&errormsg(
				"It isn't possible to delete all certificates, at least one is required for HTTPS profiles"
			);
		}
	}
}

#Service's parameters
if ( $action eq "editfarm-Service" )
{
	# Service configuration file parameters
	my $actualdyns          = &getFarmVS( $farmname, $service, "dynscale" );
	my $actualcookiei       = &getFarmVS( $farmname, $service, "cookieins" );
	my $actualcookieinsname = &getFarmVS( $farmname, $service, "cookieins-name" );
	my $actualdomainname    = &getFarmVS( $farmname, $service, "cookieins-domain" );
	my $actualpath          = &getFarmVS( $farmname, $service, "cookieins-path" );
	my $actualttlc          = &getFarmVS( $farmname, $service, "cookieins-ttlc" );
	my $actualhttpsb        = &getFarmVS( $farmname, $service, "httpsbackend" );
	my $actualredirect      = &getFarmVS( $farmname, $service, "redirect" );
	my $actualredirecttype  = &getFarmVS( $farmname, $service, "redirecttype" );
	my $actualurlp          = &getFarmVS( $farmname, $service, "urlp" );
	my $actualvser          = &getFarmVS( $farmname, $service, "vs" );
	my $actualttl           = &getFarmVS( $farmname, $service, "ttl" );
	my $actualsessionid     = &getFarmVS( $farmname, $service, "sessionid" );
	my $actualsession       = &getFarmVS( $farmname, $service, "sesstype" );

	$actualsession = 'nothing' if ( $actualsession =~ /^$/ );

	# Farmgrardian parameters for service
	my @actualfgconfig  = &getFarmGuardianConf( $farmname, $service );
	my $actualfgttcheck = $actualfgconfig[1];
	my $actualfgscript  = $actualfgconfig[2];
	my $actualfguse     = $actualfgconfig[3];
	my $actualfglog     = $actualfgconfig[4];

	# Clean farmguardian strings
	$actualfgscript =~ s/\n//g;
	$actualfgscript =~ s/\"/\'/g;
	$actualfguse =~ s/\n//g;

	#Least response
	if ( $actualdyns eq "true" and !defined ( $dynscale )
		 or defined ( $dynscale ) and $actualdyns eq "" )
	{
		if ( defined ( $dynscale ) )
		{
			$dynscale = "true";
		}
		else
		{
			$dynscale = "";
		}
		&setFarmVS( $farmname, $service, "dynscale", $dynscale );
		&successmsg( "Least response is modified for farm $farmname" );
		&setFarmRestart( $farmname );
	}

	#Cookie insertion
	if ( $actualcookiei eq "true" and !defined ( $cookieins )
		 or defined ( $cookieins ) and $actualcookiei eq "" )
	{
		if ( defined ( $cookieins ) )
		{
			$cookieins = "true";
		}
		else
		{
			$cookieins = "";
		}
		&setFarmVS( $farmname, $service, "cookieins", $cookieins );
		&successmsg( "Cookie insertion has been enabled for service $service" );
		&setFarmRestart( $farmname );
	}

	#Cookie insertion values
	if (    $actualcookieinsname ne $cookieinsname
		 or $actualdomainname ne $domainname
		 or $actualpath ne $path
		 or $actualttlc ne $ttlc )
	{
		&setFarmVS( $farmname, $service, "cookieins-name",   $cookieinsname );
		&setFarmVS( $farmname, $service, "cookieins-domain", $domainname );
		&setFarmVS( $farmname, $service, "cookieins-path",   $path );
		&setFarmVS( $farmname, $service, "cookieins-ttlc",   $ttlc );
		&successmsg(
					 "Cookie insertion definition has been modified for service $service" );
		&setFarmRestart( $farmname );
	}

	#HTTPS Backends
	if ( $actualhttpsb eq "true" and !defined ( $httpsbackend )
		 or defined ( $httpsbackend ) and $actualhttpsb eq "" )
	{
		if ( defined ( $httpsbackend ) )
		{
			$httpsbackend = "true";
		}
		else
		{
			$httpsbackend = "";
		}

		if ( $httpsbackend eq "true" )
		{
			&setFarmVS( $farmname, $service, "httpsbackend", $httpsbackend );
			&successmsg( "HTTPS mode enabled for backends in service $service" );
			&setFarmRestart( $farmname );
		}
		else
		{
			&setFarmVS( $farmname, $service, "httpsbackend", "" );
			&successmsg( "HTTPS mode disabled for backends in service $service" );
			&setFarmRestart( $farmname );
		}
	}

	#Redirect
	if (    $actualredirect ne $redirect
		 or $actualredirecttype ne $redirecttype and $redirect !~ /^$/ )
	{
		if (    $redirect =~ /^http\:\/\//i
			 || $redirect =~ /^https:\/\//i
			 || $redirect =~ /^$/ )
		{
			my $directive = "";
			if ( $redirecttype eq "default" )
			{
				$directive = "redirect";
			}
			elsif ( $redirecttype eq "append" )
			{
				$directive = "redirectappend";
			}
			&setFarmVS( $farmname, $service, $directive, $redirect );
			&successmsg(
				"Redirect option enabled for service $service with URL $redirect and type $redirecttype"
			);
			&setFarmRestart( $farmname );
		}
		else
		{
			&errormsg( "Redirect doesn't begin with http or https" );
		}
	}

	#Virtual host
	if ( $actualvser ne $vser )
	{
		&setFarmVS( $farmname, $service, "vs", $vser );
		&successmsg( "Virtual host option enabled for service $service with $vser" );
		&setFarmRestart( $farmname );
	}

	#Url pattern
	if ( $actualurlp ne $urlp )
	{
		&setFarmVS( $farmname, $service, "urlp", $urlp );
		&successmsg( "URL pattern option enabled for service $service with URL $urlp" );
		&setFarmRestart( $farmname );
	}

	#TTL
	if ( $actualttl ne $ttlserv )
	{
		$error = 0;
		if ( &isnumber( $ttlserv ) eq "false" || $ttlserv eq "" )
		{
			&errormsg( "Invalid client timeout $param value, it must be a numeric value" );
			$error = 1;
		}
		if ( $error == 0 )
		{
			$status = &setFarmVS( $farmname, $service, "ttl", "$ttlserv" );
			if ( $status == 0 )
			{
				&setFarmRestart( $farmname );
				&successmsg( "The sessions TTL for $farmname farm has been modified" );
			}
			else
			{
				&errormsg( "It's not possible to change the $farmname farm sessions TTL" );
			}
		}
	}

	#session ID
	if ( $actualsession eq $session )
	{ #Solve the problem when session type is switched and session ID variable is not found
		if ( $actualsessionid ne $sessionid )
		{
			chomp ( $sessionid );
			$sessionid =~ s/ //eg;
			$error = 0;
			if ( $sessionid eq "" )
			{
				&errormsg( "Invalid session id $sessionid value" );
				$error = 1;
			}
			if ( $error == 0 )
			{
				$status = &setFarmVS( $farmname, $service, "sessionid", "$sessionid" );
				if ( $status == 0 )
				{
					&setFarmRestart( $farmname );
					&successmsg( "The session id for $farmname farm has been modified" );
				}
				else
				{
					&errormsg( "It's not possible to change the $farmname farm session id" );
				}
			}
		}
	}

	#session type
	if ( $actualsession ne $session )
	{
		#$status = &setFarmSessionType($session,$farmname,$service);
		$status = &setFarmVS( $farmname, $service, "session", "$session" );
		if ( $status == 0 )
		{
			&setFarmRestart( $farmname );
			&successmsg( "The session type for $farmname farm has been modified" );
		}
		else
		{
			&errormsg( "It's not possible to change the $farmname farm session type" );
		}
	}

	#farm guardian
	#change farmguardian values
	if (   !defined ( $usefarmguardian ) and $actualfguse eq "true"
		 or defined ( $usefarmguardian )  and $actualfguse eq "false"
		 or !defined ( $farmguardianlog ) and $actualfglog eq "true"
		 or defined ( $farmguardianlog )  and $actualfglog eq "false"
		 or $actualfgttcheck ne $timetocheck
		 or $actualfgscript ne $check_script )
	{
		$fguardianconf = &getFarmGuardianFile( $farmname, $service );

		$usefarmguardian =
		  defined ( $usefarmguardian )
		  ? "true"
		  : "false";

		$farmguardianlog =
		  defined ( $farmguardianlog )
		  ? "true"
		  : "false";

		if ( &isnumber( $timetocheck ) eq "false" )
		{
			&errormsg( "Invalid period time value $timetocheck, it must be numeric" );
		}
		elsif ( ( !defined ( $check_script ) or $check_script eq '' )
				&& $usefarmguardian eq 'true' )
		{
			&warnmsg( "To enable FarmGuardian a command to check must be defined" );
		}
		else
		{
			$status = -1;
			$usefarmguardian =~ s/\n//g;
			&runFarmGuardianStop( $farmname, $service );
			&zenlog(
					 "creating $farmname farmguardian configuration file in $fguardianconf" )
			  if !-f "$configdir/$fguardianconf";
			$check_script =~ s/\"/\'/g;
			$status =
			  &runFarmGuardianCreate( $farmname, $timetocheck, $check_script,
									  $usefarmguardian, $farmguardianlog, $service );
			if ( $status != -1 )
			{
				&successmsg(
							 "The FarmGuardian service for the $farmname farm has been modified" );
				if ( $usefarmguardian eq "true" )
				{
					$status = &runFarmGuardianStart( $farmname, $service );
					if ( $status != -1 )
					{
						&successmsg(
									 "The FarmGuardian service for the $farmname farm has been started" );
					}
					else
					{
						&errormsg(
							"An error ocurred while starting the FarmGuardian service for the $farmname farm"
						);
					}
				}
			}
			else
			{
				&errormsg(
					"It's not possible to create the FarmGuardian configuration file for the $farmname farm"
				);
			}
		}
	}
}

# Move services
if ( $action eq "editfarm-moveservice" )
{
	if ( $moveservice =~ /up/i )
	{
		$moveservice = "up";
	}
	else
	{
		$moveservice = "down";
	}

	#check if farm is up
	my $farm_status = &getFarmStatus( $farmname );

	if ( $farm_status ne 'up' )
	{
		#change configuration file
		&moveServiceFarmStatus( $farmname, $moveservice, $service );
		&moveService( $farmname, $moveservice, $service );
	}
	else
	{
		#Stop farm
		if ( &runFarmStop( $farmname, "true" ) == 0 )
		{
			#change configuration file
			&moveServiceFarmStatus( $farmname, $moveservice, $service );
			&moveService( $farmname, $moveservice, $service );

			my $status = &runFarmStart( $farmname, "true" );
			if ( $status == 0 )
			{
				&successmsg( "The $farmname farm has been restarted" );
				&setFarmHttpBackendStatus( $farmname );
			}
			else
			{
				&errormsg( "The $farmname farm hasn't been restarted" );
			}
		}
		else
		{
			&errormsg( "The $farmname farm hasn't been restarted" );
		}
	}
}

#Maintenance mode for servers
if ( $action eq "editfarm-maintenance" )
{
	&setFarmBackendMaintenance( $farmname, $id_server, $service );
	if ( $? eq 0 )
	{
		&successmsg(
					"Enabled maintenance mode for backend $id_server in service $service" );
	}
}

#disable maintenance mode for servers
if ( $action eq "editfarm-nomaintenance" )
{
	&setFarmBackendNoMaintenance( $farmname, $id_server, $service );
	if ( $? eq 0 )
	{
		&successmsg( "Disabled maintenance mode for backend" );
	}
}

#editfarm delete service
if ( $action eq "editfarm-deleteservice" )
{
	&deleteFarmService( $farmname, $service );
	if ( $? eq 0 )
	{
		&successmsg( "Deleted service $service in farm $farmname" );
		&setFarmRestart( $farmname );
	}
}

#restart farm
if ( $action eq "editfarm-restart" )
{
	&runFarmStop( $farmname, "true" );
	my $status = &runFarmStart( $farmname, "true" );
	if ( $status == 0 )
	{
		&successmsg( "The $farmname farm has been restarted" );
		&setFarmHttpBackendStatus( $farmname );
	}
	else
	{
		&errormsg( "The $farmname farm hasn't been restarted" );
	}
}

#delete server
if ( $action eq "editfarm-deleteserver" )
{
	$status = &runFarmServerDelete( $id_server, $farmname, $service );
	if ( $status != -1 )
	{
		&setFarmRestart( $farmname );
		&successmsg(
			"The real server with ID $id_server in the service $service of the farm $farmname has been deleted"
		);
	}
	else
	{
		&errormsg(
			"It's not possible to delete the real server with ID $id_server of the $farmname farm"
		);
	}
}

#save server
if ( $action eq "editfarm-saveserver" )
{
	$error = 0;
	if ( &ipisok( $rip_server ) eq "false" )
	{
		&errormsg( "Invalid real server IP value, please insert a valid value" );
		$error = 1;
	}
	if ( $priority_server && ( $priority_server > 9 || $priority_server < 1 ) )
	{
		# For HTTP and HTTPS farms the priority field its the weight
		&errormsg( "Invalid weight value for a real server, it must be 1-9" );
		$error = 1;
	}
	if ( $rip_server =~ /^$/ || $port_server =~ /^$/ )
	{
		&errormsg( "Invalid IP address and port for a real server, it can't be blank" );
		$error = 1;
	}

	if ( $error == 0 )
	{
		$status = &setFarmServer(
								  $id_server,      $rip_server,    $port_server,
								  $max_server,     $weight_server, $priority_server,
								  $timeout_server, $farmname,      $service
		);
		if ( $status != -1 )
		{
			&setFarmRestart( $farmname );
			&successmsg(
				"The real server with ID $id_server and IP $rip_server of the $farmname farm has been modified"
			);
		}
		else
		{
			&errormsg(
				"It's not possible to modify the real server with ID $id_server and IP $rip_server of the $farmname farm"
			);
		}
	}
}

if ( $action eq "editfarm-addservice" )
{
	my $result = &setFarmHTTPNewService( $farmname, $service );
	if ( $result eq "0" )
	{
		&setFarmRestart( $farmname );
		&successmsg( "Service name $service has been added to the farm" );
	}
	if ( $resutl eq "2" )
	{
		&errormsg( "New service can't be empty" );
	}
	if ( $result eq "1" )
	{
		&errormsg( "Service named $service exists" );
	}
	if ( $result eq "3" )
	{
		&errormsg(
				  "Service name is not valid, only allowed numbers, letters and hyphens." );
	}
}

$service = $farmname;

#check if the farm need a restart
my $lock = &getFarmLock( $farmname );
if ( $lock != -1 )
{
	my $msg = "There are changes that need to be applied";

	if ( $lock !~ /^$/ && &getHTTPFarmConfigIsOK( $farmname ) != 0 )
	{
		$msg = $msg . " but it's not possible to restart the farm yet due to: $lock. Still working, retry within some seconds <form method=\"post\" action=\"index.cgi\" class=\"myform\"><button type=\"submit\" class=\"myicons\" title=\"restart\"><i class=\"fa fa-refresh action-icon fa-fw green\"></i></button><input type=\"hidden\" name=\"id\" value=\"$id\"><input type=\"hidden\" name=\"action\" value=\"editfarm\"><input type=\"hidden\" name=\"farmname\" value=\"$farmname\"></form>";
	&warnmsg( $msg );
	}
	else
	{
		$msg = $msg . ", please restart the farm to apply them. Restart here <form method=\"post\" action=\"index.cgi\" class=\"myform\"><button type=\"submit\" class=\"myicons\" title=\"restart\"><i class=\"fa fa-refresh action-icon fa-fw green\"></i></button><input type=\"hidden\" name=\"id\" value=\"$id\"><input type=\"hidden\" name=\"action\" value=\"editfarm-restart\"><input type=\"hidden\" name=\"farmname\" value=\"$farmname\"></form>";
	&tipmsg( $msg );
	}
}

1;
