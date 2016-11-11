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

use Curses::UI;
require "/usr/local/zenloadbalancer/config/global.conf";
require "/usr/local/zenloadbalancer/www/functions.cgi";
require "/usr/local/zenloadbalancer/app/zenbui/buifunctions.pl";

my $zlbmenu;
my $win3;
my $winhelp;
my $zlbhostinput;
my ( $mgmt_if, $mgmt_ip, $mgmt_mask, $mgmt_gw, $mgmt_index, $ip_version );
my ( $mgmt_if_input, $mgmt_ip_input, $mgmt_mask_input, $mgmt_gw_input );

my $zenui = new Curses::UI( -color_support => 1,
							-clear_on_exit => 1, );

my $zlbhostname = `hostname`;
chomp $zlbhostname;

my $win1 = $zenui->add(
						'win1', 'Window',
						-border       => 1,
						-y            => 0,
						-padbottom    => 4,
						-bfg          => 'green',
						-bg           => 'white',
						-tfg          => 'white',
						-tbg          => 'green',
						-title        => 'Zen Load Balancer Basic User Interface',
						-titlereverse => 0,
);

my $win2 = $win1->add(
					   'win2', 'Window',
					   -border => 1,
					   -bfg    => 'green',
					   -bg     => 'white',
					   -width  => 25,
					   -tfg    => 'white',
					   -tbg    => 'black',
					   -title  => 'ZLB Main Menu',
);

$zlbmenu = $win2->add(
					   'win2id1',
					   'Listbox',
					   -selectmode => 'single',
					   -fg         => 'white',
					   -bg         => 'black',
					   -values     => [1, 2, 3, 4, 5, 6, 7, 8],
					   -labels     => {
									1 => 'ZLB Status',
									2 => 'ZLB Services',
									3 => 'ZLB Hostname',
									4 => 'ZLB MGMT Interface',
									5 => 'ZLB Time Zone',
									6 => 'ZLB Keyboard Map',
									7 => 'ZLB Reboot/Shutdown',
									8 => 'Exit to shell',
					   },
					   -onchange => \&manage_sel,
);

#~ $zlbmenu->focus();
$zlbmenu->set_selection( 0 );
$zlbmenu->focus();

$winhelp = $zenui->add(
						'winhelp', 'Window',
						-bg     => 'white',
						-y      => -1,
						-height => 4,
);

my $help = $winhelp->add(
	'zlbhelp', 'TextViewer',
	-bg     => 'black',
	-title  => 'Zen Load Balancer Basic User Interface Help:',
	-tfg    => 'white',
	-tbg    => 'black',
	-bfg    => 'green',
	-border => 1,
	-text =>
	  "Ctrl+Q = Exit, Ctrl+X = Main menu, Arrows = Move into the item,\nTab = Change to next item, Intro = Select.\n"
);

sub exit_dialog
{
	my $return = $zenui->dialog(
								 -message  => "Do you really want to exit to shell?",
								 -title    => "ZLB Exit Confirmation",
								 -buttons  => ['yes', 'no'],
								 -selected => 1,
								 -bfg      => 'green',
								 -fg       => 'white',
								 -bg       => 'black',
								 -tfg      => 'white',
								 -tbg      => 'green',
								 -titlereverse => 0,
	);
	if ( $return )
	{
		exit ( 0 );
	}
}

sub confirm_dialog
{
	my ( $message ) = @_;
	my $return = $zenui->dialog(
								 -message      => $message,
								 -title        => "ZLB Confirmation",
								 -buttons      => ['yes', 'no'],
								 -selected     => 1,
								 -bfg          => 'green',
								 -fg           => 'white',
								 -bg           => 'black',
								 -tfg          => 'white',
								 -tbg          => 'green',
								 -titlereverse => 0,
	);

	return $return;
}

sub inform_dialog
{
	my ( $message ) = @_;
	my $return = $zenui->dialog(
								 -message      => $message,
								 -title        => "ZLB Information",
								 -buttons      => ['ok'],
								 -bfg          => 'green',
								 -fg           => 'white',
								 -bg           => 'black',
								 -tfg          => 'white',
								 -tbg          => 'green',
								 -titlereverse => 0,
	);
	return $return;
}

