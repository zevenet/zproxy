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
use Zevenet::Farm::Core;

my $configdir = &getGlobalConfiguration('configdir');

=begin nd
Function: getFarmCertificatesSNI

	List all certificates added to a farm.

Parameters:
	farmname - Farm name.

Returns:
	array - list of certificates added to the farm
=cut
sub getFarmCertificatesSNI    #($fname)
{
	my $fname = shift;

	my @output;

	my $file = &getFarmFile( $fname );
	open FI, "<$configdir/$file";
	my @content = <FI>;
	close FI;
	foreach my $line ( @content )
	{
		if ( $line =~ /Cert "/ && $line !~ /\#.*Cert/ )
		{
			my @partline = split ( '\"', $line );
			@partline = split ( "\/", $partline[1] );
			my $lfile = @partline;
			push ( @output, $partline[$lfile - 1] );
		}
	}

	#&zenlog("getting 'Certificate $output' for $fname farm $type");
	return @output;
}

=begin nd
Function: setFarmCertificateSNI

	Add a certificate to a farm.

Parameters:
	certificate_file - Certificate file
	farmname - Farm name.

Returns:
	Integer - Error code: 0 on success, or -1 on failure.
=cut
sub setFarmCertificateSNI    #($cfile,$fname)
{
	my ( $cfile, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;
	my $sw     = 0;
	my $i      = 0;

	if ( $cfile =~ /^$/ )
	{
		&zenlog ( "Certificate not found.", "warning", "LSLB" );
		return $output;
	}

	&zenlog( "setting 'Certificate $cfile' for $fname farm $type", "info", "LSLB" );

	if ( $type eq "https" )
	{
		require Tie::File;
		require Zevenet::Lock;
		&ztielock ( \my @array, "$configdir/$ffile" );

		for ( @array )
		{
			if ( $_ =~ /Cert "/ )
			{
				#s/.*Cert\ .*/\tCert\ \"$configdir\/$cfile\"/g;
				#$output = $?;
				$sw = 1;
			}

			if ( $_ !~ /Cert "/ && $sw eq 1 )
			{
				splice @array, $i, 0, "\tCert\ \"$configdir\/$cfile\"";
				$output = 0;
				last;
			}
			$i++;
		}
		untie @array;
	}
	else
	{
		&zenlog ( "Error adding certificate to farm $fname. This farm is not https type.", "error", "LSLB" );
	}

	return $output;
}

=begin nd
Function: setFarmDeleteCertSNI

	Delete the selected certificate from a HTTP farm. This function is used in zapi v2

Parameters:
	certificate - Certificate name
	farmname - Farm name.

Returns:
	Integer - Error code: 1 on success, or -1 on failure.

FIXME:
	Duplicate function with: setFarmDeleteCertNameSNI used in zapiv3
=cut
sub setFarmDeleteCertSNI    #($certn,$fname)
{
	my ( $certn, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;
	my $i      = 0;
	my $j      = 0;

	&zenlog( "Deleting 'Certificate $certn' for $fname farm $type", "info", "LSLB" );

	if ( $type eq "https" )
	{
		require Tie::File;
		require Zevenet::Lock;
		&ztielock ( \my @array, "$configdir/$ffile" );

		for ( @array )
		{
			if ( $_ =~ /Cert "/ )
			{
				$i++;
			}

			if ( $_ =~ /Cert/ && $i eq "$certn" )
			{
				splice @array, $j, 1,;
				$output = 0;

				if ( $array[$j] !~ /Cert/ && $array[$j - 1] !~ /Cert/ )
				{
					splice @array, $j, 0, "\tCert\ \"$configdir\/zencert.pem\"";
					$output = 1;
				}
				last;
			}
			$j++;
		}
		untie @array;
	}

	return $output;
}

=begin nd
Function: setFarmDeleteCertNameSNI

	Delete the selected certificate from a HTTP farm

Parameters:
	certificate - Certificate name
	farmname - Farm name.

Returns:
	Integer - Error code: 1 on success, or -1 on failure.

FIXME:
	Duplicate function with: setFarmDeleteCertSNI used in zapiv3
=cut
sub setFarmDeleteCertNameSNI    #($certn,$fname)
{
	my ( $certname, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;
	my $j      = 0;

	&zenlog( "Deleting 'Certificate $certname' for $fname farm $type", "info", "LSLB" );

	if ( $type eq "https" )
	{
		require Zevenet::Lock;
		require Tie::File;
		&ztielock ( \my @array, "$configdir/$ffile" );

		for ( @array )
		{
			if ( $_ =~ /^\s*Cert "$configdir\/$certname"/ )
			{
				splice @array, $j, 1,;
				$output = 0;

				if ( $array[$j] !~ /Cert/ && $array[$j - 1] !~ /Cert/ )
				{
					splice @array, $j, 0, "\tCert\ \"$configdir\/zencert.pem\"";
					$output = 1;
				}
				last;
			}
			$j++;
		}
		untie @array;
	}

	return $output;
}

=begin nd
Function: getFarmCipherSSLOffLoadingSupport

	Get if the process supports aes aceleration

Parameters:
	none -.

Returns:
	Integer - return 1 if proccess support AES aceleration or 0 if it doesn't
		support it

=cut
sub getFarmCipherSSLOffLoadingSupport
{
	my $aes_found = 0;
	my $proc_cpu = "/proc/cpuinfo";

	if ( -f $proc_cpu )
	{
		open my $fh, "<", $proc_cpu;

		while ( my $line = <$fh> )
		{
			if ( $line =~ /^flags.* aes / )
			{
				$aes_found = 1;
				last;
			}
		}

		close $fh;
	}

	return $aes_found;
}

sub getExtraCipherProfiles
{
	my @cipher_profiles = ();

	if ( &getFarmCipherSSLOffLoadingSupport() )
	{
		push @cipher_profiles, { 'ciphers' => "ssloffloading", "description" => "SSL offloading" };
	}

	return @cipher_profiles;
}

1;
