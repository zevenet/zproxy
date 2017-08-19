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

# GET /farms/GSLBFARM
sub farms_gslb # ()
{
	my @out;
	my @files = &getFarmList();

	foreach my $file ( @files )
	{
		my $name   = &getFarmName( $file );
		my $type   = &getFarmType( $name );
		next unless $type eq 'gslb';
		my $status = &getFarmStatus( $name );
		my $vip    = &getFarmVip( 'vip', $name );
		my $port   = &getFarmVip( 'vipp', $name );

		$status = "needed restart" if $status eq 'up' && ! &getFarmLock($name);

		push @out,
		  {
			farmname => $name,
			#~ profile  => $type,
			status   => $status,
			vip      => $vip,
			vport    => $port
		  };
	}

	my $body = {
				description => "List GSLB farms",
				params      => \@out,
	};

	&httpResponse({ code => 200, body => $body });
}

1;
