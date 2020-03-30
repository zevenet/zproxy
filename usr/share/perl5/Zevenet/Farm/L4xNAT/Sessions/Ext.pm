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

use Zevenet::Farm::L4xNAT::Config;
use Zevenet::Farm::L4xNAT::Sessions;

=begin nd
Function: addL4FarmSession

	It adds a static session to the l4xnat farm.

Parameters:
	farmname - Farm name
	session - Session value. It is the session tocken used to forward the connection
	backend - Backend id. It is the backend id where the connection will be sent when the client info matches with the session

Returns:
	Error code - 0 on success, 2 if the session already exists or 1 on failure

=cut

sub addL4FarmSession
{
	my ( $farm_name, $session, $bck ) = @_;

	require Zevenet::Farm::L4xNAT::Action;

	# delete the dynamic session if it exists in another backend
	my $session_obj = &getL4FarmSession( $farm_name, $session );
	if ( defined $session_obj )
	{
		if ( $session_obj->{ type } eq "static" )
		{
			return 2;
		}

		# else remove dynamic session
		my $err = &delL4FarmSessionNft( $farm_name, $session );
		return 1 if $err;
	}

	# translate to nftlb format
	$session =~ s/_/ \. /;

	my $configdir     = &getGlobalConfiguration( 'configdir' );
	my $farm_filename = &getFarmFile( $farm_name );
	my $err = &sendL4NlbCmd(
		{
		   farm   => $farm_name,
		   uri    => "/farms",
		   file   => "$configdir/$farm_filename",
		   method => "PUT",
		   body =>
			 qq({"farms" : [ { "name" : "$farm_name", "sessions" : [ { "client" : "$session", "backend" : "bck$bck" } ] } ] })
		}
	);
	$err = 1 if $err;

	return $err;
}

=begin nd
Function: delL4FarmSession

	It deletes a static session of a l4xnat farm.

Parameters:
	farmname - Farm name
	session - Session value. It is the session tocken used to forward the connection

Returns:
	Error code - 0 on success or another value on failure.

=cut

sub delL4FarmSession
{
	my ( $farm_name, $session ) = @_;

	my $err = &delL4FarmSessionNft( $farm_name, $session );
	if ( !$err )
	{
		$err = &saveL4Conf( $farm_name );
	}

	return $err;
}

sub delL4FarmSessionNft
{
	my ( $farm_name, $session ) = @_;

	require Zevenet::Farm::L4xNAT::Action;

	# translate to nftlb format
	$session =~ s/_/ \. /;

	my $err = &httpNlbRequest(
							 {
							   farm   => $farm_name,
							   uri    => "/farms/" . $farm_name . '/sessions/' . $session,
							   method => "DELETE",
							 }
	);

	return $err;
}

=begin nd
Function: validateL4FarmSession

	It validates the session with the type of persistence configured in the farm

Parameters:
	persistence - Persistence type
	session - Session value. It is the session tocken used to forward the connection

Returns:
	Error code - It returns 0 if the session is not valid, or 1 if it is valid

=cut

sub validateL4FarmSession
{
	my ( $persis_type, $session ) = @_;
	my $suc = 0;

	my $mac_reg  = &getValidFormat( 'mac_addr' );
	my $ip_reg   = &getValidFormat( 'ipv4v6' );
	my $port_reg = &getValidFormat( 'port' );

	$suc = 1
	  if (
		      ( $persis_type eq 'srcmac'         and $session =~ /^$mac_reg$/ )
		   or ( $persis_type eq 'srcport'        and $session =~ /^$port_reg$/ )
		   or ( $persis_type =~ /^(?:srcip|ip)$/ and $session =~ /^$ip_reg$/ )
		   or (     $persis_type =~ /^(?:srcip_srcport|srcip_dstport)$/
				and $session =~ /^${ip_reg}_$port_reg/ )
	  );

	return $suc;
}

1;

