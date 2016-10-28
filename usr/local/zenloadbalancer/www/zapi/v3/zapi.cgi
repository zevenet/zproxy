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

#~ use no warnings;
#~ use warnings;
#~ use strict;

#~ use CGI;
use CGI::Session;
#~ use CGI::Carp qw(warningsToBrowser fatalsToBrowser);
use MIME::Base64;
use JSON::XS;
use URI::Escape;

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
		204 => 'No Content',

		# 4xx Client Error codes
		400 => 'Bad Request',
		401 => 'Unauthorized',
		403 => 'Forbidden',
		404 => 'Not Found',
		406 => 'Not Acceptable',
		415 => 'Unsupported Media Type',
		422 => 'Unprocessable Entity',
	};
};

require "/usr/local/zenloadbalancer/config/global.conf";
require "/usr/local/zenloadbalancer/www/functions.cgi";
require "/usr/local/zenloadbalancer/www/cert_functions.cgi";
require "/usr/local/zenloadbalancer/www/cgi_functions.cgi";
require "/usr/local/zenloadbalancer/www/farms_functions.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/global.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/certificates.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/get.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/post.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/put.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/put_gslb.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/delete.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/delete_gslb.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/interface.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/system_stats.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/farm_guardian.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/farm_actions.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/post_gslb.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/ipds.cgi";  

my $q = &getCGI();

################################################################################
#
# Subroutines and HTTP methods
#
################################################################################

# build local key
sub keycert # ()
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
sub certcontrol # ()
{
	# requires:
	#~ use Sys::Hostname;
	#~ use Date::Parse;
	#~ use Time::localtime;

	my $basedir = &getGlobalConfiguration( 'basedir' );

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

		&httpResponse({ code => 400, body => { message => $message } });

		exit;
	}

	return $swcert;
}

sub GET($$)
{
	my ( $path, $code ) = @_;

	return unless $q->request_method eq 'GET' or $q->request_method eq 'HEAD';

	my @captures = $q->path_info =~ $path;
	return unless @captures;

	$code->( @captures );
}

sub POST($$)
{
	my ( $path, $code ) = @_;

	return unless $q->request_method eq 'POST';

	my @captures = $q->path_info =~ $path;
	return unless @captures;

	my $data = &getCgiParam( 'POSTDATA' );
	my $input_ref;

	if ( exists $ENV{ CONTENT_TYPE } && $ENV{ CONTENT_TYPE } eq 'application/json' )
	{
		$input_ref = eval{ decode_json( $data ) };
		&zenlog("json: ". Dumper $input_ref );
	}
	elsif ( exists $ENV{ CONTENT_TYPE } && $ENV{ CONTENT_TYPE } eq 'text/plain' )
	{
		$input_ref = $data;
	}
	else
	{
		&httpResponse({ code => 415 });
	}

	$code->( $input_ref, @captures );
}

sub PUT($$)
{
	my ( $path, $code ) = @_;

	return unless $q->request_method eq 'PUT';

	my @captures = $q->path_info =~ $path;
	return unless @captures;

	my $data = &getCgiParam( 'PUTDATA' );
	my $input_ref;

	if ( exists $ENV{ CONTENT_TYPE } && $ENV{ CONTENT_TYPE } eq 'application/json' )
	{
		$input_ref = eval{ decode_json( $data ) };
		&zenlog("json: ". Dumper $input_ref );
	}
	elsif ( exists $ENV{ CONTENT_TYPE } && $ENV{ CONTENT_TYPE } eq 'text/plain' )
	{
		$input_ref = $data;
	}
	else
	{
		&httpResponse({ code => 415 });
	}

	$code->( $input_ref, @captures );
}

sub DELETE($$)
{
	my ( $path, $code ) = @_;

	return unless $q->request_method eq 'DELETE';

	my @captures = $q->path_info =~ $path;
	return unless @captures;

	$code->( @captures );
}

sub OPTIONS($$)
{
	my ( $path, $code ) = @_;

	return unless $q->request_method eq 'OPTIONS';

	my @captures = $q->path_info =~ $path;
	return unless @captures;

	$code->( @captures );
}

sub logInput
{
	&zenlog("Input:(".join(', ', @_).")");
	&httpResponse({ code => 200 });
}

