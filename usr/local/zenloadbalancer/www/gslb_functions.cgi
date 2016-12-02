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

use warnings;
use strict;

require "/usr/local/zenloadbalancer/www/networking_functions.cgi";

my $configdir = &getGlobalConfiguration( 'configdir' );

# Start Farm rutine
sub _runGSLBFarmStart    # ($fname,$writeconf)
{
	my ( $fname, $writeconf ) = @_;

	my $output;
	my $status = &getFarmStatus( $fname );
	my $type   = &getFarmType( $fname );
	my $file   = &getFarmFile( $fname );

	chomp ( $status );
	if ( $status eq "up" )
	{
		return 0;
	}

	&zenlog( "running 'Start write $writeconf' for $fname farm $type" );

	&setGSLBControlPort( $fname );

	if ( $writeconf eq "true" )
	{
		unlink ( "/tmp/$fname.lock" );
		use Tie::File;
		tie my @filelines, 'Tie::File', "$configdir\/$file\/etc\/config";
		my $first = 1;
		foreach ( @filelines )
		{
			if ( $first eq 1 )
			{
				s/\;down/\;up/g;
				$first = 0;
				last;
			}
		}
		untie @filelines;
	}
	my $exec = &getGSLBStartCommand( $fname );

	&zenlog( "running $exec" );
	zsystem( "$exec > /dev/null 2>&1" );

	$output = $?;
	if ( $output != 0 )
	{
		$output = -1;
	}

	return $status;
}

# Stop Farm rutine
sub _runGSLBFarmStop    # ($farm_name,$writeconf)
{
	my ( $fname, $writeconf ) = @_;

	my $status = &getFarmStatus( $fname );
	if ( $status eq "down" )
	{
		return 0;
	}

	my $filename = &getFarmFile( $fname );
	if ( $filename == -1 )
	{
		return -1;
	}

	my $type = &getFarmType( $fname );
	$status = $type;

	&zenlog( "running 'Stop write $writeconf' for $fname farm $type" );

	my $checkfarm = &getFarmConfigIsOK( $fname );
	if ( $checkfarm == 0 )
	{
		if ( $writeconf eq "true" )
		{
			use Tie::File;
			tie my @filelines, 'Tie::File', "$configdir\/$filename\/etc\/config";
			my $first = 1;
			foreach ( @filelines )
			{
				if ( $first eq 1 )
				{
					s/\;up/\;down/g;
					$status = $?;
					$first  = 0;
				}
			}
			untie @filelines;
		}
		my $exec    = &getGSLBStopCommand( $fname );
		my $pidfile = &getGSLBFarmPidFile( $fname );
		zsystem( "$exec > /dev/null 2>&1" );

		#$exec returns 0 even when gslb stop fails, checked, so force TERM
		my $pid_gslb = &getGSLBFarmPid( $fname );
		&zenlog( "forcing stop to gslb with PID $pid_gslb" );
		if ( $pid_gslb ne "-" )
		{
			kill 'TERM' => $pid_gslb;
		}
		unlink ( $pidfile );
	}
	else
	{
		&errormsg(
			  "Farm $fname can't be stopped, check the logs and modify the configuration" );
		return 1;
	}

	return $status;
}

# Get farm services list for GSLB farms
sub getGSLBFarmServices    # ($farm_name)
{
	my ( $fname ) = @_;

	my $output = -1;
	my $ftype  = &getFarmType( $fname );
	my @srvarr = ();

	opendir ( DIR, "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/" );
	my @pluginlist = readdir ( DIR );
	closedir ( DIR );
	foreach my $plugin ( @pluginlist )
	{
		if ( $plugin !~ /^\./ )
		{
			tie my @fileconf, 'Tie::File',
			  "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/$plugin";
			my @srv = grep ( /^\t[a-zA-Z1-9].* => \{/, @fileconf );
			foreach my $srvstring ( @srv )
			{
				my @srvstr = split ( ' => ', $srvstring );
				$srvstring = $srvstr[0];
				$srvstring =~ s/^\s+|\s+$//g;
			}
			my $nsrv = @srv;
			if ( $nsrv > 0 )
			{
				push ( @srvarr, @srv );
			}
			untie @fileconf;
		}
	}
	return @srvarr;
}

# Get farm zones list for GSLB farms
sub getFarmZones    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $output    = -1;
	my $farm_type = &getFarmType( $farm_name );

	opendir ( DIR, "$configdir\/$farm_name\_$farm_type.cfg\/etc\/zones\/" );
	my @files = grep { /^[a-zA-Z]/ } readdir ( DIR );
	closedir ( DIR );

	return @files;
}

#
sub getGSLBFarmBootStatus    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $first         = "true";
	my $output        = -1;

	open FI, "<$configdir/$farm_filename/etc/config";

	while ( my $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line_a = split ( "\;", $line );
			$output = $line_a[1];
			chomp ( $output );
		}
	}
	close FI;

	return $output;
}

#function that check if the config file is OK.
sub getGSLBFarmConfigIsOK    # ($farm_name)
{
	my ( $fname ) = @_;

	my $ffile  = &getFarmFile( $fname );
	my $output = -1;
	my $gdnsd  = &getGlobalConfiguration( 'gdnsd' );

	my $gdnsd_command = "$gdnsd -c $configdir\/$ffile/etc checkconf";

	&zenlog( "running: $gdnsd_command" );
	my $run = `$gdnsd_command 2>&1`;
	$output = $?;
	&zenlog( "output: $run " );

	return $output;
}

# Returns farm PID
sub getGSLBFarmPid    # ($farm_name)
{
	my ( $fname ) = @_;

	my $type          = &getFarmType( $fname );
	my $file          = &getFarmFile( $fname );
	my $farm_filename = &getFarmFile( $fname );
	my $output        = -1;
	my $ps            = &getGlobalConfiguration( 'ps' );
	my $gdnsd         = &getGlobalConfiguration( 'gdnsd' );

	my @run =
	  `$ps -ef | grep "$gdnsd -c $configdir\/$farm_filename" | grep -v grep | awk {'print \$2'}`;

	chomp ( @run );
	
	if ( $run[0] )
	{
		$output = $run[0];
	}
	else
	{
		$output = "-";
	}

	return $output;
}

#
sub getGSLBFarmPidFile    # ($farm_name)
{
	my ( $farm_name ) = @_;

	return "$configdir\/$farm_name\_gslb.cfg\/etc\/gdnsd.pid";
}

