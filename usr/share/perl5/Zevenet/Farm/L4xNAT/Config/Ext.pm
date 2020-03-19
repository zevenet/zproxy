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

require Zevenet::Farm::L4xNAT::Config;
my $configdir = &getGlobalConfiguration( 'configdir' );

=begin nd
Function: setL4FarmParamExt

	It sets a l4 farm parameter that only applies in enterprise.
	It is equivalent to 'setL4FarmParam'

Parameters:
	param name - Name of the value in Zevenet. The options are: 'logs' and 'log-prefix'
	param value - Value for the parameter
	farmname - Farm name

		the parameters expects the following values:
			logs: true|false
			log-prefix: undef, the prefix string is taken from farmname


Returns:
	Integer - return 0 on success or <> 0 on failure

=cut

sub setL4FarmParamExt    # ($param, $value, $farm_name)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $param, $value, $farm_name ) = @_;

	require Zevenet::Farm::Core;
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $srvparam      = "";

	if ( $param eq "logs" )
	{
		$srvparam = "log";
		$value    = "forward" if ( $value eq "true" );
		$value    = "none" if ( $value eq "false" );
	}
	elsif ( $param eq "log-prefix" )
	{
		$srvparam = "log-prefix";
		$value    = "l4:$farm_name ";

	  # TODO: put a warning msg when farm name is longer than nftables reserved log size
	}
	else
	{
		return -1;
	}

	require Zevenet::Nft;
	$output = &sendL4NlbCmd(
		{
		   farm   => $farm_name,
		   file   => ( $param ne 'status' ) ? "$configdir/$farm_filename" : undef,
		   method => "PUT",
		   uri    => "/farms",
		   body   => qq({"farms" : [ { "name" : "$farm_name", "$srvparam" : "$value" } ] })
		}
	);

	return $output;
}

=begin nd
Function: modifyLogsParam

	It enables or disables the logs for a l4xnat farm

Parameters:
	farmname - Farm name
	log value - The possible values are: 'true' to enable the logs or 'false' to disable them

Returns:
	String - return an error message on error or undef on success

=cut

sub modifyLogsParam
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname  = shift;
	my $logsValue = shift;

	my $msg;
	my $err = 0;
	if ( $logsValue =~ /(?:true|false)/ )
	{
		$err = &setL4FarmParamExt( 'logs',       $logsValue, $farmname );
		$err = &setL4FarmParamExt( 'log-prefix', undef,      $farmname )
		  if ( !$err and $logsValue eq 'true' );
	}
	else
	{
		$msg = "Invalid value for logs parameter.";
	}

	if ( $err )
	{
		$msg = "Error modifying the parameter logs.";
	}
	return $msg;
}

1;

