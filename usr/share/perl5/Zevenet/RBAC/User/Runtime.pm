#!/usr/bin/perl

use strict;

use Zevenet::Core;
use Zevenet::RBAC::User::Core;

# rbac configuration paths
my $rbacPath       = &getRBACConfPath();
my $rbacUserConfig = &getRBACUserConf();

=begin nd
Function: runRBACCreateUserCmd

	It executes the command to create a user in the system

Parameters:
	User - User name
					
Returns:
	Integer -  Error code: 0 on success or other value on failure
	
=cut

sub runRBACCreateUserCmd
{
	my $user    = shift;
	my $adduser = &getGlobalConfiguration( "adduser_bin" );

	# create user
	my $cmd = "$adduser --system --shell /bin/false --no-create-home $user";
	return 1 if ( &logAndRun( $cmd ) );

	# add to rbac group
	return &runRBACAddUserToGroup( $user, "rbac" );
}

=begin nd
Function: runRBACDeleteUserCmd

	Add a user to the RBAC module

Parameters:
	User - User name
	Password - Password for the user
					
Returns:
	Integer -  Error code: 0 on success or other value on failure
	
=cut

sub runRBACDeleteUserCmd
{
	my $user    = shift;
	my $deluser = &getGlobalConfiguration( "deluser_bin" );

	my $cmd = "$deluser $user";
	return &logAndRun( $cmd );
}

=begin nd
Function: runRBACAddUserToGroup

	Run a system command to add a user to a group

Parameters:
	User - User name
	Group - group name
					
Returns:
	Integer -  Error code: 0 on success or other value on failure
	
=cut

sub runRBACAddUserToGroup
{
	my ( $user, $group ) = @_;
	my $adduser = &getGlobalConfiguration( "adduser_bin" );
	my $cmd     = "$adduser $user $group";
	return &logAndRun( $cmd );
}

=begin nd
Function: runRBACDelUserToGroup

	Run a system command to delete a user from a group

Parameters:
	User - User name
	Group - group name
					
Returns:
	Integer -  Error code: 0 on success or other value on failure
	
=cut

sub runRBACDelUserToGroup
{
	my ( $user, $group ) = @_;
	my $deluser = &getGlobalConfiguration( "deluser_bin" );
	my $cmd     = "$deluser $user $group";
	return &logAndRun( $cmd );
}

1;
