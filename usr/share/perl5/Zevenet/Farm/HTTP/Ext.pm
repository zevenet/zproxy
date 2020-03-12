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
	return &get_http_farm_ee_struct( $farm_name )->{ ignore_100_continue };
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
	return &get_http_farm_ee_struct( $farm_name )->{ logs };
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

# Add request headers

=begin nd
Function: getHTTPAddReqHeader

	Get a list with all the http headers are added by the farm

Parameters:
	farmname - Farm name

Returns:
	Array ref - headers list

=cut

sub getHTTPAddReqHeader    # ($farm_name,$service)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name ) = @_;
	return &get_http_farm_ee_struct( $farm_name )->{ addheader };
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
	my $ffile = &getFarmFile( $farm_name );
	my $errno = 1;

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
			if ( $line !~
				 /^[#\s]*(?:AddHeader|HeadRemove|AddResponseHeader|RemoveResponseHead)\s+"/
				 and $rewrite_flag )

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
	my $ffile = &getFarmFile( $farm_name );
	my $errno = 1;

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

# remove request header

=begin nd
Function: getHTTPRemReqHeader

	Get a list with all the http headers are added by the farm

Parameters:
	farmname - Farm name

Returns:
	Array ref - headers list

=cut

sub getHTTPRemReqHeader    # ($farm_name,$service)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name ) = @_;
	return &get_http_farm_ee_struct( $farm_name )->{ headremove };
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
	my $ffile = &getFarmFile( $farm_name );
	my $errno = 1;

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
			# put new headremove after than last one
			if ( $line !~
				 /^[#\s]*(?:AddHeader|HeadRemove|AddResponseHeader|RemoveResponseHead)\s+"/
				 and $rewrite_flag )
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
	my $ffile = &getFarmFile( $farm_name );
	my $errno = 1;

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

# Add response headers

=begin nd
Function: getHTTPAddRespHeader

	Get a list with all the http headers that load balancer will add to the backend repsonse

Parameters:
	farmname - Farm name

Returns:
	Array ref - headers list

=cut

sub getHTTPAddRespHeader    # ($farm_name,$service)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name ) = @_;
	return &get_http_farm_ee_struct( $farm_name )->{ addresponseheader };
}

=begin nd
Function: addHTTPAddRespheader

	The HTTP farm will add the header to the http response from the backend to the client

Parameters:
	farmname - Farm name
	header - Header to add

Returns:
	Integer - Error code: 0 on success or 1 on failure

=cut

sub addHTTPAddRespheader    # ($farm_name,$service,$code)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $header ) = @_;

	require Zevenet::Farm::Core;
	my $ffile = &getFarmFile( $farm_name );
	my $errno = 1;

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
			if ( $line !~
				 /^[#\s]*(?:AddHeader|HeadRemove|AddResponseHeader|RemoveResponseHead)\s+"/
				 and $rewrite_flag )
			{
				# example: AddHeader "header: to add"
				splice @fileconf, $index, 0, "\tAddResponseHeader \"$header\"";
				$errno = 0;
				last;
			}
		}
		$index++;
	}
	untie @fileconf;

	&zenlog( "Could not add AddResponseHeader" ) if $errno;

	return $errno;
}

=begin nd
Function: delHTTPAddRespheader

	Delete a directive "AddResponseHeader from the farm config file".

Parameters:
	farmname - Farm name
	index - Header index

Returns:
	Integer - Error code: 0 on success or 1 on failure

=cut

sub delHTTPAddRespheader    # ($farm_name,$service,$code)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $header_ind ) = @_;

	require Zevenet::Farm::Core;
	my $ffile = &getFarmFile( $farm_name );
	my $errno = 1;

	require Zevenet::Lock;
	&ztielock( \my @fileconf, "$configdir/$ffile" );

	my $index = 0;
	my $ind   = 0;
	foreach my $line ( @fileconf )
	{
		if ( $line =~ /^\s*AddResponseHeader\s+"/ )
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

	&zenlog( "Could not remove AddResponseHeader" ) if $errno;

	return $errno;
}

# remove response header

=begin nd
Function: getHTTPRemRespHeader

	Get a list with all the http headers that the load balancer will add to the
	response to the client

Parameters:
	farmname - Farm name

Returns:
	Array ref - headers list

=cut

sub getHTTPRemRespHeader    # ($farm_name,$service)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name ) = @_;
	return &get_http_farm_ee_struct( $farm_name )->{ removeresponseheader };
}

