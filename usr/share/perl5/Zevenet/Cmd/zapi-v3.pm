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
use warnings;
use Zevenet;

use Zevenet::Farm::Core;
use Zevenet::Farm::Base;
use Zevenet::Farm::Stats;
use Zevenet::Farm::Factory;
use Zevenet::Farm::Action;
use Zevenet::Farm::Config;
use Zevenet::Farm::Backend;

include 'Zevenet::API3';
include 'Zevenet::Zapi';
include 'Zevenet::Cluster';
include 'Zevenet::Net::Bonding';
include 'Zevenet::Net::Floating';
include 'Zevenet::System::SSH';

package GLOBAL
{
	our $http_status_codes = {

		# 2xx Success codes
		200 => 'OK',
		201 => 'Created',
		204 => 'No Content',

		# 4xx Client Error codes
		400 => 'Bad Request',
		401 => 'Unauthorized',
		402 => 'Certificate not valid',
		403 => 'Forbidden',
		404 => 'Not Found',
		406 => 'Not Acceptable',
		410 => 'Gone',
		415 => 'Unsupported Media Type',
		422 => 'Unprocessable Entity',
	};
};

sub OPTIONS;
sub GET;
sub POST;
sub PUT;
sub DELETE;

use Zevenet::Log;
use Zevenet::Debug;
use Zevenet::CGI;
include 'Zevenet::API3::HTTP';

my $q = &getCGI();

#  OPTIONS PreAuth
OPTIONS qr{^/.*$} => sub {
	&httpResponse( { code => 200 } );
};

require Zevenet::Config;
require Zevenet::Validate;
include 'Zevenet::API3::Auth';

################################################################################
#
# Start [Method URI] calls
#
################################################################################

#  POST CGISESSID
POST qr{^/session$} => sub {
	require CGI::Session;
	my $session = CGI::Session->new( &getCGI() );

	if ( $session && !$session->param( 'is_logged_in' ) )
	{
		my @credentials = &getAuthorizationCredentials();

		my ( $username, $password ) = @credentials;

		if ( &authenticateCredentials( @credentials ) )
		{
			# successful authentication
			&zenlog( "Login successful for user: $username" );

			$session->param( 'is_logged_in', 1 );
			$session->param( 'username',     $username );
			$session->expire( 'is_logged_in', '+30m' );

			my ( $header ) = split ( "\r\n", $session->header() );
			my ( undef, $session_cookie ) = split ( ': ', $header );
			my $key  = &keycert();
			my $host = &getHostname();

			&httpResponse(
						   {
							 body => { key => $key, host => $host },
							 code => 200,
							 headers => { 'Set-cookie' => $session_cookie },
						   }
			);
		}
		else    # not validated credentials
		{
			&zenlog( "Login failed for username: $username" );

			$session->delete();
			$session->flush();

			&httpResponse( { code => 401 } );
		}
	}

	exit;
};

#	Above this part are calls allowed without authentication
######################################################################
unless (    ( exists $ENV{ HTTP_ZAPI_KEY } && &validZapiKey() )
		 or ( exists $ENV{ HTTP_COOKIE } && &validCGISession() ) )
{
	&httpResponse(
				   { code => 401, body => { message => 'Authorization required' } } );
}

#	SESSION LOGOUT
#

#  DELETE session
DELETE qr{^/session$} => sub {
	my $cgi = &getCGI();
	if ( $cgi->http( 'Cookie' ) )
	{
		my $session = new CGI::Session( $cgi );

		if ( $session && $session->param( 'is_logged_in' ) )
		{
			my $username = $session->param( 'username' );
			my $ip_addr  = $session->param( '_SESSION_REMOTE_ADDR' );

			&zenlog( "Logged out user $username from $ip_addr" );

			$session->delete();
			$session->flush();

			&httpResponse( { code => 200 } );
		}
	}

	# with ZAPI key or expired cookie session
	&httpResponse( { code => 400 } );
};

