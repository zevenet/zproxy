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

use strict;

require "/usr/local/zenloadbalancer/www/functions_ext.cgi";
require "/usr/local/zenloadbalancer/www/system_functions.cgi";
use Config::Tiny;

sub setNotifCreateConfFile
{
	my $confdir = &getGlobalConfiguration( 'notifConfDir' );
	my $hostname = &getHostname();
	my $senderFile = "$confdir/sender.conf";
	my $alertsFile = "$confdir/alert_$hostname.conf";
	my $fileHandle;
	my $output;
	
	# create config directory
	if ( ! -d $confdir )
	{
		system ( &getGlobalConfiguration( 'mkdir' ) . " -p $confdir" );
		&zenlog( "Created $confdir directory." );
	}

	# restore old config files
	my $mv = &getGlobalConfiguration( "mv" );
	my $alertsOld = "/usr/local/zenloadbalancer/www/Plugins/Notifications/Alerts.conf";
	my $sendersOld = "/usr/local/zenloadbalancer/www/Plugins/Notifications/Senders.conf";

	if ( -e $alertsOld )	
	{
		system ( "$mv $alertsOld $alertsFile" );
		&zenlog( "Alert config file was moved to $confdir." );
	}

	if ( -e $sendersOld )
	{
		system ( "$mv $sendersOld $senderFile" );
		&zenlog( "Sender config file was moved to $confdir." );
	}
	
	# Create sender configuration file
	if ( ! -e $senderFile )
	{
		my $senderConf =
			"[Smtp]\n"
		 . "auth=LOGIN\n"
		 . "auth-password=\n"
		 . "auth-user=\n"
		 . "bin=/usr/local/zenloadbalancer/app/swaks/swaks\n"
		 . "from=\n"
		 . "server=\n"
		 . "tls=false\n"
		 . "to=\n";
		open my $fileHandle, '>', $senderFile;
		print $fileHandle $senderConf;
		close $fileHandle;
		&zenlog( "Sender config file created." );
	}
	
	# Create alert configuration file. It's different in each host
	if ( ! -e $alertsFile )
	{
		my $alertConf =
			"[Backend]\n"
		 . "PrefixSubject=\n"
		 . "SwitchTime=5\n"
		 . "Status=off\n\n"
		 . "[Cluster]\n"
		 . "PrefixSubject=\n"
		 . "Status=off\n\n"
		 . "[Notifications]\n"
		 . "Status=off\n\n";
		open my $fileHandle, '>', $alertsFile;
		print $fileHandle $alertConf;
		close $fileHandle;
		&zenlog( "Alert config file created." );
	}
	
	return $output;
}



# Check form data and configure mail server.
# &setNotifSenders ( $sender, $params );
sub setNotifSenders
{
	my $sender  = shift;
	my $params = shift;
	my $sendersFile = &getGlobalConfiguration( 'senders' );
	my $errMsg;

	foreach my $key ( keys %{ $params } )
	{
		if ( $key eq 'password' )
		{
			$errMsg =
			  &setNotifData( 'senders', $sender, 'auth-password', $params->{ $key } );
		}
		elsif ( $key eq 'user' )
		{
			$errMsg = &setNotifData( 'senders', $sender, 'auth-user', $params->{ $key } );
		}
		else
		{
			$errMsg = &setNotifData( 'senders', $sender, $key, $params->{ $key } );
		}
		last if ( $errMsg );
	}

	return $errMsg;
}

