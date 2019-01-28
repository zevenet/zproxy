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

use Time::Local;
use Crypt::CBC;
use POSIX qw(strftime);

require Zevenet::Config;

my $configdir = &getGlobalConfiguration( 'configdir' );
my $openssl   = &getGlobalConfiguration( 'openssl' );

# error codes
#swcert = -1 ==> Cert support and it's expired
#swcert = 0 ==> OK
#swcert = 1 ==> There isn't certificate
#swcert = 2 ==> Cert isn't signed OK
#swcert = 3 ==> Temporality cert and it's expired
#swcert = 4 ==> Cert is revoked
#swcert = 5 ==> Cert isn't valid
#swcert = 6 ==> Crl missing

# certificate error messages
my @certErrors = (
	"",    # there are not any error
	"There isn't a valid Zevenet Load Balancer certificate file, please request a new one",
	"The certificate file isn't signed by the Zevenet Certificate Authority, please request a new one",

	# Policy: expired testing certificates would not stop zen service,
	# but rebooting the service would not start the service,
	# interfaces should always be available.
	"The Zevenet Load Balancer certificate file you are using is for testing purposes and its expired, please request a new one",
	"The Zevenet Load Balancer certificate file has been revoked, please request a new one",
	"The Zevenet Load Balancer certificate file isn't valid for this machine.",
	"The Zevenet crl file is missing.",
	"The Zevenet Certificate has an old key, please request a new certificate",
	"The Zevenet crl file is not valid",
);

my $cert_host  = "certs.zevenet.com";
my $crl_url    = "https://$cert_host/pki/ca/index.php?stage=dl_crl";
my $crl_path   = "$configdir/cacrl.crl";
my $file_check = "$configdir/config_check";

my $keyid = "4B:1B:18:EE:21:4A:B6:F9:76:DE:C3:D8:86:6D:DE:98:DE:44:93:B9";

my @months = qw(Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec);

=begin nd
Function: buildcbc

	Build a CBC object to encrypt and decrypt the crl file

Parameters:
	none - .

Returns:
	object - CBC object

=cut

sub buildcbc
{
	my $cipher = Crypt::CBC->new(
					 -literal_key => 1,
					 -key => 'wg2kx8VY2NVYDdQSAdqffmHYMd2d97ypYdJ4hwczAm8YBPtHv28EJJ66',
					 -cipher  => 'Blowfish',
					 -iv      => 'r5JLLw4f',
					 -header  => 'none',
					 -padding => 'null'
	);

	return $cipher;
}

=begin nd
Function: encrypt

	Encrypt data using the CBC method and return the result

Parameters:
	data - String of data to encrypt

Returns:
	String - Encrypted data

=cut

sub encrypt    # string for encrypt
{
	my $data = shift;

	my $cipher = &buildcbc();
	my $result = $cipher->encrypt_hex( $data );

	return $result;
}

=begin nd
Function: decrypt

	Decrypt data using the CBC method and return the clear string

Parameters:
	data - String of encrpted data

Returns:
	String - clear data

=cut

sub decrypt    # string for decrypt
{
	my $data = shift;

	my $cipher = &buildcbc();
	my $result = $cipher->decrypt_hex( $data );

	return $result;
}

=begin nd
Function: keycert

	Build the activation certificate key of the current host

Parameters:
	none - .

Returns:
	String - certificate key

=cut

sub keycert
{
	my $dmi      = &get_sys_uuid();
	my $hostname = &getHostname();
	my $mod_appl = &get_mod_appl();

	my $key = "$hostname::$dmi::$mod_appl";
	my $str = &encrypt( $key );

	return $str;
}

=begin nd
Function: keycert_old

	Build the old activation certificate key of the current host

Parameters:
	none - .

Returns:
	String - certificate key

=cut

sub keycert_old
{
	my $dmi      = get_sys_uuid();
	my $hostname = &getHostname();

	my $block1 = crypt ( "${dmi}${hostname}", "93" );
	my $block2 = crypt ( "${hostname}${dmi}", "a3" );
	my $block3 = crypt ( "${dmi}${hostname}", "ZH" );
	my $block4 = crypt ( "${hostname}${dmi}", "h7" );
	$block1 =~ s/^93//;
	$block2 =~ s/^a3//;
	$block3 =~ s/^ZH//;
	$block4 =~ s/^h7//;

	my $str = "${block1}-${block2}-${block3}-${block4}";
	return $str;
}

=begin nd
Function: certcontrol

	This function returns a error code relates on the certificate status, if it is correct, revocked, expired...

Parameters:
	certificate - This parameter is optional. It is the certificate that will be checked.. It is useful to check the certificate status before than overwriting the current certificate.
	If this parameters is not passed, the activation certificated checket will be the default certifciate path, /usr/local/zevenet/zlbcertfile.pm

