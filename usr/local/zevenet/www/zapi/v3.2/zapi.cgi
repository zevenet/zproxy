#!/usr/bin/perl
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
use warnings;

use Zevenet::Log;
use Zevenet::Debug;
use Zevenet::CGI;
use Zevenet::API32::HTTP;
use Crypt::CBC;
use POSIX 'strftime';

my $q = &getCGI();

##### Debugging messages #############################################
#
#~ use Data::Dumper;
#~ $Data::Dumper::Sortkeys = 1;
#
#~ if ( debug() )
#~ {
#~ &zenlog( "REQUEST: $ENV{REQUEST_METHOD} $ENV{SCRIPT_URL}" ) if &debug;
#~ &zenlog( ">>>>>> CGI REQUEST: <$ENV{REQUEST_METHOD} $ENV{SCRIPT_URL}> <<<<<<" ) if &debug;
#~ &zenlog( "HTTP HEADERS: " . join ( ', ', $q->http() ) );
#~ &zenlog( "HTTP_AUTHORIZATION: <$ENV{HTTP_AUTHORIZATION}>" )
#~ if exists $ENV{ HTTP_AUTHORIZATION };
#~ &zenlog( "HTTP_ZAPI_KEY: <$ENV{HTTP_ZAPI_KEY}>" )
#~ if exists $ENV{ HTTP_ZAPI_KEY };
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
#~
#~
#~ my $post_data = $q->param( 'POSTDATA' );
#~ my $put_data  = $q->param( 'PUTDATA' );
#~
#~ &zenlog( "CGI POST DATA: " . $post_data ) if $post_data && &debug && $ENV{ CONTENT_TYPE } eq 'application/json';
#~ &zenlog( "CGI PUT DATA: " . $put_data )   if $put_data && &debug && $ENV{ CONTENT_TYPE } eq 'application/json';
#~ }

##### OPTIONS method request #########################################
require Zevenet::API32::Routes::Options
  if ( $ENV{ REQUEST_METHOD } eq 'OPTIONS' );

##### Load more basic modules ########################################
require Zevenet::Config;
require Zevenet::Validate;

##### Authentication #################################################
require Zevenet::API32::Auth;

# Session request
require Zevenet::API32::Routes::Session if ( $q->path_info eq '/session' );

# Verify authentication
unless (    ( exists $ENV{ HTTP_ZAPI_KEY } && &validZapiKey() )
		 or ( exists $ENV{ HTTP_COOKIE } && &validCGISession() ) )
{
	&httpResponse(
				   { code => 401, body => { message => 'Authorization required' } } );
}

##### Activation certificates ########################################
require Zevenet::SystemInfo;

require Zevenet::API32::Routes::Activation
  if ( $q->path_info eq '/certificates/activation' );

# Check activation certificate
&checkActivationCertificate();

# Verify RBAC permissions
require Zevenet::Core;
require Zevenet::RBAC::Core;
if ( !&getRBACPathPermissions( $q->path_info,  $ENV{REQUEST_METHOD} ) )
{
	require Zevenet::User;
	my $username = &getUser();
	my $desc = "RBAC auth";
	&httpErrorResponse(
						code => 403,
						desc => $desc,
						msg  => "The user $username has not permissions"
	);
}

##### Load API routes ################################################
require Zevenet::API32::Routes;

my $desc = 'Request not found';
my $req  = $ENV{ PATH_INFO };

&httpErrorResponse( code => 404, desc => $desc, msg => "$desc: $req" );

### Activation certificate code ############
use Time::Local;

#build CBC Object
sub buildcbc
{
	my $cipher = Crypt::CBC->new(
		-literal_key => 1,
		-key => 'wg2kx8VY2NVYDdQSAdqffmHYMd2d97ypYdJ4hwczAm8YBPtHv28EJJ66',
		-cipher => 'Blowfish',
		-iv => 'r5JLLw4f',
		-header => 'none',
		-padding => 'null'
	);

	return $cipher;
}

#encrypt CBC and return result
sub encrypt # string for encrypt
{
	my $data = shift;

	my $cipher = &buildcbc();
	my $result = $cipher->encrypt_hex($data);

	return $result;
}

sub decrypt # string for decrypt
{
	my $data = shift;
	
	my $cipher = &buildcbc();
	my $result = $cipher->decrypt_hex($data);

	return $result;
}

# build local key
sub keycert
{
	#~ use Zevenet::SystemInfo;

	my $dmi      = &get_sys_uuid();
	my $hostname = &getHostname();
	my $mod_appl = &get_mod_appl();

	my $key = "$hostname::$dmi::$mod_appl";

	my $str = &encrypt($key);

	return $str;
}

