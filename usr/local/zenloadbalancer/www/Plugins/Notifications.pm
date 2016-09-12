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

package Notifications;

#~ use strict;
#~ use warnings;

use Exporter qw(import);
our @EXPORT = qw(data);


require "/usr/local/zenloadbalancer/config/global.conf";
require "/usr/local/zenloadbalancer/www/functions.cgi";
require "/usr/local/zenloadbalancer/www/farms_functions.cgi";
require "/usr/local/zenloadbalancer/www/plugins_functions.cgi";


our %data = (
	name => __PACKAGE__,

	contentSenders  => \&contentSenders,
	contentAlerts 	=> \&contentAlerts,
	menu       		=> \&menu,
	controlSenders  => \&controlSenders,
	controlAlerts 	=> \&controlAlerts,
	zlbstart   	=> \&zlbstart,
	zlbstop    	=> \&stopNotifications,
	position 	=> \&position,
);

my $notificationsPath = $plugins::plugins_path . "/" . __PACKAGE__;
my $alertsFile = "$notificationsPath/Alerts.conf";
my $sendersFile = "$notificationsPath/Senders.conf";


# Let sort the modules
sub position
{
	my $position = 2;
	return $position;
}


sub menu
{
	my $idModule 	= &plugins::getIdModule();	
	my $output;


	# icono marcado
	my $monitoringiconclass = "";
	if ( $data{name} eq $idModule ) 	
		{ $monitoringiconclass = "active"; }


	$output .= "
	  <li class=\"nav-item\">
		<a>
			<i class=\"fa fa-bell $monitoringiconclass\"></i><p>$data{name}</p>
		</a>
	    <ul class=\"sub-nav\">	
		
			<li>					
				<form action=\"index.cgi\" method=post name=\"changepage2\"> 
					<input type=\"hidden\" name=\"id\" value=\"Notifications-Alerts\"/> 					
					<a href=\"javascript:document.changepage2.submit()\">Alerts</a>		
				</form>
			</li>
			<li>
				<form action=\"index.cgi\" method=post name=\"changepage\">
					<input type=\"hidden\" name=\"id\" value=\"Notifications-Senders\"/>
					<a href=\"javascript:document.changepage.submit()\">Senders</a>
				</form>				
			</li>
        </ul>
	  </li>
	  ";

	return $output;
}


sub contentSenders
{
	my %server = %{ &getData( $sendersFile, 'Smtp' ) };	
	my $serverName = $server{'server'};
	my $user = $server{'auth-user'};
	my $pass = $server{'auth-password'};
	my $to = $server{'to'};
	my $from = $server{'from'};
	my $tls = $server{'tls'};
	my $output = "
	
		<div class=\"box grid_6\">
			<div class=\"box-head\">
				<span class=\"box-icon-24 fugue-24 user\"></span>         
				<h2>Configure Mail Sender</h2>
			</div>
		
			<div class=\"box-content\">
				<form method=\"POST\" action=\"index.cgi\">\n
					<input type=\"hidden\" name=\"id\" value=\"Notifications-Senders\">\n
					<input type=\"hidden\" name=\"action\" value=\"edit-Senders-Smtp\">\n

					<div class=\"form-row\">
						<div class=\"box grid_4\">
							<p><b>Mail Server:</b><br> smtp.mail.com</p>\n
						</div>
						<div class=\"box grid_8\">
							<input type=\"text\" name=\"server_smtp\" class=\"fixedwidth\" value=\"$serverName\"><br>
						</div>\n
					</div>
					<div style=\"clear:both;\"></div>
	
					<div class=\"form-row\">\n
						<div class=\"box grid_4\">
							<p><b>Mail User:</b><br> userMail\@mail.com</p>\n
						</div>
						<div class=\"box grid_8\">
							<input type=\"text\" name=\"user_smtp\" class=\"fixedwidth\" value=\"$user\">
						</div>\n
					</div>\n
					<div style=\"clear:both;\"></div>
	
					<div class=\"form-row\">\n
						<div class=\"box grid_4\">
							<p><b>Password</b></p>\n
						</div>
						<div class=\"box grid_8\">
							<input type=\"password\" name=\"pass_smtp\" class=\"fixedwidth\" value=\"$pass\">
						</div>\n
					</div>
	
					<div class=\"form-row\">\n
						<div class=\"box grid_4\">\n
							<p><b>From:</b> <br>fromUser\@mail.com</p>\n
						</div>
						<div class=\"box grid_8\"><input type=\"text\" name=\"from_smtp\" class=\"fixedwidth\" value=\"$from\"></div>\n
					</div>\n
					<div style=\"clear:both;\"></div>
	
						<div class=\"form-row\">\n
						<div class=\"box grid_4\">\n
							<p class=\"form-label\"><b>To:</b> <br>toUser\@mail.com</p>\n
						</div>
						<div class=\"box grid_4\">\n<input type=\"text\" name=\"to_smtp\" class=\"fixedwidth\" value=\"$to\"></div>\n
					</div>\n
					<div style=\"clear:both;\"></div>
	
					<div class=\"form-row\">\n
						<div class=\"box grid_4\">\n
							<p class=\"form-label\"><b>Enable TLS:</b></p>
						</div>	
						<div class=\"box grid_8\">\n

					";
			
					if (  $tls eq 'true' )
					{
						$output .= 
							"<p class=\"form-label\"><input type=\"checkbox\" checked name=\"tls_smtp\" value=\"true\" class=\"fixedwidth\"> </p>";
					}
					else
					{
						$output .= 
							"<p class=\"form-label\"> <input type=\"checkbox\"  name=\"tls_smtp\" value=\"true\"> </p>";
					}
											
				$output .= "		
						
						</div>
						<div style=\"clear:both;\"></div>
						<br>\n
						<input type=\"submit\" value=\"Apply\" name=\"action\" class=\"button normal grey\">\n
					
				</form>
				</div></div>
	";	

	return $output;
}


