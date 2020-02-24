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
use Config::Tiny;
use Zevenet::Config;

sub include;

my $secConf = &getNotifConfFile();

sub getNotifConfFile
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	return &getGlobalConfiguration( "notifConfDir" ) . "/sec.rules";
}

sub setNotifCreateConfFile
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	use Zevenet::SystemInfo;

	my $confdir    = &getGlobalConfiguration( 'notifConfDir' );
	my $hostname   = &getHostname();
	my $senderFile = "$confdir/sender.conf";
	my $alertsFile = "$confdir/alert_$hostname.conf";
	my $version = 1;    # version of senders config file
	my $fileHandle;
	my $output;

	# create config directory
	if ( !-d $confdir )
	{
		my $mkdir = &getGlobalConfiguration( 'mkdir' );
		&logAndRun( "$mkdir -p $confdir" );
		&zenlog( "Created $confdir directory.", "info", "NOTIFICATIONS" );
	}

	# restore old config files
	my $mv         = &getGlobalConfiguration( "mv" );
	my $alertsOld  = "/usr/local/zevenet/www/Plugins/Notifications/Alerts.conf";
	my $sendersOld = "/usr/local/zevenet/www/Plugins/Notifications/Senders.conf";

	if ( -e $alertsOld )
	{
		&logAndRun( "$mv $alertsOld $alertsFile" );
		&zenlog( "Alert config file was moved to $confdir.", "info", "NOTIFICATIONS" );
	}

	if ( -e $sendersOld )
	{
		&logAndRun( "$mv $sendersOld $senderFile" );
		&zenlog( "Sender config file was moved to $confdir.", "info", "NOTIFICATIONS" );
	}

	# Create sender configuration file
	if ( !-e $senderFile )
	{
		my $senderConf =
		    "version=$version\n\n"
		  . "[Smtp]\n"
		  . "auth=LOGIN\n"
		  . "auth-password=\n"
		  . "auth-user=\n"
		  . "bin=/usr/local/zevenet/app/swaks/swaks\n"
		  . "from=\n"
		  . "server=\n"
		  . "tls=false\n" . "to=\n";
		open my $fileHandle, '>', $senderFile;
		print $fileHandle $senderConf;
		close $fileHandle;
		&zenlog( "Sender config file created.", "info", "NOTIFICATIONS" );
	}

	# Create alert configuration file. It's different in each host
	if ( !-e $alertsFile )
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
		&zenlog( "Alert config file created.", "info", "NOTIFICATIONS" );
	}

	return $output;
}

# Check form data and configure mail server.
# &setNotifSenders ( $sender, $params );
sub setNotifSenders
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $sender = shift;
	my $params = shift;

	my $sendersFile = &getGlobalConfiguration( 'senders' );
	my $errMsg;

	foreach my $key ( keys %{ $params } )
	{
		if ( $key eq 'password' )
		{
			include 'Zevenet::Code';

			$errMsg =
			  &setNotifData( 'senders', $sender, 'auth-password',
							 &getCodeEncode( $params->{ $key } ) );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $notif  = shift;
	my $params = shift;

	my $alertFile = &getGlobalConfiguration( 'alerts' );
	my $errMsg;

	$notif = "Backend" if ( $notif =~ /backends/i );
	$notif = "Cluster" if ( $notif =~ /cluster/i );

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
	}

	# successful message and reset
	&reloadNotifications() if ( !$errMsg );

	return $errMsg;
}

# &setNotifAlertsAction ( $alert, $action )
sub setNotifAlertsAction
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $notif = shift;
	my $action = shift // "";

	my $alertFile = &getGlobalConfiguration( 'alerts' );
	my $errMsg;
	my $noChanged;

	$notif = "Backend" if ( $notif =~ /backends/i );
	$notif = "Cluster" if ( $notif =~ /cluster/i );

	my $status = &getNotifData( 'alerts', $notif, 'Status' );

	# enable rule
	if ( $status eq 'off' && $action eq 'enable' )
	{
		$errMsg = &setNotifData( 'alerts', $notif, 'Status', 'on' );
		&zenlog( "Turn on $notif notifications.", "info", "NOTIFICATIONS" );
	}

	# disable rule
	elsif ( $status eq 'on' && $action eq 'disable' )
	{
		$errMsg = &setNotifData( 'alerts', $notif, 'Status', 'off' );
		&zenlog( "Turn off $notif notifications.", "info", "NOTIFICATIONS" );
	}
	else
	{
		$errMsg = -2;
	}

	if ( !$errMsg )
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
			$errMsg = "";
			&reloadNotifications();
		}
	}

	return $errMsg;
}

