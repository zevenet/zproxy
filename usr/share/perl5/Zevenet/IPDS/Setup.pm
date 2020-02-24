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
use warnings;

include 'Zevenet::IPDS::Blacklist::Core';
include 'Zevenet::IPDS::Blacklist::Config';

=begin nd
Function: setIPDSPackagePostinst

	This functions is called from the IPDS package postinst to upload the data
	for the IPDS rules and reload the rules that are running.

Parameters:
	data - They are the data to upload. It is a hash with the keys:
		"local_lists" are the local list names that are incluided in the package;
		"remote_lists" are URL and information about remote lists;
		"domains" are the RBL domains to feed the RBL DNS domains.

Returns:
	none - .

See Also:
	<zevenet-ipds>
=cut

sub setIPDSPackagePostinst
{
	my $data = shift;

	my $ipds_dir = &getGlobalConfiguration( "configdir" ) . "/ipds";

	# install  blacklist
	include 'Zevenet::IPDS::Blacklist::Actions';
	&setBLAddPreloadLists( $data->{ local_lists }, $data->{ remote_lists } );
	&runBLRestartModule();

	# install RBL
	my $preloadedDomainsFile = "$ipds_dir/rbl/preloaded_domains.conf";
	tie my @file, "Tie::File", $preloadedDomainsFile;

	foreach my $domain ( @{ $data->{ new_domains } } )
	{
		push @file, $domain if ( !grep ( /^$domain$/, @file ) );
	}

	# install WAF
	include 'Zevenet::IPDS::WAF::Actions';
	&updateWAFSetPreload();

	use Proc::Find qw(find_proc);
	my $pids = &find_proc( cmndline => qr/\bzeninotify\b/ );
	if ( @{ $pids } )
	{
		&zenlog( "Continuing zeninotify service after upgrading the IPDS package",
				 "debug", "ipds" );

		my $lock_ipds = &getGlobalConfiguration( 'lockIpdsPackage' );
		unlink $lock_ipds;
	}

	# restart ipds rules in remote node
	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds', 'restart' );
}

=begin nd
Function: setIPDSPackagePreinst

	This functions is called from the IPDS package preinst to upload the data
	for the IPDS rules and reload the rules that are running.

Parameters:
	Migration - It is an struct for migration process with data of the list before and after of the upgrading

Returns:
	none - .

See Also:
	<zevenet-ipds>
=cut

sub setIPDSPackagePreinst
{
	my $migration = shift;

	use Proc::Find qw(find_proc);
	my $pids = &find_proc( cmndline => qr/\bzeninotify\b/ );
	if ( @{ $pids } )
	{
		&zenlog( "Stopping zeninotify service for upgrading the IPDS package",
				 "debug", "ipds" );

		my $lock_ipds = &getGlobalConfiguration( 'lockIpdsPackage' );
		&logAndRun( "touch $lock_ipds" );
	}

	&migrate_blacklist_names( $migration );

	# function delete lists
	my @list_to_delete = ( "nonspecasiapaslocation", "test", "prueba" );

	&remove_blacklists( @list_to_delete );

	# farms to renamed
	my @list_to_rename =
	  ( { "name" => "reserved", "new_name" => "Private_networks" }, );

	&rename_blacklists( @list_to_rename );
	&set_blacklists_status();
	&set_dos_status();
}

sub initIPDSModule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	include 'Zevenet::IPDS::Blacklist::Actions';
	include 'Zevenet::IPDS::DoS::Config';
	include 'Zevenet::IPDS::RBL::Config';
	include 'Zevenet::IPDS::WAF::Actions';

	&initBLModule();
	&initDOSModule();
	&initWAFModule();
	&initRBLModule();
}

sub migrate_blacklist_names
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	# migration hash
	my $migration = shift;

	foreach my $key ( keys %{ $migration } )
	{
		my $newlist = $migration->{ $key }->{ name };
		$newlist =~ s/\.txt$//;

		foreach my $oldlist ( @{ $migration->{ $key }->{ old_names } } )
		{
			$oldlist =~ s/\.txt$//;

			#if exists migrate it
			if ( &getBLExists( $oldlist ) )
			{
				# rename first one
				if ( !&getBLExists( $newlist ) )
				{
					&setBLParam( $oldlist, 'name', $newlist );
				}
				else

				  # delete others one
				{
					&setBLDeleteList( $oldlist );
				}
			}
		}
	}
}

sub remove_blacklists
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my @lists_to_remove = @_;

	foreach my $list ( @lists_to_remove )
	{
		if ( &getBLExists( $list ) && !@{ &getBLParam( $list, 'farms' ) } )
		{
			&setBLDeleteList( $list );
		}
	}
}

