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


=begin nd
Function: upload

	NOT USED.

Parameters:
	none - .

Returns:
	none - .

Bugs:
	NOT USED.

See Also:
	
=cut
sub upload                            # ()
{
	print
	  "<a href=\"upload.cgi\" class=\"open-dialog\"><img src=\"img/icons/basic/up.png\" title=\"Upload backup\">Upload backup</a>";
	print
	  "<div id=\"dialog-container\" style=\"display: none;\"><iframe id=\"dialog\" width=\"350\" height=\"350\"></iframe></div>";
}

=begin nd
Function: uploadcerts

	NOT USED.

Parameters:
	none - .

Returns:
	none - .

Bugs:
	NOT USED.

See Also:
	
=cut
sub uploadcerts                       # ()
{
	print "<script language=\"javascript\">
                var popupWindow = null;
                function positionedPopup(url,winName,w,h,t,l,scroll)
                {
                settings ='height='+h+',width='+w+',top='+t+',left='+l+',scrollbars='+scroll+',resizable'
                popupWindow = window.open(url,winName,settings)
                }
        </script>";

	#print the information icon with the popup with info.
	print
	  "<a href=\"uploadcerts.cgi\" onclick=\"positionedPopup(this.href,'myWindow','500','300','100','200','yes');return false\"><img src='img/icons/small/arrow_up.png' title=\"upload certificate\"></a>";
}

=begin nd
Function: uptime

	NOT USED. Return the date when started (uptime)

Parameters:
	none - .

Returns:
	none - .

Bugs:
	NOT USED.

See Also:
	
=cut
sub uptime                    # ()
{
	$timeseconds = time ();
	open TIME, '/proc/uptime' or die $!;

	while ( <TIME> )
	{
		my @time = split ( "\ ", $_ );
		$uptimesec = $time[0];
	}

	$totaltime = $timeseconds - $uptimesec;

	#
	#my $time = time;       # or any other epoch timestamp
	my $time = $totaltime;
	my @months = (
				   "Jan", "Feb", "Mar", "Apr", "May", "Jun",
				   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
	);
	my ( $sec, $min, $hour, $day, $month, $year ) =
	  ( localtime ( $time ) )[0, 1, 2, 3, 4, 5, 6];

	return
	    $months[$month] . ", "
	  . $day . " "
	  . $hour . ":"
	  . $min . ":"
	  . $sec . " "
	  . ( $year + 1900 ) . "\n";
}

=begin nd
Function: graphs

	NOT USED. Configure the graphs apareance

Parameters:
	none - .

Returns:
	none - .

Bugs:
	NOT USED.

See Also:
	
