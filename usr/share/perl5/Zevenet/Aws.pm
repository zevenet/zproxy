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

=begin nd
Function: setSshForCluster

	Modify SSH configuration to allow SSH connections for cluster

Parameters:
	String - IP remote node.

Returns:
	Interger - It returns the code error

=cut

sub setSshForCluster
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $remote_ip = shift;
	my $type      = shift;

	my $sshFile = &getGlobalConfiguration( 'sshConf' );
	my $output  = 1;

	if ( !-e $sshFile )
	{
		&zenlog( "SSH configuration file doesn't exist.", "error", "AWS" );
		return -1;
	}

	require Zevenet::Lock;
	my $cat = &getGlobalConfiguration( 'cat_bin' );

	if ( $type eq 'delete'
		 && grep ( /Match Address ${remote_ip}/, `$cat $sshFile` ) )
	{

		&ztielock( \my @file, "$sshFile" );
		my $cont = 0;

		foreach my $line ( @file )
		{
			if ( $line =~ /Match Address ${remote_ip}/ )
			{
				my $start = $cont - 1;
				splice ( @file, $start, 4 );
				$output = 0;
			}
			$cont++;
		}
		untie @file;
	}
	elsif ( $type eq 'add' )
	{
		my $sshConf =
		  "\nMatch Address $remote_ip\n\tPermitRootLogin yes\n\tPasswordAuthentication yes";

		&ztielock( \my @currentConf, "$sshFile" );
		push @currentConf, $sshConf;
		untie @currentConf;
	}

	# restart service to apply changes
	my $cmd = &getGlobalConfiguration( 'sshService' ) . " restart";
	$output = &logAndRun( $cmd );

	return $output;
}

=begin nd
Function: setSshRemoteForCluster 

	Set the SSH configuration in remote node for cluster

Parameters:
	remote ip - Remote Ip of a remote load balancer
	password - Remote password of a remote load balancer
	local ip - Local IP

Returns:
	String - It returns the session cookie

=cut

sub setSshRemoteForCluster
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $remote_ip = shift;
	my $password  = shift;
	my $local_ip  = shift;

	my $cookie = &getRemoteSession( $remote_ip, $password );

	if ( !$cookie )
	{
		&zenlog( "It is not possible get the SESSION_ID", "error", "AWS" );
		return -1;
	}

	my $code = &remoteSshCall( $remote_ip, $cookie, $local_ip );

	return $code;
}

=begin nd
Function: getRemoteSession 

	Get SESSION_ID of a session with a remote load balancer 

Parameters:
	ip - Remote Ip of a load balancer
	password - Remote password of a load balancer

Returns:
	String - It returns the session cookie

=cut

sub getRemoteSession
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $remote_ip = shift;
	my $password  = shift;

	my $curl = &getGlobalConfiguration( 'curl_bin' );

	use MIME::Base64;
	include 'Zevenet::System::HTTP';
	my $auth = encode_base64( "root:$password", '' );
	my $port = &getHttpServerPort();

	my $url     = "https://$remote_ip:$port/zapi/v4.0/zapi.cgi/session";
	my $fcookie = "/tmp/remote_cookie";
	my $headers =
	  "-H 'Content-Type: application/json' -H 'Authorization: Basic $auth'";

	my $cmd =
	  "$curl -X POST -s -f -k $url --connect-timeout 2 --cookie-jar $fcookie -d '{}' $headers";
	my $error = &logAndRun( $cmd );

	if ( $error )
	{
		&zenlog( "It is not possible to open a remote session", "error", "AWS" );
		return -1;
	}

	if ( !-e $fcookie )
	{
		&zenlog( "The remote cookie cannot be obtained", "error", "AWS" );
		return -1;
	}

	my $cookie_file_lock = &openlock( $fcookie, '<' );
	my $cat = &getGlobalConfiguration( 'cat_bin' );

	my @match = grep /CGISESSID\t(.+)/, `$cat $fcookie`;
	$match[0] =~ /CGISESSID\t([a-z0-9]+)/;
	my $cookie = $1;

	close $cookie_file_lock;
	unlink $fcookie;

	if ( !$cookie )
	{
		&zenlog( "The remote cookie has not been received", "error", "AWS" );
		return -1;
	}

	return $cookie;
}

=begin nd
Function: remoteSshCall 

	Call to remote load balancer to set the SSH configuration

Parameters:
	remote ip - Remote Ip of a remote load balancer
	cookie - SESSION_ID with the remote load balancer
	local ip - Local IP

Returns:
	String - It returns the error code

=cut

sub remoteSshCall
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $remote_ip = shift;
	my $cookie    = shift;
	my $local_ip  = shift;

	include 'Zevenet::System::HTTP';
	my $curl = &getGlobalConfiguration( 'curl_bin' );
	my $port = &getHttpServerPort();

	my $url = "https://$remote_ip:$port/zapi/v4.0/zapi.cgi/aws/ssh";
	my $headers =
	  "-H 'Content-Type: application/json' -H 'Cookie: CGISESSID=$cookie'";

	my $cmd =
	  "$curl -X PUT -s -f -k $url $headers --connect-timeout 2 -d '{\"remote_ip\": \"$local_ip\"}'";
	my $error = &logAndRun( $cmd );

	if ( $error )
	{
		&zenlog( "It is not possible to modify the remote node SSH", "error", "AWS" );
		return -1;
	}

	return $error;
}

=begin nd
Function: getInstanceId

        Get instance ID

Parameters:
        none -

Returns:
        String - The instance ID

=cut

