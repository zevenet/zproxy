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

# Cookie insertion

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $service ) = @_;

	use Zevenet::Farm::Core;

	# cookieins, cookieins-name, cookieins-domain, cookieins-path, cookieins-ttlc

	# input control
	$service = "" unless $service;

#~ $tag     = "" unless $tag;
#~ $tag = ( "cookieins" || "cookieins-name" || "cookieins-domain" || "cookieins-path" || "cookieins-ttlc" );

	# look for cookie insertion policy
	my $farm_filename = &getFarmFile( $farm_name );
	my $in_block      = 0;
	my $ci_line;

	open my $fileconf, '<', "$configdir/$farm_filename";

	foreach my $line ( <$fileconf> )
	{
		if ( $line =~ /^\tService \"$service\"/ ) { $in_block = 1; }
		if ( $line =~ /^\tEnd$/ && $in_block == 1 ) { last; }

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
		my ( $prefix, $params ) = split ( "BackendCookie ", $ci_line );

		$ci->{ enabled } = ( $prefix !~ /#/ ) ? 'true' : 'false';

		my @params = split ( ' ', $params );

		for my $p ( @params )    # remove quotes
		{
			$p =~ s/^"(.*)"$/$1/;
		}

		$ci->{ name }   = shift @params;
		$ci->{ domain } = shift @params;
		$ci->{ path }   = shift @params;
		$ci->{ ttl }    = shift ( @params ) + 0;
	}

	# check errors
	unless ( defined $ci )
	{
		&zenlog(
				"Cookie insertion policy not found in Farm: $farm_name, Service: $service.",
				"warning", "LSLB" );
	}

	if (    !defined $ci->{ name }
		 || !defined $ci->{ domain }
		 || !defined $ci->{ path }
		 || !defined $ci->{ ttl } )
	{
		&zenlog(
			"Error found in cookie insertion policy: Incorrect parameter in Farm: $farm_name, Service: $service.",
			"error", "LSLB"
		);
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $service, $ci ) = @_;

	# cookieins, cookieins-name, cookieins-domain, cookieins-path, cookieins-ttlc

	my $farm_filename = &getFarmFile( $farm_name );
	my $lock_file     = &getLockFile( $farm_name );
	my $lock_fh       = &openlock( $lock_file, 'w' );
	my $updated_flag  = 0;
	my $errno         = 1;

	# TODO: check valid input

	# form new policy
	my $ci_enabled = ( $ci->{ enabled } == 1 ) ? '' : '#';
	my $new_ci_policy =
	  qq(\t\t${ci_enabled}BackendCookie "$ci->{ name }" "$ci->{ domain }" "$ci->{ path }" $ci->{ ttl });

	# apply new policy
	require Tie::File;
	tie my @fileconf, 'Tie::File', "$configdir/$farm_filename";

	my $in_block = 0;

	foreach my $line ( @fileconf )
	{
		if ( $line =~ /\tService \"$service\"/ ) { $in_block = 1; }
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
	close $lock_fh;

	# error control
	$errno = 0 if $updated_flag;

	&zenlog( "Could not apply cookie insertion change", "error", "LSLB" ) if $errno;

	return $errno;
}

sub add_service_cookie_insertion
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farmname, $service ) = @_;

	my $ci = &getHTTPServiceCookieIns( $farmname, $service->{ id } );

	$service->{ cookieinsert } = ( $ci->{ enabled } eq 'true' ) ? 'true' : 'false';
	$service->{ cookiename }   = $ci->{ name };
	$service->{ cookiedomain } = $ci->{ domain };
	$service->{ cookiepath }   = $ci->{ path };
	$service->{ cookiettl }    = $ci->{ ttl };

	return $service;
}

# Redirect

=begin nd
Function: getHTTPServiceRedirectCode

	If a redirect exists, the function returns the redirect HTTP code

Parameters:
	farmname - Farm name
	service  - Service name

Returns:
	Integer  - Redirect code: 302 ( by default ), 301 or 307
	undef    - If redirect is not configured

=cut

sub getHTTPServiceRedirectCode    # ($farm_name,$service)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $service ) = @_;

	require Zevenet::Farm::Core;

	# input control
	return unless $service;

	# look for cookie insertion policy
	my $farm_filename = &getFarmFile( $farm_name );
	my $in_block      = 0;
	my $code          = "";

	open my $fileconf, '<', "$configdir/$farm_filename";

	foreach my $line ( <$fileconf> )
	{
		if ( $line =~ /^\tService \"$service\"/ ) { $in_block = 1; }
		next if not $in_block;
		if ( $line =~ /^\tEnd$/ && $in_block == 1 ) { last; }
		if ( $line =~ /^\s*#/ ) { next; }

		# example
		# 	Redirect 301 "http://google.com"
		if ( $line =~ /^\s*(?:Redirect|RedirectAppend)\s+(\d+)?/ )
		{
			$code = $1 // 302;
			last;
		}
	}

	close $fileconf;

	return $code;
}

=begin nd
Function: setHTTPServiceRedirectCode

	Set the redirect code. This value only will be show when the line is discomment

Parameters:
	farmname - Farm name
	service - Service name
	code - The available values are: 301, 302 and 307

Returns:
	Integer - Error code: 0 on success or 1 on failure

=cut

sub setHTTPServiceRedirectCode    # ($farm_name,$service,$code)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $service, $code ) = @_;

	require Zevenet::Farm::Core;
	my $ffile     = &getFarmFile( $farm_name );
	my $lock_file = &getLockFile( $farm_name );
	my $lock_fh   = &openlock( $lock_file, 'w' );
	my $srv_flag  = 0;
	my $errno     = 1;

	require Zevenet::Lock;
	&ztielock( \my @fileconf, "$configdir/$ffile" );

	foreach my $line ( @fileconf )
	{
		if ( $line =~ /\tService \"$service\"/ ) { $srv_flag = 1; }
		if ( $line =~ /^\tEnd$/ && $srv_flag == 1 ) { last; }
		next if $srv_flag == 0;

		if ( $line =~ /^\s*(#)?\s*(Redirect|RedirectAppend)\s+(?:\d+)?\s*(\".+\")?/ )
		{
			$line  = "\t\t${1}$2 $code $3";
			$errno = 0;
			last;
		}
	}
	untie @fileconf;
	close $lock_fh;

	&zenlog( "Could not apply redirect HTTP code" ) if $errno;

	return $errno;
}

# Strict secure transport

=begin nd
Function: getHTTPServiceSTSStatus

	This function shows the status of the Strict Transport Security parameter

Parameters:
	farmname - Farm name
	service  - Service name

Returns:
	Scalar  - "true" if it is enabled or "false" if it is disabled

=cut

sub getHTTPServiceSTSStatus    # ($farm_name,$service)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $service ) = @_;

	require Zevenet::Farm::Core;

	# input control
	return unless $service;

	# look for cookie insertion policy
	my $farm_filename = &getFarmFile( $farm_name );
	my $sw            = 0;
	my $out           = "false";

	open my $fileconf, '<', "$configdir/$farm_filename";

	foreach my $line ( <$fileconf> )
	{
		if ( $line =~ /^\tService \"$service\"/ ) { $sw = 1; }
		next if not $sw;
		if ( $line =~ /^\tEnd$/ && $sw == 1 ) { last; }

		# example
		#	StrictTransportSecurity 21600000
		if ( $line =~ /^\s*StrictTransportSecurity/ )
		{
			$out = "true";
			last;
		}
	}

	close $fileconf;

	return $out;
}

=begin nd
Function: setHTTPServiceSTSStatus

	Change the status of the Strict Transport Security for a HTTP service

Parameters:
	farmname - Farm name
	service - Service name
	status - The available values are: "true" to enable STS or "false" to disable it

Returns:
	Integer - Error code: 0 on success or 1 on failure

=cut

sub setHTTPServiceSTSStatus    # ($farm_name,$service,$code)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $service, $status ) = @_;

	require Zevenet::Farm::Core;
	my $ffile     = &getFarmFile( $farm_name );
	my $lock_file = &getLockFile( $farm_name );
	my $lock_fh   = &openlock( $lock_file, 'w' );
	my $srv_flag  = 0;
	my $errno     = 1;
	my $index     = -1;

	require Zevenet::Lock;
	&ztielock( \my @fileconf, "$configdir/$ffile" );

	foreach my $line ( @fileconf )
	{
		$index++;
		if ( $line =~ /\tService \"$service\"/ ) { $srv_flag = 1; }
		if ( $line =~ /^\tEnd$/ && $srv_flag == 1 ) { last; }
		next if $srv_flag == 0;

		if ( $line =~ /StrictTransportSecurity(\s+\d+)?/ )
		{
			if ( $status eq 'true' )
			{
				my $time = $1 // 21600000;
				$time =~ s/^\s+//g;
				$line =~ s/#//g;
				$errno = 0;
			}
			else
			{
				splice @fileconf, $index, 1;
				$errno = 0;
			}
			last;
		}

		# add the line if it does not exist and status is up
		elsif ( $line =~ /BackEnd/ and $status eq 'true' )
		{
			$line  = "\t\tStrictTransportSecurity 21600000\n$line";
			$errno = 0;
			last;
		}
	}
	untie @fileconf;
	close $lock_fh;

	&zenlog( "Could not apply STS status" ) if $errno;

	return $errno;
}

=begin nd
Function: getHTTPServiceSTSTimeout

	This function shows the status of the Strict Transport Security parameter

Parameters:
	farmname - Farm name
	service  - Service name

Returns:
	Scalar  - "true" if it is enabled or "false" if it is disabled

=cut

sub getHTTPServiceSTSTimeout    # ($farm_name,$service)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $service ) = @_;

	require Zevenet::Farm::Core;

	# input control
	return unless $service;

	# look for cookie insertion policy
	my $farm_filename = &getFarmFile( $farm_name );
	my $sw            = 0;
	my $out           = "";

	open my $fileconf, '<', "$configdir/$farm_filename";

	foreach my $line ( <$fileconf> )
	{
		if ( $line =~ /^\tService \"$service\"/ ) { $sw = 1; }
		next if not $sw;
		if ( $line =~ /^\tEnd$/ && $sw == 1 ) { last; }

		# example
		#	StrictTransportSecurity 21600000
		if ( $line =~ /^\s*StrictTransportSecurity\s+(\d+)/ )
		{
			$out = $1;
			last;
		}
		else
		{
			$out = 21600000;
		}
	}

	close $fileconf;

	return $out;
}

=begin nd
Function: setHTTPServiceSTSTimeout

	Change the status of the Strict Transport Security for a HTTP service

Parameters:
	farmname - Farm name
	service - Service name
	status - It is the number of seconds for STS

Returns:
	Integer - Error code: 0 on success or 1 on failure

=cut

sub setHTTPServiceSTSTimeout    # ($farm_name,$service,$code)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $service, $time ) = @_;

	require Zevenet::Farm::Core;
	my $ffile     = &getFarmFile( $farm_name );
	my $lock_file = &getLockFile( $farm_name );
	my $lock_fh   = &openlock( $lock_file, 'w' );
	my $srv_flag  = 0;
	my $errno     = 1;

	require Zevenet::Lock;
	&ztielock( \my @fileconf, "$configdir/$ffile" );

	foreach my $line ( @fileconf )
	{
		if ( $line =~ /\tService \"$service\"/ ) { $srv_flag = 1; }
		if ( $line =~ /^\tEnd$/ && $srv_flag == 1 ) { last; }
		next if $srv_flag == 0;

		if ( $line =~ /StrictTransportSecurity/ )
		{
			$line =~ s/StrictTransportSecurity(\s+\d+)?/StrictTransportSecurity $time/;
			$errno = 0;
			last;
		}

		# add the line if the StrictTransportSecurity does not exist. Put it as disabled
		elsif ( $line =~ /BackEnd/ )
		{
			$line  = "\t\t#StrictTransportSecurity $time\n$line";
			$errno = 0;
			last;
		}
	}
	untie @fileconf;
	close $lock_fh;

	&zenlog( "Could not apply STS timeout" ) if $errno;

	return $errno;
}

=begin nd
Function: setHTTPFarmMoveService

	Move a HTTP service to change its preference. This function changes
	the possition of a service in farm config file

Parameters:
	farmname - Farm name
	service - Service to move
	index - Required index

Returns:
	integer - Always return 0

FIXME:
	Always return 0, create error control

=cut

sub setHTTPFarmMoveService
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farm      = shift;
	my $srv       = shift;
	my $req_index = shift;
	my $out;

	require Zevenet::Lock;
	require Zevenet::Farm::HTTP::Service;

	# lock file
	my $farm_filename = &getFarmFile( $farm );
	my $lock_file     = &getLockFile( $farm );
	my $lock_fh       = &openlock( $lock_file, 'w' );

	# get service code
	my $srv_block = &getHTTPServiceBlocks( $farm, $srv );

	my @sort_list = @{ $srv_block->{ farm } };

	my $size = scalar keys %{ $srv_block->{ services } };
	my $id   = 0;

	for ( my $i = 0 ; $i < $size + 1 ; $i++ )
	{
		if ( $i == $req_index )
		{
			push @sort_list, @{ $srv_block->{ request } };
		}

		else
		{
			push @sort_list, @{ $srv_block->{ services }->{ $id } };
			$id++;
		}
	}

	# finish tags of config file
	push @sort_list, "\t#ZWACL-END";
	push @sort_list, "End";

	# write in config file
	use Tie::File;
	tie my @file, "Tie::File", "$configdir/$farm_filename";
	@file = @sort_list;
	untie @file;

	# unlock file
	close $lock_fh;

	# move fg
	&setHTTPFarmMoveServiceStatusFile( $farm, $srv, $req_index );

	return $out;
}

=begin nd
Function: setHTTPFarmMoveServiceStatusFile

	Modify the service index in status file ( farmname_status.cfg ). For
	updating farmguardian backend status.

Parameters:
	farmname - Farm name
	service - Service to move
	index - position to be moved

Returns:
	integer - Always return 0

FIXME:
	Always return 0, create error control

=cut

sub setHTTPFarmMoveServiceStatusFile
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farmname, $service, $req_index ) = @_;

	use Tie::File;
	my $fileName = "$configdir\/${farmname}_status.cfg";
	tie my @file, 'Tie::File', $fileName;

	my $srv_id = &getFarmVSI( $farmname, $service );
	return if ( $srv_id == -1 );
	return if ( $srv_id == $req_index );
	#
	my $dir = ( $srv_id < $req_index ) ? "up" : "down";

	foreach my $line ( @file )
	{
		if ( $line =~ /(^-[bB] 0) (\d+) (.+)$/ )
		{
			my $cad1  = $1;
			my $index = $2;
			my $cad2  = $3;

			# replace with the new service position
			if ( $index == $srv_id ) { $index = $req_index; }

			# replace with the new service position
			elsif ( $dir eq "down" and $index < $srv_id and $index >= $req_index )
			{
				$index++;
			}

			# replace with the new service position
			elsif ( $dir eq "up" and $index > $srv_id and $index <= $req_index )
			{
				$index--;
			}

			$line = "$cad1 $index $cad2";
		}
	}

	untie @file;

	&zenlog(
		"The service \"$service\" from farm \"$farmname\" has been moved to $req_index the position",
		"debug2"
	);

	return 0;
}

1;