=cut
#function that configure the graphs apareance.
sub graphs    # ($description,@data)
{
	my ( $description, @data ) = @_;
	####graph configuration
	#midblue     => { R => 165,  G => 192, B => 220 },
	my %options = (

		#  	'file' => 'img/graphs/mygraph.jpg',
		#	'quality' => '9',
		# colours

		black      => { R => 0,   G => 0,   B => 0 },
		white      => { R => 255, G => 255, B => 255 },
		vltgrey    => { R => 245, G => 245, B => 245 },
		ltgrey     => { R => 230, G => 230, B => 230 },
		midgreen   => { R => 143, G => 184, B => 32 },
		midblue    => { R => 165, G => 192, B => 220 },
		midgray    => { R => 156, G => 156, B => 156 },
		background => { R => 238, G => 238, B => 238 },
		graybg     => { R => 238, G => 238, B => 238 },

		# file output details

		file    => $description,    # file path and name; file extension
		                            # can be .jpg|gif|png
		quality => 9,               # image quality: 1 (worst) - 10 (best)
		                            # Only applies to jpg and png

		# main image properties

		imgw     => 500,            # preferred width in pixels
		imgh     => 250,            # preferred height in pixels
		iplotpad => 8,              # padding between axis vals & plot area
		ipadding => 14,             # padding between other items
		ibgcol   => 'graybg',       # COLOUR NAME; background colour
		iborder  => '',             # COLOUR NAME; border, if any

		# plot area properties

		plinecol => 'midgrey',      # COLOUR NAME; line colour
		pflcol   => 'ltgrey',       # COLOUR NAME; floor colour
		pbgcol   => 'ltgrey',       # COLOUR NAME; back/side colour
		pbgfill  => 'gradient',     # 'gradient' or 'solid'; back/side fill
		plnspace => 25,             # minimum pixel spacing between divisions
		pnumdivs => 30,             # maximum number of y-axis divisions

		# bar properties

		bstyle      => 'bar',         # 'bar' or 'column' style
		bcolumnfill => 'gradient',    # 'gradient' or 'solid' for columns
		bminspace   => 18,            # minimum spacing between bars
		bwidth      => 18,            # width of bar
		bfacecol    => 'midgray',     # COLOUR NAME or 'random'; bar face,
		                              # 'random' for random bar face colour
		                              # graph title

		ttext    => '',               # title text
		tfont    => '',               # uses gdGiantFont unless a true type
		                              # font is specified
		tsize    => 10,               # font point size
		tfontcol => 'black',          # COLOUR NAME; font colour

		# axis labels

		xltext   => '',               # x-axis label text
		yltext   => '',               # y-axis label text
		lfont    => '',               # uses gdLargeFont unless a true type
		                              # font is specified
		lsize    => 10,               # font point size
		lfontcol => 'midblue',        # COLOUR NAME; font colour

		# axis values

		vfont    => '',               # uses gdSmallFont unless a true type
		                              # font is specified
		vsize    => 8,                # font point size
		vfontcol => 'black',          # COLOUR NAME; font colour

	);

	my $imagemap = creategraph( \@data, \%options );
}

=begin nd
Function: isnumber

	Check if variable is a number no float.

	WARNING: This function should be deprecated, replaced by getValidFormat

Parameters:
	num - Variable to be checked. 

Returns:
	scalar - Boolean. 'true' or 'false'.

Bugs:
	TO BE DEPRECATED

See Also:
	Used in: zapi/v2/post.cgi, <applySnmpChanges>,

	To be replaced for: <getValidFormat>
=cut
sub isnumber    # ($num)
{
	my $num = shift;

	if ( $num =~ /^\d+$/ )    # \d = digit, equiv. to ([0-9])
	{
		return "true";
	}
	else
	{
		return "false";
	}
}

=begin nd
Function: uploadCertFromCSR

	NOT USED.

Parameters:
	String - Certificate filename.

Returns:
	 - .

Bugs:
	NOT USED.

See Also:

=cut
sub uploadCertFromCSR    # ($certfile)
{
	my ( $certfile ) = @_;

	print "<script language=\"javascript\">
	                var popupWindow = null;
	                function positionedPopup(url,winName,w,h,t,l,scroll)
	                {
	                settings ='height='+h+',width='+w+',top='+t+',left='+l+',scrollbars='+scroll+',resizable'
	                popupWindow = window.open(url,winName,settings)
	                }
	        </script>";

	print
	  "<a href=\"uploadcertsfromcsr.cgi?certname=$certfile\" title=\"Upload certificate for CSR $certfile\" onclick=\"positionedPopup(this.href,'myWindow','500','300','100','200','yes');return false\"><i class=\"fa fa-upload action-icon fa-fw green\"></i></a> ";
}

=begin nd
Function: uploadPEMCerts

	NOT USED.

Parameters:
	String - Certificate filename.

Returns:
	 - .

Bugs:
	NOT USED.

See Also:

=cut
sub uploadPEMCerts    # ($certfile)
{
	my ( $certfile ) = @_;

	print
	  "<li><a href=\"uploadcerts.cgi\" class=\"open-dialog\"><img src=\"img/icons/basic/up.png\" alt=\"Upload cert\" title=\"Upload cert\">Upload Certificate </a></li>";
	print
	  "<div id=\"dialog-container\" style=\"display: none;\"><iframe id=\"dialog\" width=\"350\" height=\"350\"></iframe></div>";
}

