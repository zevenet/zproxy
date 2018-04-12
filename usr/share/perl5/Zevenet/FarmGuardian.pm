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

use Zevenet::Log;
use Zevenet::Config;

my $configdir = &getGlobalConfiguration( "configdir" );
my $fg_conf   = "$configdir/farmguardian.conf";
my $fg_template =
  &getGlobalConfiguration( "templatedir" ) . "/farmguardian.template";

sub getFGStatusFile
{
	my $farm = shift;
	my $srv  = shift;

	my $farm_tag = ( $srv ) ? "${farm}_$srv" : "$farm";

	return "$configdir\/$farm_tag\_status.cfg";
}

# return a struct with the parameters of farm guardian
sub getFGStruct
{
	return {
		'description' => "",       # Tiny description about the check
		'command'     => "",       # Command to check. The check must return 0 on sucess
		'farms'       => [],       # farm list where the farm guardian is applied
		'log'         => "false",  # logg farm guardian
		'interval'    => "10",     # Time between checks
		'cut_conns' => "false", # cut the connections with the backend is marked as down
		'template'  => "false",
	};
}

# the templates are not in the hash
sub getFGExistsConfig
{
	my $fg_name = shift;
	my $fh      = &getTiny( $fg_conf );
	return ( exists $fh->{ $fg_name } ) ? 1 : 0;
}

sub getFGExistsTemplate
{
	my $fg_name = shift;
	my $fh      = &getTiny( $fg_template );
	return ( exists $fh->{ $fg_name } ) ? 1 : 0;
}

sub getFGExists
{
	my $fg_name = shift;
	return ( &getFGExistsTemplate( $fg_name ) or &getFGExistsConfig( $fg_name ) );
}

# the templates are not in the list
sub getFGConfigList
{
	my $fg_file = &getTiny( $fg_conf );
	return keys %{ $fg_file };
}

sub getFGTemplateList
{
	my $fg_file = &getTiny( $fg_template );
	return keys %{ $fg_file };
}

sub getFGObject
{
	my $fg_name      = shift;
	my $use_template = shift;

	my $file = ( $use_template eq 'template' ) ? $fg_template : $fg_conf;
	my $obj = &getTiny( $file )->{ $fg_name };

	$obj = &setConfigStr2Arr( $obj, ['farms'] );

	return $obj;
}

sub getFGFarm
{
	my $farm = shift;
	my $srv  = shift;
	my $fg;

	my $farm_tag = ( $srv ) ? "${farm}_$srv" : "$farm";
	my $fg_list = &getTiny( $fg_conf );
	foreach my $fg_name ( keys %{ $fg_list } )
	{
		if ( grep ( /(^| )$farm_tag( |$)/, $fg_list->{ $fg_name }->{ farms } ) )
		{
			$fg = $fg_name;
			last;
		}
	}

	return $fg;
}

# create a farm guardian from a blank template
sub createFGBlank
{
	my $name = shift;

	my $values = &getFGStruct();
	&setFGObject( $name, $values );
}

# create a farm guardian from a blank template
sub createFGTemplate
{
	my $name     = shift;
	my $template = shift;

	my $values = &getFGObject( $template, 'template' );
	$values->{ $name }->{ 'template' } = "false";

	&setFGObject( $name, $values );
}

# create a farm guardian from a farm guardian in the config file
sub createFGConfig
{
	my $name      = shift;
	my $fg_config = shift;

	my $values = &getFGObject( $fg_config );
	$values->{ farms } = [];
	&setFGObject( $name, $values );
}

# pedir parametro force en zapi, si tiene alguna granja asociada
sub delFGObject
{
	my $fg_name = shift;

	my $out = &runFGStop( $fg_name );
	my $out = &delTinyObj( $fg_conf, $fg_name );

	return $out;
}