# &setNotifAlerts ( $alert, $params )
sub setNotifAlerts
{
	my $notif     = shift;
	my $params    = shift;
	my $alertFile = &getGlobalConfiguration( 'alerts' );
	my $errMsg;

	$notif = "Backend" if ( $notif =~ /backends/i );
	$notif = "Cluster"  if ( $notif =~ /cluster/i );

	# add subject prefix
	if ( exists $params->{ 'PrefixSubject' } )
	{
		$errMsg =
		  &setNotifData( 'alerts', $notif, 'PrefixSubject',
						 $params->{ 'PrefixSubject' } );
	}

	# change switch time
	if ( exists $params->{ 'SwitchTime' } )
	{
		$errMsg =
		  &setNotifData( 'alerts', $notif, 'SwitchTime', $params->{ 'SwitchTime' } );
		$errMsg = &changeTimeSwitch( $notif, $params->{ 'SwitchTime' } )
		  if ( ! $errMsg );
	}

	# sucessful message and reset
	&reloadNotifications() if ( ! $errMsg );

	return $errMsg;
}

# &setNotifAlertsAction ( $alert, $action )
sub setNotifAlertsAction
{
	my $notif     = shift;
	my $action    = shift;
	my $alertFile = &getGlobalConfiguration( 'alerts' );
	my $errMsg;
	my $noChanged;
	
	$notif = "Backend" if ( $notif =~ /backends/i );
	$notif = "Cluster"  if ( $notif =~ /cluster/i );

	my $status = &getNotifData( 'alerts', $notif, 'Status' );
	# enable rule
	if ( $status eq 'off' && $action eq 'enable' )
	{
		$errMsg = &setNotifData( 'alerts', $notif, 'Status', 'on' );
		$errMsg = &enableRule( $notif );
		&zenlog( "Turn on $notif notifications." );
	}

	# disable rule
	elsif ( $status eq 'on' && $action eq 'disable' )
	{
		$errMsg = &setNotifData( 'alerts', $notif, 'Status', 'off' );
		$errMsg = &disableRule( $notif );
		&zenlog( "Turn off $notif notifications." );
	}
	else
	{
		$errMsg = -2;
	}

	if ( ! $errMsg )
	{
		# enable sec process
		if (    &getNotifData( 'alerts', 'Notifications', 'Status' ) eq 'off'
			 && $action eq 'enable' )
		{
			$errMsg = &setNotifData( 'alerts', 'Notifications', 'Status', 'on' );
			&runNotifications();
		}

		# disable sec process
		elsif (    &getNotifData( 'alerts', 'Cluster', 'Status' ) eq 'off'
				&& &getNotifData( 'alerts', 'Backend', 'Status' ) eq 'off' )
		{
			$errMsg = &setNotifData( 'alerts', 'Notifications', 'Status', 'off' );
			&zlbstopNotifications();
		}
		else
		{
			&reloadNotifications();
		}
	}
	return $errMsg;
}

