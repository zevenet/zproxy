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

my $configdir = &getGlobalConfiguration( 'configdir' );

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname ) = @_;

	my $output = -1;
	my @srvarr = ();

	opendir ( DIR, "$configdir\/$fname\_gslb.cfg\/etc\/plugins\/" );
	my @pluginlist = readdir ( DIR );
	closedir ( DIR );

	foreach my $plugin ( @pluginlist )
	{
		next if $plugin =~ /^\./;

		open my $fh, "$configdir\/$fname\_gslb.cfg\/etc\/plugins\/$plugin";

		my @srv = grep ( /^\t[a-zA-Z1-9].* => \{/, <$fh> );

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

		close $fh;
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname, $svice ) = @_;

	my $output     = -1;
	my $pluginfile = "";
	my $srv_port;

	#Find the plugin file
	opendir ( DIR, "$configdir\/$fname\_gslb.cfg\/etc\/plugins\/" );
	my @pluginlist = readdir ( DIR );

	# look for the plugin file including the service
	foreach my $plugin ( @pluginlist )
	{
		tie my @fileconf, 'Tie::File',
		  "$configdir\/$fname\_gslb.cfg\/etc\/plugins\/$plugin";
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
		  qq{grep '$plugin_name!$svice ;' $configdir\/$fname\_gslb.cfg\/etc\/zones/*};

		my $grep_output = &logAndGet( $grep_cmd );

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
		  "$configdir\/$fname\_gslb.cfg\/etc\/plugins\/$pluginfile";

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
			tie my @config_file, 'Tie::File', "$configdir\/$fname\_gslb.cfg\/etc\/config";

			# remove the line of that plugin
			@config_file = grep { !/plugins\/$pluginfile/ } @config_file;
			untie @config_file;
		}

		include 'Zevenet::Farm::GSLB::FarmGuardian';
		&setGSLBDeleteFarmGuardian( $fname, $svice );
		require Zevenet::FarmGuardian;
		&runFarmGuardianRemove( $fname, $svice );

		# Delete port configuration from config file
		include 'Zevenet::Farm::GSLB::Validate';

		if ( !getGSLBCheckPort( $fname, $srv_port ) )
		{
			include 'Zevenet::Farm::GSLB::Config';
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname, $svice, $alg ) = @_;

	include 'Zevenet::Farm::GSLB::Service';

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

	include 'Zevenet::Farm::GSLB::Service';
	&zenlog( "Services: " . &getGSLBFarmServices( $fname ) );
	if ( grep ( /^$svice$/, &getGSLBFarmServices( $fname ) ) )
	{
		$output = -1;
	}
	else
	{
		if ( !( -e "$configdir/${fname}_gslb.cfg/etc/plugins/${gsalg}.cfg" ) )
		{
			open my $fd, '>', "$configdir\/$fname\_gslb.cfg\/etc\/plugins\/$gsalg.cfg";
			print $fd "$gsalg => {\n\tservice_types = up\n";
			print $fd "\t$svice => {\n\t\tservice_types = tcp_80\n";
			if ( $gsalg eq "simplefo" )
			{
				print $fd "\t\tprimary => 127.0.0.1\n";
				print $fd "\t\tsecondary => 127.0.0.1\n";
			}
			else
			{
				print $fd "\t\t1 => 127.0.0.1\n";
			}
			print $fd "\t}\n}\n";
			close $fd;
			$output = 0;
		}
		else
		{
			# Include the service in the plugin file
			use Tie::File;
			tie my @fileconf, 'Tie::File',
			  "$configdir\/$fname\_gslb.cfg\/etc\/plugins\/$gsalg.cfg";
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
			use Tie::File;

			# Include the plugin file in the main configuration
			tie my @fileconf, 'Tie::File', "$configdir\/$fname\_gslb.cfg\/etc\/config";
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
			&addGSLBDefCheck( $fname, "80" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname, $svice, $tag ) = @_;

	require Tie::File;
	require Zevenet::Farm::Core;

	my $output = "";
	my $ffile  = &getFarmFile( $fname );

	my @fileconf;
	my @linesplt;

	if ( $tag eq "ns" || $tag eq "resources" )
	{
		tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/zones/$svice";
		foreach my $line ( @fileconf )
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
		opendir ( DIR, "$configdir\/$fname\_gslb.cfg\/etc\/plugins\/" );
		my @pluginlist = readdir ( DIR );

		foreach my $plugin ( @pluginlist )
		{
			tie @fileconf, 'Tie::File',
			  "$configdir\/$fname\_gslb.cfg\/etc\/plugins\/$plugin";
			if ( grep ( /^\t$svice => /, @fileconf ) )
			{
				$pluginfile = $plugin;
			}
			untie @fileconf;
		}

		closedir ( DIR );
		tie @fileconf, 'Tie::File',
		  "$configdir\/$fname\_gslb.cfg\/etc\/plugins\/$pluginfile";

		foreach my $line ( @fileconf )
		{
			if ( $tag eq "backends" )
			{
				if ( $found == 1 && $line =~ /.*}.*/ )
				{
					last;
				}
				if ( $found == 1 && $line !~ /^$/ && $line !~ /.*service_types.*/ )
				{
					# remove tab characters
					my $tmp = $line;
					$tmp =~ s/\t//g;

					$output = "$output\n$tmp";
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname, $svice, $tag, $stri ) = @_;

	require Tie::File;

	my $ffile = &getFarmFile( $fname );
	my $pluginfile;
	my @fileconf;
	my $param;
	my @linesplt;
	my $output = "";

	if ( $tag eq "ns" )
	{
		tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/zones/$svice";
		foreach my $line ( @fileconf )
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

		include 'Zevenet::Farm::GSLB::Zone';
		&setGSLBFarmZoneSerial( $fname, $svice );
	}

	if ( $tag eq "dpc" )
	{
		my $old_port;
		include 'Zevenet::Farm::GSLB::Validate';
		require Zevenet::FarmGuardian;
		my $fg = &getFGFarm( $fname, $svice );

		# overwrite in the service file
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

		my $found = 0;
		foreach my $line ( @fileconf )
		{
			if ( $found == 1 && $line =~ /.*}.*/ )
			{
				last;
			}

			if ( $found == 1 && $line =~ /service_types = (${svice}_fg_|tcp_)(\d+)/ )
			{
				$old_port = $2;
				$line     = "\t\tservice_types = $1$stri";
				$output   = 0;
				last;
			}

			if ( $line =~ /\t$svice => / )
			{
				$found = 1;
			}
		}
		untie @fileconf;

		if ( $output )
		{
			&zenlog( "Error modifying the service port", 'error', 'GSLB' );
			return 1;
		}

		# if exists fg, change the port using fg functions
		if ( $fg )
		{
			$output = &unlinkGSLBFg( $fname, $svice );
			$output += &linkGSLBFg( $fg, $fname, $svice );
		}
		else
		{
			# create a new check port srv if the service is not using FG
			$output = &addGSLBDefCheck( $fname, $stri );

			# If the port is used for another service, do not delete it
			my $srvAsocFlag = &getGSLBCheckPort( $fname, $old_port );
			if ( !$srvAsocFlag and !$output )
			{
				include 'Zevenet::Farm::GSLB::Config';
				$output = &setGSLBRemoveTcpPort( $fname, $old_port );
			}
		}
	}

	return $output;
}