sub error_dialog
{
	my ( $message ) = @_;
	my $return = $zenui->dialog(
								 -message      => $message,
								 -title        => "ZLB Warning",
								 -buttons      => ['ok'],
								 -bfg          => 'red',
								 -fg           => 'white',
								 -bg           => 'black',
								 -tfg          => 'white',
								 -tbg          => 'red',
								 -titlereverse => 0,
	);
	return $return;
}

sub refresh_win3
{
	$zlbmenu->focus();
	&manage_sel();
}

sub manage_sel
{
	if ( $win3 )
	{
		$win1->delete( 'win3' );
	}
	my $selected = 0;
	$selected = $zlbmenu->get();
	if ( $selected )
	{
		if ( $selected == 1 )
		{
			&create_win3( 'Zen Load Balancer Status' );
			&show_status_system();
		}
		elsif ( $selected == 2 )
		{
			&create_win3( 'Zen Load Balancer Services' );
			&manage_zlb_services();
		}
		elsif ( $selected == 3 )
		{
			&create_win3( 'Zen Load Balancer Hostname' );
			&manage_zlb_hostname();
		}
		elsif ( $selected == 4 )
		{
			&create_win3( 'Zen Load Balancer MGMT Interface' );
			&manage_mgmt();
		}
		elsif ( $selected == 5 )
		{
			&create_win3( 'Zen Load Balancer Time Zone' );
			&manage_timezone();
		}
		elsif ( $selected == 6 )
		{
			&create_win3( 'Zen Load Balancer Keyboard Layout' );
			&manage_keyboard();
		}
		elsif ( $selected == 7 )
		{
			&create_win3( 'Zen Load Balancer Reboot/Shutdown' );
			&manage_power();
		}
		elsif ( $selected == 8 )
		{
			\&exit_dialog();
		}
	}
}

sub manage_power
{
	my $power = $win3->add(
		'win3id2',
		'Buttonbox',
		-bg       => 'black',
		-tfg      => 'black',
		-tbg      => 'white',
		-title    => 'ZLB Power Manager',
		-border   => 1,
		-y        => 1,
		-selected => 2,
		-buttons  => [
			{
			   -label    => '< Reboot >',
			   -value    => 1,
			   -shortcut => 1,
			   -onpress  => sub {
				   my $ret =
					 &confirm_dialog( "Are you sure you want to reboot your Zen Load Balancer?" );
				   if ( $ret )
				   {
					   my @run = `(reboot &)`;
					   exit ( 0 );
				   }
			   },
			},
			{
			   -label    => '< Shutdown >',
			   -value    => 2,
			   -shortcut => 2,
			   -onpress  => sub {
				   my $ret =
					 &confirm_dialog( "Are you sure you want to shutdown your Zen Load Balancer?" );
				   if ( $ret )
				   {
					   my @run = `(poweroff &)`;
					   exit ( 0 );
				   }
			   },
			},
			{
			   -label    => '< Cancel >',
			   -value    => 3,
			   -shortcut => 3,
			   -onpress  => sub { $zlbmenu->focus(); },
			},
		],
	);
	$power->focus();
}

sub manage_keyboard
{
	my $line;
	my $keyboardfile = "/etc/default/keyboard";
	my ( $keyboard, $zlbkeyboard );
	if ( -f $keyboardfile )
	{
		open FR, $keyboardfile;

		while ( $line = <FR> )
		{
			if ( $line =~ 'XKBLAYOUT' )
			{
				$keyboard = $line;
			}
		}
		close FR;
	}
	$zlbkeyboard = $win3->add(
							   'win3id1', 'TextEntry',
							   -bg       => 'black',
							   -tfg      => 'black',
							   -tbg      => 'white',
							   -border   => 1,
							   -y        => 1,
							   -title    => 'ZLB Keyboard Layout Configuration',
							   -text     => $keyboard,
							   -readonly => 1,
	);
	my $confirm = $win3->add(
		'win3id2',
		'Buttonbox',
		-bg       => 'black',
		-tfg      => 'black',
		-tbg      => 'white',
		-y        => 5,
		-selected => 1,
		-buttons  => [
			{
			   -label    => '< Change >',
			   -value    => 1,
			   -shortcut => 1,
			   -onpress  => sub {
				   system ( 'dpkg-reconfigure keyboard-configuration' );
				   $zenui->reset_curses();
				   &inform_dialog( "You have to reboot the host to apply the changes." );
				   &refresh_win3();
			   },
			},
			{
			   -label    => '< Cancel >',
			   -value    => 2,
			   -shortcut => 2,
			   -onpress  => sub { $zlbmenu->focus(); },
			},
		],
	);
	$confirm->focus();
}

