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

#login user
#sub login    #()
#{
#	use CGI::Session;
#	use Authen::Simple::Passwd;
#
#	my $cgi       = new CGI;
#	my $user      = "";
#	my $passw     = "";
#	my $grouplist = "";
#
#	my $session = new CGI::Session( $cgi ) or die CGI::Session->errstr;
#
#	if ( $cgi->param( 'username' ) )
#	{
#		$user  = $cgi->param( 'username' );
#		$passw = $cgi->param( 'password' );
#	}
#
#	# FIXME: show user in log prefix
#	#~ &zenlog( "Login attempt. User: $user, grouplist: $grouplist" );
#
#	my $passwd = Authen::Simple::Passwd->new( path => "$passfile" );
#
#	if ( !$session->param( 'root_logged_in' ) )
#	{
#		my $bin_id = &getGlobalConfiguration('bin_id');
#		$grouplist = `$bin_id $user`;
#		&zenlog( "grouplist is: $grouplist" );
#		if ( $passwd->authenticate( $user, $passw ) && $grouplist =~ /\(webgui\)/ )
#		{
#			#if ( $passwd->authenticate($user,$passw) ) {
#			# successful authentication
#			&zenlog( "Login Successful for user $user" );
#			$session->param( 'root_logged_in', 1 );
#			$session->param( 'username',       $user );
#		}
#		else
#		{
#			#redirect to login web
#			&zenlog( "Login failed for user $user" );
#
#			#$cgi->param('action') = "logout";
#			$cgi->param( -name => 'action', -value => 'logout' );
#
#			$session->delete();
#			$session->flush();
#
#			#&logout();
#			print $cgi->redirect( 'index.html' );
#		}
#
#	}
#	###login & session management end
#	#&zenlog("login Set-Cookie CGISESSID=".$session->id()."; path=/");
#	print "Set-Cookie: CGISESSID=" . $session->id() . "; path=/\n";
#}

#sub logout    #()
#{
#	use CGI::Session;
#	use CGI;
#
#	my $cgi = new CGI;
#	my $session = new CGI::Session( $cgi ) or die CGI::Session->errstr;
#
#	if ( $cgi->param( 'action' ) eq "logout" )
#	{
#		$session->param( -name => 'user_logged_in', -value => 0 );
#		&zenlog(
#				  "User logout. User: " . $session->param( -name => 'user_logged_in' ) );
#		$session->delete();
#		$session->flush();
#		print $cgi->redirect( 'index.html' );
#	}
#}

#sub username    #()
#{
#	use CGI::Session;
#	use CGI;
#
#	my $cgi = new CGI;
#	my $session = new CGI::Session( $cgi ) or die CGI::Session->errstr;
#
#	if ( $session->param( -name => 'username' ) )
#	{
#		return $session->param( -name => 'username' );
#	}
#}

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
