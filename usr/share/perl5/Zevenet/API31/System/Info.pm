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

# show license
sub get_license
{
	my $format = shift;

	my $desc = "Get license";
	my $licenseFile;
	my $file;

	if ( $format eq 'txt' )
	{
		$licenseFile = &getGlobalConfiguration( 'licenseFileTxt' );
	}
	elsif ( $format eq 'html' )
	{
		$licenseFile = &getGlobalConfiguration( 'licenseFileHtml' );
	}
	else
	{
		my $msg = "Not found license.";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	open ( my $license_fh, '<', $licenseFile );
	{
		local $/ = undef;
		$file = <$license_fh>;
	}
	close $license_fh;

	&httpResponse({ code => 200, body => $file, type => 'text/plain' });
}

sub get_supportsave
{
	my $desc = "Get supportsave file";
	my @ss_output = `/usr/local/zevenet/app/zbin/supportsave 2>&1`;

	# get the last "word" from the first line
	my $first_line = shift @ss_output;
	my $last_word = ( split ( ' ', $first_line ) )[-1];

	my $ss_path = $last_word;
	my ( undef, $ss_filename ) = split ( '/tmp/', $ss_path );

	&httpDownloadResponse( desc => $desc, dir => '/tmp', file => $ss_filename );
}

# GET /system/version
sub get_version
{
	require Zevenet::SystemInfo;
	require Zevenet::Certificate;

	my $desc    = "Get version";
	my $uname   = &getGlobalConfiguration( 'uname' );
	my $zevenet = &getGlobalConfiguration( 'version' );

	my $kernel     = `$uname -r`;
	my $hostname   = &getHostname();
	my $date       = &getDate();
	my $applicance = &getApplianceVersion();

	chomp $kernel;

	################ Certificate ######################

	use Time::Local;

	sub getDateEpoc
	{
		my $date_string = shift @_;
		my @months = qw(Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec);

		my ( $month, $day, $hours, $min, $sec, $year ) = split /[ :]+/, $date_string;
		( $month ) = grep { $months[$_] eq $month } 0..$#months;

		return timegm( $sec, $min, $hours, $day, $month, $year );
	}

	my $basedir = &getGlobalConfiguration( 'basedir' );
	my $zlbcertfile = "$basedir/zlbcertfile.pem";

	my $cert_ends = &getCertExpiration( "$zlbcertfile" );
	#~ zenlog("cert_ends: $cert_ends");
	my $end = &getDateEpoc( $cert_ends );
	#~ zenlog("end: $end");

	my $days_left = ( $end - time () ) / 86400;
	$days_left =~ s/\..*//g;
	$days_left = 'expired' if $days_left < 0;
	#~ zenlog("certificate remaining days: $days_left");

	#~ my $cert_begins = &getCertCreation( "$zlbcertfile" );
	#~ zenlog("cert_begins: $cert_begins");
	#~ my $init = &getDateEpoc( $cert_begins );
	#~ zenlog("init: $init");
	#~ my $totaldays = ( $end - $init ) / 86400;
	#~ zenlog("certificate duration: $totaldays");

	#################################################

	my $params = {
				   'kernel_version'    => $kernel,
				   'zevenet_version'   => $zevenet,
				   'hostname'          => $hostname,
				   'system_date'       => $date,
				   'appliance_version' => $applicance,
				   'certificate_expiration' => $days_left,
	};
	my $body = { description => $desc, params => $params };

	&httpResponse( { code => 200, body => $body } );
}

1;
