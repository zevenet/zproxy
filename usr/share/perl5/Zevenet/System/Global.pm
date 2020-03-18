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
Function: getSystemGlobal

	Get the global settings of the system.

Parameters:
	none - .

Returns:
	Hash ref -
		ssyncd, shows if ssyncd is enabled "true" or disabled "false"
		duplicated_network, shows if the system will duplicate a network segment for each interface "true" or it will be applied only once in the system "false"
		arp_announce, the system will send a arg packet to the net when it is set up or stood up, "true". The system will not notice anything to the net when it is set up or stood up, "false"
		proxy_new_generation, shows if zproxy is enabled "true" or pound is enabled "false"

=cut

sub getSystemGlobal
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $ssyncd_enabled = &getGlobalConfiguration( 'ssyncd_enabled' );
	my $duplicated_net = &getGlobalConfiguration( 'duplicated_net' );
	my $arp_announce   = &getGlobalConfiguration( 'arp_announce' );
	my $proxy          = &getGlobalConfiguration( 'proxy_ng' );

	my $out = {};
	$out->{ ssyncd }             = ( $ssyncd_enabled eq 'true' ) ? 'true' : 'false';
	$out->{ duplicated_network } = ( $duplicated_net eq 'true' ) ? 'true' : 'false';
	$out->{ arp_announce }       = ( $arp_announce eq 'true' )   ? 'true' : 'false';
	$out->{ proxy_new_generation } = ( $proxy eq 'true' ) ? 'true' : 'false';

	return $out;
}

=begin nd
Function: setSystemGlobal

	Set the global settings of the system.

Parameters:
	Hash -  Hash of global settings

Returns:
	Integer - Error code.  Returns: 0 on success,
					2 if there was an error related to stop http farms
					3 if there was an error setting up the global config
					4 if there was an error setting up the Farm config
					5 if there was an error related to start a stopped http farm


=cut

sub setSystemGlobal
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $global = shift;
	my $err    = 0;

	if ( exists $global->{ ssyncd } )
	{
		include 'Zevenet::Ssyncd';
		$err = &setSsyncd( $global->{ ssyncd } );
		if ( $err )
		{
			return $err;
		}
		else
		{
			require 'Zevenet::Cluster';
			( $global->{ ssyncd } eq 'true' )
			  ? &runZClusterRemoteManager( 'enable_ssyncd' )
			  : &runZClusterRemoteManager( 'disable_ssyncd' );
		}
	}

	if ( exists $global->{ duplicated_network } )
	{
		$err =
		  &setGlobalConfiguration( 'duplicated_net', $global->{ duplicated_network } );
		return $err if $err;
	}

	if ( exists $global->{ arp_announce } )
	{
		include 'Zevenet::Net::Util';
		$err =
		  ( $global->{ arp_announce } eq 'true' )
		  ? &setArpAnnounce()
		  : &unsetArpAnnounce();
		return $err if $err;
	}

	my $ng_cur = &getGlobalConfiguration( 'proxy_ng' );
	if ( exists $global->{ proxy_new_generation }
		 and ( $ng_cur ne $global->{ proxy_new_generation } ) )
	{
		require Zevenet::Farm::Core;
		require Zevenet::Farm::Base;
		require Zevenet::Farm::Action;
		require Zevenet::Farm::Config;

		$err = 0;
		my $base_cur          = &getGlobalConfiguration( 'base_proxy' );
		my $bin_cur           = &getGlobalConfiguration( 'proxy' );
		my $ctl_cur           = &getGlobalConfiguration( 'proxyctl' );
		my $ssyncd_base_cur   = &getGlobalConfiguration( 'base_ssyncd' );
		my $ssyncd_bin_cur    = &getGlobalConfiguration( 'ssyncd_bin' );
		my $ssyncdctl_bin_cur = &getGlobalConfiguration( 'ssyncdctl_bin' );
		my $ssyncd_enabled    = &getGlobalConfiguration( 'ssyncd_enabled' );

		# stop l7 farms
		my @farmsf = &getFarmsByType( 'http' );
		push @farmsf, &getFarmsByType( 'https' );
		my @farms_stopped;
		my @farms_config;

		foreach my $farmname ( @farmsf )
		{
			if ( &getFarmStatus( $farmname ) eq "up" )
			{
				$err = &runFarmStop( $farmname, "false" );
				if ( $err )
				{
					&zenlog( "There was an error stopping farm $farmname", "debug2", "lslb" );
					$err = 2;
					last;
				}
				else
				{
					&zenlog( "REN: Farm $farmname stopped", "", "" );
					push @farms_stopped, $farmname;
				}
			}
		}

		if ( ( !$err ) and ( $ssyncd_enabled eq "true" ) )
		{
			require Zevenet::Ssyncd;
			if ( &setSsyncdDisabled() )
			{
				&zenlog( "There was an error stopping Ssyncd", "debug2", "ssyncd" );
				$err = 3;
			}
			else
			{
				require Zevenet::Cluster;
				&runZClusterRemoteManager( 'disable_ssyncd' );
			}
		}

		if ( !$err )
		{
			if ( &setSsyncdNG( $global->{ proxy_new_generation } ) )
			{
				&zenlog(
						 "There was an error setting SsyncdNG ( "
						   . $global->{ proxy_new_generation }
						   . " ) binaries",
						 "debug2",
						 "System"
				);
				$err = 4;
			}
		}

		if ( !$err )
		{
			if ( &setProxyNG( $global->{ proxy_new_generation } ) )
			{
				&zenlog(
						 "There was an error setting ProxyNG ( "
						   . $global->{ proxy_new_generation }
						   . " ) binaries",
						 "debug2",
						 "System"
				);
				$err = 5;
			}
			else
			{
				( $global->{ proxy_new_generation } eq "true" )
				  ? &runZClusterRemoteManager( 'enable_proxyng' )
				  : &runZClusterRemoteManager( 'disable_proxyng' );
			}
		}

		if ( !$err )
		{
			# set farms config
			foreach my $farmname ( @farmsf )
			{
				if ( &setFarmProxyNGConf( $global->{ proxy_new_generation }, $farmname ) )
				{
					&zenlog( "There was an error setting Proxy Confguration in farm $farmname",
							 "debug2", "system" );
					foreach my $farmname ( @farms_config )
					{
						&zenlog( "Reverting proxyng conf ($ng_cur) in Farm $farmname ",
								 "debug2", "system" );
						&setFarmProxyNGConf( $ng_cur, $farmname );
					}
					$err = 6;
					last;
				}
				else
				{
					push @farms_config, $farmname;
				}
			}
		}

		if ( $err >= 4 )
		{
			if ( &setSsyncdNG( $ng_cur ) )
			{
				&zenlog( "Fatal Error: There was an error reverting Ssyncd binaries settings",
						 "debug2", "System" );
			}
		}

		if ( $err >= 5 )
		{
			if ( &setProxyNG( $ng_cur ) )
			{
				&zenlog( "Fatal Error: There was an error reverting Proxy binaries settings",
						 "debug2", "System" );
			}
		}

		# start l7 farms
		my $farm_err;
		foreach my $farmname ( @farms_stopped )
		{
			if ( &runFarmStart( $farmname, "false" ) )
			{
				&zenlog( "There was an error starting Farm $farmname", "debug2", "lslb" );
				$err = 7;
			}
		}

		if ( ( ( !$err ) or ( $err > 3 ) ) and ( $ssyncd_enabled eq "true" ) )
		{
			# Start Ssyncd
			my $node_role = &getZClusterNodeStatus();
			if ( $node_role eq 'master' )
			{
				if ( &setSsyncdMaster() )
				{
					&zenlog( "There was an error starting Ssyncd mode $node_role",
							 "debug2", "ssyncd" );
					$err = 8;
				}
			}
			elsif ( $node_role eq 'backup' )
			{
				if ( &setSsyncdBackup() )
				{
					&zenlog( "There was an error starting Ssyncd mode $node_role",
							 "debug2", "ssyncd" );
					$err = 8;
				}
			}
			&runZClusterRemoteManager( 'enable_ssyncd' );
		}

	}

	return $err;
}