=begin nd
Function: downloadCert

	NOT USED.

Parameters:
	String - Certificate filename.

Returns:
	 - .

Bugs:
	NOT USED.

See Also:

=cut
sub downloadCert      # ($certfile)
{
	my ( $certfile ) = @_;

	print "<script language=\"javascript\">
	                var popupWindow = null;
	                function positionedPopup(url,winName,w,h,t,l,scroll)
	                {
	                settings ='height='+h+',width='+w+',top='+t+',left='+l+',scrollbars='+scroll+',resizable'
	                popupWindow = window.open(url,winName,settings)
	                }
	        </script>";

	#print the information icon with the popup with info.
	print
	  "<a href=\"downloadcerts.cgi?certname=$certfile\" onclick=\"positionedPopup(this.href,'myWindow','500','300','100','200','yes');return false\"><img src='img/icons/small/page_white_put.png' title=\"Download $certfile\"></a> ";
}

=begin nd
Function: verifyPasswd

	NOT USED. Compare passwords.

Parameters:
	newpass     - A password.
	trustedpass - Another password.

Returns:
	scalar - Boolean. Whether the passwords are equal or not.

Bugs:
	NOT USED
=cut
sub verifyPasswd    #($newpass, $trustedpass)
{
	my ( $newpass, $trustedpass ) = @_;
	if ( $newpass !~ /^$|\s+/ && $trustedpass !~ /^$|\s+/ )
	{
		return ( $newpass eq $trustedpass );
	}
	else
	{
		return 0;
	}
}

=begin nd
Function: listActiveInterfaces

	[NOT USED] List all interfaces.

Parameters:
	class - ?????.

Returns:
	list - All interfaces name.

Bugs:
	NOT USED
=cut
# list all interfaces
sub listActiveInterfaces    # ($class)
{
	my $class = shift;

	my $s = IO::Socket::INET->new( Proto => 'udp' );
	my @interfaces = &getInterfaceList();
	my @aifaces;

	for my $if ( @interfaces )
	{
		if ( $if !~ /^lo|sit0/ )
		{
			if ( ( $class eq "phvlan" && $if !~ /\:/ ) || $class eq "" )
			{
				my $flags = $s->if_flags( $if );
				if ( $flags & IFF_UP )
				{
					push ( @aifaces, $if );
				}
			}
		}
	}

	return @aifaces;
}

=begin nd
Function: writeConfigIf

	[NOT USED] Saves network interface config to file.

Parameters:
	if - interface name.
	string - replaces config file with this string.

Returns:
	$? - .

Bugs:
	returns $?

	NOT USED
=cut
# saving network interfaces config files
sub writeConfigIf    # ($if,$string)
{
	my ( $if, $string ) = @_;

	my $configdir = &getGlobalConfiguration( 'configdir' );

	open CONFFILE, ">", "$configdir/if\_$if\_conf";
	print CONFFILE "$string\n";
	close CONFFILE;
	return $?;
}

=begin nd
Function: getDevData

	[NOT USED] Get network interfaces statistics.

	Includes bytes and packets received and transmited.

Parameters:
	dev - interface name. Optional.

Returns:
	list - array with statistics?

Bugs:
	NOT USED
