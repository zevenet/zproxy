#!/usr/bin/perl

use strict;

use Zevenet::Core;
use Zevenet::RBAC::Group::Core;
use Zevenet::RBAC::Group::Runtime;

# rbac configuration paths
my $rbacGroupConfig = &getRBACGroupConf();

=begin nd
Function: updateRBACGroup

	Apply command lines to update a group with the configuration file

Parameters:
	Group - Group name
	Action - The available actions are: "add", create a group in the system; "delete", 
	delete a group from the system; "add_user", add a user to a group; or "del_user",
	delete a user from a group
	User - This parameter is used when Action parameter has the value of del_user or 
	add_user and its the user to add or delete from the group
					
Returns:
	None - .
	
=cut

sub updateRBACGroup
{
	my $group  = shift;
	my $action = shift;
	my $user   = shift;

	# DELETE
	if ( $action eq 'delete' )
	{
		&runRBACDeleteGroupCmd( $group );
	}

	# POST
	elsif ( $action eq 'add' )
	{
		&runRBACCreateGroupCmd( $group );
	}

	# Add users
	elsif ( $action eq 'add_user' )
	{
		require Zevenet::RBAC::User::Runtime;
		&runRBACAddUserToGroup( $user, $group );
	}

	# delete users
	elsif ( $action eq 'del_user' )
	{
		require Zevenet::RBAC::User::Runtime;
		&runRBACDelUserToGroup( $user, $group );
	}

	# check status and apply the necessary actions
	else
	{
		# check if it doesn't exist
		&runRBACCreateGroupCmd( $group )
		  if ( !grep ( /^$group$/, @{ &getRBACGroupsSys() } ) );

		# update the user list
		require Zevenet::RBAC::User::Runtime;
		my @sysUsers = &getRBACGroupMembers( $group );
		my @confUsers = @{ &getRBACGroupParam( $group, 'users' ) };

		foreach my $userAux ( @confUsers )
		{
			# Add the user
			if ( !grep ( /^$userAux$/, @sysUsers ) )
			{
				&runRBACAddUserToGroup( $userAux, $group );
			}
		}

		foreach my $userAux ( @sysUsers )
		{
			# Delete the user
			if ( !grep ( /^$userAux$/, @confUsers ) )
			{
				&runRBACDelUserToGroup( $userAux, $group );
			}
		}
	}
}

=begin nd
Function: updateRBACAllGroup

	Read the group config file and update in the system all group

Parameters:
	None - .
					
Returns:
	None - .
	
=cut

sub updateRBACAllGroup
{
	# delete the removed groups
	foreach my $group ( @{ &getRBACGroupsSys() } )
	{
		if ( !&getRBACGroupExists( $group ) )
		{
			&runRBACDeleteGroupCmd( $group );
		}
	}

	# update all groupss
	foreach my $group ( &getRBACGroupList() )
	{
		&updateRBACGroup( $group );
	}
}

1;

