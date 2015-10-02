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
sub getGSLBFarmPidFile($farm_name)
{
	my ( $farm_name ) = @_;

	return "$configdir\/$farm_name\_gslb.cfg\/run\/gdnsd.pid";
}

#
sub getGSLBStartCommand($farm_name)
{
	my ( $farm_name ) = @_;

	return "$gdnsd -d $configdir\/$farm_name\_gslb.cfg start";
}

#
sub getGSLBStopCommand($farm_name)
{
	my ( $farm_name ) = @_;

	return "$gdnsd -d $configdir\/$farm_name\_gslb.cfg stop";
}

# Create a new Zone in a GSLB farm
sub setGSLBFarmNewZone($farm_name,$service)
{
	my ( $farm_name, $service ) = @_;

	my $output = -1;

	opendir ( DIR, "$configdir\/$farm_name\_gslb.cfg\/etc\/zones\/" );
	my @files = grep { /^$service/ } readdir ( DIR );
	closedir ( DIR );

	if ( $files == 0 )
	{
		open FO, ">$configdir\/$farm_name\_gslb.cfg\/etc\/zones\/$service";

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
sub setGSLBFarmDeleteZone($farm_name,$service)
{
	my ( $farm_name, $service ) = @_;

	my $output = -1;

	use File::Path 'rmtree';
	rmtree( ["$configdir\/$farm_name\_gslb.cfg\/etc\/zones\/$service"] );
	$output = 0;

	return $output;
}

# Create a new Service in a GSLB farm
sub setGSLBFarmNewService($farm_name,$service,$algorithm)
{
	my ( $farm_name, $service, $algorithm ) = @_;

	my $output         = -1;
	my $gslb_algorithm = "simplefo";

	if ( $algorithm eq "roundrobin" )
	{
		$gslb_algorithm = "multifo";
	}
	elsif ( $algorithm eq "prio" )
	{
		$gslb_algorithm = "simplefo";
	}

	opendir ( DIR, "$configdir\/$farm_name\_gslb.cfg\/etc\/plugins\/" );
	my @files = grep { /^$service/ } readdir ( DIR );
	closedir ( DIR );

	if ( $files == 0 )
	{
		open FO, ">$configdir\/$farm_name\_gslb.cfg\/etc\/plugins\/$service.cfg";

		print FO "$gslb_algorithm => {\n\tservice_types = up\n";
		print FO "\t$service => {\n\t\tservice_types = tcp_80\n";
		print FO "\t}\n}\n";

		close FO;
		$output = 0;

		# Include the plugin file in the main configuration
		tie my @configfile, 'Tie::File',
		  "$configdir\/$farm_name\_gslb.cfg\/etc\/config";
		my $found = 0;
		my $index = 0;

		foreach my $line ( @configfile )
		{
			if ( $line =~ /plugins => / )
			{
				$found = 1;
				$index++;
			}
			if ( $found == 1 )
			{
				splice @configfile, $index, 0, "	\$include{plugins\/$service.cfg},";
				last;
			}
			$index++;
		}
		untie @configfile;
		&setFarmVS( $farm_name, $service, "dpc", "80" );
	}
	else
	{
		$output = -1;
	}

	return $output;
}

# Delete an existing Service in a GSLB farm
sub setGSLBFarmDeleteService($farm_name,$service)
{
	my ( $farm_name, $service ) = @_;

	my $output = -1;

	use File::Path 'rmtree';
	rmtree( ["$configdir\/$farm_name\_gslb.cfg\/etc\/plugins\/$service.cfg"] );
	tie my @configfile, 'Tie::File',
	  "$configdir\/$farm_name\_gslb.cfg\/etc\/config";

	my $found = 0;
	my $index = 0;

	foreach my $line ( @configfile )
	{
		if ( $line =~ /plugins => / )
		{
			$found = 1;
			$index++;
		}
		if ( $found == 1 && $line =~ /plugins\/$service.cfg/ )
		{
			splice @configfile, $index, 1;
			last;
		}
		$index++;
	}
	untie @configfile;
	$output = 0;

	return $output;
}

#
sub getGSLBFarmBootStatus($farm_name)
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
			$output = @line_a[1];
			chomp ( $output );
		}
	}
	close FI;

	return $output;
}