=begin nd
Function: addHTTPRemRespHeader

	Add a directive "HeadResponseRemove". The HTTP farm will remove a reponse
	header from the backend that matches with this expression

Parameters:
	farmname - Farm name
	header - Header to add

Returns:
	Integer - Error code: 0 on success or 1 on failure

=cut

sub addHTTPRemRespHeader
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $header ) = @_;

	require Zevenet::Farm::Core;
	my $ffile = &getFarmFile( $farm_name );
	my $errno = 1;

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
			# put new headremove after than last one
			if ( $line !~
				 /^[#\s]*(?:AddHeader|HeadRemove|AddResponseHeader|RemoveResponseHead)\s+"/
				 and $rewrite_flag )
			{
				# example: AddHeader "header: to add"
				splice @fileconf, $index, 0, "\tRemoveResponseHead \"$header\"";
				$errno = 0;
				last;
			}
		}
		$index++;
	}
	untie @fileconf;

	&zenlog( "Could not add RemoveResponseHead" ) if $errno;

	return $errno;
}

=begin nd
Function: delHTTPRemRespHeader

	Delete a directive "HeadResponseRemove".

Parameters:
	farmname - Farm name
	index - Header index

Returns:
	Integer - Error code: 0 on success or 1 on failure

=cut

sub delHTTPRemRespHeader    # ($farm_name,$service,$code)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $header_ind ) = @_;

	require Zevenet::Farm::Core;
	my $ffile = &getFarmFile( $farm_name );
	my $errno = 1;

	require Zevenet::Lock;
	&ztielock( \my @fileconf, "$configdir/$ffile" );

	my $index = 0;
	my $ind   = 0;
	foreach my $line ( @fileconf )
	{
		if ( $line =~ /^\s*RemoveResponseHead\s+"/ )
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

	&zenlog( "Could not remove RemoveResponseHead" ) if $errno;

	return $errno;
}

=begin nd
Function: get_http_farm_ee_struct

	It extends farm struct with the parameters exclusives of the EE.
	It no farm struct was passed to the function. The function will returns a new
	farm struct with the enterprise fields

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
	my $farm_st = shift // {};

	$farm_st->{ ignore_100_continue }  = "false";
	$farm_st->{ logs }                 = "false";
	$farm_st->{ addheader }            = [];
	$farm_st->{ headremove }           = [];
	$farm_st->{ addresponseheader }    = [];
	$farm_st->{ removeresponseheader } = [];

	my $farm_filename = &getFarmFile( $farmname );
	open my $fileconf, '<', "$configdir/$farm_filename";

	my $add_req_head_index  = 0;
	my $rem_req_head_index  = 0;
	my $add_resp_head_index = 0;
	my $rem_resp_head_index = 0;
	foreach my $line ( <$fileconf> )
	{
		if ( $line =~ /^[#\s]*Service \"/ ) { last; }
		elsif ( $line =~ /^[#\s]*AddHeader\s+"(.+)"/ )
		{
			push @{ $farm_st->{ addheader } },
			  {
				"id"     => $add_req_head_index++,
				"header" => $1
			  };
		}
		elsif ( $line =~ /^[#\s]*HeadRemove\s+"(.+)"/ )
		{
			push @{ $farm_st->{ headremove } },
			  {
				"id"      => $rem_req_head_index++,
				"pattern" => $1
			  };
		}
		elsif ( $line =~ /^[#\s]*AddResponseHeader\s+"(.+)"/ )
		{
			push @{ $farm_st->{ addresponseheader } },
			  {
				"id"     => $add_resp_head_index++,
				"header" => $1
			  };
		}
		elsif ( $line =~ /^[#\s]*RemoveResponseHead\s+"(.+)"/ )
		{
			push @{ $farm_st->{ removeresponseheader } },
			  {
				"id"      => $rem_resp_head_index++,
				"pattern" => $1
			  };
		}
		elsif ( $line =~ /Ignore100Continue (\d).*/ )
		{
			$farm_st->{ ignore_100_continue } = ( $1 eq '0' ) ? 'false' : 'true';
		}
		elsif ( $line =~ /LogLevel\s+(\d).*/ )
		{
			$farm_st->{ logs } = ( $1 eq '0' ) ? 'false' : 'true';
		}

	}
	close $fileconf;

	return $farm_st;
}

1;

