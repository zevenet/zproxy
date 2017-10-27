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

my $configdir = &getGlobalConfiguration('configdir');

=begin nd
Function: getGSLBFarmServices

	Get farm services list for GSLB farms
	
Parameters:
	farmname - Farm name

Returns:
	Array - list of service names or -1 on failure
	
=cut
sub getGSLBFarmServices    # ($farm_name)
{
	my ( $fname ) = @_;

	require Tie::File;

	my $output = -1;
	my $ftype  = &getFarmType( $fname );
	my @srvarr = ();

	opendir ( DIR, "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/" );
	my @pluginlist = readdir ( DIR );
	closedir ( DIR );

	foreach my $plugin ( @pluginlist )
	{
		next if $plugin =~ /^\./;

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

	return @srvarr;
}

=begin nd
Function: setGSLBFarmDeleteService

	Delete an existing Service in a GSLB farm
	 
Parameters:
	farmname - Farm name
	service - Service name

Returns:
	Integer - Error code: 0 on success or different of 0 on failure

=cut
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

		require Zevenet::Farm::GSLB::FarmGuardian;
		&setGSLBDeleteFarmGuardian( $fname, $svice );

		# Delete port configuration from config file
		require Zevenet::Farm::GSLB::Validate;
		if ( !getGSLBCheckPort( $fname, $srv_port ) )
		{
			require Zevenet::Farm::GSLB::Config;
			$output = &setGSLBRemoveTcpPort( $fname, $srv_port );
		}
		untie @fileconf;
	}

	return $output;
}

=begin nd
Function: setGSLBFarmNewService

	Create a new Service in a GSLB farm
	 
Parameters:
	farmname - Farm name
	service - Service name
	algorithm - Balancing algorithm. This field can value "roundrobin" defined in plugin multifo, or "prio" defined in plugin simplefo

Returns:
	Integer - Error code: 0 on success or different of 0 on failure

Bug:
	Output is not well controlled

=cut
sub setGSLBFarmNewService    # ($farm_name,$service,$algorithm)
{
	my ( $fname, $svice, $alg ) = @_;

	require Zevenet::Farm::GSLB::Service;

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

	require Zevenet::Farm::HTTP::Service;
	zenlog( "Services: " . &getGSLBFarmServices( $fname ) );
	if ( grep ( /^$svice$/, &getGSLBFarmServices( $fname ) ) )
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
			if ( ( grep ( /include\{plugins\/$gsalg\.cfg\}/, @fileconf ) ) == 0 )
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

			require Zevenet::Farm::Config;
			&setFarmVS( $fname, $svice, "dpc", "80" );
		}
	}

	return $output;
}

=begin nd
Function: getHTTPFarmVS

	Return a virtual server parameter
	
Parameters:
	farmname - Farm name
	service - Service name
	tag - Indicate which field will be returned. The options are: 
		ns - return string
		resources - return string with format: "resource1" . "\n" . "resource2" . "\n" . "resource3"..."
		backends - return string with format: "backend1" . "\n" . "backend2" . "\n" . "backend3"..."
		algorithm - string with the possible values: "prio" for priority algorihm or "roundrobin" for round robin algorithm 
		plugin - Gslb plugin used for balancing. String with the possbible values: "simplefo " for priority or "multifo" for round robin
		dpc - Default port check. Gslb use a tcp check to a port to check if backend is alive. This is disable when farm guardian is actived

Returns:
	string - The return value format depend on tag field

FIXME:
	return a hash with all parameters
				
=cut
sub getGSLBFarmVS    # ($farm_name,$service,$tag)
{
	my ( $fname, $svice, $tag ) = @_;

	require Tie::File;
	require Zevenet::Farm::Core;

	my $output = "";
	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );

	my @fileconf;
	my $line;
	my @linesplt;

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

	# remove first '\n' string separate
	$output =~ s/^\n//;
	return $output;
}

=begin nd
Function: setGSLBFarmVS

	Set values for a gslb service. server or dpc

Parameters:
	farmname 	- Farm name
	service - Service name
	param	- Parameter to modificate. The possible values are: "ns" name server or "dpc" default tcp port check
	value	- Value for the parameter

Returns:     
	Integer  - always return 0 
	
Bug:
	Always return 0, do error control
                
=cut
sub setGSLBFarmVS    # ($farm_name,$service,$tag,$string)
{
	my ( $fname, $svice, $tag, $stri ) = @_;

	require Tie::File;

	my $type  = &getFarmType( $fname );
	my $ffile = &getFarmFile( $fname );
	my $pluginfile;
	my @fileconf;
	my $line;
	my $param;
	my @linesplt;
	my $tcp_port;
	my $output = "";

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

		require Zevenet::Farm::GSLB::Zone;
		&setGSLBFarmZoneSerial( $fname, $svice );
	}

	if ( $tag eq "dpc" )
	{
		require Zevenet::Farm::GSLB::Validate;

		my $existPortFlag = &getGSLBCheckPort( $fname, $stri );
		my $actualPort;
		my $srvConf;
		my @srvCp;
		my $firstIndNew;
		my $offsetIndNew;
		my $firstIndOld;
		my $offsetIndOld;
		my $newPortFlag;
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
				$output     = 0;
				last;
			}
			if ( $line =~ /\t$svice => / )
			{
				$found = 1;
			}
		}
		untie @fileconf;

		if ( $output == 0 )
		{
			my $srvAsocFlag = &getGSLBCheckPort( $fname, $actualPort );
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

1;