# modifico fg, reiniciar todos los fg que esten asociados tanto a granjas como a srv
# pedir confirmacion, parametro force
sub setFGObject
{
	my $fg_name = shift;
	my $key     = shift;
	my $value   = shift;

	my $restart = 0;
	my $out;

	# not restart if only is changed the parameter description
	if ( ref $key )
	{
		if ( grep ( !/^description$/, keys %{ $key } ) ) { $restart = 1; }
	}
	elsif ( $key ne 'description' ) { $restart = 1; }
	if ( not &getFGExistsConfig( $fg_name ) ) { $restart = 0; }

	$out = &runFGStop( $fg_name ) if $restart;
	$out = &setTinyObj( $fg_conf, $fg_name, $key, $value );
	$out = &runFGStart( $fg_name ) if $restart;

	return $out;
}

sub setFGFarmRename
{
	my $farm     = shift;
	my $new_farm = shift;

	my $fh = &getTiny( $fg_conf );
	my $srv;
	my $farm_tag;
	my $new_farm_tag;
	my $out;

	# foreach farm check, remove and add farm
	foreach my $fg ( keys %{ $fh } )
	{
		if ( $fh->{ $fg }->{ farms } =~ /(?:^| )${farm}_?([\w-]+)?(?:$| )/ )
		{
			$srv          = $1;
			$farm_tag     = ( $srv ) ? "${farm}_$srv" : $farm;
			$new_farm_tag = ( $srv ) ? "${new_farm}_$srv" : $farm;

			$out = &setTinyObj( $fg_conf, $fg, 'farms', $farm_tag,     'del' );
			$out = &setTinyObj( $fg_conf, $fg, 'farms', $new_farm_tag, 'add' );

			my $status_file     = &getFGStatusFile( $farm,     $srv );
			my $new_status_file = &getFGStatusFile( $new_farm, $srv );
			&zenlog( "renaming $status_file =>> $new_status_file" ) if &debug;
			rename ( $status_file, $new_status_file );
		}
	}

	return $out;
}

sub linkFGFarm
{
	my $fg_name = shift;
	my $farm    = shift;
	my $srv     = shift;
	my $out;

	require Zevenet::Farm::Base;
	my $farm_tag = ( $srv ) ? "${farm}_$srv" : "$farm";

	$out = &setTinyObj( $fg_conf, $fg_name, 'farms', $farm_tag, 'add' );

	$out |= &runFGFarmStart( $farm, $srv ) if ( &getFarmStatus( $farm ) eq 'up' );

	return $out;
}

# aplicar cuando se borra la granja
sub unlinkFGFarm
{
	my $fg_name = shift;
	my $farm    = shift;
	my $srv     = shift;

	my $type = &getFarmType( $farm );

	require Zevenet::Log;

	my $farm_tag = ( $srv ) ? "${farm}_$srv" : "$farm";
	my $out = &runFGFarmStop( $farm, $srv );

	$out = &setTinyObj( $fg_conf, $fg_name, 'farms', $farm_tag, 'del' ) if !$out;

	return $out;
}

sub delFGFarm
{
	my $farm = shift;
	my $srv  = shift;

	require Zevenet::Farm::Service;

	my $fg;
	my $err = &runFGFarmStop( $farm, $srv );
	my $type = &getFarmType( $farm );

	if ( $type =~ /http/ or $type eq 'gslb' )
	{
		if ( not $srv )
		{
			foreach $srv ( &getFarmServices( $farm ) )
			{
				$fg = &getFGFarm( $farm, $srv );
				$err |= &setTinyObj( $fg_conf, $fg, 'farms', "${farm}_$srv", 'del' );
			}
		}
		else
		{
			$fg = &getFGFarm( $farm, $srv );
			$err |= &setTinyObj( $fg_conf, $fg, 'farms', "${farm}_$srv", 'del' );
		}
	}
	else
	{
		$fg = &getFGFarm( $farm );
		$err |= &setTinyObj( $fg_conf, $fg, 'farms', $farm, 'del' );
	}
}