# Check form data and configure mail server.
sub controlSenders
{
	my $errMsg;
	my $sender;
	my $modify;
	
	if ( $main::action =~ /^edit-(\w+)-(\w+)/ )
	{
		$sender = $2;

		if ( $sender eq "Smtp" )
		{
			if ( getData($sendersFile, $sender, 'server') ne $main::server_smtp )
			{
				$errMsg = &setData ( $sendersFile, $sender, 'server', $main::server_smtp ); 
				$modify = 'true';
			}						
			if ( $errMsg eq "" && getData($sendersFile, $sender, 'auth-password') ne $main::pass_smtp )
			{ 
				$errMsg = &setData ( $sendersFile, $sender, 'auth-password', $main::pass_smtp );
				$modify = 'true';
			}			
			if ( $errMsg eq "" && getData($sendersFile, $sender, 'auth-user') ne $main::user_smtp )
			{ 				
				$errMsg = &setData ( $sendersFile, $sender, 'auth-user', $main::user_smtp ); 
				$modify = 'true';
			}
			if ( $errMsg eq "" && getData($sendersFile, $sender, 'to') ne $main::to_smtp )
			{ 
				$errMsg = &setData ( $sendersFile, $sender, 'to', $main::to_smtp ); 
				$modify = 'true';
			}
			if ( $errMsg eq "" && getData($sendersFile, $sender, 'from') ne $main::from_smtp )
			{ 
				$errMsg = &setData ( $sendersFile, $sender, 'from', $main::from_smtp ); 
				$modify = 'true';
			}
			
			if ( $errMsg eq "" )
			{
				if ( $main::tls_smtp eq 'true' )
				{ 
					if (&getData ($sendersFile, $sender, 'tls') ne 'true')
					{
						$errMsg = &setData ( $sendersFile, $sender, 'tls', 'true' ); 
						$modify = 'true'; 
					}
				}
				else
				{
					if ( &getData ($sendersFile, $sender, 'tls') ne 'false')
					{
						$errMsg = &setData ( $sendersFile, $sender, 'tls', 'false' );
						$modify = 'true';
					}
				}
			}
		}
	}
		
	if ( $errMsg eq "" && $modify eq 'true' )
		{ $errMsg = "0-Update smtp configuration"; }
	
	return $errMsg;
}


