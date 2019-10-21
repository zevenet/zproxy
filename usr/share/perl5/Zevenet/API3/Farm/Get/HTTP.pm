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

include 'Zevenet::IPDS::Core';

# GET /farms/<farmname> Request info of a http|https Farm
sub farms_name_http    # ( $farmname )
{
	my $farmname = shift;

	my $output_params;
	my @out_s;
	my @out_cn;
	my $connto          = 0 + &getFarmConnTO( $farmname );
	my $timeout         = 0 + &getFarmTimeout( $farmname );
	my $alive           = 0 + &getFarmBlacklistTime( $farmname );
	my $client          = 0 + &getFarmClientTimeout( $farmname );
	my $conn_max        = 0 + &getFarmMaxConn( $farmname );
	my $rewritelocation = 0 + &getFarmRewriteL( $farmname );
	my $httpverb        = 0 + &getFarmHttpVerb( $farmname );

	if    ( $rewritelocation == 0 ) { $rewritelocation = "disabled"; }
	elsif ( $rewritelocation == 1 ) { $rewritelocation = "enabled"; }
	elsif ( $rewritelocation == 2 ) { $rewritelocation = "enabled-backends"; }

	if    ( $httpverb == 0 ) { $httpverb = "standardHTTP"; }
	elsif ( $httpverb == 1 ) { $httpverb = "extendedHTTP"; }
	elsif ( $httpverb == 2 ) { $httpverb = "standardWebDAV"; }
	elsif ( $httpverb == 3 ) { $httpverb = "MSextWebDAV"; }
	elsif ( $httpverb == 4 ) { $httpverb = "MSRPCext"; }
	elsif ( $httpverb == 5 ) { $httpverb = "OptionsHTTP"; }

	my $type    = &getFarmType( $farmname );
	my $cipher  = '';
	my $ciphers = 'all';
	my @cnames;

	if ( $type eq "https" )
	{
		require Zevenet::Farm::HTTP::HTTPS;
		include 'Zevenet::Farm::HTTP::HTTPS::Ext';

		@cnames = &getFarmCertificatesSNI( $farmname );
		my $elem = scalar @cnames;

		for ( my $i = 0 ; $i < $elem ; $i++ )
		{
			push @out_cn, { file => $cnames[$i], id => $i + 1 };
		}

		$cipher  = &getFarmCipherList( $farmname );
		$ciphers = &getFarmCipherSet( $farmname );
		chomp ( $ciphers );

		# adapt "ciphers" to required interface values
		if ( $ciphers eq "cipherglobal" )
		{
			$ciphers = "all";
		}
		elsif ( $ciphers eq "ciphercustom" )
		{
			$ciphers = "customsecurity";
		}
		elsif ( $ciphers eq "cipherpci" )
		{
			$ciphers = "highsecurity";
		}
	}

	my $vip = &getFarmVip( "vip", $farmname );
	my $vport = 0 + &getFarmVip( "vipp", $farmname );

	my $err414 = &getFarmErr( $farmname, "414" );
	my $err500 = &getFarmErr( $farmname, "500" );
	my $err501 = &getFarmErr( $farmname, "501" );
	my $err503 = &getFarmErr( $farmname, "503" );

	my $status = &getFarmStatus( $farmname );

	if ( $status eq 'up' && -e "/tmp/$farmname.lock" )
	{
		$status = "needed restart";
	}

	# my @certnames = &getFarmCertificatesSNI($farmname);
	# my $out_certs = [];
	# foreach $file(@certnames) {
	# push $out_certs, { filename => $file };
	# }

	$output_params = {
					   status          => $status,
					   restimeout      => $timeout,
					   contimeout      => $connto,
					   resurrectime    => $alive,
					   reqtimeout      => $client,
					   rewritelocation => $rewritelocation,
					   httpverb        => $httpverb,
					   listener        => $type,
					   vip             => $vip,
					   vport           => $vport,
					   error500        => $err500,
					   error414        => $err414,
					   error501        => $err501,
					   error503        => $err503
	};

	if ( $type eq "https" )
	{
		$output_params->{ certlist } = \@out_cn;
		$output_params->{ ciphers }  = $ciphers;
		$output_params->{ cipherc }  = $cipher;
	}

	#http services
	my $services = &getFarmVS( $farmname, "", "" );
	my @serv = split ( "\ ", $services );

	foreach my $s ( @serv )
	{
		my $serviceStruct = &getZapiHTTPServiceStruct( $farmname, $s );

		# Remove backend status 'undefined', it is for news api versions
		foreach my $be ( @{ $serviceStruct->{ 'backends' } } )
		{
			$be->{ 'status' } = 'up' if ( $be->{ 'status' } eq 'undefined' );
		}

		push @out_s, $serviceStruct;
	}
	include 'Zevenet::IPDS';
	my $ipds = &getIPDSfarmsRules_zapiv3( $farmname );

	# Success
	my $body = {
				 description => "List farm $farmname",
				 params      => $output_params,
				 services    => \@out_s,
				 ipds        => $ipds,
	};

	&httpResponse( { code => 200, body => $body } );
}