#
sub setGSLBFarmBootStatus($farm_name, $status)
{
	my ( $farm_name, $status ) = @_;

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

#
sub setGSLBFarmStatus($farm_name, $status, $writeconf)
{
	my ( $farm_name, $status, $writeconf ) = @_;

	my $command = "";

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

	&logfile( "setGSLBFarmStatus(): Executing $command" );
	zsystem( "$command > /dev/null 2>&1" );
	$output = $?;

	if ( $output != 0 )
	{
		$output = -1;
	}

	return $output;
}

#function that check if the config file is OK.
sub getGSLBFarmConfigIsOK($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $gdnsd_command = "$gdnsd -d $configdir\/$farm_filename/etc checkconf";
	my $output        = -1;

	&logfile( "getGSLBFarmConfigIsOK(): Executing $gdnsd_command" );

	my $run = `$gdnsd_command 2>&1`;
	$output = $?;

	&logfile( "Execution output: $output" );

	return $output;
}

# Create a new GSLB farm
sub setGSLBFarm($vip,$vip_port,$farm_name)
{
	my ( $vip, $vip_port, $farm_name ) = @_;

	my $farm_type = "gslb";
	my $output    = -1;

	mkdir "$configdir\/$farm_name\_$farm_type.cfg";
	mkdir "$configdir\/$farm_name\_$farm_type.cfg\/etc";
	mkdir "$configdir\/$farm_name\_$farm_type.cfg\/etc\/zones";
	mkdir "$configdir\/$farm_name\_$farm_type.cfg\/etc\/plugins";

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
		open FO, ">$configdir\/$farm_name\_$farm_type.cfg\/etc\/config";

		print FO
		  ";up\noptions => {\n   listen = $vip\n   dns_port = $vip_port\n   http_port = $httpport\n   http_listen = 127.0.0.1\n}\n\n";
		print FO "service_types => { \n\n}\n\n";
		print FO "plugins => { \n\n}\n\n";

		close FO;

		#run farm
		my $command = &getGSLBStartCommand( $farm_name );
		&logfile( "setGSLBFarm(): Executing $command" );
		zsystem( "$command > /dev/null 2>&1" );
		$output = $?;

		if ( $output != 0 )
		{
			$output = -1;
		}
	}

	if ( $output != 0 )
	{
		&runFarmDelete( $farm_name );
	}

	return $output;
}

# Get farm zones list for GSLB farms
sub getFarmZones($farm_name)
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
sub setFarmZoneSerial($farm_name,$zone)
{
	my ( $farm_name, $zone ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	if ( $farm_type eq "gslb" )
	{
		my $index = 0;
		use Tie::File;
		tie my @configfile, 'Tie::File', "$configdir/$farm_filename/etc/zones/$zone";
		foreach my $line ( @configfile )
		{
			if ( $line =~ /@\tSOA / )
			{
				my $date = `date +%s`;
				splice @configfile, $index + 1, 1, "\t$date";
			}
			$index++;
		}
		untie @configfile;
		$output = $?;
	}
	return $output;
}

#
sub setFarmZoneResource($id,$resource,$ttl,$type,$rdata,$farm_name,$service)
{
	my ( $id, $resource, $ttl, $type, $rdata, $farm_name, $service ) = @_;

	my $output        = 0;
	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );

	if ( $farm_type eq "gslb" )
	{
		my $line;
		my $param;
		my $index = 0;
		my $lb    = "";

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
			push @configfile, "$resource\t$ttl\t$type\t$lb$rdata ;index_$index";
		}
		untie @configfile;
		&setFarmZoneSerial( $farm_name, $service );
		$output = $?;
	}

	return $output;
}

