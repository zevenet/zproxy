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

use Zevenet::Core;
require Zevenet::Farm::Base;
require Zevenet::Net::ConnStats;

=begin nd
Function: getGSLBGdnsdStats

	Get gslb farm stats from a local socket enabled by gdnsd service

Parameters:
	farmname - Farm name

Returns:
	String - Return a string with json format
=cut

sub getGSLBGdnsdStats    # &getGSLBGdnsdStats ( )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmName = shift;

	include 'Zevenet::Farm::GSLB::Config';

	my $wget       = &getGlobalConfiguration( 'wget' );
	my $httpPort   = &getGSLBControlPort( $farmName );
	my $gdnsdStats = &logAndGet( "$wget -qO- http://127.0.0.1:$httpPort/json" );
	my $stats;

	if ( $gdnsdStats )
	{
		require JSON::XS;
		$stats = JSON::XS::decode_json( $gdnsdStats );
	}

	return $stats;
}

=begin nd
Function: getGSLBFarmEstConns

	Get total established connections in a gslb farm

Parameters:
	farmname - Farm name
	netstat - reference to array with Conntrack -L output

Returns:
	array - Return all ESTABLISHED conntrack lines for a farm

FIXME:
	change to monitoring libs
=cut

sub getGSLBFarmEstConns    # ($farm_name,$netstat)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $netstat ) = @_;

	my $vip      = &getFarmVip( "vip",  $farm_name );
	my $vip_port = &getFarmVip( "vipp", $farm_name );

	return
	  scalar @{
		&getNetstatFilter( "udp", "",
						   "src=.* dst=$vip sport=.* dport=$vip_port .*src=.*",
						   "", $netstat )
	  };
}

sub getGSLBFarmBackendsStats
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farmname ) = @_;

	require Zevenet::Farm::Config;
	include 'Zevenet::Farm::GSLB::Service';

	my $out_rss;
	my $gslb_stats = &getGSLBGdnsdStats( $farmname );
	my @services   = &getGSLBFarmServices( $farmname );

	# alias
	include 'Zevenet::RBAC::Core';
	include 'Zevenet::Alias';
	my $permission = &getRBACRolePermission( 'alias', 'list' );
	my $alias = &getAlias( 'backend' );

	foreach my $srv ( @services )
	{
		# Default port health check
		my $port       = &getFarmVS( $farmname, $srv, "dpc" );
		my $lb         = &getFarmVS( $farmname, $srv, "algorithm" );
		my $backendsvs = &getFarmVS( $farmname, $srv, "backends" );
		my @be = split ( "\n", $backendsvs );
		my $out_b = [];

		foreach my $subline ( @be )
		{
			$subline =~ s/^\s+//;

			if ( $subline =~ /^$/ )
			{
				next;
			}

			# ID and IP
			my @subbe  = split ( " => ", $subline );
			my $id     = $subbe[0];
			my $addr   = $subbe[1];
			my $status = "undefined";

			# look for backend status in stats
			foreach my $st_srv ( @{ $gslb_stats->{ 'services' } } )
			{
				if ( $st_srv->{ 'service' } =~ /^$addr\/[\w\-]+$port$/ )
				{
					$status = $st_srv->{ 'real_state' };
					last;
				}
			}

			$id =~ s/^primary$/1/;
			$id =~ s/^secondary$/2/;
			$status = lc $status if defined $status;

			push (
				   @{ $gslb_stats->{ 'backends' } },
				   {
					  alias => ( $permission ) ? $alias->{ $addr } : undef,
					  id    => $id + 0,
					  ip    => $addr,
					  service => $srv,
					  port    => $port + 0,
					  status  => $status,
				   }
			);
		}
	}

	return $gslb_stats;
}

sub getGSLBFarmStats    # ($farm_name,$netstat)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name ) = @_;

	include 'Zevenet::Farm::GSLB::Config';

	my $vip = &getGSLBFarmVip( "vip", $farm_name );
	my $netstat = &getConntrack( "", $vip, "", "", "" );

	# ESTABLISHED connections
	my $est_conns = &getGSLBFarmEstConns( $farm_name, $netstat );

	return {
			 syn => 0,
			 est => $est_conns,
	};
}

1;
