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

use strict;

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

package GLOBAL
{
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

# all libs, tmp
require "/usr/local/zenloadbalancer/www/functions.cgi";

#~ require "/usr/local/zenloadbalancer/config/global.conf";
#~ require "/usr/local/zenloadbalancer/www/farms_functions.cgi";

# required
require "/usr/local/zenloadbalancer/www/zapi_functions.cgi";
require "/usr/local/zenloadbalancer/www/cgi_functions.cgi";
require "/usr/local/zenloadbalancer/www/cert_functions.cgi";

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
require "/usr/local/zenloadbalancer/www/zapi/v3/system.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v3/cluster.cgi";

my $q = &getCGI();

################################################################################
#
# Subroutines and HTTP methods
#
################################################################################

# build local key
sub keycert    # ()
{
	# requires:
	#~ use Sys::Hostname;

	my $dmidecode_bin = "/usr/sbin/dmidecode";    # input
	my $hostname      = &getHostname();           # input

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
sub certcontrol          # ()
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

		&httpResponse(
					   {
						 code => 403,
						 body => {
								   message         => $message,
								   certificate_key => &keycert(),
								   hostname        => &getHostname(),
						 }
					   }
		);

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
		$input_ref = eval { decode_json( $data ) };
		&zenlog( "json: " . Dumper $input_ref );
	}
	elsif ( exists $ENV{ CONTENT_TYPE } && $ENV{ CONTENT_TYPE } eq 'text/plain' )
	{
		$input_ref = $data;
	}
	elsif ( exists $ENV{ CONTENT_TYPE }
			&& $ENV{ CONTENT_TYPE } eq 'application/x-pem-file' )
	{
		$input_ref = $data;
	}
	else
	{
		&zenlog( "Content-Type not supported: $ENV{ CONTENT_TYPE }" );
		my $body = { message => 'Content-Type not supported', error => 'true' };

		&httpResponse( { code => 415, body => $body } );
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
		$input_ref = eval { decode_json( $data ) };
		&zenlog( "json: " . Dumper $input_ref );
	}
	elsif ( exists $ENV{ CONTENT_TYPE } && $ENV{ CONTENT_TYPE } eq 'text/plain' )
	{
		$input_ref = $data;
	}
	elsif ( exists $ENV{ CONTENT_TYPE }
			&& $ENV{ CONTENT_TYPE } eq 'application/x-pem-file' )
	{
		$input_ref = $data;
	}
	else
	{
		&zenlog( "Content-Type not supported: $ENV{ CONTENT_TYPE }" );
		my $body = { message => 'Content-Type not supported', error => 'true' };

		&httpResponse( { code => 415, body => $body } );
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
	&zenlog( "Input:(" . join ( ', ', @_ ) . ")" );
	&httpResponse( { code => 200 } );
}

sub validCGISession    # ()
{
	use CGI::Session;

	my $validSession = 0;
	my $session      = CGI::Session->load( &getCGI() );

	&zenlog( "CGI SESSION ID: " . $session->id ) if $session->id;

	#~ &zenlog( "session data: " . Dumper $session->dataref() ); # DEBUG

	if ( $session && $session->param( 'is_logged_in' ) && !$session->is_expired )
	{
		$session->expire( 'is_logged_in', '+30m' );

		#~ $session->expire('is_logged_in', '+5s'); # DEBUG
		$validSession = 1;
	}

	return $validSession;
}

sub validZapiKey    # ()
{
	my $validKey = 0;    # output

	my $key = "HTTP_ZAPI_KEY";

	if (
		 exists $ENV{ $key }                         # exists
		 && &getZAPI( "keyzapi" ) eq $ENV{ $key }    # matches key
		 && &getZAPI( "status" ) eq "true"
	  )                                             # zapi user enabled??
	{
		$validKey = 1;
	}

	return $validKey;
}

sub getAuthorizationCredentials                     # ()
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

	return undef if !$username or !$password;
	return ( $username, $password );
}

