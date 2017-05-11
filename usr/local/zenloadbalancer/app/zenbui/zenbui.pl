#!/usr/bin/perl -w
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

#use strict;
use Curses::UI;
my $globalcfg = "/usr/local/zenloadbalancer/config/global.conf";
require "/usr/local/zenloadbalancer/www/functions.cgi";
require "/usr/local/zenloadbalancer/app/zenbui/buifunctions.pl";
require ($globalcfg);

my $ifconfig_bin = &getGlobalConfiguration('ifconfig_bin');
my $zlbmenu;
my $win3;
my $winhelp;
my $zlbhostinput;
my ($mgmtif, $mgmtip, $mgmtmask, $mgmtgw);
my ($mgmtifinput, $mgmtipinput, $mgmtmaskinput, $mgmtgwinput);

my $zenui = new Curses::UI( -color_support => 1, 
			  -clear_on_exit => 1 );
#my $co = $Curses::UI::color_object;
#$co->define_color('white', 70, 185, 113);

my $zlbhostname = `hostname`;
chomp $zlbhostname;

my $win1 = $zenui->add(
	'win1', 'Window',
	-border 	=> 1,
	-y		=> 0,
	-padbottom 	=> 4,
	-bfg		=> 'green',
	-bg		=> 'white',
	-tfg		=> 'white',
	-tbg		=> 'green',
	-title		=> 'ZEVENET Basic User Interface',
	-titlereverse 	=> 0,
);

my $win2 = $win1->add(
	'win2', 'Window',
	-border => 1,
	-bfg => 'green',
	-bg => 'white',
	-width => 25,
	-tfg	=> 'white',
	-tbg	=> 'black',
	-title	=> 'Main Menu',
);

$zlbmenu = $win2->add(
	'win2id1', 'Listbox',
	-selectmode => 'single',
	-fg => 'white',
	-bg => 'black',
        -values    => [1, 2, 3, 4, 5, 6, 7, 8],
        -labels    => { 1 => 'Status',
			2 => 'Services', 
                       	3 => 'Hostname',
			4 => 'MGMT Interface',
			5 => 'Time Zone',
			6 => 'Keyboard Map',
			7 => 'Reboot/Shutdown',
			8 => 'Exit to shell', },
	-onchange => \&manage_sel, 
);
$zlbmenu->focus();
$zlbmenu->set_selection(0);
$zlbmenu->focus();

$winhelp = $zenui->add(
	'winhelp', 'Window',
        -bg 		=> 'white',
	-y 		=> -1,
        -height		=> 4,

);

my $help = $winhelp->add(
	'zlbhelp', 'TextViewer',
        -bg => 'black',
        -title  	=> 'ZEVENET Basic User Interface Help:',
        -tfg    	=> 'white',
        -tbg    	=> 'black',
        -bfg 		=> 'green',
        -border => 1,
        -text => "Ctrl+Q = Exit, Ctrl+X = Main menu, Arrows = Move into the item,\nTab = Change to next item, Intro = Select.\n"
);


sub exit_dialog()
{
	my $return = $zenui->dialog(
                     -message   	=> "Do you really want to exit to shell?",
                     -title     	=> "Exit Confirmation", 
                     -buttons   	=> ['yes', 'no'],
		     -selected 		=> 1,
		     -bfg 		=> 'green',
		     -fg 		=> 'white',
		     -bg		=> 'black',
		     -tfg		=> 'white',
	     	     -tbg		=> 'green',
		     -titlereverse 	=> 0,
	);
	if ($return){
        	exit(0);
	}
}

sub confirm_dialog()
{
	my ($message) = @_;
	my $return = $zenui->dialog(
                     -message   	=> $message,
                     -title     	=> "Confirmation", 
                     -buttons   	=> ['yes', 'no'],
		     -selected 		=> 1,
		     -bfg 		=> 'green',
		     -fg 		=> 'white',
		     -bg		=> 'black',
		     -tfg		=> 'white',
		     -tbg		=> 'green',
		     -titlereverse 	=> 0,
	);

        return $return;
}

