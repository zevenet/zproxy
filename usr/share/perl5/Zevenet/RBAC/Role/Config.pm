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
use Zevenet::Core;
include 'Zevenet::RBAC::Core';

=begin nd
Function: getRBACRolesList

	List all RBAC roles

Parameters:
	None - .

Returns:
	Array - List with the role names

=cut

sub getRBACRolesList
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $dir = &getRBACRolePath();
	opendir ( DIR, $dir );
	my @roles = grep ( s/.conf$//, readdir ( DIR ) );
	closedir ( DIR );

	return @roles;
}

=begin nd
Function: getRBACRoleExists

	Check if a role profile exists

Parameters:
	Role - Role name

Returns:
	Integer - Return 1 if the role exists or 0 if it doesn't exist

=cut

sub getRBACRoleExists
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $role = shift;
	my $out  = 0;
	$out = 1 if ( grep /^$role$/, &getRBACRolesList() );
	return $out;
}

=begin nd
Function: getRBACRoleParamDefaultStruct

	This function defines a hash with all role configuration parameters

Parameters:
	None - .

Returns:
	Hash ref - Hash with a default role configuration

=cut

sub getRBACRoleParamDefaultStruct
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $struct;

	# list of functions with hashes permissions
	my @functions =
	  qw(getRBACPermissionFgHash getRBACPermissionRbacHash getRBACPermissionSystemHash
	  getRBACPermissionAliasHash getRBACPermissionIpdsHash getRBACPermissionIntefaceHash
	  getRBACPermissionIntefaceVirtualHash getRBACPermissionCertificateHash getRBACPermissionFarmHash);

	foreach my $funct ( @functions )
	{
		# this step is important for strict
		my $funct_ref = \&$funct;
		my $perm      = &$funct_ref();

		foreach my $method ( qw(PUT POST GET DELETE) )
		{
			foreach my $it ( @{ $perm->{ $method } } )
			{
				my $action  = $it->{ action };
				my $section = $it->{ section };

				$struct->{ $section }->{ $action } = 'false';
			}
		}
	}

	# add menus sections actions
	my @menu_list = qw( farm interface ipds farmguardian supportsave
	  system-service log notification cluster certificate backup alias
	  rbac-role rbac-group rbac-user );
	foreach my $section ( @menu_list )
	{
		$struct->{ $section }->{ 'menu' } = 'false';
	}

	return $struct;
}

=begin nd
Function: createRBACRole

	Create a configuration file for a role

Parameters:
	Role - Role name

Returns:
	Integer - 0 on sucess or other value on failure

=cut

sub createRBACRole
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $role = shift;

	my $conf     = &getRBACRoleParamDefaultStruct();
	my $fileName = &getRBACRoleFile( $role );
	my $touch    = &getGlobalConfiguration( 'touch' );

	my $error = &logAndRun( "$touch $fileName" );
	if ( !$error )
	{
		require Config::Tiny;
		my $fileHandle = Config::Tiny->read( $fileName );
		foreach my $key ( keys %{ $conf } )
		{
			$fileHandle->{ $key } = $conf->{ $key };
		}
		$fileHandle->write( $fileName );
	}

	return $error;
}

=begin nd
Function: delRBACRole

	Delete a role configuration file

Parameters:
	Role - Role name

Returns:
	None - .

=cut

sub delRBACRole
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $role = shift;
	my $file = &getRBACRoleFile( $role );
	unlink $file;
}

=begin nd
Function: setRBACRoleConfigFile

	Save the changes in a config file.
	it can receives a hash ref with the parameter that has changed

Parameters:
	Role - Role to update
	key - it is a hash with same struct than configuration file. It has the parameters to change

Returns:
	None - .

=cut

sub setRBACRoleConfigFile
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $role, $obj ) = @_;

	require Zevenet::Lock;
	require Config::Tiny;

	my $rbacRoleFileConfig = &getRBACRoleFile( $role );
	my $lockfile           = "/tmp/rbac_role_$role.lock";
	my $lh                 = &openlock( $lockfile, 'w' );
	my $fileHandle         = Config::Tiny->read( $rbacRoleFileConfig );

	# save all struct
	if ( ref $obj )
	{
		foreach my $key ( keys %{ $obj } )
		{
			foreach my $param ( keys %{ $obj->{ $key } } )
			{
				$fileHandle->{ $key }->{ $param } = $obj->{ $key }->{ $param };
			}
		}
	}
	$fileHandle->write( $rbacRoleFileConfig );
	close $lh;
}

sub getRBACRole
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $role = shift;

	require Config::Tiny;
	my $roleFile   = &getRBACRoleFile( $role );
	my $fileHandle = Config::Tiny->read( $roleFile );
	my $out;

	my $paramStruct = &getRBACRoleParamDefaultStruct();

	foreach my $structKey ( keys %{ $paramStruct } )
	{
		foreach my $paramKey ( keys %{ $paramStruct->{ $structKey } } )
		{
			$out->{ $structKey }->{ $paramKey } =
			  $fileHandle->{ $structKey }->{ $paramKey } // 'false';
		}
	}

	return $out;
}

sub getRBACMenus
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $role;
	my $user = &getUser();

	if ( $user eq 'root' )
	{
		# get struct default
		$role = &getRBACRoleParamDefaultStruct();
	}
	else
	{
		include 'Zevenet::RBAC::Group::Core';
		my $group = &getRBACUserGroup( $user );
		my $role_name = &getRBACGroupParam( $group, 'role' );
		$role = &getRBACRole( $role_name );
	}

	# build the strcuct
	my $menus = {};
	foreach my $sect ( keys %{ $role } )
	{
		next if ( !exists $role->{ $sect }->{ menu } );

		# all menus are allowed for root
		$menus->{ $sect } =
		  ( $user eq 'root' )
		  ? 'true'
		  : $role->{ $sect }->{ menu };
	}

	# add the static menus. Those are not editable
	my $perm = ( $user eq 'root' ) ? 'true' : 'false';
	$menus->{ 'factory' }                = $perm;
	$menus->{ 'activation-certificate' } = $perm;

	return $menus;
}

1;

