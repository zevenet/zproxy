#!/usr/bin/perl 

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

use CGI;
use CGI::Carp qw(warningsToBrowser fatalsToBrowser);
use MIME::Base64;

# Certificate requrements
use Sys::Hostname;
use Date::Parse;
use Time::localtime;

#print "Content-type: text/javascript; charset=utf8\n\n";

my $q = CGI->new;
our $origin = 1;

require "/usr/local/zenloadbalancer/www/functions.cgi";
require "/usr/local/zenloadbalancer/www/cert_functions.cgi";
require "/usr/local/zenloadbalancer/www/farms_functions.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v2.1/global.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v2.1/certificates.cgi";
require "/usr/local/zenloadbalancer/config/global.conf";
require "/usr/local/zenloadbalancer/www/zapi/v2.1/get.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v2.1/post.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v2.1/put.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v2.1/delete.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v2.1/delete_gslb.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v2.1/interface.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v2.1/system_stats.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v2.1/farm_guardian.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v2.1/farm_actions.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v2.1/post_gslb.cgi";

### Verify Zen Cerfificate ###

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
	my $key         = &keycert();

	# output
	my $swcert = 0;

	if ( -e $zlbcertfile )
	{
		my @zen_cert = `$openssl_bin x509 -in $zlbcertfile -noout -text 2>/dev/null`;

		if (    ( !grep /$key/, @zen_cert )
			 || ( !grep /keyid:$keyid/,   @zen_cert )
			 || ( !grep /CN=$hostname\/|CN = $hostname\,/, @zen_cert ) )
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

{
	my $swcert = &certcontrol();

	# if $swcert is greater than 0 zapi should not work
	if ( $swcert > 0 )
	{
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '403 Forbidden'
		);

		if ( $swcert == 1 )
		{
			print
			  "There isn't a valid ZEVENET certificate file, please request a new one\n";
		}
		elsif ( $swcert == 2 )
		{
			print
			  "The certificate file isn't signed by the ZEVENET Certificate Authority, please request a new one\n";
		}
		elsif ( $swcert == 3 )
		{
			# Policy: expired testing certificates would not stop zen service,
			# but rebooting the service would not start the service,
			# interfaces should always be available.
			print
			  "The ZEVENET certificate file you are using is for testing purposes and its expired, please request a new one\n";
		}

		exit;
	}
}

#########################################
#
# Check user authentication
#
#########################################

$not_allowed = 0;

#my $userpass = $ENV{HTTP_AUTHORIZATION};
#$userpass =~ s/Basic\ //i;
#my $userpass_dec = decode_base64($userpass);
#my @user = split(":",$userpass_dec);
#my $user = @user[0];
#my $pass = @user[1];

if ( !( &checkLoggedZapiUser() ) )
{
	print $q->header(
					  -type    => 'text/plain',
					  -charset => 'utf-8',
					  -status  => '401 Unauthorized'
	);
	print "User not authorized";

	exit;
}

#########################################
#
# Check ZAPI key
#
#########################################

my %headers = map { $_ => $q->http( $_ ) } $q->http();

foreach $key ( keys ( %ENV ) )
{
	#chomp($key);
	if ( $key eq "HTTP_ZAPI_KEY" )
	{
		if (    $ENV{ $key } eq &getZAPI( "keyzapi", "" )
			 && &getZAPI( "status", "" ) eq "true" )
		{
			$not_allowed = 1;
		}
	}
}

if ( $not_allowed eq "0" )
{
	print $q->header(
					  -type    => 'text/plain',
					  -charset => 'utf-8',
					  -status  => '401 Unauthorized'
	);
	print "Not authorized";
	exit;
}

#####################################

use JSON::XS;

$enabled = 1;

sub GET($$)
{
	my ( $path, $code ) = @_;
	return unless $q->request_method eq 'GET' or $q->request_method eq 'HEAD';
	return unless $q->path_info =~ $path;
	$code->();
	exit;
}

sub POST($$)
{
	my ( $path, $code ) = @_;
	return unless $q->request_method eq 'POST';
	return unless $q->path_info =~ $path;
	$code->();
	exit;
}