Returns:
	Integer - Error code related with the certficate status. The possible output codes are:

		swcert = 0 ==> OK

		swcert = 1 ==> There isn't certificate
		swcert = 2 ==> Cert isn't signed OK
		swcert = 3 ==> Cert test and it's expired
		swcert = 4 ==> Cert is revoked
		swcert = 5 ==> Cert isn't valid
		swcert = 6 ==> Crl missing
		swcert = 7 ==> The checked uploading cert has a old key. It is not allow to upload certificates with the old key
		swcert = 8 ==> Invalid CRL

		swcert = -1 ==> Cert support and it's expired

=cut

sub certcontrol
{
	my $zlbcertfilename = shift // "zlbcertfile.pem";

	my $basedir     = &getGlobalConfiguration( 'basedir' );
	my $zlbcertfile = "$basedir/$zlbcertfilename";
	my $swcert      = 0;

	require Zevenet::SystemInfo;
	require Zevenet::Lock;

	#swcert = 1 ==> There isn't certificate
	return 1 if ( !-e $zlbcertfile );

	my $hostname = &getHostname();

	my @zen_cert = `$openssl x509 -in $zlbcertfile -noout -text 2>/dev/null`;

	#swcert = 2 ==> Cert isn't signed OK
	return 2 if ( !grep /keyid:$keyid/, @zen_cert );

	my ( $key, $cert_type ) = &getCertKey( \@zen_cert );

	# does not allow to upload old certificates
	# it is executed when is uploading a certificate by the api
	if ( $zlbcertfilename ne "zlbcertfile.pem" )
	{
		return 7 if ( $cert_type eq 'old' );
	}

	#swcert = 5 ==> Cert isn't valid
	return 5
	  if ( !&validateCertificate( \@zen_cert, $key, $hostname, $cert_type ) );

# lock the downloading crl resource.
# this is useful to another process does not try to download CRL when this process is dowloading it
	my $crl_file_lock = &getLockFile( $file_check );
	my $lock_crl_download = &openlock( $crl_file_lock, '>' );

	# download crl if it is not updated
	my $date_today = strftime( "%F", localtime );
	if ( !&checkCRLUpdated( $date_today ) )
	{
		# update crl if the server has connectivity
		&updateCRL( $date_today ) if ( &checkCRLHost() );

		#swcert = 6 ==> crl is missing
		return 6 if ( !-f $crl_path );

		my @decoded_crl = `$openssl crl -inform DER -text -noout -in $crl_path`;

		#swcert = 8 ==> The crl is not signed
		return 8 if ( !grep /keyid:$keyid/, @decoded_crl );

		#swcert = 4 ==> Revoked in CRL
		return 4 if ( &certRevoked( $zlbcertfile, \@decoded_crl ) );

		# update date of the check
		&setCRLDate( $date_today );
	}

	# free the crl download resource
	close $lock_crl_download;

	# Certificate expiring date
	my $end_cert = &getCertExpiring( \@zen_cert );
	my $dayright = ( $end_cert - time () ) / 86400;

	if ( $dayright < 0 )
	{
		if ( &getCertDefinitive( \@zen_cert, $cert_type, $end_cert ) )
		{
			# The contract support plan is expired you have to request a
			# new contract support. Only message alert!
			$swcert = -1;
		}
		else
		{
			# Policy: expired testing certificates would not stop zen service,
			# but rebooting the service would not start the service,
			# interfaces should always be available.
			$swcert = 3;
		}
	}

	#output
	return $swcert;
}

=begin nd
Function: getCertDefinitive

	This function checks if the certificate is definitive

Parameters:
	Certificate - Text array with the certificate lines
	Cert type - If the certificate is new or old
	Expiration date - Date of the certificate expiration date

Returns:
	Integer - It returns 1 when the certificate is defitive, or 0 if it is not

=cut

sub getCertDefinitive
{
	my $zen_cert   = $_[0];
	my $cert_type  = $_[1];
	my $end        = $_[2];
	my $definitive = 0;

	#Certificate with old format
	if ( $cert_type eq 'old' )
	{
		my ( $nb ) = grep /Not Before/i, @{ $zen_cert };
		$nb =~ s/.*not before.*:\ //i;

		my ( $month, $day, $hours, $min, $sec, $year ) = split /[ :]+/, $nb;
		( $month ) = grep { $months[$_] eq $month } 0 .. $#months;
		my $ini = timegm( $sec, $min, $hours, $day, $month, $year );

		$definitive = 1 if ( ( $end - $ini ) / 86400 > 364 );
	}

	#Certificate with new format
	else
	{
		my @type_cert_array = grep /C ?= ?(DE|TE)\,/, @{ $zen_cert };
		$type_cert_array[0] =~ /C ?= ?(DE|TE)\,/;
		$definitive = 1 if ( $1 eq 'DE' );
	}

	return $definitive;
}