#	CERTIFICATES
#
_certificates:

if ( $q->path_info =~ qr{^/certificates/activation$} )
{
	include 'Zevenet::API3::Certificate::Activation';

	#  GET activation certificate
	GET qr{^/certificates/activation$} => sub {
		&get_activation_certificate_info( @_ );
	};

	#  POST activation certificate
	POST qr{^/certificates/activation$} => sub {
		&upload_activation_certificate( @_ );
	};

	#  DELETE activation certificate
	DELETE qr{^/certificates/activation$} => sub {
		&delete_activation_certificate( @_ );
	};
}

#	Check activation certificate
######################################################################
&checkActivationCertificate();

my $cert_re     = &getValidFormat( 'certificate' );
my $cert_pem_re = &getValidFormat( 'cert_pem' );

if ( $q->path_info =~ qr{^/certificates} )
{
	include 'Zevenet::API3::Certificate';

	#  GET List SSL certificates
	GET qr{^/certificates$} => sub {
		&certificates();
	};

	#  Download SSL certificate
	GET qr{^/certificates/($cert_re)$} => sub {
		&download_certificate( @_ );
	};

	#  GET SSL certificate information
	GET qr{^/certificates/($cert_re)/info$} => sub {
		&get_certificate_info( @_ );
	};

	#  Create CSR certificates
	POST qr{^/certificates$} => sub {
		&create_csr( @_ );
	};

	#  POST certificates
	POST qr{^/certificates/($cert_pem_re)$} => sub {
		&upload_certificate( @_ );
	};

	#  DELETE certificate
	DELETE qr{^/certificates/($cert_re)$} => sub {
		&delete_certificate( @_ );
	};
}

#	FARMS
#
_farms:

my $farm_re    = &getValidFormat( 'farm_name' );
my $service_re = &getValidFormat( 'service' );
my $be_re      = &getValidFormat( 'backend' );

##### /farms
if ( $q->path_info =~ qr{^/farms/$farm_re/certificates} )
{
	include 'Zevenet::API3::Certificate::Farm';

	POST qr{^/farms/($farm_re)/certificates$} => sub {
		&add_farm_certificate( @_ );
	};

	DELETE qr{^/farms/($farm_re)/certificates/($cert_pem_re)$} => sub {
		&delete_farm_certificate( @_ );
	};
}

if ( $q->path_info =~ qr{^/farms/$farm_re/fg} )
{
	include 'Zevenet::API3::Farm::Guardian';

	PUT qr{^/farms/($farm_re)/fg$} => sub {
		&modify_farmguardian( @_ );
	};
}

if ( $q->path_info =~ qr{^/farms/$farm_re/actions} )
{
	include 'Zevenet::API3::Farm::Action';

	PUT qr{^/farms/($farm_re)/actions$} => sub {
		&farm_actions( @_ );
	};
}

if ( $q->path_info =~ qr{^/farms/$farm_re.*/backends/$be_re/maintenance} )
{
	include 'Zevenet::API3::Farm::Action';

	PUT qr{^/farms/($farm_re)/services/($service_re)/backends/($be_re)/maintenance$}
	  => sub {
		&service_backend_maintenance( @_ );
	  };    #  (HTTP only)

	PUT qr{^/farms/($farm_re)/backends/($be_re)/maintenance$} => sub {
		&backend_maintenance( @_ );
	};      #  (L4xNAT only)
}

