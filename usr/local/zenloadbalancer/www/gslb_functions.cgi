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

#
sub getGSLBFarmPidFile($farmname)
{
	my ( $fname ) = @_;

	my $pidf = "$configdir\/$fname\_gslb.cfg\/run\/gdnsd.pid";

	return $pidf;
}

#
sub getGSLBStartCommand($farmname)
{
	my ( $fname ) = @_;

	my $cmd = "$gdnsd -d $configdir\/$fname\_gslb.cfg start";

	return $cmd;
}

#
sub getGSLBStopCommand($farmname)
{
	my ( $fname ) = @_;

	my $cmd = "$gdnsd -d $configdir\/$fname\_gslb.cfg stop";

	return $cmd;
}

# Create a new Zone in a GSLB farm
sub setFarmGSLBNewZone($fname,$service)
{
	my ( $fname, $svice ) = @_;

	my $output = -1;

	opendir ( DIR, "$configdir\/$fname\_gslb.cfg\/etc\/zones\/" );
	my @files = grep { /^$svice/ } readdir ( DIR );
	closedir ( DIR );

	if ( $files == 0 )
	{
		open FO, ">$configdir\/$fname\_gslb.cfg\/etc\/zones\/$svice";
		print FO "@	SOA ns1 hostmaster (\n	1\n	7200\n	1800\n	259200\n	900\n)\n\n";
		print FO "@		NS	ns1 ;index_0\n";
		print FO "ns1		A	0.0.0.0 ;index_1\n";
		close FO;
		$output = 0;
	}
	else
	{
		$output = 1;
	}

	return $output;
}

# Delete an existing Zone in a GSLB farm
sub setFarmGSLBDeleteZone($fname,$service)
{
	my ( $fname, $svice ) = @_;

	my $output = -1;

	use File::Path 'rmtree';
	rmtree( ["$configdir\/$fname\_gslb.cfg\/etc\/zones\/$svice"] );
	$output = 0;

	return $output;
}

# Create a new Service in a GSLB farm
sub setFarmGSLBNewService($fname,$service,$algorithm)
{
	my ( $fname, $svice, $alg ) = @_;

	my $output = -1;
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
	opendir ( DIR, "$configdir\/$fname\_gslb.cfg\/etc\/plugins\/" );
	my @files = grep { /^$svice/ } readdir ( DIR );
	closedir ( DIR );

	if ( $files == 0 )
	{
		open FO, ">$configdir\/$fname\_gslb.cfg\/etc\/plugins\/$svice.cfg";
		print FO "$gsalg => {\n\tservice_types = up\n";
		print FO "\t$svice => {\n\t\tservice_types = tcp_80\n";
		print FO "\t}\n}\n";
		close FO;
		$output = 0;

		# Include the plugin file in the main configuration
		tie @fileconf, 'Tie::File', "$configdir\/$fname\_gslb.cfg\/etc\/config";
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
				splice @fileconf, $index, 0, "	\$include{plugins\/$svice.cfg},";
				last;
			}
			$index++;
		}
		untie @fileconf;
		&setFarmVS( $fname, $svice, "dpc", "80" );
	}
	else
	{
		$output = -1;
	}

	return $output;
}

# Delete an existing Service in a GSLB farm
sub setFarmGSLBDeleteService($fname,$service)
{
	my ( $fname, $svice ) = @_;

	my $output = -1;

	use File::Path 'rmtree';
	rmtree( ["$configdir\/$fname\_gslb.cfg\/etc\/plugins\/$svice.cfg"] );
	tie @fileconf, 'Tie::File', "$configdir\/$fname\_gslb.cfg\/etc\/config";
	my $found = 0;
	my $index = 0;
	foreach $line ( @fileconf )
	{
		if ( $line =~ /plugins => / )
		{
			$found = 1;
			$index++;
		}
		if ( $found == 1 && $line =~ /plugins\/$svice.cfg/ )
		{
			splice @fileconf, $index, 1;
			last;
		}
		$index++;
	}
	untie @fileconf;
	$output = 0;

	return $output;
}

#
sub getFarmGSLBBootStatus($file)
{
	my ( $file ) = @_;

	open FI, "<$configdir/$file/etc/config";
	my $first = "true";
	while ( $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line_a = split ( "\;", $line );
			$output = @line_a[1];
			chomp ( $output );
		}
	}
	close FI;

	return $output;
}