sub validCGISession # ()
{
	use CGI::Session;

	my $validSession = 0;
	my $session = CGI::Session->load( &getCGI() );

	&zenlog( "CGI SESSION ID: ".$session->id ) if $session->id;
	#~ &zenlog( "session data: " . Dumper $session->dataref() ); # DEBUG

	if ( $session && $session->param( 'is_logged_in' ) && ! $session->is_expired )
	{
		$session->expire('is_logged_in', '+30m');
		#~ $session->expire('is_logged_in', '+5s'); # DEBUG
		$validSession = 1;
	}

	return $validSession;
}

sub validZapiKey # ()
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

sub getAuthorizationCredentials # ()
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

		code - HTTP status code digit
		headers - optional hash reference of extra http headers to be included
		body - optional hash reference with data to be sent as JSON

	Returns:

		This function exits the execution uf the current process.
=cut
sub httpResponse # ( \%hash ) hash_keys->( code, headers, body )
{
	my $self = shift;

	#~ &zenlog("DEBUG httpResponse input: " . Dumper $self ); # DEBUG

	die 'httpResponse: Bad input' if !defined $self or ref $self ne 'HASH';

	die
	  if !defined $self->{ code }
	  or !exists $GLOBAL::http_status_codes->{ $self->{ code } };

	my $cgi = &getCGI();

	# Headers included in _ALL_ the responses, any method, any URI, sucess or error
	my @headers = (
					'Access-Control-Allow-Origin'      => $ENV{ HTTP_ORIGIN },
					'Access-Control-Allow-Credentials' => 'true',
	);

	if ( $ENV{ 'REQUEST_METHOD' } eq 'OPTIONS' )    # no session info received
	{
		push @headers,
		  'Access-Control-Allow-Methods'     => 'GET, POST, PUT, DELETE, OPTIONS',
		  'Access-Control-Allow-Headers' =>
		  'ZAPI_KEY, Authorization, Set-cookie, Content-Type, X-Requested-With',
		  ;
	}

	if ( &validCGISession() )
	{
		my $cgi            = &getCGI();
		my $session        = CGI::Session->load( $cgi );
		my $session_cookie = $cgi->cookie( CGISESSID => $session->id );

		push @headers,
		  'Set-Cookie'                       => $session_cookie,
		  'Access-Control-Expose-Headers'    => 'Set-Cookie',
		  ;
	}

	if ( $q->path_info =~ '/session' )
	{
		push @headers,
		  'Access-Control-Expose-Headers'    => 'Set-Cookie',
		  ;
	}

	# add possible extra headers
	if ( exists $self->{ headers } && ref $self->{ headers } eq 'HASH' )
	{
		push @headers, %{ $self->{ headers } };
	}

	# header
	my $content_type = 'application/json';
	$content_type = $self->{ type } if $self->{ type } && $self->{ body };

	my $output = $cgi->header(
		-type    => $content_type,
		-charset => 'utf-8',
		-status  => "$self->{ code } $GLOBAL::http_status_codes->{ $self->{ code } }",

		# extra headers
		@headers,
	);

	# body

	#~ my ( $body_ref ) = shift @_; # opcional
	if ( exists $self->{ body } )
	{
		if ( ref $self->{ body } eq 'HASH' )
		{
			my $json = JSON::XS->new->utf8->pretty( 1 );
			my $json_canonical = 1;
			$json->canonical( [$json_canonical] );

			$output .= $json->encode( $self->{ body } );
		}
		else
		{
			$output .= $self->{ body };
		}
	}

	#~ &zenlog( "Response:$output<" ); # DEBUG
	print $output;

	&zenlog( "STATUS:$self->{ code }" );

	exit;
}

#########################################
#
# Debugging messages
#
#########################################

&zenlog(">>>>>> CGI REQUEST: <$ENV{REQUEST_METHOD} $ENV{SCRIPT_URL}> <<<<<<");
&zenlog("HTTP HEADERS: " . join(', ', $q->http() ) );
&zenlog("HTTP_AUTHORIZATION: <$ENV{HTTP_AUTHORIZATION}>") if exists $ENV{HTTP_AUTHORIZATION};
&zenlog("HTTP_ZAPI_KEY: <$ENV{HTTP_ZAPI_KEY}>") if exists $ENV{HTTP_ZAPI_KEY};
#~ my $post_data = $q->param('POSTDATA');
#~ my $put_data = $q->param('PUTDATA');
#~
#~ #my $session = new CGI::Session( $q );
#~
#~ my $param_zapikey = $ENV{'HTTP_ZAPI_KEY'};
#~ my $param_session = new CGI::Session( $q );
#~
#~ my $param_client = $q->param('client');
#~
#~
#~ &zenlog("CGI PARAMS: " . Dumper $params );
#~ &zenlog("CGI OBJECT: " . Dumper $q );
#~ &zenlog("CGI VARS: " . Dumper $q->Vars() );
#~ &zenlog("PERL ENV: " . Dumper \%ENV );
#~ &zenlog("CGI POST DATA: " . $post_data );
#~ &zenlog("CGI PUT DATA: " . $put_data );