sub inform_dialog()
{
	my ($message) = @_;
	my $return = $zenui->dialog(
                     -message   	=> $message,
                     -title     	=> "Information", 
                     -buttons   	=> ['ok'],
		     -bfg 		=> 'green',
		     -fg 		=> 'white',
		     -bg		=> 'black',
		     -tfg		=> 'white',
		     -tbg		=> 'green',
		     -titlereverse 	=> 0,
	);
        return $return;
}

sub error_dialog()
{
	my ($message) = @_;
	my $return = $zenui->dialog(
                     -message   => $message,
                     -title     => "Warning", 
                     -buttons   => ['ok'],
		     -bfg 	=> 'red',
		     -fg 	=> 'white',
		     -bg	=> 'black',
		     -tfg	=> 'white',
		     -tbg	=> 'red',
		     -titlereverse 	=> 0,
	);
        return $return;
}

sub refresh_win3()
{
	$zlbmenu->focus();
	&manage_sel();	
}

sub manage_sel()
{
	if ( $win3 ){
		$win1->delete('win3');
	}
	my $selected = 0;
	$selected = $zlbmenu->get();
	if ($selected){
		if ($selected == 1){
			&create_win3('ZEVENET Status');
			&show_status_system();
		}
		elsif ($selected == 2){
			&create_win3('ZEVENET Services');
			&manage_zlb_services();
		}
		elsif ($selected == 3){
			&create_win3('ZEVENET Hostname');
			&manage_zlb_hostname();
		}
		elsif ($selected == 4){
			&create_win3('ZEVENET MGMT Interface');
			&manage_mgmt();
		}
		elsif ($selected == 5){
			&create_win3('ZEVENET Time Zone');
			&manage_timezone();
		}
		elsif ($selected == 6){
			&create_win3('ZEVENET Keyboard Layout');
			&manage_keyboard();
		}
		elsif ($selected == 7){
			&create_win3('ZEVENET Reboot/Shutdown');
			&manage_power();
		}
		elsif ($selected == 8){
			\&exit_dialog();
		}
	}
}

sub manage_power(){
    	my $power = $win3->add(
		'win3id2', 'Buttonbox',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-title => 'Power Manager',
		-border => 1,
		-y => 1,
		-selected => 2,
        	-buttons   => [
            	{ 
              		-label => '< Reboot >',
              		-value => 1,
              		-shortcut => 1,
			-onpress => 	sub { my $ret = &confirm_dialog("Are you sure you want to reboot your ZEVENET?");
						if ($ret){
							my @run = `(reboot &)`;
							exit(0);
						}
					}, 
            	},
	    	{ 
              		-label => '< Shutdown >',
              		-value => 2,
              		-shortcut => 2,
			-onpress => 	sub { my $ret = &confirm_dialog("Are you sure you want to shutdown your ZEVENET?");
						if ($ret){
							my @run = `(poweroff &)`;
							exit(0);
						}
					}, 
            	},
	    	{ 
              		-label => '< Cancel >',
              		-value => 3,
              		-shortcut => 3,
			-onpress => sub { $zlbmenu->focus(); },
            	},
        	],
	);
	$power->focus();
}

sub manage_keyboard()
{
	my $line;
	my $keyboardfile = "/etc/default/keyboard";
	my ($keyboard, $zlbkeyboard);
	if (-f $keyboardfile){
		open FR,$keyboardfile;

		while ($line=<FR>){
			if ($line =~ 'XKBLAYOUT'){
				$keyboard = $line;
			}
		}
		close FR;
	}
	$zlbkeyboard = $win3->add( 
	        'win3id1', 'TextEntry',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-border => 1,
		-y => 1,
		-title => 'Keyboard Layout Configuration', 
	    	-text => $keyboard,
		-readonly => 1,
	);
    	my $confirm = $win3->add(
		'win3id2', 'Buttonbox',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-y => 5,
		-selected => 1,
        	-buttons   => [
            	{ 
              		-label => '< Change >',
              		-value => 1,
              		-shortcut => 1,
			-onpress => sub { system('dpkg-reconfigure keyboard-configuration');
					$zenui->reset_curses();
					&inform_dialog("You have to reboot the host to apply the changes.");
					&refresh_win3(); 
					},  
            	},
	    	{ 
              		-label => '< Cancel >',
              		-value => 2,
              		-shortcut => 2,
			-onpress => sub { $zlbmenu->focus(); }, 
            	},
        	],
	);
	$confirm->focus();
}

