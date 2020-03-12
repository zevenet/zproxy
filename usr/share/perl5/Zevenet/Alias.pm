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

use Zevenet::Log;
use Zevenet::Config;
use Config::Tiny;

my $alias_file = &getGlobalConfiguration( "configdir" ) . "/alias.conf";
my $lockfile   = "/tmp/alias_file.lock";

sub createAliasFile
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $fh;

	open ( $fh, '>', $alias_file );
	print $fh "[backend]\n\n[interface]\n";
	close $fh;
}

# Get a backend alias or interface alias
sub getAlias
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $type, $name ) = @_;

	my $out;

	if ( !-f $alias_file )
	{
		&createAliasFile();
	}

	my $fileHandle = Config::Tiny->read( $alias_file );

	if ( $name )
	{
		$out = $fileHandle->{ $type }->{ $name }
		  if exists $fileHandle->{ $type }->{ $name };
	}
	elsif ( $type )
	{
		$out = $fileHandle->{ $type };
	}
	else
	{
		$out = $fileHandle;
	}

	return $out;
}

# remove a nick
sub delAlias
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	# ip is the interface ip or the backend ip
	my ( $type, $ip ) = @_;

	require Zevenet::Lock;

	if ( !-f $alias_file )
	{
		&createAliasFile();
	}

	my $lock = &openlock( $lockfile, 'w' );
	my $fileHandle = Config::Tiny->read( $alias_file );

	if ( exists $fileHandle->{ $type }->{ $ip } )
	{
		delete $fileHandle->{ $type }->{ $ip };
	}

	$fileHandle->write( $alias_file );
	close $lock;
}

# modify or create a nick
sub setAlias
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	# ip is the interface ip or the backend ip
	my ( $type, $ip, $alias ) = @_;

	require Zevenet::Lock;

	if ( !-f $alias_file )
	{
		&createAliasFile();
	}

	my $lock = &openlock( $lockfile, 'w' );
	my $fileHandle = Config::Tiny->read( $alias_file );

	# save all struct
	$fileHandle->{ $type }->{ $ip } = $alias;

	$fileHandle->write( $alias_file );
	close $lock;
}

# Add to the backend array the alias field
sub addAliasBackendsStruct
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $servers = shift;

	include 'Zevenet::RBAC::Core';
	my $permission = &getRBACRolePermission( 'alias', 'list' );
	my $alias = &getAlias( 'backend' );

	if ( ref $servers eq 'ARRAY' )
	{
		foreach my $bk ( @{ $servers } )
		{
			$bk->{ alias } = $permission ? $alias->{ $bk->{ ip } } : undef;
		}
	}
	elsif ( ref $servers eq 'HASH' )
	{
		$servers->{ alias } = $permission ? $alias->{ $servers->{ ip } } : undef;
	}

	return $servers;
}

1;