# Comemnt rule in sec rule file
sub disableRule    # &disableRule ( $rule )
{
	my ( $rule ) = @_;
	my $secConf  = &getGlobalConfiguration( 'secConf' );
	my $fileConf = $secConf;
	my $flag = 0;    # $flag = 0 rule don't find, $flag = 1 changing rule
	my $errMsg;

	if ( !-f $fileConf )
	{
		$errMsg = "don't find $fileConf file";
	}
	else
	{
		tie my @handle, 'Tie::File', $fileConf;

		# change server id
		foreach my $line ( @handle )
		{
			if ( !$flag )
			{
				if ( $line =~ /^#\[$rule/ ) { $flag = 1; }
			}
			else
			{
				# next rule
				if ( $line =~ /^#\[/ ) { last; }
				else
				{
					if ( $line ne "" ) { $line = "#$line"; }
				}
			}
		}

		untie @handle;
	}

	return $errMsg;
}

# Discomment rule in sec rule file
sub enableRule    # &enableRule ( $rule )
{
	my ( $rule ) = @_;
	my $fileConf = &getGlobalConfiguration( 'secConf' );
	my $flag = 0;    # $flag = 0 rule don't find, $flag = 1 changing rule
	my $output;

	if ( !-f $fileConf )
	{
		$output = 1;
		&zenlog ("don't find $fileConf file");
	}
	else
	{
		tie my @handle, 'Tie::File', $fileConf;

		# change server id
		foreach my $line ( @handle )
		{
			if ( !$flag )
			{
				$flag = 1 if ( $line =~ /^#\[$rule/ );
			}
			else
			{
				# next rule
				if ( $line =~ /^#\[/ ) { last; }
				else
				{
					$line =~ s/^#//;
				}
			}
		}

		untie @handle;
	}

	return $output;
}

# Change the switch time. This is the time server wait a state change to avoid do spam
sub changeTimeSwitch    # &changeTimeSwitch ( $rule, $time )
{
	my ( $rule, $time ) = @_;
	my $fileConf = &getGlobalConfiguration( 'secConf' );
	my $flag   = 0;     # $flag = 0 rule don't find, $flag = 1 changing rule
	my $errMsg = -1;

	if ( -f $fileConf )
	{
		tie my @handle, 'Tie::File', $fileConf;

		# change server id
		foreach my $line ( @handle )
		{
			if ( !$flag )
			{
				$flag = 1 if ( $line =~ /^#\[$rule/ );
			}
			else
			{
				# next rule
				if ( $line =~ /^#\[/ ) { last; }
				else
				{
					$line =~ s/window=.*/window=$time/ if ( $line =~ /window=/ );
					$line =~ s/\d+$/$time/             if ( $line =~ /action=.+ create .+ \d+/ );
					$errMsg = 0;
				}
			}
		}

		untie @handle;
	}
	return $errMsg;
}

# Check sec status and boot it if was on
sub zlbstartNotifications
{
	my $notificationsPath = &getGlobalConfiguration( 'notifConfDir' ) ;
	
	# create conf file if don't exists
	&setNotifCreateConfFile();
	
	# check last state before stop service
	my $status = &getNotifData( 'alerts', 'Notifications', 'Status' );
	my $output;

	# set switch time in sec.rules configuration file
	my $sections = &getNotifData( 'alerts' );
	foreach my $notif ( keys %{ $sections } )
	{
		if ( exists $sections->{ $notif }->{ 'SwitchTime' } )
		{
			my $time = &getNotifData( 'alerts', $notif, 'SwitchTime' );
			&changeTimeSwitch( $notif, $time );
		}
	}

	# run service if was up before than stop zenloadbalancer
	if ( $status eq 'on' )
	{
		$output = &runNotifications();
	}
	return $output;
}

sub zlbstopNotifications
{
	my $sec = &getGlobalConfiguration( 'sec' );
	return 0 if ( !$sec );

	my $pidof = &getGlobalConfiguration( 'pidof' );
	my $pid   = `$pidof -x sec`;
	if ( $pid )
	{
		kill 'KILL', $pid;
		&zenlog( "SEC stoped." );
	}
}

sub runNotifications
{
	my $pidof      = &getGlobalConfiguration( 'pidof' );
	my $sec        = &getGlobalConfiguration( 'sec' );
	my $secConf    = &getGlobalConfiguration( 'secConf' );
	my $syslogFile = &getGlobalConfiguration( 'syslogFile' );
	my $pid        = `$pidof -x sec`;

	if ( $pid eq "" )
	{
		# Fix inconguity between sec.rules and alert conf file
		&enableRule( 'Backend' )	if ( &getNotifData( 'alerts', 'Backend', 'Status' ) eq 'on');
		&enableRule( 'Cluster' )	if ( &getNotifData( 'alerts', 'Cluster', 'Status' ) eq 'on');
		
		# start sec process
		&zenlog( "$sec --conf=$secConf --input=$syslogFile" );
		system ( "$sec --conf=$secConf --input=$syslogFile >/dev/null 2>&1 &" );
		$pid = `$pidof -x sec`;
		if ( $pid )
		{
			&zenlog( "run SEC, pid $pid" );
		}
		else
		{
			&zenlog( "SEC couldn't run" );
		}
	}
	else
	{
		&zenlog(
				 "SEC couldn't run because just exits a process $pid for this program" );
	}
}

sub reloadNotifications
{
	my $pidof = &getGlobalConfiguration( 'pidof' );
	my $pid   = `$pidof -x sec`;
	if ( $pid )
	{
		kill 'HUP', $pid;
		&zenlog( "SEC reloaded successful" );
	}
}

#  &getNotifData ( $file, $section, $key, $data )
sub setNotifData
{
	my ( $name, $section, $key, $data ) = @_;
	my $errMsg;
	my $fileHandle;
	my $fileName;
	
	my $confdir = getGlobalConfiguration( 'notifConfDir' );
	if ( $name eq 'senders' )
	{
		$fileName = "$confdir/sender.conf";
	}
	elsif ( $name eq 'alerts' )
	{
		my $hostname = &getHostname();
		$fileName = "$confdir/alert_$hostname.conf";
	}

	if ( !-f $fileName )
	{
		$errMsg = -1;
	}
	else
	{
		# Open the config file
		$fileHandle = Config::Tiny->read( $fileName );
		$fileHandle->{ $section }->{ $key } = $data;
		$fileHandle->write( $fileName );
		&zenlog( "'$key' was modificated in '$section' notifications to '$data'" );
	}
	return $errMsg;
}

#  &getNotifData ( $file, $section, $key )
sub getNotifData
{
	my ( $name, $section, $key ) = @_;
	my $arguments = scalar @_;
	my $data;
	my $fileHandle;
	my $fileName;
	
	my $confdir = getGlobalConfiguration( 'notifConfDir' );
	if ( $name eq 'senders' )
	{
		$fileName = "$confdir/sender.conf";
	}
	elsif ( $name eq 'alerts' )
	{
		my $hostname = &getHostname();
		$fileName = "$confdir/alert_$hostname.conf";
	}

	if ( !-f $fileName ) { $data = -1; }
	else
	{
		$fileHandle = Config::Tiny->read( $fileName );

		if ( $arguments == 1 ) { $data = $fileHandle; }

		if ( $arguments == 2 ) { $data = $fileHandle->{ $section }; }

		if ( $arguments == 3 ) { $data = $fileHandle->{ $section }->{ $key }; }
	}

	return $data;
}

sub getNotifSendersSmtp
{
	my $method;
	$method->{ 'method' }   = 'email';
	$method->{ 'server' }   = &getNotifData( 'senders', 'Smtp', 'server' );
	$method->{ 'user' }     = &getNotifData( 'senders', 'Smtp', 'auth-user' );
	$method->{ 'from' }     = &getNotifData( 'senders', 'Smtp', 'from' );
	$method->{ 'to' }       = &getNotifData( 'senders', 'Smtp', 'to' );
	$method->{ 'tls' }      = &getNotifData( 'senders', 'Smtp', 'tls' );
	if ( &getNotifData( 'senders', 'Smtp', 'auth-password' ) )
		{ $method->{ 'password' } = '******'; }
	else
		{ $method->{ 'password' } = ''; }

	return $method;
}

sub getNotifAlert
{
	my $alert = shift;
	my $method;
	
	if ( $alert =~ /Backends/i )
	{
		$alert = 'Backend';
		$method->{ 'avoidflappingtime' } =
		  &getNotifData( 'alerts', $alert, 'SwitchTime' ) + 0;
		$method->{ 'prefix' } = &getNotifData( 'alerts', $alert, 'PrefixSubject' );
		if ( &getNotifData( 'alerts', $alert, 'Status' ) eq 'on' )
		{
			$method->{ 'status' } = "enabled";
		}
		else
		{
			$method->{ 'status' } = "disabled";
		}
	}
	elsif ( $alert =~ /cluster/ )
	{
		$method->{ 'prefix' } = &getNotifData( 'alerts', 'Cluster', 'PrefixSubject' );
		if ( &getNotifData( 'alerts', 'Cluster', 'Status' ) eq 'on' )
		{
			$method->{ 'status' } = "enabled";
		}
		else
		{
			$method->{ 'status' } = "disabled";
		}
	}
	return $method;
}


#~ # &sendByMail ( $subject, $bodycomp );
#~ sub sendByMail
#~ {
	#~# my ( $subject, $bodycomp, $section ) = @_;
	#~ my $paramsRef = shift;
	#~ my $params = %{ $paramsRef };
	#~ my $body;
	#~ my $logger = &getGlobalConfiguration ( 'logger' );
	#~ my $error;
	#~ my $command;		# keep command with pass
	#~ my $passCmd;		# keep pass command
	#~ my $finalCmd;		# keep the final command

	#~ $body = "\n***** Notifications *****\n\n";
	
	#~ # Add section if exsists
	#~ if ( $params{ 'section' } )
	#~ {
		#~ my $section = $params{ 'section' };
		#~ $body .= "Alerts: $section Notification\n";
	#~ }
	
	#~ # Add body if exists or test body
	#~ if ( $params{ 'body' } )
	#~ {
		#~ $body .= $params{ 'body' };
	#~ }
	#~ else
	#~ {
		#~ $body .= "Zen notification service.\n\nThis mail confirms that the configuration is correct.";
	#~ }
	
	#~ # Add server params
	#~ $command .= &getNotifData( 'senders', 'Smtp', 'bin' );
	#~ $command .= " --to " . &getNotifData( 'senders', 'Smtp', 'to' );
	#~ $command .= " --from " . &getNotifData( 'senders', 'Smtp', 'from' );
	#~ $command .= " --server " . &getNotifData( 'senders', 'Smtp', 'server' );
	#~ $command .= " --auth " . &getNotifData( 'senders', 'Smtp', 'auth' );
	#~ $command .= " --auth-user " . &getNotifData( 'senders', 'Smtp', 'auth-user' );
	#~ $passCmd = " --auth-password " . &getNotifData( 'senders', 'Smtp', 'auth-password' );
	
	#~ if ( 'true' eq &getNotifData( 'senders', 'Smtp', 'tls' ) ) 
	#~ { 
		#~ $command .= " -tls";
	#~ }

	#~ # add subfix	
	#~ $command .=	" --header \"Subject: ";
	#~ if ( exists $params{ 'section' } && exists $params{ 'subject' } )
	#~ {
		#~ $body .= &getNotifData( 'alerts', 'PrefixSubject', $params{ 'section' } ) . " $params{ 'subject' }\"";
	#~ }
	#~ else
	#~ {
		#~ $body .= " Test mail\"";
	#~ }
	
	#~ $finalCmd = "$command $passCmd --body \"$body\" 1>/dev/null";
	#~ $error = system ( $command );
	
	#~ # print log
	#~ $finalCmd = "$command  --auth-password ******** --body \"BODY\"";
	#~ system ("$logger \"$finalCmd\" -i -t sec");
	
	#~ return $error;
#~ }

# &sendByMail ( $subject, $bodycomp );
sub sendByMail
{
	my ( $subject, $bodycomp, $section ) = @_;
	my $body;
	my $command;
	my $logger = &getGlobalConfiguration ( 'logger' );
	my $error;

	$body = "\n***** Notifications *****\n\n" . "Alerts: $section Notification\n";
	$body .= $bodycomp;
	
	$command .= &getNotifData( 'senders', 'Smtp', 'bin' );
	$command .= " --to " . &getNotifData( 'senders', 'Smtp', 'to' );
	$command .= " --from " . &getNotifData( 'senders', 'Smtp', 'from' );
	$command .= " --server " . &getNotifData( 'senders', 'Smtp', 'server' );
	$command .= " --auth " . &getNotifData( 'senders', 'Smtp', 'auth' );
	$command .= " --auth-user " . &getNotifData( 'senders', 'Smtp', 'auth-user' );
	$command .= " --auth-password " . &getNotifData( 'senders', 'Smtp', 'auth-password' );
	if ( 'true' eq &getNotifData( 'senders', 'Smtp', 'tls' ) ) { $command .= " -tls"; }
	$command .=
		" --header \"Subject: "
	. &getNotifData( 'alerts', 'PrefixSubject', $section )
	. " $subject\"";
	$command .= " --body \"$body\"";
	
	#not print
	$command .= " 1>/dev/null";
	
	$error = system ( $command );
	
	# print log
	my $logMsg;
	$logMsg .= &getNotifData( 'senders', 'Smtp', 'bin' );
	$logMsg .= " --to " . &getNotifData( 'senders', 'Smtp', 'to' );
	$logMsg .= " --from " . &getNotifData( 'senders', 'Smtp', 'from' );
	$logMsg .= " --server " . &getNotifData( 'senders', 'Smtp', 'server' );
	$logMsg .= " --auth " . &getNotifData( 'senders', 'Smtp', 'auth' );
	$logMsg .= " --auth-user " . &getNotifData( 'senders', 'Smtp', 'auth-user' );
	$logMsg .= " --auth-password ********";
	$logMsg .= " -tls" 	if ( 'true' eq &getNotifData( 'senders', 'Smtp', 'tls' ) );
	
	$logMsg .= " --header \"Subject: "
			.  &getNotifData( 'alerts', 'PrefixSubject', $section )
			.  " $subject\"";
	
	$logMsg .= " --body \"BODY\"";
	
	system ("$logger \"$logMsg\" -i -t sec");
	
	return $error;
}


# &sendByMail ( $subject, $bodycomp );
sub sendTestMail
{
	my $bodycomp = "Zen notification service.\n\nThis mail confirms that the configuration is correct.";
	my $subject = "Test mail";
	my $command;
	my $logger = &getGlobalConfiguration ( 'logger' );
	my $error;

	my $body = "\n***** Notifications *****\n\n";
	$body .= $bodycomp;
	
	$command .= &getNotifData( 'senders', 'Smtp', 'bin' );
	$command .= " --to " . &getNotifData( 'senders', 'Smtp', 'to' );
	$command .= " --from " . &getNotifData( 'senders', 'Smtp', 'from' );
	$command .= " --server " . &getNotifData( 'senders', 'Smtp', 'server' );
	$command .= " --auth " . &getNotifData( 'senders', 'Smtp', 'auth' );
	$command .= " --auth-user " . &getNotifData( 'senders', 'Smtp', 'auth-user' );
	$command .= " --auth-password " . &getNotifData( 'senders', 'Smtp', 'auth-password' );
	if ( 'true' eq &getNotifData( 'senders', 'Smtp', 'tls' ) ) { $command .= " -tls"; }
	$command .=
		" --header \"Subject: $subject\"";
	$command .= " --body \"$body\"";
	
	#not print
	$command .= " 1>/dev/null";
	
	#~ print "$command\n";
	$error = system ( $command );
	
	# print log
	my $logMsg;
	$logMsg .= &getNotifData( 'senders', 'Smtp', 'bin' );
	$logMsg .= " --to " . &getNotifData( 'senders', 'Smtp', 'to' );
	$logMsg .= " --from " . &getNotifData( 'senders', 'Smtp', 'from' );
	$logMsg .= " --server " . &getNotifData( 'senders', 'Smtp', 'server' );
	$logMsg .= " --auth " . &getNotifData( 'senders', 'Smtp', 'auth' );
	$logMsg .= " --auth-user " . &getNotifData( 'senders', 'Smtp', 'auth-user' );
	$logMsg .= " --auth-password ********";
	$logMsg .= " -tls" 	if ( 'true' eq &getNotifData( 'senders', 'Smtp', 'tls' ) );
	
	$logMsg .= " --header \"Subject: $subject\"";
	
	$logMsg .= " --body \"BODY\"";
	
	system ("$logger \"$logMsg\" -i -t sec");
	
	return $error;
}

1;