sub manage_timezone(){
	my $line;
	my $timezonefile = "/etc/timezone";
	my ($timezone, $zlbtimezone);
	if (-f $timezonefile){
		open FR,$timezonefile;

		while ($line=<FR>){
			$timezone = $line;
		}
		close FR;
	}
	$zlbtimezone = $win3->add( 
	        'win3id1', 'TextEntry',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-border => 1,
		-y => 1,
		-title => 'Time Zone Configuration', 
	    	-text => $timezone,
		-readonly => 1,
	);
    	my $confirm = $win3->add(
		'win3id2', 'Buttonbox',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-y => 5,
		-selected => 1,
        	-buttons   => [
            	{ 
              		-label => '< Change >',
              		-value => 1,
              		-shortcut => 1,
			-onpress => sub { #$zenui->leave_curses(); 
					system('dpkg-reconfigure tzdata');
					$zenui->reset_curses();
					my @run = `(ntpdate pool.ntp.org &) > /dev/null`;
					#$zenui->reset_curses();
					&inform_dialog("Synchronizing time with pool.ntp.org...");
					&refresh_win3(); 
					}, 
            	},
	    	{ 
              		-label => '< Cancel >',
              		-value => 2,
              		-shortcut => 2,
			-onpress => sub { $zlbmenu->focus(); }, 
            	},
        	],
	);
	$confirm->focus();
}			

sub manage_mgmt(){
	my $mgmtif = "";
	my @all_interfaces = &getInterfaceTypeList( 'nic' );
	# discard bonding slave nics
	@all_interfaces = grep { $_->{ is_slave } eq 'false' } @all_interfaces;
	my $i=0;
	my $mgmtindex = 0;
	my @interfaces = ();

	foreach my $if_ref (@all_interfaces){
		push( @interfaces, $if_ref->{ name } );

		if ( $if_ref->{ name } eq "mgmt" ){
			$mgmtindex = $i;
		} 

		$i++;
	}

	$mgmtifinput = $win3->add(
		'win3id1', 'Listbox',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-border => 1,
		-vscrollbar => 1,
		-y => 0,
		-height => 4,
        	-values => \@interfaces,
		-title => 'Available Interfaces List',
		-vscrollbar => 1,
		-onchange => sub {
					$mgmtif = $mgmtifinput->get();
					my $if_ref = &getInterfaceConfig( $mgmtif );
					$mgmtip = $if_ref->{ addr } // '';
					if ($mgmtipinput){
						$mgmtipinput->text($mgmtip);
					}
					$mgmtmask = $if_ref->{ mask } // '';
					if ($mgmtmaskinput){
						$mgmtmaskinput->text($mgmtmask);
					}
					$mgmtgw = $if_ref->{ gateway } // '';
					if ($mgmtgwinput){
						$mgmtgwinput->text($mgmtgw);
					}
				},
		);
	$mgmtifinput->focus();
	$mgmtifinput->set_selection($mgmtindex);
	$mgmtif = $mgmtifinput->get();
	my $if_ref = &getInterfaceConfig( $mgmtif );
	$mgmtip = $if_ref->{ addr };
	$mgmtmask = $if_ref->{ mask };
	$mgmtgw = $if_ref->{ gateway };


	$mgmtipinput = $win3->add(
	        'win3id2', 'TextEntry',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-border => 1,
		-y => 4,
		-title => 'MGMT IP Configuration', 
	    	-text => $mgmtip,
	);

	$mgmtmaskinput = $win3->add( 
	        'win3id3', 'TextEntry',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-border => 1,
		-y => 7,
		-title => 'MGMT NetMask Configuration', 
	    	-text => $mgmtmask,
	);

	$mgmtgwinput = $win3->add( 
	        'win3id4', 'TextEntry',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-border => 1,
		-y => 10,
		-title => 'MGMT GateWay Configuration', 
	    	-text => $mgmtgw,
	);
	my $confirm = $win3->add(
		'win3id5', 'Buttonbox',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-y => 13,
		-selected => 1,
        	-buttons   => [
            	{ 
              		-label => '< Save >',
              		-value => 1,
              		-shortcut => 1,
			-onpress =>  sub { &set_net(); },
            	},
	    	{ 
              		-label => '< Cancel >',
              		-value => 2,
              		-shortcut => 2,
			-onpress => sub { $zlbmenu->focus(); }, 
            	},
        	],
	);
	$confirm->focus();
}