=begin nd
Function: setProxyNG

	Set the ProxyNG settings of the system.

Parameters:
	arg - "true" to enable zproxy binaries, or "false" to enable pound binaries.

Returns:
	Integer - Error code. Returns: 0 on success, another value on failure.

=cut

sub setProxyNG    # ($ng)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $ng  = shift;
	my $err = 0;

	my $base = ( $ng eq 'true' ) ? 'base_zproxy' : 'base_pound';
	my $bin  = ( $ng eq 'true' ) ? 'zproxy'      : 'pound';
	my $ctl  = ( $ng eq 'true' ) ? 'zproxyctl'   : 'poundctl';
	$base = &getGlobalConfiguration( $base );
	$bin  = &getGlobalConfiguration( $bin );
	$ctl  = &getGlobalConfiguration( $ctl );

	# set binary
	$err += &setGlobalConfiguration( 'base_proxy', $base );
	$err += &setGlobalConfiguration( 'proxy',      $bin );
	$err += &setGlobalConfiguration( 'proxyctl',   $ctl );
	$err += &setGlobalConfiguration( 'proxy_ng',   $ng ) if ( !$err );

	return $err;
}

=begin nd
Function: setSsyncdNG

	Set the Ssysncd settings of the system.

Parameters:
	arg - "true" to enable Ssyncd zproxy binaries, or "false" to enable Ssyncd pound binaries.

Returns:
	Integer - Error code. Returns: 0 on success, another value on failure.

=cut

sub setSsyncdNG    # ($ng)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $ng  = shift;
	my $err = 0;

	my $ssyncd_base =
	  ( $ng eq 'true' ) ? 'base_ssyncd_zproxy' : 'base_ssyncd_pound';
	my $ssyncd_bin = ( $ng eq 'true' ) ? 'ssyncd_zproxy_bin' : 'ssyncd_pound_bin';
	my $ssyncdctl_bin =
	  ( $ng eq 'true' ) ? 'ssyncdctl_zproxy_bin' : 'ssyncdctl_pound_bin';
	$ssyncd_base   = &getGlobalConfiguration( $ssyncd_base );
	$ssyncd_bin    = &getGlobalConfiguration( $ssyncd_bin );
	$ssyncdctl_bin = &getGlobalConfiguration( $ssyncdctl_bin );

	# set binary
	$err += &setGlobalConfiguration( 'base_ssyncd',   $ssyncd_base );
	$err += &setGlobalConfiguration( 'ssyncd_bin',    "$ssyncd_bin" );
	$err += &setGlobalConfiguration( 'ssyncdctl_bin', "$ssyncdctl_bin" );

	return $err;
}

1;

