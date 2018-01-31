#!/usr/bin/perl

use Zevenet::Core;
use Zevenet::CGI;

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

	my ( undef, undef, undef, $members ) = getgrnam ( $group );

	#~ $members = s/(^| )rbac( |$)/ /;
	my @members = split ( ' ', $members );

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
Function: getRBACUserGroup

	Get the group where the user is incluied

Parameters:
	User - User name
					
Returns:
	String - Group of the user
	
=cut

sub getRBACUserGroup
{
	my $user = shift;
	my @groups_list;
	my $groups_bin = &getGlobalConfiguration( "groups_bin" );
	my $groups     = `$groups_bin $user`;
	chomp $groups;
	$groups =~ s/^$user : (:?nogroup) ?/ /;
	$groups =~ s/(^| )rbac($| )/ /;
	$groups =~ s/(^| )webgui($| )/ /;
	$groups =~ s/(^| )zapi($| )/ /;

	@groups_list = split ' ', $groups;

	#~ return @groups_list;

	# In the first version, the user only will have one group
	return $groups_list[0] // '';
}

sub getRBACPath
{
	my $path = shift;

	#~ my $method = shift;

	require Zevenet::User;
	my $user       = &getUser();
	my $permission = 1;

	require Zevenet::RBAC::Group::Core;

	# check resources
	my $object_re = '[^/]+';
	if ( $path =~ qr{^/(?:stats|graphs)?/?farms/modules} ) { }
	elsif ( $path =~ qr{^/(?:stats|graphs)?/?farms/($object_re)} )
	{
		my $farm = $1;

		if ( !grep ( /^$farm$/, @{ &getRBACUsersResources( $user, 'farms' ) } ) )
		{
			$permission = 0;

			#~ &zenlog( "The user $user cannot access to the farm $farm.", 'error' );
		}

		# include permission checks foreach method
		# ...
	}
	elsif ( $path =~ qr{^/(?:graphs/)?interfaces/virtual/($object_re)} )
	{
		my $iface = $1;
		if ( !grep ( /^$iface$/, @{ &getRBACUsersResources( $user, 'interfaces' ) } ) )
		{
			$permission = 0;

			#~ &zenlog( "The user $user cannot access to the interface $iface.", 'error' );
		}
	}

#~ elsif ( $path =~ qr{^/(?:graphs/)?interfaces/(?:vlan|nic|bonding)?/?($object_re)} )
#~ {
#~ my $iface = $1;
#~ if ( ! grep( /^$iface$/, @{ &getRBACUsersResources( $user, 'interfaces' ) } ) )
#~ {
#~ $permission = 0;
#~ &zenlog( "The user $user cannot access to the interface $iface.", 'error' );
#~ }
#~ }

	return $permission;
}

1;