# Get all IPDS rules applied to a farm
sub getIPDSfarmsRules_zapiv3
{
	my $farmName = shift;

	require Config::Tiny;

	my $rules;
	my $fileHandle;
	my @dosRules        = ();
	my @blacklistsRules = ();
	my @rblRules        = ();

	my $dosConf        = &getGlobalConfiguration( 'dosConf' );
	my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
	my $rblPath        = &getGlobalConfiguration( 'configdir' ) . "/ipds/rbl";
	my $rblConf        = "$rblPath/rbl.conf";

	if ( -e $dosConf )
	{
		$fileHandle = Config::Tiny->read( $dosConf );
		foreach my $key ( keys %{ $fileHandle } )
		{
			if ( defined $fileHandle->{ $key }->{ 'farms' }
				 && $fileHandle->{ $key }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
			{
				push @dosRules, $key;
			}
		}
	}

	if ( -e $blacklistsConf )
	{
		$fileHandle = Config::Tiny->read( $blacklistsConf );
		foreach my $key ( keys %{ $fileHandle } )
		{
			if ( defined $fileHandle->{ $key }->{ 'farms' }
				 && $fileHandle->{ $key }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
			{
				push @blacklistsRules, $key;
			}
		}
	}

	if ( -e $rblConf )
	{
		$fileHandle = Config::Tiny->read( $rblConf );
		foreach my $key ( keys %{ $fileHandle } )
		{
			if ( defined $fileHandle->{ $key }->{ 'farms' }
				 && $fileHandle->{ $key }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
			{
				push @rblRules, $key;
			}
		}
	}

	$rules =
	  { dos => \@dosRules, blacklists => \@blacklistsRules, rbl => \@rblRules };
	return $rules;
}

sub getZapiHTTPServiceStruct
{
	my ( $farmname, $service_name ) = @_;

	require Zevenet::FarmGuardian;
	require Zevenet::Farm::HTTP::Backend;

	my $service_ref = -1;

	# http services
	my $services = &getHTTPFarmVS( $farmname, "", "" );
	my @serv = split ( ' ', $services );

	# return error if service is not found
	return $service_ref unless grep ( { $service_name eq $_ } @serv );

	my $vser         = &getHTTPFarmVS( $farmname, $service_name, "vs" );
	my $urlp         = &getHTTPFarmVS( $farmname, $service_name, "urlp" );
	my $redirect     = &getHTTPFarmVS( $farmname, $service_name, "redirect" );
	my $redirecttype = &getHTTPFarmVS( $farmname, $service_name, "redirecttype" );
	my $session      = &getHTTPFarmVS( $farmname, $service_name, "sesstype" );
	my $ttl          = &getHTTPFarmVS( $farmname, $service_name, "ttl" );
	my $sesid        = &getHTTPFarmVS( $farmname, $service_name, "sessionid" );
	my $dyns         = &getHTTPFarmVS( $farmname, $service_name, "dynscale" );
	my $httpsbe      = &getHTTPFarmVS( $farmname, $service_name, "httpsbackend" );

	if ( $dyns =~ /^$/ )
	{
		$dyns = "false";
	}
	if ( $httpsbe =~ /^$/ )
	{
		$httpsbe = "false";
	}

	my @fgconfig  = &getFarmGuardianConf( $farmname, $service_name );
	my $fgttcheck = $fgconfig[1] + 0;
	my $fgscript  = $fgconfig[2];
	my $fguse     = $fgconfig[3];
	my $fglog     = $fgconfig[4];

	# Default values for farm guardian parameters
	if ( !$fgttcheck ) { $fgttcheck = 5; }
	if ( !$fguse )     { $fguse     = "false"; }
	if ( !$fglog )     { $fglog     = "false"; }
	if ( !$fgscript )  { $fgscript  = ""; }

	$fgscript =~ s/\n//g;
	$fguse =~ s/\n//g;

	my $backends = &getHTTPFarmBackends( $farmname, $service_name );

	$ttl       = 0 unless $ttl;
	$fgttcheck = 0 unless $fgttcheck;

	$service_ref = {
					 id           => $service_name,
					 vhost        => $vser,
					 urlp         => $urlp,
					 redirect     => $redirect,
					 redirecttype => $redirecttype,
					 persistence  => $session,
					 ttl          => $ttl + 0,
					 sessionid    => $sesid,
					 leastresp    => $dyns,
					 httpsb       => $httpsbe,
					 backends     => $backends,
					 fgtimecheck  => $fgttcheck,
					 fgenabled    => $fguse,
					 fglog        => $fglog,
					 fgscript     => $fgscript,
	};

	include 'Zevenet::Farm::HTTP::Service::Ext';
	&add_service_cookie_insertion( $farmname, $service_ref );

	return $service_ref;
}

1;