#function that return indicated value from a HTTP Service
#vs return virtual server
sub getGSLBFarmVS    # ($farm_name,$service,$tag)
{
	my ( $fname, $svice, $tag ) = @_;

	my $output = "";
	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );

	my @fileconf;
	my $line;
	my @linesplt;
	use Tie::File;
	if ( $tag eq "ns" || $tag eq "resources" )
	{
		tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/zones/$svice";
		foreach $line ( @fileconf )
		{
			if ( $tag eq "ns" )
			{
				if ( $line =~ /@.*SOA .* hostmaster / )
				{
					@linesplt = split ( " ", $line );
					$output = $linesplt[2];
					last;
				}
			}
			if ( $tag eq "resources" )
			{
				if ( $line =~ /;index_.*/ )
				{
					my $tmpline = $line;
					$tmpline =~ s/multifo!|simplefo!//g;
					$output = "$output\n$tmpline";
				}
			}
		}
	}
	else
	{
		my $found      = 0;
		my $pluginfile = "";
		opendir ( DIR, "$configdir\/$fname\_$type.cfg\/etc\/plugins\/" );
		my @pluginlist = readdir ( DIR );

		foreach my $plugin ( @pluginlist )
		{
			tie @fileconf, 'Tie::File',
			  "$configdir\/$fname\_$type.cfg\/etc\/plugins\/$plugin";
			if ( grep ( /^\t$svice => /, @fileconf ) )
			{
				$pluginfile = $plugin;
			}
			untie @fileconf;
		}
		closedir ( DIR );
		tie @fileconf, 'Tie::File',
		  "$configdir\/$fname\_$type.cfg\/etc\/plugins\/$pluginfile";
		foreach $line ( @fileconf )
		{
			if ( $tag eq "backends" )
			{
				if ( $found == 1 && $line =~ /.*}.*/ )
				{
					last;
				}
				if ( $found == 1 && $line !~ /^$/ && $line !~ /.*service_types.*/ )
				{
					$output = "$output\n$line";
				}
				if ( $line =~ /\t$svice => / )
				{
					$found = 1;
				}
			}
			if ( $tag eq "algorithm" )
			{
				@linesplt = split ( " ", $line );
				if ( $linesplt[0] eq "simplefo" )
				{
					$output = "prio";
				}
				if ( $linesplt[0] eq "multifo" )
				{
					$output = "roundrobin";
				}
				last;
			}
			if ( $tag eq "plugin" )
			{
				@linesplt = split ( " ", $line );
				$output = $linesplt[0];
				last;
			}
			if ( $tag eq "dpc" )
			{
				if ( $found == 1 && $line =~ /.*}.*/ )
				{
					last;
				}
				if ( $found == 1 && $line =~ /.*service_types.*/ )
				{
					my @tmpline = split ( "=", $line );
					$output = $tmpline[1];
					$output =~ /_(\d+)(\s+)?$/;
					$output = $1;

					#~ $output =~ s/['\[''\]'' ']//g;
					#~ my @tmp = split ( "_", $output );
					#~ $output = $tmp[1];
					last;
				}
				if ( $line =~ /\t$svice => / )
				{
					$found = 1;
				}
			}
		}
	}
	untie @fileconf;

	return $output;
}

# Returns farm vip
sub getGSLBFarmVip    # ($info,$farm_name)
{
	my ( $info, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $i             = 0;

	open FI, "<$configdir/$farm_filename/etc/config";
	my @file = <FI>;
	close FI;

	foreach my $line ( @file )
	{
		if ( $line =~ /^options =>/ )
		{
			my $vip  = $file[$i + 1];
			my $vipp = $file[$i + 2];

			chomp ( $vip );
			chomp ( $vipp );

			my @vip  = split ( "\ ", $vip );
			my @vipp = split ( "\ ", $vipp );

			if ( $info eq "vip" )   { $output = $vip[2]; }
			if ( $info eq "vipp" )  { $output = $vipp[2]; }
			if ( $info eq "vipps" ) { $output = "$vip[2]\:$vipp[2]"; }
		}
		$i++;
	}

	return $output;
}

#
sub getGSLBStartCommand    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $gdnsd = &getGlobalConfiguration( 'gdnsd' );
	return "$gdnsd -c $configdir\/$farm_name\_gslb.cfg/etc start";
}

#
sub getGSLBStopCommand     # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $gdnsd = &getGlobalConfiguration( 'gdnsd' );
	return "$gdnsd -c $configdir\/$farm_name\_gslb.cfg/etc stop";
}

sub remFarmServiceBackend    # ($id,$farm_name,$service)
{
	my ( $id, $fname, $srv ) = @_;

	my $output = 0;
	my $ftype  = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );

	my @fileconf;
	my $line;
	my $index      = 0;
	my $pluginfile = "";
	use Tie::File;
	my $found;

	#Find the plugin file
	opendir ( DIR, "$configdir\/$ffile\/etc\/plugins\/" );
	my @pluginlist = readdir ( DIR );
	foreach my $plugin ( @pluginlist )
	{
		tie @fileconf, 'Tie::File', "$configdir\/$ffile\/etc\/plugins\/$plugin";
		if ( grep ( /^\t$srv => /, @fileconf ) )
		{
			$pluginfile = $plugin;
		}
		untie @fileconf;
	}
	closedir ( DIR );

	tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/plugins/$pluginfile";
	foreach $line ( @fileconf )
	{
		if ( $line =~ /^\t$srv => / )
		{
			$found = 1;
			$index++;
			next;
		}
		if ( $found == 1 && $line =~ /primary => / )
		{
			$output = -2;
			last;
		}
		if ( $found == 1 && $line =~ /$id => / )
		{
			my @backendslist = grep ( /^\s+[1-9].* =>/, @fileconf );
			my $nbackends = @backendslist;
			if ( $nbackends == 1 )
			{
				$output = -2;
			}
			else
			{
				splice @fileconf, $index, 1;
			}
			last;
		}
		$index++;
	}
	untie @fileconf;
	$output = $output + $?;

	return $output;
}

sub remFarmZoneResource    # ($id,$farm_name,$service)
{
	my ( $id, $fname, $service ) = @_;

	my $output = 0;
	my $ftype  = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );

	my @fileconf;
	my $line;
	my $index = 0;
	use Tie::File;
	tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/zones/$service";
	foreach $line ( @fileconf )
	{
		if ( $line =~ /\;index_$id/ )
		{
			splice @fileconf, $index, 1;
		}
		$index++;
	}
	untie @fileconf;
	$output = $?;
	&setFarmZoneSerial( $fname, $service );
	$output = $output + $?;

	return $output;
}

sub runFarmReload    # ($farm_name)
{
	my ( $fname ) = @_;

	my $type = &getFarmType( $fname );
	my $output;
	my $gdnsd = &getGlobalConfiguration( 'gdnsd' );

	my $gdnsd_command = "$gdnsd -c $configdir\/$fname\_$type.cfg/etc reload-zones";

	&zenlog( "running $gdnsd_command" );
	zsystem( "$gdnsd_command >/dev/null 2>&1" );
	$output = $?;
	if ( $output != 0 )
	{
		$output = -1;
	}

	return $output;
}

