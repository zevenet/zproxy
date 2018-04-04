#!/usr/bin/perl

use strict;
use Zevenet::Core;
use Zevenet::RBAC::Core;

=begin nd
Function: getRBACRolesList

	List all RBAC roles 

Parameters:
	None - .
					
Returns:
	Array - List with the role names
	
=cut

sub getRBACRolesList
{
	my $dir = &getRBACRolePath();
	opendir ( DIR, $dir );
	my @roles = grep ( s/.conf$//, readdir ( DIR ) );
	closedir ( DIR );

	return @roles;
}

=begin nd
Function: getRBACRoleExists

	Check if a role profile exists

Parameters:
	Role - Role name
					
Returns:
	Integer - Return 1 if the role exists or 0 if it doesn't exist
	
=cut

sub getRBACRoleExists
{
	my $role = shift;
	my $out  = 0;
	$out = 1 if ( grep /^$role$/, &getRBACRolesList() );
	return $out;
}

=begin nd
Function: getRBACRoleParamDefaultStruct

	This function defines a hash with all role configuration parameters

Parameters:
	None - .
					
Returns:
	Hash ref - Hash with a default role configuration
	
=cut

#~ return $paramStruct;
#~ }
sub getRBACRoleParamDefaultStruct
{
	my $struct;

	# list of functions with hashes permissions
	my @functions =
	  qw(getRBACPermissionFgHash getRBACPermissionRbacHash getRBACPermissionSystemHash getRBACPermissionAliasHash getRBACPermissionIpdsHash getRBACPermissionIntefaceHash getRBACPermissionIntefaceVirtualHash getRBACPermissionCertificateHash getRBACPermissionActivationCertificateHash getRBACPermissionFarmHash);

	foreach my $funct ( @functions )
	{
		# this step is important for strict
		my $funct_ref = \&$funct;
		my $perm      = &$funct_ref();

		foreach my $method ( qw(PUT POST GET DELETE) )
		{
			foreach my $it ( @{ $perm->{ $method } } )
			{
				my $action  = $it->{ action };
				my $section = $it->{ section };

				$struct->{ $section }->{ $action } = 'false';
			}
		}
	}

	return $struct;
}

=begin nd
Function: createRBACRole

	Create a configuration file for a role

Parameters:
	Role - Role name
					
Returns:
	Integer - 0 on sucess or other value on failure
	
=cut

sub createRBACRole
{
	my $role = shift;

	my $conf     = &getRBACRoleParamDefaultStruct();
	my $fileName = &getRBACRoleFile( $role );
	my $touch    = &getGlobalConfiguration( 'touch' );

	my $error = &logAndRun( "$touch $fileName" );
	if ( !$error )
	{
		require Config::Tiny;
		my $fileHandle = Config::Tiny->read( $fileName );
		foreach my $key ( keys %{ $conf } )
		{
			$fileHandle->{ $key } = $conf->{ $key };
		}
		$fileHandle->write( $fileName );
	}

	return $error;
}

=begin nd
Function: delRBACRole

	Delete a role configuration file

Parameters:
	Role - Role name
					
Returns:
	None - .
	
=cut

sub delRBACRole
{
	my $role = shift;
	my $file = &getRBACRoleFile( $role );
	unlink $file;
}

=begin nd
Function: setRBACRoleConfigFile

	Save the changes in a config file.
	it can receives a hash ref with the parameter that has changed

Parameters:
	Role - Role to update
	key - it is a hash with same struct than configuration file. It has the parameters to change
					
Returns:
	None - .

=cut

sub setRBACRoleConfigFile
{
	my ( $role, $obj ) = @_;

	require Zevenet::Lock;
	require Config::Tiny;

	my $rbacRoleFileConfig = &getRBACRoleFile( $role );
	my $lockfile           = "/tmp/rbac_role_$role.lock";
	my $lh                 = &lockfile( $lockfile );
	my $fileHandle         = Config::Tiny->read( $rbacRoleFileConfig );

	# save all struct
	if ( ref $obj )
	{
		foreach my $key ( keys %{ $obj } )
		{
			foreach my $param ( keys %{ $obj->{ $key } } )
			{
				$fileHandle->{ $key }->{ $param } = $obj->{ $key }->{ $param };
			}
		}
	}
	$fileHandle->write( $rbacRoleFileConfig );
	&unlockfile( $lh );
}

1;
