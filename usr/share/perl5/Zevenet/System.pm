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
Function: zsystem

	Run a command with tuned system parameters.

Parameters:
	exec - Command to run.

Returns:
	integer - ERRNO or return code.

See Also:
	<runFarmGuardianStart>, <_runHTTPFarmStart>, <runHTTPFarmCreate>, <_runGSLBFarmStart>, <_runGSLBFarmStop>, <runFarmReload>, <runGSLBFarmCreate>, <setGSLBFarmStatus>
=cut
sub zsystem
{
	my ( @exec ) = @_;

	#~ system ( ". /etc/profile && @exec" ); 
	my $out = `. /etc/profile && @exec`;
	
	my $error = $?;
	&zenlog ("running: @exec");
	&zenlog ("output: $out") if ( $error );
	
	return $error;
}

=begin nd
Function: getDns

	Get the dns servers.

Parameters:
	none - .

Returns:
	scalar - Hash reference.

	Example:

	$dns = {
			primary => "value",
			secundary => "value",
	};

See Also:
	zapi/v3/system.cgi
=cut
sub getDns
{
	my $dns;
	my $dnsFile = &getGlobalConfiguration( 'filedns' );

	if ( !-e $dnsFile )
	{
		return undef;
	}
	tie my @dnsArr, 'Tie::File', $dnsFile;

	#primary
	my @aux = split ( ' ', $dnsArr[0] );
	$dns->{ 'primary' } = $aux[1];

	# secondary
	if ( defined $dnsArr[1] )
	{
		@aux = split ( ' ', $dnsArr[1] );
		$dns->{ 'secondary' } = $aux[1];
	}
	else
	{
		$dns->{ 'secondary' } = "";
	}
	untie @dnsArr;

	return $dns;
}

=begin nd
Function: setDns

	Set a primary or secondary dns server.

Parameters:
	dns - 'primary' or 'secondary'.
	value - ip addres of dns server.

Returns:
	none - .

Bugs:
	Returned value.

See Also:
	zapi/v3/system.cgi
=cut
sub setDns
{
	my ( $dns, $value ) = @_;
	my $dnsFile = &getGlobalConfiguration( 'filedns' );
	my $output;

	if ( !-e $dnsFile )
	{
		$output = system ( &getGlobalConfiguration( 'touch' ) . " $dnsFile" );
	}

	tie my @dnsArr, 'Tie::File', $dnsFile;
	my $line;

	if ( $dns eq 'primary' )
	{
		$line = 0;
	}

	# secondary:   $dns eq 'secondary'
	else
	{
		$line = 1;
	}
	$dnsArr[$line] = "nameserver $value";

	untie @dnsArr;
	return $output;
}

=begin nd
Function: getSsh

	Returns hash reference to ssh configuration.

Parameters:
	none - .

Returns:
	scalar - Hash reference.

	Example:

	$ssh = {
			'port'   => 22,
			'listen' => "*",
	};

See Also:
	zapi/v3/system.cgi, dos.cgi
=cut
sub getSsh
{
	my $sshFile = &getGlobalConfiguration( 'sshConf' );
	my $ssh     = {                                       # conf
				'port'   => 22,
				'listen' => "*",
	};
	my $listen_format = &getValidFormat( 'ssh_listen' );

	if ( !-e $sshFile )
	{
		return undef;
	}
	else
	{
		tie my @file, 'Tie::File', $sshFile;
		foreach my $line ( @file )
		{
			if ( $line =~ /^Port\s+(\d+)/ )
			{
				$ssh->{ 'port' } = $1;
			}
			elsif ( $line =~ /^ListenAddress\s+($listen_format)/ )
			{
				$ssh->{ 'listen' } = $1;
			}
		}
		untie @file;
	}

	$ssh->{ 'listen' } = '*' if ( $ssh->{ 'listen' } eq '0.0.0.0' );
	return $ssh;
}

=begin nd
Function: setSsh

	Set ssh configuration.

	To listen on all the ip addresses set 'listen' to '*'.

Parameters:
	sshConf - Hash reference with ssh configuration.

	Example:

	$ssh = {
			'port'   => 22,
			'listen' => "*",
	};

Returns:
	integer - ERRNO or return code of ssh restart.

See Also:
	zapi/v3/system.cgi
=cut
sub setSsh
{
	my ( $sshConf ) = @_;
	my $sshFile     = &getGlobalConfiguration( 'sshConf' );
	my $output      = 1;
	my $index       = 5
	  ; # default, it is the line where will add port and listen if one of this doesn't exist

	# create flag to check all params are changed
	my $portFlag   = 1 if ( exists $sshConf->{ 'port' } );
	my $listenFlag = 1 if ( exists $sshConf->{ 'listen' } );
	$sshConf->{ 'listen' } = '0.0.0.0' if ( $sshConf->{ 'listen' } eq '*' );

	if ( !-e $sshFile )
	{
		&zenlog( "SSH configuration file doesn't exist." );
		return -1;
	}

	tie my @file, 'Tie::File', $sshFile;
	foreach my $line ( @file )
	{
		if ( $portFlag )
		{
			if ( $line =~ /^Port\s+/ )
			{
				$line     = "Port $sshConf->{ 'port' }";
				$output   = 0;
				$portFlag = 0;
			}
		}
		if ( $listenFlag )
		{
			if ( $line =~ /^ListenAddress\s+/ )
			{
				$line       = "ListenAddress $sshConf->{ 'listen' }";
				$listenFlag = 0;
			}
		}
	}

	# Didn't find port and required a change
	if ( $portFlag )
	{
		splice @file, $index, 0, "Port $sshConf->{ 'port' }";
	}

	# Didn't find listen and required a change
	if ( $listenFlag )
	{
		splice @file, $index, 0, "ListenAddress $sshConf->{ 'listen' }";
	}
	untie @file;

	# restart service to apply changes
	$output = system ( &getGlobalConfiguration( 'sshService' ) . " restart" );
	
	&setDOSParam( 'ssh_brute_force', 'port', $sshConf->{ 'port' } );
	# restart sshbruteforce ipds rule if this is actived
	if ( &getDOSParam( 'ssh_brute_force', 'status' ) eq 'up' )
	{
		&setDOSParam( 'ssh_brute_force', 'status', 'down' );
		&setDOSParam( 'ssh_brute_force', 'status', 'up' );
	}
	else
	{
		
	}

	return $output;
}