#
sub runGSLBFarmServerDelete    # ($ids,$farm_name,$service)
{
	my ( $ids, $farm_name, $service ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $index         = 0;

	use Tie::File;
	tie my @configfile, 'Tie::File', "$configdir/$farm_filename/etc/zones/$service";

	foreach my $line ( @configfile )
	{
		if ( $line =~ /\;index_/ )
		{
			my @linesplt = split ( "\;index_", $line );
			my $param = $linesplt[1];
			if ( $ids !~ /^$/ && $ids eq $param )
			{
				splice @configfile, $index, 1,;
			}
		}
		$index++;
	}
	untie @configfile;
	$output = $?;

	return $output;
}

#
sub setFarmZoneResource  # ($id,$resource,$ttl,$type,$rdata,$farm_name,$service)
{
	my ( $id, $resource, $ttl, $type, $rdata, $farm_name, $service ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $line;
	my $param;
	my $index = 0;
	my $lb    = "";
	my $flag  = "false";

	if ( $type =~ /DYN./ )
	{
		$lb = &getFarmVS( $farm_name, $rdata, "plugin" );
		$lb = "$lb!";
	}
	use Tie::File;
	tie my @configfile, 'Tie::File', "$configdir/$farm_filename/etc/zones/$service";

	foreach my $line ( @configfile )
	{
		if ( $line =~ /\;index_/ )
		{
			my @linesplt = split ( "\;index_", $line );
			$param = $linesplt[1];

			if ( $id !~ /^$/ && $id eq $param )
			{
				$line = "$resource\t$ttl\t$type\t$lb$rdata ;index_$param";
				$flag = "true";
			}
			else
			{
				$index = $param + 1;
			}
		}
	}
	if ( $id =~ /^$/ )
	{
		push @configfile, "$resource\t$ttl\t$type\t$lb$rdata ;index_$index";
	}
	untie @configfile;
	&setFarmZoneSerial( $farm_name, $service );

	my $output = $?;

	if ( $flag eq "false" )
	{
		$output = -2;
	}

	return $output;
}

sub setFarmZoneSerial    # ($farm_name,$zone)
{
	my ( $fname, $zone ) = @_;
	my $ftype  = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	my @fileconf;
	use Tie::File;
	tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/zones/$zone";
	my $index;
	foreach my $line ( @fileconf )
	{
		if ( $line =~ /@\tSOA / )
		{
			my $date = `date +%s`;
			splice @fileconf, $index + 1, 1, "\t$date";
		}
		$index++;
	}
	untie @fileconf;
	$output = $?;

	return $output;
}

#
sub runGSLBFarmCreate    # ($vip,$vip_port,$farm_name)
{
	my ( $fvip, $fvipp, $fname ) = @_;

	my $httpport = &getRandomPort();
	my $type     = "gslb";
	my $ffile    = &getFarmFile( $fname );
	my $output   = -1;
	if ( $ffile != -1 )
	{
		# the farm name already exists
		$output = -2;
		return $output;
	}

	my $farm_path = "$configdir/${fname}_${type}\.cfg";
	&zenlog( "running 'Create' for $fname farm $type in path $farm_path " );

	mkdir "$farm_path";
	mkdir "$farm_path\/etc";
	mkdir "$farm_path\/etc\/zones";
	mkdir "$farm_path\/etc\/plugins";

	open ( my $file, ">", "$configdir\/$fname\_$type.cfg\/etc\/config" );
	print $file ";up\n"
	  . "options => {\n"
	  . "   listen = $fvip\n"
	  . "   dns_port = $fvipp\n"
	  . "   http_port = $httpport\n"
	  . "   http_listen = 127.0.0.1\n" . "}\n\n";
	print $file "service_types => { \n\n}\n\n";
	print $file
	  "plugins => { \n\textmon => { helper_path => \"/usr/local/zenloadbalancer/app/gdnsd/gdnsd_extmon_helper\" },\n}\n\n";
	close $file;

	#run farm
	my $exec = &getGSLBStartCommand( $fname );
	&zenlog( "running $exec" );
	zsystem( "$exec > /dev/null 2>&1" );

	#TODO
	#$output = $?;
	$output = 0;

	if ( $output != 0 )
	{
		&runFarmDelete( $fname );
	}
	return $output;
}

# Get http port  where is the gslb stats
sub getGSLBControlPort    # ( $farm_name )
{
	my $farmName = shift;
	my $port     = -1;
	my $ffile    = &getFarmFile( $farmName );
	$ffile = "$configdir/$ffile/etc/config";

	tie my @file, 'Tie::File', $ffile;
	foreach my $line ( @file )
	{
		if ( $line =~ /http_port =\s*(\d+)/ )
		{
			$port = $1 + 0;
			last;
		}
	}
	untie @file;
	return $port;
}

# Set http port  where is the gslb stats
sub setGSLBControlPort    # ( $farm_name )
{
	my $farmName = shift;

	# set random port
	my $port  = &getRandomPort();
	my $ffile = &getFarmFile( $farmName );
	$ffile = "$configdir/$ffile/etc/config";

	tie my @file, 'Tie::File', $ffile;
	foreach my $line ( @file )
	{
		if ( $line =~ /http_port =/ )
		{
			$line = "   http_port = $port\n";
			last;
		}
	}
	untie @file;
	return $port;
}

#
sub setGSLBFarmBootStatus    # ($farm_name, $status)
{
	my ( $farm_name, $status ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output;

	use Tie::File;
	tie my @filelines, 'Tie::File', "$configdir\/$farm_filename\/etc\/config";
	my $first = 1;
	foreach ( @filelines )
	{
		if ( $first eq 1 )
		{
			if ( $status eq "start" )
			{
				s/\;down/\;up/g;
			}
			else
			{
				s/\;up/\;down/g;
			}
			$first = 0;
			last;
		}
	}
	untie @filelines;

	return $output;
}

# Delete an existing Service in a GSLB farm
sub setGSLBFarmDeleteService    # ($farm_name,$service)
{
	my ( $fname, $svice ) = @_;

	my $output     = -1;
	my $ftype      = &getFarmType( $fname );
	my $pluginfile = "";
	my $srv_port;

	#Find the plugin file
	opendir ( DIR, "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/" );
	my @pluginlist = readdir ( DIR );

	# look for the plugin file including the service
	foreach my $plugin ( @pluginlist )
	{
		tie my @fileconf, 'Tie::File',
		  "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/$plugin";
		if ( grep ( /^\t$svice => /, @fileconf ) )
		{
			$pluginfile = $plugin;
		}
		untie @fileconf;
	}

	closedir ( DIR );

	if ( $pluginfile eq "" )
	{
		$output = -1;
	}
	else
	{
		# do not remove service if it is still in use
		my ( $plugin_name ) = split ( '.cfg', $pluginfile );
		my $grep_cmd =
		  qq{grep '$plugin_name!$svice ;' $configdir\/$fname\_$ftype.cfg\/etc\/zones/* 2>/dev/null};

		my $grep_output = `$grep_cmd`;

		if ( $grep_output ne '' )
		{
			$output = -2;    # service in use
			return $output;
		}

		# service not in use, proceed to remove it
		my $found   = 0;
		my $index   = 0;
		my $deleted = 0;

		#Delete section from the plugin file
		tie my @fileconf, 'Tie::File',
		  "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/$pluginfile";

		while ( $deleted == 0 )
		{
			if ( $fileconf[$index] =~ /^\t$svice => / )
			{
				$found = 1;
			}

			if ( $found == 1 )
			{
				if ( $fileconf[$index] !~ /^\t\}\h*$/ )
				{
					if ( $fileconf[$index] =~ /service_types = tcp_(\d+)/ )
					{
						$srv_port = $1;
					}
					splice @fileconf, $index, 1;
				}
				else
				{
					splice @fileconf, $index, 1;
					$found   = 0;
					$output  = 0;
					$deleted = 1;
				}
			}

			if ( $found == 0 )
			{
				$index++;
			}
		}

		#Bug fixed: if there are plugin files included, without services, gdnsd crashes.
		# if the plugin file has no services
		if ( scalar @fileconf < 5 )    #=3
		{
			tie my @config_file, 'Tie::File', "$configdir\/$fname\_$ftype.cfg\/etc\/config";

			# remove the line of that plugin
			@config_file = grep { !/plugins\/$pluginfile/ } @config_file;
			untie @config_file;
		}

		&setGSLBDeleteFarmGuardian( $fname, $svice );

		# Delete port configuration from config file
		if ( !getCheckPort( $fname, $srv_port ) )
		{
			$output = &setGSLBRemoveTcpPort( $fname, $srv_port );
		}
		untie @fileconf;
	}

	return $output;
}

# Delete an existing Zone in a GSLB farm
sub setGSLBFarmDeleteZone    # ($farm_name,$service)
{
	my ( $farm_name, $service ) = @_;

	my $output = -1;

	use File::Path 'rmtree';
	rmtree( ["$configdir\/$farm_name\_gslb.cfg\/etc\/zones\/$service"] );
	$output = 0;

	return $output;
}

sub setGSLBFarmNewBackend    # ($farm_name,$service,$lb,$id,$ipaddress)
{
	my ( $fname, $srv, $lb, $id, $ipaddress ) = @_;

	my $output = 0;
	my $ftype  = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );

	my @fileconf;
	my $line;
	my @linesplt;
	my $found      = 0;
	my $index      = 0;
	my $idx        = 0;
	my $pluginfile = "";
	use Tie::File;

	#Find the plugin file
	opendir ( DIR, "$configdir\/$ffile\/etc\/plugins\/" );
	my @pluginlist = readdir ( DIR );
	foreach my $plugin ( @pluginlist )
	{
		tie @fileconf, 'Tie::File', "$configdir\/$ffile\/etc\/plugins\/$plugin";
		if ( grep ( /^\t$srv => /, @fileconf ) )
		{
			$pluginfile = $plugin;
		}
		untie @fileconf;
	}
	closedir ( DIR );
	tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/plugins/$pluginfile";
	foreach $line ( @fileconf )
	{
		if ( $line =~ /^\t$srv => / )
		{
			$found = 1;
			$index++;
			next;
		}
		if ( $found == 1 && $lb eq "prio" && $line =~ /\}/ && $id eq "primary" )
		{
			splice @fileconf, $index, 0, "		$id => $ipaddress";
			last;
		}
		if (    $found == 1
			 && $lb eq "prio"
			 && $line =~ /primary => /
			 && $id eq "primary" )
		{
			splice @fileconf, $index, 1, "		$id => $ipaddress";
			last;
		}
		if ( $found == 1 && $lb eq "prio" && $line =~ /\}/ && $id eq "secondary" )
		{
			splice @fileconf, $index, 0, "		$id => $ipaddress";
			last;
		}
		if (    $found == 1
			 && $lb eq "prio"
			 && $line =~ /secondary => /
			 && $id eq "secondary" )
		{
			splice @fileconf, $index, 1, "		$id => $ipaddress";
			last;
		}
		if ( $found == 1 && $lb eq "roundrobin" && $line =~ /\t\t$id => / )
		{
			splice @fileconf, $index, 1, "		$id => $ipaddress";
			last;
		}
		if ( $found == 1 && $lb eq "roundrobin" && $line =~ / => / )
		{
			# What is the latest id used?
			my @temp = split ( " => ", $line );
			$idx = $temp[0];
			$idx =~ s/^\s+//;
		}
		if ( $found == 1 && $lb eq "roundrobin" && $line =~ /\}/ )
		{
			$idx++;
			splice @fileconf, $index, 0, "		$idx => $ipaddress";
			last;
		}
		$index++;
	}
	untie @fileconf;
	$output = $?;

	return $output;
}

# Create a new Service in a GSLB farm
sub setGSLBFarmNewService    # ($farm_name,$service,$algorithm)
{
	my ( $fname, $svice, $alg ) = @_;

	my $output = -1;
	my $ftype  = &getFarmType( $fname );
	my $gsalg  = "simplefo";

	if ( $alg eq "roundrobin" )
	{
		$gsalg = "multifo";
	}
	else
	{
		if ( $alg eq "prio" )
		{
			$gsalg = "simplefo";
		}
	}
	if ( grep ( /^$svice$/, &getFarmServices( $fname ) ) )
	{
		$output = -1;
	}
	else
	{
		if ( !( -e "$configdir/${fname}_${ftype}.cfg/etc/plugins/${gsalg}.cfg" ) )
		{
			open FO, ">$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/$gsalg.cfg";
			print FO "$gsalg => {\n\tservice_types = up\n";
			print FO "\t$svice => {\n\t\tservice_types = tcp_80\n";
			if ( $gsalg eq "simplefo" )
			{
				print FO "\t\tprimary => 127.0.0.1\n";
				print FO "\t\tsecondary => 127.0.0.1\n";
			}
			else
			{
				print FO "\t\t1 => 127.0.0.1\n";
			}
			print FO "\t}\n}\n";
			close FO;
			$output = 0;
		}
		else
		{
			# Include the service in the plugin file
			tie my @fileconf, 'Tie::File',
			  "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/$gsalg.cfg";
			if ( grep ( /^\t$svice =>.*/, @fileconf ) )
			{
				$output = -1;
			}
			else
			{
				my $found = 0;
				my $index = 0;
				foreach my $line ( @fileconf )
				{
					if ( $line =~ /$gsalg => / )
					{
						$found = 1;
					}
					if ( $found == 1 && $line =~ /service_types / )
					{
						$index++;

						#splice @fileconf,$index,0,"     \$include{plugins\/$svice.cfg},";
						if ( $gsalg eq "simplefo" )
						{
							splice @fileconf, $index, 0,
							  (
								"\t$svice => {",
								"\t\tservice_types = tcp_80",
								"\t\tprimary => 127.0.0.1",
								"\t\tsecondary => 127.0.0.1",
								"\t}"
							  );
						}
						else
						{
							splice @fileconf, $index, 0,
							  ( "\t$svice => {", "\t\tservice_types = tcp_80", "\t\t1 => 127.0.0.1",
								"\t}" );
						}
						$found = 0;
						last;
					}
					$index++;
				}
				$output = 0;
			}
			untie @fileconf;
		}
		if ( $output == 0 )
		{
			# Include the plugin file in the main configuration
			tie my @fileconf, 'Tie::File', "$configdir\/$fname\_$ftype.cfg\/etc\/config";
			if ( ( grep ( /include{plugins\/$gsalg\.cfg}/, @fileconf ) ) == 0 )
			{
				my $found = 0;
				my $index = 0;
				foreach my $line ( @fileconf )
				{
					if ( $line =~ /plugins => / )
					{
						$found = 1;
						$index++;
					}
					if ( $found == 1 )
					{
						splice @fileconf, $index, 0, "\t\$include{plugins\/$gsalg.cfg},";
						last;
					}
					$index++;
				}
			}
			untie @fileconf;
			&setFarmVS( $fname, $svice, "dpc", "80" );
		}
	}

	return $output;
}

# Create a new Zone in a GSLB farm
sub setGSLBFarmNewZone    # ($farm_name,$service)
{
	my ( $fname, $zone ) = @_;

	my $output = -1;
	my $ftype  = &getFarmType( $fname );
	my $fvip   = &getFarmVip( "vip", $fname );

	opendir ( DIR, "$configdir\/$fname\_$ftype.cfg\/etc\/zones\/" );
	my @files = grep { /^$zone/ } readdir ( DIR );
	closedir ( DIR );

	if ( scalar @files == 0 )
	{
		open ( my $file, ">", "$configdir\/$fname\_$ftype.cfg\/etc\/zones\/$zone" )
		  or warn "cannot open > $configdir\/$fname\_$ftype.cfg\/etc\/zones\/$zone: $!";
		print $file "@	SOA ns1 hostmaster (\n" . "	1\n"
		  . "	7200\n"
		  . "	1800\n"
		  . "	259200\n"
		  . "	900\n" . ")\n\n";
		print $file "@		NS	ns1 ;index_0\n";
		print $file "ns1		A	$fvip ;index_1\n";
		close $file;

		$output = 0;
	}
	else
	{
		$output = 1;
	}

	return $output;
}

#
sub setGSLBFarmStatus    # ($farm_name, $status, $writeconf)
{
	my ( $farm_name, $status, $writeconf ) = @_;

	my $command;

	unlink ( "/tmp/$farm_name.lock" );

	if ( $writeconf eq "true" )
	{
		&setGSLBFarmBootStatus( $farm_name, $status );
	}

	if ( $status eq "start" )
	{
		$command = &getGSLBStartCommand( $farm_name );
	}
	else
	{
		$command = &getGSLBStopCommand( $farm_name );
	}

	&zenlog( "setGSLBFarmStatus(): Executing $command" );
	zsystem( "$command > /dev/null 2>&1" );

	#TODO
	my $output = 0;

	if ( $output != 0 )
	{
		$output = -1;
	}

	return $output;
}

=begin nd
        Function: setGSLBRemoveTcpPort

        This functions removes tcp_port config from gdnsd config file

        Parameters:

                fname - farm name
                port  - tcp_PORT to delete

        Returns:
        
                0	- successful
				-3	- error in config file format
               
=cut

# &setGSLBRemoveTcpPort ($farmName,$port);
sub setGSLBRemoveTcpPort
{
	my ( $fname, $port ) = @_;
	my $ffile = &getFarmFile( $fname );
	my $found = 0;
	my $index = 1;

	use Tie::File;
	tie my @fileconf, 'Tie::File', "$configdir/$ffile/etc/config";

	while ( ( $fileconf[$index] !~ /^plugins => / ) && ( $found !~ 2 ) )
	{
		my $line = $fileconf[$index];

		if ( $line =~ /tcp_$port => / )
		{
			$found = 1;
		}

		if ( $found == 1 )
		{
			my $rs = splice ( @fileconf, $index, 1 );

			if ( $line =~ /\}/ )
			{
				$found = 2;
			}
		}

		if ( !$found )
		{
			$index++;
		}
	}

	untie @fileconf;

	$found = -3 if ( $found == 1 );
	$found = 0 if ( $found == 0 || $found == 2 );

	return $found;
}

