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
Function: checkport

	Check if a TCP port is open in a local or remote IP.

Parameters:
	host - IP address (or hostname?).
	port - TCP port number.

Returns:
	boolean - string "true" or "false".

See Also:
	<getRandomPort>
=cut
#check if a port in a ip is up
sub checkport    # ($host, $port)
{
	my ( $host, $port ) = @_;

	# check local ports;
	if ( $host eq '127.0.0.1' || $host =~ /local/ )
	{
		my $flag = system ( "netstat -putan | grep $port" );
		if ( $flag )
		{
			return "true";
		}
	}

	# check remote ports
	else
	{
		use IO::Socket;
		my $sock = new IO::Socket::INET(
										 PeerAddr => $host,
										 PeerPort => $port,
										 Proto    => 'tcp'
		);

		if ( $sock )
		{
			close ( $sock );
			return "true";
		}
		else
		{
			return "false";
		}
	}
	return "false";
}

=begin nd
Function: ipisok

	Check if a string has a valid IP address format.

Parameters:
	checkip - IP address string.
	version - 4 or 6 to validate IPv4 or IPv6 only. Optional.

Returns:
	boolean - string "true" or "false".
=cut
#check if a ip is ok structure
sub ipisok    # ($checkip, $version)
{
	my $checkip = shift;
	my $version = shift;
	my $return  = "false";

	use Data::Validate::IP;

	if ( !$version || $version != 6 )
	{
		if ( is_ipv4( $checkip ) )
		{
			$return = "true";
		}
	}

	if ( !$version || $version != 4 )
	{
		if ( is_ipv6( $checkip ) )
		{
			$return = "true";
		}
	}

	return $return;
}

=begin nd
Function: ipversion

	Returns IP version number of input IP address.

Parameters:
	checkip - string to .

Returns:
	list - All IP addresses up.

Bugs:
	Fix return on non IPv4 or IPv6 valid address.
=cut
#check if a ip is IPv4 or IPv6
sub ipversion    # ($checkip)
{
	my $checkip = shift;
	my $output  = "-";

	use Data::Validate::IP;

	if ( is_ipv4( $checkip ) )
	{
		$output = 4;
	}
	elsif ( is_ipv6( $checkip ) )
	{
		$output = 6;
	}

	return $output;
}

=begin nd
Function: ipinrange

	[NOT USED] Check if an IP is in a range.

Parameters:
	netmask - .
	toip - .
	newip - .

Returns:
	boolean - string "true" or "false".

Bugs:
	NOT USED
=cut
#function checks if ip is in a range
sub ipinrange    # ($netmask, $toip, $newip)
{
	my ( $netmask, $toip, $newip ) = @_;

	use Net::IPv4Addr qw( :all );

	#$ip_str1="10.234.18.13";
	#$mask_str1="255.255.255.0";
	#$cidr_str2="10.234.18.23";
	#print "true" if ipv4_in_network( $toip, $netmask, $newip );
	if ( ipv4_in_network( $toip, $netmask, $newip ) )
	{
		return "true";
	}
	else
	{
		return "false";
	}
}

=begin nd
Function: ifexist

	Check if interface exist.

	Look for link interfaces, Virtual interfaces return "false".
	If the interface is IFF_RUNNING or configuration file exists return "true".
	If interface found but not IFF_RUNNING nor configutaion file exists returns "created".

Parameters:
	nif - network interface name.

Returns:
	string - "true", "false" or "created".

Bugs:
	"created"
=cut
#function check if interface exist
sub ifexist    # ($nif)
{
	my $nif = shift;

	use IO::Socket;
	use IO::Interface qw(:flags);
	my $s          = IO::Socket::INET->new( Proto => 'udp' );
	require Zevenet::Net::Interface;
	my @interfaces = &getInterfaceList();
	my $configdir  = &getGlobalConfiguration( 'configdir' );

	my $status;
	for my $if ( @interfaces )
	{
		if ( $if eq $nif )
		{
			my $flags = $s->if_flags( $if );

			if   ( $flags & IFF_RUNNING ) { $status = "up"; }
			else                          { $status = "down"; }

			if ( $status eq "up" || -e "$configdir/if_$nif\_conf" )
			{
				return "true";
			}

			return "created";
		}
	}

	return "false";
}

=begin nd
Function: isValidPortNumber

	Check if the input is a valid port number.

Parameters:
	port - Port number.

Returns:
	boolean - "true" or "false".

See Also:
	snmp_functions.cgi, check_functions.cgi, zapi/v3/post.cgi, zapi/v3/put.cgi
=cut
sub isValidPortNumber    # ($port)
{
	my $port = shift;
	my $valid;

	if ( $port >= 1 && $port <= 65535 )
	{
		$valid = 'true';
	}
	else
	{
		$valid = 'false';
	}

	return $valid;
}

1;
