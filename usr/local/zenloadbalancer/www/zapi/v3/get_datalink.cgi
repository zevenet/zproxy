#! /usr/bin/perl -w

##############################################################################
#
#     This file is part of the Zen Load Balancer Enterprise Edition software
#     package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This file cannot be distributed, released in public domain and/or for
#     commercial purposes.
#
###############################################################################

use warnings;
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