sub manage_timezone
{
	my $line;
	my $timezonefile = "/etc/timezone";
	my ( $timezone, $zlbtimezone );
	if ( -f $timezonefile )
	{
		open FR, $timezonefile;

		while ( $line = <FR> )
		{
			$timezone = $line;
		}
		close FR;
	}
	$zlbtimezone = $win3->add(
							   'win3id1', 'TextEntry',
							   -bg       => 'black',
							   -tfg      => 'black',
							   -tbg      => 'white',
							   -border   => 1,
							   -y        => 1,
							   -title    => 'ZLB Time Zone Configuration',
							   -text     => $timezone,
							   -readonly => 1,
	);
	my $confirm = $win3->add(
		'win3id2',
		'Buttonbox',
		-bg       => 'black',
		-tfg      => 'black',
		-tbg      => 'white',
		-y        => 5,
		-selected => 1,
		-buttons  => [
			{
			   -label    => '< Change >',
			   -value    => 1,
			   -shortcut => 1,
			   -onpress  => sub {           #$zenui->leave_curses();
				   system ( 'dpkg-reconfigure tzdata' );
				   $zenui->reset_curses();
				   my @run = `(ntpdate pool.ntp.org &) > /dev/null`;

				   #$zenui->reset_curses();
				   &inform_dialog( "Synchronizing time with pool.ntp.org..." );
				   &refresh_win3();
			   },
			},
			{
			   -label    => '< Cancel >',
			   -value    => 2,
			   -shortcut => 2,
			   -onpress  => sub { $zlbmenu->focus(); },
			},
		],
	);
	$confirm->focus();
}