# Discomment rule in sec rule file
sub enableRule    # &enableRule ( $rule )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $rule ) = @_;

	my $flag = 0;    # $flag = 0 rule don't find, $flag = 1 changing rule
	my $output;

	if ( !-f $secConf )
	{
		$output = 1;
		&zenlog( "don't find $secConf file", "error", "NOTIFICATIONS" );
	}
	else
	{
		require Tie::File;
		tie my @handle, 'Tie::File', $secConf;

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $rule, $time ) = @_;

	my $fileConf = $secConf;
	my $flag     = 0;          # $flag = 0 rule don't find, $flag = 1 changing rule
	my $errMsg   = -1;

	if ( -f $fileConf )
	{
		require Tie::File;
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $notificationsPath = &getGlobalConfiguration( 'notifConfDir' );
	my $output;

	# create conf file if don't exists
	&setNotifCreateConfFile();

	# check last state before stop service
	my $status = &getNotifData( 'alerts', 'Notifications', 'Status' );

	# run service if was up before than stop zevenet
	if ( $status eq 'on' )
	{
		$output = &runNotifications();
	}

	return $output;
}

sub zlbstopNotifications
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $sec = &getGlobalConfiguration( 'sec' );
	return 0 if ( !$sec );

	my $pidof = &getGlobalConfiguration( 'pidof' );
	my $pid   = &logAndGet( "$pidof -x sec" );

	if ( $pid )
	{
		kill 'KILL', $pid;
		&zenlog( "SEC stopped.", "info", "NOTIFICATIONS" );
	}
}

sub createSecConfig
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $template = &getGlobalConfiguration( 'secTemplate' );

	# Copy the template
	my $cp = &getGlobalConfiguration( "cp" );
	&logAndRun( "$cp $template $secConf" );

	# Fix inconguity between sec.rules and alert conf file
	if ( &getNotifData( 'alerts', 'Backend', 'Status' ) eq 'on' )
	{
		my $time = &getNotifData( 'alerts', 'Backend', 'SwitchTime' );
		&enableRule( 'Backend' );
		&changeTimeSwitch( 'Backend', $time );
	}
	&enableRule( 'Cluster' )
	  if ( &getNotifData( 'alerts', 'Cluster', 'Status' ) eq 'on' );
}

sub runNotifications
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $pidof      = &getGlobalConfiguration( 'pidof' );
	my $sec        = &getGlobalConfiguration( 'sec' );
	my $syslogFile = &getGlobalConfiguration( 'syslogFile' );
	my $pid        = &logAndGet( "$pidof -x sec" );

	if ( $pid eq "" )
	{
		&createSecConfig();

		# start sec process
		&logAndRunBG( "$sec --conf=$secConf --input=$syslogFile" );
		$pid = &logAndGet( "$pidof -x sec" );
		if ( $pid )
		{
			&zenlog( "run SEC, pid $pid", "info", "NOTIFICATIONS" );
		}
		else
		{
			&zenlog( "SEC could not run", "error", "NOTIFICATIONS" );
		}
	}
	else
	{
		&zenlog(
			"SEC couldn't run because a process for this program already exists, pid:$pid.",
			"info", "NOTIFICATIONS"
		);
	}
}

sub reloadNotifications
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $pidof = &getGlobalConfiguration( 'pidof' );
	my $pid   = &logAndGet( "$pidof -x sec" );

	if ( $pid )
	{
		&createSecConfig();
		kill 'HUP', $pid;
		&zenlog( "SEC reloaded successfully", "info", "NOTIFICATIONS" );
	}
}

#  &getNotifData ( $file, $section, $key, $data )
sub setNotifData
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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