=begin nd
Function: getCertErrorMessage

	This function returns the error message of a certificate error code

Parameters:
	error code - It is a number with the error code

Returns:
	String - It is the message error string

=cut

sub getCertErrorMessage
{
	my $swcert = shift;
	return $certErrors[$swcert];
}

=begin nd
Function: checkActivationCertificate

	It returns a HTTP error via zapi if the installed activation certificate is not valid.
	This functon finihses the execution if the certificate is not valid.

Parameters:
	none - .

Returns:
	none - .

=cut

sub checkActivationCertificate
{
	my $swcert = &certcontrol();

	# if $swcert is greater than 0 zapi should not work
	if ( $swcert > 0 )
	{
		my $body = {
					 message         => $certErrors[$swcert],
					 certificate_key => &keycert(),
					 hostname        => &getHostname(),
		};

		&httpResponse( { code => 402, body => $body } );
	}
}

=begin nd
Function: get_sys_uuid

	It returns the UUID of the local host

Parameters:
	none - .

Returns:
	String - UUID

=cut

sub get_sys_uuid
{
	my ( $dmi ) = grep ( /UUID\:/, `/usr/sbin/dmidecode` );
	( undef, $dmi ) = split ( /:\s+/, $dmi );

	chomp $dmi;

	return $dmi;
}

=begin nd
Function: get_mod_appl

	It returns the type of Zevenet template of the host

Parameters:
	none - .

Returns:
	String - Zevenet version type: ZVA, ZBA, ZNA

=cut

sub get_mod_appl
{
	my @mod = grep ( /\w{3} ?\d{4}/, `cat /etc/zevenet_version` );
	$mod[0] =~ /(\w{3} ?\d{4})/;

	my $mod_appl = $1;
	$mod_appl =~ s/ //;

	return $mod_appl;
}

=begin nd
Function: updateCRL

	It updates the CA CRL, downloading it from the zevenet sever

Parameters:
	time - current time

Returns:
	none - .

=cut

sub updateCRL
{
	my $date_today = $_[0];
	my $tmp_file   = '/tmp/cacrl.crl';
	my $wget       = &getGlobalConfiguration( 'wget' );

	# Download CRL
	my $download = `$wget -q -T5 -t1 -O $tmp_file $crl_url`;

	if ( -s $tmp_file > 0 )
	{
		&zenlog( "CRL Downloaded on $date_today", 'info', 'certifcate' );
		my $copy = `cp $tmp_file $crl_path`;
	}
	else
	{
		&zenlog( "The CRL could not be updated on $date_today", 'info', 'certifcate' );
	}

	unlink $tmp_file;
}

=begin nd
Function: checkCRLHost

	It does a network check to validate if Zevenet certificate server is UP.
	This function uses proxy if it is configured

Parameters:
	none - .

Returns:
	Integer - It returns 1 if the server is UP or 0 if it is not

=cut

sub checkCRLHost
{
	my $isUp        = 0;
	my $proxy_https = $ENV{ https_proxy };

	# If proxy, use openssl
	if ( $proxy_https )
	{
		# delete https:// if exists
		$proxy_https =~ s/https\:\/\// /;
		( my $proxyIp, my $proxyPort ) = split /\:(?=\d)/, $proxy_https;
		$proxyPort = "443" if ( !defined $proxyPort );
		my $cmd =
		  "echo -e 'GET / HTTP/1.1\\r\\n' | timeout 2 $openssl s_client -connect $cert_host:443 -proxy $proxyIp:$proxyPort";
		$isUp = ( &logAndRun( $cmd ) ) ? 0 : 1;    # invert the value returned
	}

	# If !proxy, use IO::Socket::INET
	else
	{
		require IO::Socket;
		if (
			 my $scan = IO::Socket::INET->new(
											   PeerAddr => $cert_host,
											   PeerPort => 443,
											   Proto    => 'tcp',
											   Timeout  => 2
			 )
		  )
		{
			$isUp = 1;
			$scan->close();
		}
	}
	return $isUp;
}

=begin nd
Function: certRevoked

	Check if the certificate is in the list of revoked certificates. It is compare the key with the list keys from crl dedoced

Parameters:
	Serial - Host serial to check in the crl list
	list - List of serial revoked in the crl

Returns:
	Integer - It returns 1 if the serial is revoked or 0 if it is not revoked

=cut

sub certRevoked
{
	my ( $zlbcertfile, $decoded ) = @_;

	my $serial = &getCertSerial( $zlbcertfile );

	foreach my $line ( @{ $decoded } )
	{
		if ( grep /Serial Number\: ?$serial/, $line )
		{
			&zenlog( "Certificate Revoked (CRL check)", 'info', 'certificate' );
			return 1;
		}
	}

	return 0;
}

