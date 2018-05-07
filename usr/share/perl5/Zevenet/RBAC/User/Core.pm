#!/usr/bin/perl

use strict;
use Zevenet::Core;
include 'Zevenet::RBAC::Core';

my $rbacUserConfig = &getRBACUserConf();

=begin nd
Function: getRBACUserConf

	Return the path of the user configuration files

Parameters:
	None - .

Returns:
	String - path

=cut

sub getRBACUserConf
{
	my $rbacPath = &getRBACConfPath();
	return "$rbacPath/users.conf";
}

=begin nd
Function: getRBACUserList

	List all created users in the load balancer

Parameters:
	None - .

Returns:
	Array - List of users

=cut

sub getRBACUserList
{
	require Config::Tiny;
	my $fileHandle = Config::Tiny->read( $rbacUserConfig );

	return keys %{ $fileHandle };
}

=begin nd
Function: getRBACUserExists

	Check if a user exists in the load balancer

Parameters:
	User - User name

Returns:
	Integer - 1 if the user exists or 0 if it doesn't exist

=cut

sub getRBACUserExists
{
	my $user = shift;

	my $out = 0;
	$out = 1 if ( grep ( /^$user$/, &getRBACUserList() ) );

	return $out;
}

=begin nd
Function: getRBACUserObject

	get a object with all parameters of a user

Parameters:
	User - User name

Returns:
	Hash ref - Configuration of a user

=cut

sub getRBACUserObject
{
	my $user = shift;

	require Config::Tiny;
	my $fileHandle = Config::Tiny->read( $rbacUserConfig );

	return $fileHandle->{ $user };
}

=begin nd
Function: getRBACUserParam

	Get a configuration parameter of a user

Parameters:
	User - User name
	Parameter - Required parameter

Returns:
	Scalar - the data type depends of the required parameter

=cut

sub getRBACUserParam
{
	my $user   = shift;
	my $param  = shift;
	my $object = &getRBACUserObject( $user );
	return $object->{ $param };
}

=begin nd
Function: validateRBACUserZapi

	It validate if a user has zapi permissions and check if the zapikey is correct

Parameters:
	User - User name
	zapikey - Zapikey sent by the user. It is encrypt

Returns:
	Integer - 1 if the user has been validated sucessfully or 0 if it has not

=cut

sub validateRBACUserZapi
{
	my ( $zapikey ) = @_;

	include 'Zevenet::Code';

	my $user;

	# look for the user owned of zapikey
	require Config::Tiny;
	my $fileHandle = Config::Tiny->read( $rbacUserConfig );

	foreach my $key ( keys %{ $fileHandle } )
	{
		if ( &validateCryptString( $fileHandle->{ $key }->{ 'zapikey' }, $zapikey ) )
		{
			$user = $key;
			last;
		}
	}

	if ( !$user )
	{
		&zenlog( "RBAC, the zapikey does not match with any user" );
		return 0;
	}

	# check permissions
	my $groups      = &getGlobalConfiguration( 'groups_bin' );
	my $user_groups = `$groups $user`;
	chomp $user_groups;

	if ( !grep ( / zapi( |$)/, $user_groups ) )
	{
		&zenlog( "RBAC, the user $user has not zapi permissions" );
		return 0;
	}

	return $user;
}

1;