################################################################################
#
# Start [Method URI] calls
#
################################################################################

#  OPTIONS PreAuth
OPTIONS qr{^/.*$} => sub {
	&httpResponse({ code => 200 });
};

#  POST CGISESSID
POST qr{^/session$} => sub {

	my $session = new CGI::Session( &getCGI() );

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
			my ( undef, $session_cookie ) = split( ': ', $header );

			&httpResponse({
				code => 200,
				headers => { 'Set-cookie' => $session_cookie },
			});
		}
		else # not validated credentials
		{
			&zenlog( "Login failed for username: $username" );

			$session->delete();
			$session->flush();

			&httpResponse({ code => 401 });
		}
	}

	exit;
};


#	Above this part are calls allowed without authentication
######################################################################
if ( not ( &validZapiKey() or &validCGISession() ) )
{
	&httpResponse({ code => 401 });
}

#	SESSION LOGOUT
#

#  DELETE session
DELETE qr{^/session$} => sub {
	my $cgi = &getCGI();
	if ( $cgi->http( 'Cookie' ) )
	{
		my $session = new CGI::Session( $cgi );

		if ( $session && $session->param( 'is_logged_in' ) )
		{
			my $username = $session->param( 'username' );
			my $ip_addr  = $session->param( '_SESSION_REMOTE_ADDR' );

			&zenlog( "Logged out user $username from $ip_addr" );

			$session->delete();
			$session->flush();

			&httpResponse( { code => 200 } );
		}
	}

	# with ZAPI key or expired cookie session
	&httpResponse( { code => 400 } );
};

#	CERTIFICATES
#

#  POST activation certificate
POST qr{^/certificates/activation$} => sub {
	&upload_activation_certificate( @_ );
};

#	Check activation certificate
######################################################################
&checkActivationCertificate();

#  GET List SSL certificates
GET qr{^/certificates$} => sub {
	&certificates();
};

my $cert_re = &getValidFormat('certificate');
my $cert_pem_re = &getValidFormat('cert_pem');

#  Download SSL certificate
GET qr{^/certificates/($cert_re)$} => sub {
	&download_certificate( @_ );
};

#  GET SSL certificate information
GET qr{^/certificates/($cert_re)/info$} => sub {
	&get_certificate_info( @_ );
};

#  Create CSR certificates
POST qr{^/certificates$} => sub {
	&create_csr( @_ );
};

#  POST certificates
POST qr{^/certificates/($cert_pem_re)$} => sub {
	&upload_certs( @_ );
};

#  DELETE certificate
DELETE qr{^/certificates/($cert_re)$} => sub {
	&delete_certificate( @_ );
};

#	FARMS
#

my $farm_re = &getValidFormat('farm_name');

##### /farms

#  GET List all farms
GET qr{^/farms$} => sub {
	&farms();
};

#  POST new farm
POST qr{^/farms$} => sub {
	&new_farm( @_ );
};

##### /farms/FARM

#  GET get farm info
GET qr{^/farms/($farm_re)$} => sub {
	&farms_name( @_ );
};

#  POST new farm
POST qr{^/farms/($farm_re)$} => sub {
	&new_farm( @_ );
};

#  PUT farm
PUT qr{^/farms/($farm_re)$} => sub {
	&modify_farm( @_ );
};

#  DELETE farm
DELETE qr{^/farms/($farm_re)$} => sub {
	&delete_farm( @_ );
};


##### /farms/FARM/backends

#  GET backends list
GET qr{^/farms/($farm_re)/backends$} => sub {
	&backends( @_ );
};

#  POST new backend
POST qr{^/farms/($farm_re)/backends$} => sub {
	&new_farm_backend( @_ );
};

##### /farms/FARM/backends/BACKEND

my $be_re = &getValidFormat('backend');

#  PUT backend
PUT qr{^/farms/($farm_re)/backends/($be_re)$} => sub {
	&modify_backends( @_ );
};

#  DELETE backend (L4XNAT/DATALINK)
DELETE qr{^/farms/($farm_re)/backends/($be_re)$} => sub {
	&delete_backend( @_ );
};


