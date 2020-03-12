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
use Config::Tiny;
include 'Zevenet::RBAC::Group::Core';
include 'Zevenet::RBAC::Group::Runtime';

# rbac configuration paths
my $rbacGroupConfig = &getRBACGroupConf();

=begin nd
Function: setRBACGroupLockConfigFile

	Lock the group configuration file for nobody writes in it

Parameters:
	None - .

Returns:
	Integer - 0 on failure or other value on success

=cut

sub setRBACGroupLockConfigFile
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Lock;

	my $lockfile = "/tmp/rbac_groups.lock";
	return &openlock( $lockfile, 'w' );
}

=begin nd
Function: setRBACGroupConfigFile

	Save a change in a config file.
	This function has 2 behaviors:
	it can receives a hash ref to save a struct
	or it can receive a key and parameter to replace a value

Parameters:
	Group - Group to apply the change
	key - parameter to change or struct ref
	value - new value for the parameter
	action - This is a optional parameter. The possible values are: "add" to add
	a item to a list, or "del" to delete a item from a list

Returns:
	None - .

=cut

sub setRBACGroupConfigFile
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $group, $key, $value, $action ) = @_;

	# the group root mustn't exist
	return 0 if $group eq 'root';

	my $lock       = &setRBACGroupLockConfigFile();
	my $fileHandle = Config::Tiny->read( $rbacGroupConfig );

	# save all struct
	if ( ref $key )
	{
		foreach my $param ( keys %{ $key } )
		{
			$key->{ $param } = join ( ' ', @{ $param } ) if ( ref $param );
		}
		$fileHandle->{ $group } = $key;
	}

	# save a parameter
	else
	{
		if ( 'add' eq $action )
		{
			$fileHandle->{ $group }->{ $key } .= " $value";
		}
		elsif ( 'del' eq $action )
		{
			$fileHandle->{ $group }->{ $key } =~ s/(^| )$value( |$)/ /;
		}
		else
		{
			$fileHandle->{ $group }->{ $key } = $value;
		}
	}
	$fileHandle->write( $rbacGroupConfig );
	close $lock;
}

=begin nd
Function: createRBACGroup

	Add a group to the RBAC module

Parameters:
	Group - Group name

Returns:
	Integer -  Error code: 0 on success or other value on failure

=cut

sub createRBACGroup
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $group = shift;
	my $group_obj;

	# execute cmd
	my $error = &runRBACCreateGroupCmd( $group );

	# write in config file
	if ( !$error )
	{
		# save it
		$group_obj->{ 'interfaces' } = '';
		$group_obj->{ 'farms' }      = '';
		$group_obj->{ 'users' }      = '';
		$group_obj->{ 'role' }       = '';

		&setRBACGroupConfigFile( $group, $group_obj );
	}

	return $error;
}

=begin nd
Function: delRBACGroup

	It deletes a RBAC group

Parameters:
	Group - Group name

Returns:
	Integer -  Error code: 0 on success or other value on failure

=cut

sub delRBACGroup
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $group = shift;

	# remove from system
	my $error = &runRBACDeleteGroupCmd( $group );

	# remove from config file
	if ( !$error )
	{
		my $lock       = &setRBACGroupLockConfigFile();
		my $fileHandle = Config::Tiny->read( $rbacGroupConfig );
		delete $fileHandle->{ $group };
		$fileHandle->write( $rbacGroupConfig );
		close $lock;
	}

	return $error;
}

=begin nd
Function: addRBACGroupResource

	It adds a resource to a RBAC group

Parameters:
	Group - Group name
	Resource value - It can be a farm name, virtual interface name...
	Resource type - Resource type. It indicates the type of resource: "user", "farm" or "interface"

Returns:
	Integer -  Error code: 0 on success or other value on failure

=cut

sub addRBACGroupResource
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $group    = shift;
	my $resource = shift;
	my $type     = shift;
	my $error;

	# Add it to system
	if ( $type eq 'users' )
	{
		include 'Zevenet::RBAC::User::Runtime';
		$error = &runRBACAddUserToGroup( $resource, $group );
	}

	# Edit it in the config file
	if ( !$error )
	{
		# remove the all resources and add the global parameter '*'
		if ( $type =~ /^(?:farm|interface)s?$/ and $resource eq '*' )
		{
			&setRBACGroupConfigFile( $group, $type, $resource );
		}
		else
		{
			&setRBACGroupConfigFile( $group, $type, $resource, 'add' );
		}
	}

	return $error;
}

=begin nd
Function: delRBACGroupResource

	It deletes a resource from a RBAC group

Parameters:
	Group - Group name
	Name - Resource name. It can be a farm name, virtual interface name...
	Resource - Resource type. It indicates the type of resource: "users", "farms" or "interfaces"

Returns:
	Integer -  Error code: 0 on success or other value on failure

=cut

sub delRBACGroupResource
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $group    = shift;
	my $resource = shift;
	my $type     = shift;
	my $error;

	# Add it to system
	if ( $type eq "users" )
	{
		include 'Zevenet::RBAC::User::Runtime';
		$error = &runRBACDelUserToGroup( $resource, $group );
	}

	# Edit it in the config file
	if ( !$error )
	{
		# remove the all resources and add the global parameter '*'
		if ( $type =~ /^(?:farm|interface)s?$/ and $resource eq '*' )
		{
			&setRBACGroupConfigFile( $group, $type, '' );
		}
		else
		{
			&setRBACGroupConfigFile( $group, $type, $resource, 'del' );
		}
	}

	return $error;
}

=begin nd
Function: addRBACUserResource

	Add a resource user's group that has executed the zapi call

Parameters:
	Name - Resource name. It can be a farm name, virtual interface name...
	Resource - Resource type. It indicates the type of resource: "user", "farm" or "interface"

Returns:
	Integer -  Error code: 0 on success or other value on failure

=cut

sub addRBACUserResource
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $resource = shift;
	my $type     = shift;

	my $error;

	require Zevenet::User;
	my $user = &getUser();

	if ( $user ne 'root' )
	{
		my $group = &getRBACUserGroup( $user );
		return 1 if ( !$group );
		$error = &addRBACGroupResource( $group, $resource, $type );
	}

	return $error;
}

=begin nd
Function: delRBACResource

	Delete a resource from all groups where it appears

Parameters:
	Resource - Resource name
	Type - Type of resource to delete

Returns:
	None - .

=cut

sub delRBACResource
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $resource = shift;
	my $type     = shift;

	foreach my $group ( &getRBACGroupList() )
	{
		if ( grep ( /^$resource$/, @{ &getRBACGroupParam( $group, $type ) } ) )
		{
			&delRBACGroupResource( $group, $resource, $type );
		}
	}
}

=begin nd
Function: setRBACRenameByFarm

	Rename a farm in all groups where it appears

Parameters:
	Name - Current farm name
	New name - New farm name

Returns:
	None - .

=cut

sub setRBACRenameByFarm
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $old_farmname = shift;
	my $new_farmname = shift;

	foreach my $group ( &getRBACGroupList() )
	{
		if ( grep ( /^$old_farmname$/, @{ &getRBACGroupParam( $group, 'farms' ) } ) )
		{
			&delRBACGroupResource( $group, $old_farmname, 'farms' );
			&addRBACGroupResource( $group, $new_farmname, 'farms' );
		}
	}

}

1;

