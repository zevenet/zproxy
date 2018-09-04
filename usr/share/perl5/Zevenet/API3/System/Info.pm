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
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my $format = shift;
	my $description = "Get license";
	my $file;

	if ( $format eq 'txt' )
	{
		my $licenseFile = &getGlobalConfiguration( 'licenseFileTxt' );
		open ( my $license_fh, '<', "$licenseFile" );
		$file .= $_ while ( <$license_fh> );
		# Close this particular file.
		close $license_fh;
		&httpResponse({ code => 200, body => $file, type => 'text/plain' });
	}
	elsif ( $format eq 'html' )
	{
		my $licenseFile = &getGlobalConfiguration( 'licenseFileHtml' );
		open ( my $license_fh, '<', "$licenseFile" );
		$file .= $_ while ( <$license_fh> );
		# Close this particular file.
		close $license_fh;
		&httpResponse({ code => 200, body => $file, type => 'text/html' });
	}
	else
	{
		my $errormsg = "Not found license.";
		my $body =
		  { description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 404, body => $body } );
	}
}

sub get_supportsave
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my $description = "Get supportsave file";
	my @ss_output = `/usr/local/zevenet/bin/supportsave 2>&1`;

	# get the last "word" from the first line
	my $first_line = shift @ss_output;
	my $last_word = ( split ( ' ', $first_line ) )[-1];

	my $ss_path = $last_word;
	my ( undef, $ss_filename ) = split ( '/tmp/', $ss_path );

	open ( my $ss_fh, '<', $ss_path );

	if ( -f $ss_path && $ss_fh )
	{
		my $cgi = &getCGI();
		print $cgi->header(
							-type            => 'application/x-download',
							-attachment      => $ss_filename,
							'Content-length' => -s $ss_path,
		);

		binmode $ss_fh;
		print while <$ss_fh>;
		close $ss_fh;
		unlink $ss_path;
		exit;
	}
	else
	{
		# Error
		my $errormsg = "Error getting a supportsave file";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 400, body => $body } );
	}
}

# GET /system/version
sub get_version
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my $description = "Get version";

	my $uname      = &getGlobalConfiguration( 'uname' );
	my $zevenet    = &getGlobalConfiguration( 'version' );
	my $kernel     = `$uname -r`;
	my $hostname   = &getHostname();
	my $date       = &getDate();
	my $applicance = getApplianceVersion();

	chop $kernel;
	chop $hostname;

	&httpResponse(
		{ 	code => 200, body => { description => $description,
				params => {
					'kernel_version' => $kernel,
					'zevenet_version' => $zevenet,
					'hostname' => $hostname,
					'system_date' => $date,
					'appliance_version' => $applicance,
				} }
		}
	);
}

1;