=cut
sub getDevData    # ($dev)
{
	my $dev = shift;

	open FI, "<", "/proc/net/dev";

	my $exit = "false";
	my @dataout;
	
	my $line;
	while ( $line = <FI> && $exit eq "false" )
	{
		if ( $dev ne "" )
		{
			my @curline = split ( ":", $line );
			my $ini = $curline[0];
			chomp ( $ini );
			if ( $ini ne "" && $ini =~ $dev )
			{
				$exit = "true";
				my @datain = split ( " ", $curline[1] );
				push ( @dataout, $datain[0] );
				push ( @dataout, $datain[1] );
				push ( @dataout, $datain[8] );
				push ( @dataout, $datain[9] );
			}
		}
		else
		{
			if ( $line ne // )
			{
				push ( @dataout, $line );
			}
			else
			{
				$exit = "true";
			}
		}
	}
	close FI;

	return @dataout;
}

=begin nd
Function: uplinkUsed

	[NOT USED] Return if interface is used for datalink farm

Parameters:
	none - .

Returns:
	boolean - "true" or "false".

Bugs:
	NOT USED
=cut
# Return if interface is used for datalink farm
sub uplinkUsed          # ($if)
{
	my $if = shift;

	my @farms  = &getFarmsByType( "datalink" );
	my $output = "false";

	foreach my $farm ( @farms )
	{
		my $farmif = &getFarmVip( "vipp", $farm );
		my $status = &getFarmStatus( $farm );
		if ( $status eq "up" && $farmif eq $if )
		{
			$output = "true";
		}
	}
	return $output;
}

=begin nd
Function: getVirtualInterfaceFilenameList

	[NOT USED] Get a list of the virtual interfaces configuration filenames.

Parameters:
	none - .

Returns:
	list - Every configuration file of virtual interfaces.

Bugs:
	NOT USED
=cut
sub getVirtualInterfaceFilenameList
{
	opendir ( DIR, &getGlobalConfiguration( 'configdir' ) );

	my @filenames = grep ( /^if.*\:.*$/, readdir ( DIR ) );

	closedir ( DIR );

	return @filenames;
}

=begin nd
Function: getConntrackExpect

	[NOT USED] Get conntrack sessions.

Parameters:
	none - .

Returns:
	list - list of conntrack sessions.

Bugs:
	NOT USED
=cut
# get conntrack sessions
sub getConntrackExpect    # ($args)
{
	my ( $args ) = @_;

	open CONNS, "</proc/net/nf_conntrack_expect";

	#open CONNS, "</proc/net/nf_conntrack";
	my @expect = <CONNS>;
	close CONNS;

	return @expect;
}

=begin nd
Function: setInterfaceUp

	[NOT USED] Configure interface reference in the system, and optionally store the configuration

Parameters:
	interface - interface reference.
	writeconf - true value to store the interface configuration.

Returns:
	scalar - 0 on success, or 1 on failure.

Bugs:
	NOT USED
=cut
# configure interface reference in the system, and optionally save the configuration
sub setInterfaceUp
{
	my $interface = shift;	# Interface reference
	my $writeconf = shift;	# TRUE value to write configuration, FALSE otherwise

	if ( ref $interface ne 'HASH' )
	{
		&zenlog("Argument must be a reference");
		return 1;
	}
	
	# vlans need to be created if they don't already exist
	my $exists = &ifexist( $interface->{ name } );

	if ( $exists eq "false" )
	{
		&createIf( $interface );    # create vlan if needed
	}

	if ( $writeconf )
	{
		my $old_iface_ref =
		&getInterfaceConfig( $interface->{ name }, $interface->{ ip_v } );

		if ( $old_iface_ref )
		{
			# Delete old IP and Netmask
			# delete interface from system to be able to repace it
			&delIp(
					$$old_iface_ref{ name },
					$$old_iface_ref{ addr },
					$$old_iface_ref{ mask }
			);

			# Remove routes if the interface has its own route table: nic and vlan
			if ( $interface->{ vini } eq '' )
			{
				&delRoutes( "local", $old_iface_ref );
			}
		}
	}

	&addIp( $interface );

	my $state = &upIf( $interface, $writeconf );

	if ( $state == 0 )
	{
		$interface->{ status } = "up";
		&zenlog( "Network interface $interface->{name} is now UP" );
	}

	# Writing new parameters in configuration file
	if ( $interface->{ name } !~ /:/ )
	{
		&writeRoutes( $interface->{ name } );
	}

	&setInterfaceConfig( $interface ) if $writeconf;
	&applyRoutes( "local", $interface );

	return 0; # FIXME
}

=begin nd
Function: getFarmGlobalStatus

	[NOT USED] Get the status of a farm and its backends
	
Parameters:
	farmname - Farm name

Returns:
	array - ???

BUG:
	NOT USED
	
=cut
sub getFarmGlobalStatus    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my @run;

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		@run = &getTcpUdpFarmGlobalStatus( $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		@run = getHTTPFarmGlobalStatus( $farm_name );
	}

	return @run;
}

