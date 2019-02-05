#!/bin/perl
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
use Zevenet::Farm::Core;

my $configdir = &getGlobalConfiguration( 'configdir' );

=begin nd
Function: getHTTPFarm100Continue

	Return 100 continue Header configuration HTTP and HTTPS farms

Parameters:
	farmname - Farm name

Returns:
	scalar - The possible values are: 0 on disabled, 1 on enabled or -1 on failure

=cut

sub getHTTPFarm100Continue    # ($farm_name)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	open my $fd, '<', "$configdir\/$farm_filename" or return $output;
	$output = 1;    # if the directive is not in config file, it is enabled
	my @file = <$fd>;
	close $fd;

	foreach my $line ( @file )
	{
		if ( $line =~ /Ignore100Continue (\d).*/ )
		{
			$output = $1;
			last;
		}
	}

	return $output;
}

=begin nd
Function: setHTTPFarm100Continue

	Enable or disable the HTTP 100 continue header

Parameters:
	farmname - Farm name
	action - The available actions are: 1 to enable or 0 to disable

Returns:
	scalar - The possible values are: 0 on success or -1 on failure

=cut

sub setHTTPFarm100Continue    # ($farm_name, $action)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $action ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	require Tie::File;
	tie my @file, 'Tie::File', "$configdir/$farm_filename";

	# check if 100 continue directive exists
	if ( !grep ( s/^Ignore100Continue\ .*/Ignore100Continue $action/, @file ) )
	{
		foreach my $line ( @file )
		{
			# put ignore below than rewritelocation
			if ( $line =~ /^Control\s/ )
			{
				$line = "$line\nIgnore100Continue $action";
				last;
			}
		}
	}
	$output = 0;
	untie @file;

	return $output;
}

=begin nd
Function: getHTTPFarmLogs

	Return the log connection tracking status

Parameters:
	farmname - Farm name

Returns:
	scalar - The possible values are: 0 on disabled, possitive value on enabled or -1 on failure

=cut

sub getHTTPFarmLogs    # ($farm_name)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	open my $fd, '<', "$configdir\/$farm_filename" or return $output;
	$output = 0;       # if the directive is not in config file, it is disabled
	my @file = <$fd>;
	close $fd;

	foreach my $line ( @file )
	{
		if ( $line =~ /LogLevel\s+(\d).*/ )
		{
			$output = $1;
			last;
		}
	}

	return $output;
}

=begin nd
Function: setHTTPFarmLogs

	Enable or disable the log connection tracking for a http farm

Parameters:
	farmname - Farm name
	action - The available actions are: "true" to enable or "false" to disable

Returns:
	scalar - The possible values are: 0 on success or -1 on failure

=cut

sub setHTTPFarmLogs    # ($farm_name, $action)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $action ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	my $loglvl = ( $action eq "true" ) ? 5 : 0;

	require Tie::File;
	tie my @file, 'Tie::File', "$configdir/$farm_filename";

	# check if 100 continue directive exists
	if ( !grep ( s/^LogLevel\s+(\d).*$/LogLevel\t$loglvl/, @file ) )
	{
		&zenlog( "Error modifying http logs", "error", "HTTP" );
	}
	else
	{
		$output = 0;
	}
	untie @file;

	return $output;
}

# Add headers

=begin nd
Function: getHTTPAddheader

	Get a list with all the http headers are added by the farm

Parameters:
	farmname - Farm name

Returns:
	Array ref - headers list

=cut