#~ &zenlog( "'$key' was modificated in '$section' notifications to '$data'", "info", "SYSTEM" );
	}

	return $errMsg;
}

#  &getNotifData ( $file, $section, $key )
sub getNotifData
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $method;
	$method->{ 'method' } = 'email';
	$method->{ 'server' } = &getNotifData( 'senders', 'Smtp', 'server' );
	$method->{ 'user' }   = &getNotifData( 'senders', 'Smtp', 'auth-user' );
	$method->{ 'from' }   = &getNotifData( 'senders', 'Smtp', 'from' );
	$method->{ 'to' }     = &getNotifData( 'senders', 'Smtp', 'to' );
	$method->{ 'tls' }    = &getNotifData( 'senders', 'Smtp', 'tls' );
	if ( &getNotifData( 'senders', 'Smtp', 'auth-password' ) )
	{
		$method->{ 'password' } = '******';
	}
	else { $method->{ 'password' } = ''; }

	return $method;
}

sub getNotifAlert
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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

# &sendByMail ( $subject, $bodycomp );
sub sendByMail
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $subject, $bodycomp, $section ) = @_;

	my $body;
	my $command;
	my $logger = &getGlobalConfiguration( 'logger' );
	my $error;

	my $pass = &getNotifData( 'senders', 'Smtp', 'auth-password' );
	if ( $pass )
	{
		include 'Zevenet::Code';
		$pass = &getCodeDecode( $pass );
	}

	$body = "\n***** Notifications *****\n\n" . "Alerts: $section Notification\n";
	$body .= $bodycomp;

	my $from = &getNotifData( 'senders', 'Smtp', 'from' );
	$command .= &getNotifData( 'senders', 'Smtp', 'bin' );
	$command .= " --to " . &getNotifData( 'senders', 'Smtp', 'to' );
	$command .= " --from " . &getNotifData( 'senders', 'Smtp', 'from' );
	$command .= " --server " . &getNotifData( 'senders', 'Smtp', 'server' );

	if (    &getNotifData( 'senders', 'Smtp', 'auth-user' )
		 || &getNotifData( 'senders', 'Smtp', 'auth-password' ) )
	{
		$command .= " --auth " . &getNotifData( 'senders', 'Smtp', 'auth' );
		$command .= " --auth-user " . &getNotifData( 'senders', 'Smtp', 'auth-user' )
		  if ( &getNotifData( 'senders', 'Smtp', 'auth-user' ) );
		$command .= " --auth-password " . $pass if ( $pass );
	}

	if ( 'true' eq &getNotifData( 'senders', 'Smtp', 'tls' ) )
	{
		$command .= " -tls";
	}

	#~ $command .= " --header 'From: $from '";
	$command .=
	    " --header 'Subject: "
	  . &getNotifData( 'alerts', $section, 'PrefixSubject' )
	  . " $subject'";

	$command .= " --body '$body'";

	$error = &logAndRun( $command );

	# print log
	my $logMsg;
	$logMsg .= &getNotifData( 'senders', 'Smtp', 'bin' );
	$logMsg .= " --to " . &getNotifData( 'senders', 'Smtp', 'to' );
	$logMsg .= " --from " . &getNotifData( 'senders', 'Smtp', 'from' );
	$logMsg .= " --server " . &getNotifData( 'senders', 'Smtp', 'server' );

	if (    &getNotifData( 'senders', 'Smtp', 'auth-user' )
		 || &getNotifData( 'senders', 'Smtp', 'auth-password' ) )
	{
		$logMsg .= " --auth " . &getNotifData( 'senders', 'Smtp', 'auth' );
		$logMsg .= " --auth-user " . &getNotifData( 'senders', 'Smtp', 'auth-user' )
		  if ( &getNotifData( 'senders', 'Smtp', 'auth-user' ) );
		$logMsg .= " --auth-password ********"
		  if ( &getNotifData( 'senders', 'Smtp', 'auth-password' ) );
	}
	$logMsg .= " -tls" if ( 'true' eq &getNotifData( 'senders', 'Smtp', 'tls' ) );

	#~ $logMsg .= " --header 'From: $from'";
	$logMsg .=
	    " --header 'Subject: "
	  . &getNotifData( 'alerts', $section, 'PrefixSubject' )
	  . " $subject'";
	$logMsg .= " --body 'BODY'";

	system ( "$logger \"$logMsg\" -i -t sec" );

	return $error;
}