sub contentAlerts
{
	my $idSubModule = &plugins::getIdSubModule();
	my $idModule = &plugins::getIdModule();
	my $output;

	my %notificationHash = %{ &getData( $alertsFile ) };	
	delete $notificationHash{$idModule};
	
	# activation general   
	my $status = &getData ( $alertsFile, 'Notifications', 'Status' );
	my $description = &getData ( $alertsFile, 'Notifications', 'Description' );

	{
	$output .= "
			<div class=\"box grid_12\">
				<div class=\"box-head\">
					<span class=\"box-icon-24 fugue-24 user\"></span>
					<h2>Alerts</h2>
				</div>
				<div class=\"box-content\">		
					<form method=\"post\" action=\"index.cgi\">
	";
#					<div>
#						<h6>Global Notifications</h6>
#					</div>
	$output .= "
					<div>
					<input type=\"hidden\" name=\"id\" value=\"$idModule-$idSubModule\">
						<input type=\"hidden\" name=\"action\" value=\"edit-config\">
	";
#						<div class=\"form-row\">\n
#							<div class=\"box grid_2\">
#								<p ><b>Enable notifications</b></p>
#							</div>


#	if ( $status eq 'on' )
#	{
#		$output .= "
#							<div class=\"box grid_1\">
#								<p >
#									<input type=\"checkbox\" checked name=\"enable_alert_Notifications\" value=\"true\" class=\"fixedwidth\"> 
#								</p>
#							</div>";
#	}
#	else
#	{
#		$output .= "
#							<div class=\"box grid_1\">
#								<p >
#									<input type=\"checkbox\" name=\"enable_alert_Notifications\" value=\"true\"> 
#								</p>
#							</div>";
#	}

#	$output .= "
#							<div class=\"box grid_3\">
#								<p ><b>Description:</b><br>$description</p>
#						</div>
#							<div style=\"clear:both;\"></div>
#							<br></div></div><hr/>
#			";
	}

	foreach my $notif ( sort keys ( %notificationHash ) )
	{
		$status = $notificationHash{$notif}->{ 'Status' };
		$description = $notificationHash{$notif}->{ 'Description' };
		$prefixSubject = $notificationHash{$notif}->{ 'PrefixSubject' };
		$switchTime = $notificationHash{$notif}->{ 'SwitchTime' };
 		 		
		$output .= "
			<div>\n
				<div >
					<br>
					<h6>$notif Notifications</h6>
				</div>				
				<div class=\"form-row\">\n
					
					<div class=\"box grid_2\">
						<p ><b>Enable $notif notifications</b></p>
					</div>
		";

		if ( $status eq 'on' )
		{
			$output .= 
				"<div class=\"box grid_1\">
				<p >
					<input type=\"checkbox\" checked name=\"enable_alert_$notif\" value=\"true\" class=\"fixedwidth\"> 
				</p>
				</div>";
		}
		else
		{
			$output .= 
				"<div class=\"box grid_1\">
				<p > 
					<input type=\"checkbox\"  name=\"enable_alert_$notif\" value=\"true\"> 
				</p>
				</div>";
		}

		# Delay time = switchTime
		$output .= "
				<div class=\"box grid_3\">
					<p><b>Description:</b><br>$description</p>
				</div>
				<div class=\"box grid_2\">
					<p ><b>Prefix Subject</b> (optional)
						<input type=\"text\" name=\"prefixSubject_$notif\" value=\"$prefixSubject\">
					</p>
				</div> ";
		
		if ( $switchTime ne "" )		
		{		
			$output .= "
				<div class=\"box grid_2\">
					<p >			
						<b>Avoid Flapping time</b>. In seconds.
						<input type=\"number\" name=\"switchTime_$notif\" value=\"$switchTime\">
					</p>
				</div> ";
		}
		$output .= "
				<div style=\"clear:both;\"></div>
			</div></div>";								
	}
	$output.="
				<br><br>
				<input type=\"submit\" value=\"Modify\" name=\"action\" class=\"button normal grey\">
			</div></div>";

	return $output;
}


