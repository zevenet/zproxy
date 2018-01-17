#!/usr/bin/perl

use Zevenet::Core;
use strict;

=begin nd
Function: getRBACConfPath

	Return the path of rbac config files

Parameters:
	None - .
					
Returns:
	String - path
	
=cut

sub getRBACConfPath
{
	return &getGlobalConfiguration( 'configdir' ) . "/rbac";
}

=begin nd
Function: getRBACGroupMembers

	Get the list of members in a group

Parameters:
	Group - group name
					
Returns:
	Array - List of members

=cut

sub getRBACGroupMembers
{
	my $group = shift;

	my ( $name, $passwd, $gid, $members ) = getgrnam ( $group );
	my @members = split ' ', $members;

	return @members;
}

=begin nd
Function: getRBACUserIsMember

	Validate if a user is member of a group

Parameters:
	User - User name
	Group - Group name
					
Returns:
	Integer - Return 1 if the user is member of the group or 0 else it is not
	
=cut

sub getRBACUserIsMember
{
	my $user  = shift;
	my $group = shift;

	my $out = 0;
	$out = 1 if ( grep ( /^$user$/, &getRBACGroupMembers( $group ) ) );

	return $out;
}

=begin nd
Function: getRBACUserGroups

	Get a list with all groups where the user is incluied

Parameters:
	User - User name
					
Returns:
	Array - List of groups
	
=cut

sub getRBACUserGroups
{
	my $user = shift;
	my @groups_list;
	my $groups_bin = &getGlobalConfiguration( "groups_bin" );
	my $groups     = `$groups_bin $user`;
	chomp $groups;
	$groups =~ s/^$user : (:?nogroup) ?//;
	$groups =~ s/(^| )rbac($| )//;
	$groups =~ s/(^| )webgui($| )//;
	$groups =~ s/(^| )zapi($| )//;

	@groups_list = split ' ', $groups;
	return @groups_list;
}

1;