=begin nd
        Function: getCheckPort

        This function checks if some service uses this port

        Parameters:

                fname 	- farm name
                checkport - port to check 

        Returns:
        
                servicePorts  - number of services are using the port
               
=cut

# &getCheckPort ( $fname, $checkPort );
sub getCheckPort
{
	my ( $fname, $checkPort ) = @_;

	my $ftype        = &getFarmType( $fname );
	my $servicePorts = 0;

	use Tie::File;

	# select all ports used in plugins
	opendir ( DIR, "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/" );

	#~ opendir ( DIR, "plugins\/" );
	my @pluginlist = readdir ( DIR );
	closedir ( DIR );
	foreach my $plugin ( @pluginlist )
	{
		if ( $plugin !~ /^\./ )
		{
			my @fileconf = ();

			tie @fileconf, 'Tie::File',
			  "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/$plugin";

			#~ tie @fileconf, 'Tie::File', "plugins\/$plugin";
			$servicePorts += grep ( /service_types = tcp_$checkPort/,   @fileconf );
			$servicePorts += grep ( /service_types = .+_fg_$checkPort/, @fileconf );

			untie @fileconf;
		}
	}
	return $servicePorts;
}

=begin nd
        Function: setGSLBFarmVS

        This function can change name server or dpc

        Parameters:

                fname 	- farm name
                service - service name
                param	- param to modificate
                value	- value for the param

        Returns:
        
                newCmd  - command with extmon format
                
        See Also:
                
                
        More info:

                
