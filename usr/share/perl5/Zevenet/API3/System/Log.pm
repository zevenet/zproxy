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

#	GET	/system/logs
sub get_logs
{
	require Zevenet::System::Log;

	my $description = "Get logs";
	my $backups = &getLogs;

	&httpResponse(
		 { code => 200, body => { description => $description, params => $backups } } );
}

#	GET	/system/logs/LOG
sub download_logs
{
	my $logFile      = shift;
	my $description = "Download a log file";
	my $errormsg    = "$logFile was download successful.";
	my $logPath = &getGlobalConfiguration( 'logdir') . "/$logFile";

	if ( ! -f $logPath )
	{
		$errormsg = "Not found $logFile file.";
		my $body =
		  { description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 404, body => $body } );
	}
	else
	{
# Download function ends communication if itself finishes successful. It is not necessary send "200 OK" msg
		require Zevenet::System::Log;
		$errormsg = &downloadLog( $logFile );
		if ( $errormsg )
		{
			$errormsg = "Error, downloading backup.";
		}
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };

	&httpResponse( { code => 404, body => $body } );
}

1;
