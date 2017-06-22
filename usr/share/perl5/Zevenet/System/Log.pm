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

=begin nd
Function: getLogs

	Get list of log files.

Parameters:
	none - .

Returns:
	scalar - Array reference.

	Array element example:

	{
		'file' => $line,
		'date' => $datetime_string
	}

See Also:
	zapi/v3/system.cgi
=cut
sub getLogs
{
	my @logs;
	my $logdir = &getGlobalConfiguration( 'logdir' );

	opendir ( DIR, $logdir );
	my @files = grep ( /^syslog/, readdir ( DIR ) );
	closedir ( DIR );

	foreach my $line ( @files )
	{
		my $filepath = "$logdir/$line";
		chomp ( $filepath );
		my $datetime_string = ctime( stat ( $filepath )->mtime );
		push @logs, { 'file' => $line, 'date' => $datetime_string };
	}

	return \@logs;
}

=begin nd
Function: downloadLog

	Download a log file.

	This function ends the current precess on success.

	Should this function be part of the API?

Parameters:
	logFile - log file name in /var/log.

Returns:
	1 - on failure.

See Also:
	zapi/v3/system.cgi
=cut
sub downloadLog
{
	my $logFile = shift;
	my $error;

	my $logdir = &getGlobalConfiguration( 'logdir' );
	open ( my $download_fh, '<', "$logdir/$logFile" );

	if ( -f "$logdir\/$logFile" && $download_fh )
	{
		my $cgi = &getCGI();
		print $cgi->header(
							-type            => 'application/x-download',
							-attachment      => $logFile,
							'Content-length' => -s "$logdir/$logFile",
		);

		binmode $download_fh;
		print while <$download_fh>;
		close $download_fh;
		exit;
	}
	else
	{
		$error = 1;
	}
	return $error;
}

1;