=begin nd
Function: getCertSerial

	it gets the serial from an activation certificate. The serial is unique for issued certificate

Parameters:
	certificate - Path to the certificate

Returns:
	String - It returns a string with the certificate serial

=cut

sub getCertSerial
{
	my $zlbcertfile = shift;
	my $serial      = `$openssl x509 -in $zlbcertfile -serial -noout`;
	$serial =~ /serial\=(\w+)/;
	$serial = $1;
	return $serial;
}

=begin nd
Function: getCertKey

	it gets the activation certificate key from an certificate and if the key of the old or new certificates.

Parameters:
	Certificate - Text array with the certificate lines

Returns:
	Array with 2 values:
	String - It returns a string with the certificate serial. If the key is blank is becouse the certificate key does not match with certificate host
	String - Identify if the certificate is 'old' or 'new'

=cut

sub getCertKey
{
	my $zen_cert = $_[0];

	my @key_cert = grep /Subject: ?.+/, @{ $zen_cert };
	my $cert_type;    # old or new
	my $key;
	my $host_key;

	if ( $key_cert[0] =~ /Subject: ?.+1\.2\.3\.4\.5\.8 ?= ?(.+)/ )
	{
		$key       = $1;
		$cert_type = "new";
		$host_key  = &keycert();
	}
	elsif ( $key_cert[0] =~ /Subject: ?.+OU ?= ?([.\/0-9A-Za-z\-]+), ?/ )
	{
		$key       = $1;
		$cert_type = "old";
		$host_key  = &keycert_old();
	}

	# return blank key if it is not correct for the current host
	$key = "" if ( $key ne $host_key );

	return ( $key, $cert_type );
}

=begin nd
Function: setCRLDate

	It saves the date of the last CRL update

Parameters:
	time - current time

Returns:
	none - .

=cut

sub setCRLDate
{
	my $date_today = shift;

	my $date_encode = &encrypt( $date_today );
	$date_encode =~ s/\s*$//;

	my $write_check = &openlock( $file_check, '>' );
	if ( $write_check )
	{
		print $write_check $date_encode;
		close $write_check;
	}
	else
	{
		&zenlog( "Error opening $file_check", "ERROR", "certificate" );
	}
}

=begin nd
Function: checkCRLUpdated

	It verifies if the CRL has been uploaded today.

Parameters:
	Date - Today date

Returns:
	Integer - It returns 1 if the last updated has been today or 0 in another case.

=cut

sub checkCRLUpdated
{
	my $date_today  = $_[0];
	my $date_encode = &encrypt( $date_today );
	$date_encode =~ s/\s*$//;

	my $read_check = &openlock( $file_check, '<' );
	my $date_check = <$read_check>;
	$date_check =~ s/\s*$//;
	close $read_check;

	return ( $date_check eq $date_encode ) ? 1 : 0;
}

=begin nd

Function: getCertExpiring

	It returns the certificate expiring date

Parameters:
	Certificate - Text array with the certificate lines

Returns:
	Date - Certificate expiring date

=cut

sub getCertExpiring
{
	my $zen_cert = $_[0];

	my ( $na ) = grep /Not After/i, @{ $zen_cert };
	$na =~ s/.*not after.*:\ //i;

	my ( $month2, $day2, $hours2, $min2, $sec2, $year2 ) = split /[ :]+/, $na;
	( $month2 ) = grep { $months[$_] eq $month2 } 0 .. $#months;
	my $end = timegm( $sec2, $min2, $hours2, $day2, $month2, $year2 );

	return $end;
}

=begin nd

Function: validateCertificate

	It checks if the certificate is valid for the current machine

Parameters:
	Certificate - Text array with the certificate lines
	Key - Host certificate key
	hostname - name of the host
	cert type - If the certificate is the new o old type

Returns:
	Integer - It returns 0 if the certificate is not valid or 1 if it is valid.

=cut

sub validateCertificate
{
	my $zen_cert  = $_[0];
	my $key       = $_[1];
	my $hostname  = $_[2];
	my $cert_type = $_[3];

	return 0 if ( !$key );
	return 0 if ( !grep ( /CN ?= ?$hostname\b/, @{ $zen_cert } ) );

	# Advanced validations of the new certificate
	if ( $cert_type eq 'new' )
	{
		my $dmi      = &get_sys_uuid();
		my $mod_appl = &get_mod_appl();

		my $key_decrypy = &decrypt( $key );
		my @data_key = split /::/, $key_decrypy;

		return 0
		  if (    ( !grep /$hostname/, $data_key[0] )
			   || ( !grep /$dmi/,      $data_key[1] )
			   || ( !grep /$mod_appl/, $data_key[2] ) );
	}

	return 1;
}

1;