sub getInstanceId
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $wget          = &getGlobalConfiguration( 'wget' );
	my $cloud_address = &getGlobalConfiguration( 'cloud_address_metadata' );

	my $instance_id = &logAndGet(
			  "$wget -q -O - -T 5 http://$cloud_address/latest/meta-data/instance-id" );

	return $instance_id;
}

=begin nd
Function: reassignInterfaces 

	Reassign interfaces of the remote node to this node

Parameters:
	none -

Returns:
	Interger - It returns the code error

=cut

sub reassignInterfaces
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	include 'Zevenet::Cluster';
	my $zcl_conf      = &getZClusterConfig();
	my $remote_hn     = &getZClusterRemoteHost();
	my $cloud_address = &getGlobalConfiguration( 'cloud_address_metadata' );
	my $aws           = &getGlobalConfiguration( 'aws_bin' );
	my $wget          = &getGlobalConfiguration( 'wget' );

	my $remote_instance_id = &runRemotely(
				"$wget -q -O - -T 5 http://$cloud_address/latest/meta-data/instance-id",
				$zcl_conf->{ $remote_hn }->{ ip } );

	my $instance_id = &getInstanceId();
	my $error       = 0;

	if ( $instance_id && $remote_instance_id )
	{
		my @network_ids = @{ &getNetworksInterfaces( $instance_id ) };

		my $query = @{
			&logAndGet(
				"$aws ec2 describe-instances --instance-ids $remote_instance_id --query \"Reservations[*].Instances[*].NetworkInterfaces[*]\""
			)
		};

		my $json = eval { JSON::XS::decode_json( $query ) };
		my @virtuals_ip = @{ $json->[0]->[0] };

		foreach my $network ( @virtuals_ip )
		{
			my $subnet = $network->{ SubnetId };
			my @network_iface = grep { $_->{ SubnetId } eq $subnet } @network_ids;

			foreach my $line ( @{ $network->{ PrivateIpAddresses } } )
			{
				if ( !$line->{ Primary } )
				{
					$error = &logAndRun(
						"$aws ec2 assign-private-ip-addresses --allow-reassignment --network-interface-id $network_iface[0]->{ NetworkInterfaceId } --private-ip-addresses $line->{ PrivateIpAddress }"
					);

					if ( $error )
					{
						&zenlog(
							"It is not possible to change the private IP $line->{ \" PrivateIpAddress \" }",
							"error", "AWS"
						);
						return -1;
					}
				}
			}
		}
		return 0;
	}

	&zenlog( "It is not possible to get the instance ID", "error", "AWS" );
	return -1;
}

=begin nd
Function: getNetworksInterfaces 

	Get the network interfaces IDs of a instance

Parameters:
	id - Instance ID

Returns:
	Array - It returns the networks interfaces IDs

=cut

sub getNetworksInterfaces
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $instance_id = shift;
	my $aws         = &getGlobalConfiguration( 'aws_bin' );

	my $query = @{
		&logAndGet(
			"$aws ec2 describe-instances --instance-ids $instance_id --query \"Reservations[*].Instances[*].NetworkInterfaces[*]\""
		)
	};

	require JSON::XS;
	my $json = eval { JSON::XS::decode_json( $query ) };
	my @network_ifaces = @{ $json->[0]->[0] };

	return \@network_ifaces;
}

=begin nd
Function: disableSshCluster 

	Disable the SSH configuration for cluster

Parameters:
	none -

Returns:
	String - It returns the code error

=cut

sub disableSshCluster
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	include 'Zevenet::Cluster';
	require Zevenet::SystemInfo;
	my $zcl_conf  = &getZClusterConfig();
	my $remote_hn = &getZClusterRemoteHost();

	my $output = &setSshForCluster( $zcl_conf->{ $remote_hn }->{ ip }, 'delete' );

	return $output;
}

=begin nd
Function: getCredentials 

	Get AWS credentials

Parameters:
	file - File to get. Credentials or credentials config

Returns:
	Array - It returns the credentials or the credentials config

=cut

sub getCredentials
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $file = shift;

	require Config::Tiny;
	require Zevenet::Config;

	my $file = &getGlobalConfiguration( "aws_$file" );

	if ( !-f $file )
	{
		open my $zcl_file, '>', $file;

		if ( !$zcl_file )
		{
			&zenlog( "Could not create file $file: $!", "error", "AWS" );
			return;
		}

		close $zcl_file;
	}

	my $config = Config::Tiny->read( $file ) // {};

	# returns object on success or undef on error.
	return $config;
}

=begin nd
Function: setCredentials 

	Set AWS credentials

Parameters:
	json_obj - Object with parameter to set.

Returns:
	String - It returns the code error.

=cut

sub setCredentials
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $aws      = &getGlobalConfiguration( 'aws_bin' );

	if ( exists ( $json_obj->{ access_key } ) )
	{

		my $error = &logAndRun(
						 "$aws configure set aws_access_key_id $json_obj->{ access_key }" );
		if ( $error )
		{
			return $error;
		}
	}
	if ( exists ( $json_obj->{ secret_key } )
		 && !grep ( /^\*+$/, $json_obj->{ secret_key } ) )
	{

		my $error = &logAndRun(
					 "$aws configure set aws_secret_access_key $json_obj->{ secret_key }" );
		if ( $error )
		{
			return $error;
		}
	}
	if ( exists ( $json_obj->{ region } ) )
	{

		my $error = &logAndRun( "$aws configure set region $json_obj->{ region }" );
		if ( $error )
		{
			return $error;
		}
	}
	&logAndRun( "$aws configure set output json" );

	return 0;
}

1;