if ( $q->path_info =~ qr{^/farms/$farm_re/zones} )
{
	include 'Zevenet::API3::Farm::Zone';

	POST qr{^/farms/($farm_re)/zones$} => sub {
		&new_farm_zone( @_ );
	};

	my $zone_re = &getValidFormat( 'zone' );

	PUT qr{^/farms/($farm_re)/zones/($zone_re)$} => sub {
		&modify_zones( @_ );
	};

	DELETE qr{^/farms/($farm_re)/zones/($zone_re)$} => sub {
		&delete_zone( @_ );
	};

	GET qr{^/farms/($farm_re)/zones/($zone_re)/resources$} => sub {
		&gslb_zone_resources( @_ );
	};

	POST qr{^/farms/($farm_re)/zones/($zone_re)/resources$} => sub {
		&new_farm_zone_resource( @_ );
	};

	my $resource_id_re = &getValidFormat( 'resource_id' );

	PUT qr{^/farms/($farm_re)/zones/($zone_re)/resources/($resource_id_re)$} =>
	  sub {
		&modify_zone_resource( @_ );
	  };

	DELETE qr{^/farms/($farm_re)/zones/($zone_re)/resources/($resource_id_re)$} =>
	  sub {
		&delete_zone_resource( @_ );
	  };
}

if ( $q->path_info =~ qr{^/farms/$farm_re(?:/services/$service_re)?/backends} )
{
	include 'Zevenet::API3::Farm::Backend';

	GET qr{^/farms/($farm_re)/backends$} => sub {
		&backends( @_ );
	};

	POST qr{^/farms/($farm_re)/backends$} => sub {
		&new_farm_backend( @_ );
	};

	PUT qr{^/farms/($farm_re)/backends/($be_re)$} => sub {
		&modify_backends( @_ );
	};

	DELETE qr{^/farms/($farm_re)/backends/($be_re)$} => sub {
		&delete_backend( @_ );
	};

	GET qr{^/farms/($farm_re)/services/($service_re)/backends$} => sub {
		&service_backends( @_ );
	};

	POST qr{^/farms/($farm_re)/services/($service_re)/backends$} => sub {
		&new_service_backend( @_ );
	};

	PUT qr{^/farms/($farm_re)/services/($service_re)/backends/($be_re)$} => sub {
		&modify_service_backends( @_ );
	};

	DELETE qr{^/farms/($farm_re)/services/($service_re)/backends/($be_re)$} => sub {
		&delete_service_backend( @_ );
	};
}

if ( $q->path_info =~ qr{^/farms/$farm_re/services} )
{
	include 'Zevenet::API3::Farm::Service';

	POST qr{^/farms/($farm_re)/services$} => sub {
		&new_farm_service( @_ );
	};

	GET qr{^/farms/($farm_re)/services/($service_re)$} => sub {
		&farm_services( @_ );
	};

	POST qr{^/farms/($farm_re)/services/($service_re)/actions$} => sub {
		&move_services( @_ );
	};

	PUT qr{^/farms/($farm_re)/services/($service_re)$} => sub {
		&modify_services( @_ );
	};

	DELETE qr{^/farms/($farm_re)/services/($service_re)$} => sub {
		&delete_service( @_ );
	};
}

if ( $q->path_info =~ qr{^/farms} )
{
	include 'Zevenet::API3::Farm';

	GET qr{^/farms$} => sub {
		&farms();
	};

	POST qr{^/farms$} => sub {
		&new_farm( @_ );
	};

	##### /farms

	GET qr{^/farms/modules/lslb$} => sub {
		&farms_lslb();
	};

	GET qr{^/farms/modules/gslb$} => sub {
		&farms_gslb();
	};

	GET qr{^/farms/modules/dslb$} => sub {
		&farms_dslb();
	};

	##### /farms/FARM

	GET qr{^/farms/($farm_re)$} => sub {
		&farms_name( @_ );
	};

	PUT qr{^/farms/($farm_re)$} => sub {
		&modify_farm( @_ );
	};

	DELETE qr{^/farms/($farm_re)$} => sub {
		&delete_farm( @_ );
	};
}

#	NETWORK INTERFACES
#
_interfaces:

my $nic_re  = &getValidFormat( 'nic_interface' );
my $bond_re = &getValidFormat( 'bond_interface' );
my $vlan_re = &getValidFormat( 'vlan_interface' );

