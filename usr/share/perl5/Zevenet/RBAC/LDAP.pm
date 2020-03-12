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
use Zevenet::Config;
include 'Zevenet::RBAC::Core';

my $ldap_file = &getRBACServicesConfPath();

=begin nd
Function: getLDAP

	Get the configuration to connect with the the LDAP server

Parameters:
	none - .

Returns:
	hash ref - the LDAP server settings. The list of parameters are:
		enabled, it indicates if the service is enabled (value 'true') or if it is not (value 'false')
		host, it is the LDAP URL or the server IP
		port, it is the port where the LDAP server is listening. This filed is skipt if the host is a URL or overwrite the port
	    binddn, it is the LDAP admin user used to modify manage. It is not necessary if the LDAP can be queried anonimously
	    bindpw, it is the password for the admin user
	    basedn, it is the base used to look for the user in the LDAP
	    filter, it is used to get an user based on some attribute
	    version, it is the LDAP version used by the server
	    scope, the search scope, can be base, one or sub, defaults to sub
        timeout, timeout of the query

=cut

sub getLDAP
{
	my $ldap = &getTiny( $ldap_file );
	$ldap = $ldap->{ 'ldap' };

#~ my $ldap_host = "192.168.101.253";
#~ my $ldap_binddn = "cn=admin,dc=zevenet,dc=com";
#~ my $ldap_bindpwd = "admin";
#~ my $ldap_basedn = "dc=zevenet,dc=com";
#~ my $ldap_filter = '(&(objectClass=inetOrgPerson)(objectClass=posixAccount)(uid=%s))';

	$ldap->{ enabled } //= 'false';
	$ldap->{ host }    //= '';
	$ldap->{ port }    //= '389';
	$ldap->{ binddn }  //= '';
	$ldap->{ bindpw }  //= '';
	$ldap->{ basedn }  //= '';
	$ldap->{ filter }  //= '';
	$ldap->{ version } //= 3;
	$ldap->{ scope }   //= 'sub';
	$ldap->{ timeout } //= 60;

	return $ldap;
}

=begin nd
Function: setLDAP

	Modify the LDAP configuration which is used to connect with the LDAP server

Parameters:
	hash ref - the LDAP server settings. The list of parameters are:
		enabled, it indicates if the service is enabled (value 'true') or if it is not (value 'false')
		host, it is the LDAP URL or the server IP
		port, it is the port where the LDAP server is listening. This filed is skipt if the host is a URL or overwrite the port
	    binddn, it is the LDAP admin user used to modify manage. It is not necessary if the LDAP can be queried anonimously
	    bindpw, it is the password for the admin user
	    basedn, it is the base used to look for the user in the LDAP
	    filter, it is used to get an user based on some attribute
	    version, it is the LDAP version used by the server
	    scope, the search scope, can be base, one or sub, defaults to sub
        timeout, timeout of the query

Returns:
	Integer - Error code. 0 on success or another value on failure

=cut

sub setLDAP
{
	my $conf = shift;

	if ( exists $conf->{ bindpw } )
	{
		include 'Zevenet::Code';
		$conf->{ bindpw } = &getCodeEncode( $conf->{ bindpw } );
	}

	my $err = &setTinyObj( $ldap_file, 'ldap', $conf );
	return $err;
}

=begin nd
Function: testLDAP

	Do a connect against the LDAP server to check the availability

Parameters:
	none - .

Returns:
	Integer - Returns 1 when the server is reachable or 0 on connecting failure

=cut

sub testLDAP
{
	my $suc       = 0;
	my $ldap_conf = &getLDAP();

	if ( $ldap_conf->{ host } )
	{
		require Authen::Simple::LDAP;
		my $ldap;
		if (
			 $ldap = Net::LDAP->new(
									 $ldap_conf->{ host },
									 port    => $ldap_conf->{ port },
									 timeout => $ldap_conf->{ timeout },
									 version => $ldap_conf->{ version },
			 )
		  )
		{
			if ( $ldap_conf->{ binddn } )
			{
				my @bind_cfg = ( $ldap_conf->{ binddn } );
				if ( $ldap_conf->{ bindpw } )
				{
					include 'Zevenet::Code';
					my $pass = &getCodeDecode( $ldap_conf->{ bindpw } );
					push @bind_cfg, ( 'password' => $pass );
				}

				my $msg = $ldap->bind( @bind_cfg );
				unless ( $msg->code )
				{
					$suc = 1;
					$ldap->unbind();
				}
			}

			# anonymous bind
			else
			{
				$suc = 1;
			}
		}
	}

	if ( $suc )
	{
		&zenlog( "The load balancer can access to the LDAP service", "debug", "rbac" );
	}
	else
	{
		&zenlog( "The load balancer cannot access to the LDAP service",
				 "debug", "rbac" );
	}

	return $suc;
}

=begin nd
Function: authLDAP

	Authenticate a user against a LDAP server

Parameters:
	User - User name
	Password - User password

Returns:
	Integer - Return 1 if the user was properly validated or another value if it failed

=cut

sub authLDAP
{
	my ( $user, $pass ) = @_;
	my $suc       = 0;
	my $ldap_conf = &getLDAP();
	delete $ldap_conf->{ filter } if ( $ldap_conf->{ filter } eq '' );

	if ( &getRBACServiceEnabled( 'ldap' ) eq 'true' )
	{
		delete $ldap_conf->{ enabled };
		require Authen::Simple::LDAP;
		eval {

			include 'Zevenet::Code';
			$ldap_conf->{ bindpw } = &getCodeDecode( $ldap_conf->{ bindpw } )
			  if ( defined $ldap_conf->{ bindpw } );

			my $ldap = Authen::Simple::LDAP->new( $ldap_conf );
			if ( $ldap->authenticate( $user, $pass ) )
			{
				&zenlog( "The user '$user' login with ldap auth service", "debug", "auth" );
				$suc = 1;
			}
		};
		if ( $@ )
		{
			$suc = 0;
			&zenlog( "The load balancer cannot run the LDAP query: $@", "debug", "rbac" );
		}
	}
	else
	{
		$suc = 0;
		&zenlog( "LDAP Authentication Service is not active", "debug", "rbac" );
	}

	return $suc;
}

1;

