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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $group  = shift;
	my $param  = shift;
	my $object = &getRBACGroupObject( $group );
	return $object->{ $param };
}

=begin nd
Function: getRBACUsersResources

	Get a list with all of resources that a user has in its group.
	If the resource has the value '*', it is expanded

Parameters:
	User - Group name
	Type - It is the type of resource to list

Returns:
	Array ref - list of elements

=cut

sub getRBACUsersResources
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $user = shift;
	my $type = shift;

	my $group    = &getRBACUserGroup( $user );
	my $list_ref = &getRBACGroupParam( $group, $type );
	my @list     = @{ $list_ref };

	# expand '*' if the resource is a farm or a virtual interface
	if ( $list[0] eq '*' )
	{
		if ( $type eq 'farms' )
		{
			@list = &getFarmNameList();
		}
		elsif ( $type eq 'interfaces' )
		{
			@list = &getVirtualInterfaceNameList();
		}
	}

	return \@list;
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	include 'Zevenet::RBAC::Group::Core';
	@out = @{ &getRBACUserSet( 'farms', \@out ) };

=cut

sub getRBACUserSet
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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

sub lockRBACGroupResource
{
	# Lock resource
	require Zevenet::Lock;
	&lockResource( &getGlobalConfiguration( "groups_bin" ), "l" );
}

sub unlockRBACGroupResource
{
	# unlock resource
	require Zevenet::Lock;
	&lockResource( &getGlobalConfiguration( "groups_bin" ), "ud" );
}

1;
