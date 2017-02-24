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

use strict;

require "/usr/local/zenloadbalancer/www/system_functions.cgi";
require "/usr/local/zenloadbalancer/www/snmp_functions.cgi";
require "/usr/local/zenloadbalancer/www/notifications.cgi";

# GET /system/dns
sub get_dns
{
	my $description = "Get dns";
	my $dns         = &getDns();

	&httpResponse(
			 { code => 200, body => { description => $description, params => $dns } } );
}

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
			unless ( &getValidFormat( 'dns_nameserver', $json_obj->{ $key } )
					 || ( $key eq 'secondary' && $json_obj->{ $key } eq '' ) )
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

# GET /system/ssh
sub get_ssh
{
	my $description = "Get ssh";
	my $ssh         = &getSsh();

	&httpResponse(
			 { code => 200, body => { description => $description, params => $ssh } } );
}

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

# GET /system/snmp
sub get_snmp
{
	my $description = "Get snmp";
	my %snmp        = %{ &getSnmpdConfig() };
	$snmp{ 'status' } = &getSnmpdStatus();
	
	
	&httpResponse(
		   { code => 200, body => { description => $description, params => \%snmp } } );
}

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

# GET /system/ntp
sub get_ntp
{
	my $description = "Get ntp";
	my $ntp         = &getGlobalConfiguration( 'ntp' );

	&httpResponse(
			 { code => 200, body => { description => $description, params => { "server" => $ntp } } } );
}

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
				system ( "/etc/init.d/cherokee restart > /dev/null &" );
				&httpResponse(
					{ code => 200, body => { description => $description, params => $json_obj } } );
			}
		}
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

#	GET	/system/backup
sub get_logs
{
	my $description = "Get logs";
	my $backups = &getLogs;

	&httpResponse(
		 { code => 200, body => { description => $description, params => $backups } } );
}

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

#	GET	/system/users
sub get_all_users
{
	my $description = "Get users";
	my $zapiStatus = &getZAPI( "status" );
	my @users = ( { "user"=>"root", "status"=>"true" }, { "user"=>"zapi","status"=>"$zapiStatus" } );
	
	&httpResponse(
		  { code => 200, body => { description => $description, params => \@users } } );
}

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
		my $zapi->{ 'key' } = &getZAPI( "keyzapi" );
		$zapi->{ 'status' } = &getZAPI( "status" );
		&httpResponse(
				{ code => 200, body => { description => $description, params => $zapi } } );
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 404, body => $body } );
}

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
				 && &getZAPI( "status") eq 'false' )
			{
				&setZAPI( "enable" );
			}
			elsif (    $json_obj->{ 'status' } eq 'disable'
					&& &getZAPI( "status" ) eq 'true' )
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

#	GET	/system/backup
sub get_backup
{
	my $description = "Get backups";

	my $backups = &getBackup;

	&httpResponse(
		 { code => 200, body => { description => $description, params => $backups } } );
}

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


sub get_supportsave
{
	my $description = "Get supportsave file";
	my @ss_output = `/usr/local/zenloadbalancer/app/zbin/supportsave 2>&1`;

	# get the last "word" from the first line
	my $first_line = shift @ss_output;
	my $last_word = ( split ( ' ', $first_line ) )[-1];

	my $ss_path = $last_word;
	my ( undef, $ss_filename ) = split ( '/tmp/', $ss_path );

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
	my $date = &getDate ();
	my $applicance = getApplianceVersion ();

	&httpResponse(
		{ 	code => 200, body => { description => $description, 
				params => { 
					'kernel_version' => $kernel,
					'zevenet_version' => $zevenet,
					'hostname' => $hostname,
					'system_date' => $date,
					'appliance_version' => $applicance,
				} } 
		}
	);
}

1;
