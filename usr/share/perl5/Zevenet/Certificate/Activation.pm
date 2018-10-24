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

use Time::Local;
use Zevenet::Config;
use Zevenet::SystemInfo;
use Crypt::CBC;
use POSIX 'strftime';

#build CBC Object
sub buildcbc
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
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
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my $data = shift;

	my $cipher = &buildcbc();
	my $result = $cipher->encrypt_hex($data);

	return $result;
}

sub decrypt # string for decrypt
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my $data = shift;

	my $cipher = &buildcbc();
	my $result = $cipher->decrypt_hex($data);

	return $result;
}

# build local key
sub keycert
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	#~ use Zevenet::SystemInfo;

	my $dmi      = &get_sys_uuid();
	my $hostname = &getHostname();
	my $mod_appl = &get_mod_appl();

	my $key = "$hostname::$dmi::$mod_appl";
	my $str = &encrypt($key);

	return $str;
}

# build local old key
sub keycert_old
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
    #~ use Zevenet::SystemInfo;
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

# evaluate certificate
sub certcontrol
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
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
	my $openssl 	= &getGlobalConfiguration( 'openssl' );
	my $keyid       = "4B:1B:18:EE:21:4A:B6:F9:76:DE:C3:D8:86:6D:DE:98:DE:44:93:B9";
	my @months      = qw(Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec);
	my $hostname    = &getHostname();
	my $key         = &keycert_old();

	my @zen_cert    = `$openssl x509 -in $zlbcertfile -noout -text 2>/dev/null`;

	my $serial = `$openssl x509 -in $zlbcertfile -serial -noout`;
	$serial =~ /serial\=(\w+)/;
	$serial = $1;

	my @key_cert = grep /Subject: ?.+/, @zen_cert;
	$key_cert[0] =~ /Subject: ?.+OU ?= ?([.\/0-9A-Za-z\-]+), ?/;
	my $cert_ou = $1;

	if ($cert_ou eq 'false')
	{
		$key_cert[0] =~ /Subject: ?.+1\.2\.3\.4\.5\.8 ?= ?(.+)/;
		my $cert_ou = $1;
		$key = &keycert();
	}

	if ( !grep /keyid:$keyid/, @zen_cert ) {
        #swcert = 2 ==> Cert isn't signed OK
        $swcert = 2;
        return $swcert;
    } elsif (( !grep /$key/, @zen_cert )
			 || ( !grep (/(CN=$hostname\/|CN = $hostname\,)/, @zen_cert)) ) {
 		#swcert = 5 ==> Cert isn't valid
       	$swcert = 5;
       	return $swcert;
 	}

	# Verify date of check
	my $date_today = strftime "%F", localtime;
	my $date_encode = &encrypt($date_today);
	$date_encode =~ s/\s*$//;

	my $configdir = &getGlobalConfiguration( 'configdir' );
	my $file_check = "$configdir/config_check";

    require Zevenet::Lock;
    my $file_lock = &getLockFile( $file_check );
    my $lock_fd = &lockfile( $file_lock );

    my $open_check = open ( my $read_check, '<', $file_check );
    my $date_check = <$read_check>;
    $date_check =~ s/\s*$//;
    close $read_check;

	if ($date_check ne $date_encode)
	{
		my $open_check2 = open ( my $write_check, '>', $file_check );
		print $write_check $date_encode;
		close $write_check;

		my $crl_path = "$configdir/cacrl.crl";

		my $date_mod = '';

		if ( -f $crl_path )
		{
			$date_mod = `stat -c%y $crl_path`;
		}
		else
		{
			&zenlog("WARNING!!! File $crl_path not found.");
		}
		my $wget = &getGlobalConfiguration( 'wget' );
		my @modification = split /\ /, $date_mod;
		$modification[0] = $modification[0] // '';

		if ( $modification[0] ne $date_today) {
			require IO::Socket;

            if ( my $scan = IO::Socket::INET->new(PeerAddr => "certs.zevenet.com" , PeerPort => 443 , Proto => 'tcp' , Timeout => 2) ) {
            	$scan->close();
                my $tmp_file = '/tmp/cacrl.crl';

				# Download CRL
				my $download = `$wget -q -T5 -t1 -O $tmp_file https://certs.zevenet.com/pki/ca/index.php?stage=dl_crl`;
				if ( -s $tmp_file > 0 ) {
					&zenlog("CRL Downloaded on $date_today");
					my $copy = `cp $tmp_file $crl_path`;
				}
				unlink $tmp_file;
			}
	  	}

		my @decoded = ();
		@decoded = `$openssl crl -inform DER -text -noout -in $crl_path` if -f $crl_path;
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
	}
	&unlockfile( $lock_fd );

 	 # Certificate expiring date
    my ( $na ) = grep /Not After/i, @zen_cert;
    $na =~ s/.*not after.*:\ //i;
    my ( $month2, $day2, $hours2, $min2, $sec2, $year2 ) = split /[ :]+/, $na;
	( $month2 ) = grep { $months[$_] eq $month2 } 0 .. $#months;
    my $end = timegm( $sec2, $min2, $hours2, $day2, $month2, $year2 );
    my $totaldays = '';
    my $type_cert = '';

	if ($cert_ou =~ m/-/ ) {
		# Certificate validity date
       	my ( $nb ) = grep /Not Before/i, @zen_cert;
       	$nb =~ s/.*not before.*:\ //i;

       	my ( $month, $day, $hours, $min, $sec, $year ) = split /[ :]+/, $nb;
       	( $month ) = grep { $months[$_] eq $month } 0 .. $#months;
       	my $ini = timegm( $sec, $min, $hours, $day, $month, $year );

       	$totaldays = ( $end - $ini ) / 86400;
		$totaldays =~ s/\-//g;

	} else {
		my $dmi 		= &get_sys_uuid();
		my $mod_appl	= &get_mod_appl();

		my $key_decrypy = &decrypt($key);
		my @data_key = split /::/, $key_decrypy;

		my @type_cert_array = grep /C ?= ?(DE|TE)\,/, @zen_cert;
		$type_cert_array[0] =~ /C ?= ?(DE|TE)\,/;
		$type_cert = $1;

		if (( !grep /$hostname/, $data_key[0] )
			 || ( !grep /$dmi/, $data_key[1] )
			 || ( !grep /$mod_appl/, $data_key[2] ))
		{
			#swcert = 5 ==> Cert isn't valid
			$swcert = 5;
			return $swcert;
		}
	}

	my $dayright = ( $end - time () ) / 86400;

	if ( $dayright < 0 )
	{
		#control errors
		if ( ($totaldays ne '' && $totaldays < 364 ) || ($totaldays eq '' && $type_cert eq 'TE') )
		{
			# Policy: expired testing certificates would not stop zen service,
			# but rebooting the service would not start the service,
			# interfaces should always be available.
			$swcert = 3;
		}

		if ( ($totaldays ne '' && $totaldays > 364 ) || ($totaldays eq '' && $type_cert eq 'DE') )
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
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
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

		return &httpResponse( { code => 402, body => $body } );
	}

	return $swcert;
}

sub get_sys_uuid
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my ( $dmi ) = grep ( /UUID\:/, `/usr/sbin/dmidecode` );
	( undef, $dmi ) = split ( /:\s+/, $dmi );

	chomp $dmi;

	return $dmi;
}

sub get_mod_appl
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my @mod = grep ( /\w{3} ?\d{4}/, `cat /etc/zevenet_version` );
	$mod[0] =~ /(\w{3} ?\d{4})/;

	my $mod_appl = $1;
	$mod_appl =~ s/ //;

	return $mod_appl;
}

1;