sub controlAlerts
{
	my $errMsg;
	my $status;
	my $idModule = &plugins::getIdModule();
	my $modify;
	my $cgi = &main::getCgiData;
	my %notificationHash = %{ &getData( $alertsFile ) };
	my $notif;	
	
	delete $notificationHash{$idModule};

	if ( $cgi->{'action'} =~ /edit-config/ )
	{		
		
		# specific alert configuration 
		foreach $notif ( sort keys ( %notificationHash ) )		
		{
			# enable rule
			if ( $cgi->{ "enable_alert_$notif" } eq 'true' )
			{
				if (&getData ($alertsFile, $notif, 'Status') ne 'on')
				{
					$errMsg = &setData ( $alertsFile, $notif, 'Status', 'on' );
					&enableRule ( $notif );
					$modify='true';
				}
			}
			# disable rule
			else
			{
				if ( &getData ($alertsFile, $notif, 'Status') ne 'off')
				{
					$errMsg = &setData ( $alertsFile, $notif, 'Status', 'off' );
					&disableRule ( $notif );
					$modify='true';
				}
			}
			# add subject id
			if ( &getData ( $alertsFile, $notif, 'PrefixSubject' ) ne $cgi->{"prefixSubject_$notif" } )
			{
				$errMsg = &setData ( $alertsFile, $notif, 'PrefixSubject', $cgi->{"prefixSubject_$notif" } );
				$modify='true';
			}
			# change switch time
			if ( &getData ( $alertsFile, $notif, 'SwitchTime' ) ne $cgi->{"switchTime_$notif"} )
			{
				$errMsg = &setData ( $alertsFile, $notif, 'SwitchTime', $cgi->{"switchTime_$notif"} );
				&changeTimeSwitch ( $notif, $cgi->{"switchTime_$notif"} );
				$modify='true';
			}
		}
	
		# global configuration
		#~ $notif = 'Notifications';
		#~ if ( $cgi->{"enable_alert_$notif"} eq 'true' )
		#~ {
			#~ if (&getData ($alertsFile, $notif, 'Status') ne 'on')
			#~ {
				#~ $errMsg = &setData ( $alertsFile, $notif, 'Status', 'on' );
				#~ if ( $errMsg eq "" ) { $errMsg = "0-Notification is enabled now"; }
				#~ &runNotifications ();
			#~ }
		#~ }
		#~ else
		#~ {
			#~ if ( &getData ($alertsFile, $notif, 'Status') ne 'off')
			#~ {
				#~ $errMsg = &setData ( $alertsFile, $notif, 'Status', 'off' );
				#~ if ( $errMsg eq "" ) { $errMsg = "0-Notification is disabled now"; }
				#~ &stopNotifications ();
			#~ }
		#~ }


		my $flag = 0;
		if (&getData ($alertsFile, 'Notifications', 'Status') eq 'off')
		{
			foreach $notif ( sort keys ( %notificationHash ) )
			{
				if ( &getData ($alertsFile, $notif, 'Status') eq 'on' )
				{
					$flag = 1;
				}
			}
			if ( $flag )
			{
				$errMsg = &setData ( $alertsFile, 'Notifications', 'Status', 'on' );
				if ( $errMsg eq "" ) { $errMsg = "0-Notification is enabled now"; }
				&runNotifications ();
			}
		}
		else
		{
			foreach $notif ( sort keys ( %notificationHash ) )
			{
				if ( &getData ($alertsFile, $notif, 'Status') eq 'on' )
				{
					$flag = 1;
				}
			}
			if ( !$flag )
			{
				$errMsg = &setData ( $alertsFile, 'Notifications', 'Status', 'off' );
				if ( $errMsg eq "" ) { $errMsg = "0-Notification is disabled now"; }
				&stopNotifications ();	
			}
		}

		# sucessful message and reset
		if ( $errMsg eq "" && $modify eq 'true')
		{
			$errMsg = "0-Alerts were modificated."; 
			&reloadNotifications();
		}
	}


	return $errMsg;
}


# Comemnt rule in sec rule file 
sub disableRule		# &disableRule ( $rule )
{
	my ( $rule ) = @_;
	my $fileConf = $main::secConf;
	my $flag = 0;	  # $flag = 0 rule don't find, $flag = 1 changing rule
	my $errMsg;

	if ( ! -f $fileConf )
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
				if ( $line =~ /^#\[$rule/ ) 
					{ $flag=1; }
			}
			else
			{
				# next rule
				if ( $line =~ /^#\[/ )
					{ last; }
				else
				{
					if ( $line ne "" )
						{ $line = "#$line"; }
				}
			}
		}
	
		untie @file;
	}
	
	return $errMsg;
}


