#!/usr/bin/perl -w

#~ use no warnings;
use warnings;
use strict;



############ GET HTTP/S
# curl --tlsv1 -k --header 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/newfarmHTTP
#
#
#####Documentation of GET HTTP or HTTPS####
#**
#  @api {get} /farms/<farmname> Request info of a http|https Farm
#  @apiGroup Farm Get
#  @apiName GetFarmNameHTTP
#  @apiDescription Get the Params of a given Farm <farmname> with HTTP or HTTPS profile
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "List farm FarmHTTP",
#   "params" : [
#      {
#         "certlist" : [
#            {
#               "file" : "example.pem",
#               "id" : 1
#            },
#            {
#               "file" : "zencert.pem",
#               "id" : 2
#            }
#         ],
#         "cipherc" : "ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+3DES:!aNULL:!MD5:!DSS:!SSLv3",
#         "ciphers" : "customsecurity",
#         "contimeout" : 30,
#         "error414" : "Message error 414",
#         "error500" : "Message error 500",
#         "error501" : "Message error 501",
#         "error503" : "Message error 503",
#         "httpverb" : "extendedHTTP",
#         "listener" : "https",
#         "maxthreads" : 50,
#         "reqtimeout" : 50,
#         "restimeout" : 50,
#         "resurrectime" : 12,
#         "rewritelocation" : "disabled",
#         "status" : "needed restart",
#         "vip" : "178.62.126.152",
#         "vport" : 89
#      }
#   ],
#   "services" : [
#      {
#         "backends" : [
#            {
#               "backendstatus" : "up"
#               "id" : 0,
#               "ip" : "192.168.0.11",
#               "port" : 88,
#               "timeout" : 13,
#               "weight" : 4
#            },
#            {
#               "backendstatus" : "maintenance"
#               "id" : 1,
#               "ip" : "192.168.0.10",
#               "port" : 88,
#               "timeout" : 12,
#               "weight" : 1
#            }
#         ],
#		  "cookiedomain" : "domainname.com",
#         "cookieinsert" : "true",
#         "cookiename" : "ZENSESSIONID",
#         "cookiepath" : "/",
#         "cookiettl" : 10,
#         "fgenabled" : "true",
#         "fglog" : "true",
#         "fgscript" : "farm guardian command",
#         "fgtimecheck" : "5",
#         "httpsb" : "false",
#         "id" : "sev2",
#         "leastresp" : "false",
#         "persistence" : "URL",
#         "redirect" : "http://zenloadbalancer.com",
#		  "redirecttype" : "append",
#         "sessionid" : "sid",
#         "ttl" : 125,
#         "urlp" : "^/myapp1$",
#         "vhost" : "www.mywebserver.com"
#      }
#   ]
#}
#
#
#@apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#         https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmHTTP
#
#@apiSampleRequest off
#
#**

