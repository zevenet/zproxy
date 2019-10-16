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

use strict;
use warnings;
use Curses::UI;
use Zevenet::Config;
use Zevenet::Debug;
include 'Zevenet::Net::DHCP';

# This two sentences should make zenbui behave like zenbui.sh
$ENV{ NCURSES_NO_UTF8_ACS } = 1;
open ( STDERR, '>', '/dev/null' ) if &debug();
my $ifconfig_bin = &getGlobalConfiguration( 'ifconfig_bin' );
my $zlbmenu;
my $win3;
my $winhelp;
my $zlbhostinput;
my ( $mgmtif, $mgmtip, $mgmtmask, $mgmtgw, $mgmtdhcp, $mgmthttp, $mgmthttps );
my (
	 $mgmtifinput, $mgmtipinput,   $mgmtmaskinput, $mgmtdhcpinput,
	 $mgmtgwinput, $mgmthttpinput, $mgmthttpsinput
);

my $zenui = Curses::UI->new( -color_support => 1, -clear_on_exit => 1 );

#my $co = $Curses::UI::color_object;
#$co->define_color('white', 70, 185, 113);

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
						-title        => 'ZEVENET Basic User Interface',
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
					   -title  => 'Main Menu',
);

$zlbmenu = $win2->add(
					   'win2id1',
					   'Listbox',
					   -radio      => 1,
					   -selectmode => 'single',
					   -fg         => 'white',
					   -bg         => 'black',
					   -values     => [1, 2, 3, 4, 9, 5, 6, 10, 7, 8],
					   -labels     => {
									1  => 'Status',
									2  => 'Services',
									3  => 'Hostname',
									4  => 'MGMT Interface',
									9  => 'Proxy Settings',
									5  => 'Time Zone',
									6  => 'Keyboard Map',
									10 => 'Factory Reset',
									7  => 'Reboot/Shutdown',
									8  => 'Exit to shell',
					   },
					   -onchange => \&manage_sel,
					   -onfocus  => sub { $zlbmenu->clear_selection(); },
);
$zlbmenu->focus();
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
	-title  => 'ZEVENET Basic User Interface Help:',
	-tfg    => 'white',
	-tbg    => 'black',
	-bfg    => 'green',
	-border => 1,
	-text =>
	  "Ctrl+Q = Exit, Ctrl+X = Main menu, Arrows = Move into the item,\nTab = Change to next item, Intro = Select.\n"
);

sub exit_dialog()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $return = $zenui->dialog(
								 -message  => "Do you really want to exit to shell?",
								 -title    => "Exit Confirmation",
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

sub confirm_dialog()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $message ) = @_;
	my $return = $zenui->dialog(
								 -message      => $message,
								 -title        => "Confirmation",
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

sub inform_dialog()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $message ) = @_;
	my $return = $zenui->dialog(
								 -message      => $message,
								 -title        => "Information",
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

sub error_dialog()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $message ) = @_;
	my $return = $zenui->dialog(
								 -message      => $message,
								 -title        => "Warning",
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

sub refresh_win3()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	$zlbmenu->focus();
	&manage_sel();
}

sub manage_sel()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
			&create_win3( 'ZEVENET Status' );
			&show_status_system();
		}
		elsif ( $selected == 2 )
		{
			&create_win3( 'ZEVENET Services' );
			&manage_zlb_services();
		}
		elsif ( $selected == 3 )
		{
			&create_win3( 'ZEVENET Hostname' );
			&manage_zlb_hostname();
		}
		elsif ( $selected == 4 )
		{
			&create_win3( 'ZEVENET MGMT Interface' );
			&manage_mgmt();
		}
		elsif ( $selected == 9 )
		{
			&create_win3( ' ZEVENET Proxy Setting' );
			&manage_proxy();
		}
		elsif ( $selected == 5 )
		{
			&create_win3( 'ZEVENET Time Zone' );
			&manage_timezone();
		}
		elsif ( $selected == 6 )
		{
			&create_win3( 'ZEVENET Keyboard Layout' );
			&manage_keyboard();
		}
		elsif ( $selected == 10 )
		{
			&create_win3( 'ZEVENET Factory Reset' );
			&manage_factory_reset();
		}
		elsif ( $selected == 7 )
		{
			&create_win3( 'ZEVENET Reboot/Shutdown' );
			&manage_power();
		}
		elsif ( $selected == 8 )
		{
			\&exit_dialog();
		}
	}
}