############# run process

sub getFGPidFile
{
	my $fname  = shift;
	my $svice  = shift;
	my $piddir = &getGlobalConfiguration( 'piddir' );
	my $file;

	if ( $svice )
	{
		# return a regexp for a farm the request service
		$file = "$piddir/${fname}_${svice}_guardian.pid";
	}
	else
	{
		# return a regexp for a farm and all its services
		$file = "$piddir/${fname}_guardian.pid";
	}

	return $file;
}

# get the farmguardian pid for a farm. If the farm is http, this function acts in two ways:
# 1- farm and service parameters are sent, the function will return the pid for the farma and service requested
# 2- only farm parameter is sent, then the function will return a list with the running farmguardian pid, one foreach service
sub getFGPidFarm
{
	my $farm    = shift;
	my $service = shift;
	my $pid;

	# get pid
	my $pidFile = &getFGPidFile( $farm, $service );

	open my $fh, '<', $pidFile or return 0;
	$pid = <$fh>;
	close $fh;

	# check if the pid exists
	my $run = kill 0, $pid;

	# if it does not exists, remove the pid file
	if ( !$run )
	{
		$pid = 0;
		unlink $pidFile;
	}

	# return status
	return $pid;
}

# Reset farm guardian for all farms
# si reinicio|paro|arranco granja o si borro un servicio, seleccionar todos los fg que tengan algun serivcio de esa granja
sub runFGStop
{
	my $fgname = shift;
	my $out;

	&zenlog( "Stopping farmguardian $fgname", "debug", "FG" );

	my $obj = &getFGObject( $fgname );
	foreach my $farm ( @{ $obj->{ farms } } )
	{
		my $srv;
		if ( $farm =~ /([^_]+)_(.+)/ )
		{
			$farm = $1;
			$srv  = $2;
		}

		$out |= &runFGFarmStop( $farm, $srv );
	}

	return $out;
}

sub runFGStart
{
	my $fgname = shift;
	my $out;

	&zenlog( "Starting farmguardian $fgname", "debug", "FG" );

	my $obj = &getFGObject( $fgname );
	foreach my $farm ( @{ $obj->{ farms } } )
	{
		my $srv;
		if ( $farm =~ /([^_]+)_(.+)/ )
		{
			$farm = $1;
			$srv  = $2;
		}

		$out |= &runFGFarmStart( $farm, $srv );
	}

	return $out;
}

sub runFGRestart
{
	my $fgname = shift;
	my $out;

	$out = &runFGStop( $fgname );
	$out |= &runFGStart( $fgname );

	return $out;
}

