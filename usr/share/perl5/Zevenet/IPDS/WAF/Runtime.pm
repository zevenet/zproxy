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

use Zevenet::Core;
use Zevenet::Lock;

include 'Zevenet::IPDS::WAF::Core';

=begin nd
Function: reloadWAFByFarm

	It reloads a farm to update the WAF configuration.

Parameters:
	Farm - It is the farm name

Returns:
	Integer - It returns 0 on success or another value on failure.

=cut

sub reloadWAFByFarm
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farm = shift;
	my $err  = 0;

	require Zevenet::Farm::Base;
	return 0 if ( &getFarmStatus( $farm ) ne 'up' );

	require Zevenet::Farm::HTTP::Config;
	my $proxy_ctl = &getGlobalConfiguration( 'proxyctl' );
	my $socket    = &getHTTPFarmSocket( $farm );

	$err = &logAndRun( "$proxy_ctl -c $socket -R 0" );

	return $err;
}

=begin nd
Function: addWAFsetToFarm

	It applies a WAF set to a HTTP farm.

Parameters:
	Farm - It is the farm name
	Set  - It is the WAF set name

Returns:
	Integer - It returns 0 on success or another value on failure.

=cut

sub addWAFsetToFarm
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farm = shift;
	my $set  = shift;
	my $err  = 1;

	use File::Copy;
	require Zevenet::Farm::Core;

	my $set_file  = &getWAFSetFile( $set );
	my $farm_file = &getFarmFile( $farm );
	my $configdir = &getGlobalConfiguration( 'configdir' );
	my $farm_path = "$configdir/$farm_file";
	my $tmp_conf  = "/tmp/waf_$farm.tmp";
	my $proxy     = &getGlobalConfiguration( 'proxy' );
	my $cp        = &getGlobalConfiguration( 'cp' );
	my $mv        = &getGlobalConfiguration( 'mv' );

	my $lock_file = &getLockFile( $tmp_conf );
	my $lock_fh = &openlock( $lock_file, 'w' );

	$err = &logAndRun( "$cp $farm_path $tmp_conf" );
	if ( $err )
	{
		&zenlog( "The file $farm_path could not be copied", "error", "waf" );
		unlink $tmp_conf;
		close $lock_fh;
		return $err;
	}

	use Tie::File;
	tie my @filefarmhttp, 'Tie::File', $tmp_conf;

	# write conf
	my $flag_sets = 0;
	foreach my $line ( @filefarmhttp )
	{
		if ( $line =~ /[\s#]*WafRules/ )
		{
			$flag_sets = 1;
		}
		elsif ( $line !~ /[\s#]*WafRules/ and $flag_sets )
		{
			$err  = 0;
			$line = "\tWafRules	\"$set_file\"" . "\n" . $line;
			last;
		}

		# not found any waf directive
		elsif ( $line =~ /[\s#]*ZWACL-INI"/ or $line =~ /[\s#]*Service "/ )
		{
			$err  = 0;
			$line = "\tWafRules	\"$set_file\"" . "\n" . $line;
			last;
		}
	}
	untie @filefarmhttp;

	# check config file
	my $cmd = "$proxy -f $tmp_conf -c";
	$err = &logAndRun( $cmd );
	if ( $err )
	{
		unlink $tmp_conf;
		close $lock_fh;
		return $err;
	}

	require Zevenet::Farm::Base;

	# if there is not error, overwrite configfile
	$err = &logAndRun( "$mv $tmp_conf $farm_path" );
	if ( $err )
	{
		&zenlog( 'Error saving changes', 'error', "waf" );
	}
	elsif ( &getFarmStatus( $farm ) eq 'up' )
	{
		# reload farm
		$err = &reloadWAFByFarm( $farm );
	}

	# Not to need farm restart
	close $lock_fh;

	return $err;
}

=begin nd
Function: removeWAFSetFromFarm

	It removes a WAF set from a HTTP farm.

Parameters:
	Farm - It is the farm name
	Set  - It is the WAF set name

Returns:
	Integer - It returns 0 on success or another value on failure.

=cut

sub removeWAFSetFromFarm
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farm = shift;
	my $set  = shift;
	my $err  = 0;

	require Zevenet::Farm::Core;

	my $set_file  = &getWAFSetFile( $set );
	my $farm_file = &getFarmFile( $farm );
	my $configdir = &getGlobalConfiguration( 'configdir' );
	my $farm_path = "$configdir/$farm_file";

	my $lock_file = &getLockFile( $farm );
	my $lock_fh = &openlock( $lock_file, 'w' );

	# write conf
	$err = 1;
	&ztielock( \my @fileconf, $farm_path );

	my $index = 0;
	foreach my $line ( @fileconf )
	{
		if ( $line =~ /^\s*WafRules\s+\"$set_file\"/ )
		{
			$err = 0;
			splice @fileconf, $index, 1;
			last;
		}
		$index++;
	}
	untie @fileconf;

	# This is a bugfix. Not to check WAF when it is deleting rules.

	# reload farm
	require Zevenet::Farm::Base;
	if ( &getFarmStatus( $farm ) eq 'up' and !$err )
	{
		$err = &reloadWAFByFarm( $farm );
	}

	close $lock_fh;

	# Not to need farm restart
	unlink $lock_file;

	return $err;
}

=begin nd
Function: reloadWAFByRule

	It reloads all farms where the WAF set is applied

Parameters:
	Set  - It is the WAF set name

Returns:
	Integer - It returns 0 on success or another value on failure.

=cut

sub reloadWAFByRule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $set = shift;
	my $err;

	require Zevenet::Farm::Base;
	foreach my $farm ( &listWAFBySet( $set ) )
	{
		if ( &getFarmStatus( $farm ) eq 'up' )
		{
			if ( &reloadWAFByFarm( $farm ) )
			{
				$err++;
				&zenlog( "Error reloading the WAF in the farm $farm", "error", "waf" );
			}
		}
	}
	return $err;
}

1;

