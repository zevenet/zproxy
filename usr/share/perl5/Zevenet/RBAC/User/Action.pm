#!/usr/bin/perl

use strict;

use Zevenet::Core;
use Zevenet::RBAC::User::Core;
use Zevenet::RBAC::User::Runtime;

# rbac configuration paths
my $rbacPath       = &getRBACConfPath();
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
	my $user   = shift;
	my $action = shift;

	require Zevenet::RBAC::User::Config;

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
		my $groups     = &getGlobalConfiguration( 'groups_bin' );
		my $permission = `$groups $user`;
		chomp $permission;

		my $user_struct = &getRBACUserObject( $user );

		# set zapi permissions
		if ( $user_struct->{ 'zapi_permissions' } eq 'true' )
		{
			&runRBACAddUserToGroup( $user, 'zapi' ) if ( $permission !~ / zapi( |$)/ );
		}
		else
		{
			&runRBACDelUserToGroup( $user, 'zapi' ) if ( $permission =~ / zapi( |$)/ );
		}

		# set webgui permissions
		if ( $user_struct->{ 'webgui_permissions' } eq 'true' )
		{
			&runRBACAddUserToGroup( $user, 'webgui' ) if ( $permission !~ / webgui( |$)/ );
		}
		else
		{
			&runRBACDelUserToGroup( $user, 'webgui' ) if ( $permission =~ / webgui( |$)/ );
		}

		# set user password
		my $password = $user_struct->{ 'password' };
		my ( $id, $encrypt_pass ) = getpwnam ( $user );
		if ( $encrypt_pass ne $password )
		{
			&setRBACUserPasswordInSystem( $user, $password );
		}
	}

	# check status and apply necessary actions
	else
	{
		# check if it exists
		my ( $id_user, $encrypt_pass ) = getpwnam ( $user );
		if ( !$id_user )
		{
			&runRBACCreateUserCmd( $user );
		}

		# update it
		my $user_struct = &getRBACUserObject( $user );
		my $groups      = &getGlobalConfiguration( 'groups_bin' );
		my $permission  = `$groups $user`;
		chomp $permission;

		# set zapi permissions
		if ( $user_struct->{ 'zapi_permissions' } eq 'true' )
		{
			&runRBACAddUserToGroup( $user, 'zapi' ) if ( $permission !~ / zapi( |$)/ );
		}
		else
		{
			&runRBACDelUserToGroup( $user, 'zapi' ) if ( $permission =~ / zapi( |$)/ );
		}

		# set webgui permissions
		if ( $user_struct->{ 'webgui_permissions' } eq 'true' )
		{
			&runRBACAddUserToGroup( $user, 'webgui' ) if ( $permission !~ / webgui( |$)/ );
		}
		else
		{
			&runRBACDelUserToGroup( $user, 'webgui' ) if ( $permission =~ / webgui( |$)/ );
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

=begin nd
Function: initRBACModule

	Create configuration files and run all needed commands requested to RBAC module

Parameters:
	None - .
					
Returns:
	None - .
	
=cut

sub initRBACModule
{
	my $touch    = &getGlobalConfiguration( "touch" );
	my $groupadd = &getGlobalConfiguration( "groupadd_bin" );
	mkdir $rbacPath                        if ( !-d $rbacPath );
	&logAndRun( "$touch $rbacUserConfig" ) if ( !-f $rbacUserConfig );
	&logAndRun( "$groupadd zapi" )         if ( !getgrnam ( 'zapi' ) );
	&logAndRun( "$groupadd rbac" )         if ( !getgrnam ( 'rbac' ) );

	&updateRBACAllUser();
}

1;

