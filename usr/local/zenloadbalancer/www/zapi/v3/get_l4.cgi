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


########### GET L4XNAT
# GET /farms/<farmname> Request info of a l4xnat Farm

use warnings;
use strict;

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
	
	############ FG
	my @fgconfig    = &getFarmGuardianConf( $farmname, "" );
	my $fguse       = $fgconfig[3];
	my $fgcommand   = $fgconfig[2];
	my $fgtimecheck = $fgconfig[1];
	my $fglog       = $fgconfig[4];
	
	if ( !$fgtimecheck ) { $fgtimecheck = 5; }
    if ( !$fguse ) { $fguse = "false"; }
    if ( !$fglog  ) { $fglog = "false"; }
    if ( !$fgcommand ) { $fgcommand = ""; }

	my $status = &getFarmStatus( $farmname );

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
			   fgenabled   => $fguse,
			   fgtimecheck => $fgtimecheck + 0,
			   fgscript    => $fgcommand,
			   fglog       => $fglog,
			   listener    => 'l4xnat',
	};

	########### backends
	my @run = &getFarmServers( $farmname );

	foreach my $l_servers ( @run )
	{
		my @l_serv = split ( ";", $l_servers );

		$l_serv[0] = $l_serv[0] + 0;

		&zenlog( Dumper $l_serv[2] );

		if ( !$l_serv[2] =~ /^$/ )
		{
			$l_serv[2] = $l_serv[2] + 0;
		}

		&zenlog( Dumper $l_serv[2] );

		$l_serv[3] = $l_serv[3] + 0;
		$l_serv[2] = $l_serv[2]? $l_serv[2]+0: undef;
		$l_serv[4] = $l_serv[4]? $l_serv[4]+0: undef;
		$l_serv[5] = $l_serv[5]? $l_serv[5]+0: undef;
		$l_serv[2] = undef if $l_serv[2] eq '';
		chomp $l_serv[6];

		push @out_b,
		  {
			id       => $l_serv[0],
			ip       => $l_serv[1],
			port     => $l_serv[2],
			weight   => $l_serv[4],
			priority => $l_serv[5],
			status   => $l_serv[6],
		  };
	}
	my $ipds = &getIPDSfarmsRules( $farmname );

	my $body = {
				 description => "List farm $farmname",
				 params      => $out_p,
				 backends   => \@out_b,
				 ipds 			=>  $ipds,
	};

	&httpResponse({ code => 200, body => $body });
}

1;