sub getGSLBFarmServicesStruct
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname = shift;

	require Zevenet::FarmGuardian;
	include 'Zevenet::Farm::GSLB::Backend';
	include 'Zevenet::Alias';

	my @out_s = ();

	# Services
	my @services = &getGSLBFarmServices( $farmname );

	foreach my $srv_it ( @services )
	{
		my @serv = split ( ".cfg", $srv_it );
		my $srv  = $serv[0];
		my $lb   = &getGSLBFarmVS( $farmname, $srv, "algorithm" );

		# Default port health check
		my $dpc = &getGSLBFarmVS( $farmname, $srv, "dpc" );

		# Backends
		my $out_b = &getGSLBFarmBackends( $farmname, $srv );
		&addAliasBackendsStruct( $out_b );

		push @out_s,
		  {
			id           => $srv,
			algorithm    => $lb,
			deftcpport   => $dpc + 0,
			farmguardian => &getFGFarm( $farmname, $srv ),
			backends     => $out_b,
		  };
	}

	return \@out_s;
}

sub getGSLBFarmServicesStruct31
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname = shift;

	require Zevenet::FarmGuardian;

	# Services
	my @services = @{ &getGSLBFarmServicesStruct( $farmname ) };

	foreach my $srv ( @services )
	{
		delete $srv->{ farmguardian };

		# Farmguardian
		my ( $fgTime, $fgScrip ) =
		  &getGSLBFarmGuardianParams( $farmname, $srv->{ id } );
		my $fgStatus = &getGSLBFarmFGStatus( $farmname, $srv->{ id } );

		$srv->{ fgenabled }   = $fgStatus;
		$srv->{ fgscript }    = $fgScrip;
		$srv->{ fgtimecheck } = $fgTime + 0;
	}

	return \@services;
}

sub setGSLBFarmPort
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farmname, $service, $defport ) = @_;
	my $error = 0;

	include 'Zevenet::Farm::GSLB::FarmGuardian';
	include 'Zevenet::Farm::GSLB::Config';

	my $old_deftcpport = &getGSLBFarmVS( $farmname, $service, 'dpc' );
	&setFarmVS( $farmname, $service, "dpc", $defport );

	# Update farmguardian
	my ( $fgTime, $fgScript ) = &getGSLBFarmGuardianParams( $farmname, $service );

	# Changing farm guardian port check
	if ( $fgScript =~ s/-p $old_deftcpport/-p$defport/ )
	{
		$error = &setGSLBFarmGuardianParams( $farmname, $service, 'cmd', $fgScript );
	}

	# check if setting FG params failed
	if ( !$error )
	{
		&runGSLBFarmReload( $farmname );
	}

	return $error;
}

sub existGSLBDefCheck
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farm      = shift;
	my $port      = shift;
	my $ffile     = &getFarmFile( $farm );
	my $farm_file = "$configdir/$ffile/etc/config";
	my $exist     = 0;

	open my $fh, '<', $farm_file or return 0;
	$exist = grep ( /tcp_$port =>/, <$fh> );
	close $fh;

	return $exist;
}

sub addGSLBDefCheck
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm, $port ) = @_;

	# do not add if it already exists
	if ( &existGSLBDefCheck( $farm, $port ) )
	{
		return 0;
	}

	require Zevenet::File;
	my $newTcp =
	    "\ttcp_$port => {\n"
	  . "\t\tplugin = tcp_connect,\n"
	  . "\t\tport = $port,\n"
	  . "\t\tup_thresh = 2,\n"
	  . "\t\tok_thresh = 2,\n"
	  . "\t\tdown_thresh = 2,\n"
	  . "\t\tinterval = 5,\n"
	  . "\t\ttimeout = 3,\n" . "\t}\n";

	my $ffile     = &getFarmFile( $farm );
	my $farm_file = "$configdir/$ffile/etc/config";

	my $err = &insertFileWithPattern( $farm_file, [$newTcp], "service_types => \\{",
									  'after' );

	return $err;
}

1;
