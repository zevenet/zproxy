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

my $configdir = &getGlobalConfiguration( 'configdir' );

=begin nd
Function: getHTTPServiceCookieIns

	Get cookie insertion data in a hash ref for a farm and service.

Parameters:
	farmname - Farm name
	service  - Service name

Returns:
	hash ref - Cookie data in a hash reference.
	undef    - If could not read any cookie insertion data.

	{
	   enabled => 'true' || 'false',
	   name    => COOKIE_TAG,
	   domain  => DOMAIN_NAME,
	   path    => PATH,
	   ttl     => 60,			# Time to live in seconds
	}
=cut

sub getHTTPServiceCookieIns    # ($farm_name,$service)
{
	my ( $farm_name, $service ) = @_;

	# cookieins, cookieins-name, cookieins-domain, cookieins-path, cookieins-ttlc

	# input control
	$service = "" unless $service;
	#~ $tag     = "" unless $tag;
	#~ $tag = ( "cookieins" || "cookieins-name" || "cookieins-domain" || "cookieins-path" || "cookieins-ttlc" );

	# look for cookie insertion policy
	my $farm_filename = &getFarmFile( $farm_name );
	my $in_block = 0;
	my $ci_line;

	open my $fileconf, '<', "$configdir/$farm_filename";

	foreach my $line ( <$fileconf> )
	{
		if ( $line =~ /^\tService \"$service\"/ )    { $in_block = 1; }
		if ( $line =~ /^\tEnd$/ && $in_block == 1 )  { last; }

		if ( $in_block && $line =~ "BackendCookie \"" )
		{
			$ci_line = $line;
			last;
		}
	}

	close $fileconf;

	# parse cookie insertion policy
	my $ci;

	if ( $ci_line )
	{
		my ( $prefix, $params ) = split( "BackendCookie ", $ci_line );

		$ci->{ enabled } = $prefix !~ /#/ ? 'true' : 'false';

		my @params = split( ' ', $params );

		for my $p ( @params ) # remove quotes
		{
			s/^".*"$/$1/;
		}

		$ci->{ name }   = shift @params;
		$ci->{ domain } = shift @params;
		$ci->{ path }   = shift @params;
		$ci->{ ttl }    = shift @params + 0;
	}

	# check errors
	unless ( defined $ci )
	{
		&zenlog("Cookie insertion policy not found in Farm: $farm_name, Service: $service.");
	}

	if ( ! defined $ci->{ name } || ! defined $ci->{ domain } || ! defined $ci->{ path } || ! defined $ci->{ ttl } )
	{
		&zenlog("Error found in cookie insertion policy: Incorrect parameter in Farm: $farm_name, Service: $service.");
	}

	return $ci;
}

=begin nd
Function: setHTTPServiceCookieIns

	Set values for service parameters. The parameters are: vs, urlp, redirect, redirectappend,

	cookieins, cookieins-name, cookieins-domain, cookieins-path, cookieins-ttlc

	A blank string comment the tag field in config file

Parameters:
	farmname - Farm name
	service - Service name
	tag - Indicate which parameter modify
	string - value for the field "tag"

Returns:
	Integer - Error code: 0 on success or -1 on failure

=cut

sub setHTTPServiceCookieIns    # ($farm_name,$service,$ci)
{
	my ( $farm_name, $service, $ci ) = @_;

	# cookieins, cookieins-name, cookieins-domain, cookieins-path, cookieins-ttlc

	my $farm_filename = &getFarmFile( $farm_name );
	my $updated_flag  = 0;
	my $errno         = 1;

	# TODO: check valid input

	# form new policy
	my $ci_enabled = $ci->{ enabled } == 1 ? '' : '#';
	my $new_ci_policy = qq(\t\t${ci_enabled}BackendCookie "$ci->{ enabled }" "$ci->{ name }" "$ci->{ domain }" "$ci->{ path }" $ci->{ ttl });

	# apply new policy
	require Tie::File;
	tie my @fileconf, 'Tie::File', "$configdir/$farm_filename";

	my $in_block = 0;

	foreach my $line ( @fileconf )
	{
		if ( $line =~ /\tService \"$service\"/ )    { $in_block = 1; }
		if ( $line =~ /^\tEnd$/ && $in_block == 1 ) { last; }

		next if $in_block == 0;

		if ( $in_block && $line =~ "BackendCookie \"" )
		{
			$line         = $new_ci_policy;
			$updated_flag = 1;
			last;
		}
	}
	untie @fileconf;

	# error control
	$errno = 0 if $updated_flag;

	&zenlog("Could not apply cookie insertion change") if $errno;

	return $errno;
}

sub add_service_cookie_intertion
{
	my ( $farmname, $s ) = @_;

	my $ci = &getHTTPServiceCookieIns( $farmname, $s->{ id } );

	$service->{ cookieinsert } = $ci->{ status };
	$service->{ cookiename }   = $ci->{ name };
	$service->{ cookiedomain } = $ci->{ domain };
	$service->{ cookiepath }   = $ci->{ path };
	$service->{ cookiettl }    = $ci->{ ttl };

	return;
}

1;