sub manage_mgmt
{
	my @interfaces =
	  `ifconfig -a | grep ' Link' | awk {'print \$1'} | grep -v lo | grep -v ':'`;
	chomp ( @interfaces );

	my $offset_x = 14;

	$mgmt_if    = $mgmt_if    // $interfaces[0];
	$mgmt_index = $mgmt_index // 0;                # default interface
	$ip_version = $ip_version // 4;
	$ipv_height = 4;

	my $i = 0;

	foreach my $interface ( @interfaces )
	{
		if ( $interface eq "mgmt" )
		{
			$mgmt_index = $i;
		}

		$i++;
	}

	#~ my $ip_version_listbox = $win3->add(
		#~ 'IPversion_select',
		#~ 'Listbox',
		#~ -title  => 'IP version',
		#~ -height => 4,
		#~ -values => \@interfaces,
		#~ -title => 'ZLB Available Interfaces List',
		#~ -vscrollbar => 1,
		#~ -onchange => sub {
					#~ $mgmt_if = $mgmt_if_input->get();
					#~ $mgmt_ip = `ifconfig $mgmt_if | awk -F'inet addr:' '{print \$2}' | awk '{printf \$1}'`;
					#~ if ($mgmtipinput){
						#~ $mgmtipinput->text($mgmt_ip);
					#~ }
					#~ $mgmt_mask = `ifconfig $mgmt_if | awk -F'Mask:' '{printf \$2}'`;
					#~ if ($mgmtmaskinput){
						#~ $mgmtmaskinput->text($mgmt_mask);
					#~ }
					#~ $mgmt_gw =`ip route show | grep default | awk '{printf \$3}'`;
					#~ if ($mgmtgwinput){
						#~ $mgmtgwinput->text($mgmt_gw);
					#~ }
				#~ },
		#~ );

	$mgmt_ip = `ifconfig $mgmt_if | awk -F'inet addr:' '{print \$2}' | awk '{printf \$1}'`;
	$mgmt_mask = `ifconfig $mgmt_if | awk -F'Mask:' '{printf \$2}'`;
	$mgmt_gw =`ip route show | grep default | awk '{printf \$3}'`;

	$mgmt_if_input = $win3->add(
		'win3id1',
		'Listbox',
		-bg         => 'black',
		-tfg        => 'black',
		-tbg        => 'white',
		-border     => 1,
		-vscrollbar => 1,
		-y          => 4 - $ipv_height,
		-height     => 4,
		-values     => \@interfaces,
		-title      => 'ZLB Available Interfaces List',
		-selected   => $mgmt_index,
		-radio      => 1,
		-onchange   => sub {
			$mgmt_if    = $mgmt_if_input->get();
			$mgmt_index = $mgmt_if_input->get_active_id();

			( $mgmt_ip, $mgmt_mask, $mgmt_gw ) =
			  &get_interface_stack_ip_mask_gateway( $mgmt_if, $ip_version );

			if ( defined $mgmt_ip_input )
			{
				$mgmt_ip_input->text( $mgmt_ip );
			}

			if ( defined $mgmt_mask_input )
			{
				$mgmt_mask_input->text( $mgmt_mask );
			}

			if ( defined $mgmt_gw_input )
			{
				$mgmt_gw_input->text( $mgmt_gw );
			}

			#~ &zenlog("mgmt_index:$mgmt_index");
			#~ &zenlog("mgmt_if:$mgmt_if");
			#~ &zenlog("mgmt_ip:$mgmt_ip");
			#~ &zenlog("mgmt_mask:$mgmt_mask");
			#~ &zenlog("mgmt_gw:$mgmt_gw");
		},
	);

	$mgmt_if_input->focus();
	$mgmt_if_input->set_selection($mgmt_index);
	$mgmt_if = $mgmt_if_input->get();
	#~ $mgmt_ip = `ifconfig $mgmt_if | awk -F'inet addr:' '{print \$2}' | awk '{printf \$1}'`;
	#~ $mgmt_mask = `ifconfig $mgmt_if | awk -F'Mask:' '{printf \$2}'`;
	#~ $mgmt_gw =`ip route show | grep default | awk '{printf \$3}'`;

	&zenlog("mgmt_if:$mgmt_if");
	&zenlog("mgmt_ip:$mgmt_ip");
	&zenlog("mgmt_mask:$mgmt_mask");
	&zenlog("mgmt_gw:$mgmt_gw");

	#~ $mgmtipinput = $win3->add(
        #~ 'win3id2', 'TextEntry',
		#~ -bg => 'black',
		#~ -tfg => 'black',
		#~ -tbg => 'white',
		#~ -border => 1,
		#~ -bg     => 'black',
		#~ -tfg    => 'black',
		#~ -tbg    => 'white',
		#~ -values => [4, 6],
		#~ -labels => {
					 #~ 4 => 'IPv4',
					 #~ 6 => 'IPv6'
		#~ },
		#~ -selected => ( $ip_version == 6 ) ? 1 : 0,
		#~ -radio    => 1,
		#~ -onchange => sub {
			#~ my $listbox = shift;
			#~ $ip_version = $listbox->get;
#~ 
			#~ ( $mgmt_ip, $mgmt_mask, $mgmt_gw ) =
			  #~ &get_interface_stack_ip_mask_gateway( $mgmt_if, $ip_version );
#~ 
			#~ if ( $mgmt_ip_input )
			#~ {
				#~ $mgmt_ip_input->text( $mgmt_ip );
			#~ }
#~ 
			#~ if ( $mgmt_mask_input )
			#~ {
				#~ $mgmt_mask_input->text( $mgmt_mask );
			#~ }
#~ 
			#~ if ( $mgmt_gw_input )
			#~ {
				#~ $mgmt_gw_input->text( $mgmt_gw );
			#~ }
		#~ }
	#~ );

	#~ $mgmt_if_input = $win3->add(
		#~ 'win3id1',
		#~ 'Listbox',
		#~ -bg         => 'black',
		#~ -tfg        => 'black',
		#~ -tbg        => 'white',
		#~ -border     => 1,
		#~ -vscrollbar => 1,
		#~ -y          => 4 - $ipv_height,
		#~ -height     => 4,
		#~ -values     => \@interfaces,
		#~ -title      => 'ZLB Available Interfaces List',
		#~ -selected   => $mgmt_index,
		#~ -radio      => 1,
		#~ -onchange   => sub {
			#~ $mgmt_if    = $mgmt_if_input->get();
			#~ $mgmt_index = $mgmt_if_input->get_active_id();
#~ 
			#~ ( $mgmt_ip, $mgmt_mask, $mgmt_gw ) =
			  #~ &get_interface_stack_ip_mask_gateway( $mgmt_if, $ip_version );
#~ 
			#~ if ( defined $mgmt_ip_input )
			#~ {
				#~ $mgmt_ip_input->text( $mgmt_ip );
			#~ }
#~ 
			#~ if ( defined $mgmt_mask_input )
			#~ {
				#~ $mgmt_mask_input->text( $mgmt_mask );
			#~ }
#~ 
			#~ if ( defined $mgmt_gw_input )
			#~ {
				#~ $mgmt_gw_input->text( $mgmt_gw );
			#~ }
		#~ },
	#~ );

	$mgmt_if_input->focus();
	$mgmt_if_input->set_selection( $mgmt_index );
	$mgmt_if = $mgmt_if_input->get();

	if ( not defined $mgmt_ip || not defined $mgmt_mask || not defined $mgmt_mask )
	{
		( $mgmt_ip, $mgmt_mask, $mgmt_gw ) =
		  &get_interface_stack_ip_mask_gateway( $mgmt_if, $ip_version );
	}

	my $label1 = $win3->add(
							 'IP', 'Label',
							 -text => 'IP Address',
							 -y    => 9 - $ipv_height,
	);

	$mgmt_ip_input = $win3->add(
								 'win3id2', 'TextEditor',
								 -bg         => 'black',
								 -tfg        => 'black',
								 -tbg        => 'white',
								 -border     => 0,
								 -y          => 9 - $ipv_height,
								 -title      => 'IP',
								 -text       => $mgmt_ip,
								 -singleline => 1,
								 -x          => $offset_x,
								 -sbborder   => 1,
	);

	my $label2 = $win3->add(
							 'Netmask', 'Label',
							 -text => 'Netmask',
							 -y    => 10 - $ipv_height,
	);

	$mgmt_mask_input = $win3->add(
								   'win3id3', 'TextEditor',
								   -bg         => 'black',
								   -tfg        => 'black',
								   -tbg        => 'white',
								   -border     => 0,
								   -y          => 10 - $ipv_height,
								   -title      => 'Netmask',
								   -text       => $mgmt_mask,
								   -singleline => 1,
								   -x          => $offset_x,
								   -sbborder   => 1,
	);

	my $label3 = $win3->add(
							 'Gateway', 'Label',
							 -text => 'Gateway',
							 -y    => 11 - $ipv_height,
	);

	$mgmt_gw_input = $win3->add(
								 'win3id4', 'TextEditor',
								 -bg         => 'black',
								 -tfg        => 'black',
								 -tbg        => 'white',
								 -border     => 0,
								 -y          => 11 - $ipv_height,
								 -title      => 'Gateway',
								 -text       => $mgmt_gw,
								 -singleline => 1,
								 -x          => $offset_x,
								 -sbborder   => 1,
	);

	my $confirm = $win3->add(
							  'win3id5',
							  'Buttonbox',
							  -bg       => 'black',
							  -tfg      => 'black',
							  -tbg      => 'white',
							  -y        => 13 - $ipv_height,
							  -selected => 1,
							  -buttons  => [
										   {
											 -label    => '< Save >',
											 -value    => 1,
											 -shortcut => 1,
											 -onpress  => sub { &set_net(); },
										   },
										   {
											 -label    => '< Cancel >',
											 -value    => 2,
											 -shortcut => 2,
											 -onpress  => sub { $zlbmenu->focus(); },
										   },
							  ],
	);

	$confirm->focus();
}