# evaluate certificate
sub certcontrol
{
	#~ require Time::Local;
	#~ use Zevenet::Config;
	require Zevenet::SystemInfo;

	my $basedir = &getGlobalConfiguration( 'basedir' );
	my $zlbcertfile = "$basedir/zlbcertfile.pem";
	my $swcert = 0;

	if ( ! -e $zlbcertfile )
	{
		#swcert = 1 ==> There isn't certificate
		$swcert = 1;
		return $swcert;
	}
	my $openssl_bin = "/usr/bin/openssl";
	my $keyid       = "4B:1B:18:EE:21:4A:B6:F9:76:DE:C3:D8:86:6D:DE:98:DE:44:93:B9";
	my @months      = qw(Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec);
	my $hostname    = &getHostname();
	my $key         = &keycert();
	my $dmi 		= &get_sys_uuid();
	my $mod_appl	= &get_mod_appl();

	my @zen_cert    = `$openssl_bin x509 -in $zlbcertfile -noout -text 2>/dev/null`;

	my $serial = `$openssl_bin x509 -in $zlbcertfile -serial -noout`;
	$serial =~ /serial\=(\w+)/;
	$serial = $1;
#	&zenlog("Serial: $serial");

	my $key_decrypy = &decrypt($key);
	my @data_key = split /::/, $key_decrypy;

	my @type_cert_array = grep /C ?= ?(DE|TE)\,/, @zen_cert;
	$type_cert_array[0] =~ /C ?= ?(DE|TE)\,/;
	my $type_cert = $1;
#	&zenlog("Type cert: $type_cert");

	if (    ( !grep /$key/, @zen_cert )
		 || ( !grep /CN=$hostname\/|CN = $hostname\,/, @zen_cert )
		 || ( !grep /$hostname/, $data_key[0] )
		 || ( !grep /$dmi/, $data_key[1] )
		 || ( !grep /$mod_appl/, $data_key[2] ))
	{
		#swcert = 5 ==> Cert isn't valid
		$swcert = 5;
		return $swcert;

	}elsif ( !grep /keyid:$keyid/, @zen_cert ) {
		#swcert = 2 ==> Cert isn't signed OK
		$swcert = 2;
		return $swcert;
	}

	# Verify date of check
	my $date_today = strftime "%F", localtime;
	my $date_encode = &encrypt($date_today);
	$date_encode =~ s/\s*$//;
#	&zenlog("Date today: $date_today\n Date today encode: $date_encode");

	my $configdir = &getGlobalConfiguration( 'configdir' );
	my $file_check = "$configdir/config_check";
	my $date_check = `cat $file_check`;
	$date_check =~ s/\s*$//;
#	&zenlog("Date check encode: $date_check\n Date check decode: $last_date_check");

	if ($date_check ne $date_encode) {
		my $crl_path = "$configdir/cacrl.crl";

		my $date_mod = `stat -c%y $crl_path`;
		my @modification = split /\ /, $date_mod;

		if ( $modification[0] ne $date_today) {
			# Download CRL
	  		my $download = `wget -q -O $crl_path https://devcerts.zevenet.com/pki/ca/index.php?stage=dl_crl`;
	  		&zenlog("CRL Downloaded on $date_today");
	  	}

		my @decoded = `openssl crl -inform DER -text -noout -in $crl_path`;
		if ( !grep /keyid:$keyid/, @decoded ) {
			#swcert = 2 ==> Cert isn't signed OK
			$swcert = 2;
			return $swcert;
		}				

		foreach my $line (@decoded) {
			if (grep /Serial Number\: ?$serial/, $line) {
				my $isRevoked = grep /Serial Number\: ?$serial/, $line;
				if ($isRevoked > 0) {
					&zenlog("Certificate Revoked (CRL check)");
					$swcert = 4;
					return $swcert;
				}
			}
		}
		require Tie::File;
		tie my @contents, 'Tie::File', "$file_check";
		@contents = ($date_encode);

		untie @contents;
	}
	# Certificate expiring date
	my ( $na ) = grep /Not After/i, @zen_cert;
	$na =~ s/.*not after.*:\ //i;

	my ( $month, $day, $hours, $min, $sec, $year ) = split /[ :]+/, $na;
	( $month ) = grep { $months[$_] eq $month } 0..$#months;
	my $end = timegm( $sec, $min, $hours, $day, $month, $year );

	my $dayright = ( $end - time () ) / 86400;

	if ( $dayright < 0 )
	{
		#control errors
		if ( $type_cert eq 'TE' )
		{
			# Policy: expired testing certificates would not stop zen service,
			# but rebooting the service would not start the service,
			# interfaces should always be available.
			$swcert = 3;
		}

		if ( $type_cert eq 'DE' )
		{
			# The contract support plan is expired you have to request a
			# new contract support. Only message alert!
			$swcert = -1;
		}
	}

	# error codes
	#swcert = 0 ==> OK
	#swcert = 1 ==> There isn't certificate
	#swcert = 2 ==> Cert isn't signed OK
	#swcert = 3 ==> Cert test and it's expired
	#swcert = 4 ==> Cert is revoked
	#swcert = 5 ==> Cert isn't valid

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
		my $msg;

		if ( $swcert == 1 )
		{
			$msg =
			  "There isn't a valid Zevenet Load Balancer certificate file, please request a new one";
		}
		elsif ( $swcert == 2 )
		{
			$msg =
			  "The certificate file isn't signed by the Zevenet Certificate Authority, please request a new one";
		}
		elsif ( $swcert == 3 )
		{
			# Policy: expired testing certificates would not stop zen service,
			# but rebooting the service would not start the service,
			# interfaces should always be available.
			$msg =
			  "The Zevenet Load Balancer certificate file you are using is for testing purposes and its expired, please request a new one";
		}
		elsif ( $swcert == 4 )
		{
			$msg =
			  "The Zevenet Load Balancer certificate file has been revoked, please request a new one";
		}
		elsif ( $swcert == 5 )
		{
			$msg =
			  "The Zevenet Load Balancer certificate file isn't valid for this machine.";
		}

		my $body = {
					 message         => $msg,
					 certificate_key => &keycert(),
					 hostname        => &getHostname(),
		};

		return &httpResponse( { code => 403, body => $body } );
	}

	return $swcert;
}

sub get_sys_uuid
{
	my ( $dmi ) = grep ( /UUID\:/, `/usr/sbin/dmidecode` );
	( undef, $dmi ) = split ( /:\s+/, $dmi );

	chomp $dmi;

	return $dmi;
}

sub get_mod_appl
{
	my @mod = grep ( /\w{3} ?\d{4}/, `cat /etc/zevenet_version` );
	$mod[0] =~ /(\w{3} ?\d{4})/;

	my $mod_appl = $1;
	$mod_appl =~ s/ //;

	return $mod_appl;
}