# Reset farm guardian for farm
# si reinicio|paro|arranco granja o si borro un servicio, seleccionar todos los fg que tengan algun serivcio de esa granja
#
sub runFGFarmStop
{
	my $farm    = shift;
	my $service = shift
	  ; # optional, if the farm is http and the service is not sent to the function, all services will be restarted
	my $out;
	my $srvtag;
	my $status_file = &getFGStatusFile( $farm, $service );

	require Zevenet::Farm::Core;
	my $type = &getFarmType( $farm );
	if ( $type =~ /http/ and not $service )
	{
		require Zevenet::Farm::Service;
		foreach my $srv ( &getFarmServices( $farm ) )
		{
			$out |= &runFGFarmStop( $farm, $srv );
		}
	}
	else
	{
		my $fgpid = &getFGPidFarm( $farm, $service );

		if ( $fgpid )
		{
			&zenlog( "running 'kill 9, $fgpid' stopping FarmGuardian $farm $service",
					 "debug", "FG" );
			# kill returns the number of process affected
			$out = kill 9, $fgpid;
			$out = ( not $out );
			if ( $out )
			{
				&zenlog( "running 'kill 9, $fgpid' stopping FarmGuardian $farm $service",
						 "error", "FG" );
			}

			# delete pid files
			unlink &getFGPidFile( $farm, $service );

			# put backend up
			if ( $type eq "http" || $type eq "https" )
			{
				if ( -e $status_file )
				{
					require Zevenet::Farm::HTTP::Config;
					my $portadmin = &getHTTPFarmSocket( $farm );
					my $idsv = &getFarmVSI( $farm, $service );

					require Tie::File;
					tie my @filelines, 'Tie::File', $status_file;

					my @fileAux = @filelines;
					my $lines   = scalar @fileAux;

					while ( $lines >= 0 )
					{
						$lines--;
						my $line = $fileAux[$lines];
						if ( $fileAux[$lines] =~ /0 $idsv (\d+) fgDOWN/ )
						{
							my $index    = $1;
							my $auxlin   = splice ( @fileAux, $lines, 1, );
							my $poundctl = &getGlobalConfiguration( 'poundctl' );

							&logAndRun( "$poundctl -c $portadmin -B 0 $idsv $index" );
						}
					}
					@filelines = @fileAux;
					untie @filelines;
				}
			}

			if ( $type eq "l4xnat" )
			{
				require Zevenet::Farm::Backend;

				my @be = &getFarmBackendStatusCtl( $farm );
				my $i  = -1;

				foreach my $line ( @be )
				{
					my @subbe = split ( ";", $line );
					$i++;
					my $backendid     = $i;
					my $backendserv   = $subbe[2];
					my $backendport   = $subbe[3];
					my $backendstatus = $subbe[7];
					chomp $backendstatus;

					if ( $backendstatus eq "fgDOWN" )
					{
						$out |= &setL4FarmBackendStatus( $farm, $i, "up" );
					}
				}
			}
		}
		$srvtag = "${service}_" if ( $service );
		unlink "$configdir/${farm}_${srvtag}status.cfg";
	}

	return $out;
}

# the pid file is created by the farmguardian process
sub runFGFarmStart
{
	my ( $farm, $svice ) = @_;

	my $status = 0;
	my $log;
	my $sv;

	require Zevenet::Farm::Core;
	require Zevenet::Farm::Base;

	my $ftype = &getFarmType( $farm );

	# check if the farm is up
	return if ( &getFarmStatus( $farm ) ne 'up' );

	# if the farmguardian is running...
	if ( &getFGPidFarm( $farm, $svice ) )
	{
		return;
		#~ &runFGFarmStop( $farm, $svice );
	}

	&zenlog( "Start fg for farm $farm, $svice", "debug2", "FG" );


	if ( $ftype =~ /http/ && $svice eq "" )
	{
		require Zevenet::Farm::Config;

		# Iterate over every farm service
		my $services = &getFarmVS( $farm, "", "" );
		my @servs = split ( " ", $services );

		foreach my $service ( @servs )
		{
			$status |= &runFGFarmStart( $farm, $service );
		}
	}
	elsif ( $ftype eq 'l4xnat' || $ftype =~ /http/ )
	{
		my $fgname = &getFGFarm( $farm, $svice );

		return 0 if not $fgname;

		&zenlog( "Starting fg $fgname, farm $farm, $svice", "debug2", "FG" );
		my $fg = &getFGObject( $fgname );

		if ( $fg->{ log } eq 'true' )
		{
			$log = "-l";
		}

		if ( $svice ne "" )
		{
			$sv = "-s $svice";
		}

		my $farmguardian = &getGlobalConfiguration( 'farmguardian' );
		my $fg_cmd       = "$farmguardian $farm $sv $log";

		require Zevenet::Log;
		$status = system ( "$fg_cmd >/dev/null 2>&1 &" );
		if   ( $status ) { &zenlog( "running $fg_cmd", "error", "FG" ); }
		else             { &zenlog( "running $fg_cmd", 'debug', 'FG' ); }

		# necessary for waiting that fg process write its process
		sleep ( 1 );
	}
	# the gslb fg is put in the start process, then, it is necessary to restart the farm
	elsif ( $ftype eq 'gslb' )
	{
		require Zevenet::Farm::Action;
		&setFarmRestart( $farm );
	}
	else
	{
		# WARNING: farm types not supported by farmguardian return 0.
		$status = 1;
	}

	return $status;
}