#
sub remFarmZoneResource($id,$farm_name,$service)
{
	my ( $id, $farm_name, $service ) = @_;

	my $output        = 0;
	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );

	if ( $farm_type eq "gslb" )
	{
		my $index = 0;
		use Tie::File;
		tie my @configfile, 'Tie::File', "$configdir/$farm_filename/etc/zones/$service";
		foreach my $line ( @configfile )
		{
			if ( $line =~ /\;index_$id/ )
			{
				splice @configfile, $index, 1;
			}
			$index++;
		}
		untie @configfile;
		$output = $?;
		&setFarmZoneSerial( $farm_name, $service );
		$output = $output + $?;
	}
	return $output;
}

#
sub setGSLBFarmNewBackend($farm_name,$service,$lb,$id,$ipaddress)
{
	my ( $farm_name, $service, $lb, $id, $ipaddress ) = @_;

	my $output        = 0;
	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );

	if ( $farm_type eq "gslb" )
	{
		my $found      = 0;
		my $index      = 0;
		my $idx        = 0;
		my $pluginfile = "";

		use Tie::File;

		#Find the plugin file
		tie my @configfile, 'Tie::File',
		  "$configdir/$farm_filename/etc/plugins/$service.cfg";
		foreach my $line ( @configfile )
		{
			if ( $line =~ /^\t$service => / )
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
				splice @configfile, $index, 0, "		$id => $ipaddress";
				last;
			}
			if (    $found == 1
				 && $lb eq "prio"
				 && $line =~ /primary => /
				 && $id eq "primary" )
			{
				splice @configfile, $index, 1, "		$id => $ipaddress";
				last;
			}
			if (    $found == 1
				 && $lb eq "prio"
				 && $line =~ /\}/
				 && $id eq "secondary" )
			{
				splice @configfile, $index, 0, "		$id => $ipaddress";
				last;
			}
			if (    $found == 1
				 && $lb eq "prio"
				 && $line =~ /secondary => /
				 && $id eq "secondary" )
			{
				splice @configfile, $index, 1, "		$id => $ipaddress";
				last;
			}
			if ( $found == 1 && $lb eq "roundrobin" && $line =~ /\t\t$id => / )
			{
				splice @configfile, $index, 1, "		$id => $ipaddress";
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
				splice @configfile, $index, 0, "		$idx => $ipaddress";
				last;
			}
			$index++;
		}
		untie @configfile;
		$output = $?;
	}

	return $output;
}

# Stop Farm rutine
sub _runGSLBFarmStop($farm_name,$writeconf)
{
	my ( $farm_name, $writeconf ) = @_;

	my $status = -1;

	if ( &getFarmConfigIsOK( $farm_name ) == 0 )
	{
		$status = &setGSLBFarmStatus( $farm_name, "stop", $writeconf );
		unlink ( $pidfile );
	}
	else
	{
		&errormsg(
			 "Farm $farm_name can't be stopped, check the logs and modify the configuration"
		);
		return 1;
	}

	return $status;
}

# Returns farm PID
sub getGSLBFarmPid($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $pidfile       = &getGSLBFarmPidFile( $farm_name );
	my $output        = -1;

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
sub getGSLBFarmVip($info,$farm_name)
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
sub setGSLBFarmVirtualConf($vip,$vip_port,$farm_name)
{
	my ( $vip, $vip_port, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $stat          = -1;
	my $index         = 0;
	my $found         = 0;

	tie my @configfile, 'Tie::File', "$configdir/$farm_filename/etc/config";

	foreach my $line ( @configfile )
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
			$line =~ s/$line/   dns_port = $vip_port/g;
		}
		if ( $found == 1 && $line =~ /\}/ )
		{
			last;
		}
		$index++;
	}
	untie @configfile;
	$stat = $?;

	return $stat;
}