sub set_net
{
	my $setchanges = 1;

	if ( $mgmt_if_input && $mgmt_ip_input && $mgmt_mask_input && $mgmt_gw_input )
	{
		# initialize interface hash reference
		my $if_ref;
		$$if_ref{ name }    = $mgmt_if_input->get();
		$$if_ref{ addr }    = $mgmt_ip_input->get();
		$$if_ref{ mask }    = $mgmt_mask_input->get();
		$$if_ref{ gateway } = $mgmt_gw_input->get();
		$$if_ref{ dev }     = $$if_ref{ name };
		$$if_ref{ ip_v }    = &ipversion( $$if_ref{ addr } );
		$$if_ref{ status }  = 'up';

		if ( &ipisok( $$if_ref{ addr }, 4 ) eq "false" )
		{
			&error_dialog( "IP Address $$if_ref{addr} structure is not ok" );
			$setchanges = 0;
		}

		# check if the new netmask is correct, if empty don't worry
		if (    $$if_ref{ mask } ne ''
			 && &ipisok( $$if_ref{ mask }, 4 ) eq "false"
			 && ( $$if_ref{ mask } < 0 || $$if_ref{ mask } > 128 ) )
		{
			&error_dialog( "Netmask address $$if_ref{ mask } structure is not ok" );
			$setchanges = 0;
		}

		# check if the new gateway is correct, if empty don't worry
		if ( $$if_ref{ gateway } !~ /^$/ && &ipisok( $$if_ref{ gateway }, 4 ) eq "false" )
		{
			&inform_dialog(
				"Gateway address $$if_ref{ gateway } structure is not ok, set it in the web GUI"
			);
			$$if_ref{ gateway } = "";
		}
		if ( $setchanges )
		{
			my $ret = &confirm_dialog(
					 "Are you sure you want to change your Zen Load Balancer MGMT Interface?" );
			if ( $ret )
			{
				&createIf( $if_ref );

				# remove previous configuration
				my $prev_iface = &getInterfaceConfig( $if_ref->{name}, 4 );

				if ( 	$if_ref->{ addr } ne $prev_iface->{ addr }
					||	$if_ref->{ mask } ne $prev_iface->{ mask } )
				{
					&delRoutes( "local", $prev_iface );
					&delIp( $prev_iface->{name}, $prev_iface->{addr}, $prev_iface->{mask} );
					&addIp( $if_ref );
				}

				my $state = &upIf( $if_ref, 'writeconf' );

				if ( $state == 0 )
				{
					#~ $status = "up";
					&inform_dialog( "Network interface $$if_ref{name} is now UP" );
					&writeRoutes( $$if_ref{ name } );

					&applyRoutes( "local", $if_ref );

					#apply the GW to default gw.
					&applyRoutes( "global", $if_ref, $$if_ref{ gateway } );
					&setInterfaceConfig( $if_ref );
					&inform_dialog( "All is ok, saved $$if_ref{name} interface config file" );

					# if ip is v6 the format in browsers is [ip_address]
					my $ip_addr_format =
					  ( $$if_ref{ ip_v } == 6 ) ? "[$$if_ref{addr}]" : $$if_ref{ addr };

					&inform_dialog(
						"If this is your first boot you can access to Zen Web GUI through\nhttps://$ip_addr_format:444\nwith user root and password admin,\nremember to change the password for security reasons in web GUI."
					);

					# apply new values to variables used by the interface
					$mgmt_ip   = $$if_ref{ addr };
					$mgmt_mask = $$if_ref{ mask };
					$mgmt_gw   = $$if_ref{ gateway };
				}
				else
				{
					&error_dialog(
						"A problem is detected configuring $$if_ref{name} interface, you have to configure your $$if_ref{name} \nthrough command line and after save the configuration in the web GUI"
					);
				}
			}
		}
		&refresh_win3();
	}
}

