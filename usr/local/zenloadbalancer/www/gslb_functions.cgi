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

# Start Farm rutine
sub _runGSLBFarmStart    # ($fname,$writeconf)
{
	my ( $fname, $writeconf ) = @_;

	my $status = &getFarmStatus( $fname );
	my $type   = &getFarmType( $fname );
	my $file   = &getFarmFile( $fname );

	chomp ( $status );
	if ( $status eq "up" )
	{
		return 0;
	}

	&zenlog( "running 'Start write $writeconf' for $fname farm $type" );

	if ( $writeconf eq "true" )
	{
		unlink ( "/tmp/$fname.lock" );
		use Tie::File;
		tie @filelines, 'Tie::File', "$configdir\/$file\/etc\/config";
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
			tie @filelines, 'Tie::File', "$configdir\/$filename\/etc\/config";
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
		&zenlog( "running $exec" );
		zsystem( "$exec > /dev/null 2>&1" );
		$status = $?;
		if ( $status != 0 )
		{
			$status = -1;
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
	foreach $plugin ( @pluginlist )
	{
		if ( $plugin !~ /^\./ )
		{
			@fileconf = ();
			tie @fileconf, 'Tie::File',
			  "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/$plugin";
			my @srv = grep ( /^\t[a-zA-Z1-9].* => \{/, @fileconf );
			foreach $srvstring ( @srv )
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

	my $ffile = &getFarmFile( $fname );
	$output = -1;

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

	my $type   = &getFarmType( $fname );
	my $file   = &getFarmFile( $fname );
	my $output = -1;

	@fname = split ( /\_/, $file );
	my $pidfile = &getGSLBFarmPidFile( $fname );
	if ( -e $pidfile )
	{
		open FPID, "<$pidfile";
		@pid = <FPID>;
		close FPID;
		$pid_hprof = $pid[0];
		chomp ( $pid_hprof );
		my $exists = kill 0, $pid_hprof;
		if   ( $pid_hprof =~ /^[1-9].*/ && $exists ) { $output = "$pid_hprof"; }
		else                                         { $output = "-"; }
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
		foreach $plugin ( @pluginlist )
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
					$output =~ s/['\[''\]'' ']//g;
					my @tmp = split ( "_", $output );
					$output = $tmp[1];
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

	foreach $line ( @file )
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

	return "$gdnsd -c $configdir\/$farm_name\_gslb.cfg/etc start";
}

#
sub getGSLBStopCommand     # ($farm_name)
{
	my ( $farm_name ) = @_;

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

	#Find the plugin file
	opendir ( DIR, "$configdir\/$ffile\/etc\/plugins\/" );
	my @pluginlist = readdir ( DIR );
	foreach $plugin ( @pluginlist )
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
	foreach $line ( @fileconf )
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

	my $httpport = 35060;
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

	while ( $httpport < 35160 && &checkport( "127.0.0.1", $httpport ) eq "true" )
	{
		$httpport++;
	}
	if ( $httpport == 35160 )
	{
		$output = -1;    # No room for a new farm
	}
	else
	{
		open ( my $file, ">", "$configdir\/$fname\_$type.cfg\/etc\/config" );
		print $file ";up\n"
		  . "options => {\n"
		  . "   listen = $fvip\n"
		  . "   dns_port = $fvipp\n"
		  . "   http_port = $httpport\n"
		  . "   http_listen = 127.0.0.1\n" . "}\n\n";
		print $file "service_types => { \n\n}\n\n";
		print $file "plugins => { \n\n}\n\n";
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
			$output = -1;
		}
	}
	if ( $output != 0 )
	{
		&runFarmDelete( $fname );
	}
	return $output;
}

#
sub setGSLBFarmBootStatus    # ($farm_name, $status)
{
	my ( $farm_name, $status ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );

	use Tie::File;
	tie @filelines, 'Tie::File', "$configdir\/$farm_filename\/etc\/config";
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
	foreach $plugin ( @pluginlist )
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
			tie @fileconf, 'Tie::File',
			  "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/$gsalg.cfg";
			if ( grep ( /^\t$svice =>.*/, @fileconf ) )
			{
				$output = -1;
			}
			else
			{
				my $found = 0;
				my $index = 0;
				foreach $line ( @fileconf )
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
			tie @fileconf, 'Tie::File', "$configdir\/$fname\_$ftype.cfg\/etc\/config";
			if ( ( grep ( /include{plugins\/$gsalg\.cfg}/, @fileconf ) ) == 0 )
			{
				my $found = 0;
				my $index = 0;
				foreach $line ( @fileconf )
				{
					if ( $line =~ /plugins => / )
					{
						$found = 1;
						$index++;
					}
					if ( $found == 1 )
					{
						splice @fileconf, $index, 0, "     \$include{plugins\/$gsalg.cfg},";
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
	$output = 0;

	if ( $output != 0 )
	{
		$output = -1;
	}

	return $output;
}

#set values for a service
sub setGSLBFarmVS    # ($farm_name,$service,$tag,$string)
{
	( $fname, $svice, $tag, $stri ) = @_;

	my $output = "";
	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );

	my @fileconf;
	my $line;
	my $param;
	my @linesplt;
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
		my $found = 0;

		#Find the plugin file
		opendir ( DIR, "$configdir\/$ffile\/etc\/plugins\/" );
		my @pluginlist = readdir ( DIR );
		foreach $plugin ( @pluginlist )
		{
			tie @fileconf, 'Tie::File', "$configdir\/$ffile\/etc\/plugins\/$plugin";
			if ( grep ( /^\t$svice => /, @fileconf ) )
			{
				$pluginfile = $plugin;
			}
			untie @fileconf;
		}
		closedir ( DIR );

		tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/plugins/$pluginfile";
		foreach $line ( @fileconf )
		{
			if ( $found == 1 && $line =~ /.*}.*/ )
			{
				last;
			}
			if ( $found == 1 && $line =~ /.*service_types.*/ )
			{
				$line   = "\t\tservice_types = tcp_$stri";
				$output = "0";
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
			# Check if there is already an entry
			my $found = 0;
			my $index = 1;
			tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/config";
			while ( $fileconf[$index] !~ /plugins => / )
			{
				my $line = $fileconf[$index];
				if ( $found == 2 && $line =~ /.*}.*/ )
				{
					splice @fileconf, $index, 1;
					last;
				}
				if ( $found == 2 )
				{
					splice @fileconf, $index, 1;
					next;
				}
				if ( $found == 1 && $line =~ /tcp_$stri => / )
				{
					splice @fileconf, $index, 1;
					$found = 2;
					next;
				}
				if ( $line =~ /service_types => / )
				{
					$found = 1;
				}
				$index++;
			}
			untie @fileconf;

			# New service_types entry
			$index = 0;
			tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/config";
			foreach $line ( @fileconf )
			{
				if ( $line =~ /service_types => / )
				{
					$index++;
					splice @fileconf, $index, 0,
					  "\ttcp_$stri => {\n\t\tplugin = tcp_connect,\n\t\tport = $stri,\n\t\tup_thresh = 2,\n\t\tok_thresh = 2,\n\t\tdown_thresh = 2,\n\t\tinterval = 5,\n\t\ttimeout = 3,\n\t}\n";
					last;
				}
				$index++;
			}
			untie @fileconf;
		}
	}

	return @output;
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
	tie @fileconf, 'Tie::File', "$configdir/$fconf/etc/config";
	foreach $line ( @fileconf )
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
	foreach $plugin ( @pluginlist )
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
sub getGSLBGdnsdStats
{
	$gdnsdStats = `wget -qO- http://127.0.0.1:35060/json`;

	return $gdnsdStats;
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

# do not remove this
1;
