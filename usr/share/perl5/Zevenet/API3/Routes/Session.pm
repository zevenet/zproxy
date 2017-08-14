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

require CGI::Session;


# POST CGISESSID to login
POST qr{^/session$} => \&session_login;

#  DELETE session to logout
DELETE qr{^/session$} => \&session_logout;


sub session_login
{
	my $session = CGI::Session->new( &getCGI() );

	if ( $session && !$session->param( 'is_logged_in' ) )
	{
		my ( $username, $password ) = &getAuthorizationCredentials();

		if ( &authenticateCredentials( $username, $password ) )
		{
			# successful authentication
			&zenlog( "Login successful for user: $username" );

			$session->param( 'is_logged_in', 1 );
			$session->param( 'username',     $username );
			$session->expire( 'is_logged_in', '+30m' );

			require Zevenet::Certificate::Activation;

			my ( $header ) = split ( "\r\n", $session->header() );
			my ( undef, $session_cookie ) = split ( ': ', $header );
			my $key =  &keycert();
			my $host = &getHostname();

			&httpResponse(
						   {
								body => { key	=> $key, host => $host },
								code    => 200,
								headers => { 'Set-cookie' => $session_cookie },
						   }
			);
		}
		else    # not validated credentials
		{
			&zenlog( "Login failed for username: $username" );

			$session->delete();
			$session->flush();

			&httpResponse( { code => 401 } );
		}
	}
}

sub session_logout
{
	my $cgi = &getCGI();

	if ( $cgi->http( 'Cookie' ) )
	{
		my $session = new CGI::Session( $cgi );

		if ( $session && $session->param( 'is_logged_in' ) )
		{
			my $username = $session->param( 'username' );
			my $ip_addr  = $session->param( '_SESSION_REMOTE_ADDR' );

			&zenlog( "Logged out user $username from $ip_addr" );

			$session->delete();
			$session->flush();

			&httpResponse( { code => 200 } );
		}
	}

	# with ZAPI key or expired cookie session
	&httpResponse( { code => 400 } );
}

1;