sub authenticateCredentials    #($user,$curpasswd)
{
	my ( $user, $pass ) = @_;

	return undef if !defined $user or !defined $pass;

	use Authen::Simple::Passwd;

	#~ use Authen::Simple::PAM;

	my $valid_credentials = 0;    # output

	my $passfile = "/etc/shadow";
	my $simple = Authen::Simple::Passwd->new( path => "$passfile" );

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

sub httpResponse    # ( \%hash ) hash_keys->( code, headers, body )
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
		  'Access-Control-Allow-Methods' => 'GET, POST, PUT, DELETE, OPTIONS',
		  'Access-Control-Allow-Headers' =>
		  'ZAPI_KEY, Authorization, Set-cookie, Content-Type, X-Requested-With',
		  ;
	}

	if ( &validCGISession() )
	{
		my $session = CGI::Session->load( $cgi );
		my $session_cookie = $cgi->cookie( CGISESSID => $session->id );

		push @headers,
		  'Set-Cookie'                    => $session_cookie,
		  'Access-Control-Expose-Headers' => 'Set-Cookie',
		  ;
	}

	if ( $q->path_info =~ '/session' )
	{
		push @headers,
		  'Access-Control-Expose-Headers' => 'Set-Cookie',
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
			my $json           = JSON::XS->new->utf8->pretty( 1 );
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

	&zenlog( "STATUS: $self->{ code }" );
	if ( ref $self->{ body } eq 'HASH' )
	{
		&zenlog( "MESSAGE: $self->{ body }->{ message }" )
		  if ( exists $self->{ body }->{ message } );
	}
	&zenlog( "MEMORY: " . &getMemoryUsage );

	exit;
}

#########################################
#
# Debugging messages
#
#########################################

&zenlog( ">>>>>> CGI REQUEST: <$ENV{REQUEST_METHOD} $ENV{SCRIPT_URL}> <<<<<<" );
&zenlog( "HTTP HEADERS: " . join ( ', ', $q->http() ) );
&zenlog( "HTTP_AUTHORIZATION: <$ENV{HTTP_AUTHORIZATION}>" )
  if exists $ENV{ HTTP_AUTHORIZATION };
&zenlog( "HTTP_ZAPI_KEY: <$ENV{HTTP_ZAPI_KEY}>" )
  if exists $ENV{ HTTP_ZAPI_KEY };

my $post_data = $q->param( 'POSTDATA' );
my $put_data  = $q->param( 'PUTDATA' );

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
&zenlog( "CGI POST DATA: " . $post_data ) if $post_data;
&zenlog( "CGI PUT DATA: " . $put_data )   if $put_data;

################################################################################
#
# Start [Method URI] calls
#
################################################################################

#  OPTIONS PreAuth
OPTIONS qr{^/.*$} => sub {
	&httpResponse( { code => 200 } );
};

#  POST CGISESSID
POST qr{^/session$} => sub {

	my $session = new CGI::Session( &getCGI() );

	if ( $session && !$session->param( 'is_logged_in' ) )
	{
		my @credentials = &getAuthorizationCredentials();

		my ( $username, $password ) = @credentials;

		&zenlog( "credentials: @credentials<" );

		if ( &authenticateCredentials( @credentials ) )
		{
			# successful authentication
			&zenlog( "Login successful for username: $username" );

			$session->param( 'is_logged_in', 1 );
			$session->param( 'username',     $username );
			$session->expire( 'is_logged_in', '+30m' );

			my ( $header ) = split ( "\r\n", $session->header() );
			my ( undef, $session_cookie ) = split ( ': ', $header );

			&httpResponse(
						   {
							 code    => 200,
							 headers => { 'Set-cookie' => $session_cookie },
						   }
			);
		}
		else    # not validated credentials
		{
			&zenlog( "Login failed for username: $username" );

			$session->delete();
			$session->flush();

			&httpResponse( { code => 401 } );
		}
	}

	exit;
};

