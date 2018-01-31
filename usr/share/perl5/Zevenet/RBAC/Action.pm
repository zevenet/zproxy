#!/usr/bin/perl

use strict;

use Zevenet::Core;
require Zevenet::RBAC::User::Action;
require Zevenet::RBAC::Group::Action;
require Zevenet::RBAC::Group::Core;
require Zevenet::RBAC::Core;

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
	my $touch           = &getGlobalConfiguration( "touch" );
	my $groupadd        = &getGlobalConfiguration( "groupadd_bin" );
	my $rbacPath        = &getRBACConfPath();
	my $rbacUserConfig  = &getRBACUserConf();
	my $rbacGroupConfig = &getRBACGroupConf();
	mkdir $rbacPath                         if ( !-d $rbacPath );
	&logAndRun( "$touch $rbacUserConfig" )  if ( !-f $rbacUserConfig );
	&logAndRun( "$touch $rbacGroupConfig" ) if ( !-f $rbacGroupConfig );
	&runRBACCreateGroupCmd( "zapi" )        if ( !getgrnam ( 'zapi' ) );
	&runRBACCreateGroupCmd( "rbac" )        if ( !getgrnam ( 'rbac' ) );

	# create  rbac user
	my $adduser = &getGlobalConfiguration( "adduser_bin" );
	&logAndRun( "$adduser --system --shell /bin/false --no-create-home rbac" )
	  if ( !getpwnam ( 'rbac' ) );

	&updateRBACAllUser();
	&updateRBACAllGroup();
}

1;