sub manage_factory_reset()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	require Zevenet::Net::Interface;

	my $nic_hash = {};
	my $label    = ();
	foreach my $if ( &getInterfaceTypeList( 'nic' ) )
	{
		if ( $if->{ addr } )
		{
			$nic_hash->{ $if->{ name } } = $if->{ addr };
			$label->{ $if->{ name } }    = "$if->{name}, $if->{addr}";
		}
	}
	my @nic_list = keys %{ $nic_hash };

	my $nicselect = $win3->add(
								'win3id1',
								'Listbox',
								-radio      => 1,
								-bg         => 'black',
								-tfg        => 'black',
								-tbg        => 'white',
								-border     => 1,
								-y          => 0,
								-height     => 6,
								-selected   => 0,
								-values     => \@nic_list,
								-labels     => $label,
								-title      => 'Select the management interface',
								-vscrollbar => 1,
	);

	$nicselect->focus();

	my $reset = $win3->add(
		'win3id2',
		'Buttonbox',
		-bg       => 'black',
		-tfg      => 'black',
		-tbg      => 'white',
		-title    => 'Factory Reset',
		-border   => 1,
		-y        => 7,
		-selected => 2,
		-buttons  => [
			{
			   -label    => '< Apply >',
			   -value    => 1,
			   -shortcut => 1,
			   -onpress  => sub {
				   my $if_sel = $nicselect->get();
				   my $ip_sel = $nic_hash->{ $if_sel };
				   my $ret = &confirm_dialog(
					   "A factory reset will REMOVE all services and will DELETE compleatily the load balancer configuration.
Are you SURE about applying the factory reset to your ZEVENET?
After the reset the load balancer will be accesible by the IP $ip_sel"
				   );
				   if ( $ret )
				   {
					   require Zevenet::System;
					   &applyFactoryReset( $if_sel, 'hard-reset' );
					   exit 0;
				   }
			   },
			},
			{
			   -label    => '< Return >',
			   -value    => 3,
			   -shortcut => 3,
			   -onpress  => sub { $zlbmenu->focus(); },
			},
		],
	);
	$reset->focus();
}

sub manage_power()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $power = $win3->add(
		'win3id2',
		'Buttonbox',
		-bg       => 'black',
		-tfg      => 'black',
		-tbg      => 'white',
		-title    => 'Power Manager',
		-border   => 1,
		-y        => 1,
		-selected => 2,
		-buttons  => [
			{
			   -label    => '< Reboot >',
			   -value    => 1,
			   -shortcut => 1,
			   -onpress  => sub {
				   my $ret = &confirm_dialog( "Are you sure you want to reboot your ZEVENET?" );
				   if ( $ret )
				   {
					   my $reboot_bin = &getGlobalConfiguration( 'reboot_bin' );
					   my @run        = `$reboot_bin &`;
					   exit ( 0 );
				   }
			   },
			},
			{
			   -label    => '< Shutdown >',
			   -value    => 2,
			   -shortcut => 2,
			   -onpress  => sub {
				   my $ret = &confirm_dialog( "Are you sure you want to shutdown your ZEVENET?" );
				   if ( $ret )
				   {
					   my $poweroff_bin = &getGlobalConfiguration( 'poweroff_bin' );
					   my @run          = `$poweroff_bin &`;
					   exit ( 0 );
				   }
			   },
			},
			{
			   -label    => '< Return >',
			   -value    => 3,
			   -shortcut => 3,
			   -onpress  => sub { $zlbmenu->focus(); },
			},
		],
	);
	$power->focus();
}

sub manage_keyboard()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $keyboardfile = "/etc/default/keyboard";
	my ( $keyboard, $zlbkeyboard );

	if ( -f $keyboardfile )
	{
		open my $fd, '<', $keyboardfile;

		while ( my $line = <$fd> )
		{
			if ( $line =~ 'XKBLAYOUT' )
			{
				$keyboard = $line;
			}
		}
		close $fd;
	}

	$zlbkeyboard = $win3->add(
							   'win3id1', 'TextEntry',
							   -bg       => 'black',
							   -tfg      => 'black',
							   -tbg      => 'white',
							   -border   => 1,
							   -y        => 1,
							   -title    => 'Keyboard Layout Configuration',
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
				   &logAndRun( 'dpkg-reconfigure keyboard-configuration' );
				   $zenui->reset_curses();
				   &inform_dialog( "You have to reboot the host to apply the changes." );
				   &refresh_win3();
			   },
			},
			{
			   -label    => '< Return >',
			   -value    => 2,
			   -shortcut => 2,
			   -onpress  => sub { $zlbmenu->focus(); },
			},
		],
	);
	$confirm->focus();
}

