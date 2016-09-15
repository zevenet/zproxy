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
use CGI::Session;
use CGI::Carp qw(warningsToBrowser fatalsToBrowser);
use MIME::Base64;
use JSON::XS;

# Certificate requrements
use Date::Parse;
use Time::localtime;

# Debugging
use Data::Dumper;
#~ use Devel::Size qw(size total_size);

package GLOBAL {
	our $http_status_codes = {
		# 2xx Success codes
		200 => 'OK',
		201 => 'Created',

		# 4xx Client Error codes
		400 => 'Bad Request',
		401 => 'Unauthorized',
		403 => 'Forbidden',
		404 => 'Not Found',
	};
};

require "/usr/local/zenloadbalancer/config/global.conf";
require "/usr/local/zenloadbalancer/www/functions.cgi";
require "/usr/local/zenloadbalancer/www/cert_functions.cgi";
require "/usr/local/zenloadbalancer/www/farms_functions.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/global.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/certificates.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/get.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/post.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/put.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/delete.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/delete_gslb.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/interface.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/system_stats.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/farm_guardian.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/farm_actions.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/post_gslb.cgi";

my $q = &getCGI();
our $origin = 1;

# build local key
sub keycert()
{
	# requires:
	#~ use Sys::Hostname;

	my $dmidecode_bin = "/usr/sbin/dmidecode";    # input
	my $hostname      = &getHostname();               # input

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
	my $hostname    = &getHostname();
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

sub checkActivationCertificate
{
	my $swcert = &certcontrol();

	# if $swcert is greater than 0 zapi should not work
	if ( $swcert > 0 )
	{
		my $message;

		if ( $swcert == 1 )
		{
			$message =
			  "There isn't a valid Zen Load Balancer certificate file, please request a new one";
		}
		elsif ( $swcert == 2 )
		{
			$message =
			  "The certificate file isn't signed by the Zen Load Balancer Certificate Authority, please request a new one";
		}
		elsif ( $swcert == 3 )
		{
			# Policy: expired testing certificates would not stop zen service,
			# but rebooting the service would not start the service,
			# interfaces should always be available.
			$message =
			  "The Zen Load Balancer certificate file you are using is for testing purposes and its expired, please request a new one";
		}

		&httpResponse({ http_code => 400, body => { message => $message } });

		exit;
	}

	return $swcert;
}

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

sub OPTIONS($$)
{
	my ( $path, $code ) = @_;
	return unless $q->request_method eq 'OPTIONS';
	return unless $q->path_info =~ $path;
	$code->();
	exit;
}

sub validCGISession
{
	my $validSession = 0;
	my $session = CGI::Session->load( $cgi );

	&zenlog( "CGI SESSION ID: ".$session->id );
	#~ &zenlog( "session data: " . Dumper $session->dataref() ); # DEBUG

	if ( $session && $session->param( 'is_logged_in' ) && ! $session->is_expired )
	{
		$session->expire('is_logged_in', '+30m');
		#~ $session->expire('is_logged_in', '+5s'); # DEBUG
		$validSession = 1;
	}

	return $validSession;
}

sub validZapiKey
{
	my $validKey = 0; # output

	my $key = "HTTP_ZAPI_KEY";

	if (  exists $ENV{ $key }	# exists
		 && &getZAPI( "keyzapi" ) eq $ENV{ $key } # matches key
		 && &getZAPI( "status" ) eq "true" )	# zapi user enabled??
	{
		$validKey = 1;
	}

	return $validKey;
}

sub getAuthorizationCredentials
{
	my $base64_digest;
	my $username;
	my $password;

	if ( exists $ENV{ HTTP_AUTHORIZATION } )
	{
		# Expected header example: 'Authorization': 'Basic aHR0cHdhdGNoOmY='
		$ENV{ HTTP_AUTHORIZATION } =~ /^Basic (.+)$/;
		$base64_digest = $1;
	}

	if ( $base64_digest )
	{
		# $decoded_digest format: "username:password"
		my $decoded_digest = decode_base64( $base64_digest );
		chomp $decoded_digest;
		( $username, $password ) = split ( ":", $decoded_digest );
	}

	return undef if ! $username or ! $password;
	return ( $username, $password );
}

sub authenticateCredentials    #($user,$curpasswd)
{
	my ( $user, $pass ) = @_;

	return undef if ! defined $user or ! defined $pass;

	use Authen::Simple::Passwd;
	#~ use Authen::Simple::PAM;

	my $valid_credentials = 0;	# output

	my $passfile = "/etc/shadow";
	my $simple   = Authen::Simple::Passwd->new( path => "$passfile" );
	#~ my $simple   = Authen::Simple::PAM->new();

	if ( $simple->authenticate( $user, $pass ) )
	{
		$valid_credentials = 1;
	}

	return $valid_credentials;
}

=begin nd
	Function: httpResponse

	Render and print zapi response fron data input.

	Parameters:

		Hash reference with these key-value pairs:

		http_code - HTTP status code digit
		headers - optional hash reference of extra http headers to be included
		body - optional hash reference with data to be sent as JSON

	Returns:

		Nothing useful.
=cut
sub httpResponse
{
	my $self = shift;

	#~ &zenlog("DEBUG httpResponse input: " . Dumper $self ); # DEBUG

	die 'httpResponse: Bad input' if !defined $self or ref $self ne 'HASH';

	die
	  if !defined $self->{ http_code }
	  or !exists $GLOBAL::http_status_codes->{ $self->{ http_code } };

	my $cgi = &getCGI();
	my @headers = ( 'Access-Control-Allow-Origin' => '*' );

	if ( $ENV{ 'REQUEST_METHOD' } eq 'OPTIONS' )
	{
		push @headers,
		  'Access-Control-Allow-Methods' => 'GET, POST, PUT, DELETE, OPTIONS',
		  'Access-Control-Allow-Headers' => 'Authorization, Set-cookie, Content-Type';
	}

	# add possible extra headers
	if ( exists $self->{ headers } && ref $self->{ headers } eq 'HASH' )
	{
		push @headers, %{ $self->{ headers } };
	}

	# header

	my $output = $cgi->header(

		# Standard headers
		# -type    => 'text/plain',
		# -type    => 'application/json',

		-type    => 'application/json',
		-charset => 'utf-8',
		-status  => "$self->{ http_code }",

		# extra headers
		@headers,
	);

	# body

	#~ my ( $body_ref ) = shift @_; # opcional
	if ( exists $self->{ body } && ref $self->{ body } eq 'HASH' )
	{
		my $json    = JSON::XS->new->utf8->pretty( 1 );
		my $enabled = 1;
		$json->canonical( [$enabled] );
		$output .= $json->encode( $self->{ body } );
	}

	#~ &zenlog( "Response:$output<" ); # DEBUG
	print $output;

	&zenlog( "STATUS:$self->{ http_code }" );

	exit;
}

#########################################
#
# Debugging messages
#
#########################################

&zenlog(">>>>>> CGI REQUEST: <$ENV{REQUEST_METHOD} $ENV{SCRIPT_URL}> <<<<<<");
&zenlog("HTTP HEADERS: " . join(', ', $cgi->http() ) );
&zenlog("HTTP_AUTHORIZATION: <$ENV{HTTP_AUTHORIZATION}>") if exists $ENV{HTTP_AUTHORIZATION};
&zenlog("HTTP_ZAPI_KEY: <$ENV{HTTP_ZAPI_KEY}>") if exists $ENV{HTTP_ZAPI_KEY};
#~ my $post_data = $q->param('POSTDATA');
#~ my $put_data = $q->param('PUTDATA');
#~
#~ #my $session = new CGI::Session( $cgi );
#~
#~ my $param_zapikey = $ENV{'HTTP_ZAPI_KEY'};
#~ my $param_session = new CGI::Session( $q );
#~
#~ my $param_client = $q->param('client');
#~
#~
#~ &zenlog("CGI PARAMS: " . Dumper $params );
#~ &zenlog("CGI OBJECT: " . Dumper $cgi );
#~ &zenlog("CGI VARS: " . Dumper $cgi->Vars() );
#~ &zenlog("PERL ENV: " . Dumper \%ENV );
#~ &zenlog("CGI POST DATA: " . $post_data );
#~ &zenlog("CGI PUT DATA: " . $put_data );

#####################################

#use JSON::XS;
$enabled = 1; # legacy

################################################################################
#
# Start [Method URI] calls
#
################################################################################

#~ GET '/test' => sub {
#~
	#~ &httpResponse({
		#~ http_code => 200,
		#~ body => { msg => 'hola' }
	#~ });
	#~
	#~ exit;
#~ };

#  OPTIONS PreAuth
OPTIONS qr{^.*} => sub {
	&httpResponse({ http_code => 200 });
};

#  GET CGISESSID
GET qr{^/session/login$} => sub {

	my $session = new CGI::Session( $cgi );

	if ( $session && ! $session->param( 'is_logged_in' ) )
	{
		my @credentials = &getAuthorizationCredentials();

		my ( $username, $password ) = @credentials;

		&zenlog("credentials: @credentials<");

		if ( &authenticateCredentials( @credentials ) )
		{
			# successful authentication
			&zenlog( "Login successful for username: $username" );

			$session->param( 'is_logged_in', 1 );
			$session->param( 'username', $username );
			$session->expire('is_logged_in', '+30m');

			my ( $header ) = split( "\r\n", $session->header() );
			my ( undef, $setcookie ) = split( ': ', $header );

			&httpResponse({
				http_code => 200,
				headers => { 'Set-cookie' => $setcookie },
			});
		}
		else # not validated credentials
		{
			&zenlog( "Login failed for username: $username" );

			$session->delete();
			$session->flush();

			&httpResponse({ http_code => 401 });
		}
	}

	exit;
};


#	Above this part are calls allowed without authentication
######################################################################
if ( not ( &validZapiKey() or &validCGISession() ) )
{
	&httpResponse({ http_code => 401 });
	exit;
}

#	SESSION LOGOUT
#

#  LOGOUT session
GET qr{^/session/logout$} => sub {
	if ( $cgi->http( 'Cookie' ) )
	{
		my $session = new CGI::Session( $cgi );

		if ( $session && $session->param( 'is_logged_in' ) )
		{
			my $username = $session->param( username );
			my $ip_addr  = $session->param( _SESSION_REMOTE_ADDR );

			&zenlog( "Logged out user $username from $ip_addr" );

			$session->delete();
			$session->flush();

			&httpResponse( { http_code => 200 } );

			exit;
		}
	}

	# with ZAPI key or expired cookie session
	&httpResponse( { http_code => 400 } );
	exit;
};

#	CERTIFICATES
#

#  POST activation certificate
POST qr{^/certificates/activation$} => sub {
	&upload_activation_certificate();
};

#	Check activation certificate
######################################################################
&checkActivationCertificate();

#  GET List SSL certificates
GET qr{^/certificates$} => sub {
	&certificates();
};

#  POST certificates
POST qr{^/certificates$} => sub {
	&upload_certs();
};

#  DELETE certificate
DELETE qr{^/certificates/(\w+\.\w+$)} => sub {
	&delete_certificate( $1 );
};

#	FARMS
#

#  GET List all farms
GET qr{^/farms$} => sub {
	&farms();
};

#  GET get farm info
GET qr{^/farms/(\w+$)} => sub {
	&farms_name();
};

#  POST new farm
POST qr{^/farms/(\w+$)} => sub {
	&new_farm( $1 );
};

#  POST new service
POST qr{^/farms/(\w+)/services$} => sub {
	&new_farm_service( $1 );
};

#  POST new zone
POST qr{^/farms/(\w+)/zones$} => sub {
	&new_farm_zone( $1 );
};

#  POST new backend
POST qr{^/farms/(\w+)/backends$} => sub {
	&new_farm_backend( $1 );
};

#  POST new zone resource
POST qr{^/farms/(\w+)/zoneresources$} => sub {
	&new_farm_zoneresource( $1 );
};

#  POST farm actions
POST qr{^/farms/(\w+)/actions$} => sub {
	&actions( $1 );
};

#  POST status backend actions
POST qr{^/farms/(\w+)/maintenance$} => sub {
	&maintenance( $1 );
};

#  DELETE farm
DELETE qr{^/farms/(\w+$)} => sub {
	&delete_farm( $1 );
};

#  DELETE farm certificate
DELETE qr{^/farms/(\w+)/deletecertificate/(\w+$)} => sub {
	&delete_farmcertificate( $1, $2 );
};

#  DELETE service
DELETE qr{^/farms/(\w+)/services/(\w+$)} => sub {
	&delete_service( $1, $2 );
};

#  DELETE zone
#DELETE qr{^/farms/(\w+)/zones/(.*+$)} => sub {
DELETE qr{^/farms/(\w+)/zones/(([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$)} => sub {
	&delete_zone( $1, $2 );
};

#  DELETE backend (TCP/UDP/L4XNAT/DATALINK)
DELETE qr{^/farms/(\w+)/backends/(\w+$)} => sub {
	&delete_backend( $1, $2 );
};

#  DELETE backend (HTTP/HTTPS/GSLB)
DELETE qr{^/farms/(\w+)/services/(\w+)/backends/(\w+$)} => sub {
	&delete_service_backend( $1, $2, $3 );
};

#  DELETE zone resource
DELETE qr{^/farms/(\w+)/zones/([a-z0-9].*-*.*\.[a-z0-9].*)/resources/(\w+$)} =>
  sub {
	&delete_zone_resource( $1, $2, $3 );
  };

#  PUT farm
PUT qr{^/farms/(\w+$)} => sub {
	&modify_farm( $1 );
};

#  PUT backend
PUT qr{^/farms/(\w+)/backends/(\w+$)} => sub {
	&modify_backends( $1, $2 );
};

#  PUT farmguardian
PUT qr{^/farms/(\w+)/fg$} => sub {
	&modify_farmguardian( $1 );
};

#  PUT resources
PUT qr{^/farms/(\w+)/resources/(\w+$)} => sub {
	&modify_resources( $1, $2 );
};

#  PUT zones
PUT qr{^/farms/(\w+)/zones/(.*+$)} => sub {
	&modify_zones( $1, $2 );
};

#  PUT services
PUT qr{^/farms/(\w+)/services/(\w+$)} => sub {
	&modify_services( $1, $2 );
};

#  POST add certificates
POST qr{^/farms/(\w+)/addcertificate$} => sub {
	&add_farmcertificate( $1 );
};

#  PUT change certificates
PUT qr{^/farms/(\w+)/changecertificate$} => sub {
	&change_farmcertificate( $1 );
};

#	NETWORK INTERFACES
#

#  GET interfaces
GET qr{^/interfaces$} => sub {
	&get_interface();
};

#  POST virtual interface
POST qr{^/addvini/(.*$)} => sub {
	&new_vini( $1 );
};

#  POST vlan interface
POST qr{^/addvlan/(.*$)} => sub {
	&new_vlan( $1 );
};

#  POST action interface
POST qr{^/ifaction/(.*+$)} => sub {
	&ifaction( $1 );
};

#  DELETE virtual interface (default)
DELETE qr{^/deleteif/(.*$)} => sub {
	&delete_interface( $1 );
};

#  PUT interface
PUT qr{^/modifyif/(.*$)} => sub {
	&modify_interface( $1 );
};

#	STATS
#

#  GET stats
GET qr{^/stats$} => sub {
	&stats();
};

#  GET stats mem
GET qr{^/stats/mem$} => sub {
	&stats_mem();
};

#  GET stats load
GET qr{^/stats/load$} => sub {
	&stats_load();
};

#  GET stats network
GET qr{^/stats/network$} => sub {
	&stats_network();
};

#  GET stats cpu
GET qr{^/stats/cpu$} => sub {
	&stats_cpu();
};

#  GET farm stats
GET qr{^/farms/(\w+)/stats$} => sub {
	&farm_stats( $1 );
};

#	GRAPHS
#

#  GET graphs
GET qr{^/graphs/(\w+)/(.*)/(\w+$)} => sub {
	&get_graphs( $1, $2, $3 );
};

#  GET possible graphs
GET qr{^/graphs} => sub {
	&possible_graphs();
};

&httpResponse({ http_code => 400 });
