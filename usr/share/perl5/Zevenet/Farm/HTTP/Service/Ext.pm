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
	my ( $farm_name, $service ) = @_;

	require Zevenet::Farm::Core;

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

		$ci->{ enabled } = ( $prefix !~ /#/ ) ? 'true' : 'false';

		my @params = split( ' ', $params );

		for my $p ( @params ) # remove quotes
		{
			$p =~ s/^"(.*)"$/$1/;
		}

		$ci->{ name }   = shift @params;
		$ci->{ domain } = shift @params;
		$ci->{ path }   = shift @params;
		$ci->{ ttl }    = shift( @params ) + 0;
	}

	# check errors
	unless ( defined $ci )
	{
		&zenlog("Cookie insertion policy not found in Farm: $farm_name, Service: $service.", "warning", "LSLB");
	}

	if ( ! defined $ci->{ name } || ! defined $ci->{ domain } || ! defined $ci->{ path } || ! defined $ci->{ ttl } )
	{
		&zenlog("Error found in cookie insertion policy: Incorrect parameter in Farm: $farm_name, Service: $service.", "error", "LSLB");
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
	my $ci_enabled = ( $ci->{ enabled } == 1 ) ? '' : '#';
	my $new_ci_policy = qq(\t\t${ci_enabled}BackendCookie "$ci->{ name }" "$ci->{ domain }" "$ci->{ path }" $ci->{ ttl });

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

	&zenlog("Could not apply cookie insertion change", "error", "LSLB") if $errno;

	return $errno;
}