sub manage_timezone()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $timezonefile = "/etc/timezone";
	my ( $timezone, $zlbtimezone );

	if ( -f $timezonefile )
	{
		open my $fd, '<', $timezonefile;

		while ( my $line = <$fd> )
		{
			$timezone = $line;
		}
		close $fd;
	}

	$zlbtimezone = $win3->add(
							   'win3id1', 'TextEntry',
							   -bg       => 'black',
							   -tfg      => 'black',
							   -tbg      => 'white',
							   -border   => 1,
							   -y        => 1,
							   -title    => 'Time Zone Configuration',
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
				   &logAndRun( 'dpkg-reconfigure tzdata' );
				   $zenui->reset_curses();
				   &logAndRun( "ntpdate pool.ntp.org" );

				   #$zenui->reset_curses();
				   &inform_dialog( "Synchronizing time with pool.ntp.org..." );
				   &refresh_win3();
			   },
			},
			{
			   -label    => '< Return >',
			   -value    => 2,
			   -shortcut => 2,
			   -onpress  => sub { $zlbmenu->focus(); },
			},
		],
	);
	$confirm->focus();
}

sub manage_proxy()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $mgmthttp = &getGlobalConfiguration( 'http_proxy' ) // '';
	if ( $mgmthttpinput )
	{
		$mgmthttpinput->text( $mgmthttp );
	}
	my $mgmthttps = &getGlobalConfiguration( 'https_proxy' ) // '';
	if ( $mgmthttpsinput )
	{
		$mgmthttpsinput->text( $mgmthttps );
	}

	$mgmthttpinput = $win3->add(
		'win3id1', 'TextEntry',
		-bg     => 'black',
		-tfg    => 'black',
		-tbg    => 'white',
		-border => 1,
		-y      => 1,
		-title  => 'HTTP Proxy Configuration',
		-text   => $mgmthttp,

	);

	#$mgmthttpinput->focus();

	$mgmthttpsinput = $win3->add(
		'win3id2', 'TextEntry',
		-bg     => 'black',
		-tfg    => 'black',
		-tbg    => 'white',
		-border => 1,
		-y      => 4,
		-title  => 'HTTPS Proxy Configuration',
		-text   => $mgmthttps,

	);

	my $confirm = $win3->add(
							  'win3id3',
							  'Buttonbox',
							  -bg       => 'black',
							  -tfg      => 'black',
							  -tbg      => 'white',
							  -y        => 8,
							  -selected => 1,
							  -buttons  => [
										   {
											 -label    => '< Save >',
											 -value    => 1,
											 -shortcut => 1,
											 -onpress  => sub { &set_proxy(); },
										   },
										   {
											 -label    => '< Return >',
											 -value    => 2,
											 -shortcut => 2,
											 -onpress  => sub { $zlbmenu->focus(); },
										   },
							  ],
	);
	$confirm->focus();

}