# &sendTestMail ( $subject, $bodycomp );
sub sendTestMail
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $bodycomp =
	  "Zevenet notification service.\n\nThis mail confirms that the configuration is correct.";
	my $subject = "Test mail";
	my $command;
	my $logger = &getGlobalConfiguration( 'logger' );
	my $error;

	my $pass = &getNotifData( 'senders', 'Smtp', 'auth-password' );
	if ( $pass )
	{
		include 'Zevenet::Code';
		$pass = &getCodeDecode( $pass );
	}

	my $body = "\n***** Notifications *****\n\n";
	$body .= $bodycomp;

	my $from = &getNotifData( 'senders', 'Smtp', 'from' );
	$command .= &getNotifData( 'senders', 'Smtp', 'bin' );
	$command .= " --to " . &getNotifData( 'senders', 'Smtp', 'to' );
	$command .= " --from " . &getNotifData( 'senders', 'Smtp', 'from' );
	$command .= " --server " . &getNotifData( 'senders', 'Smtp', 'server' );

	if (    &getNotifData( 'senders', 'Smtp', 'auth-user' )
		 || &getNotifData( 'senders', 'Smtp', 'auth-password' ) )
	{
		$command .= " --auth " . &getNotifData( 'senders', 'Smtp', 'auth' );
		$command .= " --auth-user " . &getNotifData( 'senders', 'Smtp', 'auth-user' )
		  if ( &getNotifData( 'senders', 'Smtp', 'auth-user' ) );
		$command .= " --auth-password " . $pass if ( $pass );
	}
	if ( 'true' eq &getNotifData( 'senders', 'Smtp', 'tls' ) )
	{
		$command .= " -tls";
	}

	#~ $command .= " --header 'From: $from, ' --header 'Subject: $subject'";
	$command .= " --header 'Subject: $subject'";
	$command .= " --body '$body'";

	#~ print "$command\n";
	$error = &logAndRun( $command );

	# print log
	my $logMsg;
	$logMsg .= &getNotifData( 'senders', 'Smtp', 'bin' );
	$logMsg .= " --to " . &getNotifData( 'senders', 'Smtp', 'to' );
	$logMsg .= " --from " . &getNotifData( 'senders', 'Smtp', 'from' );
	$logMsg .= " --server " . &getNotifData( 'senders', 'Smtp', 'server' );

	if (    &getNotifData( 'senders', 'Smtp', 'auth-user' )
		 || &getNotifData( 'senders', 'Smtp', 'auth-password' ) )
	{
		$logMsg .= " --auth " . &getNotifData( 'senders', 'Smtp', 'auth' );
		$logMsg .= " --auth-user " . &getNotifData( 'senders', 'Smtp', 'auth-user' )
		  if ( &getNotifData( 'senders', 'Smtp', 'auth-user' ) );
		$logMsg .= " --auth-password ********"
		  if ( &getNotifData( 'senders', 'Smtp', 'auth-password' ) );
	}

	$logMsg .= " -tls" if ( 'true' eq &getNotifData( 'senders', 'Smtp', 'tls' ) );

	#~ $logMsg .= " --header 'From: $from' --header 'Subject: $subject'";
	$logMsg .= " --header 'Subject: $subject'";
	$logMsg .= " --body 'BODY'";

	system ( "$logger \"$logMsg\" -i -t sec" );

	return $error;
}

sub encryptNotifPass
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	include 'Zevenet::Code';
	if ( !&getNotifData( "senders", "_", "version" ) )
	{
		my $pass = &getNotifData( "senders", "Smtp", "auth-password" );

		if ( $pass )
		{
			include 'Zevenet::Code';
			my $coded = &getCodeEncode( $pass );
			&setNotifData( "senders", "Smtp", "auth-password", &getCodeEncode( $pass ) );
		}

		&setNotifData( "senders", "_", "version", 1 );
	}
}

1;