sub runFGFarmRestart
{
	my $farm    = shift;
	my $service = shift;
	my $out;

	$out = &runFGFarmStop( $farm, $service );
	$out |= &runFGFarmStart( $farm, $service );

	return $out;
}

# if farm guardian is applied some running farm
# return all running farms where farm guardian is working
sub getFGRunningFarms
{
	my $fg = shift;
	my @runfarm;

	require Zevenet::Farm::Core;
	require Zevenet::Farm::Base;
	# check all pid
	foreach my $farm ( @{ &getFGObject( $fg )->{ 'farms' } } )
	{
		my $srv;
		if ( $farm =~ /([^_]+)_(.+)/ )
		{
			$farm = $1;
			$srv  = $2;
		}

		if ( &getFarmStatus( $farm ) eq 'up' )
		{
			push @runfarm, $farm;
		}
	}
	return \@runfarm;
}

sub getFGMigrateFile
{
	my $farm = shift;
	my $srv  = shift;

	return ( $srv ) ? "_default_${farm}_$srv" : "_default_$farm";
}

sub setOldFarmguardian
{
	my $obj = shift;

	my $srv  = $obj->{ service } // "";
	my $farm = $obj->{ farm };
	my $name = &getFGMigrateFile( $obj->{ farm }, $srv );
	my $type = &getFarmType( $farm );
	my $set;

	&zenlog( "setOldFarmguardian: $farm, $srv", "debug2", "FG" );

	# default object
	my $def = {
		'description' =>
		  "Deprecated. This farm guardian was created using a zapi version before than 3.2",
		'command'   => $obj->{ command },
		'log'       => $obj->{ log },
		'interval'  => $obj->{ interval },
		'cut_conns' => ( $type =~ /http/ ) ? "true" : "false",
		'template'  => "false",
		'farms'     => [],
	};

	&runFGFarmStop( $farm, $srv );

	# if exists, update it
	if ( &getFGExistsConfig( $name ) )
	{
		$set               = &getFGObject( $name );
		$set->{ command }  = $obj->{ command } if exists $obj->{ command };
		$set->{ log }      = $obj->{ log } if exists $obj->{ log };
		$set->{ interval } = $obj->{ interval } if exists $obj->{ interval };
	}

	# else create it
	else
	{
		$set = $def;
	}

	&setFGObject( $name, $set );
	my $farm_tag = ( $srv ) ? "${farm}_$srv" : $farm;
	&setTinyObj( $fg_conf, $name, 'farms', $farm_tag, 'add' )
	  if ( $obj->{ enable } eq 'true' );
}

####################################################################
######## ######## 	OLD FUNCTIONS 	######## ########
# Those functions are for compatibility with the APIs 3.0 and 3.1
####################################################################

=begin nd
Function: getFarmGuardianStatus

	Returns if FarmGuardian is activated for this farm

Parameters:
	fname - Farm name.
	svice - Service name. Only apply if the farm profile has services. Leave undefined for farms without services.

Returns:
	-1 - If farmguardian file was not found.
	 0 - If farmguardian is disabled.
	 1 - If farmguardian is enabled.

=cut

sub getFarmGuardianStatus    # ($fname,$svice)
{
	my ( $fname, $svice ) = @_;

	if ( !&getFGFarm( $fname, $svice ) )
	{
		&zenlog( "The $fname $svice has not farm guardian linked", "debug", "FG" );
		return -1;
	}

	if ( &getFGPidFarm( $fname, $svice ) )
	{
		&zenlog( "The fg for $fname $svice is running", "debug2", "FG" );
		return 1;
	}

	return 0;
}