sub PUT($$)
{
	my ( $path, $code ) = @_;
	return unless $q->request_method eq 'PUT';
	return unless $q->path_info =~ $path;
	$code->();
	exit;
}

sub DELETE($$)
{
	my ( $path, $code ) = @_;
	return unless $q->request_method eq 'DELETE';
	return unless $q->path_info =~ $path;
	$code->();
	exit;
}

eval {

	#########################################
	#
	#  GET List all farms
	#
	#########################################
	GET qr{^/farms$} => sub {

		&farms();

	};

	#########################################
	#
	#  GET List SSL certificates
	#
	#########################################
	GET qr{^/certificates$} => sub {

		&certificates();

	};

	#########################################
	#
	#  GET stats
	#
	#########################################

	GET qr{^/stats$} => sub {
		&stats();

	};

	#########################################
	#
	#  GET stats mem
	#
	#########################################

	GET qr{^/stats/mem$} => sub {
		&stats_mem();

	};

	#########################################
	#
	#  GET stats load
	#
	#########################################

	GET qr{^/stats/load$} => sub {
		&stats_load();

	};

	#########################################
	#
	#  GET stats network
	#
	#########################################

	GET qr{^/stats/network$} => sub {
		&stats_network();

	};

	#########################################
	#
	#  GET stats cpu
	#
	#########################################

	GET qr{^/stats/cpu$} => sub {
		&stats_cpu();

	};

	#########################################
	#
	#  GET get farm info
	#
	#########################################
	GET qr{^/farms/(\w+$)} => sub {

		&farms_name();

	};

	#########################################
	#
	#  POST new farm
	#
	#########################################
	POST qr{^/farms/(\w+$)} => sub {

		&new_farm( $1 );

	};

	#########################################
	#
	#  POST new service
	#
	#########################################

	POST qr{^/farms/(\w+)/services$} => sub {

		&new_farm_service( $1 );

	};

	#########################################
	#
	#  POST new zone
	#
	#########################################

	POST qr{^/farms/(\w+)/zones$} => sub {

		&new_farm_zone( $1 );

	};

	#########################################
	#
	#  POST new backend
	#
	#########################################

	POST qr{^/farms/(\w+)/backends$} => sub {

		&new_farm_backend( $1 );

	};

	#########################################
	#
	#  POST new zone resource
	#
	#########################################

	POST qr{^/farms/(\w+)/zoneresources$} => sub {

		&new_farm_zoneresource( $1 );

	};

	#########################################
	#
	#  POST farm actions
	#
	#########################################

	POST qr{^/farms/(\w+)/actions$} => sub {

		&actions( $1 );

	};

	#########################################
	#
	#  POST status backend actions
	#
	#########################################

	POST qr{^/farms/(\w+)/maintenance$} => sub {

		&maintenance( $1 );

	};

	#########################################
	#
	#  DELETE farm
	#
	#########################################
	DELETE qr{^/farms/(\w+$)} => sub {

		&delete_farm( $1 );

	};

	#########################################
	#
	#  DELETE certificate
	#
	#########################################
	DELETE qr{^/certificates/(\w+\.\w+$)} => sub {

		&delete_certificate( $1 );

	};

	#########################################
	#
	#  DELETE farm certificate
	#
	#########################################
	DELETE qr{^/farms/(\w+)/deletecertificate/(\w+$)} => sub {

		&delete_farmcertificate( $1, $2 );

	};

	#########################################
	#
	#  DELETE service
	#
	#########################################

	DELETE qr{^/farms/(\w+)/services/(\w+$)} => sub {

		&delete_service( $1, $2 );

	};

	#########################################
	#
	#  DELETE zone
	#
	#########################################

	#DELETE qr{^/farms/(\w+)/zones/(.*+$)} => sub {
	DELETE qr{^/farms/(\w+)/zones/(([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$)} => sub {

		&delete_zone( $1, $2 );

	};

	#########################################
	#
	#  DELETE backend (TCP/UDP/L4XNAT/DATALINK)
	#
	#########################################

	DELETE qr{^/farms/(\w+)/backends/(\w+$)} => sub {

		&delete_backend( $1, $2 );

	};

	#########################################
	#
	#  DELETE backend (HTTP/HTTPS/GSLB)
	#
	#########################################

	DELETE qr{^/farms/(\w+)/services/(\w+)/backends/(\w+$)} => sub {

		&delete_service_backend( $1, $2, $3 );

	};

	#########################################
	#
	#  DELETE zone resource
	#
	#########################################

	DELETE qr{^/farms/(\w+)/zones/([a-z0-9].*-*.*\.[a-z0-9].*)/resources/(\w+$)} =>
	  sub {
		&delete_zone_resource( $1, $2, $3 );

	  };

	#########################################
	#
	#  PUT farm
	#
	#########################################

	PUT qr{^/farms/(\w+$)} => sub {

		&modify_farm( $1 );

	};

	#########################################
	#
	#  PUT backend
	#
	#########################################

	PUT qr{^/farms/(\w+)/backends/(\w+$)} => sub {

		&modify_backends( $1, $2 );

	};

	#########################################
	#
	#  PUT farmguardian
	#
	#########################################

	PUT qr{^/farms/(\w+)/fg$} => sub {
		&modify_farmguardian( $1 );

	};

	#########################################
	#
	#  PUT resources
	#
	#########################################

	PUT qr{^/farms/(\w+)/resources/(\w+$)} => sub {
		&modify_resources( $1, $2 );

	};

	#########################################
	#
	#  PUT zones
	#
	#########################################

	PUT qr{^/farms/(\w+)/zones/(.*+$)} => sub {
		&modify_zones( $1, $2 );

	};

	#########################################
	#
	#  PUT services
	#
	#########################################

	PUT qr{^/farms/(\w+)/services/(\w+$)} => sub {
		&modify_services( $1, $2 );

	};

	#########################################
	#
	#  POST virtual interface
	#
	#########################################

	POST qr{^/addvini/(.*$)} => sub {

		&new_vini( $1 );

	};

	#########################################
	#
	#  POST vlan interface
	#
	#########################################

	POST qr{^/addvlan/(.*$)} => sub {

		&new_vlan( $1 );

	};

	#########################################
	#
	#  POST action interface
	#
	#########################################

	POST qr{^/ifaction/(.*+$)} => sub {

		&ifaction( $1 );

	};

	#########################################
	#
	#  POST certificates
	#
	#########################################

	POST qr{^/certificates$} => sub {

		&upload_certs();

	};

	#########################################
	#
	#  POST add certificates
	#
	#########################################

	POST qr{^/farms/(\w+)/addcertificate$} => sub {

		&add_farmcertificate( $1 );

	};

	#########################################
	#
	#  PUT change certificates
	#
	#########################################

	PUT qr{^/farms/(\w+)/changecertificate$} => sub {

		&change_farmcertificate( $1 );

	};

	#########################################
	#
	#  DELETE virtual interface (default)
	#
	#########################################

	DELETE qr{^/deleteif/(.*$)} => sub {

		&delete_interface( $1 );

	};

	#########################################
	#
	#  GET interfaces
	#
	#########################################
	GET qr{^/interfaces$} => sub {
		&get_interface();

	};

	#########################################
	#
	#  PUT interface
	#
	#########################################

	PUT qr{^/modifyif/(.*$)} => sub {

		&modify_interface( $1 );

	};

	#########################################
	#
	#  GET farm stats
	#
	#########################################
	GET qr{^/farms/(\w+)/stats$} => sub {
		&farm_stats( $1 );

	};

	#########################################
	#
	#  GET graphs
	#
	#########################################
	GET qr{^/graphs/(\w+)/(.*)/(\w+$)} => sub {
		&get_graphs( $1, $2, $3 );

	};

	#########################################
	#
	#  GET possible graphs
	#
	#########################################
	GET qr{^/graphs} => sub {
		&possible_graphs();

	};

	#end eval
};