=cut

#set values for a service
sub setGSLBFarmVS    # ($farm_name,$service,$tag,$string)
{
	my ( $fname, $svice, $tag, $stri ) = @_;

	my $output = "";

	my $type  = &getFarmType( $fname );
	my $ffile = &getFarmFile( $fname );

	my $pluginfile;
	my @fileconf;
	my $line;
	my $param;
	my @linesplt;
	my $tcp_port;

	use Tie::File;

	if ( $tag eq "ns" )
	{
		tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/zones/$svice";
		foreach $line ( @fileconf )
		{
			if ( $line =~ /^@\tSOA .* hostmaster / )
			{
				@linesplt = split ( " ", $line );
				$param    = $linesplt[2];
				$line     = "@\tSOA $stri hostmaster (";
			}
			if ( $line =~ /\t$param / )
			{
				$line =~ s/\t$param /\t$stri /g;
			}
			if ( $line =~ /^$param\t/ )
			{
				$line =~ s/^$param\t/$stri\t/g;
			}
		}
		untie @fileconf;
		&setFarmZoneSerial( $fname, $svice );
	}

	if ( $tag eq "dpc" )
	{
		my $actualPort;
		my $srvConf;
		my @srvCp;
		my $firstIndNew;
		my $offsetIndNew;
		my $firstIndOld;
		my $offsetIndOld;
		my $newPortFlag;
		my $existPortFlag = &getCheckPort( $fname, $stri );
		my $found         = 0;
		my $existFG       = 0;
		my $newTcp =
		    "\ttcp_$stri => {\n"
		  . "\t\tplugin = tcp_connect,\n"
		  . "\t\tport = $stri,\n"
		  . "\t\tup_thresh = 2,\n"
		  . "\t\tok_thresh = 2,\n"
		  . "\t\tdown_thresh = 2,\n"
		  . "\t\tinterval = 5,\n"
		  . "\t\ttimeout = 3,\n" . "\t}\n";
		my $newFG =
		    "\t${svice}_fg_$stri => {\n"
		  . "\t\tplugin = extmon,\n"
		  . "\t\tup_thresh = 2,\n"
		  . "\t\tok_thresh = 2,\n"
		  . "\t\tdown_thresh = 2,\n"
		  . "\t\tinterval = 5,\n"
		  . "\t\ttimeout = 3,\n"
		  . "\t\tcmd = [1],\n" . "\t}\n";

		# cmd = [1], it's a initial value for avoiding syntasis error in config file,
		# but can't be active it with this value.

		#Find the plugin file
		opendir ( DIR, "$configdir\/$ffile\/etc\/plugins\/" );
		my @pluginlist = readdir ( DIR );
		foreach my $plugin ( @pluginlist )
		{
			tie @fileconf, 'Tie::File', "$configdir\/$ffile\/etc\/plugins\/$plugin";
			if ( grep ( /^\t$svice => /, @fileconf ) )
			{
				$pluginfile = $plugin;
			}
			untie @fileconf;
		}
		closedir ( DIR );

		# Change configuration in plugin file
		tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/plugins/$pluginfile";
		foreach $line ( @fileconf )
		{
			if ( $found == 1 && $line =~ /.*}.*/ )
			{
				last;
			}
			if ( $found == 1 && $line =~ /service_types = (${svice}_fg_|tcp_)(\d+)/ )
			{
				$actualPort = $2;
				$line       = "\t\tservice_types = $1$stri";
				$output     = "0";
				last;
			}
			if ( $line =~ /\t$svice => / )
			{
				$found = 1;
			}
		}
		untie @fileconf;

		if ( $output eq "0" )
		{
			my $srvAsocFlag = &getCheckPort( $fname, $actualPort );
			my $found       = 0;
			my $index       = 1;

			# Checking if tcp_port is defined
			tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/config";
			my $existTcp = grep ( /tcp_$actualPort =>/, @fileconf );
			untie @fileconf;

			if ( !$existTcp )
			{
				$newPortFlag = 1;
			}

			else
			{
				tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/config";
				while ( $fileconf[$index] !~ /^plugins => / )
				{
					my $line = $fileconf[$index];

					# Checking if exist conf block for the new port. Keeping its index
					if ( $fileconf[$index] =~ s/(${svice}_fg_)\d+/$1$stri/ )
					{
						$existFG = 1;
					}

					if ( $found == 1 )
					{
						my $line2 = $line;
						$line2 =~ s/port =.*,/port = $stri,/;
						$line2 =~ s/cmd = \[(.+), "-p", "\d+"/cmd = \[$1, "-p", "$stri"/;
						push @srvCp, $line2;
						$offsetIndOld++;

						# block finished
						if ( $line =~ /.*}.*/ )
						{
							$found = 0;
						}
					}
					if ( $line =~ /tcp_$actualPort => / )
					{
						my $line2 = $line;
						$line2 =~ s/tcp_$actualPort => /tcp_$stri => /;
						$found = 1;
						push @srvCp, $line2;
						$firstIndOld = $index;
						$offsetIndOld++;
					}

					# keeping index for actual tcp_port
					if ( $found == 2 )
					{
						$offsetIndNew++;

						# conf block finished
						if ( $line =~ /.*}.*/ )
						{
							$found = 0;
						}
					}
					if ( ( $line =~ /tcp_$stri => / ) && ( $stri ne $actualPort ) )
					{
						$found = 2;
						$offsetIndNew++;
						$firstIndNew = $index;
					}

					$index++;
				}
				untie @fileconf;

				# delete tcp_port if this is not used
				tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/config";
				if ( ( $stri eq $actualPort ) && $existPortFlag )
				{
					splice ( @fileconf, $firstIndOld, $offsetIndOld );
				}
				else
				{
					if ( $firstIndNew > $firstIndOld )
					{
						if ( $existPortFlag )
						{
							splice ( @fileconf, $firstIndNew, $offsetIndNew );
						}
						if ( !$srvAsocFlag )
						{
							splice ( @fileconf, $firstIndOld, $offsetIndOld );
						}
					}
					else
					{
						if ( !$srvAsocFlag )
						{
							splice ( @fileconf, $firstIndOld, $offsetIndOld );
						}
						if ( $existPortFlag )
						{
							splice ( @fileconf, $firstIndNew, $offsetIndNew );
						}
					}
				}
				untie @fileconf;

			}

			# create the new port configuration
			$index = 0;
			my $firstIndex = 0;
			tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/config";
			foreach $line ( @fileconf )
			{
				if ( $line =~ /service_types => / )
				{
					$index++;
					$firstIndex = $index;

					# New port
					if ( $newPortFlag )
					{
						splice @fileconf, $index, 0, $newTcp;
					}
					else
					{
						foreach my $confline ( @srvCp )
						{
							splice @fileconf, $index++, 0, $confline;
						}
					}
					last;
				}
				$index++;
			}
			untie @fileconf;

			# if it's a new service, it creates fg config
			if ( !$existFG )
			{
				tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/config";
				splice @fileconf, $firstIndex, 0, $newFG;
				untie @fileconf;
			}

		}
	}
	return $output;
}