sub farms_name_http # ( $farmname )
{
	my $farmname = shift;

	my $output_params;
	my @out_s;
	my @out_cn;
	my $connto          = &getFarmConnTO( $farmname );
	$connto          = $connto + 0;
	my $timeout         = &getFarmTimeout( $farmname );
	$timeout         = $timeout + 0;
	my $alive           = &getFarmBlacklistTime( $farmname );
	$alive           = $alive + 0;
	my $client          = &getFarmClientTimeout( $farmname );
	$client          = $client + 0;
	my $conn_max        = &getFarmMaxConn( $farmname );
	$conn_max        = $conn_max + 0;
	my $rewritelocation = &getFarmRewriteL( $farmname );
	$rewritelocation = $rewritelocation + 0;

	if ( $rewritelocation == 0 )
	{
		$rewritelocation = "disabled";
	}
	elsif ( $rewritelocation == 1 )
	{
		$rewritelocation = "enabled";
	}
	elsif ( $rewritelocation == 2 )
	{
		$rewritelocation = "enabled-backends";
	}

	my $httpverb = &getFarmHttpVerb( $farmname );
	$httpverb = $httpverb + 0;

	if ( $httpverb == 0 )
	{
		$httpverb = "standardHTTP";
	}
	elsif ( $httpverb == 1 )
	{
		$httpverb = "extendedHTTP";
	}
	elsif ( $httpverb == 2 )
	{
		$httpverb = "standardWebDAV";
	}
	elsif ( $httpverb == 3 )
	{
		$httpverb = "MSextWebDAV";
	}
	elsif ( $httpverb == 4 )
	{
		$httpverb = "MSRPCext";
	}

	my $type     = &getFarmType( $farmname );
	my $certname;
	my $cipher   = '';
	my $ciphers  = 'all';
	my @cnames;

	if ( $type eq "https" )
	{
		$certname = &getFarmCertificate( $farmname );
		@cnames   = &getFarmCertificatesSNI( $farmname );
		my $elem     = scalar @cnames;

		for ( my $i = 0 ; $i < $elem ; $i++ )
		{
			push @out_cn, { file => $cnames[$i], id => $i + 1 };
		}

		$cipher  = &getFarmCipherList( $farmname );
		$ciphers = &getFarmCipherSet( $farmname );
		chomp ( $ciphers );

		if ( $ciphers eq "cipherglobal" )
		{
			$ciphers = "all";
		}
	}

	my $vip   = &getFarmVip( "vip",  $farmname );
	my $vport = &getFarmVip( "vipp", $farmname );
	$vport = $vport + 0;

	my @err414 = &getFarmErr( $farmname, "414" );
	chomp(@err414);
	my @err500 = &getFarmErr( $farmname, "500" );
	chomp(@err500);
	my @err501 = &getFarmErr( $farmname, "501" );
	chomp(@err501);
	my @err503 = &getFarmErr( $farmname, "503" );
	chomp(@err503);

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
		error500        => @err500,
		error414        => @err414,
		error501        => @err501,
		error503        => @err503
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
		my $vser         = &getFarmVS( $farmname, $s, "vs" );
		my $urlp         = &getFarmVS( $farmname, $s, "urlp" );
		my $redirect     = &getFarmVS( $farmname, $s, "redirect" );
		my $redirecttype = &getFarmVS( $farmname, $s, "redirecttype" );
		my $session      = &getFarmVS( $farmname, $s, "sesstype" );
		my $ttl          = &getFarmVS( $farmname, $s, "ttl" );
		my $sesid        = &getFarmVS( $farmname, $s, "sessionid" );
		my $dyns         = &getFarmVS( $farmname, $s, "dynscale" );
		my $httpsbe      = &getFarmVS( $farmname, $s, "httpsbackend" );
		my $cookiei      = &getFarmVS( $farmname, $s, "cookieins" );

		if ( $cookiei eq "" )
		{
			$cookiei = "false";
		}

		my $cookieinsname = &getFarmVS( $farmname, $s, "cookieins-name" );
		my $domainname    = &getFarmVS( $farmname, $s, "cookieins-domain" );
		my $path          = &getFarmVS( $farmname, $s, "cookieins-path" );
		my $ttlc          = &getFarmVS( $farmname, $s, "cookieins-ttlc" );

		if ( $dyns =~ /^$/ )
		{
			$dyns = "false";
		}
		if ( $httpsbe =~ /^$/ )
		{
			$httpsbe = "false";
		}

		my @fgconfig  = &getFarmGuardianConf( $farmname, $s );
		my $fgttcheck = $fgconfig[1];
		my $fgscript  = $fgconfig[2];
		$fgscript =~ s/\n//g;
		$fgscript =~ s/\"/\'/g;
		my $fguse = $fgconfig[3];
		$fguse =~ s/\n//g;
		my $fglog      = $fgconfig[4];

		# Default values for farm guardian parameters
		if ( !$fgttcheck ) { $fgttcheck = 5; }
        if ( !$fguse ) { $fguse = "false"; }
        if ( !$fglog  ) { $fglog = "false"; }
        if ( !$fgscript ) { $fgscript = ""; }

		my @out_ba;
		my $backendsvs = &getFarmVS( $farmname, $s, "backends" );
		my @be         = split ( "\n", $backendsvs );

		foreach my $subl ( @be )
		{
			my @subbe       = split ( "\ ", $subl );
			my $id          = $subbe[1] + 0;
			my $maintenance = &getFarmBackendMaintenance( $farmname, $id, $s );

			my $backendstatus;
			if ( $maintenance != 0 )
			{
				$backendstatus = "up";
			}
			else
			{
				$backendstatus = "maintenance";
			}

			my $ip   = $subbe[3];
			my $port = $subbe[5] + 0;
			my $tout = $subbe[7];
			my $prio = $subbe[9];

			$tout = $tout eq '-' ? undef: $tout+0;
			$prio = $prio eq '-' ? undef: $prio+0;

			push @out_ba,
			  {
				id      => $id,
				status  => $backendstatus,
				ip      => $ip,
				port    => $port,
				timeout => $tout,
				weight  => $prio
			  };
		}

		push @out_s,
		  {
			id           => $s,
			vhost        => $vser,
			urlp         => $urlp,
			redirect     => $redirect,
			redirecttype => $redirecttype,
			cookieinsert => $cookiei,
			cookiename   => $cookieinsname,
			cookiedomain => $domainname,
			cookiepath   => $path,
			cookiettl    => $ttlc + 0,
			persistence  => $session,
			ttl          => $ttl + 0,
			sessionid    => $sesid,
			leastresp    => $dyns,
			httpsb       => $httpsbe,
			fgtimecheck  => $fgttcheck + 0,
			fgscript     => $fgscript,
			fgenabled    => $fguse,
			fglog        => $fglog,
			backends     => \@out_ba,
		  };
	}
	my $ipds = &getIPDSfarmsRules( $farmname );

	# Success
	my $body = {
				 description => "List farm $farmname",
				 params      => $output_params,
				 services    	=> \@out_s,
				 ipds			=> $ipds,
	};

	&httpResponse({ code => 200, body => $body });
}

1;
