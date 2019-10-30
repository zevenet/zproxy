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
use Config::Tiny;

#~ ipds		rbl
#~ domains
#~ waf		ruleset
#~ *files

my $FIN = undef;

sub getIdsTree
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	require Zevenet::Farm::Core;
	require Zevenet::FarmGuardian;
	require Zevenet::Net::Interface;
	require Zevenet::Certificate;
	require Zevenet::Backup;
	require Zevenet::System::Log;
	include 'Zevenet::RBAC::User::Core';
	include 'Zevenet::RBAC::Group::Core';
	include 'Zevenet::RBAC::Role::Config';
	include 'Zevenet::Alias';
	include 'Zevenet::IPDS::WAF::Core';

	my $tree = $FIN;

	$tree->{ 'farms' } = $FIN;
	foreach my $type ( 'https', 'http', 'l4xnat', 'gslb', 'datalink' )
	{
		my @farms = &getFarmsByType( $type );

		# add farm
		foreach my $f ( @farms )
		{
			require Zevenet::Farm::Service;
			$tree->{ 'farms' }->{ $f }->{ 'services' } = $FIN;

			# add srv
			my @srv = ( $type =~ /http|gslb/ ) ? &getFarmServices( $f ) : ( '_' );
			foreach my $s ( @srv )
			{
				require Zevenet::Farm::Backend;

				$tree->{ 'farms' }->{ $f }->{ 'services' }->{ $s }->{ 'backends' } = $FIN;

				# add bk
				my $bks = &getFarmServers( $f, $s );

				foreach my $b ( @{ $bks } )
				{
					$tree->{ 'farms' }->{ $f }->{ 'services' }->{ $s }->{ 'backends' }
					  ->{ $b->{ 'id' } } = $FIN;
				}

				my $fg = &getFGFarm( $f, $s );
				$tree->{ 'farms' }->{ $f }->{ 'services' }->{ $s }->{ 'fg' }->{ $fg } = $FIN
				  if ( $fg ne '' );
			}

			# add certificates
			if ( $type =~ /http/ )
			{

				include 'Zevenet::Farm::HTTP::HTTPS::Ext';
				my @certs = &getFarmCertificatesSNI( $f );
				$tree->{ 'farms' }->{ $f }->{ 'certificates' } = &addIdsArrays( \@certs );
			}

			# add zones
			if ( $type eq 'gslb' )
			{
				include 'Zevenet::Farm::GSLB::Zone';
				my @zones = &getGSLBFarmZones( $f );
				$tree->{ 'farms' }->{ $f }->{ 'zones' } = &addIdsArrays( \@zones );
			}

			# add bl
			include 'Zevenet::IPDS::Blacklist::Core';
			my @bl = &listBLByFarm( $f );
			$tree->{ 'farms' }->{ $f }->{ 'ipds' }->{ 'blacklists' } =
			  &addIdsArrays( \@bl );

			# add dos
			include 'Zevenet::IPDS::DoS::Core';
			my @dos = &listDOSByFarm( $f );
			$tree->{ 'farms' }->{ $f }->{ 'ipds' }->{ 'dos' } = &addIdsArrays( \@dos );

			# add rbl
			include 'Zevenet::IPDS::RBL::Core';
			my @rbl = &listRBLByFarm( $f );
			$tree->{ 'farms' }->{ $f }->{ 'ipds' }->{ 'blacklists' } =
			  &addIdsArrays( \@rbl );

			#add waf
			if ( $type =~ /http/ )
			{
				include 'Zevenet::IPDS::WAF::Core';
				my @waf = &listWAFByFarm( $f );
				$tree->{ 'farms' }->{ $f }->{ 'ipds' }->{ 'waf' } = &addIdsArrays( \@waf );
			}
		}
	}

	# add fg
	my @fg = &getFGList();
	$tree->{ 'farmguardians' } = &addIdsArrays( \@fg );

	# add ssl certs
	my @certs = &getCertFiles();
	$tree->{ 'certificates' } = &addIdsArrays( \@certs );

	# add interfaces
	foreach my $type ( 'nic', 'bond', 'vlan', 'virtual' )
	{
		my $if_key = ( $type eq 'bond' ) ? 'bonding' : $type;
		$tree->{ 'interfaces' }->{ $if_key } = $FIN;

		my @list = &getInterfaceTypeList( $type );
		foreach my $if ( @list )
		{
			$tree->{ 'interfaces' }->{ $if_key }->{ $if->{ name } } = $FIN;
		}
	}

	# ipds
	my $fileHandle;
	my $dosConf        = &getGlobalConfiguration( 'dosConf' );
	my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
	my $rblPath        = &getGlobalConfiguration( 'configdir' ) . "/ipds/rbl";
	my $rblConf        = "$rblPath/rbl.conf";

	my @bl  = ();
	my @dos = ();
	my @rbl = ();
	my @waf = sort &listWAFSet();

	if ( -e $dosConf )
	{
		$fileHandle = Config::Tiny->read( $dosConf );
		@dos        = sort keys %{ $fileHandle };
	}

	if ( -e $blacklistsConf )
	{
		$fileHandle = Config::Tiny->read( $blacklistsConf );
		@bl         = sort keys %{ $fileHandle };
	}

	if ( -e $rblConf )
	{
		$fileHandle = Config::Tiny->read( $rblConf );
		@rbl        = sort keys %{ $fileHandle };
	}

	$tree->{ 'ipds' }->{ 'blacklists' } = &addIdsArrays( \@bl );
	$tree->{ 'ipds' }->{ 'dos' }        = &addIdsArrays( \@dos );
	$tree->{ 'ipds' }->{ 'rbl' }        = &addIdsArrays( \@rbl );
	$tree->{ 'ipds' }->{ 'waf' }        = &addIdsArrays( \@waf );

	# add rbac
	my @users  = &getRBACUserList();
	my @groups = &getRBACGroupList();
	my @roles  = &getRBACRolesList();
	$tree->{ 'rbac' }->{ 'users' }  = &addIdsArrays( \@users );
	$tree->{ 'rbac' }->{ 'groups' } = &addIdsArrays( \@groups );
	$tree->{ 'rbac' }->{ 'roles' }  = &addIdsArrays( \@roles );

	# add aliases
	my $alias_bck_ref = &getAlias( 'backend' );
	my $alias_if_ref  = &getAlias( 'interface' );
	$tree->{ 'aliases' }->{ 'backends' }   = &addIdsKeys( $alias_bck_ref );
	$tree->{ 'aliases' }->{ 'interfaces' } = &addIdsKeys( $alias_if_ref );

	# add backups
	my $backups = &getBackup();
	$tree->{ 'backups' } = &addIdsArrays( $backups );

	# add logs
	my $logs = &getLogs();
	$tree->{ 'logs' } = $FIN;
	foreach my $l ( @{ $logs } )
	{
		$tree->{ 'logs' }->{ $l->{ file } } = $FIN;
	}

	return $tree;
}

sub addIdsKeys
{
	my $hash_ref = shift;
	my @arr_keys = keys %{ $hash_ref };
	return &addIdsArrays( \@arr_keys );
}

sub addIdsArrays
{
	my $arr = shift;
	my $out = {};

	foreach my $it ( @{ $arr } )
	{
		$out->{ $it } = $FIN;
	}

	return ( !keys %{ $out } ) ? undef : $out;
}

1;