##### /farms/FARM/services

#  POST new service
POST qr{^/farms/($farm_re)/services$} => sub {
	&new_farm_service( @_ );
};

##### /farms/FARM/services/SERVICE

my $service_re = &getValidFormat('service');

#  PUT service
PUT qr{^/farms/($farm_re)/services/($service_re)$} => sub {
	&modify_services( @_ );
};

#  DELETE service
DELETE qr{^/farms/($farm_re)/services/($service_re)$} => sub {
	&delete_service( @_ );
};

##### /farms/FARM/services/SERVICE/backends

#  GET service backends (HTTP/HTTPS/GSLB)
GET qr{^/farms/($farm_re)/services/($service_re)/backends$} => sub {
	&service_backends( @_ );
};

#  POST service backends (HTTP/HTTPS/GSLB)
POST qr{^/farms/($farm_re)/services/($service_re)/backends$} => sub {
	&new_service_backend( @_ );
};

##### /farms/FARM/services/SERVICE/backends/BACKEND

#  PUT backend (HTTP/HTTPS/GSLB)
PUT qr{^/farms/($farm_re)/services/($service_re)/backends/($be_re)$} => sub {
	&modify_service_backends( @_ );
};

#  DELETE backend (HTTP/HTTPS/GSLB)
DELETE qr{^/farms/($farm_re)/services/($service_re)/backends/($be_re)$} => sub {
	&delete_service_backend( @_ );
};


##### /farms/FARM/zones

#  POST new zone
POST qr{^/farms/($farm_re)/zones$} => sub {
	&new_farm_zone( @_ );
};

##### /farms/FARM/zones/ZONE

my $zone_re = &getValidFormat('zone');

#  PUT zones
PUT qr{^/farms/($farm_re)/zones/($zone_re)$} => sub {
	&modify_zones( @_ );
};

#  DELETE zone
#DELETE qr{^/farms/(\w+)/zones/(.*+$)} => sub {
DELETE qr{^/farms/($farm_re)/zones/($zone_re)$} => sub {
	&delete_zone( @_ );
};

##### /farms/FARM/zones/ZONE/resources

#  POST new zone resource
POST qr{^/farms/($farm_re)/zones/($zone_re)/resources$} => sub {
	&new_farm_zone_resource( @_ );
};

##### /farms/FARM/zones/ZONE/resources/RESOURCE

my $resource_id_re = &getValidFormat('resource_id');

#  PUT zone resources
PUT qr{^/farms/($farm_re)/zones/($zone_re)/resources/($resource_id_re)$} => sub {
	&modify_zone_resource( @_ );
};

#  DELETE zone resource
DELETE qr{^/farms/($farm_re)/zones/($zone_re)/resources/($resource_id_re)$} => sub {
	&delete_zone_resource( @_ );
};


##### /farms/FARM/actions
##### /farms/FARM/fg
##### /farms/FARM/maintenance

#  PUT farm actions
PUT qr{^/farms/($farm_re)/actions$} => sub {
	&farm_actions( @_ );
};

#  PUT farmguardian
PUT qr{^/farms/($farm_re)/fg$} => sub {
	&modify_farmguardian( @_ );
};

#  PUT status backend actions (for HTTP only)
PUT qr{^/farms/($farm_re)/services/($service_re)/backends/($be_re)/maintenance$} => sub {
	&service_backend_maintenance( @_ );
};


##### FARMS CERTIFICATES (HTTPS)
##### /farms/FARM/certificates

#  POST add certificates
POST qr{^/farms/($farm_re)/certificates$} => sub {
	&add_farmcertificate( @_ );
};

##### /farms/FARM/certificates/CERTIFICATE

#  DELETE farm certificate
DELETE qr{^/farms/($farm_re)/certificates/($cert_pem_re)$} => sub {
	&delete_farmcertificate( @_ );
};


#	NETWORK INTERFACES
#
my $virt_interface = &getValidFormat ('virt_interface');
my $vlan_interface = &getValidFormat ('vlan_interface');

##### /interfaces

#  GET interfaces
GET qr{^/interfaces$} => sub {
	&get_interfaces();
};

##### /interfaces/nic

#  GET interfaces nic
GET qr{^/interfaces/nic$} => sub {
	&get_interfaces_nic();
};

##### /interfaces/nic/NIC
my $nic_re = &getValidFormat ('nic_interface');

#  PUT interfaces nic
PUT qr{^/interfaces/nic/($nic_re)$} => sub {
	&modify_interface_nic( @_ );
};