sub rename_blacklists
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my @list_to_rename = @_;

	foreach my $list ( @list_to_rename )
	{
		if (    &getBLExists( $list->{ name } )
			 && &getBLParam( $list->{ name }, 'preload' ) eq "true" )
		{
			&setBLParam( $list->{ name }, 'name', $list->{ new_name } );
		}
	}
}

# populate status parameter for blacklist rules
sub set_blacklists_status
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Config::Tiny;

	my $blacklistsConf = "/usr/local/zevenet/config/ipds/blacklists/lists.conf";
	my $fileHandle     = Config::Tiny->read( $blacklistsConf );

	foreach my $list ( keys %{ $fileHandle } )
	{
		next if ( exists $fileHandle->{ $list }->{ status } );

		if ( $fileHandle->{ $list }->{ farms } =~ /\w/ )
		{
			$fileHandle->{ $list }->{ status } = "up";
		}
		else
		{
			$fileHandle->{ $list }->{ status } = "down";
		}
	}

	$fileHandle->write( $blacklistsConf );
}

# populate status parameter for dos rules
sub set_dos_status
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Config::Tiny;

	my $dosConf    = "/usr/local/zevenet/config/ipds/dos/dos.conf";
	my $fileHandle = Config::Tiny->read( $dosConf );

	foreach my $rule ( keys %{ $fileHandle } )
	{
		next if ( exists $fileHandle->{ $rule }->{ status } );

		if ( $fileHandle->{ $rule }->{ farms } =~ /\w/ )
		{
			$fileHandle->{ $rule }->{ status } = "up";
		}
		else
		{
			$fileHandle->{ $rule }->{ status } = "down";
		}
	}

	$fileHandle->write( $dosConf );
}

=begin nd
Function: getIpdsPackageStatus

	This function get the status of the package and return the state

Parameters:
	none - .

Returns:
	Integer - The state of the package (0 Installed and updated, 1 Updates available, 2 Not installed) or undef in other case.

=cut

sub getIpdsPackageStatus
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Config;
	my $checkupgrades_bin = &getGlobalConfiguration( "checkupgrades_bin" );

	my $output = &logAndGet( "$checkupgrades_bin zevenet-ipds" );
	return 0 if ( $output =~ /already\sthe\snewest\sversion/ );
	return 1 if ( $output =~ /new\sversion/ );
	return 2 if ( $output =~ /not\sinstalled/ );
	return undef;
}

=begin nd
Function: getIpdsRulesetDate

	This function get the date of creation of the current ipds ruleset

Parameters:
	none - .

Returns:
	String - Date of creation of the ruleset, undef in other case.

=cut

sub getIpdsRulesetDate
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Config;
	my $dpkg_bin   = &getGlobalConfiguration( "dpkg_bin" );
	my $tail_bin   = &getGlobalConfiguration( "tail" );
	my $date_regex = qw/^\w+\s+zevenet-ipds\s+\d+\.\d+\.\d+\.(\d+)/;
	my $date       = undef;

	my $output = &logAndGet( "$dpkg_bin -l zevenet-ipds | $tail_bin -n 1" );

	$date = $1 if ( $output =~ $date_regex );

	return $date;
}

=begin nd
Function: getIpdsSchedule

	This function get the cron configuration for ipds upgrade

Parameters:
	none - .

Returns:
	String - The chedule configuration.

=cut

sub getIpdsSchedule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Config;
	my $ipdsCronFile = &getGlobalConfiguration( "ipdsCronFile" );
	my $error        = 0;
	my $cronFormat_re =
	  qw/^(?<min>\d+)\s+(?<hour>\d+(\-23\/\d*)?)\s+(?<dom>\d+|\*)\s+(?<month>\d+|\*)\s+(?<dow>[1-7]|\*)/;
	my $out = {
				mode      => "",
				frequency => "",
				time      => {
						  hour   => "0",
						  minute => "",
				},
	};
	if ( -e $ipdsCronFile )
	{
		require Zevenet::Lock;
		&ztielock( \my @list, $ipdsCronFile );
		if ( $list[0] =~ $cronFormat_re )
		{
			$out->{ mode } = "daily"
			  if ( $+{ dom } eq "*" && $+{ month } eq "*" && $+{ dow } eq "*" );
			$out->{ mode } = "weekly"
			  if ( $+{ dom } eq "*" && $+{ month } eq "*" && $+{ dow } ne "*" );
			$out->{ mode } = "monthly"
			  if ( $+{ dom } ne "*" && $+{ month } eq "*" && $+{ dow } eq "*" );

			if ( $out->{ mode } eq "weekly" or $out->{ mode } eq "monthly" )
			{
				$out->{ time }->{ hour }   = $+{ hour };
				$out->{ time }->{ minute } = $+{ min };
				$out->{ frequency } = $+{ dow } if ( $out->{ mode } eq "weekly" );
				$out->{ frequency } = $+{ dom } if ( $out->{ mode } eq "monthly" );
			}

			#Daily
			elsif ( $out->{ mode } eq "daily" )
			{
				my $hour = $+{ hour };
				$out->{ time }->{ minute } = $+{ min };
				if ( $hour =~ /(^\d+)(\-23\/)?(\d*)?/ )
				{
					$out->{ time }->{ hour } = $1 if ( $1 );
					$out->{ frequency } = $3 if ( $3 );
				}

				# ERROR: Not in valid format
				else
				{
					$error = 1;
				}
			}
			else
			{
				$error = 1;
			}
		}
		untie @list;
	}

	return undef if ( $error );
	return $out  if ( !$error );
}