=begin nd
Function: getFarmGuardianLog

	Returns if FarmGuardian has logs activated for this farm

Parameters:
	fname - Farm name.
	svice - Service name. Only apply if the farm profile has services. Leave undefined for farms without services.

Returns:
	-1 - If farmguardian file was not found.
	 0 - If farmguardian log is disabled.
	 1 - If farmguardian log is enabled.

Bugs:

See Also:
	<runFarmGuardianStart>
=cut

sub getFarmGuardianLog    # ($fname,$svice)
{
	my ( $fname, $svice ) = @_;

	my $fg = &getFGFarm( $fname, $svice );

	return &getFGObject( $fg )->{ logs } // undef;
}

=begin nd
Function: runFarmGuardianStart

	Start FarmGuardian rutine

Parameters:
	fname - Farm name.
	svice - Service name. Only apply if the farm profile has services. Leave undefined for farms without services.

Returns:
	-1       - If farmguardian file was not found or if farmguardian is not running.
	 0       - If farm profile is not supported by farmguardian, or farmguardian was executed.

Bugs:
	Returning $? after running a command in the background & gives the illusion of capturing the ERRNO of the ran program. That is not possible since the program may not have finished.

See Also:
	zcluster-manager, zevenet, <runFarmStart>, <setNewFarmName>, zapi/v3/farm_guardian.cgi, zapi/v2/farm_guardian.cgi
=cut

sub runFarmGuardianStart    # ($fname,$svice)
{
	my ( $fname, $svice ) = @_;

	return &runFGFarmStart( $fname, $svice );
}

=begin nd
Function: runFarmGuardianStop

	Stop FarmGuardian rutine

Parameters:
	fname - Farm name.
	svice - Service name. Only apply if the farm profile has services. Leave undefined for farms without services.

Returns:
	Integer - 0 on success, or greater than 0 on failure.

See Also:
	zevenet, <runFarmStop>, <setNewFarmName>, zapi/v3/farm_guardian.cgi, <runFarmGuardianRemove>
=cut

sub runFarmGuardianStop    # ($fname,$svice)
{
	my ( $fname, $svice ) = @_;

	return &runFGFarmStop( $fname, $svice );
}

=begin nd
Function: runFarmGuardianCreate

	Create or update farmguardian config file

	ttcheck and script must be defined and non-empty to enable farmguardian.

Parameters:
	fname - Farm name.
	ttcheck - Time between command executions for all the backends.
	script - Command to run.
	usefg - 'true' to enable farmguardian, or 'false' to disable it.
	fglog - 'true' to enable farmguardian verbosity in logs, or 'false' to disable it.
	svice - Service name.

Returns:
	-1 - If ttcheck or script is not defined or empty and farmguardian is enabled.
	 0 - If farmguardian configuration was created.

Bugs:
	The function 'print' does not write the variable $?.

See Also:
	zapi/v3/farm_guardian.cgi, zapi/v2/farm_guardian.cgi
=cut

sub runFarmGuardianCreate    # ($fname,$ttcheck,$script,$usefg,$fglog,$svice)
{
	my ( $fname, $ttcheck, $script, $usefg, $fglog, $svice ) = @_;

	&zenlog(
		"runFarmGuardianCreate( farm: $fname, interval: $ttcheck, cmd: $script, log: $fglog, enabled: $usefg )",
		"debug2"
	);

	# get default name and check not exist
	my $obj = {
				'service'  => $svice,
				'farm'     => $fname,
				'command'  => $script,
				'log'      => $fglog,
				'interval' => $ttcheck,
				'enable'   => $usefg,
	};

	my $output = &setOldFarmguardian( $obj );

	# start
	$output |= &runFGFarmStart( $fname, $svice );

	return $output;
}

=begin nd
Function: runFarmGuardianRemove

	Remove farmguardian down status on backends.

	When farmguardian is stopped or disabled any backend marked as down by farmgardian must reset it's status.

