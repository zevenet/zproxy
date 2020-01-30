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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	return &getGlobalConfiguration( 'configdir' ) . "/rbac";
}

=begin nd
Function: getRBACServicesConfPath

	It returns the path of rbac services config file

Parameters:
	None - .

Returns:
	String - path

=cut

sub getRBACServicesConfPath
{
	return &getRBACConfPath() . "/services.conf";
}

=begin nd
Function: getRBACLocalEnabled

	It gets the status of the authentication using the system users.

Parameters:
	None - .

Returns:
	String - 'true' if the users are being authentication using the system or 'false' if they aren't

=cut

sub getRBACLocalEnabled
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	return ( &getRBACServiceEnabled( "local" ) );
}

=begin nd
Function: getRBACServices

	It gets the authentication services.

Parameters:
	None - 

Returns:
	Array - List of Services

=cut

sub getRBACServices
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my @services = ( 'local', 'ldap' );

	return @services;
}

=begin nd
Function: getRBACServiceDefault

	It gets the authentication service default value.

Parameters:
	String - Authentication service

Returns:
	String - Default value

=cut

sub getRBACServiceDefault
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $service = shift;

	my %services = (
					 'local' => 'true',
					 'ldap'  => 'false',
	);

	return $services{ $service };
}

=begin nd
Function: getRBACServiceEnabled

	It gets the status of the authentication service.

Parameters:
	Service - Authentication Service.

Returns:
	String - 'true' if the users can be authenticated by the service or 'false' if they aren't

=cut

sub getRBACServiceEnabled
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $srv      = shift;
	my $srv_file = &getRBACServicesConfPath();
	my $services = &getTiny( $srv_file );
	my $service  = $services->{ $srv };

	my $output = 'false';
	if ( exists $service->{ enabled } )
	{
		$output = $service->{ enabled };
	}
	return $output;
}

=begin nd
Function: setRBACLocalEnabled

	It modify the status for authenticate users using the system.
	To enable or disable the status is written in a configuration file that is checked
	before than authentica the user

Parameters:
	Status - Status to set.

Returns:
	Integer - Error code: 0 on success or another value on failure

=cut

sub setRBACLocalEnabled
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $enabled = shift;

	die "Error in parameters for the function setRBACLocalEnabled"
	  if $enabled !~ /^true|false$/;

	return ( &setRBACServiceEnabled( 'local', $enabled ) );
}

=begin nd
Function: setRBACServiceEnabled

	It modify the status for authenticating service.
	To enable or disable the status is written in a configuration file that is checked
	before than authenticate the user

Parameters:
	Service - Authentication Service.
	Status - Status to set.

Returns:
	Integer - Error code: 0 on success or another value on failure

=cut

sub setRBACServiceEnabled
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $srv     = shift;
	my $enabled = shift;

	die "Error in parameters for the function setRBACServiceEnabled"
	  if $enabled !~ /^true|false$/;

	my $srv_file = &getRBACServicesConfPath();
	my $err = &setTinyObj( $srv_file, $srv, 'enabled', $enabled );
	return $err;
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $group = shift;

	my ( undef, undef, undef, $members ) = getgrnam ( $group );

	#~ $members = s/(^| )rbac( |$)/ /;
	my @members = split ( ' ', $members );

	return @members;
}

=begin nd
Function: getRBACUserAuthservice

	Get the Authentication Service used by the user

Parameters:
	User - User name

Returns:
	String - Authentication Service

=cut

sub getRBACUserAuthservice
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $user = shift;
	include 'Zevenet::RBAC::User::Core';

	return &getRBACUserParam( $user, 'service' );

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $user  = shift;
	my $group = shift;

	my $out = 0;
	$out = 1 if ( grep ( /^$user$/, &getRBACGroupMembers( $group ) ) );

	return $out;
}

=begin nd
Function: getRBACUserGroup

	Get the group where the user is included

Parameters:
	User - User name

Returns:
	String - Group of the user

=cut

sub getRBACUserGroup
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	String - returns a blank string if the user has permissions, or a error message if it has not

=cut