sub set_net()
{
	my $setchanges = 1;
	if ( $mgmtifinput && $mgmtipinput && $mgmtmaskinput && $mgmtgwinput )
	{
		my $newif   = $mgmtifinput->get();
		my $newip   = $mgmtipinput->get();
		my $newmask = $mgmtmaskinput->get();
		my $newgw   = $mgmtgwinput->get();

		if ( &ipisok( $newip ) eq "false" )
		{
			&error_dialog( "IP Address $newip structure is not ok" );
			$setchanges = 0;
		}

		# check if the new netmask is correct, if empty don't worry
		if ( $newmask !~ /^$/ && &ipisok( $newmask ) eq "false" )
		{
			&error_dialog( "Netmask address $newmask structure is not ok" );
			$setchanges = 0;
		}

		# check if the new gateway is correct, if empty don't worry
		if ( $newgw !~ /^$/ && &ipisok( $newgw ) eq "false" )
		{
			&inform_dialog(
						  "Gateway address $newgw structure is not ok, set it in the web GUI" );
			$newgw = "";
		}

		if ( $setchanges )
		{
			my $ret = &confirm_dialog(
							   "Are you sure you want to change your ZEVENET MGMT Interface?" );

			# Get interface configuration structure
			my $if_ref = &getInterfaceConfig( $newif ) // &getSystemInterface( $newif );

			if ( $ret )
			{
				if ( $if_ref->{addr} )
				{
					# Delete old IP and Netmask from system to replace it
					&delIp( $if_ref->{name}, $if_ref->{addr}, $if_ref->{mask} );

					# Remove routes if the interface has its own route table: nic and vlan
					&delRoutes( "local", $if_ref );
				}

				# Set new interface configuration
				$if_ref->{ addr }    = $newip   if $newip;
				$if_ref->{ mask }    = $newmask if $newmask;
				$if_ref->{ gateway } = $newgw   if $newgw;
				$if_ref->{ ip_v }    = 4;

				# Add new IP, netmask and gateway
				&addIp( $if_ref );

				# Writing new parameters in configuration file
				&writeRoutes( $if_ref->{ name } );

				# Put the interface up
				{
					my $previous_status = $if_ref->{ status };
					my $state = &upIf( $if_ref, 'writeconf' );

					if ( $state == 0 )
					{
						$if_ref->{ status } = "up";
						&inform_dialog( "Network interface $newif is now UP" );

						&applyRoutes( "local", $if_ref );

						#apply the GW to default gw.
						&applyRoutes( "global", $if_ref, $newgw );

						&inform_dialog( "All is ok, saved $newif interface config file" );
						&inform_dialog(
							"If this is your first boot you can access to ZEVENET Web GUI through\nhttps://$newip:444\nwith user root and password admin,\nremember to change the password for security reasons in web GUI."
						);
					}
					else
					{
						$if_ref->{ status } = $previous_status;
						&error_dialog(
							"A problem is detected configuring $newif interface, you have to configure your $newif \nthrough command line and after save the configuration in the web GUI"
						);
					}
				}

				&setInterfaceConfig( $if_ref );
			}
		}

		&refresh_win3();
	}
}

