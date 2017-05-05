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

############ GET HTTP/S
# curl --tlsv1 -k --header 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/newfarmHTTP
#
#
#####Documentation of GET HTTP or HTTPS####
#**
#  @api {get} /farms/<farmname> Request info of a http|https Farm
#  @apiGroup Farm Get
#  @apiName GetFarmNameHTTP
#  @apiDescription Get the Params of a given Farm <farmname> with HTTP or HTTPS profile
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiVersion 2.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "List farm FarmHTTP",
#   "params" : [
#      {
#         "certlist" : [
#            {
#               "certname" : "example.pem",
#               "id" : 1
#            },
#            {
#               "certname" : "zencert.pem",
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
#       -u zapi:<password>  https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/FarmHTTP
#
#@apiSampleRequest off
#
#**

our $origin;
if ( $origin ne 1 )
{
	exit;
}

sub farms_name_http()
{

	use CGI;
	my $q = CGI->new;

	my $out_p  = [];
	my $out_b  = [];
	my $out_s  = [];
	my $out_cn = [];
##
	$farmname        = $1;
	$connto          = &getFarmConnTO( $farmname );
	$connto          = $connto + 0;
	$timeout         = &getFarmTimeout( $farmname );
	$timeout         = $timeout + 0;
	$alive           = &getFarmBlacklistTime( $farmname );
	$alive           = $alive + 0;
	$client          = &getFarmClientTimeout( $farmname );
	$client          = $client + 0;
	$conn_max        = &getFarmMaxConn( $farmname );
	$conn_max        = $conn_max + 0;
	$rewritelocation = &getFarmRewriteL( $farmname );
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
	$httpverb = &getFarmHttpVerb( $farmname );
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
	$type     = &getFarmType( $farmname );
	$certname = $na;
	$cipher   = $na;
	$ciphers  = $na;

	if ( $type eq "https" )
	{
		##
		$certname = &getFarmCertificate( $farmname );
		@cnames   = &getFarmCertificatesSNI( $farmname );
		$elem     = @cnames;
		for ( $i = 0 ; $i < $elem ; $i++ )
		{
			push $out_cn, { certname => $cnames[$i], id => $i + 1 };
		}
		$cipher  = &getFarmCipherList( $farmname );
		$ciphers = &getFarmCipherSet( $farmname );
		chomp ( $ciphers );
		if ( $ciphers eq "cipherglobal" )
		{
			$ciphers = "all";
		}
	}

	$vip   = &getFarmVip( "vip",  $farmname );
	$vport = &getFarmVip( "vipp", $farmname );
	$vport = $vport + 0;

	@err414 = &getFarmErr( $farmname, "414" );
	chomp(@err414);
	@err500 = &getFarmErr( $farmname, "500" );
	chomp(@err500);
	@err501 = &getFarmErr( $farmname, "501" );
	chomp(@err501);
	@err503 = &getFarmErr( $farmname, "503" );
	chomp(@err503);


	if ( -e "/tmp/$farmname.lock" )
	{
		$status = "needed restart";
	}
	else
	{
		$status = "ok";
	}

	# my @certnames = &getFarmCertificatesSNI($farmname);
	# my $out_certs = [];
	# foreach $file(@certnames) {
	# push $out_certs, { filename => $file };
	# }

	push $out_p,
	  {
		certlist        => $out_cn,
		status          => $status,
		restimeout      => $timeout,
		contimeout      => $connto,
		resurrectime    => $alive,
		reqtimeout      => $client,
		maxthreads      => $conn_max,
		rewritelocation => $rewritelocation,
		httpverb        => $httpverb,
		listener        => $type,
		ciphers         => $ciphers,
		cipherc         => $cipher,
		vip             => $vip,
		vport           => $vport,
		error500        => @err500,
		error414        => @err414,
		error501        => @err501,
		error503        => @err503
	  };

	#http services
	my $services = &getFarmVS( $farmname, "", "" );
	my @serv = split ( "\ ", $services );
	foreach $s ( @serv )
	{
		$vser         = &getFarmVS( $farmname, $s, "vs" );
		$urlp         = &getFarmVS( $farmname, $s, "urlp" );
		$redirect     = &getFarmVS( $farmname, $s, "redirect" );
		$redirecttype = &getFarmVS( $farmname, $s, "redirecttype" );
		$session      = &getFarmVS( $farmname, $s, "sesstype" );
		$ttl          = &getFarmVS( $farmname, $s, "ttl" );
		$ttl          = $ttl + 0;
		$sesid        = &getFarmVS( $farmname, $s, "sessionid" );
		$dyns         = &getFarmVS( $farmname, $s, "dynscale" );
		$httpsbe      = &getFarmVS( $farmname, $s, "httpsbackend" );
		$cookiei      = &getFarmVS( $farmname, $s, "cookieins" );
		if ( $cookiei eq "" )
		{
			$cookiei = "false";
		}
		$cookieinsname = &getFarmVS( $farmname, $s, "cookieins-name" );
		$domainname    = &getFarmVS( $farmname, $s, "cookieins-domain" );
		$path          = &getFarmVS( $farmname, $s, "cookieins-path" );
		$ttlc          = &getFarmVS( $farmname, $s, "cookieins-ttlc" );
		if ( $dyns =~ /^$/ )
		{
			$dyns = "false";
		}
		if ( $httpsbe =~ /^$/ )
		{
			$httpsbe = "false";
		}
		my @fgconfig  = &getFarmGuardianConf( $farmname, $s );
		my $fgttcheck = @fgconfig[1];
		my $fgscript  = @fgconfig[2];
		$fgscript =~ s/\n//g;
		$fgscript =~ s/\"/\'/g;
		my $fguse = @fgconfig[3];
		$fguse =~ s/\n//g;
		my $fglog      = @fgconfig[4];
		my $out_ba     = [];
		my $backendsvs = &getFarmVS( $farmname, $s, "backends" );
		my @be         = split ( "\n", $backendsvs );

		foreach $subl ( @be )
		{
			my @subbe       = split ( "\ ", $subl );
			my $id          = @subbe[1] + 0;
			my $maintenance = &getFarmBackendMaintenance( $farmname, $id, $s );
			if ( $maintenance != 0 )
			{
				$backendstatus = "up";
			}
			else
			{
				$backendstatus = "maintenance";
			}
			my $ip   = @subbe[3];
			my $port = @subbe[5] + 0;
			my $tout = @subbe[7] + 0;
			my $prio = @subbe[9] + 0;
			push $out_ba,
			  {
				id            => $id,
				backendstatus => $backendstatus,
				ip            => $ip,
				port          => $port,
				timeout       => $tout,
				weight        => $prio
			  };
		}

		push $out_s,
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
			ttl          => $ttl,
			sessionid    => $sesid,
			leastresp    => $dyns,
			httpsb       => $httpsbe,
			fgtimecheck  => $fgttcheck,
			fgscript     => $fgscript,
			fgenabled    => $fguse,
			fglog        => $fglog,
			backends     => $out_ba
		  };
	}

	# Success
	print $q->header(
					  -type    => 'text/plain',
					  -charset => 'utf-8',
					  -status  => '200 OK'
	);

	my $j = JSON::XS->new->utf8->pretty( 1 );

	#$j->canonical($enabled);
	$j->canonical( 1 );
	my $output = $j->encode(
							 {
							   description => "List farm $farmname",
							   params      => $out_p,
							   services    => $out_s
							 }
	);
	print $output;
}

1;