=begin nd
Function: runIpdsUpgrade

	This function launch or schedule the update of the zevenet-ipds package

Parameters:
	none - .

Returns:
	Integer - Error code: 0 on success, undef if already latest version or other value on failure

=cut

sub runIpdsUpgrade
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $params = shift;
	my $error  = 0;
	require Zevenet::Config;
	my $aptget_bin = &getGlobalConfiguration( "aptget_bin" );

	if ( $params->{ action } eq "upgrade" )
	{
		my $cmd = "$aptget_bin update; $aptget_bin install zevenet-ipds";
		unless ( &getIpdsPackageStatus() )
		{
			&zenlog( "IPDS package: You already have the latest version", "info", "IPDS" );
			return undef;
		}
		require Zevenet::Log;
		$error = &logAndRun( "$cmd" );
		return $error if ( $error );
		&zenlog( "IPDS package: Successfully upgraded", "info", "IPDS" );
	}
	elsif ( $params->{ action } eq "schedule" )
	{
		$error = &setCronConfig( $params );
		return $error if ( $error );
	}
	return 0;
}

=begin nd
Function: setCronConfig

	This function launch or schedule the update of the zevenet-ipds package

Parameters:
	none - .

Returns:
	Integer - Error code: 0 on success or other value on failure

=cut

sub setCronConfig
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $params       = shift;
	my $aptget_bin   = &getGlobalConfiguration( "aptget_bin" );
	my $ipdsCronFile = &getGlobalConfiguration( "ipdsCronFile" );
	my $error        = 0;
	my $cronOpts = {
					 min   => "",
					 hour  => "",
					 dom   => "",
					 month => "",
					 dow   => "",
					 cmd   => "",
					 user  => "root",
	};

	$cronOpts->{ cmd } =
	  "$aptget_bin update && $aptget_bin install -y zevenet-ipds";

	# One day each week at fixed hour
	if ( $params->{ mode } eq "weekly" )
	{
		$cronOpts->{ dow }   = $params->{ frequency };
		$cronOpts->{ dom }   = "*";
		$cronOpts->{ month } = "*";
		$cronOpts->{ hour }  = $params->{ time }->{ hour };
		$cronOpts->{ min }   = $params->{ time }->{ minute };
	}

	# One day each month at fixed hour
	elsif ( $params->{ mode } eq "monthly" )
	{
		$cronOpts->{ dow }   = "*";
		$cronOpts->{ dom }   = $params->{ frequency };
		$cronOpts->{ month } = "*";
		$cronOpts->{ hour }  = $params->{ time }->{ hour };
		$cronOpts->{ min }   = $params->{ time }->{ minute };
	}
	elsif ( $params->{ mode } eq "daily" )
	{
		$cronOpts->{ dow }   = "*";
		$cronOpts->{ dom }   = "*";
		$cronOpts->{ month } = "*";
		$cronOpts->{ hour }  = "$params->{ time }->{ hour }-23/$params->{ frequency }"
		  if ( $params->{ frequency } != 0 );
		$cronOpts->{ hour } = $params->{ time }->{ hour }
		  if ( $params->{ frequency } == 0 );
		$cronOpts->{ min } = $params->{ time }->{ minute };
	}
	elsif ( $params->{ mode } eq "disabled" )
	{
		return 1 if ( !-f $ipdsCronFile );
		unlink $ipdsCronFile;
		&zenlog( "IPDS package: Successfully removed from cron", "info", "IPDS" );
	}

	if ( $params->{ mode } ne "disabled" )
	{
		require Zevenet::Lock;
		&ztielock( \my @list, $ipdsCronFile );
		@list = (
			"$cronOpts->{min} $cronOpts->{hour} $cronOpts->{dom} $cronOpts->{month} $cronOpts->{dow}\t$cronOpts->{user}\t$cronOpts->{cmd}"
		);
		untie @list;
		&zenlog( "IPDS package: Successfully added to cron", "info", "IPDS" );
	}

	return 0;
}

1;