sub manage_zlb_services(){
	my @services=('cherokee', 'zenloadbalancer');
	my $cherokeestatus = "STOPPED";
	my $zlbservicestatus = "STOPPED";
	my @run = `ps ex`;
	if (grep (/$services[0]/,@run)){
		$cherokeestatus = "ACTIVE";
	}
	@run = `ifconfig`;
	@run = grep (!/^ /,@run);
	@run = grep (!/^lo/,@run);
	if (grep (/^[a-z]/,@run)){
		$zlbservicestatus = "ACTIVE";
	}
	my $servicestatus = $win3->add( 
	        'win3id1', 'TextViewer',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-border => 1,
		-y => 0,
		-height => 5,
		-vscrollbar => 1,
		-title => 'Services Status', 
	    	-text => "ZEVENET Services:\n"
			. "\tWeb Service:\t"
			. $cherokeestatus . "\n"
			. "\tZEVENET:\t"
			. $zlbservicestatus . "\n",
	);

	my $service1 = $win3->add(
		'win3id2', 'Buttonbox',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-title => 'Web Service Manager',
		-border => 1,
		-y => 5,
        	-buttons   => [
            	{ 
              		-label => '< Stop >',
              		-value => 1,
              		-shortcut => 1,
			-onpress => sub { my $ret = &confirm_dialog("Are you sure you want to STOP Web Server?");
						if ($ret){
    							my @run = `(/etc/init.d/cherokee stop &) > /dev/null`;
							&inform_dialog('Service already stopped');
							$zlbmenu->focus();
							$zlbmenu->set_selection(1);
							&manage_sel(); 
						}
					}, 
            	},
	    	{ 
              		-label => '< Start >',
              		-value => 2,
              		-shortcut => 2,
			-onpress => sub { my $ret = &confirm_dialog("Are you sure you want to START Web Server?");
						if ($ret){
    							my @run = `(/etc/init.d/cherokee start &) > /dev/null`;
							&inform_dialog('Service already started');
							$zlbmenu->focus();
							$zlbmenu->set_selection(1);
							&manage_sel();  
						}
					}, 
            	},
	    	{ 
              		-label => '< Restart >',
              		-value => 3,
              		-shortcut => 3,
			-onpress => sub { my $ret = &confirm_dialog("Are you sure you want to RESTART Web Server?");
						if ($ret){
    							my @run = `(/etc/init.d/cherokee restart &) > /dev/null`;
							&inform_dialog('Service already restarted');
							$zlbmenu->focus();
							$zlbmenu->set_selection(1);
							&manage_sel(); 
						}
					}, 
            	}
        	],
	);

	my $service2 = $win3->add(
		'win3id3', 'Buttonbox',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-title => 'ZEVENET Service Manager',
		-border => 1,
		-y => 8,
        	-buttons   => [
            	{ 
              		-label => '< Stop >',
              		-value => 1,
              		-shortcut => 1,
			-onpress => sub { my $ret = &confirm_dialog("Are you sure you want to STOP Zenloadbalancer service?");
						if ($ret){
    							my @run = `(/etc/init.d/zenloadbalancer stop &) > /dev/null`;
							&inform_dialog('Service already stopped');
							$zlbmenu->focus();
							$zlbmenu->set_selection(1);
							&manage_sel(); 
						}
					}, 
            	},
	    	{ 
              		-label => '< Start >',
              		-value => 2,
              		-shortcut => 2,
			-onpress => sub { my $ret = &confirm_dialog("Are you sure you want to START ZEVENET service?");
						if ($ret){
    							my @run = `(/etc/init.d/zenloadbalancer start &) > /dev/null`;
							&inform_dialog('Service already started');
							$zlbmenu->focus();
							$zlbmenu->set_selection(1);
							&manage_sel(); 
						}
					}, 
            	},
	    	{ 
              		-label => '< Restart >',
              		-value => 3,
              		-shortcut => 3,
			-onpress => sub { my $ret = &confirm_dialog("Are you sure you want to RESTART ZEVENET service?");
						if ($ret){
    							my @run = `(/etc/init.d/zenloadbalancer restart &) > /dev/null`;
							&inform_dialog('Service already restarted');
							$zlbmenu->focus();
							$zlbmenu->set_selection(1);
							&manage_sel(); 
						}
					}, 
            	}
        	],
	);

	my $refresh = $win3->add(
		'win3id4', 'Buttonbox',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-y => 11,
		-selected => 1,
        	-buttons   => [
            	{ 
              		-label => '< Refresh >',
              		-value => 1,
              		-shortcut => 1,
			-onpress => sub { refresh_win3(); }, 
            	},
		{ 
              		-label => '< Cancel >',
              		-value => 2,
              		-shortcut => 2,
			-onpress => sub { $zlbmenu->focus(); }, 
            	},
        	],
	);

	$refresh->focus();

}