#
sub setFarmGSLBBootStatus($fname, $status)
{
	my ( $fname, $status ) = @_;

	use Tie::File;
	tie @filelines, 'Tie::File', "$configdir\/$file\/etc\/config";
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

#
sub setFarmGSLBStatus($fname, $status, $writeconf)
{

	my ( $fname, $status, $writeconf ) = @_;

	my $exec = "";

	unlink ( "/tmp/$fname.lock" );
	if ( $writeconf eq "true" )
	{
		&setFarmGSLBBootStatus( $fname, $status );
	}

	if ( $status eq "start" )
	{
		$exec = &getGSLBStartCommand( $fname );
	}
	else
	{
		$exec = &getGSLBStopCommand( $fname );
	}
	&logfile( "setFarmGSLBStatus(): Executing $exec" );
	zsystem( "$exec > /dev/null 2>&1" );
	$output = $?;
	if ( $output != 0 )
	{
		$output = -1;
	}

	return $output;
}

#function that check if the config file is OK.
sub getFarmGSLBConfigIsOK($ffile)
{
	( $ffile ) = @_;

	my $output = -1;

	&logfile(
		"getFarmGSLBConfigIsOK(): Executing $gdnsd -c $configdir\/$ffile/etc checkconf "
	);
	my $run = `$gdnsd -c $configdir\/$ffile/etc checkconf 2>&1`;
	$output = $?;
	&logfile( "Execution output: $output " );

	return $output;
}

# Create a new GSLB farm
sub setFarmGSLB($fvip,$fvipp,$fname)
{
	my ( $fvip, $fvipp, $fname ) = @_;

	my $output = -1;
	my $type   = "gslb";

	mkdir "$configdir\/$fname\_$type.cfg";
	mkdir "$configdir\/$fname\_$type.cfg\/etc";
	mkdir "$configdir\/$fname\_$type.cfg\/etc\/zones";
	mkdir "$configdir\/$fname\_$type.cfg\/etc\/plugins";
	my $httpport = 35060;
	while ( $httpport < 35160 && &checkport( 127.0.0.1, $httpport ) eq "true" )
	{
		$httpport++;
	}
	if ( $httpport == 35160 )
	{
		$output = -1;    # No room for a new farm
	}
	else
	{
		open FO, ">$configdir\/$fname\_$type.cfg\/etc\/config";
		print FO
		  ";up\noptions => {\n   listen = $fvip\n   dns_port = $fvipp\n   http_port = $httpport\n   http_listen = 127.0.0.1\n}\n\n";
		print FO "service_types => { \n\n}\n\n";
		print FO "plugins => { \n\n}\n\n";
		close FO;

		#run farm
		my $exec = &getGSLBStartCommand( $fname );
		&logfile( "setFarmGSLB(): Executing $exec" );
		zsystem( "$exec > /dev/null 2>&1" );
		$output = $?;
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

# Get farm zones list for GSLB farms
sub getFarmZones($fname)
{
	my ( $fname ) = @_;

	my $output = -1;
	my $ftype  = &getFarmType( $fname );

	opendir ( DIR, "$configdir\/$fname\_$ftype.cfg\/etc\/zones\/" );
	my @files = grep { /^[a-zA-Z]/ } readdir ( DIR );
	closedir ( DIR );

	return @files;
}

#
sub setFarmZoneSerial($fname,$zone)
{
	my ( $fname, $zone ) = @_;
	my $ftype  = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;
	if ( $ftype eq "gslb" )
	{
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
	}
	return $output;
}

#
sub setFarmZoneResource($id,$resource,$ttl,$type,$rdata,$fname,$service)
{
	my ( $id, $resource, $ttl, $type, $rdata, $fname, $service ) = @_;

	my $output = 0;
	my $ftype  = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );

	if ( $ftype eq "gslb" )
	{
		my @fileconf;
		my $line;
		my $param;
		my @linesplt;
		my $index = 0;
		my $lb    = "";
		if ( $type =~ /DYN./ )
		{
			$lb = &getFarmVS( $fname, $rdata, "plugin" );
			$lb = "$lb!";
		}
		use Tie::File;
		tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/zones/$service";
		foreach $line ( @fileconf )
		{
			if ( $line =~ /\;index_/ )
			{
				@linesplt = split ( "\;index_", $line );
				$param = @linesplt[1];
				if ( $id !~ /^$/ && $id eq $param )
				{
					$line = "$resource\t$ttl\t$type\t$lb$rdata ;index_$param";
				}
				else
				{
					$index = $param + 1;
				}
			}
		}
		if ( $id =~ /^$/ )
		{
			push @fileconf, "$resource\t$ttl\t$type\t$lb$rdata ;index_$index";
		}
		untie @fileconf;
		&setFarmZoneSerial( $fname, $service );
		$output = $?;
	}

	return $output;
}

#
sub remFarmZoneResource($id,$fname,$service)
{
	my ( $id, $fname, $service ) = @_;

	my $output = 0;
	my $ftype  = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );

	if ( $ftype eq "gslb" )
	{
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
	}
	return $output;
}

#
sub setFarmGSLBNewBackend($fname,$srv,$lb,$id,$ipaddress)
{
	my ( $fname, $srv, $lb, $id, $ipaddress ) = @_;

	my $output = 0;
	my $ftype  = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );

	if ( $ftype eq "gslb" )
	{
		my @fileconf;
		my $line;
		my @linesplt;
		my $found      = 0;
		my $index      = 0;
		my $idx        = 0;
		my $pluginfile = "";
		use Tie::File;

		#Find the plugin file
		tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/plugins/$srv.cfg";
		foreach $line ( @fileconf )
		{
			if ( $line =~ /^\t$srv => / )
			{
				$found = 1;
				$index++;
				next;
			}
			if (    $found == 1
				 && $lb eq "prio"
				 && $line =~ /\}/
				 && $id eq "primary" )
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
			if (    $found == 1
				 && $lb eq "prio"
				 && $line =~ /\}/
				 && $id eq "secondary" )
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
				$idx = @temp[0];
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
	}

	return $output;
}

