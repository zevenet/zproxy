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

=begin nd
Function: getSsh

	Returns hash reference to ssh configuration.

Parameters:
	none - .

Returns:
	scalar - Hash reference.

	Example:

	{
		'port'   => 22,
		'listen' => "*",
	}

See Also:
	zapi/v3/system.cgi, dos.cgi
=cut

sub getSsh
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Validate;

	my $sshFile       = &getGlobalConfiguration( 'sshConf' );
	my $listen_format = &getValidFormat( 'ssh_listen' );
	my $ssh           = {                                       # conf
				'port'   => 22,
				'listen' => "*",
	};

	if ( !-e $sshFile )
	{
		return;
	}
	else
	{
		require Tie::File;
		tie my @file, 'Tie::File', $sshFile;

		foreach my $line ( @file )
		{
			if ( $line =~ /^Port\s+(\d+)/ )
			{
				$ssh->{ 'port' } = $1;
			}
			elsif ( $line =~ /^ListenAddress\s+($listen_format)/ )
			{
				$ssh->{ 'listen' } = $1;
			}
		}
		untie @file;
	}

	$ssh->{ 'listen' } = '*' if ( $ssh->{ 'listen' } eq '0.0.0.0' );
	return $ssh;
}

=begin nd
Function: setSsh

	Set ssh configuration.

	To listen on all the ip addresses set 'listen' to '*'.

Parameters:
	sshConf - Hash reference with ssh configuration.

	Example:

	$ssh = {
			'port'   => 22,
			'listen' => "*",
	};

Returns:
	integer - ERRNO or return code of ssh restart.

See Also:
	zapi/v3/system.cgi
=cut

sub setSsh
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $sshConf ) = @_;

	my $sshFile = &getGlobalConfiguration( 'sshConf' );
	my $output  = 1;
	my $index = 5;    # default, it is the line where will add port
	                  # and listen if one of this doesn't exist

	# create flag to check all params are changed
	my $portFlag;
	my $listenFlag;
	$portFlag   = 1 if ( exists $sshConf->{ 'port' } );
	$listenFlag = 1 if ( exists $sshConf->{ 'listen' } );

	$sshConf->{ 'listen' } = '0.0.0.0' if ( $sshConf->{ 'listen' } eq '*' );

	if ( !-e $sshFile )
	{
		&zenlog( "SSH configuration file doesn't exist.", "error", "SYSTEM" );
		return -1;
	}

	require Tie::File;
	tie my @file, 'Tie::File', $sshFile;

	foreach my $line ( @file )
	{
		if ( $portFlag )
		{
			if ( $line =~ /^Port\s+/ )
			{
				$line     = "Port $sshConf->{ 'port' }";
				$output   = 0;
				$portFlag = 0;
			}
		}

		if ( $listenFlag )
		{
			if ( $line =~ /^ListenAddress\s+/ )
			{
				$line       = "ListenAddress $sshConf->{ 'listen' }";
				$listenFlag = 0;
			}
		}
	}

	# Didn't find port and required a change
	if ( $portFlag )
	{
		splice @file, $index, 0, "Port $sshConf->{ 'port' }";
	}

	# Didn't find listen and required a change
	if ( $listenFlag )
	{
		splice @file, $index, 0, "ListenAddress $sshConf->{ 'listen' }";
	}
	untie @file;

	# restart service to apply changes
	include 'Zevenet::IPDS::DoS::Config';

	my $cmd = &getGlobalConfiguration( 'sshService' ) . " restart";
	$output = &logAndRun( $cmd );

	return $output;
}

1;