# Set farm virtual IP and virtual PORT
sub setGSLBFarmVirtualConf    # ($vip,$vip_port,$farm_name)
{
	my ( $vip, $vipp, $fname ) = @_;

	my $fconf = &getFarmFile( $fname );
	my $type  = &getFarmType( $fname );
	my $stat  = -1;

	&zenlog( "setting 'VirtualConf $vip $vipp' for $fname farm $type" );

	my $index = 0;
	my $found = 0;
	tie my @fileconf, 'Tie::File', "$configdir/$fconf/etc/config";

	foreach my $line ( @fileconf )
	{
		if ( $line =~ /options => / )
		{
			$found = 1;
		}
		if ( $found == 1 && $line =~ / listen = / )
		{
			$line =~ s/$line/   listen = $vip/g;
		}
		if ( $found == 1 && $line =~ /dns_port = / )
		{
			$line =~ s/$line/   dns_port = $vipp/g;
		}
		if ( $found == 1 && $line =~ /\}/ )
		{
			last;
		}
		$index++;
	}
	untie @fileconf;
	$stat = $?;

	return $stat;
}

#function that renames a farm
sub setGSLBNewFarmName    # ($farm_name,$new_farm_name)
{
	my ( $fname, $newfname ) = @_;

	my $rrdap_dir = &getGlobalConfiguration( "rrdap_dir" );
	my $rrd_dir   = &getGlobalConfiguration( "rrd_dir" );
	my $configdir = &getGlobalConfiguration( "configdir" );
	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $newfname =~ /^$/ )
	{
		&zenlog( "error 'NewFarmName $newfname' is empty" );
		return -2;
	}

	&zenlog( "setting 'NewFarmName $newfname' for $fname farm $type" );

	my $newffile = "$newfname\_$type.cfg";
	rename ( "$configdir\/$ffile", "$configdir\/$newffile" );
	$output = 0;

	# rename rrd
	rename ( "$rrdap_dir/$rrd_dir/$fname-farm.rrd",
			 "$rrdap_dir/$rrd_dir/$newfname-farm.rrd" );

	# delete old graphs
	unlink ( "img/graphs/bar$fname.png" );

	return $output;
}