if ( $q->path_info =~ qr{^/interfaces/nic} )
{
	include 'Zevenet::API3::Interface::NIC';

	GET qr{^/interfaces/nic$} => sub {
		&get_nic_list();
	};

	GET qr{^/interfaces/nic/($nic_re)$} => sub {
		&get_nic( @_ );
	};

	PUT qr{^/interfaces/nic/($nic_re)$} => sub {
		&modify_interface_nic( @_ );
	};

	DELETE qr{^/interfaces/nic/($nic_re)$} => sub {
		&delete_interface_nic( @_ );
	};

	POST qr{^/interfaces/nic/($nic_re)/actions$} => sub {
		&actions_interface_nic( @_ );
	};
}

if ( $q->path_info =~ qr{^/interfaces/vlan} )
{
	include 'Zevenet::API3::Interface::VLAN';

	GET qr{^/interfaces/vlan$} => sub {
		&get_vlan_list();
	};

	POST qr{^/interfaces/vlan$} => sub {
		&new_vlan( @_ );
	};

	GET qr{^/interfaces/vlan/($vlan_re)$} => sub {
		&get_vlan( @_ );
	};

	PUT qr{^/interfaces/vlan/($vlan_re)$} => sub {
		&modify_interface_vlan( @_ );
	};

	DELETE qr{^/interfaces/vlan/($vlan_re)$} => sub {
		&delete_interface_vlan( @_ );
	};

	POST qr{^/interfaces/vlan/($vlan_re)/actions$} => sub {
		&actions_interface_vlan( @_ );
	};
}

if ( $q->path_info =~ qr{^/interfaces/bonding} )
{
	include 'Zevenet::API3::Interface::Bonding';

	GET qr{^/interfaces/bonding$} => sub {
		&get_bond_list();
	};

	POST qr{^/interfaces/bonding$} => sub {
		&new_bond( @_ );
	};

	GET qr{^/interfaces/bonding/($bond_re)$} => sub {
		&get_bond( @_ );
	};

	PUT qr{^/interfaces/bonding/($bond_re)$} => sub {
		&modify_interface_bond( @_ );
	};

	DELETE qr{^/interfaces/bonding/($bond_re)$} => sub {
		&delete_interface_bond( @_ );
	};

	POST qr{^/interfaces/bonding/($bond_re)/slaves$} => sub {
		&new_bond_slave( @_ );
	};

	DELETE qr{^/interfaces/bonding/($bond_re)/slaves/($nic_re)$} => sub {
		&delete_bond_slave( @_ );
	};

	POST qr{^/interfaces/bonding/($bond_re)/actions$} => sub {
		&actions_interface_bond( @_ );
	};
}

if ( $q->path_info =~ qr{^/interfaces/virtual} )
{
	include 'Zevenet::API3::Interface::Virtual';

	GET qr{^/interfaces/virtual$} => sub {
		&get_virtual_list();
	};

	POST qr{^/interfaces/virtual$} => sub {
		&new_vini( @_ );
	};

	my $virtual_re = &getValidFormat( 'virt_interface' );

	GET qr{^/interfaces/virtual/($virtual_re)$} => sub {
		&get_virtual( @_ );
	};

	PUT qr{^/interfaces/virtual/($virtual_re)$} => sub {
		&modify_interface_virtual( @_ );
	};

	DELETE qr{^/interfaces/virtual/($virtual_re)$} => sub {
		&delete_interface_virtual( @_ );
	};

	POST qr{^/interfaces/virtual/($virtual_re)/actions$} => sub {
		&actions_interface_virtual( @_ );
	};
}

