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

use File::Copy "cp";
use Zevenet::Core;
include 'Zevenet::RBAC::User::Action';
include 'Zevenet::RBAC::Group::Action';
include 'Zevenet::RBAC::Group::Core';
include 'Zevenet::RBAC::Core';

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $touch            = &getGlobalConfiguration( "touch" );
	my $groupadd         = &getGlobalConfiguration( "groupadd_bin" );
	my $rbacRolesTpl_dir = &getGlobalConfiguration( 'rbacRolesTpl_dir' );
	my $rbacPath         = &getRBACConfPath();
	my $rbacRolePath     = &getRBACRolePath();
	my $rbacUserConfig   = &getRBACUserConf();
	my $rbacGroupConfig  = &getRBACGroupConf();
	mkdir $rbacPath                         if ( !-d $rbacPath );
	mkdir $rbacRolePath                     if ( !-d $rbacRolePath );
	&logAndRun( "$touch $rbacUserConfig" )  if ( !-f $rbacUserConfig );
	&logAndRun( "$touch $rbacGroupConfig" ) if ( !-f $rbacGroupConfig );

	# update roles templates
	opendir ( my $dir, $rbacRolesTpl_dir );
	foreach my $file ( readdir $dir )
	{
		next if ( $file =~ /^\./ );
		if ( !-f "$rbacRolePath/$file" )
		{
			cp( "$rbacRolesTpl_dir/$file", "$rbacRolePath/$file" )
			  or
			  &zenlog( "The role template $file could not be imported", "error", "rbac" );
		}
	}
	closedir $dir;

	# create  rbac user
	my $adduser = &getGlobalConfiguration( "adduser_bin" );
	&logAndRun( "$adduser --system --shell /bin/false --no-create-home rbac" )
	  if ( !getpwnam ( 'rbac' ) );

	# create group
	&logAndRun( "$groupadd rbac" ) if ( !getgrnam ( 'rbac' ) );
	&logAndRun( "$groupadd zapi" ) if ( !getgrnam ( 'zapi' ) );

	&updateRBACAllUser();
	&updateRBACAllGroup();

	# create services
	&setRBACServiceEnabled( 'local', 'true' );
	&setRBACServiceEnabled( 'ldap',  'false' );

}

1;