sub manage_zlb_services
{
	my @services         = ( 'cherokee', 'zenloadbalancer' );
	my $cherokeedstatus  = "STOPPED";
	my $zlbservicestatus = "STOPPED";
	my @run              = `ps ex`;
	if ( grep ( /$services[0]/, @run ) )
	{
		$cherokeestatus = "ACTIVE";
	}
	@run = `ifconfig`;
	@run = grep ( !/^ /, @run );
	@run = grep ( !/^lo/, @run );
	if ( grep ( /^[a-z]/, @run ) )
	{
		$zlbservicestatus = "ACTIVE";
	}
	my $servicestatus = $win3->add(
									'win3id1', 'TextViewer',
									-bg         => 'black',
									-tfg        => 'black',
									-tbg        => 'white',
									-border     => 1,
									-y          => 0,
									-height     => 5,
									-vscrollbar => 1,
									-title      => 'ZLB Services Status',
									-text       => "Zen Load Balancer Services:\n"
									  . "\tZLB Web Service:\t"
									  . $cherokeestatus . "\n"
									  . "\tZenloadbalancer:\t"
									  . $zlbservicestatus . "\n",
	);

	my $service1 = $win3->add(
		'win3id2',
		'Buttonbox',
		-bg      => 'black',
		-tfg     => 'black',
		-tbg     => 'white',
		-title   => 'ZLB Web Service Manager',
		-border  => 1,
		-y       => 5,
		-buttons => [
			{
			   -label    => '< Stop >',
			   -value    => 1,
			   -shortcut => 1,
			   -onpress  => sub {
				   my $ret = &confirm_dialog( "Are you sure you want to STOP ZLB Web Server?" );
				   if ( $ret )
				   {
					   my @run = `(/etc/init.d/cherokee stop &) > /dev/null`;
					   &inform_dialog( 'Service already stopped' );
					   $zlbmenu->focus();
					   $zlbmenu->set_selection( 1 );
					   &manage_sel();
				   }
			   },
			},
			{
			   -label    => '< Start >',
			   -value    => 2,
			   -shortcut => 2,
			   -onpress  => sub {
				   my $ret = &confirm_dialog( "Are you sure you want to START ZLB Web Server?" );
				   if ( $ret )
				   {
					   my @run = `(/etc/init.d/cherokee start &) > /dev/null`;
					   &inform_dialog( 'Service already started' );
					   $zlbmenu->focus();
					   $zlbmenu->set_selection( 1 );
					   &manage_sel();
				   }
			   },
			},
			{
			   -label    => '< Restart >',
			   -value    => 3,
			   -shortcut => 3,
			   -onpress  => sub {
				   my $ret = &confirm_dialog( "Are you sure you want to RESTART ZLB Web Server?" );
				   if ( $ret )
				   {
					   my @run = `(/etc/init.d/cherokee restart &) > /dev/null`;
					   &inform_dialog( 'Service already restarted' );
					   $zlbmenu->focus();
					   $zlbmenu->set_selection( 1 );
					   &manage_sel();
				   }
			   },
			}
		],
	);

	my $service2 = $win3->add(
		'win3id3',
		'Buttonbox',
		-bg      => 'black',
		-tfg     => 'black',
		-tbg     => 'white',
		-title   => 'ZLB Zenloadbalancer Service Manager',
		-border  => 1,
		-y       => 8,
		-buttons => [
			{
			   -label    => '< Stop >',
			   -value    => 1,
			   -shortcut => 1,
			   -onpress  => sub {
				   my $ret =
					 &confirm_dialog( "Are you sure you want to STOP Zenloadbalancer service?" );
				   if ( $ret )
				   {
					   my @run = `(/etc/init.d/zenloadbalancer stop &) > /dev/null`;
					   &inform_dialog( 'Service already stopped' );
					   $zlbmenu->focus();
					   $zlbmenu->set_selection( 1 );
					   &manage_sel();
				   }
			   },
			},
			{
			   -label    => '< Start >',
			   -value    => 2,
			   -shortcut => 2,
			   -onpress  => sub {
				   my $ret =
					 &confirm_dialog( "Are you sure you want to START Zenloadbalancer service?" );
				   if ( $ret )
				   {
					   my @run = `(/etc/init.d/zenloadbalancer start &) > /dev/null`;
					   &inform_dialog( 'Service already started' );
					   $zlbmenu->focus();
					   $zlbmenu->set_selection( 1 );
					   &manage_sel();
				   }
			   },
			},
			{
			   -label    => '< Restart >',
			   -value    => 3,
			   -shortcut => 3,
			   -onpress  => sub {
				   my $ret =
					 &confirm_dialog( "Are you sure you want to RESTART Zenloadbalancer service?" );
				   if ( $ret )
				   {
					   my @run = `(/etc/init.d/zenloadbalancer restart &) > /dev/null`;
					   &inform_dialog( 'Service already restarted' );
					   $zlbmenu->focus();
					   $zlbmenu->set_selection( 1 );
					   &manage_sel();
				   }
			   },
			}
		],
	);

	my $refresh = $win3->add(
							  'win3id4',
							  'Buttonbox',
							  -bg       => 'black',
							  -tfg      => 'black',
							  -tbg      => 'white',
							  -y        => 11,
							  -selected => 1,
							  -buttons  => [
										   {
											 -label    => '< Refresh >',
											 -value    => 1,
											 -shortcut => 1,
											 -onpress  => sub { refresh_win3(); },
										   },
										   {
											 -label    => '< Cancel >',
											 -value    => 2,
											 -shortcut => 2,
											 -onpress  => sub { $zlbmenu->focus(); },
										   },
							  ],
	);

	$refresh->focus();

}

