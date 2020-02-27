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
use File::Copy;

require Zevenet::Config;
require Zevenet::SystemInfo;
require Zevenet::Certificate;

my $configdir = &getGlobalConfiguration( 'configdir' );
my $openssl   = &getGlobalConfiguration( 'openssl' );

# it needs a default value, maybe the globalconf is not updated yet
my $zlbcertfile_path = &getGlobalConfiguration( 'zlbcertfile_path' )
  // '/usr/local/zevenet/www/zlbcertfile.pem';

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
Function: getKeySigned

	It returns the key id which is used to sign the certificates

Parameters:
	none - .

Returns:
	String - key ID

=cut

sub getKeySigned
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	return $keyid;
}

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $data = shift;

	my $cipher = &buildcbc();
	my $result = $cipher->decrypt_hex( $data );

	return $result;
}

=begin nd
Function: getCertActivationData

	It returns the certificate data without parsing

Parameters:
	Certificate path - Path of the zevenet activation certificate

Returns:
	Ref Array - reference to the certificate text

=cut

sub getCertActivationData
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $zlbcertfile = shift;
	my @data        = `$openssl x509 -in $zlbcertfile -noout -text 2>/dev/null`;
	return \@data;
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $dmi      = &get_sys_uuid();
	my $hostname = &getHostname();
	my $mod_appl = &get_mod_appl();

	my $key = "${hostname}::${dmi}::${mod_appl}";
	my $str = &encrypt( $key );

	return $str;
}

=begin nd
Function: keycert_old

	Build the old activation certificate key of the current host.
	IMPORTANT: This key is used only to validate the old keys.

Parameters:
	none - .

Returns:
	String - certificate key

=cut

sub keycert_old
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
Function: crlcontrol

	Build the old activation certificate key of the current host.
	IMPORTANT: This key is used only to validate the old keys.

Parameters:
	none - .

Returns:
	Integer - It returns 0 on success, 1 if the CRL could not be updated (host without connection or error dowloading the CRL)

=cut

sub crlcontrol
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $err = 1;

# lock the downloading crl resource.
# this is useful to another process does not try to download CRL when this process is dowloading it
	my $crl_file_lock = &getLockFile( $file_check );
	my $lock_crl_download = &openlock( $crl_file_lock, '>' );

	# download crl if it is not updated
	my $date_today = strftime( "%F", localtime );
	if ( !&checkCRLUpdated( $date_today ) )
	{
# Bugfix: Updating config_check without taking into account the CACRL download avoids problems to load balancers without internet
		&setCRLDate( $date_today );

		# update crl if the server has connectivity
		$err = &updateCRL( $date_today );
	}
	else
	{
		$err = 0;
	}

	# free the crl download resource
	close $lock_crl_download;

	#swcert = 6 ==> crl is missing
	return -1 if ( !-f $crl_path );

	return $err;
}

