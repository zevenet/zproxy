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

use Config::Tiny;
use Zevenet::Config;
use Zevenet::Log;
include 'Zevenet::Notify';

( my $section, my $pattern ) = @ARGV;

my $command;
my ( $subject, $bodycomp ) = &getSubjectBody( $pattern );
my $logger = &getGlobalConfiguration( 'logger' );

if ( $subject eq "error" || !$bodycomp )
{
	# log the pattern is a trigger for the sec event
	# &zenlog ( "Error parsing the alert pattern: '$pattern'", "error", "notif" );
	exit 1;
}

my $error = &sendByMail( $subject, $bodycomp, $section );

exit $error;

# return:   @array = [ $subject, $body ]
# my ( $subject, $body ) = getSubjectBody( $msg )
sub getSubjectBody    # &getSubjectBody ( $msg )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $msg ) = @_;

	my @output;
	my $subject;
	my $body;

	my ( $date, $host, $program, $ip, $port, $status, $farm, $service, $pid );
	my $auxBody = "";

	# Keep date, host and program from log msg
	# Sep  1 15:59:06 maqvir gdnsd[18513]:
	if ( $msg =~ s/(\w+\s+\d+\s+\d+:\d+:\d+)\s+([\w-]+)\s+(\w+)(\[\d+\])?\: // )
	{
		$date    = $1;
		$host    = $2;
		$program = $3;
		$pid     = $4;
		$pid =~ s/[\[\]]//g;
	}
	else
	{
		&zenlog( "Error getting system information", 'error', "notif" );
	}

	# Gdnsd msg
	# example:
	# state of '192.168.0.167/tcp_80' changed from UP/5 to DOWN/10
	if (    $program =~ /gdnsd/
		 && $msg =~
		 /state of \'(\d+\.\d+\.\d+\.\d+)\/(tcp|.+_fg)_(\d+)\' .+ to (DOWN|UP)/ )
	{
		$ip      = $1;
		$port    = $3;
		$status  = $4;
		$service = $2;
		$farm    = &getGSLBFarm( $pid );

		if ( $service eq 'tcp' )
		{
			$program = "It has been";
		}
		else
		{
			$program = "Farmguardian";
		}

		$service =~ s/^tcp$//;
		$service =~ s/_fg//;

		if ( $farm && !$service ) { $auxBody = "(farm: '$farm')"; }
		if ( $farm && $service )  { $auxBody = "(farm: '$farm', service: '$service')"; }

		$body .= "\n"
		  . "$program detected a status change to $status $auxBody\n"
		  . "Zevenet Server: $host\n"
		  . "Backend: $ip\n"
		  . "Port: $port\n";

		$subject = "Backend $ip changed to $status";

	}

# l7 proxy msg
# example:
# (7f4dccf24700) BackEnd 192.168.0.172:80 dead (killed) in farm: 'test', service: 'srv1'
	elsif ( ( $program =~ /zproxy|pound/ || $program =~ /farmguardian/ )
		&& $msg =~
		/BackEnd (\d+\.\d+\.\d+\.\d+):(\d+)? (\w+)(?: \(\w+\))? in farm: '([\w-]+)'(, service: '([\w-]+)')?/
	  )
	{
		$ip      = $1;
		$port    = $2;
		$status  = $3;
		$farm    = $4;
		$service = $5;

		if ( $service =~ /'(.+)'/ ) { $service = "$1"; }

		if    ( $program =~ /zproxy|pound/ ) { $program = "It has been"; }
		elsif ( $program =~ /farmguardian/ ) { $program = "Farmguardian"; }

		if ( $status =~ /dead/ || $status =~ /down/ ) { $status = "DOWN"; }
		elsif ( $status =~ /resurrect/ ) { $status = "UP"; }

		if ( $farm && !$service ) { $auxBody = "(farm: '$farm')"; }
		if ( $farm && $service )  { $auxBody = "(farm: '$farm', service: '$service')"; }

		$body .= "\n"
		  . "$program detected a status change to $status $auxBody\n"
		  . "Zevenet Server: $host\n"
		  . "Backend: $ip\n"
		  . "Port: $port\n";

		$subject = "Backend $ip changed to $status";

	}

	# Cluster msg
	# example:
	# [WARNING] Switching to state: MASTER
	elsif (
		$program =~ /Keepalived_vrrp/

		#~ && $msg =~ /\[WARNING\] Switching to state: (\w+)/ )
		&& $msg =~ /\(ZCluster\) Entering (\w+) STATE/
	  )
	{
		$status = $1;

		$body .= "\n"
		  . "Zevenet server switched to $status\n"
		  . "Zevenet Server: $host\n"
		  . "Current Status: $status\n";

		$subject = "Zevenet server \"$host\" switched to $status";
	}

	else
	{
		$subject = "error";
	}

	$body .= "\n\nDate/Time: $date\n\n";

	push @output, $subject, $body;
	return @output;
}

#   &getGSLBFarm ( $pid )
sub getGSLBFarm
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $pid ) = @_;

	my $grep = &getGlobalConfiguration( 'grep_bin' );
	my $ps   = &getGlobalConfiguration( 'ps' );

	my $farm;
	my $cmd = "$ps -ef | $grep $pid";
	my @aux = @{ &logAndGet( $cmd, "array" ) };

	foreach my $line ( @aux )
	{
		if ( $line =~ /config\/(.+)_gslb\.cfg/ ) { $farm = $1; }
	}

	return $farm;
}

