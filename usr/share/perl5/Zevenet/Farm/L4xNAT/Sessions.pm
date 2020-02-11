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

=begin nd
Function: parseL4FarmSessions

	It transform the session output of nftlb output in a Zevenet session struct

Parameters:
	farmname - Farm struct with the farm configuration
	session ref - It is the session hash returned for nftlb. Example:
		session = {
			'expiration' => '1h25m31s364ms',
			'backend' => 'bck0',
			'client' => '192.168.10.162'
		}

Returns:
	Hash ref - It is a hash with two keys: 'session' returns the session token and
		'id' returns the backen linked with the session token. If any session was found
		the function will return 'undef'.

	ref = {
		"id" : 3,
		"session" : "192.168.1.186"
	}

=cut

sub parseL4FarmSessions
{
	my $farm = shift;
	my $s    = shift;

	my $obj = {
				'session' => $s->{ client },
				'type'    => ( exists $s->{ expiration } ) ? 'dynamic' : 'static',
				'ttl'     => ( exists $s->{ expiration } ) ? $s->{ expiration } : undef,
	};

	if ( $s->{ backend } =~ /bck(\d+)/ )
	{
		$obj->{ id } = $1;
	}

	return $obj;
}

=begin nd
Function: listL4FarmSessions

	Get a list of the static and dynamic l4 sessions in a farm. Using nftlb

Parameters:
	farmname - Farm name

Returns:
	array ref - Returns a list of hash references with the following parameters:
		"client" is the client position entry in the session table
		"id" is the backend id assigned to session
		"session" is the key that identifies the session

		[
			{
			"client" : 0,
			"id" : 3,
			"session" : "192.168.1.186"
			}
		]

=cut

sub listL4FarmSessions
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname = shift;

	require Zevenet::Lock;
	require Zevenet::JSON;
	require Zevenet::Nft;

	my $nft_bin  = &getGlobalConfiguration( 'nft_bin' );
	my $farm     = &getL4FarmStruct( $farmname );
	my @sessions = ();
	my $data     = 0;
	my $it;

	return [] if ( $farm->{ persist } eq "" );

	my $session_tmp = "/tmp/session_$farmname.data";
	my $lock_f      = &getLockFile( $session_tmp );
	my $lock_fd     = &openlock( $lock_f, '>' );
	my $err = &httpNlbRequest(
							   {
								 method => "GET",
								 uri    => "/farms/" . $farmname . '/sessions',
								 file   => $session_tmp,
							   }
	);

	my $nftlb_resp;
	if ( !$err )
	{
		$nftlb_resp = &decodeJSONFile( $session_tmp );
	}

	close $lock_fd;
	return [] if ( $err or !defined $nftlb_resp );

	my $client_id = 0;
	foreach my $s ( @{ $nftlb_resp->{ sessions } } )
	{
		$it = &parseL4FarmSessions( $farm, $s );
		$it->{ client } = $client_id++;
		push @sessions, $it;
	}

	return \@sessions;
}

=begin nd
Function: getL4FarmSession

	It selects an session item of the sessions list. The session key is used to select the item

Parameters:
	farmname - Farm name
	session - Session value. It is the session tocken used to forward the connection

Returns:
	Hash ref - Returns session struct with information about the session.
		"client" is the client position entry in the session table
		"id" is the backend id assigned to session
		"session" is the key that identifies the session

		[
			{
			"client" : 0,
			"id" : 3,
			"session" : "192.168.1.186"
			}
		]

=cut

sub getL4FarmSession
{
	my $farm    = shift;
	my $session = shift;

	my $list = &listL4FarmSessions( $farm );

	foreach my $s ( @{ $list } )
	{
		return $s if ( $s->{ session } eq $session );
	}

	return undef;
}

=begin nd
Function: addL4FarmSession

	It adds a static session to the l4xnat farm.

Parameters:
	farmname - Farm name
	session - Session value. It is the session tocken used to forward the connection
	backend - Backend id. It is the backend id where the connection will be sent when the client info matches with the session

Returns:
	Error code - 0 on success or another value on failure.

=cut

sub addL4FarmSession
{
	my ( $farm_name, $session, $bck ) = @_;

	require Zevenet::Farm::L4xNAT::Action;

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

	require Zevenet::Farm::L4xNAT::Action;

	my $configdir     = &getGlobalConfiguration( 'configdir' );
	my $farm_filename = &getFarmFile( $farm_name );

	my $err = &httpNlbRequest(
							 {
							   farm   => $farm_name,
							   uri    => "/farms/" . $farm_name . '/sessions/' . $session,
							   method => "DELETE",
							 }
	);

	if ( !$err )
	{
		$err = &saveL4Conf( $farm_name );
	}

	return $err;
}

=begin nd
Function: validateL4FarmSession

	It deletes a static session of a l4xnat farm.

Parameters:
	farmname - Farm name
	session - Session value. It is the session tocken used to forward the connection

Returns:
	Error code - 0 on success or another value on failure.

=cut

#~ sub validateL4FarmSession
#~ {
#~ my ($persis_type, $session) = @_;
#~ my $suc = 0;

#~ return $suc;
#~ }

1;