sub getHTTPAddheader    # ($farm_name,$service)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name ) = @_;
	my @out = ();

	require Zevenet::Farm::Core;

	# look for cookie insertion policy
	my $farm_filename = &getFarmFile( $farm_name );
	my $sw            = 0;
	my $out           = "false";

	open my $fileconf, '<', "$configdir/$farm_filename";

	my $index = 0;
	foreach my $line ( <$fileconf> )
	{
		if ( $line =~ /^[#\s]*Service \"/ ) { last; }
		elsif ( $line =~ /^[#\s]*AddHeader\s+"(.+)"/ )
		{
			my %hash = (
						 "id"     => $index,
						 "header" => $1
			);
			push @out, \%hash;
			$index++;
		}
	}

	close $fileconf;

	return \@out;
}

=begin nd
Function: addHTTPHeadremove

	The HTTP farm will add the header to the http communication

Parameters:
	farmname - Farm name
	header - Header to add

Returns:
	Integer - Error code: 0 on success or 1 on failure

=cut

sub addHTTPAddheader    # ($farm_name,$service,$code)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $header ) = @_;

	require Zevenet::Farm::Core;
	my $ffile    = &getFarmFile( $farm_name );
	my $srv_flag = 0;
	my $errno    = 1;

	require Zevenet::Lock;
	&ztielock( \my @fileconf, "$configdir/$ffile" );

	my $index        = 0;
	my $rewrite_flag = 0;    # it is used to add HeadRemove before than AddHeader
	foreach my $line ( @fileconf )
	{
		if ( $line =~ /[#\s]*RewriteLocation/ )
		{
			$rewrite_flag = 1;
		}
		elsif ( $rewrite_flag )
		{
			# put new headremove before than last one
			if ( $line !~ /^[#\s]*AddHeader\s+"/ and $rewrite_flag )
			{
				# example: AddHeader "header: to add"
				splice @fileconf, $index, 0, "\tAddHeader \"$header\"";
				$errno = 0;
				last;
			}
		}
		$index++;
	}
	untie @fileconf;

	&zenlog( "Could not add AddHeader" ) if $errno;

	return $errno;
}

=begin nd
Function: delHTTPAddheader

	Delete a directive "AddHeader".

Parameters:
	farmname - Farm name
	index - Header index

Returns:
	Integer - Error code: 0 on success or 1 on failure

=cut

sub delHTTPAddheader    # ($farm_name,$service,$code)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $header_ind ) = @_;

	require Zevenet::Farm::Core;
	my $ffile    = &getFarmFile( $farm_name );
	my $srv_flag = 0;
	my $errno    = 1;

	require Zevenet::Lock;
	&ztielock( \my @fileconf, "$configdir/$ffile" );

	my $index = 0;
	my $ind   = 0;
	foreach my $line ( @fileconf )
	{
		if ( $line =~ /^\s*AddHeader\s+"/ )
		{
			if ( $header_ind == $ind )
			{
				$errno = 0;
				splice @fileconf, $index, 1;
				last;
			}
			else
			{
				$ind++;
			}
		}
		$index++;
	}
	untie @fileconf;

	&zenlog( "Could not remove HeadRemove" ) if $errno;

	return $errno;
}

# remove header

=begin nd
Function: getHTTPHeadremove

	Get a list with all the http headers are added by the farm

Parameters:
	farmname - Farm name

Returns:
	Array ref - headers list

=cut

sub getHTTPHeadremove    # ($farm_name,$service)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name ) = @_;
	my @out = ();

	require Zevenet::Farm::Core;

	# look for cookie insertion policy
	my $farm_filename = &getFarmFile( $farm_name );
	my $sw            = 0;
	my $out           = "false";

	open my $fileconf, '<', "$configdir/$farm_filename";

	my $index = 0;
	foreach my $line ( <$fileconf> )
	{
		if ( $line =~ /^[#\s]*Service \"/ ) { last; }
		elsif ( $line =~ /^[#\s]*HeadRemove\s+"(.+)"/ )
		{
			my %hash = (
						 "id"      => $index,
						 "pattern" => $1
			);
			push @out, \%hash;
			$index++;
		}
	}

	close $fileconf;

	return \@out;
}

=begin nd
Function: addHTTPHeadremove

	Add a directive "HeadRemove". The HTTP farm will remove the header that match with the sentence

Parameters:
	farmname - Farm name
	header - Header to add

Returns:
	Integer - Error code: 0 on success or 1 on failure

=cut

sub addHTTPHeadremove    # ($farm_name,$service,$code)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $header ) = @_;

	require Zevenet::Farm::Core;
	my $ffile    = &getFarmFile( $farm_name );
	my $srv_flag = 0;
	my $errno    = 1;

	require Zevenet::Lock;
	&ztielock( \my @fileconf, "$configdir/$ffile" );

	my $index        = 0;
	my $rewrite_flag = 0;    # it is used to add HeadRemove before than AddHeader
	foreach my $line ( @fileconf )
	{
		if ( $line =~ /[#\s]*RewriteLocation/ )
		{
			$rewrite_flag = 1;
		}
		elsif ( $rewrite_flag )
		{
			# put new headremove before than last one
			if ( $line !~ /^[#\s]*(?:AddHeader|HeadRemove)\s+"/ and $rewrite_flag )
			{
				# example: AddHeader "header: to add"
				splice @fileconf, $index, 0, "\tHeadRemove \"$header\"";
				$errno = 0;
				last;
			}
		}
		$index++;
	}
	untie @fileconf;

	&zenlog( "Could not add HeadRemove" ) if $errno;

	return $errno;
}

=begin nd
Function: delHTTPHeadremove

	Delete a directive "HeadRemove".

Parameters:
	farmname - Farm name
	index - Header index

Returns:
	Integer - Error code: 0 on success or 1 on failure

=cut

sub delHTTPHeadremove    # ($farm_name,$service,$code)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $header_ind ) = @_;

	require Zevenet::Farm::Core;
	my $ffile    = &getFarmFile( $farm_name );
	my $srv_flag = 0;
	my $errno    = 1;

	require Zevenet::Lock;
	&ztielock( \my @fileconf, "$configdir/$ffile" );

	my $index = 0;
	my $ind   = 0;
	foreach my $line ( @fileconf )
	{
		if ( $line =~ /^\s*HeadRemove\s+"/ )
		{
			if ( $header_ind == $ind )
			{
				$errno = 0;
				splice @fileconf, $index, 1;
				last;
			}
			else
			{
				$ind++;
			}
		}
		$index++;
	}
	untie @fileconf;

	&zenlog( "Could not remove HeadRemove" ) if $errno;

	return $errno;
}

=begin nd
Function: get_http_farm_ee_struct

	It extends farm struct with the parameters exclusives of the EE

Parameters:
	farmname - Farm name
	farm struct - Struct with the farm configuration parameters

Returns:
	Hash ref - Farm struct updated with EE parameters

=cut

sub get_http_farm_ee_struct
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname = shift;
	my $farm_st  = shift;

	# 100 Continue
	$farm_st->{ ignore_100_continue } =
	  ( &getHTTPFarm100Continue( $farmname ) ) ? "true" : "false";

	# Logs
	$farm_st->{ logs } = ( &getHTTPFarmLogs( $farmname ) ) ? "true" : "false";

	# Add/remove header
	$farm_st->{ addheader }  = &getHTTPAddheader( $farmname );
	$farm_st->{ headremove } = &getHTTPHeadremove( $farmname );

	return $farm_st;
}

1;
