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

sub farms_name_datalink    # ( $farmname )
{
	my $farmname = shift;

	my @out_b;
	my $vip = &getFarmVip( "vip", $farmname );
	my $status = &getFarmStatus( $farmname );

	my $out_p = {
				  vip       => $vip,
				  algorithm => &getFarmAlgorithm( $farmname ),
				  status    => $status,
	};

########### backends
	my @run = &getFarmServers( $farmname );

	foreach my $l_servers ( @run )
	{
		my @l_serv = split ( ";", $l_servers );

		$l_serv[0] = $l_serv[0] + 0;
		$l_serv[3] = ( $l_serv[3] ) ? $l_serv[3] + 0 : undef;
		$l_serv[4] = ( $l_serv[4] ) ? $l_serv[4] + 0 : undef;
		$l_serv[5] = $l_serv[5] + 0;

		if ( $l_serv[1] ne "0.0.0.0" )
		{
			push @out_b,
			  {
				id        => $l_serv[0],
				ip        => $l_serv[1],
				interface => $l_serv[2],
				weight    => $l_serv[3],
				priority  => $l_serv[4]
			  };
		}
	}

	my $body = {
				 description => "List farm $farmname",
				 params      => $out_p,
				 backends    => \@out_b,
	};

	&httpResponse( { code => 200, body => $body } );
}

1;