=begin nd
Function: getClusterInfo

	NOT USED

Parameters:
	none - .

Returns:
	none - .

Bugs:
	NOT USED

See Also:
	<getClusterStatus>
=cut
sub getClusterInfo
{
	my $cluster_msg  = "Not configured";
	my $cluster_icon = "fa-cog yellow";

	if ( &getZClusterStatus() )
	{
		$cluster_msg = &getZClusterNodeStatus();
		
		if ( $cluster_msg eq 'master' )
		{
			$cluster_icon = "fa-cog green";
		}
		elsif ( $cluster_msg eq 'maintenance' )
		{
			$cluster_icon = "fa-cog red";
		}
		elsif ( $cluster_msg eq 'backup' )
		{
			$cluster_icon = "fa-cog green";
		}

		$cluster_msg = ucfirst $cluster_msg;
	}

	return ( $cluster_msg, $cluster_icon );
}

=begin nd
Function: getClusterStatus

	NOT USED

Parameters:
	none - .

Returns:
	none - .

Bugs:
	NOT USED

See Also:

=cut
sub getClusterStatus
{
	my ( $cluster_msg, $cluster_icon ) = &getClusterInfo();
	
	if ( $cluster_msg eq "Not configured" )
	{
		print
		  "<div class=\"grid_6\"><p class=\"cluster\"><a href=\"http://www.zenloadbalancer.com/eliminate-a-single-point-of-failure/\" target=\"_blank\"><i class=\"fa fa-fw $cluster_icon action-icon\" title=\"How to eliminate this single point of failure\"></i></a> Cluster status: $cluster_msg</p></div>";
		print "<div class=\"clear\"></div>";
	}
	else
	{
		print
		  "<div class=\"grid_6\"><p class=\"cluster\"><i class=\"fa fa-fw $cluster_icon action-icon\"></i> Cluster status: $cluster_msg</p></div>";
		print "<div class=\"clear\"></div>";
	}
}

=begin nd
Function: getZCusterStatusInfo

	NOT USED

Parameters:
	none - .

Returns:
	none - .

Bugs:
	NOT USED

See Also:

=cut
sub getZCusterStatusInfo
{
	my $status;

	# check zcluster configuration
	if ( ! -f &getGlobalConfiguration('filecluster') )
	{
		$status->{ cl_conf } = 'ko';
		return $status;
	}
	
	my $zcl_conf = &getZClusterConfig();
	my $localhost = &getHostname();
	my $remotehost = &getZClusterRemoteHost();

	$status->{ localhost } = $localhost;
	$status->{ remotehost } = $remotehost;

	### Localhost ###

	# check local keepalived
	if ( &getZClusterRunning() )
	{
		$status->{ $localhost }->{ keepalived } = 'ok';
	}
	else
	{
		$status->{ $localhost }->{ keepalived } = 'ko';
	}

	# check local node role
	if ( $status->{ $localhost }->{ keepalived } eq 'ok' )
	{
		$status->{ $localhost }->{ node_role } = &getZClusterNodeStatus();
	}

	# check local zeninotify
	if ( $status->{ $localhost }->{ keepalived } eq 'ok' )
	{
		my $zenino_procs_found = `pgrep zeninotify | wc -l`;
		chomp $zenino_procs_found;

		if ( $status->{ $localhost }->{ node_role } eq 'master' && $zenino_procs_found == 1 )
		{
			$status->{ $localhost }->{ zeninotify } = 'ok';
		}
		elsif ( $status->{ $localhost }->{ node_role } eq 'backup' && $zenino_procs_found == 0 )
		{
			$status->{ $localhost }->{ zeninotify } = 'ok';
		}
		else
		{
			$status->{ $localhost }->{ zeninotify } = 'ko';
		}
	}
	else
	{
		$status->{ $localhost }->{ zeninotify } = 'ko';
	}
	
	# check local conntrackd
	if ( &getConntrackdRunning() )
	{
		$status->{ $localhost }->{ conntrackd } = 'ok';
	}
	else
	{
		$status->{ $localhost }->{ conntrackd } = 'ko';
	}

	# check local arp/neighbour
	my @arptables_lines = `arptables -L INPUT`;

	for my $if_ref ( &getInterfaceList() )
	{
		next if $if_ref->{ vini } eq ''; # only virtual ips

		# check if the ip is been dropped in arptables
		my $is_dropping_ip = 0;
		foreach my $line ( @arptables_lines )
		{
			$is_dropping_ip++ if $line =~ /^-j DROP -d $if_ref->{ addr } $/;
		}

		if ( $status->{ $localhost }->{ node_role } ne 'master' && ! $is_dropping_ip )
		{
			$status->{ $localhost }->{ arp } = 'ko';
			last;
		}
		elsif ( $status->{ $localhost }->{ node_role } eq 'master' && $is_dropping_ip )
		{
			$status->{ $localhost }->{ arp } = 'ko';
			last;
		}
	}

	if ( $status->{ $localhost }->{ arp } ne 'ko' )
	{
		$status->{ $localhost }->{ arp } = 'ok';
	}

	# check local floating ips
	# FIXME

	### Remotehost ###

	# check remote keepalived
	my $zcluster_manager = &getGlobalConfiguration('zcluster_manager');

	if ( &runRemotely( "$zcluster_manager getZClusterRunning", $zcl_conf->{$remotehost}->{ip} ) == 1 )
	{
		$status->{ $remotehost }->{ keepalived } = 'ok';
	}
	else
	{
		$status->{ $remotehost }->{ keepalived } = 'ko';
	}

	# check remote node role
	if ( $status->{ $remotehost }->{ keepalived } eq 'ok' )
	{
		$status->{ $remotehost }->{ node_role } = &runRemotely( "$zcluster_manager getZClusterNodeStatus", $zcl_conf->{$remotehost}->{ip} );
		chomp $status->{ $remotehost }->{ node_role };
	}

	# check remote zeninotify
	if ( $status->{ $remotehost }->{ keepalived } eq 'ok' )
	{
		my $zenino_procs_found = &runRemotely( "pgrep zeninotify | wc -l", $zcl_conf->{$remotehost}->{ip} );
		chomp $zenino_procs_found;

		if ( $status->{ $remotehost }->{ node_role } eq 'master' && $zenino_procs_found == 1 )
		{
			$status->{ $remotehost }->{ zeninotify } = 'ok';
		}
		elsif ( $status->{ $remotehost }->{ node_role } eq 'backup' && $zenino_procs_found == 0 )
		{
			$status->{ $remotehost }->{ zeninotify } = 'ok';
		}
		else
		{
			$status->{ $remotehost }->{ zeninotify } = 'ko';
		}
	}
	else
	{
		$status->{ $remotehost }->{ zeninotify } = 'ko';
	}
	
	# check remote conntrackd
	if ( &runRemotely( "$zcluster_manager getConntrackdRunning", $zcl_conf->{$remotehost}->{ip} ) == 1 )
	{
		$status->{ $remotehost }->{ conntrackd } = 'ok';
	}
	else
	{
		$status->{ $remotehost }->{ conntrackd } = 'ko';
	}

	# check remote arp/neighbour
	$status->{ $remotehost }->{ arp } = &runRemotely( "$zcluster_manager getZClusterArpStatus", $zcl_conf->{$remotehost}->{ip} );
	chomp $status->{ $remotehost }->{ arp };

	# check remote floating ips
	# FIXME

	return $status;
}

