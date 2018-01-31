#!/usr/bin/perl

use strict;

use Zevenet::Core;
use Zevenet::RBAC::Group::Core;

# rbac configuration paths
my $rbacGroupConfig = &getRBACGroupConf();

=begin nd
Function: runRBACCreateGroupCmd

	It executes the command to create a group in the system

Parameters:
	Group - Group name
					
Returns:
	Integer -  Error code: 0 on success or other value on failure
	
=cut

sub runRBACCreateGroupCmd
{
	my $group    = shift;
	my $groupadd = &getGlobalConfiguration( "groupadd_bin" );

	# create group
	my $error = &logAndRun( "$groupadd $group" );

	# add it to rbac user
	require Zevenet::RBAC::User::Runtime;
	$error = &runRBACAddUserToGroup( 'rbac', $group ) if ( !$error );

	return $error;
}

=begin nd
Function: runRBACDeleteGroupCmd

	Delete a group from the system

Parameters:
	Group - Group name
					
Returns:
	Integer -  Error code: 0 on success or other value on failure
	
=cut

sub runRBACDeleteGroupCmd
{
	my $group    = shift;
	my $groupdel = &getGlobalConfiguration( "groupdel_bin" );

	# delete the group
	my $error = &logAndRun( "$groupdel $group" );

	return $error;
}

1;