sub manage_zlb_hostname(){
	$zlbhostname = `hostname`;
	chomp $zlbhostname;
	$zlbhostinput = $win3->add( 
	        'win3id1', 'TextEntry',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-border => 1,
		-y => 1,
		-title => 'Hostname Configuration', 
	    	-text => $zlbhostname,
	);
    	my $confirm = $win3->add(
		'win3id2', 'Buttonbox',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-y => 5,
		-selected => 1,
        	-buttons   => [
            	{ 
              		-label => '< Save >',
              		-value => 1,
              		-shortcut => 1,
			-onpress => sub { &set_new_hostname();  }, 
            	},
	    	{ 
              		-label => '< Cancel >',
              		-value => 2,
              		-shortcut => 2,
			-onpress => sub { $zlbmenu->focus(); },
            	},
        	],
	);
	$confirm->focus();
}

sub set_new_hostname(){
	if ($zlbhostinput){
		my $ret = &confirm_dialog("Are you sure you want to change your ZEVENET hostname?");
		if ($ret){
    			my $newhost = $zlbhostinput->get();
			if ($newhost && $newhost ne $zlbhostname){
			        my @run = `echo $newhost > /etc/hostname`;
			        @run = `hostname $newhost`;
			}
			else{
				&error_dialog("Hostname has not changed or is empty. Changes are not applied.");
			} 
			&refresh_win3();
		}
	}
}

sub show_status_system()
{
	my @memdata       = &get_system_mem();
	my $memstring     = &set_data_string( @memdata );
	my @loadavgdata   = &get_system_loadavg();
	my $loadavgstring = &set_data_string( @loadavgdata );
	my @cpudata       = &get_system_cpu();
	my $cpustring     = &set_data_string( @cpudata );
	my $zlbversion    = &getGlobalConfiguration('version');
	my $zaversion     = &getApplianceVersion();
	my $ncores = 1 + `grep processor /proc/cpuinfo | tail -1 | awk '{printf \$3}'`;
	$zlbhostname = `hostname`;
	chomp $zlbhostname;

	my $refresh = $win3->add(
		'win3id1', 'Buttonbox',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-y => 1,
		-selected => 1,
        	-buttons   => [
            	{ 
              		-label => '< Refresh >',
              		-value => 1,
              		-shortcut => 1,
			-onpress => sub { refresh_win3(); }, 
            	},
		{ 
              		-label => '< Cancel >',
              		-value => 2,
              		-shortcut => 2,
			-onpress => sub { $zlbmenu->focus(); }, 
            	},
        	],
	);

	my $textviewer = $win3->add( 
        'win3id2', 'TextViewer',
	-bg => 'black',
	-border => 1,
	-y => 3,
	-vscrollbar => 1,
    	-text => "\nAppliance Version:\n"
		. "\t" . $zaversion . "\n"
		. "\nSoftware Version:\n"
		. "\t" . $zlbversion . "\n"
		. "\nHostname:\n"
		. "\t" . $zlbhostname . "\n"
		. "\nMemory (MB):\n"
               	. $memstring
		. "\nLoad AVG:\n"
		. $loadavgstring
		. "\nNumber of CPU cores:\n"
		. "\t" . $ncores . "\n"
		. "\nCPU Usage (%):\n"
		. $cpustring,
    	);

    	$refresh->focus();

}

sub create_win3(){
	my ($title) = @_;
	$win3 = $win1->add(
		'win3', 'Window',
		-border	=> 1,
		-bfg 	=> 'green',
		-fg 	=> 'white',
		-tfg	=> 'white',
		-tbg	=> 'black',
		-x 	=> 26,
		-title 	=> $title,
	);
}

$zenui->set_binding(sub {$zlbmenu->focus()}, "\cX");
$zenui->set_binding( \&exit_dialog , "\cQ");

$zenui->mainloop();