=begin nd
Function: certcontrol

	This function returns a error code relates on the certificate status, if it is correct, revoked, expired...

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $zlbcertfile = shift // $zlbcertfile_path;

	my $swcert = 0;

	require Zevenet::Lock;

	#swcert = 1 ==> There isn't certificate
	return 1 if ( !-e $zlbcertfile );

	# CRL control. Update the revoked certificate list
	# system can not work without CRL
	return 6 if ( &crlcontrol() < 0 );

	my $cert_info = &getCertActivationInfo( $zlbcertfile );

	#swcert = 8 ==> cacrl is not signed
	return 8 if ( $cert_info->{ crl_signed } ne 'true' );

	#swcert = 2 ==> Cert isn't signed OK
	return 2 if ( $cert_info->{ signed } ne 'true' );

	#swcert = 5 ==> Cert isn't valid
	return 5 if ( $cert_info->{ valid } ne 'true' );

	#swcert = 4 ==> Revoked in CRL
	return 4 if ( $cert_info->{ revoked } eq 'true' );

	if ( $cert_info->{ support } ne 'true' )
	{
		if ( $cert_info->{ cert_type } eq 'permanent' )
		{
			# It is not allow to upgrade without support

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $dmi ) = grep ( /UUID\:/, `/usr/sbin/dmidecode` );
	( undef, $dmi ) = split ( /:\s+/, $dmi );

	chomp $dmi;

# dmidcode for zevenet 6 shows UUID data in lowercase, in previous versions shown in uppercase.
	my $zen_version_type = &get_mod_appl();
	$dmi = uc ( $dmi ) if ( $zen_version_type =~ /ZNA.*/ );

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	Integer - It returns 0 on success or 1 on failure

=cut

sub updateCRL
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $date_today = $_[0];
	my $tmp_file   = '/tmp/cacrl.crl';
	my $curl       = &getGlobalConfiguration( 'curl_bin' );
	my $err        = 1;

	# Download CRL
	my $cmd = "$curl -s -f -k $crl_url -o $tmp_file --connect-timeout 2";
	&logAndRun( $cmd );

	my $check_crl = system (
		"$openssl crl -inform DER -text -noout -in $tmp_file | head | grep support\@sofintel.net"
	);

	if ( -s $tmp_file > 0 and $check_crl == 0 )
	{
		move( $tmp_file, $crl_path );
		&zenlog( "CRL downloaded on $date_today", 'info', 'certifcate' );
		$err = 0;
	}
	else
	{
		unlink $tmp_file;
		&zenlog( "The CRL could not be updated on $date_today", 'info', 'certifcate' );
	}

	return $err;
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $zlbcertfile ) = @_;

	# check crl y descargar
	my @decoded_crl = `$openssl crl -inform DER -text -noout -in $crl_path`;

	#swcert = 8 ==> The crl is not signed
	return 8 if ( !grep /keyid:$keyid/, @decoded_crl );

	my $serial = &getCertSerial( $zlbcertfile );

	foreach my $line ( @decoded_crl )
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	else
	{
		&zenlog( "It has not been found any valid key in the certificate",
				 "error", "certificate" );
	}

	# return blank key if it is not correct for the current host
	if ( $key ne $host_key )
	{
		&zenlog(
				"The certificate key: '$key' does not match with the host key: '$host_key'",
				"error", "certificate" );
		$key = "";
	}

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	# it is necessary a CRL if the file does not exist, download it
	return 0 if ( !-f $crl_path );

	my $date_today  = $_[0];
	my $date_encode = &encrypt( $date_today );
	my $date_check  = "";

	$date_encode =~ s/\s*$//;
	if ( -f $file_check )
	{
		my $read_check = &openlock( $file_check, '<' );
		$date_check = <$read_check>;
		$date_check =~ s/\s*$//;
		close $read_check;
	}

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $zen_cert  = $_[0];
	my $key       = $_[1];
	my $hostname  = $_[2];
	my $cert_type = $_[3];

	my $hostname = &getHostname();

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
		  if (    ( $hostname ne $data_key[0] )
			   || ( $dmi ne $data_key[1] )
			   || ( $mod_appl ne $data_key[2] ) );
	}

	return 1;
}

=begin nd
Function: delCert_activation

	Removes the activation certificate

Parameters:
	String - Certificate filename.

Returns:
	Integer - 0 on success, other on failure.

=cut

sub delCert_activation    # ($certname)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $files_removed = 1;

	if ( -f $zlbcertfile_path )
	{
		unlink ( $zlbcertfile_path );
	}
	else
	{
		&zenlog( "The activation certificate $zlbcertfile_path is not found",
				 "error", "Activation" );
	}

	$files_removed = 0 if ( !-f $zlbcertfile_path );

	return $files_removed;
}

=begin nd
Function: getCertActivationInfo

	Retrieve the activation certification information. It shows the information and the status

Parameters:
	Certificate - Certificate path.