if ( $q->path_info =~ qr{^/interfaces/floating} )
{
	include 'Zevenet::API3::Interface::Floating';

	GET qr{^/interfaces/floating$} => sub {
		&get_interfaces_floating( @_ );
	};

	GET qr{^/interfaces/floating/($nic_re|$bond_re|$vlan_re)$} => sub {
		&get_floating( @_ );
	};

	PUT qr{^/interfaces/floating/($nic_re|$bond_re|$vlan_re)$} => sub {
		&modify_interface_floating( @_ );
	};

	DELETE qr{^/interfaces/floating/($nic_re|$bond_re|$vlan_re)$} => sub {
		&delete_interface_floating( @_ );
	};
}

if ( $q->path_info =~ qr{^/interfaces/gateway} )
{
	include 'Zevenet::API3::Interface::Gateway';

	GET qr{^/interfaces/gateway$} => sub {
		&get_gateway( @_ );
	};

	PUT qr{^/interfaces/gateway$} => sub {
		&modify_gateway( @_ );
	};

	DELETE qr{^/interfaces/gateway$} => sub {
		&delete_gateway( @_ );
	};
}

if ( $q->path_info =~ qr{^/interfaces} )
{
	include 'Zevenet::API3::Interface::Generic';

	GET qr{^/interfaces$} => sub {
		&get_interfaces();
	};
}

#	STATS
#
_stats:

if ( $q->path_info =~ qr{^/stats} )
{
	include 'Zevenet::API3::Stats';

	# System stats
	GET qr{^/stats$} => sub {
		&stats();
	};

	GET qr{^/stats/system/memory$} => sub {
		&stats_mem();
	};

	GET qr{^/stats/system/load$} => sub {
		&stats_load();
	};

	GET qr{^/stats/system/network$} => sub {
		&stats_network();
	};

	GET qr{^/stats/system/network/interfaces$} => sub {
		&stats_network_interfaces();
	};

	GET qr{^/stats/system/cpu$} => sub {
		&stats_cpu();
	};

	GET qr{^/stats/system/connections$} => sub {
		&stats_conns();
	};

	# Farm stats
	my $modules_re = &getValidFormat( 'farm_modules' );
	GET qr{^/stats/farms$} => sub {
		&all_farms_stats( @_ );
	};

	GET qr{^/stats/farms/total$} => sub {
		&farms_number( @_ );
	};

	GET qr{^/stats/farms/modules$} => sub {
		&module_stats_status( @_ );
	};

	GET qr{^/stats/farms/modules/($modules_re)$} => sub {
		&module_stats( @_ );
	};

	GET qr{^/stats/farms/($farm_re)$} => sub {
		&farm_stats( @_ );
	};

	GET qr{^/stats/farms/($farm_re)/backends$} => sub {
		&farm_stats( @_ );
	};

	# Fixed: make 'service' or 'services' valid requests for compatibility
	# with previous bug.
	GET qr{^/stats/farms/($farm_re)/services?/($service_re)/backends$} => sub {
		&farm_stats( @_ );
	};
}

#	GRAPHS
#
_graphs:

