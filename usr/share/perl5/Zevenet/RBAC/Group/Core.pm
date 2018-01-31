#!/usr/bin/perl

use strict;
use Zevenet::Core;
use Zevenet::RBAC::Core;

my $rbacGroupConfig = &getRBACGroupConf();

=begin nd
Function: getRBACGroupConf

	Return the path of the group configuration files

Parameters:
	None - .
					
Returns:
	String - path
	
=cut

sub getRBACGroupConf
{
	my $rbacPath = &getRBACConfPath();
	return "$rbacPath/groups.conf";
}

=begin nd
Function: getRBACGroupList

	List all created groups in the load balancer

Parameters:
	None - .
					
Returns:
	Array - List of groups
	
=cut

sub getRBACGroupList
{
	require Config::Tiny;
	my $fileHandle = Config::Tiny->read( $rbacGroupConfig );

	return keys %{ $fileHandle };
}

=begin nd
Function: getRBACGroupExists

	Check if a group exists in the load balancer

Parameters:
	Group - Group name
					
Returns:
	Integer - 1 if the group exists or 0 if it doesn't exist
	
=cut

sub getRBACGroupExists
{
	my $group = shift;

	my $out = 0;
	$out = 1 if ( grep ( /^$group$/, &getRBACGroupList() ) );

	return $out;
}

=begin nd
Function: getRBACGroupObject

	get a object with all parameters of a group

Parameters:
	Group - Group name
					
Returns:
	Hash ref - Configuration of a group
	
=cut

sub getRBACGroupObject
{
	my $group = shift;

	require Config::Tiny;
	my $fileHandle = Config::Tiny->read( $rbacGroupConfig );
	my $out        = $fileHandle->{ $group };

	my @users      = ();
	my @interfaces = ();
	my @farms      = ();

	@users = sort split ( ' ', $fileHandle->{ $group }->{ 'users' } )
	  if ( $fileHandle->{ $group }->{ 'users' } );
	@farms = sort split ( ' ', $fileHandle->{ $group }->{ 'farms' } )
	  if ( $fileHandle->{ $group }->{ 'farms' } );
	@interfaces = sort split ( ' ', $fileHandle->{ $group }->{ 'interfaces' } )
	  if ( $fileHandle->{ $group }->{ 'interfaces' } );

	$out->{ 'users' }      = \@users;
	$out->{ 'farms' }      = \@farms;
	$out->{ 'interfaces' } = \@interfaces;

	return $out;
}

=begin nd
Function: getRBACGroupParam

	Get a configuration parameter of a group

Parameters:
	Group - Group name
	Parameter - Required parameter
					
Returns:
	Scalar - the data type depends of the required parameter
	
=cut

sub getRBACGroupParam
{
	my $group  = shift;
	my $param  = shift;
	my $object = &getRBACGroupObject( $group );
	return $object->{ $param };
}

=begin nd
Function: getRBACUsersResources

	Get a list with all of resources that a user has in its group

Parameters:
	User - Group name
	Type - It is the type of resource to list
					
Returns:
	Array ref - list of elements
	
=cut

sub getRBACUsersResources
{
	my $user = shift;
	my $type = shift;

	my $group = &getRBACUserGroup( $user );

	return &getRBACGroupParam( $group, $type );
}

=begin nd
Function: getRBACGroupsSys

	Get from system, all groups were created by rbac module

Parameters:
	None - .

Returns:
	Array ref - list of group names

=cut

sub getRBACGroupsSys
{
	my $groups_bin = &getGlobalConfiguration( "groups_bin" );
	my $users      = `$groups_bin rbac`;
	chomp $users;
	$users =~ s/^rbac : (:?nogroup) ?//;

	my @users_arr = split ( ' ', $users );

	return \@users_arr;
}

=begin nd
Function: getRBACUserSet

	Select from a list a set with the resources that a user has in its group

Parameters:
	User - User name
	Type - It is the type of resource to list. The availabe values are: "farms", "interfaces"
	List - It is an array reference to a list with all elements of a type

Returns:
	Array ref - list of elements that are user's resources

Example:
	if ( eval{ require Zevenet::RBAC::Group::Core; } )
	{
		@out = @{ &getRBACUserSet( 'farms', \@out ) };
	}

=cut

sub getRBACUserSet
{
	my $type    = shift;
	my $rawSet  = shift;
	my @userSet = ();

	require Zevenet::User;
	my $user = &getUser();

	return $rawSet if ( $user eq 'root' );

	my @userResources = @{ &getRBACUsersResources( $user, $type ) };
	my $key;

	$key = 'farmname' if ( $type eq 'farms' );
	$key = 'name'     if ( $type eq 'interfaces' );

	foreach my $item ( @{ $rawSet } )
	{
		my $name = $item->{ $key };

		if ( grep ( /^$name$/, @userResources ) )
		{
			push @userSet, $item;
		}
	}

	return \@userSet;
}

=begin nd
Function: getRBACResourcesFromList

	Remove from an array all elements are not from the user's group

Parameters:
	Type - It is the type of resource. The availabe values are: "farms", "interfaces"
	List - It is an array reference to a list with all elements of a type

Returns:
	Array ref - list of elements that are user's resources

Example:
	@farms = @{ &getRBACResourcesFromList( 'farms', \@farms ) };

=cut

sub getRBACResourcesFromList
{
	my $type    = shift;
	my $rawSet  = shift;
	my @userSet = ();

	require Zevenet::User;
	my $user = &getUser();

	return $rawSet if ( $user eq 'root' );

	my @userResources = @{ &getRBACUsersResources( $user, $type ) };
	my $key;

	$key = 'farmname' if ( $type eq 'farms' );
	$key = 'name'     if ( $type eq 'interfaces' );

	foreach my $item ( @{ $rawSet } )
	{
		if ( grep ( /^$item$/, @userResources ) )
		{
			push @userSet, $item;
		}
	}

	return \@userSet;

}

1;