=begin nd
Function: getZClusterLocalhostStatusDigest

	NOT USED

Parameters:
	none - .

Returns:
	scalar - Hash reference.

	my $node = {
				 role    => 'value',
				 status  => 'value',
				 message => 'value',
	};

Bugs:
	NOT USED

See Also:

=cut
#sub getZClusterLocalhostStatusDigest
#{
#	my $node = {
#				 role    => undef,
#				 status  => undef,
#				 message => undef,
#	};
#
#	if ( ! &getZClusterStatus() )
#	{
#		$node->{ role } = 'not configured';
#		$node->{ status } = 'not configured';
#		$node->{ message } = 'Cluster not configured';
#	}
#	else
#	{
#		my $n = &getZClusterNodeStatusInfo();
#		my $node = &getZClusterNodeStatusDigest();
#	}
#
#	return $node;
#}

=begin nd
Function: checkZClusterInterfaces

	NOT USED

Parameters:
	cl_conf - Cluster configuration.
	nodeIP - .

Returns:
	list - .

Bugs:
	NOT USED

See Also:

=cut
#sub checkZClusterInterfaces # @inmatched_ifaces ( $cl_conf, $nodeIP )
#{
#	my $cl_conf = shift;
#	my $nodeIP = shift;
#
#	require NetAddr::IP;
#
#	my @unmatched_ifaces; 
#
#	for my $if_name ( values %{ $cl_conf->{interfaceList} } )
#	{
#		my $iface = &getInterfaceConfig( $if_name, 4 );
#
#		# get local data
#		my $local_addr = new NetAddr::IP->new( $iface->{addr}, $iface->{mask} );
#
#		# get remote data
#		my @output_line = &runRemotely( "ifconfig $if_name", $nodeIP );
#
#		# strip ipv4
#		my ( $output_line ) = grep /inet addr/, @output_line; # get line
#		my @line_words = split( /\s+/, $output_line );	# divide into words
#
#		# get ip and mask parts
#		my ( $remote_ip ) = grep( /addr/, @line_words );
#		my ( $remote_mask ) = grep( /Mask/, @line_words );
#		
#		# remove attached tags
#		( undef, $remote_ip ) = split( 'addr:', $remote_ip );
#		( undef, $remote_mask ) = split( 'Mask:', $remote_mask );
#
#		#~ print "remote_ip:$remote_ip\n";
#		#~ print "remote_mask:$remote_mask\n";
#
#		my $remote_addr = new NetAddr::IP ( $remote_ip, $remote_mask );
#		#~ print "remote_network:$remote_addr->network()\n";
#
#		if ( $local_addr->network() ne $remote_addr->network() )
#		{
#			#~ print "$if_name network did not match.";
#			push @unmatched_ifaces, $if_name;
#		}
#	}
#
#	return @unmatched_ifaces;
#}

=begin nd
Function: getMasterNode

	COMMENTED FUNCTION

Parameters:
	none - .

Returns:
	none - .

Bugs:
	COMMENTED FUNCTION

See Also:

=cut
#sub getMasterNode # $ip_addr ()
#{
	#my @sucess_lines = grep /SUCCESS/, &parallel_run( 'ls /etc/MASTER' );
	
	##~ &zenlog("getMasterNode1:@sucess_lines");

	## take from the first line, the forth element
	## sample: [1] 11:46:11 [SUCCESS] 192.168.101.12
	#my $ip_address = ( split / /, $sucess_lines[0] )[3];
	#chomp $ip_address;

	##~ &zenlog("getMasterNode2 ip_address:$ip_address<");
	
	#return $ip_address;
#}

1;