sub manage_zlb_hostname
{
	$zlbhostname = `hostname`;
	chomp $zlbhostname;
	$zlbhostinput = $win3->add(
								'win3id1', 'TextEntry',
								-bg     => 'black',
								-tfg    => 'black',
								-tbg    => 'white',
								-border => 1,
								-y      => 1,
								-title  => 'ZLB Hostname Configuration',
								-text   => $zlbhostname,
	);
	my $confirm = $win3->add(
							  'win3id2',
							  'Buttonbox',
							  -bg       => 'black',
							  -tfg      => 'black',
							  -tbg      => 'white',
							  -y        => 5,
							  -selected => 1,
							  -buttons  => [
										   {
											 -label    => '< Save >',
											 -value    => 1,
											 -shortcut => 1,
											 -onpress  => sub { &set_new_hostname(); },
										   },
										   {
											 -label    => '< Cancel >',
											 -value    => 2,
											 -shortcut => 2,
											 -onpress  => sub { $zlbmenu->focus(); },
										   },
							  ],
	);
	$confirm->focus();
}

sub set_new_hostname
{
	if ( $zlbhostinput )
	{
		my $ret = &confirm_dialog(
					   "Are you sure you want to change your Zen Load Balancer hostname?" );
		if ( $ret )
		{
			my $newhost = $zlbhostinput->get();
			if ( $newhost && $newhost ne $zlbhostname )
			{
				my @run = `echo $newhost > /etc/hostname`;
				@run = `hostname $newhost`;
			}
			else
			{
				&error_dialog(
							   "Hostname has not changed or is empty. Changes are not applied." );
			}
			&refresh_win3();
		}
	}
}