#
sub runGSLBFarmServerDelete($ids,$farm_name,$service)
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
			my $param = @linesplt[1];
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

#function that renames a farm
sub setGSLBNewFarmName($farm_name,$new_farm_name)
{
	my ( $farm_name, $new_farm_name ) = @_;

	my $farm_filename     = &getFarmFile( $farm_name );
	my $farm_type         = &getFarmType( $farm_name );
	my $new_farm_filename = "$new_farm_name\_$farm_type.cfg";

	return
	  rename ( "$configdir\/$farm_filename", "$configdir\/$new_farm_filename" );
}

# GSLB function
# Get farm services list for GSLB farms
sub getFarmServices($farm_name)
{
	my ( $farm_name ) = @_;

	my $output        = -1;
	my $farm_type     = &getFarmType( $farm_name );
	my @service_array = ();

	opendir ( DIR, "$configdir\/$farm_name\_$farm_type.cfg\/etc\/plugins\/" );
	my @pluginlist = readdir ( DIR );
	closedir ( DIR );

	foreach my $plugin ( @pluginlist )
	{
		if ( $plugin !~ /^\./ )
		{
			tie my @configfile, 'Tie::File',
			  "$configdir\/$farm_name\_$farm_type.cfg\/etc\/plugins\/$plugin";
			my @srv = grep ( /^\t[a-zA-Z1-9].* => {/, @configfile );

			foreach my $srvstring ( @srv )
			{
				my @srvstr = split ( ' => ', $srvstring );
				$srvstring = $srvstr[0];
				$srvstring =~ s/^\s+|\s+$//g;
			}
			my $nsrv = @srv;

			if ( $nsrv > 0 )
			{
				push ( @service_array, @srv );
			}
			untie @configfile;
		}
	}
	return @service_array;
}

#function that return indicated value from a HTTP Service
#vs return virtual server
sub getGSLBFarmVS($farm_name, $service, $tag)
{
	my ( $farm_filename, $service, $tag ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = "";
	my @linesplt;

	use Tie::File;

	if ( $tag eq "ns" || $tag eq "resources" )
	{
		tie my @configfile, 'Tie::File', "$configdir/$farm_filename/etc/zones/$service";
		foreach my $line ( @configfile )
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

		opendir ( DIR, "$configdir\/$farm_name\_$farm_type.cfg\/etc\/plugins\/" );
		my @pluginlist = readdir ( DIR );

		foreach my $plugin ( @pluginlist )
		{
			tie my @configfile, 'Tie::File',
			  "$configdir\/$farm_name\_$farm_type.cfg\/etc\/plugins\/$plugin";
			if ( grep ( /^\t$service => /, @configfile ) )
			{
				$pluginfile = $plugin;
			}
			untie @configfile;
		}
		closedir ( DIR );

		tie my @configfile, 'Tie::File',
		  "$configdir\/$farm_name\_$farm_type.cfg\/etc\/plugins\/$pluginfile";
		foreach my $line ( @configfile )
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
	untie @configfile;

	return $output;
}

#set values for a service
sub setGSLBFarmVS($farm_name,$service,$tag,$string)
{
	my ( $farm_name, $service, $tag, $string ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $param;

	use Tie::File;

	if ( $tag eq "ns" )
	{
		tie my @configfile, 'Tie::File', "$configdir/$farm_filename/etc/zones/$service";
		foreach my $line ( @configfile )
		{
			if ( $line =~ /^@\tSOA .* hostmaster / )
			{
				( undef, undef, $param ) = split ( " ", $line );
				$line = "@\tSOA $string hostmaster (";
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
		untie @configfile;
		&setFarmZoneSerial( $farm_name, $service );
	}
	if ( $tag eq "dpc" )
	{
		my $found = 0;

		#Find the plugin file
		opendir ( DIR, "$configdir\/$farm_filename\/etc\/plugins\/" );
		my @pluginlist = readdir ( DIR );

		foreach my $plugin ( @pluginlist )
		{
			tie my @configfile, 'Tie::File',
			  "$configdir\/$farm_filename\/etc\/plugins\/$plugin";
			if ( grep ( /^\t$service => /, @configfile ) )
			{
				$pluginfile = $plugin;
			}
			untie @configfile;
		}
		closedir ( DIR );

		tie my @configfile, 'Tie::File',
		  "$configdir/$farm_filename/etc/plugins/$pluginfile";
		foreach my $line ( @configfile )
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
		untie @configfile;
		if ( $output eq "0" )
		{
			# Check if there is already an entry
			my $found = 0;
			my $index = 1;
			tie my @configfile, 'Tie::File', "$configdir/$farm_filename/etc/config";
			while ( @configfile[$index] !~ /plugins => / )
			{
				my $line = @configfile[$index];
				if ( $found == 2 && $line =~ /.*}.*/ )
				{
					splice @configfile, $index, 1;
					last;
				}
				if ( $found == 2 )
				{
					splice @configfile, $index, 1;
					next;
				}
				if ( $found == 1 && $line =~ /tcp_$string => / )
				{
					splice @configfile, $index, 1;
					$found = 2;
					next;
				}
				if ( $line =~ /service_types => / )
				{
					$found = 1;
				}
				$index++;
			}
			untie @configfile;

			# New service_types entry
			my $index = 0;
			tie my @configfile, 'Tie::File', "$configdir/$farm_filename/etc/config";
			foreach my $line ( @configfile )
			{
				if ( $line =~ /service_types => / )
				{
					$index++;
					splice @configfile, $index, 0,
					  "\ttcp_$string => {\n\t\tplugin = tcp_connect,\n\t\tport = $string,\n\t\tup_thresh = 2,\n\t\tok_thresh = 2,\n\t\tdown_thresh = 2,\n\t\tinterval = 5,\n\t\ttimeout = 3,\n\t}\n";
					last;
				}
				$index++;
			}
			untie @configfile;
		}
	}

	return $output;
}

# Remove Gslb service
sub remFarmServiceBackend($id,$farm_name,$service)
{
	my ( $id, $farm_name, $service ) = @_;

	my $output        = 0;
	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );

	if ( $farm_type eq "gslb" )
	{
		my $line;
		my $index      = 0;
		my $pluginfile = "";
		use Tie::File;

		#Find the plugin file
		opendir ( DIR, "$configdir\/$farm_filename\/etc\/plugins\/" );
		my @pluginlist = readdir ( DIR );
		foreach $plugin ( @pluginlist )
		{
			tie my @configfile, 'Tie::File',
			  "$configdir\/$farm_filename\/etc\/plugins\/$plugin";
			if ( grep ( /^\t$service => /, @configfile ) )
			{
				$pluginfile = $plugin;
			}
			untie @configfile;
		}
		closedir ( DIR );

		tie my @configfile, 'Tie::File',
		  "$configdir/$farm_filename/etc/plugins/$pluginfile";
		foreach my $line ( @configfile )
		{
			if ( $line =~ /^\t$service => / )
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
				my @backendslist = grep ( /^\s+[1-9].* =>/, @configfile );
				my $nbackends = @backendslist;
				if ( $nbackends == 1 )
				{
					$output = -2;
				}
				else
				{
					splice @configfile, $index, 1;
				}
				last;
			}
			$index++;
		}
		untie @configfile;
		$output = $output + $?;
	}

	return $output;
}

sub runFarmReload($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output;

	if ( $farm_type eq "gslb" )
	{
		my $gdnsd_command =
		  "$gdnsd -d $configdir\/$farm_name\_$farm_type.cfg/etc reload-zones";

		&logfile( "running $gdnsd_command" );
		zsystem( "$gdnsd_command 2>/dev/null" );
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
