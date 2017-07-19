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

# build local key
sub keycert
{
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
	#~ require Time::Local;
	#~ use Zevenet::Config;
	#~ use Zevenet::SystemInfo;

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
	my @zen_cert    = `$openssl_bin x509 -in $zlbcertfile -noout -text 2>/dev/null`;

	if (    ( !grep /$key/, @zen_cert )
		 || ( !grep /keyid:$keyid/, @zen_cert )
		 || ( !grep /CN=$hostname\/|CN = $hostname\,/, @zen_cert ) )
	{
		#swcert = 2 ==> Cert isn't signed OK
		$swcert = 2;
		return $swcert;
	}

	# Certificate validity date
	my ( $nb ) = grep /Not Before/i, @zen_cert;
	$nb =~ s/.*not before.*:\ //i;

	my ( $month, $day, $hours, $min, $sec, $year ) = split /[ :]/, $nb;
	( $month ) = grep { $months[$_] eq $month } 0..$#months;
	my $ini = timegm( $sec, $min, $hours, $day, $month, $year );

	# Certificate expiring date
	my ( $na ) = grep /Not After/i, @zen_cert;
	$na =~ s/.*not after.*:\ //i;

	( $month, $day, $hours, $min, $sec, $year ) = split /[ :]/, $na;
	( $month ) = grep { $months[$_] eq $month } 0..$#months;
	my $end = timegm( $sec, $min, $hours, $day, $month, $year );

	# Validity remaining
	my $totaldays = ( $end - $ini ) / 86400;
	$totaldays =~ s/\-//g;
	my $dayright = ( $end - time () ) / 86400;

	if ( $dayright < 0 )
	{
		#control errors
		if ( $totaldays < 364 )
		{
			# Policy: expired testing certificates would not stop zen service,
			# but rebooting the service would not start the service,
			# interfaces should always be available.
			$swcert = 3;
		}

		if ( $totaldays > 364 )
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
			  "The certificate file isn't signed by the Zevenet Certificate Authority, please request a new one";
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

sub get_sys_uuid
{
	my $uuid_file_path = '/sys/class/dmi/id/product_uuid';

	open( my $file, '<', $uuid_file_path);

	unless ( $file )
	{
		my $msg = "Could not open file $uuid_file_path: $!";
		zenlog( $msg );
		die( $msg );
	}

	my $uuid = <$file>;
	close $file;

	return $uuid;
}

1;
