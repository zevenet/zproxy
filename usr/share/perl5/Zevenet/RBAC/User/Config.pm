#!/usr/bin/perl

use strict;

use Zevenet::Core;
use Zevenet::RBAC::User::Core;
use Zevenet::RBAC::User::Runtime;

# rbac configuration paths
my $rbacUserConfig = &getRBACUserConf();

=begin nd
Function: setRBACUserLockConfigFile

	Lock the user configuration file for nobody writes in it

Parameters:
	None - .

Returns:
	Integer - 0 on failure or other value on success

=cut

sub setRBACUserLockConfigFile
{
	require Zevenet::Lock;

	my $lockfile = "/tmp/rbac_users.lock";
	return &lockfile( $lockfile );
}

=begin nd
Function: setRBACUserUnlockConfigFile

	Unlock the user configuration file

Parameters:
	Integer - Lock file identifier

Returns:
	None - .

=cut

sub setRBACUserUnlockConfigFile
{
	my $lock_fd = shift;

	require Zevenet::Lock;
	&unlockfile( $lock_fd );
}

=begin nd
Function: setRBACUserConfigFile

	Save a change in a config file.
	This function has 2 behaviors:
	it can receives a hash ref to save a struct
	or it can receive a key and parameter to replace a value

Parameters:
	User - User to apply the change
	key - parameter to change or struct ref
	value - new value for the parameter

Returns:
	None - .

=cut

sub setRBACUserConfigFile
{
	my ( $user, $key, $value ) = @_;

	my $lock       = &setRBACUserLockConfigFile();
	my $fileHandle = Config::Tiny->read( $rbacUserConfig );

	# save all struct
	if ( ref $key )
	{
		$fileHandle->{ $user } = $key;
	}

	# save a parameter
	else
	{
		$fileHandle->{ $user }->{ $key } = $value;
	}
	$fileHandle->write( $rbacUserConfig );
	&setRBACUserUnlockConfigFile( $lock );
}

=begin nd
Function: createRBACUser

	Add a user to the RBAC module

Parameters:
	User - User name
	Password - Password for the user

Returns:
	Integer -  Error code: 0 on success or other value on failure

=cut

sub createRBACUser
{
	my $user   = shift;
	my $passwd = shift;
	my $user_obj;

	# execute cmd
	my $error = &runRBACCreateUserCmd( $user );

	# Change pass
	require Zevenet::Login;
	$error = &changePassword( $user, $passwd ) if ( !$error );

	# write in config file
	if ( !$error )
	{
		# get password from system
		my ( undef, $encrypt_pass ) = getpwnam ( $user );

		# save it
		$user_obj->{ 'password' }           = $encrypt_pass;
		$user_obj->{ 'zapi_permissions' }   = 'false';
		$user_obj->{ 'webgui_permissions' } = 'false';
		$user_obj->{ 'zapikey' }            = '';

		&setRBACUserConfigFile( $user, $user_obj );
	}

	return $error;
}

=begin nd
Function: delRBACUser

	It deletes a RBAC user

Parameters:
	User - User name

Returns:
	Integer -  Error code: 0 on success or other value on failure

=cut

sub delRBACUser
{
	my $user = shift;

	include 'Zevenet::RBAC::Group::Config';

	# delete from its group
	my $group = &getRBACUserGroup( $user );
	my $error = &delRBACGroupResource( $group, $user, 'users' ) if ( $group );

	# remove from system. It removes the user of the groups
	$error = &runRBACDeleteUserCmd( $user ) if ( !$error );

	# remove from config file
	if ( !$error )
	{
		my $lock       = &setRBACUserLockConfigFile();
		my $fileHandle = Config::Tiny->read( $rbacUserConfig );
		delete $fileHandle->{ $user };
		$fileHandle->write( $rbacUserConfig );
		&setRBACUserUnlockConfigFile( $lock );
	}

	return $error;
}

=begin nd
Function: setRBACUserWebPermissions

	Allow to a user to use the web gui

Parameters:
	User - User name
	Actived - "true" if the user has got webgui permissions or "false" it it has not got

Returns:
	Integer -  Error code: 0 on success or other value on failure

=cut

sub setRBACUserWebPermissions
{
	my $user    = shift;
	my $actived = shift;

	# enable
	if ( $actived eq "true" )
	{
		return 1 if ( &runRBACAddUserToGroup( $user, "webgui" ) );
		&setRBACUserConfigFile( $user, "webgui_permissions", "true" );
	}

	# disable
	else
	{
		return 1 if ( &runRBACDelUserToGroup( $user, "webgui" ) );
		&setRBACUserConfigFile( $user, "webgui_permissions", "false" );
	}
	return 0;
}

=begin nd
Function: setRBACUserZapiPermissions

	Allow to a user to use the zapi

Parameters:
	User - User name
	Actived - "true" if the user has got zapi permissions or "false" it it has not got

Returns:
	Integer -  Error code: 0 on success or other value on failure

=cut

sub setRBACUserZapiPermissions
{
	my $user    = shift;
	my $actived = shift;

	# enable
	if ( $actived eq "true" )
	{
		return 1 if ( &runRBACAddUserToGroup( $user, "zapi" ) );
		&setRBACUserConfigFile( $user, "zapi_permissions", "true" );
	}

	# disable
	else
	{
		return 1 if ( &runRBACDelUserToGroup( $user, "zapi" ) );
		&setRBACUserConfigFile( $user, "zapi_permissions", "false" );
	}
	return 0;
}

=begin nd
Function: setRBACUserZapikey

	Change the zapikey for a user

Parameters:
	User - User name
	zapikey - zapikey in plain text

Returns:
	Integer -  Error code: 0 on success or other value on failure

=cut

sub setRBACUserZapikey
{
	my ( $user, $zapikey ) = @_;

	include 'Zevenet::Code';

	# encrypt
	$zapikey = &setCryptString( $zapikey );

	# save
	&setRBACUserConfigFile( $user, "zapikey", $zapikey );
}

=begin nd
Function: setRBACUserPassword

	Change the password for a user

Parameters:
	User - User name
	password - the new password

Returns:
	Integer -  Error code: 0 on success or other value on failure

=cut

sub setRBACUserPassword
{
	my $user     = shift;
	my $password = shift;

	# Change pass
	require Zevenet::Login;

	if ( !&changePassword( $user, $password ) )
	{
		# get password from system
		my ( undef, $encrypt_pass ) = getpwnam ( $user );

		# save it in the config file
		&setRBACUserConfigFile( $user, 'password', $encrypt_pass ) if ( $encrypt_pass );
	}
}

1;
