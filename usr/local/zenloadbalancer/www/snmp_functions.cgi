###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This library is free software; you can redistribute it and/or modify it
#     under the terms of the GNU Lesser General Public License as published
#     by the Free Software Foundation; either version 2.1 of the License, or
#     (at your option) any later version.
#
#     This library is distributed in the hope that it will be useful, but
#     WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
#     General Public License for more details.
#
#     You should have received a copy of the GNU Lesser General Public License
#     along with this library; if not, write to the Free Software Foundation,
#     Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
###############################################################################

#require "/usr/local/zenloadbalancer/www/functions.cgi";

sub setSnmpdStatus    # ($snmpd_status)
{
	# get 'true' string to start, or a 'false' string to stop
	my ( $snmpd_status ) = @_;

	my $return_code = -1;

	if ( $snmpd_status eq 'true' )
	{
		&zenlog( "Starting snmp service" );

		if ( -f $systemctl )
		{
			$return_code = system ( "$systemctl start snmpd > /dev/null" );
		}
		else
		{
			$return_code = system ( "/etc/init.d/snmpd start > /dev/null" );
		}
	}
	elsif ( $snmpd_status eq 'false' )
	{
		&zenlog( "Stopping snmp service" );

		if ( -f $systemctl )
		{
			$return_code = system ( "$systemctl stop snmpd > /dev/null" );
		}
		else
		{
			$return_code = system ( "/etc/init.d/snmpd stop > /dev/null" );
		}
	}
	else
	{
		&zenlog( "SNMP requested state is invalid" );
		return -1;
	}

	# returns 0 = DONE SUCCESSFULLY
	return $return_code;
}

sub getSnmpdStatus    # ()
{
	my $status      = `$pidof snmpd`;
	my $return_code = $?;

	# if not empty pid
	if ( $return_code == 0 )
	{
		$return_code = "true";
	}
	else
	{
		$return_code = "false";
	}

	return $return_code;
}

sub getSnmpdConfig    # ()
{
	tie my @config_file, 'Tie::File', $snmpdconfig_file;

	## agentAddress line ##
	# agentAddress udp:127.0.0.1:161
	my ( undef, $snmpd_ip, $snmpd_port ) = split ( /:/, $config_file[0] );

	## rocommunity line ##
	# rocommunity public 0.0.0.0/0
	my ( undef, $snmpd_community, $snmpd_scope ) =
	  split ( /\s+/, $config_file[1] );

	# Close file
	untie @config_file;

	my %snmpd_conf = (
					   ip        => $snmpd_ip,
					   port      => $snmpd_port,
					   community => $snmpd_community,
					   scope     => $snmpd_scope,
	);

	return ( \%snmpd_conf );
}

sub setSnmpdConfig    # ($snmpd_conf)
{
	my ( $snmpd_conf ) = @_;

	return -1 if ref $snmpd_conf ne 'HASH';

	# Open config file
	open my $config_file, '>', $snmpdconfig_file;

	if ( !$config_file )
	{
		&zenlog( "Colud not open $snmpdconfig_file: $!" );
		return -1;
	}

	if ( $snmpd_conf->{ ip } eq '*' )
	{
		$snmpd_conf->{ ip } = '0.0.0.0';
	}

	# example: agentAddress  udp:127.0.0.1:161
	# example: rocommunity public  0.0.0.0/0
	print $config_file "agentAddress udp:$snmpd_conf->{ip}:$snmpd_conf->{port}\n";
	print $config_file
	  "rocommunity $snmpd_conf->{community} $snmpd_conf->{scope}\n";
	print $config_file "includeAllDisks 10%\n";
	print $config_file "#zenlb\n";

	# Close config file
	close @config_file;

	return 0;
}