sub getRBACResourcePermissions
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $path = shift;

	require Zevenet::User;
	my $user     = &getUser();
	my $rbac_msg = "";

	include 'Zevenet::RBAC::Group::Core';

	# check resources
	if ( $path =~ qr{^/(?:stats|graphs)?/?farms/modules} ) { }
	elsif ( $path =~ qr{^/(?:stats|graphs)?/?farms/($object_re)} )
	{
		my $farm = $1;
		require Zevenet::Farm::Core;

		# check if it exists to control the HTTP output code
		if ( &getFarmExists( $farm ) )
		{
			if ( !grep ( /^$farm$/, @{ &getRBACUsersResources( $user, 'farms' ) } ) )
			{
				$rbac_msg = "The farm $farm is not accessible by the user $user";
			}
		}
	}
	elsif ( $path =~ qr{^/(?:graphs/)?interfaces/virtual/($object_re)} )
	{
		my $iface = $1;
		require Zevenet::Net::Interface;

		if ( &getInterfaceConfig( $iface ) )
		{
			if ( !grep ( /^$iface$/, @{ &getRBACUsersResources( $user, 'interfaces' ) } ) )
			{
				$rbac_msg = "The interface $iface is not accessible by the user $user";
			}
		}
	}

	return $rbac_msg;
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $section = shift;
	my $action  = shift;

	my $out = 0;

	my $roleFile;
	my $fileHandle;
	require Zevenet::User;
	my $user = &getUser();
	if ( $user eq 'root' ) { return 1 }

	my $group = &getRBACUserGroup( $user );

	&zenlog( "The user $user has not a group", "debug", "RBAC" ) if not $group;

	include 'Zevenet::RBAC::Group::Core';
	my $role = &getRBACGroupParam( $group, 'role' );
	&zenlog( "The user $user has not a role", "debug", "RBAC" )
	  if ( not $role and $group );

	if ( $role )
	{
		$out = 1;
		my $roleFile = &getRBACRoleFile( $role );
		require Config::Tiny;
		$fileHandle = Config::Tiny->read( $roleFile );

		$out = 0
		  if (    !exists ( $fileHandle->{ $section }->{ $action } )
			   || !defined ( $fileHandle->{ $section }->{ $action } )
			   || $fileHandle->{ $section }->{ $action } ne 'true' );
	}

	&zenlog( "$ENV{ REQUEST_METHOD } $ENV{ PATH_INFO }", "debug", "RBAC" );
	&zenlog(
		"Permissions: $out, user:$user, group:$group, role:$role \[$section\]\->\{$action\} = $fileHandle->{ $section }->{ $action }",
		"debug", "RBAC"
	);

	return $out;
}

=begin nd
Function: getRBACPermissionsMsg

	Check if a user has permissions for a request.
	If a path is not contempled in the role configuration file, by default it will be allowed
	If a user has not a group or role, the user will be blocked

Parameters:
	Path - URL path of the HTTP request
	Method - HTTP method of the request

Returns:
	String - returns a blank string if the user has permissions, or a error message if it has not

=cut

sub getRBACPermissionsMsg
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $path   = shift;
	my $method = shift;

	my $msg     = "";
	my $section = "";
	my $action  = "";

	require Zevenet::User;
	my $username = &getUser();

	# if the user is root, the user can use any call
	if ( $username eq 'root' )
	{
	}

	# all user have permissions
	elsif ( &getRBACExceptions( $path, $method ) )
	{
	}

	# zapi calls reserved for root user
	elsif ( &getRBACForbidden( $path, $method ) )
	{
		$msg = "This call is exclusive for the 'root' user";
	}
	else
	{
		# it is resource?
		$msg = &getRBACResourcePermissions( $path );

		if ( !$msg )
		{
			# get action and section of config file
			( $section, $action ) = &getRBACPermissionHash( $path, $method );

			# allow by default if there is no specific permission
			if ( $section ne '' && $action ne '' )
			{
				# get permission role
				my $permission = &getRBACRolePermission( $section, $action );
				$msg =
				  "The user '$username' has not permissions for the object '$section' and the action '$action'"
				  if ( !$permission );
			}
		}
	}

	if ( $msg )
	{
		&zenlog( "Request from $username to $method $path. Action BLOCKED",
				 "Error", "RBAC" );
	}

# elsif ( &getRBACExceptions( $path, $method ) ) {}  # it is not needed now. All exceptions are GET methods
	elsif ( $method eq 'GET' ) { }    # to not log GET requests
	else
	{
		&zenlog( "Request from $username to $method $path. Action allowed",
				 "Info", "RBAC" );
	}

	return $msg;
}

=begin nd
Function: getRBACForbidden

	Check if any user can use the zapi request

Parameters:
	Path - URL path of the HTTP request
	Method - HTTP method of the request

Returns:
	Integer - 1 if the call is reserved for root user or 0 if any user can use it
=cut

sub getRBACForbidden
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $path   = shift;
	my $method = shift;
	my $deny   = 0;

	if ( $path eq "/system/users/zapi" )       { $deny = 1; }
	if ( $path eq "/system/factory" )          { $deny = 1; }
	if ( $path eq '/certificates/activation' ) { $deny = 1; }

	if ( $deny == 1 )
	{
		&zenlog( "The path '$method $path' is reserved for the user 'root'",
				 "warning", "RBAC" );
	}

	return $deny;
}

=begin nd
Function: getRBACForbidden

	Check if any user can use the zapi request

Parameters:
	Path - URL path of the HTTP request
	Method - HTTP method of the request

Returns:
	Integer - 1 if the call is reserved for root user or 0 if any user can use it
=cut