sub manage_mgmt()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Net::Interface;

	my $mgmtif         = "";
	my @all_interfaces = &getInterfaceTypeList( 'nic' );

	# widget sizes
	my $pos_y           = 0;
	my $size_iface_list = 3;
	my $size_dhcp       = 3;
	my $size_ip         = 3;
	my $size_gw         = 3;
	my $size_net        = 3;

	# discard bonding slave nics
	@all_interfaces = grep { $_->{ is_slave } eq 'false' } @all_interfaces;
	my $i            = 0;
	my $mgmtindex    = 0;
	my @interfaces   = ();
	my $dhcp_enabled = 0;

	foreach my $if_ref ( @all_interfaces )
	{
		push ( @interfaces, $if_ref->{ name } );

		if ( $if_ref->{ name } eq "mgmt" )
		{
			$mgmtindex = $i;
		}

		$i++;
	}

	$mgmtifinput = $win3->add(
							   'win3id1',
							   'Listbox',
							   -radio      => 1,
							   -bg         => 'black',
							   -tfg        => 'black',
							   -tbg        => 'white',
							   -border     => 1,
							   -vscrollbar => 1,
							   -y          => $pos_y,
							   -height     => $size_iface_list,
							   -values     => \@interfaces,
							   -title      => 'Available Interfaces List',
							   -onchange   => sub { &update_mgmt_view(); },
	);
	$pos_y += $size_iface_list;

	$mgmtdhcpinput = $win3->add(
		'win3id6',
		'Checkbox',
		-label    => "Check to enable the DHCP service",
		-checked  => $dhcp_enabled,
		-bg       => 'black',
		-fg       => 'white',
		-tfg      => 'black',
		-tbg      => 'white',
		-border   => 1,
		-y        => $pos_y,
		-title    => 'MGMT DHCP Configuration',
		-onchange => sub {
			&set_dhcp();
			&update_mgmt_view();
		},
	);
	$pos_y += $size_dhcp;

	$mgmtipinput = $win3->add(
		'win3id2', 'TextEditor',
		-bg         => 'black',
		-tfg        => 'black',
		-tbg        => 'white',
		-border     => 1,
		-y          => $pos_y,
		-title      => 'MGMT IP Configuration',
		-text       => '',                        # ip
		-readonly   => $dhcp_enabled,
		-singleline => 1,
	);
	$pos_y += $size_ip;

	$mgmtmaskinput = $win3->add(
		'win3id3', 'TextEditor',
		-bg         => 'black',
		-tfg        => 'black',
		-tbg        => 'white',
		-border     => 1,
		-y          => $pos_y,
		-title      => 'MGMT NetMask Configuration',
		-text       => '',                             # mask
		-singleline => 1,
	);
	$pos_y += $size_gw;

	$mgmtgwinput = $win3->add(
		'win3id4', 'TextEditor',
		-bg         => 'black',
		-tfg        => 'black',
		-tbg        => 'white',
		-border     => 1,
		-y          => $pos_y,
		-title      => 'MGMT Gateway Configuration',
		-text       => '',                             # gw
		-singleline => 1,
	);
	$pos_y += $size_net;

	my $confirm = $win3->add(
		'win3id5',
		'Buttonbox',
		-bg       => 'black',
		-tfg      => 'black',
		-tbg      => 'white',
		-y        => $pos_y,
		-selected => 1,
		-buttons  => [
			{
			   -label    => '< Save >',
			   -value    => 1,
			   -shortcut => 1,
			   -onpress  => sub { &set_net(); },
			},
			{
			   -label    => '< unset >',
			   -value    => 1,
			   -shortcut => 1,
			   -onpress  => sub {
				   my $if     = $mgmtifinput->get();
				   my $if_ref = &getInterfaceConfig( $if );
				   my $ret = &confirm_dialog( "Are you sure you want to unset the interface $if?" );
				   if ( $ret )
				   {
					   &unset_iface( $if_ref );
				   }
			   },
			},
			{
			   -label    => '< Return >',
			   -value    => 2,
			   -shortcut => 2,
			   -onpress  => sub { $zlbmenu->focus(); },
			},
		],
	);

	# finish boxes definitions and begin user logic
	$mgmtifinput->focus();
	$mgmtifinput->set_selection( $mgmtindex );

	$confirm->focus();
}

sub update_mgmt_view()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	# not continue if the boxes are not defined
	return
	  unless (     $mgmtipinput
			   and $mgmtmaskinput
			   and $mgmtgwinput
			   and $mgmtdhcpinput );

	$mgmtif = $mgmtifinput->get();
	my $if_ref = &getInterfaceConfig( $mgmtif );

	my $dhcp_enabled = ( $if_ref->{ dhcp } eq 'true' ) ? 1 : 0;

	$mgmtip = $if_ref->{ addr } // '';
	$mgmtipinput->text( $mgmtip );

	$mgmtmask = $if_ref->{ mask } // '';
	$mgmtmaskinput->text( $mgmtmask );

	$mgmtgw = $if_ref->{ gateway } // '';
	$mgmtgwinput->text( $mgmtgw );

	# set only read the configuration box, y dhcp is enabled
	if ( $dhcp_enabled )
	{
		$mgmtdhcpinput->check();
		$mgmtipinput->set_color_bfg( 'red' );
		$mgmtmaskinput->set_color_bfg( 'red' );
		$mgmtgwinput->set_color_bfg( 'red' );
	}
	else
	{
		$mgmtdhcpinput->uncheck();
		$mgmtipinput->set_color_bfg( 'yellow' );
		$mgmtmaskinput->set_color_bfg( 'yellow' );
		$mgmtgwinput->set_color_bfg( 'yellow' );
	}
	$mgmtdhcpinput->intellidraw();    # update checkbox view

	$mgmtipinput->readonly( $dhcp_enabled );
	$mgmtmaskinput->readonly( $dhcp_enabled );
	$mgmtgwinput->readonly( $dhcp_enabled );
}