sub setSnmpdService    # ($snmpd_enabled)
{
	my ( $snmpd_enabled ) = @_;

	my $return_code = -1;

	# verify valid input
	if ( $snmpd_enabled ne 'true' && $snmpd_enabled ne 'false' )
	{
		&zenlog( "SNMP Service: status not available" );
		return $return_code;
	}

	# change snmpd status
	$return_code = &setSnmpdStatus( $snmpd_enabled );
	if ( $return_code != 0 )
	{
		&zenlog( "SNMP Status change failed" );
		return $return_code;
	}

	# perform runlevel change
	if ( $snmpd_enabled eq 'true' )
	{
		&zenlog( "Enabling snmp service" );

		if ( -f $systemctl )
		{
			$return_code = system ( "$systemctl enable snmpd > /dev/null" );
		}
		else
		{
			$return_code = system ( "$insserv snmpd" );
		}
	}
	else
	{
		&zenlog( "Disabling snmp service" );

		if ( -f $systemctl )
		{
			$return_code = system ( "$systemctl disable snmpd > /dev/null" );
		}
		else
		{
			$return_code = system ( "$insserv -r snmpd" );
		}
	}

	# show message if failed
	if ( $return_code != 0 )
	{
		&zenlog( "SNMP runlevel setup failed" );
	}
	return $return_code;
}

sub applySnmpChanges # ($snmpd_enabled, $snmpd_port, $snmpd_community, $snmpd_scope)
{
	my ( $snmpd_new ) = @_;

	my $return_code = -1;

	if ( ref $snmpd_new ne 'HASH' )
	{
		&zenlog( "Wrong argument applying snmp changes." );
		return $return_code;
	}

	## setting up valiables ##
	# if checkbox not checked set as false instead of undefined
	if ( !defined $snmpd_new->{ status } )
	{
		$snmpd_enabled = 'false';
	}

	# read current management IP
	#~ my $snmpd_ip = &GUIip();
	if ( $snmpd_new->{ ip } eq '*' )
	{
		$snmpd_ip = '0.0.0.0';
	}

	## validating some input values ##
	# check port
	if ( !&isValidPortNumber( $snmpd_new->{ port } ) )
	{
		&zenlog( "SNMP: Port out of range" );
		return $return_code;
	}

	# if $snmpd_scope is not a valid ip or subnet
	my ( $ip, $subnet ) = split ( '/', $snmpd_new->{ scope } );

	if ( &ipisok( $ip, 4 ) eq 'false' )
	{
		&zenlog( "SNMP: Invalid ip or subnet with access" );
		return $return_code;
	}
	if ( &isnumber( $subnet ) eq 'false' || $subnet < 0 || $subnet > 32 )
	{
		&zenlog( "SNMP: Invalid subnet with access" );
		return $return_code;
	}

	# SNMP arguments validated

	# get config values of snmp server
	my $snmpd_old = &getSnmpdConfig();
	$snmpd_old->{ status } = &getSnmpdStatus();

	my $conf_changed = 'false';

	# configuration/service status logic
	# setup config file if requested configuration changes
	if (    $snmpd_old->{ ip } ne $snmpd_new->{ ip }
		 || $snmpd_old->{ port } ne $snmpd_new->{ port }
		 || $snmpd_old->{ community } ne $snmpd_new->{ community }
		 || $snmpd_old->{ scope } ne $snmpd_new->{ scope } )
	{
		$return_code  = &setSnmpdConfig( $snmpd_new );
		$conf_changed = 'true';

		return $return_code if $return_code;
	}

   # if the desired snmp status is different to the current status => switch service
	if ( $snmpd_new->{ status } ne $snmpd_old->{ status } )
	{
		$return_code = &setSnmpdService( $snmpd_new->{ status } );

		if ( $return_code )
		{
			&zenlog( "SNMP failed setting the service" );
			return $return_code;
		}
	}

	# if snmp is on and want it on loading new configuration => restart server
	elsif (    $snmpd_new->{ status } eq 'true'
			&& $snmpd_old->{ status } eq 'true'
			&& $conf_changed eq 'true' )
	{
		if ( &setSnmpdStatus( 'false' ) || &setSnmpdStatus( 'true' ) )
		{
			&zenlog( "SNMP failed restarting the server" );
			return -1;
		}
	}
	return 0;
}

1;