sub getRBACExceptions
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $path   = shift;
	my $method = shift;

	if ( $path eq "/certificates/activation/info" and $method eq 'GET' )
	{
		return 1;
	}

   #~ if ( $path eq "/stats/system/connections" and $method eq 'GET' ) { return 1; }
	if ( $path eq "/system/cluster/nodes/localhost" and $method eq 'GET' )
	{
		return 1;
	}
	if ( $path eq "/system/version" and $method eq 'GET' ) { return 1; }
	if ( $path =~ "/stats"          and $method eq 'GET' ) { return 1; }
	if ( $path =~ "/graphs"         and $method eq 'GET' ) { return 1; }

	return 0;
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $path = shift;
	my $hash;

	if ( $path =~ /^\/farms/ )
	{
		$hash = &getRBACPermissionFarmHash( $path );
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
	elsif ( $path =~ /^\/alias/ )
	{
		$hash = &getRBACPermissionAliasHash( $path );
	}
	elsif ( $path =~ /^\/rbac/ )
	{
		$hash = &getRBACPermissionRbacHash( $path );
	}
	elsif ( $path =~ /^\/monitoring\/fg/ )
	{
		$hash = &getRBACPermissionFgHash( $path );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
					  'regex'   => qr{^/farms/($farm_re)/ipds/},
					  'section' => 'farm',
					  'action'  => 'action',
				   },
				   {
					  'regex'   => qr{^/farms/($farm_re)/certificates$},
					  'section' => 'farm',
					  'action'  => 'modify',
				   },
				   {
					  'regex'   => qr{^/farms/($farm_re)/certificates/($cert_pem_re)/actions$},
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
					  'regex'   => qr{^/farms/$object_re(?:/services/$object_re)?/fg$},
					  'section' => 'farm',
					  'action'  => 'modify',
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
			   'regex'   => qr{^/farms/$object_re(?:/services/$object_re)?/fg/$object_re$},
			   'section' => 'farm',
			   'action'  => 'modify',
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

# [certificate]
#	show=false
#	create=false
#	download=false
#	upload=false
#	delete=false

sub getRBACPermissionCertificateHash
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $hash = {
		 'PUT' => [
				   {
					 'regex'   => qr{^/interfaces/(?:nic|vlan|gateway|floating|bonding)},
					 'section' => 'interface',
					 'action'  => 'modify',
				   },
				   {
					 'regex'   => qr{^/routing/},
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
					  {
						'regex'   => qr{^/routing/},
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
					{
					  'regex'   => qr{^/routing/},
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
					  'regex'   => qr{^/ipds/(?:rbl|blacklist|dos)/($object_re)/actions$},
					  'section' => 'ipds',
					  'action'  => 'action',
				   },
				   {
					  'regex'   => qr{^/ipds},
					  'section' => 'ipds',
					  'action'  => 'modify',
				   },
		],
	};

	return $hash;
}

# [alias]
# modify=false
# delete=true

sub getRBACPermissionAliasHash
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $hash = {
				 'PUT' => [
						   {
							 'regex'   => qr{^/aliases},
							 'section' => 'alias',
							 'action'  => 'modify',
						   },
				 ],
				 'DELETE' => [
							  {
								'regex'   => qr{^/aliases},
								'section' => 'alias',
								'action'  => 'delete',
							  },
				 ],
				 'GET' => [
						   {
							 'regex'   => qr{^/aliases},
							 'section' => 'alias',
							 'action'  => 'list',
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
					  'regex'   => qr{^/system/(?:ssh|dns|ntp|http|snmp)$},
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
					  'regex'   => qr{^/system/notifications/methods/email$},
					  'section' => 'notification',
					  'action'  => 'modify',
				   },
				   {
					  'regex'   => qr{^/system/notifications/methods/email/actions$},
					  'section' => 'notification',
					  'action'  => 'test',
				   },
				   {
					  'regex'   => qr{^/system/notifications/alerts/$object_re$},
					  'section' => 'notification',
					  'action'  => 'modify',
				   },
				   {
					  'regex'   => qr{^/system/notifications/alerts/$object_re/actions$},
					  'section' => 'notification',
					  'action'  => 'action',
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
					 'regex'   => qr{^/system/supportsave$},
					 'section' => 'supportsave',
					 'action'  => 'download',
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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

# fg

sub getRBACPermissionFgHash
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $hash = {
				 'PUT' => [
						   {
							 'regex'   => qr{^/monitoring/fg/$object_re$},
							 'section' => 'farmguardian',
							 'action'  => 'modify',
						   },
				 ],
				 'DELETE' => [
							  {
								'regex'   => qr{^/monitoring/fg/$object_re$},
								'section' => 'farmguardian',
								'action'  => 'modify',
							  },
				 ],
				 'POST' => [
							{
							  'regex'   => qr{^/monitoring/fg$},
							  'section' => 'farmguardian',
							  'action'  => 'modify',
							},
				 ],
	};

	return $hash;
}

1;
