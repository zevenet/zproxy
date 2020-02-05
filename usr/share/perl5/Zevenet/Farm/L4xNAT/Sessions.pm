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
Function: getL4FarmSessions

	Get a list of the current l4 sessions in a farm.

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

sub getL4FarmSessions
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
		$it = &parseL4Session( $farm, $s );
		$it->{ client } = $client_id++;
		push @sessions, $it;
	}

	return \@sessions;
}

=begin nd
Function: parseSession

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

sub parseL4Session
{
	my $farm = shift;
	my $s    = shift;

	my $obj = {
				'session' => $s->{ client },
				'type'    => ( exists $s->{ expiration } ) ? 'dynamic' : 'static',
	};

	if ( $s->{ backend } =~ /bck(\d+)/ )
	{
		$obj->{ id } = $1;
	}

	return $obj;
}

1;
