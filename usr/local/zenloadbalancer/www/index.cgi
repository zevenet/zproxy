#!/usr/bin/perl 

###############################################################################
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

# For debuging
#~ use strict;
#~ use warnings;
#~ require "/usr/local/zenloadbalancer/config/global.conf";
#~ our ( $basedir, $configdir, $logdir, $logfile, $timeouterrors, $filecluster, $confhttp, $ntp, $backupfor, $backupdir, $rttables, $globalcfg, $version, $cipher_pci, $buy_ssl, $url, $htpass, $zapikey, $filedns, $fileapt, $tar, $ifconfig_bin, $ip_bin, $pen_bin, $pen_ctl, $fdisk_bin, $df_bin, $sshkeygen, $ssh, $scp, $rsync, $ucarp, $pidof, $ps, $tail, $zcat, $datentp, $arping_bin, $ping_bin, $openssl, $unzip, $mv, $ls, $cp, $iptables, $modprobe, $lsmod, $netstatNat, $gdnsd, $l4sd, $bin_id, $conntrack, $pound, $poundctl, $poundtpl, $piddir, $fwmarksconf, $defaultgw, $defaultgwif, $pingc, $libexec_dir, $farmguardian, $farmguardian_dir, $farmguardian_logs, $rrdap_dir, $img_dir, $rrd_dir, $log_rrd, $zenino, $zeninopid, $zeninolog, $zenrsync, $zenlatup, $zenlatdown, $zenlatlog, $zenbackup );
#~ use Data::Dumper;
# End debugging

# Call external files
require "/usr/local/zenloadbalancer/www/functions.cgi";
require "/usr/local/zenloadbalancer/config/global.conf";

use CGI;
use CGI::Carp qw(warningsToBrowser fatalsToBrowser);

use Sys::Hostname;
use Date::Parse;
use Time::localtime;

# build local key
sub keycert()
{
	# requires:
	#~ use Sys::Hostname;

	my $dmidecode_bin = "/usr/sbin/dmidecode";    # input
	my $hostname      = hostname();               # input

	my @dmidec  = `$dmidecode_bin`;
	my @dmidec2 = grep ( /UUID\:/, @dmidec );
	my $dmi     = $dmidec2[0];

	$dmi =~ s/\"//g;     # remove doble quotes
	$dmi =~ s/^\s+//;    # remove whitespaces at the begining
	$dmi =~ s/\s+$//;    # remove whitespaces at the end
	$dmi =~ s/\ //g;     # remove spaces

	my @dmidec3 = split ( ":", $dmi );
	$dmi = $dmidec3[1];

	$hostname =~ s/\"//g;     # remove doble quotes
	$hostname =~ s/^\s+//;    # remove whitespaces at the begining
	$hostname =~ s/\s+$//;    # remove whitespaces at the end

	my $encrypted_string  = crypt ( "${dmi}${hostname}", "93" );
	my $encrypted_string2 = crypt ( "${hostname}${dmi}", "a3" );
	my $encrypted_string3 = crypt ( "${dmi}${hostname}", "ZH" );
	my $encrypted_string4 = crypt ( "${hostname}${dmi}", "h7" );
	$encrypted_string =~ s/^93//;
	$encrypted_string2 =~ s/^a3//;
	$encrypted_string3 =~ s/^ZH//;
	$encrypted_string4 =~ s/^h7//;

	my $str =
	  "${encrypted_string}-${encrypted_string2}-${encrypted_string3}-${encrypted_string4}";

	$str =~ s/\"//g;     # remove doble quotes
	$str =~ s/^\s+//;    # remove whitespaces at the begining
	$str =~ s/\s+$//;    # remove whitespaces at the end

	return $str;
}

