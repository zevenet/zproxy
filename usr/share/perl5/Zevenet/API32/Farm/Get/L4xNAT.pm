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
use Zevenet::FarmGuardian;
use Zevenet::Farm::Config;
use Zevenet::Farm::L4xNAT::Backend;

my $eload;
if ( eval { require Zevenet::ELoad; } ) { $eload = 1; }

# GET /farms/<farmname> Request info of a l4xnat Farm
sub farms_name_l4 # ( $farmname )
{
	my $farmname = shift;

	my $out_p;
	my @out_b;

	my $vip   = &getFarmVip( "vip",  $farmname );
	my $vport = &getFarmVip( "vipp", $farmname );

	if ( $vport =~ /^\d+$/ )
	{
		$vport = $vport + 0;
	}

	my @ttl = &getFarmMaxClientTime( $farmname, "" );
	my $timetolimit = $ttl[0] + 0;

	my $status = &getFarmVipStatus( $farmname );

	my $persistence = &getFarmPersistence( $farmname );
	$persistence = "" if $persistence eq 'none';

	$out_p = {
			   status      => $status,
			   vip         => $vip,
			   vport       => $vport,
			   algorithm   => &getFarmAlgorithm( $farmname ),
			   nattype     => &getFarmNatType( $farmname ),
			   persistence => $persistence,
			   protocol    => &getFarmProto( $farmname ),
			   ttl         => $timetolimit,
			   farmguardian => &getFGFarm( $farmname ),
			   listener    => 'l4xnat',
	};

	# Backends
	@out_b = &getL4FarmBackends( $farmname );

	my $body = {
				 description => "List farm $farmname",
				 params      => $out_p,
				 backends    => \@out_b,
	};

	$body->{ ipds } = &eload(
			module => 'Zevenet::IPDS::Core',
			func   => 'getIPDSfarmsRules',
			args   => [$farmname],
	) if ( $eload );

	&httpResponse({ code => 200, body => $body });
}

1;