if ( $q->path_info =~ qr{^/graphs} )
{
	include 'Zevenet::API3::Graph';

	my $frequency_re = &getValidFormat( 'graphs_frequency' );
	my $system_id_re = &getValidFormat( 'graphs_system_id' );

	#  GET graphs

	#  GET possible graphs
	GET qr{^/graphs$} => sub {
		&possible_graphs();
	};

	##### /graphs/system
	#  GET all possible system graphs
	GET qr{^/graphs/system$} => sub {
		&get_all_sys_graphs();
	};

	#  GET system graphs
	GET qr{^/graphs/system/($system_id_re)$} => sub {
		&get_sys_graphs( @_ );
	};

	#  GET frequency system graphs
	GET qr{^/graphs/system/($system_id_re)/($frequency_re)$} => sub {
		&get_frec_sys_graphs( @_ );
	};

	##### /graphs/system/disk

	# $disk_re includes 'root' at the beginning
	my $disk_re = &getValidFormat( 'mount_point' );

	GET qr{^/graphs/system/disk$} => sub {
		&list_disks( @_ );
	};

	# keep before next request
	GET qr{^/graphs/system/disk/($disk_re)/($frequency_re)$} => sub {
		&graph_disk_mount_point_freq( @_ );
	};

	GET qr{^/graphs/system/disk/($disk_re)$} => sub {
		&graphs_disk_mount_point_all( @_ );
	};

	##### /graphs/interfaces

	#  GET all posible interfaces graphs
	GET qr{^/graphs/interfaces$} => sub {
		&get_all_iface_graphs( @_ );
	};

	#  GET interfaces graphs
	GET qr{^/graphs/interfaces/($nic_re|$vlan_re)$} => sub {
		&get_iface_graphs( @_ );
	};

	#  GET frequency interfaces graphs
	GET qr{^/graphs/interfaces/($nic_re)/($frequency_re)$} => sub {
		&get_frec_iface_graphs( @_ );
	};

	##### /graphs/farms

	#  GET all posible farm graphs
	GET qr{^/graphs/farms$} => sub {
		&get_all_farm_graphs( @_ );
	};

	#  GET farm graphs
	GET qr{^/graphs/farms/($farm_re)$} => sub {
		&get_farm_graphs( @_ );
	};

	#  GET frequency farm graphs
	GET qr{^/graphs/farms/($farm_re)/($frequency_re)$} => sub {
		&get_frec_farm_graphs( @_ );
	};
}

# SYSTEM
#
_system:

if ( $q->path_info =~ qr{^/system/cluster} )
{
	include 'Zevenet::API3::System::Cluster';

	#### /system/cluster
  _cluster:
	GET qr{^/system/cluster$} => sub {
		&get_cluster( @_ );
	};

	POST qr{^/system/cluster$} => sub {
		&enable_cluster( @_ );
	};

	PUT qr{^/system/cluster$} => sub {
		&modify_cluster( @_ );
	};

	DELETE qr{^/system/cluster$} => sub {
		&disable_cluster( @_ );
	};

	POST qr{^/system/cluster/actions$} => sub {
		&set_cluster_actions( @_ );
	};

	GET qr{^/system/cluster/nodes$} => sub {
		&get_cluster_nodes_status( @_ );
	};

	GET qr{^/system/cluster/nodes/localhost$} => sub {
		&get_cluster_localhost_status( @_ );
	};
}

if ( $q->path_info =~ qr{^/system/dns} )
{
	include 'Zevenet::API3::System::Service::DNS';

	#  GET dns
	GET qr{^/system/dns$} => sub {
		&get_dns;
	};

	#  POST dns
	POST qr{^/system/dns$} => sub {
		&set_dns( @_ );
	};
}

if ( $q->path_info =~ qr{^/system/ssh} )
{
	include 'Zevenet::API3::System::Service::SSH';

	#  GET ssh
	GET qr{^/system/ssh$} => sub {
		&get_ssh;
	};

	#  POST ssh
	POST qr{^/system/ssh$} => sub {
		&set_ssh( @_ );
	};
}

if ( $q->path_info =~ qr{^/system/snmp} )
{
	include 'Zevenet::API3::System::Service::SNMP';

	#  GET snmp
	GET qr{^/system/snmp$} => sub {
		&get_snmp;
	};

	#  POST snmp
	POST qr{^/system/snmp$} => sub {
		&set_snmp( @_ );
	};
}

if ( $q->path_info =~ qr{^/system/ntp} )
{
	include 'Zevenet::API3::System::Service::NTP';

	#  GET ntp
	GET qr{^/system/ntp$} => sub {
		&get_ntp;
	};

	#  POST ntp
	POST qr{^/system/ntp$} => sub {
		&set_ntp( @_ );
	};
}

if ( $q->path_info =~ qr{^/system/http} )
{
	include 'Zevenet::API3::System::Service::HTTP';

	#  GET http
	GET qr{^/system/http$} => sub {
		&get_http;
	};

	#  POST http
	POST qr{^/system/http$} => sub {
		&set_http( @_ );
	};
}