sub set_proxy()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $newhttp  = $mgmthttpinput->get();
	my $newhttps = $mgmthttpsinput->get();

	my $ret = &confirm_dialog(
						"Are you sure you want to change your ZEVENET Proxy Setting?" );
	if ( $ret )
	{
		&setGlobalConfiguration( 'http_proxy',  $newhttp );
		&setGlobalConfiguration( 'https_proxy', $newhttps );
		&refresh_win3();
	}

}

sub unset_iface
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $if_ref = shift;

	&delRoutes( "local", $if_ref );
	&delIf( $if_ref );
	&update_mgmt_view();
}

sub set_net()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Net::Validate;
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
			require Zevenet::Net::Interface;
			my $ret = &confirm_dialog(
							   "Are you sure you want to change your ZEVENET MGMT Interface?" );

			# Get interface configuration structure
			my $if_ref = &getInterfaceConfig( $newif ) // &getSystemInterface( $newif );

			if ( $ret )
			{
				require Zevenet::Net::Core;
				require Zevenet::Net::Route;
				if ( $if_ref->{ addr } )
				{
					# Delete old IP and Netmask from system to replace it
					&delIp( $if_ref->{ name }, $if_ref->{ addr }, $if_ref->{ mask } );

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

				require Zevenet::Net::Interface;
				&setInterfaceConfig( $if_ref );
			}
		}

		&update_mgmt_view();
	}

}

sub set_dhcp()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Net::Validate;

	if ( $mgmtifinput && $mgmtdhcpinput )
	{
		my $newif = $mgmtifinput->get();

		# get 1 when has been ckecked or 0 if it has been unchecked
		my $newdhcp = $mgmtdhcpinput->get();
		my $err     = 0;

		# Get interface configuration structure
		my $if_ref = &getInterfaceConfig( $newif ) // &getSystemInterface( $newif );
		my $dhcp_status = ( $if_ref->{ dhcp } eq 'true' ) ? 1 : 0;

		# do not to save, if the value is the same
		return if ( $dhcp_status == $newdhcp );

		# set the interface up
		if ( $if_ref->{ status } ne 'up' )
		{
			if ( &upIf( $if_ref, 'writeconf' ) )
			{
				&error_dialog( "A problem is detected setting up the $newif interface." );
				return undef;
			}
		}

		require Zevenet::Net::Core;
		require Zevenet::Net::Route;
		if ( $if_ref->{ addr } )
		{
			# Delete old IP and Netmask from system to replace it
			&delIp( $if_ref->{ name }, $if_ref->{ addr }, $if_ref->{ mask } );

			# Remove routes if the interface has its own route table: nic and vlan
			&delRoutes( "local", $if_ref );
		}

		if ( $newdhcp )
		{
			&zenlog( "Enabling DHCP for the interface $newif", 'debug', 'zenbui' );
			$err = &enableDHCP( $if_ref );
		}
		else
		{
			&zenlog( "Disabling DHCP for the interface $newif", 'debug', 'zenbui' );
			$err = &disableDHCP( $if_ref );
		}

		# update the network configuration
		$if_ref = &getInterfaceConfig( $if_ref->{ name } );
		$newif  = $if_ref->{ name };
		my $newip = $if_ref->{ addr };

		if ( !$err )
		{
			&inform_dialog( "The $newif interface config has been saved" );
			if ( !$newip and $newdhcp )
			{
				&error_dialog(
							 "No IP has been found, wait a while or try to configure it manually" );
			}
			elsif ( $newip ne '' )
			{
				&inform_dialog(
					"If this is your first boot you can access to ZEVENET Web GUI through\nhttps://$newip:444\nwith user root and password admin,\nremember to change the password for security reasons in web GUI."
				);
			}
		}
		else
		{
			&error_dialog(
				"A problem is detected configuring $newif interface, you have to configure your $newif \nthrough command line and after save the configuration in the web GUI"
			);
		}
	}
}

