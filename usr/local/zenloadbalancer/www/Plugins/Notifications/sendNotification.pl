#!/usr/bin/perl

###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This library is free software; you can redistribute it and/or modify it
#     under the terms of the GNU Lesser General Public License as published
#     by the Free Software Foundation; either version 2.1 of the License, or
#     (at your option) any later version.
#
#     This library is distributed in the hope that it will be useful, but
#     WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
#     General Public License for more details.
#
#     You should have received a copy of the GNU Lesser General Public License
#     along with this library; if not, write to the Free Software Foundation,
#     Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
###############################################################################

use Config::Tiny;

( my $section, my $pattern ) = @ARGV;

my $body;
my $command;
my ( $subject, $bodycomp ) = &getSubjectBody( $pattern );

if ( $subject eq "error" || !$bodycomp )
{
	exit 1;
}

$body = "\n***** Notifications *****\n\n" . "Alerts: $section Notification\n";
$body .= $bodycomp;

$command .= &getData( 'bin' );
$command .= " --to " . &getData( 'to' );
$command .= " --from " . &getData( 'from' );
$command .= " --server " . &getData( 'server' );
$command .= " --auth " . &getData( 'auth' );
$command .= " --auth-user " . &getData( 'auth-user' );
$command .= " --auth-password " . &getData( 'auth-password' );
if ( 'true' eq &getData( 'tls' ) ) { $command .= " -tls"; }
$command .=
    " --header \"Subject: "
  . &getData( 'PrefixSubject', $section )
  . " $subject\"";
$command .= " --body \"$body\"";

#not print
$command .= " 1>/dev/null";

#~ print "$body";
system ( $command );

# return:   @array = [ $subject, $body ]
# my ( $subject, $body ) = getSubjectBody( $msg )
sub getSubjectBody    # &getSubjectBody ( $msg )
{
	my ( $msg ) = @_;

	my @output;
	my $subject;
	my $body;

	my ( $date, $host, $program, $ip, $port, $status, $farm, $service, $pid );
	my $auxBody;

	# Keep date, host and program from log msg
	# Sep  1 15:59:06 maqvir gdnsd[18513]:
	if ( $msg =~ s/(\w+\s+\d+\s+\d+:\d+:\d+)\s+(\w+)\s+(\w+)(\[\d+\])?\: // )
	{
		$date    = $1;
		$host    = $2;
		$program = $3;
		$pid     = $4;
		$pid =~ s/[\[\]]//g;
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

		if ( $service eq tcp )
		{
			$program = "Farmguardian";
		}

		$service =~ s/^tcp$//;
		$service =~ s/_fg//;

		if ( $farm && !$service ) { $auxBody = "(farm: '$farm')"; }
		if ( $farm && $service )  { $auxBody = "(farm: '$farm', service: '$service')"; }

		$body .= "\n"
		  . "$program detected a status change to $status $auxBody\n"
		  . "Zen Server: $host\n"
		  . "Backend: $ip\n"
		  . "Port: $port\n";

		$subject = "Backend $ip changed to $status";

	}

# pound msg
# example:
# (7f4dccf24700) BackEnd 192.168.0.172:80 dead (killed) in farm: 'test', service: 'srv1'
	elsif ( ( $program =~ /pound/ || $program =~ /farmguardian/ )
		&& $msg =~
		/BackEnd (\d+\.\d+\.\d+\.\d+):(\d+) (\w+)(?: \(\w+\))? in farm: '(\w+)'(, service: '(\w+)')?/
	  )
	{
		$ip      = $1;
		$port    = $2;
		$status  = $3;
		$farm    = $4;
		$service = $5;

		if    ( $service =~ /'(.+)'/ )        { $service = "$1"; }

		if    ( $program =~ /pound/ )        { $program = "It has been"; }
		elsif ( $program =~ /farmguardian/ ) { $program = "Farmguardian"; }

		if ( $status =~ /dead/ || $status =~ /down/ ) { $status = "DOWN"; }
		elsif ( $status =~ /resurrect/ ) { $status = "UP"; }

		if ( $farm && !$service ) { $auxBody = "(farm: '$farm')"; }
		if ( $farm && $service )  { $auxBody = "(farm: '$farm', service: '$service')"; }

		$body .= "\n"
		  . "$program detected a status change to $status $auxBody\n"
		  . "Zen Server: $host\n"
		  . "Backend: $ip\n"
		  . "Port: $port\n";

		$subject = "Backend $ip changed to $status";

	}

	# Cluster msg
	# example:
	# [WARNING] Switching to state: MASTER
	elsif (    $program =~ /ucarp/
			&& $msg =~ /\[WARNING\] Switching to state: (\w+)/ )
	{
		$status = $1;

		$body .= "\n"
		  . "Zen server switched to $status\n"
		  . "Zen Server: $host\n"
		  . "Current Status: $status\n";

		$subject = "Zen server \"$host\" switched to $status";

	}

	else
	{
		$subject = "error";
	}

	$body .= "\n\nDate/Time: $date\n\n";

	push @output, $subject, $body;
	return @output;
}

#  &getData ( $key, $section )
#  &getData ( $key )
sub getData
{
	my ( $key, $section ) = @_;
	my $argumentos = scalar @_;
	my $data;
	my $fileHandle;
	my $fileName;

	if ( $argumentos == 1 )
	{
		$section  = 'Smtp';
		$fileName = "/usr/local/zenloadbalancer/www/Plugins/Notifications/Senders.conf";
	}
	else
	{
		$fileName = "/usr/local/zenloadbalancer/www/Plugins/Notifications/Alerts.conf";
	}

	if ( !-f $fileName )
	{
		print "don't find $fileName.";
	}
	else
	{
		$fileHandle = Config::Tiny->read( $fileName );
		$data       = $fileHandle->{ $section }->{ $key };
	}

	return $data;
}

#   &getGSLBFarm ( $pid )
sub getGSLBFarm
{
	my ( $pid ) = @_;
	my $farm;

	my @aux = `ps -ef | grep $pid `;

	$pr = @aux;

	foreach my $line ( @aux )
	{
		if ( $line =~ /config\/(.+)_gslb\.cfg/ ) { $farm = $1; }
	}

	return $farm;
}