sub show_status_system
{
	my @memdata       = &get_system_mem();
	my $memstring     = &set_data_string( @memdata );
	my @loadavgdata   = &get_system_loadavg();
	my $loadavgstring = &set_data_string( @loadavgdata );
	my @cpudata       = &get_system_cpu();
	my $cpustring     = &set_data_string( @cpudata );
	my $zlbversion    = &getGlobalConfiguration('version');
	my $zaversion     = `dpkg -l | grep zen | awk '{printf \$3}'`;
	my $ncores = 1 + `grep processor /proc/cpuinfo | tail -1 | awk '{printf \$3}'`;
	$zlbhostname = `hostname`;
	chomp $zlbhostname;

	my $refresh = $win3->add(
							  'win3id1',
							  'Buttonbox',
							  -bg       => 'black',
							  -tfg      => 'black',
							  -tbg      => 'white',
							  -y        => 1,
							  -selected => 1,
							  -buttons  => [
										   {
											 -label    => '< Refresh >',
											 -value    => 1,
											 -shortcut => 1,
											 -onpress  => sub { refresh_win3(); },
										   },
										   {
											 -label    => '< Cancel >',
											 -value    => 2,
											 -shortcut => 2,
											 -onpress  => sub { $zlbmenu->focus(); },
										   },
							  ],
	);

	my $textviewer = $win3->add(
								 'win3id2', 'TextViewer',
								 -bg         => 'black',
								 -border     => 1,
								 -y          => 3,
								 -vscrollbar => 1,
								 -text       => "\nZLB Appliance Version:\n"
								   . "\tZen Load Balancer EE "
								   . $zaversion . "\n"
								   . "\nZLB Software Version:\n" . "\t"
								   . $zlbversion . "\n"
								   . "\nZLB Hostname:\n" . "\t"
								   . $zlbhostname . "\n"
								   . "\nZLB Memory (MB):\n"
								   . $memstring
								   . "\nZLB Load AVG:\n"
								   . $loadavgstring
								   . "\nZLB Number of CPU cores:\n" . "\t"
								   . $ncores . "\n"
								   . "\nZLB CPU Usage (%):\n"
								   . $cpustring,
	);

	$refresh->focus();

}

sub create_win3
{
	my ( $title ) = @_;

	$win3 = $win1->add(
						'win3', 'Window',
						-border => 1,
						-bfg    => 'green',
						-fg     => 'white',
						-tfg    => 'white',
						-tbg    => 'black',
						-x      => 26,
						-title  => $title,
	);
}

$zenui->set_binding( sub { $zlbmenu->focus() }, "\cX" );
$zenui->set_binding( \&exit_dialog, "\cQ" );

$zenui->mainloop();