sub manage_zlb_services()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my @services         = ( 'cherokee', 'zevenet' );
	my $cherokeestatus   = "STOPPED";
	my $zlbservicestatus = "STOPPED";
	my $ps_bin           = &getGlobalConfiguration( 'ps' );
	my @run              = `$ps_bin ex`;
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
									-title      => 'Services Status',
									-text       => "ZEVENET Services:\n"
									  . "\tWeb Service:\t"
									  . $cherokeestatus . "\n"
									  . "\tZEVENET:\t"
									  . $zlbservicestatus . "\n",
	);

	my $service1 = $win3->add(
		'win3id2',
		'Buttonbox',
		-bg      => 'black',
		-tfg     => 'black',
		-tbg     => 'white',
		-title   => 'Web Service Manager',
		-border  => 1,
		-y       => 5,
		-buttons => [
			{
			   -label    => '< Stop >',
			   -value    => 1,
			   -shortcut => 1,
			   -onpress  => sub {
				   my $ret = &confirm_dialog( "Are you sure you want to STOP Web Server?" );
				   if ( $ret )
				   {
					   &logAndRun( "/etc/init.d/cherokee stop" );
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
				   my $ret = &confirm_dialog( "Are you sure you want to START Web Server?" );
				   if ( $ret )
				   {
					   &logAndRun( "/etc/init.d/cherokee start" );
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
				   my $ret = &confirm_dialog( "Are you sure you want to RESTART Web Server?" );
				   if ( $ret )
				   {
					   &logAndRun( "/etc/init.d/cherokee restart" );
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
		-title   => 'ZEVENET Service Manager',
		-border  => 1,
		-y       => 8,
		-buttons => [
			{
			   -label    => '< Stop >',
			   -value    => 1,
			   -shortcut => 1,
			   -onpress  => sub {
				   my $ret = &confirm_dialog( "Are you sure you want to STOP ZEVENET service?" );
				   if ( $ret )
				   {
					   my $zenbin = "/usr/local/zevenet/bin/zevenet";
					   &logAndRun( "$zenbin stop" );
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
				   my $ret = &confirm_dialog( "Are you sure you want to START ZEVENET service?" );
				   if ( $ret )
				   {
					   my $zenbin = "/usr/local/zevenet/bin/zevenet";
					   &logAndRun( "$zenbin start" );
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
				   my $ret = &confirm_dialog( "Are you sure you want to RESTART ZEVENET service?" );
				   if ( $ret )
				   {
					   my $zenbin = "/usr/local/zevenet/bin/zevenet";
					   &logAndRun( "$zenbin stop" );
					   &logAndRun( "$zenbin start" );
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
											 -label    => '< Return >',
											 -value    => 2,
											 -shortcut => 2,
											 -onpress  => sub { $zlbmenu->focus(); },
										   },
							  ],
	);

	$refresh->focus();

}

sub manage_zlb_hostname()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	$zlbhostname = `hostname`;
	chomp $zlbhostname;
	$zlbhostinput = $win3->add(
								'win3id1', 'TextEntry',
								-bg     => 'black',
								-tfg    => 'black',
								-tbg    => 'white',
								-border => 1,
								-y      => 1,
								-title  => 'Hostname Configuration',
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
											 -label    => '< Return >',
											 -value    => 2,
											 -shortcut => 2,
											 -onpress  => sub { $zlbmenu->focus(); },
										   },
							  ],
	);
	$confirm->focus();
}

sub set_new_hostname()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	if ( $zlbhostinput )
	{
		my $ret =
		  &confirm_dialog( "Are you sure you want to change your ZEVENET hostname?" );
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

sub show_status_system()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::SystemInfo;
	require Zevenet::Stats;

	my @memdata       = &getMemStats();
	my $memstring     = &set_data_string( @memdata );
	my @loadavgdata   = &getLoadStats();
	my $loadavgstring = &set_data_string( @loadavgdata );
	my @cpudata       = &getCPU();
	my $cpustring     = &set_data_string( @cpudata );
	my $zlbversion    = &getGlobalConfiguration( 'version' );
	my $zaversion     = &getApplianceVersion();
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
											 -label    => '< Return >',
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
								 -text       => "\nAppliance Version:\n" . "\t"
								   . $zaversion . "\n"
								   . "\nSoftware Version:\n" . "\t"
								   . $zlbversion . "\n"
								   . "\nHostname:\n" . "\t"
								   . $zlbhostname . "\n"
								   . "\nMemory (MB):\n"
								   . $memstring
								   . "\nLoad AVG:\n"
								   . $loadavgstring
								   . "\nNumber of CPU cores:\n" . "\t"
								   . $ncores . "\n"
								   . "\nCPU Usage (%):\n"
								   . $cpustring,
	);

	$refresh->focus();

}

sub create_win3()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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

sub set_data_string
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( @datain ) = @_;

	my $output = "";

	for my $i ( 0 .. $#datain )
	{
		$output .= "\t$datain[$i][0]: $datain[$i][1]\n";
	}

	return $output;
}