# Stop Farm rutine
sub _runGSLBFarmStop($fname,$writeconf,$status)
{
	my ( $fname, $writeconf, $status ) = @_;

	my $checkfarm = &getFarmConfigIsOK( $fname );
	if ( $checkfarm == 0 )
	{
		$output = &setFarmGSLBStatus( $fname, "stop", $writeconf );
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

# Returns farm PID
sub getGSLBFarmPid($fname,$file)
{
	my ( $fname, $file ) = @_;
	my $output = -1;

	my @fname = split ( /\_/, $file );
	my $pidfile = &getGSLBFarmPidFile( $fname );
	if ( -e $pidfile )
	{
		open FPID, "<$pidfile";
		my @pid = <FPID>;
		close FPID;
		my $pid_hprof = @pid[0];
		chomp ( $pid_hprof );
		my $exists = kill 0, $pid_hprof;
		if ( $pid_hprof =~ /^[1-9].*/ && $exists )
		{
			$output = "$pid_hprof";
		}
		else
		{
			$output = "-";
		}
	}
	else
	{
		$output = "-";
	}

	return $output;
}

# Returns farm vip
sub getGSLBFarmVip($info,$file)
{
	my ( $info, $file ) = @_;
	my $output = -1;

	open FI, "<$configdir/$file/etc/config";
	my @file = <FI>;
	my $i    = 0;
	close FI;
	foreach $line ( @file )
	{
		if ( $line =~ /^options =>/ )
		{
			my $vip  = @file[$i + 1];
			my $vipp = @file[$i + 2];
			chomp ( $vip );
			chomp ( $vipp );
			my @vip  = split ( "\ ", $vip );
			my @vipp = split ( "\ ", $vipp );
			if ( $info eq "vip" )   { $output = @vip[2]; }
			if ( $info eq "vipp" )  { $output = @vipp[2]; }
			if ( $info eq "vipps" ) { $output = "@vip[2]\:@vipp[2]"; }
		}
		$i++;
	}

	return $output;
}

# Set farm virtual IP and virtual PORT
sub setGSLBFarmVirtualConf($vip,$vipp,$fconf)
{

	my $stat  = -1;
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

#
sub runGSLBFarmServerDelete($ids,$ffile,$service)
{
	my ( $ids, $ffile, $service ) = @_;

	my $output = -1;
	my $param;
	my @linesplt;
	my $index = 0;
	use Tie::File;
	tie my @fileconf, 'Tie::File', "$configdir/$ffile/etc/zones/$service";
	foreach my $line ( @fileconf )
	{

		if ( $line =~ /\;index_/ )
		{
			@linesplt = split ( "\;index_", $line );
			$param = @linesplt[1];
			if ( $ids !~ /^$/ && $ids eq $param )
			{
				splice @fileconf, $index, 1,;
			}
		}
		$index++;
	}
	untie @fileconf;
	$output = $?;

	return $output;
}

#function that renames a farm
sub setGSLBNewFarmName($newfname,$ffile,$type)
{
	my ( $newfname, $ffile, $type ) = @_;
	my $output = -1;

	my $newffile = "$newfname\_$type.cfg";
	rename ( "$configdir\/$ffile", "$configdir\/$newffile" );
	$output = 0;

	return $output;
}

# Get farm services list for GSLB farms
sub getFarmServices($fname)
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
			my @srv = grep ( /^\t[a-zA-Z1-9].* => {/, @fileconf );
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

#function that return indicated value from a HTTP Service
#vs return virtual server
sub getGSLBFarmVS($ffile,$service,$tag)
{
	my ( $ffile, $service, $tag ) = @_;

	my $output = "";

	my @fileconf;
	my $line;
	my @linesplt;
	use Tie::File;
	if ( $tag eq "ns" || $tag eq "resources" )
	{
		tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/zones/$service";
		foreach $line ( @fileconf )
		{
			if ( $tag eq "ns" )
			{
				if ( $line =~ /@.*SOA .* hostmaster / )
				{
					@linesplt = split ( " ", $line );
					$output = @linesplt[2];
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
			if ( grep ( /^\t$service => /, @fileconf ) )
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
				if (    $found == 1
					 && $line !~ /^$/
					 && $line !~ /.*service_types.*/ )
				{
					$output = "$output\n$line";
				}
				if ( $line =~ /\t$service => / )
				{
					$found = 1;
				}
			}
			if ( $tag eq "algorithm" )
			{
				@linesplt = split ( " ", $line );
				if ( @linesplt[0] eq "simplefo" )
				{
					$output = "prio";
				}
				if ( @linesplt[0] eq "multifo" )
				{
					$output = "roundrobin";
				}
				last;
			}
			if ( $tag eq "plugin" )
			{
				@linesplt = split ( " ", $line );
				$output = @linesplt[0];
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
					$output = @tmpline[1];
					$output =~ s/['\[''\]'' ']//g;
					my @tmp = split ( "_", $output );
					$output = @tmp[1];
					last;
				}
				if ( $line =~ /\t$service => / )
				{
					$found = 1;
				}
			}
		}
	}
	untie @fileconf;

	return $output;
}

#set values for a service
sub setGSLBFarmVS($ffile,$service,$tag,$string)
{
	my ( $ffile, $service, $tag, $string ) = @_;
	my $output = "";

	my @fileconf;
	my $line;
	my $param;
	my @linesplt;
	use Tie::File;
	if ( $tag eq "ns" )
	{
		tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/zones/$service";
		foreach $line ( @fileconf )
		{
			if ( $line =~ /^@\tSOA .* hostmaster / )
			{
				@linesplt = split ( " ", $line );
				$param    = @linesplt[2];
				$line     = "@\tSOA $string hostmaster (";
			}
			if ( $line =~ /\t$param / )
			{
				$line =~ s/\t$param /\t$string /g;
			}
			if ( $line =~ /^$param\t/ )
			{
				$line =~ s/^$param\t/$string\t/g;
			}
		}
		untie @fileconf;
		&setFarmZoneSerial( $fname, $service );
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
			if ( grep ( /^\t$service => /, @fileconf ) )
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
				$line   = "\t\tservice_types = tcp_$string";
				$output = "0";
				last;
			}
			if ( $line =~ /\t$service => / )
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
			while ( @fileconf[$index] !~ /plugins => / )
			{
				my $line = @fileconf[$index];
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
				if ( $found == 1 && $line =~ /tcp_$string => / )
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
			my $index = 0;
			tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/config";
			foreach $line ( @fileconf )
			{
				if ( $line =~ /service_types => / )
				{
					$index++;
					splice @fileconf, $index, 0,
					  "\ttcp_$string => {\n\t\tplugin = tcp_connect,\n\t\tport = $string,\n\t\tup_thresh = 2,\n\t\tok_thresh = 2,\n\t\tdown_thresh = 2,\n\t\tinterval = 5,\n\t\ttimeout = 3,\n\t}\n";
					last;
				}
				$index++;
			}
			untie @fileconf;
		}
	}

	return $output;
}

# Remove Gslb service
sub remFarmServiceBackend($id,$fname,$service)
{
	my ( $id, $fname, $srv ) = @_;

	my $output = 0;
	my $ftype  = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );

	if ( $ftype eq "gslb" )
	{
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
	}

	return $output;
}

sub runFarmReload($farmname)
{
	my ( $fname ) = @_;

	my $type = &getFarmType( $fname );
	my $output;

	if ( $type eq "gslb" )
	{
		&logfile( "running $gdnsd -c $configdir\/$fname\_$type.cfg/etc reload-zones" );
		zsystem(
				 "$gdnsd -c $configdir\/$fname\_$type.cfg/etc reload-zones 2>/dev/null" );
		$output = $?;
		if ( $output != 0 )
		{
			$output = -1;
		}
	}

	return $output;
}

# do not remove this
1
