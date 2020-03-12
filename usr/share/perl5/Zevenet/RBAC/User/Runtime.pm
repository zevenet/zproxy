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

# rbac configuration paths
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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

	Delete a user from the system

Parameters:
	User - User name

Returns:
	Integer -  Error code: 0 on success or other value on failure

=cut

sub runRBACDeleteUserCmd
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $user, $group ) = @_;
	my $deluser = &getGlobalConfiguration( "deluser_bin" );
	my $cmd     = "$deluser $user $group";
	return &logAndRun( $cmd );
}

1;

