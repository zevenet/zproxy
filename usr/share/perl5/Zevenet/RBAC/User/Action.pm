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
include 'Zevenet::RBAC::User::Core';
include 'Zevenet::RBAC::User::Runtime';

# rbac configuration paths
my $rbacUserConfig = &getRBACUserConf();

=begin nd
Function: updateRBACUser

	Apply command lines to update a user with the configuration file

Parameters:
	User - User name
	Action - The available actions are: "add", create a user in the system; "delete",
	delete a user from the system; "modify", update the parameters of the user; or "", nothing
	review the user and update it.

Returns:
	None - .

=cut

sub updateRBACUser
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $user   = shift;
	my $action = shift;

	# DELETE
	if ( $action eq 'delete' )
	{
		&runRBACDeleteUserCmd( $user );
	}

	# POST
	elsif ( $action eq 'add' )
	{
		&runRBACCreateUserCmd( $user );

		# set user password
		my $password = &getRBACUserParam( $user, 'password' );
		&setRBACUserPasswordInSystem( $user, $password );
	}

	# PUT
	elsif ( $action eq 'modify' )
	{
		my $user_struct = &getRBACUserObject( $user );

		# set zapi permissions
		if ( $user_struct->{ 'zapi_permissions' } eq 'true' )
		{
			&runRBACAddUserToGroup( $user, 'zapi' )
			  if ( !&getRBACUserIsMember( $user, 'zapi' ) );
		}
		else
		{
			&runRBACDelUserToGroup( $user, 'zapi' )
			  if ( &getRBACUserIsMember( $user, 'zapi' ) );
		}

		# set webgui permissions
		if ( $user_struct->{ 'webgui_permissions' } eq 'true' )
		{
			&runRBACAddUserToGroup( $user, 'webgui' )
			  if ( !&getRBACUserIsMember( $user, 'webgui' ) );
		}
		else
		{
			&runRBACDelUserToGroup( $user, 'webgui' )
			  if ( &getRBACUserIsMember( $user, 'webgui' ) );
		}

		# set user password
		my $password = $user_struct->{ 'password' };
		my ( undef, $encrypt_pass ) = getpwnam ( $user );
		if ( $encrypt_pass ne $password )
		{
			&setRBACUserPasswordInSystem( $user, $password );
		}
	}

	# check status and apply necessary actions
	else
	{
		my $user_struct = &getRBACUserObject( $user );

		# check if it exists
		my ( $id_user, $encrypt_pass ) = getpwnam ( $user );
		if ( !$id_user )
		{
			&runRBACCreateUserCmd( $user );
		}

		# update it
		# set zapi permissions
		if ( $user_struct->{ 'zapi_permissions' } eq 'true' )
		{
			&runRBACAddUserToGroup( $user, 'zapi' )
			  if ( !&getRBACUserIsMember( $user, 'zapi' ) );
		}
		else
		{
			&runRBACDelUserToGroup( $user, 'zapi' )
			  if ( &getRBACUserIsMember( $user, 'zapi' ) );
		}

		# set webgui permissions
		if ( $user_struct->{ 'webgui_permissions' } eq 'true' )
		{
			&runRBACAddUserToGroup( $user, 'webgui' )
			  if ( !&getRBACUserIsMember( $user, 'webgui' ) );
		}
		else
		{
			&runRBACDelUserToGroup( $user, 'webgui' )
			  if ( &getRBACUserIsMember( $user, 'webgui' ) );
		}

		# set user password
		my $password = $user_struct->{ 'password' };
		if ( $encrypt_pass ne $password )
		{
			&setRBACUserPasswordInSystem( $user, $password );
		}
	}

}

=begin nd
Function: updateRBACAllUser

	Read the user config file and update in the system all users

Parameters:
	None - .

Returns:
	None - .

=cut

sub updateRBACAllUser
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my @userList = &getRBACUserList();

	# delete the removed users
	foreach my $user ( &getRBACGroupMembers( "rbac" ) )
	{
		if ( !&getRBACUserExists( $user ) )
		{
			&runRBACDeleteUserCmd( $user );
		}
	}

	# update all users
	foreach my $user ( @userList )
	{
		&updateRBACUser( $user );
	}
}

=begin nd
Function: setRBACUserPasswordInSystem

	Save in the file /etc/shadow the encrypted password copied from config file

Parameters:
	User - User name
	Password - Encrypted password of user to save in shadow file


Returns:
	None - .

=cut

sub setRBACUserPasswordInSystem
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $user     = shift;
	my $password = shift;

	require Zevenet::Lock;
	my $shadow_file = &getGlobalConfiguration( 'shadow_file' );
	&ztielock( \my @array, $shadow_file );

	foreach my $line ( @array )
	{
		last if ( $line =~ s/^$user:[^:]+/$user:$password/ );
	}
	untie @array;
}

1;

