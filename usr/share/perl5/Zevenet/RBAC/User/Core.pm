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

my $rbacUserConfig = &getRBACUserConf();

=begin nd
Function: getRBACUserConf

	Return the path of the user configuration files

Parameters:
	None - .

Returns:
	String - path

=cut

sub getRBACUserConf
{
	my $rbacPath = &getRBACConfPath();
	return "$rbacPath/users.conf";
}

=begin nd
Function: getRBACUserList

	List all created users in the load balancer

Parameters:
	None - .

Returns:
	Array - List of users

=cut

sub getRBACUserList
{
	require Config::Tiny;
	my $fileHandle = Config::Tiny->read( $rbacUserConfig );

	return keys %{ $fileHandle };
}

=begin nd
Function: getRBACUserExists

	Check if a user exists in the load balancer

Parameters:
	User - User name

Returns:
	Integer - 1 if the user exists or 0 if it doesn't exist

=cut

sub getRBACUserExists
{
	my $user = shift;

	my $out = 0;
	$out = 1 if ( grep ( /^$user$/, &getRBACUserList() ) );

	return $out;
}

=begin nd
Function: getRBACUserObject

	get a object with all parameters of a user

Parameters:
	User - User name

Returns:
	Hash ref - Configuration of a user

=cut

sub getRBACUserObject
{
	my $user = shift;

	require Config::Tiny;
	my $fileHandle = Config::Tiny->read( $rbacUserConfig );

	return $fileHandle->{ $user };
}

=begin nd
Function: getRBACUserParam

	Get a configuration parameter of a user

Parameters:
	User - User name
	Parameter - Required parameter

Returns:
	Scalar - the data type depends of the required parameter

=cut

sub getRBACUserParam
{
	my $user   = shift;
	my $param  = shift;
	my $object = &getRBACUserObject( $user );
	return $object->{ $param };
}

=begin nd
Function: validateRBACUserZapi

	It validate if a user has zapi permissions and check if the zapikey is correct

Parameters:
	User - User name
	zapikey - Zapikey sent by the user. It is encrypt

Returns:
	Integer - 1 if the user has been validated sucessfully or 0 if it has not

=cut

sub validateRBACUserZapi
{
	my ( $zapikey ) = @_;

	include 'Zevenet::Code';

	# look for the user owned of zapikey
	my $user = &getRBACUserbyZapikey( $zapikey );

	if ( !$user )
	{
		&zenlog( "RBAC, the zapikey does not match with any user", "warning", "RBAC" );
		return 0;
	}
	elsif ( $user eq 'root' )
	{
		return $user;
	}

	# check permissions
	my $groups      = &getGlobalConfiguration( 'groups_bin' );
	my $user_groups = `$groups $user`;
	chomp $user_groups;

	if ( !grep ( / zapi( |$)/, $user_groups ) )
	{
		&zenlog( "RBAC, the user $user has not zapi permissions", "warning", "RBAC" );
		return 0;
	}

	return $user;
}


sub getRBACUserbyZapikey
{
	my $zapikey = shift;
	my $user;
	include 'Zevenet::Zapi';
	include 'Zevenet::Code';
	if ( &validateCryptString( &getZAPI( 'zapikey' ), $zapikey ) )
	{
		$user = 'root';
	}
	else
	{
		require Config::Tiny;
		my $fileHandle = Config::Tiny->read( $rbacUserConfig );
		foreach my $key ( keys %{ $fileHandle } )
		{
			if ( &validateCryptString( $fileHandle->{ $key }->{ 'zapikey' }, $zapikey ) )
			{
				$user = $key;
				last;
			}
		}
	}

	return $user;
}



1;
