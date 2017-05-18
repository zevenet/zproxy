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

my $passfile = "/etc/shadow";

sub changePassword    #($user, $newpass, $verifypass)
{
	my ( $user, $newpass, $verifypass ) = @_;

	##write \$ instead $
	$newpass =~ s/\$/\\\$/g;
	$verifypass =~ s/\$/\\\$/g;

	my $output = 0;
	chomp ( $newpass );
	chomp ( $verifypass );

	##no move the next lines
	my @run = `
/usr/bin/passwd $user 2>/dev/null<<EOF
$newpass
$verifypass
EOF
	`;

	$output = $?;

	return $output;
}

sub checkValidUser    #($user,$curpasswd)
{
	my ( $user, $curpasswd ) = @_;

	my $output = 0;
	use Authen::Simple::Passwd;
	my $passwd = Authen::Simple::Passwd->new( path => "$passfile" );
	if ( $passwd->authenticate( $user, $curpasswd ) )
	{
		$output = 1;
	}

	return $output;
}

sub verifyPasswd    #($newpass, $trustedpass)
{
	my ( $newpass, $trustedpass ) = @_;
	if ( $newpass !~ /^$|\s+/ && $trustedpass !~ /^$|\s+/ )
	{
		return ( $newpass eq $trustedpass );
	}
	else
	{
		return 0;
	}
}

sub checkLoggedZapiUser    #()
{
	my $allowed  = 0;
	my $userpass = $ENV{ HTTP_AUTHORIZATION };
	$userpass =~ s/Basic\ //i;
	my $userpass_dec = decode_base64( $userpass );
	my @user         = split ( ":", $userpass_dec );
	my $user         = $user[0];
	my $pass         = $user[1];

	if ( &checkValidUser( "zapi", $pass ) )
	{
		$allowed = 1;
	}
	return $allowed;
}

1;