#	Above this part are calls allowed without authentication
######################################################################
if ( not ( &validZapiKey() or &validCGISession() ) )
{
	&httpResponse(
				   { code => 401, body => { message => 'Authorization required' } } );
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
_certificates:

#  POST activation certificate
POST qr{^/certificates/activation$} => sub {
	&upload_activation_certificate( @_ );
};

#	Check activation certificate
######################################################################
&checkActivationCertificate();

my $cert_re     = &getValidFormat( 'certificate' );
my $cert_pem_re = &getValidFormat( 'cert_pem' );

#  GET List SSL certificates
GET qr{^/certificates$} => sub {
	&certificates();
};

#  GET activation certificate
GET qr{^/certificates/activation$} => sub {
	&get_activation_certificate_info( @_ );
};

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

#  DELETE activation certificate
DELETE qr{^/certificates/activation$} => sub {
	&delete_activation_certificate( @_ );
};

#  DELETE certificate
DELETE qr{^/certificates/($cert_re)$} => sub {
	&delete_certificate( @_ );
};

#	FARMS
#
_farms:

my $farm_re = &getValidFormat( 'farm_name' );

##### /farms

GET qr{^/farms$} => sub {
	&farms();
};

POST qr{^/farms$} => sub {
	&new_farm( @_ );
};

##### /farms

GET qr{^/farms/modules/lslb$} => sub {
	&farms_lslb();
};

GET qr{^/farms/modules/gslb$} => sub {
	&farms_gslb();
};

GET qr{^/farms/modules/dslb$} => sub {
	&farms_dslb();
};

##### /farms/FARM

GET qr{^/farms/($farm_re)$} => sub {
	&farms_name( @_ );
};

PUT qr{^/farms/($farm_re)$} => sub {
	&modify_farm( @_ );
};

DELETE qr{^/farms/($farm_re)$} => sub {
	&delete_farm( @_ );
};

##### /farms/FARM/backends

GET qr{^/farms/($farm_re)/backends$} => sub {
	&backends( @_ );
};

POST qr{^/farms/($farm_re)/backends$} => sub {
	&new_farm_backend( @_ );
};

##### /farms/FARM/backends/BACKEND

my $be_re = &getValidFormat( 'backend' );

PUT qr{^/farms/($farm_re)/backends/($be_re)$} => sub {
	&modify_backends( @_ );
};

DELETE qr{^/farms/($farm_re)/backends/($be_re)$} => sub {
	&delete_backend( @_ );
};

##### /farms/FARM/services

POST qr{^/farms/($farm_re)/services$} => sub {
	&new_farm_service( @_ );
};

##### /farms/FARM/services/SERVICE

my $service_re = &getValidFormat( 'service' );

POST qr{^/farms/($farm_re)/services/($service_re)/actions$} => sub {
	&move_services( @_ );
};

PUT qr{^/farms/($farm_re)/services/($service_re)$} => sub {
	&modify_services( @_ );
};

DELETE qr{^/farms/($farm_re)/services/($service_re)$} => sub {
	&delete_service( @_ );
};

##### /farms/FARM/services/SERVICE/backends

GET qr{^/farms/($farm_re)/services/($service_re)/backends$} => sub {
	&service_backends( @_ );
};

POST qr{^/farms/($farm_re)/services/($service_re)/backends$} => sub {
	&new_service_backend( @_ );
};

##### /farms/FARM/services/SERVICE/backends/BACKEND

PUT qr{^/farms/($farm_re)/services/($service_re)/backends/($be_re)$} => sub {
	&modify_service_backends( @_ );
};

DELETE qr{^/farms/($farm_re)/services/($service_re)/backends/($be_re)$} => sub {
	&delete_service_backend( @_ );
};

##### /farms/FARM/zones

POST qr{^/farms/($farm_re)/zones$} => sub {
	&new_farm_zone( @_ );
};

##### /farms/FARM/zones/ZONE

my $zone_re = &getValidFormat( 'zone' );

PUT qr{^/farms/($farm_re)/zones/($zone_re)$} => sub {
	&modify_zones( @_ );
};

DELETE qr{^/farms/($farm_re)/zones/($zone_re)$} => sub {
	&delete_zone( @_ );
};

##### /farms/FARM/zones/ZONE/resources

GET qr{^/farms/($farm_re)/zones/($zone_re)/resources$} => sub {
	&gslb_zone_resources( @_ );
};

POST qr{^/farms/($farm_re)/zones/($zone_re)/resources$} => sub {
	&new_farm_zone_resource( @_ );
};

##### /farms/FARM/zones/ZONE/resources/RESOURCE

my $resource_id_re = &getValidFormat( 'resource_id' );

PUT qr{^/farms/($farm_re)/zones/($zone_re)/resources/($resource_id_re)$} =>
  sub {
	&modify_zone_resource( @_ );
  };

DELETE qr{^/farms/($farm_re)/zones/($zone_re)/resources/($resource_id_re)$} =>
  sub {
	&delete_zone_resource( @_ );
  };

##### /farms/FARM/actions
##### /farms/FARM/fg
##### /farms/FARM/maintenance

PUT qr{^/farms/($farm_re)/actions$} => sub {
	&farm_actions( @_ );
};

PUT qr{^/farms/($farm_re)/fg$} => sub {
	&modify_farmguardian( @_ );
};

PUT qr{^/farms/($farm_re)/services/($service_re)/backends/($be_re)/maintenance$}
  => sub {
	&service_backend_maintenance( @_ );
  };    #  (HTTP only)

PUT qr{^/farms/($farm_re)/backends/($be_re)/maintenance$} => sub {
	&backend_maintenance( @_ );
};      #  (L4xNAT only)

##### FARMS CERTIFICATES (HTTPS)

##### /farms/FARM/certificates

POST qr{^/farms/($farm_re)/certificates$} => sub {
	&add_farm_certificate( @_ );
};

##### /farms/FARM/certificates/CERTIFICATE

DELETE qr{^/farms/($farm_re)/certificates/($cert_pem_re)$} => sub {
	&delete_farm_certificate( @_ );
};

#	NETWORK INTERFACES
#
_interfaces:

my $virt_interface = &getValidFormat( 'virt_interface' );
my $vlan_interface = &getValidFormat( 'vlan_interface' );
my $nic_re         = &getValidFormat( 'nic_interface' );

GET qr{^/interfaces$} => sub {
	&get_interfaces();
};

##### /interfaces/nic

GET qr{^/interfaces/nic$} => sub {
	&get_nic_list();
};

##### /interfaces/nic/NIC

GET qr{^/interfaces/nic/($nic_re)$} => sub {
	&get_nic( @_ );
};

PUT qr{^/interfaces/nic/($nic_re)$} => sub {
	&modify_interface_nic( @_ );
};

DELETE qr{^/interfaces/nic/($nic_re)$} => sub {
	&delete_interface_nic( @_ );
};

##### /interfaces/nic/NIC/actions

POST qr{^/interfaces/nic/($nic_re)/actions$} => sub {
	&actions_interface_nic( @_ );
};

##### /interfaces/vlan

GET qr{^/interfaces/vlan$} => sub {
	&get_vlan_list();
};

POST qr{^/interfaces/vlan$} => sub {
	&new_vlan( @_ );
};

##### /interfaces/vlan/VLAN

GET qr{^/interfaces/vlan/($vlan_interface)$} => sub {
	&get_vlan( @_ );
};

PUT qr{^/interfaces/vlan/($vlan_interface)$} => sub {
	&modify_interface_vlan( @_ );
};

DELETE qr{^/interfaces/vlan/($vlan_interface)$} => sub {
	&delete_interface_vlan( @_ );
};

##### /interfaces/vlan/VLAN/actions

POST qr{^/interfaces/vlan/($vlan_interface)/actions$} => sub {
	&actions_interface_vlan( @_ );
};

##### /interfaces/virtual

GET qr{^/interfaces/virtual$} => sub {
	&get_virtual_list();
};

POST qr{^/interfaces/virtual$} => sub {
	&new_vini( @_ );
};

##### /interfaces/virtual/VIRTUAL

GET qr{^/interfaces/virtual/($virt_interface)$} => sub {
	&get_virtual( @_ );
};

PUT qr{^/interfaces/virtual/($virt_interface)$} => sub {
	&modify_interface_virtual( @_ );
};

DELETE qr{^/interfaces/virtual/($virt_interface)$} => sub {
	&delete_interface_virtual( @_ );
};

##### /interfaces/virtual/VIRTUAL/actions

POST qr{^/interfaces/virtual/($virt_interface)/actions$} => sub {
	&actions_interface_virtual( @_ );
};

##### /interfaces/bonding

GET qr{^/interfaces/bonding$} => sub {
	&get_bond_list();
};

POST qr{^/interfaces/bonding$} => sub {
	&new_bond( @_ );
};

##### /interfaces/bonding/BOND
my $bond_re = &getValidFormat( 'bond_interface' );

GET qr{^/interfaces/bonding/($bond_re)$} => sub {
	&get_bond( @_ );
};

PUT qr{^/interfaces/bonding/($bond_re)$} => sub {
	&modify_interface_bond( @_ );
};

DELETE qr{^/interfaces/bonding/($bond_re)$} => sub {
	&delete_interface_bond( @_ );
};

##### /interfaces/bonding/BOND/slaves

POST qr{^/interfaces/bonding/($bond_re)/slaves$} => sub {
	&new_bond_slave( @_ );
};

##### /interfaces/bonding/BOND/slaves/SLAVE

DELETE qr{^/interfaces/bonding/($bond_re)/slaves/($nic_re)$} => sub {
	&delete_bond_slave( @_ );
};

##### /interfaces/bonding/BOND/actions

POST qr{^/interfaces/bonding/($bond_re)/actions$} => sub {
	&actions_interface_bond( @_ );
};

##### /interfaces/floating

GET qr{^/interfaces/floating$} => sub {
	&get_interfaces_floating( @_ );
};

##### /interfaces/floating/FLOATING

GET qr{^/interfaces/floating/($nic_re|$bond_re|$vlan_interface)$} => sub {
	&get_floating( @_ );
};

PUT qr{^/interfaces/floating/($nic_re|$bond_re|$vlan_interface)$} => sub {
	&modify_interface_floating( @_ );
};

DELETE qr{^/interfaces/floating/($nic_re|$bond_re|$vlan_interface)$} => sub {
	&delete_interface_floating( @_ );
};

##### /interfaces/gateway

GET qr{^/interfaces/gateway$} => sub {
	&get_gateway( @_ );
};

PUT qr{^/interfaces/gateway$} => sub {
	&modify_gateway( @_ );
};

DELETE qr{^/interfaces/gateway$} => sub {
	&delete_gateway( @_ );
};

#	STATS
#
_stats:

# System stats
GET qr{^/stats$} => sub {
	&stats();
};

GET qr{^/stats/system/memory$} => sub {
	&stats_mem();
};

GET qr{^/stats/system/load$} => sub {
	&stats_load();
};

GET qr{^/stats/system/network$} => sub {
	&stats_network();
};

GET qr{^/stats/system/network/interfaces$} => sub {
	&stats_network_interfaces();
};

GET qr{^/stats/system/cpu$} => sub {
	&stats_cpu();
};

GET qr{^/stats/system/connections$} => sub {
	&stats_conns();
};


# Farm stats
my $modules_re = &getValidFormat( 'farm_modules' );
GET qr{^/stats/farms$} => sub {
	&all_farms_stats( @_ );
};

GET qr{^/stats/farms/modules$} => sub {
	&module_stats_status( @_ );
};

GET qr{^/stats/farms/modules/($modules_re)$} => sub {
	&module_stats( @_ );
};

GET qr{^/stats/farms/($farm_re)$} => sub {
	&farm_stats( @_ );
};

GET qr{^/stats/farms/($farm_re)/backends$} => sub {
	&farm_stats( @_ );
};

GET qr{^/stats/farms/($farm_re)/service/($service_re)/backends$} => sub {
	&farm_stats( @_ );
};

#	GRAPHS
#
_graphs:

my $frequency_re = &getValidFormat( 'graphs_frequency' );
my $system_id_re = &getValidFormat( 'graphs_system_id' );

#  GET graphs
#~ GET qr{^/graphs/(\w+)/(.*)/(\w+$)} => sub {
#~ &get_graphs( @_ );
#~ };

#  GET possible graphs
GET qr{^/graphs$} => sub {
	&possible_graphs();
};

##### /graphs/system
#  GET all possible system graphs
GET qr{^/graphs/system$} => sub {
	&get_all_sys_graphs();
};

#  GET system graphs
GET qr{^/graphs/system/($system_id_re)$} => sub {
	&get_sys_graphs( @_ );
};

#  GET frequency system graphs
GET qr{^/graphs/system/($system_id_re)/($frequency_re)$} => sub {
	&get_frec_sys_graphs( @_ );
};

##### /graphs/system/disk

# $disk_re includes 'root' at the beginning
my $disk_re = &getValidFormat( 'mount_point' );

GET qr{^/graphs/system/disk$} => sub {
	&list_disks( @_ );
};

# keep before next request
GET qr{^/graphs/system/disk/($disk_re)/($frequency_re)$} => sub {
	&graph_disk_mount_point_freq( @_ );
};

GET qr{^/graphs/system/disk/($disk_re)$} => sub {
	&graphs_disk_mount_point_all( @_ );
};

##### /graphs/interfaces

#  GET all posible interfaces graphs
GET qr{^/graphs/interfaces$} => sub {
	&get_all_iface_graphs( @_ );
};

#  GET interfaces graphs
GET qr{^/graphs/interfaces/($nic_re|$vlan_interface)$} => sub {
	&get_iface_graphs( @_ );
};

#  GET frequency interfaces graphs
GET qr{^/graphs/interfaces/($nic_re)/($frequency_re)$} => sub {
	&get_frec_iface_graphs( @_ );
};

##### /graphs/farms

#  GET all posible farm graphs
GET qr{^/graphs/farms$} => sub {
	&get_all_farm_graphs( @_ );
};

#  GET farm graphs
GET qr{^/graphs/farms/($farm_re)$} => sub {
	&get_farm_graphs( @_ );
};

#  GET frequency farm graphs
GET qr{^/graphs/farms/($farm_re)/($frequency_re)$} => sub {
	&get_frec_farm_graphs( @_ );
};

# SYSTEM
#
_system:

#  GET version
GET qr{^/system/version$} => sub {
	&get_version;
};

#  GET dns
GET qr{^/system/dns$} => sub {
	&get_dns;
};

#  POST dns
POST qr{^/system/dns$} => sub {
	&set_dns( @_ );
};

#  GET ssh
GET qr{^/system/ssh$} => sub {
	&get_ssh;
};

#  POST ssh
POST qr{^/system/ssh$} => sub {
	&set_ssh( @_ );
};

#  GET snmp
GET qr{^/system/snmp$} => sub {
	&get_snmp;
};

#  POST snmp
POST qr{^/system/snmp$} => sub {
	&set_snmp( @_ );
};

my $license_re = &getValidFormat( 'license_format' );

#  GET license
GET qr{^/system/license/($license_re)$} => sub {
	&get_license( @_ );
};

#  GET ntp
GET qr{^/system/ntp$} => sub {
	&get_ntp;
};

#  POST ntp
POST qr{^/system/ntp$} => sub {
	&set_ntp( @_ );
};

#  GET http
GET qr{^/system/http$} => sub {
	&get_http;
};

#  POST http
POST qr{^/system/http$} => sub {
	&set_http( @_ );
};

my $user_re = &getValidFormat( 'user' );

#  GET users
GET qr{^/system/users$} => sub {
	&get_all_users;
};

#  GET user settings
GET qr{^/system/users/($user_re)$} => sub {
	&get_user;
};

#  POST zapi user
POST qr{^/system/users/zapi$} => sub {
	&set_user_zapi( @_ );
};

#  POST other user
POST qr{^/system/users/($user_re)$} => sub {
	&set_user( @_ );
};

my $logs_re = &getValidFormat( 'log' );

#  GET logs
GET qr{^/system/logs$} => sub {
	&get_logs;
};

#  GET download log file
GET qr{^/system/logs/($logs_re)$} => sub {
	&download_logs;
};

_system_backup:

# BACKUPS
my $backup_re = &getValidFormat( 'backup' );

#  GET list backups
GET qr{^/system/backup$} => sub {
	&get_backup( @_ );
};

#  POST create backups
POST qr{^/system/backup$} => sub {
	&create_backup( @_ );
};

#  GET download backups
GET qr{^/system/backup/($backup_re)$} => sub {
	&download_backup( @_ );
};

#  PUT  upload backups
PUT qr{^/system/backup/($backup_re)$} => sub {
	&upload_backup( @_ );
};

#  DELETE  backups
DELETE qr{^/system/backup/($backup_re)$} => sub {
	&del_backup( @_ );
};

#  POST  apply backups
POST qr{^/system/backup/($backup_re)/actions$} => sub {
	&apply_backup( @_ );
};

_system_notifications:

# NOTIFICATIONS
my $alert_re  = &getValidFormat( 'notif_alert' );
my $method_re = &getValidFormat( 'notif_method' );

#  GET notification methods
GET qr{^/system/notifications/methods/($method_re)$} => sub {
	&get_notif_methods( @_ );
};

#  POST notification methods
POST qr{^/system/notifications/methods/($method_re)$} => sub {
	&set_notif_methods( @_ );
};

#  GET notification alert status
GET qr{^/system/notifications/alerts$} => sub {
	&get_notif_alert_status( @_ );
};

#  GET notification alerts
GET qr{^/system/notifications/alerts/($alert_re)$} => sub {
	&get_notif_alert( @_ );
};

#  POST notification alerts
POST qr{^/system/notifications/alerts/($alert_re)$} => sub {
	&set_notif_alert( @_ );
};

#  POST notification alert actions
POST qr{^/system/notifications/alerts/($alert_re)/actions$} => sub {
	&set_notif_alert_actions( @_ );
};

#  POST  notifications test
POST qr{^/system/notifications/methods/email/actions$} => sub {
	&send_test_mail( @_ );
};

#### /system/cluster
_cluster:
GET qr{^/system/cluster$} => sub {
	&get_cluster( @_ );
};

POST qr{^/system/cluster$} => sub {
	&enable_cluster( @_ );
};

PUT qr{^/system/cluster$} => sub {
	&modify_cluster( @_ );
};

DELETE qr{^/system/cluster$} => sub {
	&disable_cluster( @_ );
};

POST qr{^/system/cluster/actions$} => sub {
	&set_cluster_actions( @_ );
};

GET qr{^/system/cluster/nodes$} => sub {
	&get_cluster_nodes_status( @_ );
};

GET qr{^/system/cluster/nodes/localhost$} => sub {
	&get_cluster_localhost_status( @_ );
};

#### /system/supportsave

GET qr{^/system/supportsave$} => sub {
	&get_supportsave( @_ );
};

#	IPDS
#
_ipds:

my $blacklists_list      = &getValidFormat( 'blacklists_name' );
my $blacklists_source_id = &getValidFormat( 'blacklists_source_id' );

# BLACKLISTS
#  GET all blacklists
GET qr{^/ipds/blacklists$} => sub {
	&get_blacklists_all_lists;
};

#  POST blacklists list
POST qr{^/ipds/blacklists$} => sub {
	&add_blacklists_list( @_ );
};

#  GET blacklists lists
GET qr{^/ipds/blacklists/($blacklists_list)$} => sub {
	&get_blacklists_list( @_ );
};

#  PUT blacklists list
PUT qr{^/ipds/blacklists/($blacklists_list)$} => sub {
	&set_blacklists_list( @_ );
};

#  DELETE blacklists list
DELETE qr{^/ipds/blacklists/($blacklists_list)$} => sub {
	&del_blacklists_list( @_ );
};

#  UPDATE a remote blacklists
POST qr{^/ipds/blacklists/($blacklists_list)/actions$} => sub {
	&update_remote_blacklists( @_ );
};

#  GET a source from a blacklists
GET qr{^/ipds/blacklists/($blacklists_list)/sources$} => sub {
	&get_blacklists_source( @_ );
};

#  POST a source from a blacklists
POST qr{^/ipds/blacklists/($blacklists_list)/sources$} => sub {
	&add_blacklists_source( @_ );
};

#  PUT a source from a blacklists
PUT qr{^/ipds/blacklists/($blacklists_list)/sources/($blacklists_source_id)$} =>
  sub {
	&set_blacklists_source( @_ );
  };

#  DELETE a source from a blacklists
DELETE
  qr{^/ipds/blacklists/($blacklists_list)/sources/($blacklists_source_id)$} =>
  sub {
	&del_blacklists_source( @_ );
  };

#  POST list to farm
POST qr{^/farms/($farm_re)/ipds/blacklists$} => sub {
	&add_blacklists_to_farm( @_ );
};

#  DELETE list from farm
DELETE qr{^/farms/($farm_re)/ipds/blacklists/($blacklists_list)$} => sub {
	&del_blacklists_from_farm( @_ );
};

# DoS
my $dos_rule = &getValidFormat( 'dos_name' );

#  GET dos settings
GET qr{^/ipds/dos/rules$} => sub {
	&get_dos_rules( @_ );
};

#  GET dos settings
GET qr{^/ipds/dos$} => sub {
	&get_dos( @_ );
};

#  GET dos configuration
GET qr{^/ipds/dos/($dos_rule)$} => sub {
	&get_dos_rule( @_ );
};

#  POST dos settings
POST qr{^/ipds/dos$} => sub {
	&create_dos_rule( @_ );
};

#  PUT dos rule
PUT qr{^/ipds/dos/($dos_rule)$} => sub {
	&set_dos_rule( @_ );
};

#  DELETE dos rule
DELETE qr{^/ipds/dos/($dos_rule)$} => sub {
	&del_dos_rule( @_ );
};

#  POST DoS to a farm
POST qr{^/farms/($farm_re)/ipds/dos$} => sub {
	&add_dos_to_farm( @_ );
};

#  DELETE DoS from a farm
DELETE qr{^/farms/($farm_re)/ipds/dos/($dos_rule)$} => sub {
	&del_dos_from_farm( @_ );
};

&httpResponse(
			   {
				 code => 404,
				 body => {
						   message => 'Request not found',
						   error   => 'true',
				 }
			   }
);