# evaluate certificate
sub certcontrol()
{
	# requires:
	#~ use Sys::Hostname;
	#~ use Date::Parse;
	#~ use Time::localtime;

	# input
	my $hostname    = hostname();
	my $zlbcertfile = "$basedir/zlbcertfile.pem";
	my $openssl_bin = "/usr/bin/openssl";
	my $keyid       = "4B:1B:18:EE:21:4A:B6:F9:76:DE:C3:D8:86:6D:DE:98:DE:44:93:B9";

	# output
	my $swcert = 0;

	if ( -e $zlbcertfile )
	{
		my @zen_cert = `$openssl_bin x509 -in $zlbcertfile -noout -text 2>/dev/null`;

		if (    ( !grep /$key/, @zen_cert )
			 || ( !grep /keyid:$keyid/,   @zen_cert )
			 || ( !grep /CN=$hostname\//, @zen_cert ) )
		{
			$swcert = 2;
		}

		my $now = ctime();

		# Certificate validity date
		my @notbefore = grep /Not Before/i, @zen_cert;
		my $nb = join '', @notbefore;
		$nb =~ s/not before.*:\ //i;
		my $ini = str2time( $nb );

		# Certificate expiring date
		my @notafter = grep /Not After/i, @zen_cert;
		my $na = join "", @notafter;
		$na =~ s/not after.*:\ //i;
		my $end = str2time( $na );

		# Validity remaining
		my $totaldays = ( $end - $ini ) / 86400;
		$totaldays =~ s/\-//g;
		my $dayright = ( $end - time () ) / 86400;

		#control errors
		if ( $totaldays < 364 && $dayright < 0 && $swcert == 0 )
		{
			# Policy: expired testing certificates would not stop zen service,
			# but rebooting the service would not start the service,
			# interfaces should always be available.
			$swcert = 3;
		}

		if ( $totaldays > 364 && $dayright < 0 && $swcert == 0 )
		{
			# The contract support plan is expired you have to request a
			# new contract support. Only message alert!
			$swcert = -1;
		}
	}
	else
	{
		#There isn't certificate in the machine
		$swcert = 1;
	}

	# error codes
	#swcert = 0 ==> OK
	#swcert = 1 ==> There isn't certificate
	#swcert = 2 ==> Cert isn't signed OK
	#swcert = 3 ==> Cert test and it's expired
	#swcert = -1 ==> Cert support and it's expired

	#output
	return $swcert;
}

####################################################################

&login();
my $cgi = new CGI;

#uncomment for debug
#&logfile( "index.cgi cgi:" . Dumper( \{ $cgi->Vars } ) );

#Global Parameters
$id = $cgi->param( 'id' )
  if ( defined ( $cgi->param( 'id' ) ) );
$farmname = $cgi->param( 'farmname' )
  if ( defined ( $cgi->param( 'farmname' ) ) );
$action = $cgi->param( 'action' )
  if ( defined ( $cgi->param( 'action' ) ) );

#GSLB Global Parameters
$newfarmname = $cgi->param( 'newfarmname' )
  if ( defined ( $cgi->param( 'newfarmname' ) ) );
$vip = $cgi->param( 'vip' )
  if ( defined ( $cgi->param( 'vip' ) ) );
$vipp = $cgi->param( 'vipp' )
  if ( defined ( $cgi->param( 'vipp' ) ) );

#GSLB Add Service
$service_type = $cgi->param( 'service_type' )
  if ( defined ( $cgi->param( 'service_type' ) ) );
$lb = $cgi->param( 'lb' )
  if ( defined ( $cgi->param( 'lb' ) ) );
$service = $cgi->param( 'service' )
  if ( defined ( $cgi->param( 'service' ) ) );

#GSLB Service Parameters
$dpc = $cgi->param( 'dpc' )
  if ( defined ( $cgi->param( 'dpc' ) ) );

#GSLB Server Parameters
$rip_server = $cgi->param( 'rip_server' )
  if ( defined ( $cgi->param( 'rip_server' ) ) );

#GSLB Add Zone
$zone = $cgi->param( 'zone' )
  if ( defined ( $cgi->param( 'zone' ) ) );

#GSLB Zone Parameters
$ns = $cgi->param( 'ns' )
  if ( defined ( $cgi->param( 'ns' ) ) );

#GSLB Resource Parameters
$resource_server = $cgi->param( 'resource_server' )
  if ( defined ( $cgi->param( 'resource_server' ) ) );
$ttl_server = $cgi->param( 'ttl_server' )
  if ( defined ( $cgi->param( 'ttl_server' ) ) );
$rdata_server = $cgi->param( 'rdata_server' )
  if ( defined ( $cgi->param( 'rdata_server' ) ) );
$type_server = $cgi->param( 'type_server' )
  if ( defined ( $cgi->param( 'type_server' ) ) );

#DATALINK Global Parameters (newfarmname, vip y lb)

#L4xNAT Global Parameters
$session = $cgi->param( 'session' )
  if ( defined ( $cgi->param( 'session' ) ) );
$sessttl = $cgi->param( 'sessttl' )
  if ( defined ( $cgi->param( 'sessttl' ) ) );
$farmprotocol = $cgi->param( 'farmprotocol' )
  if ( defined ( $cgi->param( 'farmprotocol' ) ) );
$nattype = $cgi->param( 'nattype' )
  if ( defined ( $cgi->param( 'nattype' ) ) );
$timetocheck = $cgi->param( 'timetocheck' )
  if ( defined ( $cgi->param( 'timetocheck' ) ) );
$usefarmguardian = $cgi->param( 'usefarmguardian' )
  if ( defined ( $cgi->param( 'usefarmguardian' ) ) );
$check_script = $cgi->param( 'check_script' )
  if ( defined ( $cgi->param( 'check_script' ) ) );
$farmguardianlog = $cgi->param( 'farmguardianlog' )
  if ( defined ( $cgi->param( 'farmguardianlog' ) ) );

#L4xNAT Server Parameters
$id_server = $cgi->param( 'id_server' )
  if ( defined ( $cgi->param( 'id_server' ) ) );
$port_server = $cgi->param( 'port_server' )
  if ( defined ( $cgi->param( 'port_server' ) ) );
$weight_server = $cgi->param( 'weight_server' )
  if ( defined ( $cgi->param( 'weight_server' ) ) );
$priority_server = $cgi->param( 'priority_server' )
  if ( defined ( $cgi->param( 'priority_server' ) ) );

#HTTP Global Parameters
$conntout = $cgi->param( 'conntout' )
  if ( defined ( $cgi->param( 'conntout' ) ) );
$resptout = $cgi->param( 'resptout' )
  if ( defined ( $cgi->param( 'resptout' ) ) );
$checkalive = $cgi->param( 'checkalive' )
  if ( defined ( $cgi->param( 'checkalive' ) ) );
$clienttout = $cgi->param( 'clienttout' )
  if ( defined ( $cgi->param( 'clienttout' ) ) );
$conn_max = $cgi->param( 'conn_max' )
  if ( defined ( $cgi->param( 'conn_max' ) ) );
$rewritelocation = $cgi->param( 'rewritelocation' )
  if ( defined ( $cgi->param( 'rewritelocation' ) ) );
$httpverb = $cgi->param( 'httpverb' )
  if ( defined ( $cgi->param( 'httpverb' ) ) );
$farmlisten = $cgi->param( 'farmlisten' )
  if ( defined ( $cgi->param( 'farmlisten' ) ) );
$err414 = $cgi->param( 'err414' )
  if ( defined ( $cgi->param( 'err414' ) ) );
$err500 = $cgi->param( 'err500' )
  if ( defined ( $cgi->param( 'err500' ) ) );
$err501 = $cgi->param( 'err501' )
  if ( defined ( $cgi->param( 'err501' ) ) );
$err503 = $cgi->param( 'err503' )
  if ( defined ( $cgi->param( 'err503' ) ) );
$ciphers = $cgi->param( 'ciphers' )
  if ( defined ( $cgi->param( 'ciphers' ) ) );
$cipherc = $cgi->param( 'cipherc' )
  if ( defined ( $cgi->param( 'cipherc' ) ) );

#HTTPS Add Cert to SNI List
$certname = $cgi->param( 'certname' )
  if ( defined ( $cgi->param( 'certname' ) ) );

#HTTPS Delete Cert of SNI List (certname)

#HTTP Add Service

#HTTP Service Parameters
$vser = $cgi->param( 'vser' )
  if ( defined ( $cgi->param( 'vser' ) ) );
$urlp = $cgi->param( 'urlp' )
  if ( defined ( $cgi->param( 'urlp' ) ) );
$redirect = $cgi->param( 'redirect' )
  if ( defined ( $cgi->param( 'redirect' ) ) );
$redirecttype = $cgi->param( 'redirecttype' )
  if ( defined ( $cgi->param( 'redirecttype' ) ) );
$dynscale = $cgi->param( 'dynscale' )
  if ( defined ( $cgi->param( 'dynscale' ) ) );
$httpsbackend = $cgi->param( 'httpsbackend' )
  if ( defined ( $cgi->param( 'httpsbackend' ) ) );
$cookieins = $cgi->param( 'cookieins' )
  if ( defined ( $cgi->param( 'cookieins' ) ) );
$cookieinsname = $cgi->param( 'cookieinsname' )
  if ( defined ( $cgi->param( 'cookieinsname' ) ) );
$domainname = $cgi->param( 'domainname' )
  if ( defined ( $cgi->param( 'domainname' ) ) );
$path = $cgi->param( 'path' )
  if ( defined ( $cgi->param( 'path' ) ) );
$ttlc = $cgi->param( 'ttlc' )
  if ( defined ( $cgi->param( 'ttlc' ) ) );
$session = $cgi->param( 'session' )
  if ( defined ( $cgi->param( 'session' ) ) );
$ttlserv = $cgi->param( 'ttlserv' )
  if ( defined ( $cgi->param( 'ttlserv' ) ) );
$sessionid = $cgi->param( 'sessionid' )
  if ( defined ( $cgi->param( 'sessionid' ) ) );

#HTTP Server Parameters
$timeout_server = $cgi->param( 'timeout_server' )
  if ( defined ( $cgi->param( 'timeout_server' ) ) );

#TCP Global Parameters
$timeout = $cgi->param( 'timeout' )
  if ( defined ( $cgi->param( 'timeout' ) ) );
$blacklist = $cgi->param( 'blacklist' )
  if ( defined ( $cgi->param( 'blacklist' ) ) );
$persistence = $cgi->param( 'persistence' )
  if ( defined ( $cgi->param( 'persistence' ) ) );
$max_clients = $cgi->param( 'max_clients' )
  if ( defined ( $cgi->param( 'max_clients' ) ) );
$tracking = $cgi->param( 'tracking' )
  if ( defined ( $cgi->param( 'tracking' ) ) );
$conn_max = $cgi->param( 'conn_max' )
  if ( defined ( $cgi->param( 'conn_max' ) ) );
$max_servers = $cgi->param( 'max_servers' )
  if ( defined ( $cgi->param( 'max_servers' ) ) );
$xforwardedfor = $cgi->param( 'xforwardedfor' )
  if ( defined ( $cgi->param( 'xforwardedfor' ) ) );

#TCP Server Parameters
$max_server = $cgi->param( 'max_server' )
  if ( defined ( $cgi->param( 'max_server' ) ) );

#Stats
$viewtableclients = $cgi->param( 'viewtableclients' )
  if ( defined ( $cgi->param( 'viewtableclients' ) ) );
$viewtableconn = $cgi->param( 'viewtableconn' )
  if ( defined ( $cgi->param( 'viewtableconn' ) ) );
$refresh = $cgi->param( 'refresh' )
  if ( defined ( $cgi->param( 'refresh' ) ) );

#Content2-1
$graphtype = $cgi->param( 'graphtype' )
  if ( defined ( $cgi->param( 'graphtype' ) ) );

#Content2-3
$nlines = $cgi->param( 'nlines' )
  if ( defined ( $cgi->param( 'nlines' ) ) );
$filelog = $cgi->param( 'filelog' )
  if ( defined ( $cgi->param( 'filelog' ) ) );

#Content3-1
$touterr = $cgi->param( 'touterr' )
  if ( defined ( $cgi->param( 'touterr' ) ) );
$ntp = $cgi->param( 'ntp' )
  if ( defined ( $cgi->param( 'ntp' ) ) );
$zenrsync = $cgi->param( 'zenrsync' )
  if ( defined ( $cgi->param( 'zenrsync' ) ) );
$var1 = $cgi->param( 'var1' )
  if ( defined ( $cgi->param( 'var1' ) ) );
$var2 = $cgi->param( 'var2' )
  if ( defined ( $cgi->param( 'var2' ) ) );
$var3 = $cgi->param( 'var3' )
  if ( defined ( $cgi->param( 'var3' ) ) );
$ipgui = $cgi->param( 'ipgui' )
  if ( defined ( $cgi->param( 'ipgui' ) ) );
$guiport = $cgi->param( 'guiport' )
  if ( defined ( $cgi->param( 'guiport' ) ) );
$var = $cgi->param( 'var' )
  if ( defined ( $cgi->param( 'var' ) ) );
$dnsserv = $cgi->param( 'dnsserv' )
  if ( defined ( $cgi->param( 'dnsserv' ) ) );
$aptrepo = $cgi->param( 'aptrepo' )
  if ( defined ( $cgi->param( 'aptrepo' ) ) );

#Content3-21
$if = $cgi->param( 'if' )
  if ( defined ( $cgi->param( 'if' ) ) );
$toif = $cgi->param( 'toif' )
  if ( defined ( $cgi->param( 'toif' ) ) );
$status = $cgi->param( 'status' )
  if ( defined ( $cgi->param( 'status' ) ) );
$newip = $cgi->param( 'newip' )
  if ( defined ( $cgi->param( 'newip' ) ) );
$netmask = $cgi->param( 'netmask' )
  if ( defined ( $cgi->param( 'netmask' ) ) );
$gwaddr = $cgi->param( 'gwaddr' )
  if ( defined ( $cgi->param( 'gwaddr' ) ) );
$source = $cgi->param( 'source' )
  if ( defined ( $cgi->param( 'source' ) ) );
$status = $cgi->param( 'status' )
  if ( defined ( $cgi->param( 'status' ) ) );

#Content3-3
$vipcl = $cgi->param( 'vipcl' )
  if ( defined ( $cgi->param( 'vipcl' ) ) );
$lhost = $cgi->param( 'lhost' )
  if ( defined ( $cgi->param( 'lhost' ) ) );
$lip = $cgi->param( 'lip' )
  if ( defined ( $cgi->param( 'lip' ) ) );
$rhost = $cgi->param( 'rhost' )
  if ( defined ( $cgi->param( 'rhost' ) ) );
$rip = $cgi->param( 'rip' )
  if ( defined ( $cgi->param( 'rip' ) ) );
$idcluster = $cgi->param( 'idcluster' )
  if ( defined ( $cgi->param( 'idcluster' ) ) );
$deadratio = $cgi->param( 'deadratio' )
  if ( defined ( $cgi->param( 'deadratio' ) ) );
$typecl = $cgi->param( 'typecl' )
  if ( defined ( $cgi->param( 'typecl' ) ) );
$aptrepo = $cgi->param( 'aptrepo' )
  if ( defined ( $cgi->param( 'aptrepo' ) ) );
$clstatus = $cgi->param( 'clstatus' )
  if ( defined ( $cgi->param( 'clstatus' ) ) );
$ifname = $cgi->param( 'ifname' )
  if ( defined ( $cgi->param( 'ifname' ) ) );
$cable = $cgi->param( 'cable' )
  if ( defined ( $cgi->param( 'cable' ) ) );

#Content3-4
$enablepass = $cgi->param( 'enablepass' )
  if ( defined ( $cgi->param( 'enablepass' ) ) );
$keyzapi = $cgi->param( 'keyzapi' )
  if ( defined ( $cgi->param( 'keyzapi' ) ) );
$pass = $cgi->param( 'pass' )
  if ( defined ( $cgi->param( 'pass' ) ) );
$newpass = $cgi->param( 'newpass' )
  if ( defined ( $cgi->param( 'newpass' ) ) );
$trustedpass = $cgi->param( 'trustedpass' )
  if ( defined ( $cgi->param( 'trustedpass' ) ) );

#Content3-5
$name = $cgi->param( 'name' )
  if ( defined ( $cgi->param( 'name' ) ) );
$file = $cgi->param( 'file' )
  if ( defined ( $cgi->param( 'file' ) ) );

$cert_name = $cgi->param( 'cert_name' )
  if ( defined ( $cgi->param( 'cert_name' ) ) );
$cert_issuer = $cgi->param( 'cert_issuer' )
  if ( defined ( $cgi->param( 'cert_issuer' ) ) );
$cert_fqdn = $cgi->param( 'cert_fqdn' )
  if ( defined ( $cgi->param( 'cert_fqdn' ) ) );
$cert_division = $cgi->param( 'cert_division' )
  if ( defined ( $cgi->param( 'cert_division' ) ) );
$cert_organization = $cgi->param( 'cert_organization' )
  if ( defined ( $cgi->param( 'cert_organization' ) ) );
$cert_locality = $cgi->param( 'cert_locality' )
  if ( defined ( $cgi->param( 'cert_locality' ) ) );
$cert_state = $cgi->param( 'cert_state' )
  if ( defined ( $cgi->param( 'cert_state' ) ) );
$cert_country = $cgi->param( 'cert_country' )
  if ( defined ( $cgi->param( 'cert_country' ) ) );
$cert_mail = $cgi->param( 'cert_mail' )
  if ( defined ( $cgi->param( 'cert_mail' ) ) );
$cert_password = $cgi->param( 'cert_password' )
  if ( defined ( $cgi->param( 'cert_password' ) ) );
$cert_cpassword = $cgi->param( 'cert_cpassword' )
  if ( defined ( $cgi->param( 'cert_cpassword' ) ) );
$cert_key = $cgi->param( 'cert_key' )
  if ( defined ( $cgi->param( 'cert_key' ) ) );

if ( $action eq "logout" )
{
	&logfile( "Session Logged out" );
	&logout();
}

if ( !$id )
{
	$id = "1-1";
}

##HEADER
require "/usr/local/zenloadbalancer/www/header.cgi";
require "/usr/local/zenloadbalancer/www/menu.cgi";

if ( !-f "$basedir/lock" )
{
	eval {
		local $SIG{ ALARM } = sub { die "alarm\n" };

		alarm $timeouterrors;

		my $key    = &keycert();
		my $swcert = &certcontrol();
		my $host   = hostname();

		if ( $swcert != 0 )
		{
			print "<!--- CONTENT AREA -->";
			print "<div class=\"content container_12\">";

			if ( $swcert == 1 )
			{
				&errormsg(
					"There isn't a valid Zen Load Balancer certificate file, please request a new one"
				);
			}
			elsif ( $swcert == 2 )
			{
				&errormsg(
					"The certificate file isn't signed by the Zen Load Balancer Certificate Authority, please request a new one"
				);
			}
			elsif ( $swcert == 3 )
			{
				# Policy: expired testing certificates would not stop zen service,
				# but rebooting the service would not start the service,
				# interfaces should always be available.
				&errormsg(
					"The Zen Load Balancer certificate file you are using is for testing purposes and its expired, please request a new one"
				);
			}
			elsif ( $swcert == -1 )
			{
				&warnmsg(
					"The Zen Load Balancer certificate file support is expired, please request a new one"
				);
			}

			print "
				<div class=\"box grid_12\">
				  <div class=\"box-head\">
					<span class=\"box-icon-24 fugue-24 server\"></span>	  
					<h2>Request Certificate</h2>
				  </div>
				  <div class=\"box-content\">
					<p><h6>Certificate key:</h6></p>
					<div class=\"row\">
					  <p>$key</p>
					</div>
					<p><h6>Hostname:</h6></p>
					<div class=\"row\">
					  <p>$host</p>
					</div>
					<p  style=\"margin-bottom: 6px;\">
					  <a href=\"uploadcertfile.cgi\" class=\"open-dialog button grey\">
						Upload a Zen Load Balancer certificate file
					  </a>
					</p>
					<div id=\"dialog-container\" style=\"display: none;\">
					  <iframe id=\"dialog\" width=\"100%\" height=\"350\"></iframe></div>
					  <script>
						\$(document).ready(function () {
							\$(\".open-dialog\").click(function () {
								\$(\"#dialog\").attr('src', \$(this).attr(\"href\"));
								\$(\"#dialog-container\").dialog({
									width: 350,
									height: 350,
									modal: true,
									close: function () {
										window.location.replace('index.cgi');
									}
								});
								return false;
							});
						});
					  </script>
					</div>
				  </div>\n";
		}

		if ( $swcert == 0 || $swcert == -1 )
		{
			require "/usr/local/zenloadbalancer/www/content" . $id . ".cgi";
			alarm 0;
		}
	};

	if ( $@ ) { print "Error in content$id cgi execution, output: $@\n"; }
}
else
{
	&errormsg(
		"Actually Zen GUI is locked, please unlock with '/etc/init.d/zenloadbalancer start' command"
	);
}

#FOOTER
require "/usr/local/zenloadbalancer/www/footer.cgi";