#  DELETE interfaces nic
DELETE qr{^/interfaces/nic/($nic_re)$} => sub {
	&delete_interface_nic( @_ );
};

##### /interfaces/bonding

#  GET interfaces bonding
GET qr{^/interfaces/bonding$} => sub {
	&get_interfaces_bond();
};

##### /interfaces/vlan

#  GET interfaces vlan
GET qr{^/interfaces/vlan$} => sub {
	&get_interfaces_vlan();
};

#  POST vlan interface
POST qr{^/interfaces/vlan$} => sub {
	&new_vlan( @_ );
};

##### /interfaces/virtual

#  GET interfaces virtual
GET qr{^/interfaces/virtual$} => sub {
	&get_interfaces_virtual();
};

#  POST virtual interface
POST qr{^/interfaces/virtual$} => sub {
	&new_vini( @_ );
};

# FIXME: implement up/down in PUT method
#  POST action interface
#~ PUT qr{^/interfaces/(.+)$} => sub {
	#~ &ifaction( $1 );
#~ };

#  DELETE virtual interface (default)
DELETE qr{^/interfaces/($vlan_interface|$virt_interface)$} => sub {
	&delete_interface( @_ );
};

#  PUT interface
PUT qr{^/interfaces/($vlan_interface|$virt_interface)$} => sub {
	&modify_interface( @_ );
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
GET qr{^/stats/farms$} => sub {
	&all_farms_stats( @_ );
};

#  GET farm stats
GET qr{^/stats/farms/($farm_re)$} => sub {
	&farm_stats( @_ );
};

#	GRAPHS
#

#  GET graphs
GET qr{^/graphs/(\w+)/(.*)/(\w+$)} => sub {
	&get_graphs( @_ );
};

#  GET possible graphs
GET qr{^/graphs} => sub {
	&possible_graphs();
};


#	IPDS
#
ipds:

my $rbl_list = &getValidFormat('rbl_list_name');
my $rbl_source = &getValidFormat('rbl_source');

# RBL
#  GET all rbl lists
GET qr{^/ipds/rbl$} => sub {
	&get_rbl_all_lists;
};

#  GET rbl lists
GET qr{^/ipds/rbl/($rbl_list)$} => sub {
	&get_rbl_list ( @_ );
};

#  POST rbl list
POST qr{^/ipds/rbl/($rbl_list)$} => sub {
	&add_rbl_list ( @_ );
};

#  PUT rbl list
PUT qr{^/ipds/rbl/($rbl_list)$} => sub {
	&set_rbl_list ( @_ );
};

#  DELETE rbl list
DELETE qr{^/ipds/rbl/($rbl_list)$} => sub {
	&del_rbl_list ( @_ );
};

#  POST a source from a rbl list
POST qr{^/ipds/rbl/($rbl_list)/list} => sub {
	&add_rbl_source ( @_ );
};

#  PUT a source from a rbl list
PUT qr{^/ipds/rbl/($rbl_list)/list/($rbl_source$)} => sub {
	&set_rbl_source ( @_ );
};

#  DELETE a source from a rbl list
DELETE qr{^/ipds/rbl/($rbl_list)/list/($rbl_source$)} => sub {
	&del_rbl_source ( @_ );
};

#  POST list to farm
POST qr{^/farms/($farm_re)/ipds/rbl$} => sub {
	&add_rbl_to_farm ( @_ );
};

#  DELETE list from farm
DELETE qr{^/farms/($farm_re)/ipds/rbl/($rbl_list$)} => sub {
	&del_rbl_from_farm ( @_ );
};


# DDoS
#  GET ddos settings
GET qr{^/ipds/ddos$} => sub {
	&get_ddos ( @_ );
};

#  PUT ddos settings
PUT qr{^/ipds/ddos$} => sub {
	&set_ddos ( @_ );
};

#  GET status ddos for a farm
GET qr{^/farms/($farm_re)/ipds/ddos$} => sub {
	&get_ddos_farm ( @_ );
};

#  POST DDoS to a farm
POST qr{^/farms/($farm_re)/ipds/ddos$} => sub {
	&add_ddos_to_farm ( @_ );
};

#  DELETE DDoS from a farm
DELETE qr{^/farms/($farm_re)/ipds/ddos$} => sub {
	&del_ddos_from_farm ( @_ );
};



&httpResponse({
	code => 404,
	body => {
		message => 'Request not found',
		error => 'true', 
		}
	});