if ( $q->path_info =~ qr{^/system/users} )
{
	include 'Zevenet::API3::System::User';

	my $user_re = &getValidFormat( 'user' );

	#  GET users
	GET qr{^/system/users$} => sub {
		&get_all_users;
	};

	#  GET user settings
	GET qr{^/system/users/($user_re)$} => sub {
		&get_user;
	};

	#  POST zapi user
	POST qr{^/system/users/zapi$} => sub {
		&set_user_zapi( @_ );
	};

	#  POST other user
	POST qr{^/system/users/($user_re)$} => sub {
		&set_user( @_ );
	};
}

if ( $q->path_info =~ qr{^/system/log} )
{
	include 'Zevenet::API3::System::Log';

	#  GET logs
	GET qr{^/system/logs$} => sub {
		&get_logs;
	};

	my $logs_re = &getValidFormat( 'log' );

	#  GET download log file
	GET qr{^/system/logs/($logs_re)$} => sub {
		&download_logs;
	};
}

if ( $q->path_info =~ qr{^/system/backup} )
{
	include 'Zevenet::API3::System::Backup';

	#  GET list backups
	GET qr{^/system/backup$} => sub {
		&get_backup( @_ );
	};

	#  POST create backups
	POST qr{^/system/backup$} => sub {
		&create_backup( @_ );
	};

	my $backup_re = &getValidFormat( 'backup' );

	#  GET download backups
	GET qr{^/system/backup/($backup_re)$} => sub {
		&download_backup( @_ );
	};

	#  PUT  upload backups
	PUT qr{^/system/backup/($backup_re)$} => sub {
		&upload_backup( @_ );
	};

	#  DELETE  backups
	DELETE qr{^/system/backup/($backup_re)$} => sub {
		&del_backup( @_ );
	};

	#  POST  apply backups
	POST qr{^/system/backup/($backup_re)/actions$} => sub {
		&apply_backup( @_ );
	};
}

if ( $q->path_info =~ qr{^/system/notifications} )
{
	include 'Zevenet::API3::System::Notification';

	my $alert_re  = &getValidFormat( 'notif_alert' );
	my $method_re = &getValidFormat( 'notif_method' );

	#  GET notification methods
	GET qr{^/system/notifications/methods/($method_re)$} => sub {
		&get_notif_methods( @_ );
	};

	#  POST notification methods
	POST qr{^/system/notifications/methods/($method_re)$} => sub {
		&set_notif_methods( @_ );
	};

	#  GET notification alert status
	GET qr{^/system/notifications/alerts$} => sub {
		&get_notif_alert_status( @_ );
	};

	#  GET notification alerts
	GET qr{^/system/notifications/alerts/($alert_re)$} => sub {
		&get_notif_alert( @_ );
	};

	#  POST notification alerts
	POST qr{^/system/notifications/alerts/($alert_re)$} => sub {
		&set_notif_alert( @_ );
	};

	#  POST notification alert actions
	POST qr{^/system/notifications/alerts/($alert_re)/actions$} => sub {
		&set_notif_alert_actions( @_ );
	};

	#  POST  notifications test
	POST qr{^/system/notifications/methods/email/actions$} => sub {
		&send_test_mail( @_ );
	};
}

if ( $q->path_info =~ qr{^/system} )
{
	include 'Zevenet::API3::System::Info';

	#  GET version
	GET qr{^/system/version$} => sub {
		&get_version;
	};

	my $license_re = &getValidFormat( 'license_format' );

	#  GET license
	GET qr{^/system/license/($license_re)$} => sub {
		&get_license( @_ );
	};

	#### /system/supportsave
	GET qr{^/system/supportsave$} => sub {
		&get_supportsave( @_ );
	};
}

#	IPDS
#
_ipds:

