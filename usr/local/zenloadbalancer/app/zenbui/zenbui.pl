#!/usr/bin/perl -w
###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
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


#use strict;
use Curses::UI;
my $globalcfg = "/usr/local/zenloadbalancer/config/global.conf";
require "/usr/local/zenloadbalancer/www/functions.cgi";
require "/usr/local/zenloadbalancer/app/zenbui/buifunctions.pl";
require ($globalcfg);


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
	-title		=> 'Zen Load Balancer Basic User Interface',
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
	-title	=> 'ZLB Main Menu',
);

$zlbmenu = $win2->add(
	'win2id1', 'Listbox',
	-selectmode => 'single',
	-fg => 'white',
	-bg => 'black',
        -values    => [1, 2, 3, 4, 5, 6, 7, 8],
        -labels    => { 1 => 'ZLB Status',
			2 => 'ZLB Services', 
                       	3 => 'ZLB Hostname',
			4 => 'ZLB MGMT Interface',
			5 => 'ZLB Time Zone',
			6 => 'ZLB Keyboard Map',
			7 => 'ZLB Reboot/Shutdown',
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
        -title  	=> 'Zen Load Balancer Basic User Interface Help:',
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
                     -title     	=> "ZLB Exit Confirmation", 
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
                     -title     	=> "ZLB Confirmation", 
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
                     -title     	=> "ZLB Information", 
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
                     -title     => "ZLB Warning", 
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
			&create_win3('Zen Load Balancer Status');
			&show_status_system();
		}
		elsif ($selected == 2){
			&create_win3('Zen Load Balancer Services');
			&manage_zlb_services();
		}
		elsif ($selected == 3){
			&create_win3('Zen Load Balancer Hostname');
			&manage_zlb_hostname();
		}
		elsif ($selected == 4){
			&create_win3('Zen Load Balancer MGMT Interface');
			&manage_mgmt();
		}
		elsif ($selected == 5){
			&create_win3('Zen Load Balancer Time Zone');
			&manage_timezone();
		}
		elsif ($selected == 6){
			&create_win3('Zen Load Balancer Keyboard Layout');
			&manage_keyboard();
		}
		elsif ($selected == 7){
			&create_win3('Zen Load Balancer Reboot/Shutdown');
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
		-title => 'ZLB Power Manager',
		-border => 1,
		-y => 1,
		-selected => 2,
        	-buttons   => [
            	{ 
              		-label => '< Reboot >',
              		-value => 1,
              		-shortcut => 1,
			-onpress => 	sub { my $ret = &confirm_dialog("Are you sure you want to reboot your Zen Load Balancer?");
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
			-onpress => 	sub { my $ret = &confirm_dialog("Are you sure you want to shutdown your Zen Load Balancer?");
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
		-title => 'ZLB Keyboard Layout Configuration', 
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
		-title => 'ZLB Time Zone Configuration', 
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
	my @interfaces = `ifconfig -a | grep ' Link' | awk {'print \$1'} | grep -v lo | grep -v ':'`;
	my $i=0;
	my $mgmtindex = 0;
	foreach (@interfaces){
        	chomp($_);
		$interfaces[$i] = $_;
		if ( $_ eq "mgmt" ){
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
		-title => 'ZLB Available Interfaces List',
		-vscrollbar => 1,
		-onchange => sub {
					$mgmtif = $mgmtifinput->get();
					$mgmtip = `ifconfig $mgmtif | awk -F'inet addr:' '{print \$2}' | awk '{printf \$1}'`;
					if ($mgmtipinput){
						$mgmtipinput->text($mgmtip);
					}
					$mgmtmask = `ifconfig $mgmtif | awk -F'Mask:' '{printf \$2}'`;
					if ($mgmtmaskinput){
						$mgmtmaskinput->text($mgmtmask);
					}
					$mgmtgw =`ip route show | grep default | awk '{printf \$3}'`;
					if ($mgmtgwinput){
						$mgmtgwinput->text($mgmtgw);
					}
				},
		);
	$mgmtifinput->focus();
	$mgmtifinput->set_selection($mgmtindex);
	$mgmtif = $mgmtifinput->get();
	$mgmtip = `ifconfig $mgmtif | awk -F'inet addr:' '{print \$2}' | awk '{printf \$1}'`;
	$mgmtmask = `ifconfig eth0 | awk -F'Mask:' '{printf \$2}'`;
	$mgmtgw =`ip route show | grep default | awk '{printf \$3}'`;


	$mgmtipinput = $win3->add(
	        'win3id2', 'TextEntry',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-border => 1,
		-y => 4,
		-title => 'ZLB MGMT IP Configuration', 
	    	-text => $mgmtip,
	);

	$mgmtmaskinput = $win3->add( 
	        'win3id3', 'TextEntry',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-border => 1,
		-y => 7,
		-title => 'ZLB MGMT NetMask Configuration', 
	    	-text => $mgmtmask,
	);

	$mgmtgwinput = $win3->add( 
	        'win3id4', 'TextEntry',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-border => 1,
		-y => 10,
		-title => 'ZLB MGMT GateWay Configuration', 
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
	if ($mgmtifinput && $mgmtipinput && $mgmtmaskinput && $mgmtgwinput){
		my $newif = $mgmtifinput->get();
    		my $newip = $mgmtipinput->get();
    		my $newmask = $mgmtmaskinput->get();
    		my $newgw = $mgmtgwinput->get();

		if (&ipisok($newip) eq "false") {
        		&error_dialog("IP Address $newip structure is not ok");
        		$setchanges = 0;
        	}
		# check if the new netmask is correct, if empty don't worry
		if ( $newmask !~ /^$/ && &ipisok($newmask) eq "false"){
        		&error_dialog("Netmask address $newmask structure is not ok");
        		$setchanges = 0;
        	}
		# check if the new gateway is correct, if empty don't worry
		if ( $newgw !~ /^$/ && &ipisok($newgw) eq "false"){
        		&inform_dialog("Gateway address $newgw structure is not ok, set it in the web GUI");
			$newgw = "";
        	}
		if ($setchanges){
			my $ret = &confirm_dialog("Are you sure you want to change your Zen Load Balancer MGMT Interface?");
			if ($ret){
				&createIf($newif);
	        		&delRoutes("local",$newif);
	        		&logfile("running '$ifconfig_bin $newif $newip netmask $newmask' ");
	        		@eject = `$ifconfig_bin $newif $newip netmask $newmask 2> /dev/null`;
	        		&upIf($newif);
	        		$state = $?;
	        		if ($state == 0){
	                		$status = "up";
	                		&inform_dialog("Network interface $newif is now UP");
	                		&writeRoutes($newif);
	                		&writeConfigIf($newif,"$newif\:\:$newip\:$newmask\:$status\:$newgw\:");
	                		&applyRoutes("local",$newif,$newgw);
	                		#apply the GW to default gw. 
	                		&applyRoutes("global",$newif,$newgw);
	                		#apply the GW to default gw. 
	                		&applyRoutes("global",$newif,$newgw);
					&inform_dialog("All is ok, saved $newif interface config file");
	                		&inform_dialog("If this is your first boot you can access to Zen Web GUI through\nhttps://$newip:444\nwith user root and password admin,\nremember to change the password for security reasons in web GUI.");
	         		} else {
	                		&error_dialog("A problem is detected configuring $newif interface, you have to configure your $newif \nthrough command line and after save the configuration in the web GUI");
	         		}
			}
		}
		&refresh_win3();
	}		
}

sub manage_zlb_services(){
	my @services=('cherokee', 'zenloadbalancer');
	my $cherokeedstatus = "STOPPED";
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
		-title => 'ZLB Services Status', 
	    	-text => "Zen Load Balancer Services:\n"
			. "\tZLB Web Service:\t"
			. $cherokeestatus . "\n"
			. "\tZenloadbalancer:\t"
			. $zlbservicestatus . "\n",
	);

	my $service1 = $win3->add(
		'win3id2', 'Buttonbox',
		-bg => 'black',
		-tfg => 'black',
		-tbg => 'white',
		-title => 'ZLB Web Service Manager',
		-border => 1,
		-y => 5,
        	-buttons   => [
            	{ 
              		-label => '< Stop >',
              		-value => 1,
              		-shortcut => 1,
			-onpress => sub { my $ret = &confirm_dialog("Are you sure you want to STOP ZLB Web Server?");
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
			-onpress => sub { my $ret = &confirm_dialog("Are you sure you want to START ZLB Web Server?");
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
			-onpress => sub { my $ret = &confirm_dialog("Are you sure you want to RESTART ZLB Web Server?");
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
		-title => 'ZLB Zenloadbalancer Service Manager',
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
			-onpress => sub { my $ret = &confirm_dialog("Are you sure you want to START Zenloadbalancer service?");
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
			-onpress => sub { my $ret = &confirm_dialog("Are you sure you want to RESTART Zenloadbalancer service?");
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
		-title => 'ZLB Hostname Configuration', 
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
		my $ret = &confirm_dialog("Are you sure you want to change your Zen Load Balancer hostname?");
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
	my @memdata = &get_system_mem();
	my $memstring = &set_data_string(@memdata);
	my @loadavgdata = &get_system_loadavg();
	my $loadavgstring = &set_data_string(@loadavgdata);
	my @cpudata = &get_system_cpu();
	my $cpustring = &set_data_string(@cpudata);
	my $zlbversion = $version;
	my $zaversion = `dpkg -l | grep zen | awk '{printf \$3}'`;
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
    	-text => "\nZLB Appliance Version:\n"
		. "\tZen Load Balancer EE " . $zaversion . "\n"
		. "\nZLB Software Version:\n"
		. "\t" . $zlbversion . "\n"
		. "\nZLB Hostname:\n"
		. "\t" . $zlbhostname . "\n"
		. "\nZLB Memory (MB):\n"
               	. $memstring
		. "\nZLB Load AVG:\n"
		. $loadavgstring
		. "\nZLB Number of CPU cores:\n"
		. "\t" . $ncores . "\n"
		. "\nZLB CPU Usage (%):\n"
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