Returns:
	hash ref -
	{
          'issuer' => ' ZLB Certificate Authority, emailAddress = support@sofintel.net',
          'key' => '64701fe98a4ff3143364d9be1c39915ccc27d65327869fe9a50a6eef34445874',
          'version' => 'new',
          'days_to_expire' => 216,
          'crl_signed' => 'false',
          'signed' => 'true',
          'support' => 'true',
          'type' => 'Certificate',
          'expiration' => '2019-09-16 06:21:38 UTC',
          'type_cert' => 'temporal',
          'creation' => '2018-10-18 06:21:38 UTC',
          'valid' => 'true',
          'file' => 'zlbcertfile.pem',
          'revoked' => 'false',
          'CN' => 'zva500nodeA'
    };


=cut

sub getCertActivationInfo
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $zlbcertfile = shift;
	my $cert_data   = &getCertActivationData( $zlbcertfile );

	# get basic info
	my $info = &getCertInfo( $zlbcertfile );
	$info->{ creation }   = &getDateUtc( $info->{ creation } );
	$info->{ expiration } = &getDateUtc( $info->{ expiration } );

	# get activation cert
	my ( $key, $cert_version ) = &getCertKey( $cert_data );
	$info->{ key }     = $key;
	$info->{ version } = $cert_version;
	$info->{ type_cert } =
	  ( &getCertDefinitive( $cert_data, $key, $cert_version ) )
	  ? 'permanent'
	  : 'temporal';
	$info->{ signed } = ( grep /keyid:$keyid/, @{ $cert_data } ) ? 'true' : 'false';
	$info->{ valid } =
	  ( &validateCertificate( $cert_data, $key, $hostname, $cert_version ) )
	  ? 'true'
	  : 'false';

	# check with CRL
	my $crl_err = &certRevoked( $zlbcertfile );

	$info->{ revoked }    = ( !$crl_err )     ? 'false' : 'true';
	$info->{ crl_signed } = ( $crl_err == 8 ) ? 'false' : 'true';

	# Certificate expiring date
	$info->{ days_to_expire } = &getCertDaysToExpire( $info->{ expiration } );
	$info->{ support } = ( $info->{ days_to_expire } < 0 ) ? 'false' : 'true';

	return $info;
}

=begin nd
Function: uploadCertActivation

	Retrieve the activation certification information. It shows the information and the status

Parameters:
	Certificate - Certificate path.

Returns:
	String - It returns undef on success or a string with a error message on failure

=cut

sub uploadCertActivation
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $upload_data = shift;
	my $errmsg;
	my $tmpFilename = '/tmp/zlbcertfile.tmp.pem';

	require Zevenet::File;

	unless ( &setFile( $tmpFilename, $upload_data ) )
	{
		return "Could not save the activation certificate";
	}

	# do not allow to upload certificates with old key
	my $cert_data = &getCertActivationData( $tmpFilename );
	my ( undef, $cert_type ) = &getCertKey( $cert_data );

	unless ( $cert_type eq 'new' )
	{
		unlink $tmpFilename;
		return &getCertErrorMessage( 7 );
	}

	my $checkCert = &certcontrol( $tmpFilename );
	if ( $checkCert > 0 )
	{
		unlink $tmpFilename;
		return &getCertErrorMessage( $checkCert );
	}

	&zenlog(
		   "The certfile is correct, moving the uploaded certificate to the right path",
		   "debug", "certificate" );
	rename ( $tmpFilename, $zlbcertfile_path );

 # This is a BUGFIX for the zevenet preinst! In that script is not defined "include"
	my $err = &eload( module => 'Zevenet::Apt',
					  func   => 'setAPTRepo', );
	if ( $err )
	{
		return "An error occurred configuring the Zevenet repository";
	}
	else
	{
		&zenlog( "Restarting Zevenet service", 'info', 'service' );
		my $zevenet_srv = &getGlobalConfiguration( "zevenet_service" );
		&logAndRun( "$zevenet_srv start" );
	}

	return undef;
}

1;