if ( $q->path_info =~ qr{/ipds/blacklist} )
{
	include 'Zevenet::API3::IPDS::Blacklist';

	my $blacklists_list      = &getValidFormat( 'blacklists_name' );
	my $blacklists_source_id = '\d+';

	# BLACKLISTS
	#  GET all blacklists
	GET qr{^/ipds/blacklists$} => sub {
		&get_blacklists_all_lists;
	};

	#  POST blacklists list
	POST qr{^/ipds/blacklists$} => sub {
		&add_blacklists_list( @_ );
	};

	#  GET blacklists lists
	GET qr{^/ipds/blacklists/($blacklists_list)$} => sub {
		&get_blacklists_list( @_ );
	};

	#  PUT blacklists list
	PUT qr{^/ipds/blacklists/($blacklists_list)$} => sub {
		&set_blacklists_list( @_ );
	};

	#  DELETE blacklists list
	DELETE qr{^/ipds/blacklists/($blacklists_list)$} => sub {
		&del_blacklists_list( @_ );
	};

	#  UPDATE a remote blacklists
	POST qr{^/ipds/blacklists/($blacklists_list)/actions$} => sub {
		&update_remote_blacklists( @_ );
	};

	#  GET a source from a blacklists
	GET qr{^/ipds/blacklists/($blacklists_list)/sources$} => sub {
		&get_blacklists_source( @_ );
	};

	#  POST a source from a blacklists
	POST qr{^/ipds/blacklists/($blacklists_list)/sources$} => sub {
		&add_blacklists_source( @_ );
	};

	#  PUT a source from a blacklists
	PUT qr{^/ipds/blacklists/($blacklists_list)/sources/($blacklists_source_id)$} =>
	  sub {
		&set_blacklists_source( @_ );
	  };

	#  DELETE a source from a blacklists
	DELETE
	  qr{^/ipds/blacklists/($blacklists_list)/sources/($blacklists_source_id)$} =>
	  sub {
		&del_blacklists_source( @_ );
	  };

	#  POST list to farm
	POST qr{^/farms/($farm_re)/ipds/blacklists$} => sub {
		&add_blacklists_to_farm( @_ );
	};

	#  DELETE list from farm
	DELETE qr{^/farms/($farm_re)/ipds/blacklists/($blacklists_list)$} => sub {
		&del_blacklists_from_farm( @_ );
	};
}

if ( $q->path_info =~ qr{/ipds/dos} )
{
	include 'Zevenet::API3::IPDS::DoS';

	my $dos_rule = &getValidFormat( 'dos_name' );

	#  GET dos settings
	GET qr{^/ipds/dos/rules$} => sub {
		&get_dos_rules( @_ );
	};

	#  GET dos settings
	GET qr{^/ipds/dos$} => sub {
		&get_dos( @_ );
	};

	#  GET dos configuration
	GET qr{^/ipds/dos/($dos_rule)$} => sub {
		&get_dos_rule( @_ );
	};

	#  POST dos settings
	POST qr{^/ipds/dos$} => sub {
		&create_dos_rule( @_ );
	};

	#  PUT dos rule
	PUT qr{^/ipds/dos/($dos_rule)$} => sub {
		&set_dos_rule( @_ );
	};

	#  DELETE dos rule
	DELETE qr{^/ipds/dos/($dos_rule)$} => sub {
		&del_dos_rule( @_ );
	};

	#  POST DoS to a farm
	POST qr{^/farms/($farm_re)/ipds/dos$} => sub {
		&add_dos_to_farm( @_ );
	};

	#  DELETE DoS from a farm
	DELETE qr{^/farms/($farm_re)/ipds/dos/($dos_rule)$} => sub {
		&del_dos_from_farm( @_ );
	};
}

&httpResponse(
			   {
				 code => 404,
				 body => {
						   message => 'Request not found',
						   error   => 'true',
				 }
			   }
);