# Discomment rule in sec rule file
sub enableRule		# &enableRule ( $rule )
{
	my ( $rule ) = @_;
	my $fileConf = $main::secConf;
	my $flag = 0;	  # $flag = 0 rule don't find, $flag = 1 changing rule
	my $errMsg;

	if ( ! -f $fileConf )
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
				$flag=1 if ( $line =~ /^#\[$rule/ );
			}
			else
			{
				# next rule
				if ( $line =~ /^#\[/ )
					{ last; }
				else
				{
					$line =~ s/^#//;
				}
			}
		}
	
		untie @file;
	}
	
	return $errMsg;
}


# Change the switch time. This is the time server wait a state change to avoid do spam
sub changeTimeSwitch		# &changeTimeSwitch ( $rule, $time )
{
	my ( $rule, $time ) = @_;
	my $fileConf = $main::secConf;
	my $flag = 0;	  # $flag = 0 rule don't find, $flag = 1 changing rule
	my $errMsg;

	if ( ! -f $fileConf )
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
				$flag=1 if ( $line =~ /^#\[$rule/ );
			}
			else
			{
				# next rule
				if ( $line =~ /^#\[/ )
					{ last; }
				else
				{
					$line =~ s/window=.*/window=$time/ if ( $line =~ /window=/ );
					$line =~ s/\d+$/$time/ if ( $line =~ /action=create .+ \d+/ );
				}
			}
		}
	
		untie @file;
	}
	
	return $errMsg;
}


# Check sec status and boot it if was on
sub zlbstart
{
	my $status = &getData( $alertsFile, 'Notifications', 'Status');
	my $output;
	
	if ( $status eq 'on' )
	{
		$output = &runNotifications;
	}
	return $output;
}


sub runNotifications
{
	my $idModule = &plugins::getIdModule();
	my $pid = `$main::pidof -x sec`;	

	if ($pid eq "")
	{ 
		system ("$main::sec --conf=$main::secConf --input=$main::syslogFile 1>/dev/null &");
		$pid = `$main::pidof -x sec`;
		if ( $pid ) 
		{			
			&main::zenlog( "run SEC, pid $pid" );
		}
		else
		{
			&main::zenlog( "SEC couldn't run" );
		}
	}
}


sub stopNotifications
{
	return 0 if (! defined $main::sec);

	my $idModule = &plugins::getIdModule();

	my $pid = `$main::pidof -x sec`;
	if ( $pid ) 
		{ kill 'KILL', $pid; }
}


sub reloadNotifications
{
	my $pid = `$main::pidof -x sec`;
	if ( $pid ) 
	{ 
		kill 'HUP', $pid; 
		&main::zenlog( "SEC reloaded successful" ); 
	}
}


sub setData	  #  &getData ( $file, $section, $key, $data )
{
	my ( $fileName, $section, $key, $data ) = @_;
	my $errMsg;	
	my $fileHandle;
		
	if ( !-f $fileName )
	{
		$errMsg = "Don't find $fileName.";
	}
	else
	{
		# Open the config file
		$fileHandle = Config::Tiny->read( $fileName );
		$fileHandle->{ $section }->{ $key } = $data;
		$fileHandle->write( $fileName );
	}
	return $errMsg;
}


#  &getData ( $file, $section, $key )
sub getData   
{
	my ( $fileName, $section, $key ) = @_;
	my $arguments = scalar @_;
	my $data;
	my $fileHandle;	

	if ( !-f $fileName )
		{ $data = "don't find $fileName."; }
	else
	{
		my $fileHandle = Config::Tiny->read( $fileName );
		
		if ( $arguments == 1 )
			{ $data = $fileHandle; }
			
		if ( $arguments == 2 )
			{ $data = $fileHandle->{ $section }; }
		
		if ( $arguments == 3 )
			{ $data = $fileHandle->{ $section }->{ $key }; }
	}

	return $data;
}



&plugins::plugins( \%data );
1;