Parameters:
	fname - Farm name.
	svice - Service name. Only apply if the farm profile has services. Leave undefined for farms without services.

Returns:
	none - Nothing is returned explicitly.

Bugs:

See Also:
	zapi/v3/farm_guardian.cgi, zapi/v2/farm_guardian.cgi, <deleteFarmService>
=cut

sub runFarmGuardianRemove    # ($fname,$svice)
{
	my ( $fname, $svice ) = @_;

	my $fg = &getFGFarm( $fname, $svice );

	return if ( not $fg );

	# "unlink" stops the fg
	my $out = &unlinkFGFarm( $fg, $fname, $svice );

	if ( $fg eq &getFGMigrateFile( $fname, $svice )
		 and !@{ &getFGObject( $fg )->{ farms } } )
	{
		$out |= &delFGObject( $fg );
	}

	return;
}

=begin nd
Function: getFarmGuardianConf

	Get farmguardian configuration for a farm-service.

Parameters:
	fname - Farm name.
	svice - Service name. Only apply if the farm profile has services. Leave undefined for farms without services.

Returns:
	list - List with (fname, ttcheck, script, usefg, fglog).

Bugs:
	There is no control if the file could not be opened, for example, if it does not exist.

See Also:
	L4xNAT: <setL4FarmSessionType>, <setL4FarmAlgorithm>, <setFarmProto>, <setFarmNatType>, <setL4FarmMaxClientTime>, <setL4FarmVirtualConf>, <setL4FarmServer>, <runL4FarmServerDelete>, <setL4FarmBackendStatus>, <setL4NewFarmName>, <_runL4ServerStart>, <_runL4ServerStop>

	zapi/v3/get_l4.cgi, zapi/v3/farm_guardian.cgi,

	zapi/v2/get_l4.cgi, zapi/v2/farm_guardian.cgi, zapi/v2/get_http.cgi, zapi/v2/get_tcp.cgi

	<getHttpFarmService>, <getHTTPServiceStruct>
=cut

sub getFarmGuardianConf    # ($fname,$svice)
{
	my ( $fname, $svice ) = @_;

	# name for old checks
	my $old = &getFGMigrateFile( $fname, $svice );
	my $obj;
	my $usefg = "true";

	my $fg = &getFGFarm( $fname, $svice );
	if ( not $fg )
	{
		$fg = $old if &getFGExists( $old );
		$usefg = "false";
	}

	if ( $fg )
	{
		$obj = &getFGObject( $fg );

		# (fname, ttcheck, script, usefg, fglog).
		return ( $fname, $obj->{ interval }, $obj->{ command }, $usefg, $obj->{ log } );
	}

	return;
}

=begin nd
Function: getFarmGuardianPid

	Read farmgardian pid from pid file. Check if the pid is running and return it,
	else it removes the pid file.

Parameters:
	fname - Farm name.
	svice - Service name. Only apply if the farm profile has services. Leave undefined for farms without services.

Returns:
	-1      - If farmguardian PID file was not found (farmguardian not running).
	integer - PID number (unsigned integer) if farmguardian is running.

Bugs:
	Regex with .* should be fixed.

See Also:
	zevenet

	L4xNAT: <setL4FarmSessionType>, <setL4FarmAlgorithm>, <setFarmProto>, <setFarmNatType>, <setL4FarmMaxClientTime>, <setL4FarmVirtualConf>, <setL4FarmServer>, <runL4FarmServerDelete>, <setL4FarmBackendStatus>, <setL4NewFarmName>, <_runL4ServerStart>, <_runL4ServerStop>
=cut

sub getFarmGuardianPid    # ($fname,$svice)
{
	my ( $fname, $svice ) = @_;

	my @pid_list = &getFGPidFarm( $fname, $svice );
	return $pid_list[0];
}

1;
