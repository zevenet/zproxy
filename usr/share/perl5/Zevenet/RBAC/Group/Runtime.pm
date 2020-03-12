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
include 'Zevenet::RBAC::Group::Core';

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $group    = shift;
	my $groupadd = &getGlobalConfiguration( "groupadd_bin" );

	# create group
	my $error = &logAndRun( "$groupadd $group" );

	# add it to rbac user
	include 'Zevenet::RBAC::User::Runtime';
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $group    = shift;
	my $groupdel = &getGlobalConfiguration( "groupdel_bin" );

	# delete the group
	my $error = &logAndRun( "$groupdel $group" );

	return $error;
}

1;