sub add_service_cookie_insertion
{
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
	my ( $farm_name, $service ) = @_;

	require Zevenet::Farm::Core;

	# input control
	return undef unless $service;

	# look for cookie insertion policy
	my $farm_filename = &getFarmFile( $farm_name );
	my $in_block = 0;
	my $code = "";

	open my $fileconf, '<', "$configdir/$farm_filename";

	foreach my $line ( <$fileconf> )
	{
		if ( $line =~ /^\tService \"$service\"/ )    { $in_block = 1; }
		next if not $in_block;
		if ( $line =~ /^\tEnd$/ && $in_block == 1 )  { last; }
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
	my ( $farm_name, $service, $code ) = @_;

	require Zevenet::Farm::Core;
	my $ffile = &getFarmFile( $farm_name );
	my $srv_flag  = 0;
	my $errno     = 1;

	require Zevenet::Lock;
	&ztielock ( \my @fileconf, "$configdir/$ffile" );

	foreach my $line ( @fileconf )
	{
		if ( $line =~ /\tService \"$service\"/ )    { $srv_flag = 1; }
		if ( $line =~ /^\tEnd$/ && $srv_flag == 1 ) { last; }
		next if $srv_flag == 0;

		if ( $line =~ /^\s*(#)?\s*(Redirect|RedirectAppend)\s+(?:\d+)?\s*(\".+\")?/ )
		{
			$line = "\t\t${1}$2 $code $3";
			$errno = 0;
			last;
		}
	}
	untie @fileconf;

	&zenlog("Could not apply redirect HTTP code") if $errno;

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
	my ( $farm_name, $service ) = @_;

	require Zevenet::Farm::Core;

	# input control
	return undef unless $service;

	# look for cookie insertion policy
	my $farm_filename = &getFarmFile( $farm_name );
	my $sw = 0;
	my $out = "false";

	open my $fileconf, '<', "$configdir/$farm_filename";

	foreach my $line ( <$fileconf> )
	{
		if ( $line =~ /^\tService \"$service\"/ )    { $sw = 1; }
		next if not $sw;
		if ( $line =~ /^\tEnd$/ && $sw == 1 )  { last; }

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
	my ( $farm_name, $service, $status ) = @_;

	require Zevenet::Farm::Core;
	my $ffile = &getFarmFile( $farm_name );
	my $srv_flag  = 0;
	my $errno     = 1;
	my $index  = -1;

	require Zevenet::Lock;
	&ztielock ( \my @fileconf, "$configdir/$ffile" );

	foreach my $line ( @fileconf )
	{
		$index++;
		if ( $line =~ /\tService \"$service\"/ )    { $srv_flag = 1; }
		if ( $line =~ /^\tEnd$/ && $srv_flag == 1 ) { last; }
		next if $srv_flag == 0;

		if ( $line =~ /StrictTransportSecurity(\s+\d+)?/ )
		{
			if ($status eq 'true')
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
			$line = "\t\tStrictTransportSecurity 21600000\n$line";
			$errno = 0;
			last;
		}
	}
	untie @fileconf;

	&zenlog("Could not apply STS status") if $errno;

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
	my ( $farm_name, $service ) = @_;

	require Zevenet::Farm::Core;

	# input control
	return undef unless $service;

	# look for cookie insertion policy
	my $farm_filename = &getFarmFile( $farm_name );
	my $sw = 0;
	my $out = "";

	open my $fileconf, '<', "$configdir/$farm_filename";

	foreach my $line ( <$fileconf> )
	{
		if ( $line =~ /^\tService \"$service\"/ )    { $sw = 1; }
		next if not $sw;
		if ( $line =~ /^\tEnd$/ && $sw == 1 )  { last; }

		# example
		#	StrictTransportSecurity 21600000
		if ( $line =~ /^\s*StrictTransportSecurity\s+(\d+)/ )
		{
			$out = $1;
			last;
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
	my ( $farm_name, $service, $time ) = @_;

	require Zevenet::Farm::Core;
	my $ffile = &getFarmFile( $farm_name );
	my $srv_flag  = 0;
	my $errno     = 1;

	require Zevenet::Lock;
	&ztielock ( \my @fileconf, "$configdir/$ffile" );

	foreach my $line ( @fileconf )
	{
		if ( $line =~ /\tService \"$service\"/ )    { $srv_flag = 1; }
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
			$line = "\t\t#StrictTransportSecurity $time\n$line";
			$errno = 0;
			last;
		}
	}
	untie @fileconf;

	&zenlog("Could not apply STS timeout") if $errno;

	return $errno;
}

# Move/Sort services

=begin nd
Function: moveService

	Move a HTTP service to change its preference. This function changes the possition of a service in farm config file

Parameters:
	farmname - Farm name
	move - Direction where it moves the service. The possbile value are: "down", decrease the priority or "up", increase the priority
	service - Service to move

Returns:
	integer - Always return 0

FIXME:
	Rename function to setHTTPFarmMoveService
	Always return 0, create error control

=cut
sub moveService    # moveService ( $farmName, $move, $serviceSelect);
{
	# Params
	my $farmName      = shift;
	my $move          = shift;
	my $serviceSelect = shift;

	my $farm_filename = &getFarmFile( $farmName );
	$farm_filename = "$configdir\/$farm_filename";

	my @file;
	my @services = &getHTTPFarmServices( $farmName );
	my @serviceIndex;
	my $selectServiceInd;
	my $size = scalar @services;
	my @aux;
	my $lastService;

	# loop
	my $ind        = 0;
	my $serviceNum = 0;
	my $flag       = 0;
	my @definition;    # Service definition

	if (    ( ( $move eq 'up' ) && ( $services[0] ne $serviceSelect ) )
		 || ( ( $move eq 'down' ) && ( $services[$size - 1] ne $serviceSelect ) ) )
	{
		#~ system ( "cp $farm_filename $farm_filename.bak" );
		tie @file, 'Tie::File', $farm_filename;

		# Find service indexs
		foreach my $line ( @file )
		{
			# Select service index
			if ( $line =~ /^\tService \"$serviceSelect\"$/ )
			{
				$flag             = 1;
				$selectServiceInd = $serviceNum;
			}

			# keep service definition and delete it from configuration file
			if ( $flag == 1 )
			{
				push @definition, $line;

				# end service definition
				if ( $line =~ /^\tEnd$/ )
				{
					$flag = 0;
					$ind -= 1;
				}
			}
			else
			{
				push @aux, $line;
			}

			# add a new index to the index table
			if ( $line =~ /^\tService \"$services[$serviceNum]\"$/ )
			{
				push @serviceIndex, $ind;
				$serviceNum += 1;
			}

			# index of last service
			if ( $line =~ /^\tEnd$/ )
			{
				$lastService = $ind + 1;
			}

			if ( !$flag )
			{
				$ind += 1;
			}

		}
		@file = @aux;

		# move up service
		if ( $move eq 'up' )
		{
			splice ( @file, $serviceIndex[$selectServiceInd - 1], 0, @definition );
		}

		# move down service
		elsif ( $move eq 'down' )
		{
			if ( $selectServiceInd == ( $size - 2 ) )
			{
				unshift @definition, "\n";
				splice ( @file, $lastService + 1, 0, @definition );
			}
			else
			{
				splice ( @file, $serviceIndex[$selectServiceInd + 2], 0, @definition );
			}
		}
		untie @file;
	}

	return 0;
}

=begin nd
Function: moveServiceFarmStatus

	Modify the service index in status file ( farmname_status.cfg ). For updating farmguardian backend status.

Parameters:
	farmname - Farm name
	move - Direction where it moves the service. The possbile value are: "down", decrease the priority or "up", increase the priority
	service - Service to move

Returns:
	integer - Always return 0

FIXME:
	Rename function to setHTTPFarmMoveServiceStatusFile
	Always return 0, create error control

=cut
sub moveServiceFarmStatus
{
	my ( $farmName, $moveService, $serviceSelect ) = @_;

	require Tie::File;
	my @file;
	my $fileName = "$configdir\/${farmName}_status.cfg";

	my @services = &getHTTPFarmServices( $farmName );
	my $size     = scalar @services;
	my $ind      = -1;
	my $auxInd;
	my $serviceNum;

	# Find service select index
	foreach my $se ( @services )
	{
		$ind += 1;
		last if ( $services[$ind] eq $serviceSelect );
	}

	#~ system ( "cp $fileName $fileName.bak" );

	tie @file, 'Tie::File', $fileName;

	# change server id
	foreach my $line ( @file )
	{
		$line =~ /(^-[bB] 0 )(\d+)/;
		my $cad = $1;
		$serviceNum = $2;

		#	&main::zenlog("$moveService::$ind::$serviceNum");
		if ( ( $moveService eq 'up' ) && ( $serviceNum == $ind ) )
		{
			$auxInd = $serviceNum - 1;
			$line =~ s/^-[bB] 0 (\d+)/${cad}$auxInd/;
		}

		if ( ( $moveService eq 'up' ) && ( $serviceNum == $ind - 1 ) )
		{
			$auxInd = $serviceNum + 1;
			$line =~ s/^-[bB] 0 (\d+)/${cad}$auxInd/;
		}

		if ( ( $moveService eq 'down' ) && ( $serviceNum == $ind ) )
		{
			$auxInd = $serviceNum + 1;
			$line =~ s/^-[bB] 0 (\d+)/${cad}$auxInd/;
		}

		if ( ( $moveService eq 'down' ) && ( $serviceNum == $ind + 1 ) )
		{
			$auxInd = $serviceNum - 1;
			$line =~ s/^-[bB] 0 (\d+)/${cad}$auxInd/;
		}
	}

	untie @file;

	&zenlog(
		"The service \"$serviceSelect\" from farm \"$farmName\" has been moved $moveService", "info", "LSLB"
	);

	return 0;
}

1;
