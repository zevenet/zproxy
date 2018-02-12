#!/usr/bin/perl

use Zevenet::Core;
use Zevenet::CGI;

use strict;

my $object_re = '[^\/]+';

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

=begin nd
Function: getRBACResourcePermissions

	Check if the request is for a farm or virtual interface. This function
	will check if it's a resource of the user

Parameters:
	URL path - Request URL. It was sent by the user in the HTTP request

Returns:
	Integer - 0 if the user has not permissions or 1 if he can continue with the request

=cut

sub getRBACResourcePermissions
{
	my $path = shift;

	require Zevenet::User;
	my $user       = &getUser();
	my $permission = 1;

	require Zevenet::RBAC::Group::Core;

	# check resources
	if ( $path =~ qr{^/(?:stats|graphs)?/?farms/modules} ) { }
	elsif ( $path =~ qr{^/(?:stats|graphs)?/?farms/($object_re)} )
	{
		my $farm = $1;

		if ( !grep ( /^$farm$/, @{ &getRBACUsersResources( $user, 'farms' ) } ) )
		{
			$permission = 0;

			#~ &zenlog( "The user $user cannot access to the farm $farm.", 'error' );
		}
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

	return $permission;
}

=begin nd
Function: getRBACRolePath

	Return the path of the role configuration files

Parameters:
	None - .

Returns:
	String - path

=cut

sub getRBACRolePath
{
	return &getRBACConfPath() . "/roles";
}

=begin nd
Function: getRBACRoleFile

	Return the absolute path of a role configuration file

Parameters:
	Role - Role name

Returns:
	String - path

=cut

sub getRBACRoleFile
{
	my $role = shift;
	return &getRBACRolePath() . "/$role.conf";
}

=begin nd
Function: getRBACRolePermission

	Check if a user's role has permissions for a request.
	If a path is not contempled in the role configuration file, by default it will be allowed
	If a user has not a group or role, the user will be blocked

Parameters:
	Role - Role name

Returns:
	Integerr - 0 if the user's role has not permissions for the path or 1 if it has

=cut

sub getRBACRolePermission
{
	my $section = shift;
	my $action  = shift;
	my $out     = 0;

	my $roleFile;
	my $fileHandle;

	my $user  = &getUser();
	my $group = &getRBACUserGroup( $user );
	my $role  = &getRBACGroupParam( $group, 'role' );
	my $fileHandle;

	if ( $role )
	{
		$out = 1;
		my $roleFile = &getRBACRoleFile( $role );
		require Config::Tiny;
		$fileHandle = Config::Tiny->read( $roleFile );

		$out = 0 if ( $fileHandle->{ $section }->{ $action } eq 'false' );
	}

	&zenlog( "RBAC:: $ENV{ REQUEST_METHOD } $ENV{ PATH_INFO } " ) if &debug;
	&zenlog(
		"RBAC:: Permissions: $out, user:$user, group:$group, role:$role \[$section\]\->\{$action\} = $fileHandle->{ $section }->{ $action } "
	) if &debug;

	return $out;
}

=begin nd
Function: getRBACPathPermissions

	Check if a user has permissions for a request.
	If a path is not contempled in the role configuration file, by default it will be allowed
	If a user has not a group or role, the user will be blocked

Parameters:
	Path - URL path of the HTTP request
	Method - HTTP method of the request

Returns:
	Integerr - 0 if the user's role has not permissions for the path or 1 if it has

=cut

sub getRBACPathPermissions
{
	my $path   = shift;
	my $method = shift;

	my $permission;
	my $section;
	my $action;

	# it is resource?
	$permission = &getRBACResourcePermissions( $path );

	&zenlog( "Checking resource ($permission) " ) if &debug > 1;

	return 0 if ( !$permission );

	# get action and section of config file
	( $section, $action ) = &getRBACPermissionHash( $path, $method );

	# get permission role
	$permission = &getRBACRolePermission( $section, $action );

	return $permission;
}

=begin nd
Function: getRBACPermissionHash

	It matches the method and path of the HTTP request with a parameter of the role.
	The parameter is defined in the role configuration file for a 'section' and 'action':
	$ref->{ $section }->{ $action }

Parameters:
	Path - URL path of the HTTP request
	Method - HTTP method of the request

Returns:
	Array - Array with 2 elements. The first is the configuration file section and second one is the action

=cut

sub getRBACPermissionHash
{
	my $path   = shift;
	my $method = shift;
	my $section;
	my $action;
	my $hashSection;

	# exceptions or advances checks
	if ( $path =~ qr{^/interfaces/($object_re)} and $method eq 'POST' )
	{
		if ( $1 ne 'virtual' )
		{
			my $data = &getCgiParam( 'POSTDATA' );
			require JSON::XS;
			my $json = eval { JSON::XS::decode_json( $data ) };

			$section = 'interface';
			if ( $path =~ qr{/actions$} and exists $json->{ action } )
			{
				$action = 'action';
			}
			else
			{
				$action = 'modify';
			}
		}
	}

	# ipds actions
	if ( $path =~ qr{^/ipds/(?:rbl|blacklist|dos)/($object_re)/actions$} )
	{
		$section = 'ipds';
		$action  = 'action';
	}

	if ( !$action or !$section )
	{
		$hashSection = &getRBACRoleMenu( $path );

		if ( exists $hashSection->{ $method } and $hashSection )
		{
			foreach my $ref ( @{ $hashSection->{ $method } } )
			{
				if ( $path =~ /$ref->{ regex }/ )
				{
					$action  = $ref->{ action };
					$section = $ref->{ section };
					last;
				}
			}
		}
	}

	return ( $section, $action );
}

=begin nd
Function: getRBACRoleMenu

	The checking of the path is splitted in several hashes, because it is big, then
	this function is a trigger to get the needed hash

Parameters:
	Path - URL path of the HTTP request

Returns:
	Hash ref - hash to get the role configuration file

=cut

sub getRBACRoleMenu
{
	my $path = shift;
	my $hash;

	if ( $path =~ /^\/farms/ )
	{
		$hash = &getRBACPermissionFarmHash( $path );
	}
	elsif ( $path =~ /^\/certificates\/activation/ )
	{
		$hash = &getRBACPermissionActivationCertificateHash( $path );
	}
	elsif ( $path =~ /^\/certificates/ )
	{
		$hash = &getRBACPermissionCertificateHash( $path );
	}
	elsif ( $path =~ /^\/interfaces\/virtual/ )
	{
		$hash = &getRBACPermissionIntefaceVirtualHash( $path );
	}
	elsif ( $path =~ /^\/interfaces/ )
	{
		$hash = &getRBACPermissionIntefaceHash( $path );
	}
	elsif ( $path =~ /^\/ipds/ )
	{
		$hash = &getRBACPermissionIpdsHash( $path );
	}
	elsif ( $path =~ /^\/system/ )
	{
		$hash = &getRBACPermissionSystemHash( $path );
	}
	elsif ( $path =~ /^\/rbac/ )
	{
		$hash = &getRBACPermissionRbacHash( $path );
	}

	return $hash;
}

# [farm]
#	create=false
#	delete=false
#	modify=false
#	action=false
#	maintenance=true

sub getRBACPermissionFarmHash
{
	my $zone_re         = &getValidFormat( 'zone' );
	my $resource_id_re  = &getValidFormat( 'resource_id' );
	my $farm_re         = &getValidFormat( 'farm_name' );
	my $service_re      = &getValidFormat( 'service' );
	my $be_re           = &getValidFormat( 'backend' );
	my $blacklists_list = &getValidFormat( 'blacklists_name' );
	my $rbl_name        = &getValidFormat( 'rbl_name' );
	my $dos_rule        = &getValidFormat( 'dos_name' );
	my $cert_pem_re     = &getValidFormat( 'cert_pem' );

	my $hash = {
		'PUT' => [
			{
			   'regex'   => qr{^/farms/($farm_re)/actions$},
			   'section' => 'farm',
			   'action'  => 'action',
			},
			{
			   'regex'   => qr{^/farms/($farm_re)/backends/($be_re)/maintenance$},
			   'section' => 'farm',
			   'action'  => 'maintenance',
			},
			{
			   'regex' =>
				 qr{^/farms/($farm_re)/services/($service_re)/backends/($be_re)/maintenance$},
			   'section' => 'farm',
			   'action'  => 'maintenance',
			},
			{
			   'regex'   => qr{^/farms/($farm_re)/zones/($zone_re)$},
			   'section' => 'farm',
			   'action'  => 'modify',
			},
			{
			   'regex' => qr{^/farms/($farm_re)/zones/($zone_re)/resources/($resource_id_re)$},
			   'section' => 'farm',
			   'action'  => 'modify',
			},
			{
			   'regex'   => qr{^/farms/($farm_re)/services/($service_re)$},
			   'section' => 'farm',
			   'action'  => 'modify',
			},
			{
			   'regex'   => qr{^/farms/($farm_re)/backends/($be_re)$},
			   'section' => 'farm',
			   'action'  => 'modify',
			},
			{
			   'regex'   => qr{^/farms/($farm_re)/fg$},
			   'section' => 'farm',
			   'action'  => 'modify',
			},
			{
			   'regex'   => qr{^/farms/($farm_re)$},
			   'section' => 'farm',
			   'action'  => 'modify',
			},
			{
			   'regex'   => qr{^/farms/($farm_re)/services/($service_re)/backends/($be_re)$},
			   'section' => 'farm',
			   'action'  => 'modify',
			},
		],
		'POST' => [
				   {
					  'regex'   => qr{^/farms/($farm_re)/zones/($zone_re)/resources$},
					  'section' => 'farm',
					  'action'  => 'modify',
				   },
				   {
					  'regex'   => qr{^/farms/($farm_re)/ipds/$},
					  'section' => 'farm',
					  'action'  => 'action',
				   },
				   {
					  'regex'   => qr{^/farms/($farm_re)/certificates$},
					  'section' => 'farm',
					  'action'  => 'modify',
				   },
				   {
					  'regex'   => qr{^/farms/($farm_re)/services$},
					  'section' => 'farm',
					  'action'  => 'modify',
				   },
				   {
					  'regex'   => qr{^/farms/($farm_re)/backends$},
					  'section' => 'farm',
					  'action'  => 'modify',
				   },
				   {
					  'regex'   => qr{^/farms/($farm_re)/services/($service_re)/backends$},
					  'section' => 'farm',
					  'action'  => 'modify',
				   },
				   {
					  'regex'   => qr{^/farms$},
					  'section' => 'farm',
					  'action'  => 'create',
				   },
				   {
					  'regex'   => qr{^/farms/($farm_re)/zones$},
					  'section' => 'farm',
					  'action'  => 'modify',
				   },
				   {
					  'regex'   => qr{^/farms/($farm_re)/services/($service_re)/actions$},
					  'section' => 'farm',
					  'action'  => 'modify',
				   },
		],
		'DELETE' => [
			{
			   'regex'   => qr{^/farms/($farm_re)/ipds/},
			   'section' => 'farm',
			   'action'  => 'action',
			},
			{
			   'regex'   => qr{^/farms/($farm_re)/certificates/($cert_pem_re)$},
			   'section' => 'farm',
			   'action'  => 'modify',
			},
			{
			   'regex'   => qr{^/farms/($farm_re)/services/($service_re)$},
			   'section' => 'farm',
			   'action'  => 'modify',
			},
			{
			   'regex'   => qr{^/farms/($farm_re)/backends/($be_re)$},
			   'section' => 'farm',
			   'action'  => 'modify',
			},
			{
			   'regex'   => qr{^/farms/($farm_re)/services/($service_re)/backends/($be_re)$},
			   'section' => 'farm',
			   'action'  => 'modify',
			},
			{
			   'regex'   => qr{^/farms/($farm_re)/zones/($zone_re)$},
			   'section' => 'farm',
			   'action'  => 'modify',
			},
			{
			   'regex' => qr{^/farms/($farm_re)/zones/($zone_re)/resources/($resource_id_re)$},
			   'section' => 'farm',
			   'action'  => 'modify',
			},
			{
			   'regex'   => qr{^/farms/($farm_re)$},
			   'section' => 'farm',
			   'action'  => 'delete',
			},
		],
		'GET' => [],
	};

	return $hash;
}

# [activation-certificate]
#	show=true
#	upload=false
#	delete=false

sub getRBACPermissionActivationCertificateHash
{
	my $hash = {
				 'GET' => [
						   {
							 'regex'   => qr{^/certificates/activation},
							 'section' => 'activation-certificate',
							 'action'  => 'show',
						   },
				 ],
				 'POST' => [
							{
							  'regex'   => qr{^/certificates/activation},
							  'section' => 'activation-certificate',
							  'action'  => 'upload',
							},
				 ],
				 'DELETE' => [
							  {
								'regex'   => qr{^/certificates/activation$},
								'section' => 'activation-certificate',
								'action'  => 'delete',
							  },
				 ],
				 'PUT' => [],
	};

	return $hash;
}

# [certificate]
#	show=false
#	create=false
#	download=false
#	upload=false
#	delete=false

sub getRBACPermissionCertificateHash
{
	my $cert_re     = &getValidFormat( 'certificate' );
	my $cert_pem_re = &getValidFormat( 'cert_pem' );

	my $hash = {
				 'GET' => [
						   {
							 'regex'   => qr{^/certificates/($cert_re)$},
							 'section' => 'certificate',
							 'action'  => 'download',
						   },
						   {
							 'regex'   => qr{^/certificates/($cert_re)/info$},
							 'section' => 'certificate',
							 'action'  => 'show',
						   },
				 ],
				 'POST' => [
							{
							  'regex'   => qr{^/certificates$},
							  'section' => 'certificate',
							  'action'  => 'create',
							},
							{
							  'regex'   => qr{^/certificates/($cert_pem_re)$},
							  'section' => 'certificate',
							  'action'  => 'upload',
							},
				 ],
				 'DELETE' => [
							  {
								'regex'   => qr{^/certificates/($cert_re)$},
								'section' => 'certificate',
								'action'  => 'delete',
							  },
				 ],
				 'PUT' => [],
	};

	return $hash;
}

# [interface-virtual]
#	POST qr{^/interfaces/virtual$}
#	POST qr{^/interfaces/virtual/($virtual_re)/actions$}
#	PUT qr{^/interfaces/virtual/($virtual_re)$}
#	DELETE qr{^/interfaces/virtual/($virtual_re)$}

sub getRBACPermissionIntefaceVirtualHash
{
	my $virtual_re = &getValidFormat( 'virt_interface' );

	my $hash = {
			   'POST' => [
						  {
							'regex'   => qr{^/interfaces/virtual$},
							'section' => 'interface-virtual',
							'action'  => 'create',
						  },
						  {
							'regex'   => qr{^/interfaces/virtual/($virtual_re)/actions$},
							'section' => 'interface-virtual',
							'action'  => 'action',
						  },
			   ],
			   'PUT' => [
						 {
						   'regex'   => qr{^/interfaces/virtual/($virtual_re)$},
						   'section' => 'interface-virtual',
						   'action'  => 'modify',
						 },
			   ],
			   'DELETE' => [
							{
							  'regex'   => qr{^/interfaces/virtual/($virtual_re)$},
							  'section' => 'interface-virtual',
							  'action'  => 'delete',
							},
			   ],
	};

	return $hash;
}

# [Interface]
#	modify=false
#	action=false

sub getRBACPermissionIntefaceHash
{
	my $hash = {
		 'PUT' => [
				   {
					 'regex'   => qr{^/interfaces/(?:nic|vlan|gateway|floating|bonding)},
					 'section' => 'interface',
					 'action'  => 'modify',
				   },
		 ],
		 'DELETE' => [
					  {
						'regex'   => qr{^/interfaces/(?:nic|vlan|gateway|floating|bonding)},
						'section' => 'interface',
						'action'  => 'modify',
					  },
		 ],
		 'POST' => [
					{
					  'regex'   => qr{^/interfaces/(?:nic|vlan|gateway|floating|bonding)},
					  'section' => 'interface',
					  'action'  => 'modify',
					},
		 ],
	};

	return $hash;
}

# [ipds]
# modify=false
# action=true

sub getRBACPermissionIpdsHash
{
	my $hash = {
				 'PUT' => [
						   {
							 'regex'   => qr{^/ipds},
							 'section' => 'ipds',
							 'action'  => 'modify',
						   },
				 ],
				 'DELETE' => [
							  {
								'regex'   => qr{^/ipds},
								'section' => 'ipds',
								'action'  => 'modify',
							  },
				 ],
				 'POST' => [
							{
							  'regex'   => qr{^/ipds},
							  'section' => 'ipds',
							  'action'  => 'modify',
							},
				 ],
	};

	return $hash;
}

#	[system-service]
#	modify=false
#
#	[log]
#	download=true
#	show=true
#
#	[backup]
#	create=true
#	apply=false
#	upload=false
#	download=false
#	delete=false
#
#	[cluster]
#	create=false
#	modify=false
#	delete=false
#	maintenance=false
#
#	[notification]
#	show=false
#	modify-method=false
#	modify=false
#	test=true
#	modify-alert=false
#	action=false
#
#	[system-user]
#	modify=false
#	show=false
#
#	[supportsave]
#	download=true

sub getRBACPermissionSystemHash
{
	my $hash = {
		'PUT' => [
				  {
					 'regex'   => qr{^/system/backup/$object_re$},
					 'section' => 'backup',
					 'action'  => 'upload',
				  },
				  {
					 'regex'   => qr{^/system/cluster$},
					 'section' => 'cluster',
					 'action'  => 'modify',
				  },
		],
		'DELETE' => [
					 {
						'regex'   => qr{^/system/backup/$object_re$},
						'section' => 'backup',
						'action'  => 'delete',
					 },
					 {
						'regex'   => qr{^/system/cluster$},
						'section' => 'cluster',
						'action'  => 'delete',
					 },
		],
		'POST' => [
				   {
					  'regex'   => qr{^/system/(?:ssh|dns|ntp|snmp)$},
					  'section' => 'system-service',
					  'action'  => 'modify',
				   },
				   {
					  'regex'   => qr{^/system/backup$},
					  'section' => 'backup',
					  'action'  => 'create',
				   },
				   {
					  'regex'   => qr{^/system/backup/$object_re/actions$},
					  'section' => 'backup',
					  'action'  => 'apply',
				   },
				   {
					  'regex'   => qr{^/system/cluster$},
					  'section' => 'cluster',
					  'action'  => 'create',
				   },
				   {
					  'regex'   => qr{^/system/cluster/actions$},
					  'section' => 'cluster',
					  'action'  => 'maintenance',
				   },
				   {
					  'regex'   => qr{^/system/notifications/email$},
					  'section' => 'notification',
					  'action'  => 'modify-method',
				   },
				   {
					  'regex'   => qr{^/system/notifications/email/actions$},
					  'section' => 'notification',
					  'action'  => 'test',
				   },
				   {
					  'regex'   => qr{^/system/notifications/alerts/$object_re$},
					  'section' => 'notification',
					  'action'  => 'modify-alert',
				   },
				   {
					  'regex'   => qr{^/system/notifications/alerts/$object_re/actions$},
					  'section' => 'notification',
					  'action'  => 'action',
				   },
				   {
					  'regex'   => qr{^/system/users/root$},
					  'section' => 'system-user',
					  'action'  => 'modify',
				   },
				   {
					  'regex'   => qr{^/system/users/zapi$},
					  'section' => 'system-user',
					  'action'  => 'modify',
				   },
		],
		'GET' => [
				  {
					 'regex'   => qr{^/system/logs/$object_re$},
					 'section' => 'log',
					 'action'  => 'download',
				  },
				  {
					 'regex'   => qr{^/system/logs/$object_re/lines/$object_re$},
					 'section' => 'log',
					 'action'  => 'show',
				  },
				  {
					 'regex'   => qr{^/system/backup/$object_re$},
					 'section' => 'backup',
					 'action'  => 'download',
				  },
				  {
					 'regex'   => qr{^/system/notifications/methods/email$},
					 'section' => 'notification',
					 'action'  => 'show',
				  },
				  {
					 'regex'   => qr{^/system/supportsve$},
					 'section' => 'supportsave',
					 'action'  => 'download',
				  },
				  {
					 'regex'   => qr{^/system/users/zapi$},
					 'section' => 'system-user',
					 'action'  => 'show',
				  },
		],

	};

	return $hash;
}

#	[rbac-user]
#	list=false
#	create=false
#	show=false
#	modify=false
#	delete=false
#
#	[rbac-group]
#	list=false
#	create=false
#	delete=false
#	show=false
#	modify=false
#
#	[rbac-role]
#	create=false
#	delete=false
#	show=false
#	modify=false

sub getRBACPermissionRbacHash
{
	my $hash = {
		'PUT' => [
				  {
					 'regex'   => qr{^/rbac/users/$object_re$},
					 'section' => 'rbac-user',
					 'action'  => 'modify',
				  },
				  {
					 'regex'   => qr{^/rbac/groups/$object_re$},
					 'section' => 'rbac-group',
					 'action'  => 'modify',
				  },
				  {
					 'regex'   => qr{^/rbac/roles/$object_re$},
					 'section' => 'rbac-role',
					 'action'  => 'modify',
				  },
		],
		'DELETE' => [
			{
			   'regex'   => qr{^/rbac/users/$object_re$},
			   'section' => 'rbac-user',
			   'action'  => 'delete',
			},
			{
			   'regex'   => qr{^/rbac/groups/$object_re$},
			   'section' => 'rbac-group',
			   'action'  => 'delete',
			},
			{
			   'regex'   => qr{^/rbac/groups/$object_re/(?:interfaces|farms|users)/$object_re$},
			   'section' => 'rbac-group',
			   'action'  => 'modify',
			},
			{
			   'regex'   => qr{^/rbac/roles/$object_re$},
			   'section' => 'rbac-role',
			   'action'  => 'delete',
			},
		],
		'POST' => [
				   {
					  'regex'   => qr{^/rbac/users$},
					  'section' => 'rbac-user',
					  'action'  => 'create',
				   },
				   {
					  'regex'   => qr{^/rbac/groups$},
					  'section' => 'rbac-group',
					  'action'  => 'create',
				   },
				   {
					  'regex'   => qr{^/rbac/groups/$object_re/(?:interfaces|farms|users)},
					  'section' => 'rbac-group',
					  'action'  => 'modify',
				   },
				   {
					  'regex'   => qr{^/rbac/roles$},
					  'section' => 'rbac-role',
					  'action'  => 'create',
				   },
		],
		'GET' => [
				  {
					 'regex'   => qr{^/rbac/users$},
					 'section' => 'rbac-user',
					 'action'  => 'list',
				  },
				  {
					 'regex'   => qr{^/rbac/users/$object_re$},
					 'section' => 'rbac-user',
					 'action'  => 'show',
				  },
				  {
					 'regex'   => qr{^/rbac/groups$},
					 'section' => 'rbac-group',
					 'action'  => 'list',
				  },
				  {
					 'regex'   => qr{^/rbac/groups/$object_re$},
					 'section' => 'rbac-group',
					 'action'  => 'show',
				  },
				  {
					 'regex'   => qr{^/rbac/roles/$object_re$},
					 'section' => 'rbac-role',
					 'action'  => 'show',
				  },
		],
	};

	return $hash;
}

1;