=begin nd
Function: getHttpServerPort

	Get the web GUI port.

Parameters:
	none - .

Returns:
	integer - Web GUI port.

See Also:
	zapi/v3/system.cgi
=cut
sub getHttpServerPort
{
	my $gui_port;    # output

	my $confhttp = &getGlobalConfiguration( 'confhttp' );
	open my $fh, "<", "$confhttp";

	# read line matching 'server!bind!1!port = <PORT>'
	my $config_item = 'server!bind!1!port';

	while ( my $line = <$fh> )
	{
		if ( $line =~ /$config_item/ )
		{
			( undef, $gui_port ) = split ( "=", $line );
			last;
		}
	}

	#~ my @httpdconffile = <$fr>;
	close $fh;

	chomp ( $gui_port );
	$gui_port =~ s/\s//g;
	$gui_port = 444 if ( !$gui_port );

	return $gui_port;
}

=begin nd
Function: setHttpServerPort

	Set the web GUI port.

Parameters:
	httpport - Port number.

Returns:
	none - .

See Also:
	zapi/v3/system.cgi
=cut
sub setHttpServerPort
{
	my ( $httpport ) = @_;
	$httpport =~ s/\ //g;

	my $confhttp = &getGlobalConfiguration( 'confhttp' );
	use Tie::File;
	tie my @array, 'Tie::File', "$confhttp";
	@array[2] = "server!bind!1!port = $httpport\n";
	untie @array;
}

=begin nd
Function: getHttpServerIp

	Get the GUI service ip address

Parameters:
	none - .

Returns:
	scalar - GUI ip address or '*' for all local addresses

See Also:
	zapi/v3/system.cgi, zenloadbalancer
=cut
sub getHttpServerIp
{
	my $gui_ip;        # output

	my $confhttp = &getGlobalConfiguration( 'confhttp' );
	open my $fh, "<", "$confhttp";

	# read line matching 'server!bind!1!interface = <IP>'
	my $config_item = 'server!bind!1!interface';

	while ( my $line = <$fh> )
	{
		if ( $line =~ /$config_item/ )
		{
			( undef, $gui_ip ) = split ( "=", $line );
			last;
		}
	}

	close $fh;

	chomp ( $gui_ip );
	$gui_ip =~ s/\s//g;

	if ( &ipisok( $gui_ip, 4 ) ne "true" )
	{
		$gui_ip = "*";
	}

	return $gui_ip;
}

=begin nd
Function: setHttpServerIp

	Set the GUI service ip address

Parameters:
	ip - IP address.

Returns:
	none - .

See Also:
	zapi/v3/system.cgi
=cut
sub setHttpServerIp
{
	my $ip = shift;

	my $confhttp = &getGlobalConfiguration( 'confhttp' );

	#action save ip
	use Tie::File;
	tie my @array, 'Tie::File', "$confhttp";
	if ( $ip =~ /^\*$/ )
	{
		@array[1] = "#server!bind!1!interface = \n";
		&zenlog( "The interface where is running is --All interfaces--" );
	}
	else
	{
		@array[1] = "server!bind!1!interface = $ip\n";

		#~ if ( &ipversion( $ipgui ) eq "IPv6" )
		#~ {
		#~ @array[4] = "server!ipv6 = 1\n";
		#~ &zenlog(
		#~ "The interface where is running the GUI service is: $ipgui with IPv6" );
		#~ }
		#~ elsif ( &ipversion( $ipgui ) eq "IPv4" )
		#~ {
		#~ @array[4] = "server!ipv6 = 0\n";
		#~ &zenlog(
		#~ "The interface where is running the GUI service is: $ipgui with IPv4" );
		#~ }
	}
	untie @array;
}

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

=begin nd
Function: getTotalConnections

	Get the number of current connections on this appliance.

Parameters:
	none - .

Returns:
	integer - The number of connections.

See Also:
	zapi/v3/system_stats.cgi
=cut
sub getTotalConnections
{
	my $conntrack = &getGlobalConfiguration ( "conntrack" );
	my $conns = `$conntrack -C`;
	$conns =~ s/(\d+)/$1/;
	$conns += 0;
	
	return $conns;
}

=begin nd
Function: indexOfElementInArray

	Get the index of the first position where an element if found in an array.

Parameters:
	searched_element - Element to search.
	array_ref        - Reference to the array to be searched.

Returns:
	integer - Zero or higher if the element was found. -1 if the element was not found. -2 if no array reference was received.

See Also:
	Zapi v3: <new_bond>
=cut
sub indexOfElementInArray
{
	my $searched_element = shift;
	my $array_ref = shift;

	if ( ref $array_ref ne 'ARRAY' )
	{
		return -2;
	}
	
	my @arrayOfElements = @{ $array_ref };
	my $index = 0;
	
	for my $list_element ( @arrayOfElements )
	{
		if ( $list_element eq $searched_element )
		{
			last;
		}

		$index++;
	}

	# if $index is greater than the last element index
	if ( $index > $#arrayOfElements )
	{
		# return an invalid index
		$index = -1;
	}

	return $index;
}

1;