# translate dns service descriptor to service name
# if the same backend is in several services, return all service names
# e.j.   typeService = tcp_54
sub dnsServiceType    #  dnsServiceType ( $farmname, $ip, $tcp_port )
{
	my ( $fname, $ip, $serviceType ) = @_;
	my $name;
	my @serviceNames;
	my $ftype = &getFarmType( $fname );
	my @file;
	my $findePort = 0;    # var aux

	opendir ( DIR, "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/" );
	my @pluginlist = readdir ( DIR );
	closedir ( DIR );
	foreach my $plugin ( @pluginlist )
	{

		if ( $plugin !~ /^\./ )
		{
			@file = ();
			tie @file, 'Tie::File', "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/$plugin";

			foreach my $line ( @file )
			{
				$line =~ /^\t(\w+) => \{/;

				# find potential name
				if ( $1 )
				{
					$name      = $1;
					$findePort = 0;
				}

				# find potential port
				if ( $name && $line =~ /$serviceType/ )
				{
					$findePort = 1;
				}

				# find ip, add servername to array
				if ( $findePort && $line =~ /$ip/ ) { push @serviceNames, $name; }
			}

			untie @file;
		}
	}
	return @serviceNames;
}

# this function return one string with json format
sub getGSLBGdnsdStats    # &getGSLBGdnsdStats ( )
{
	my $farmName   = shift;
	my $wget       = &getGlobalConfiguration( 'wget' );
	my $httpPort   = &getGSLBControlPort( $farmName );
	my $gdnsdStats = `$wget -qO- http://127.0.0.1:$httpPort/json`;

	my $stats;
	if ( $gdnsdStats )
	{
		$stats = decode_json( $gdnsdStats );
	}
	return $stats;
}

#
sub getGSLBFarmEstConns    # ($farm_name,@netstat)
{
	my ( $farm_name, @netstat ) = @_;

	my $vip      = &getFarmVip( "vip",  $farm_name );
	my $vip_port = &getFarmVip( "vipp", $farm_name );

	return
	  &getNetstatFilter( "udp", "",
						 "src=.* dst=$vip sport=.* dport=$vip_port .*src=.*",
						 "", @netstat );
}

## GSLB FARMGUARDIAN FUNCTIONS

=begin nd
        Function: getGSLBCommandInExtmonFormat

        Transform command with farm guardian format to command with extmon format,
        this function is used to show the command in GUI.

        Parameters:

                cmd		- command with farm guardian format
                port	- port where service is checking

        Returns:
        
                newCmd  - command with extmon format
                
        See Also:
                
                changeCmdToFGFormat
                
        More info:

			Farmguardian Fotmat	: bin -x option...
			Extmon Format		: "bin", "-x", "option"...
                
=cut

#	&getGSLBCommandInExtmonFormat( $cmd, $port );
sub getGSLBCommandInExtmonFormat
{
	my ( $cmd, $port ) = @_;

	my $libexec_dir = &getGlobalConfiguration ( 'libexec_dir' );
	my @aux = split ( ' ', $cmd );
	my $newCmd = "\"$libexec_dir/$aux[0]\"";
	my $stringArg;
	my $flag;

	splice @aux, 0, 1;

	foreach my $word ( @aux )
	{
		# Argument is between ""
		if ( $word =~ /^".+"$/ )
		{
			$word =~ s/^"//;
			$word =~ s/"$//;
		}

		# finish a string
		if ( $word =~ /\"$/ && $flag )
		{
			$flag = 0;
			chop $word;
			$word = "$stringArg $word";
		}

		# part of a string
		elsif ( $flag )
		{
			$stringArg .= " $word";
			next;
		}

		# begin a string
		elsif ( $word =~ /^"\w/ )
		{
			$flag = 1;
			$word =~ s/^.//;
			$stringArg = $word;
			next;
		}

		if ( $word eq 'PORT' )
		{
			$word = $port;
		}

		$word =~ s/HOST/%%ITEM%%/;
		if ( !$flag )
		{
			$newCmd .= ", \"$word\"";
		}
	}
	$newCmd =~ s/^, //;

	return $newCmd;
}

=begin nd
        Function: getGSLBCommandInFGFormat

        Transform command with extmon format to command with fg format,
        this function is used to show the command in GUI.

        Parameters:

                cmd		- command with extmon format
                port	- port where service is checking

        Returns:
        
                newCmd  - command with farm guardian format
                
        See Also:
                
                changeCmdToExtmonFormat
                
        More info:

			Farmguardian Fotmat	: bin -x option...
			Extmon Format		: "bin", "-x", "option"...
			
=cut

# &getGSLBCommandInFGFormat ( $cmd, $port );
sub getGSLBCommandInFGFormat
{
	my ( $cmd, $port ) = @_;

	my $libexec_dir = &getGlobalConfiguration ( 'libexec_dir' );
	my $newCmd;
	my @aux = split ( ', ', $cmd );
	my $flagPort;
	my $newCmd = $aux[0];

	splice @aux, 0, 1;

	$newCmd =~ s/$libexec_dir\///;
	$newCmd =~ s/^"(.+)"$/$1/;

	foreach my $word ( @aux )
	{
		if ( $word =~ '-p' )
		{
			$flagPort = 1;
		}

		# dns only can check one port
		if ( $flagPort && $word =~ /^"$port"$/ )
		{
			$word     = "PORT";
			$flagPort = 0;
		}

		# change HOST param from FG to %%ITEM%% from extmon
		$word =~ s/%%ITEM%%/HOST/;

		# remove " only if $word isn't a string
		if ( $word !~ / / )
		{
			$word =~ s/^"(.+)"$/$1/;
		}
		$newCmd .= " $word";
	}
	return $newCmd;
}

=begin nd
        Function: getGSLBFarmGuardianParams

        Get farmguardian configuration

        Parameters:

                fname 	- farm name
                service - service name

        Returns:
        
                @output =
					time  - interval time to repeat cmd
					cmd	  - command to check backend

=cut

#	&getGSLBFarmGuardianParams( farmName, $service );
sub getGSLBFarmGuardianParams
{
	my ( $fname, $service ) = @_;
	my $ftype = &getFarmType( $fname );

	my $cmd;
	my $time;
	my $flagSvc = 0;

	my $port = &getFarmVS( $fname, $service, "dpc" );

	tie my @file, 'Tie::File', "$configdir\/$fname\_$ftype.cfg\/etc\/config";

	foreach my $line ( @file )
	{
		# Begin service block
		if ( $line =~ /^\t$service.+ =>/ )
		{
			$flagSvc = 1;
		}
		elsif ( $flagSvc )
		{
			# get interval time
			if ( $line =~ /interval = (\d+),/ )
			{
				$time = $1;
				next;
			}

			# get cmd
			elsif ( $line =~ /cmd = \[(.+)\],/ )
			{
				$cmd = $1;
				$cmd = getGSLBCommandInFGFormat( $cmd, $port );
				next;
			}
		}
		if ( $flagSvc && $line =~ /\t}/ )
		{
			last;
		}
	}

	# $cmd it's initialized "1" for avoid systasis error
	if ( $cmd eq "1" )
	{
		$cmd = "";
	}

	my @config;
	push @config, $time, $cmd;
	untie @file;

	return @config;
}

=begin nd
        Function: setGSLBFarmGuardianParams

        Change gslb farm guardian params

        Parameters:

                fname 	- farm name
                service - service name
                param	- cmd / interval
                value	- value for the param

        Returns:
        
				-1  - error
				0	- successful

=cut

# 	&setGSLBFarmGuardianParams( farmName, service, param, value );
sub setGSLBFarmGuardianParams
{
	my ( $fname, $service, $param, $value ) = @_;
	my $ftype = &getFarmType( $fname );
	my @file;
	my $flagSvc = 0;
	my $err     = -1;
	my $port;

	tie @file, 'Tie::File', "$configdir\/$fname\_$ftype.cfg\/etc\/config";

	foreach my $line ( @file )
	{
		# Begin service block
		if ( $line =~ /${service}_fg_(\d+) =>/ )
		{
			$flagSvc = 1;
			$port    = $1;
		}

		# End service block
		elsif ( $flagSvc && $line =~ /^\t\}/ )
		{
			&zenlog( "GSLB FarmGuardian has corrupt fileconf", "Error" );
		}
		elsif ( $flagSvc && $line =~ /$param/ )
		{
			# change interval time
			if ( $line =~ /interval/ )
			{
				$line =~ s/interval =.*,/interval = $value,/;
				$err = 0;
				next;
			}

			# change cmd
			elsif ( $line =~ /cmd/ )
			{
				my $cmd = &getGSLBCommandInExtmonFormat( $value, $port );
				$line =~ s/cmd =.*,/cmd = \[$cmd\],/;
				$err = 0;
				last;
			}
		}

		# change timeout if we are changing interval. timeout = interval / 2
		elsif ( $line =~ /timeout =/ && $flagSvc && $param =~ /interval/ )
		{
			my $timeout = int ( $value / 2 );
			$line =~ s/timeout =.*,/timeout = $timeout,/;
			$err = 0;
			last;
		}

	}
	untie @file;

	return $err;
}

=begin nd
        Function: setGSLBDeleteFarmGuardian

        Delete Farm Guardian configuration from gslb farm configuration

        Parameters:

                fname 	- farm name
                service - service name

        Returns:
        
				-1  - error
				0	- successful

=cut

# &setGSLBDeleteFarmGuardian ( $fname, $service );
sub setGSLBDeleteFarmGuardian
{
	my ( $fname, $service ) = @_;
	my $ftype   = &getFarmType( $fname );
	my $err     = -1;
	my $index   = 0;
	my $flagSvc = 0;

	tie my @file, 'Tie::File', "$configdir\/$fname\_$ftype.cfg\/etc\/config";

	my $start_i;
	my $end_i;

	foreach my $line ( @file )
	{
		# Begin service block
		if ( $line =~ /^\t${service}_fg_.+ =>/ )
		{
			$flagSvc = 1;
			$start_i = $index;
		}
		if ( $flagSvc )
		{
			if ( $line =~ /^\t}/ )
			{
				$err   = 0;
				$end_i = $index;
				last;
			}
		}
		$index++;
	}
	splice @file, $start_i, $end_i - $start_i + 1;
	untie @file;

	return $err;
}

=begin nd
        Function: getGSLBFarmFGStatus

        Reading farmguardian status for a service

        Parameters:

                fname 	- farm name
                service - service name

        Returns:
        
                true	  	- fg is enabled
                false  	- fg is disabled
                -1 	  		- error
=cut

# &getGSLBFarmFGStatus ( fname, service );
sub getGSLBFarmFGStatus
{
	my ( $fname, $service ) = @_;

	my $ftype  = &getFarmType( $fname );
	my $output = -1;

	use Tie::File;

	# select all ports used in plugins
	opendir ( DIR, "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/" );
	my @pluginlist = readdir ( DIR );
	closedir ( DIR );

	foreach my $plugin ( @pluginlist )
	{
		if ( $plugin !~ /^\./ )
		{
			my @fileconf = ();

			tie @fileconf, 'Tie::File',
			  "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/$plugin";

			# looking for in plugins
			foreach my $line ( @fileconf )
			{
				# find service
				if ( $line =~ /$service =>/ )
				{
					$output = 0;
				}

				# find line with status
				if ( !$output && $line =~ /service_types/ )
				{
					# if service_type point to tpc_port, fg is down
					if ( $line =~ /service_types = tcp_\d+/ )
					{
						$output = "false";
					}

					# if service_type point to fg, fg is up
					elsif ( $line =~ /service_types = ${service}_fg_\d+/ )
					{
						$output = "true";
					}
					else
					{
						# file corrupt
						$output = -1;
					}
					last;
				}

				# didn't find
				if ( !$output && $line =~ /\}/ )
				{
					$output = -1;
					last;
				}
			}
			untie @fileconf;
		}
	}
	return $output;
}

=begin nd
        Function: enableGSLBFarmGuardian

        Enable or disable a service farmguardian in gslb farms

        Parameters:

                fname 	- farm name
                service - service name
                option	- up / down

        Returns:

                port - port where service is listening
                -1	 - error
                0	 - don't modificate
=cut

#		&enableGSLBFarmGuardian ( $fname, $service, $option );
sub enableGSLBFarmGuardian
{
	my ( $fname, $service, $option ) = @_;

	my $ftype  = &getFarmType( $fname );
	my $output = -1;

	use Tie::File;

	# select all ports used in plugins
	opendir ( DIR, "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/" );
	my @pluginlist = readdir ( DIR );
	closedir ( DIR );
	foreach my $plugin ( @pluginlist )
	{
		if ( $plugin !~ /^\./ )
		{
			my @fileconf = ();

			tie @fileconf, 'Tie::File',
			  "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/$plugin";

			foreach my $line ( @fileconf )
			{
				if ( $line =~ /$service =>/ )
				{
					$output = 1;
				}
				if ( $output == 1 )
				{
					if ( $option =~ /true/ && $line =~ /service_types = tcp_(\d+)/ )
					{
						$line   = "\t\tservice_types = ${service}_fg_$1";
						$output = 0;
						last;
					}
					elsif ( $option =~ /false/ && $line =~ /service_types = ${service}_fg_(\d+)/ )
					{
						$line   = "\t\tservice_types = tcp_$1";
						$output = 0;
						last;
					}
				}
			}

			untie @fileconf;
		}
	}
	return $output;
}

#&getGSLBCheckConf  ( $farmname );
sub getGSLBCheckConf
{
	my $farmname = shift;

	my $gdnsd = &getGlobalConfiguration( 'gdnsd' );
	my $errormsg = system (
		   "$gdnsd -c $configdir\/$farmname\_gslb.cfg/etc checkconf > /dev/null 2>&1" );
	if ( $errormsg )
	{
		my @run =
		  `$gdnsd -c $configdir\/$farmname\_gslb.cfg/etc checkconf 2>&1 > /dev/null `;

		@run = grep ( /# error:/, @run );
		$errormsg = $run[0];

		if ( $errormsg =~ /Zone ([\w\.]+).: Zonefile parse error at line (\d+)/ )
		{
			my $fileZone = "$configdir\/$farmname\_gslb.cfg/etc/zones/$1";
			my $numLine  = $2 - 1;

			use Tie::File;
			tie my @filelines, 'Tie::File', $fileZone;
			$errormsg = $filelines[$numLine];
			untie @filelines;
		}
	}

	return $errormsg;
}

# Get hash array with all resources for a farm and service
# &getGSLBResources ( $farmname, $zone )
sub getGSLBResources
{
	my ( $farmname, $zone ) = @_;
	my $backendsvs = &getFarmVS( $farmname, $zone, "resources" );
	my @resourcesArray;

	my @be = split ( "\n", $backendsvs );

	my $ind;
	foreach my $subline ( @be )
	{
		$ind++;
		my %resources;

		if ( $subline =~ /^$/ )
		{
			next;
		}

		my @subbe  = split ( " \;", $subline );
		my @subbe1 = split ( "\t",  $subbe[0] );
		my @subbe2 = split ( "_",   $subbe[1] );

		$resources{ rname } = $subbe1[0];
		$resources{ id }    = $subbe2[1] + 0;
		$resources{ ttl }   = $subbe1[1];
		$resources{ type }  = $subbe1[2];
		$resources{ rdata } = $subbe1[3];

		push @resourcesArray, \%resources;
	}

	return \@resourcesArray;
}

# do not remove this
1;
