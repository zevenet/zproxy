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

my $configdir = &getGlobalConfiguration( 'configdir' );

=begin nd
Function: getL4FarmParam

	Returns farm parameter

Parameters:
	param - requested parameter. The options are:
		"vip": get the virtual IP
		"vipp": get the virtual port
		"status": get the status and boot status
		"mode": get the topology (or nat type)
		"scheduler": get the algorithm
		"proto": get the protocol
		"persist": get persistence
		"persisttm": get client persistence timeout
	farmname - Farm name

Returns:
	Scalar - return the parameter as a string or -1 on failure

=cut

sub getL4FarmParam    # ($param, $farm_name)
{
	my ( $param, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	open FI, "<", "$configdir/$farm_filename";
	chomp(my @content = <FI>);
	close FI;

	$output = &_getL4ParseFarmConfig( $param, undef, \@content );

	return $output;
}


=begin nd
Function: setL4FarmParam

	Writes a farm parameter

Parameters:
	param - requested parameter. The options are:
		"family": write ipv4 or ipv6
		"vip": write the virtual IP
		"vipp": write the virtual port
		"status": write the status and boot status
		"mode": write the topology (or nat type)
		"alg": write the algorithm
		"proto": write the protocol
		"persist": write persistence
		"persisttm": write client persistence timeout
	value - the new value of the given parameter of a certain farm
	farmname - Farm name

Returns:
	Scalar - return the parameter as a string or -1 on failure

=cut

sub setL4FarmParam    # ($param, $value, $farm_name)
{
	my ( $param, $value, $farm_name ) = @_;

	my $farm_filename	= &getFarmFile( $farm_name );
	my $output		= -1;
	my $srvparam		= "";

	if ( $param eq "vip" )
	{
		$output = &setL4FarmVirtualConf( $value, undef, $farm_name );
	}
	elsif ( $param eq "vipp" )
	{
		$output = &setL4FarmVirtualConf( undef, $value, $farm_name );
	}
	elsif ( $param eq "alg" )
	{
		$output = &setL4FarmAlgorithm( $value, $farm_name );
	}
	elsif ( $param eq "proto" )
	{
		$output = &setL4FarmProto( $value, $farm_name );
	}
	elsif ( $param eq "mode" )
	{
		$output = &setFarmNatType( $value, $farm_name );
	}
	elsif ( $param eq "persist" )
	{
		$output = &setL4FarmSessionType( $value, $farm_name );
	}
	elsif ( $param eq "persisttm" )
	{
		$output = &setL4FarmMaxClientTime( $value, $farm_name );
	} else
	{
		return -1;
	}

	return $output;
}


=begin nd
Function: _getL4ParseFarmConfig

	Parse the farm file configuration and read/write a certain parameter

Parameters:
	param - requested parameter. The options are "family", "vip", "vipp", "status", "mode", "alg", "proto", "persist", "presisttm"
	value - value to be changed in case of write operation, undef for read only cases
	config - reference of an array with the full configuration file

Returns:
	Scalar - return the parameter value on read or the changed value in case of write as a string or -1 in other case

=cut

sub _getL4ParseFarmConfig    # ($param, $value, $config)
{
	my ( $param, $value, $config )	= @_;
	my $output		= -1;
	my $first         = "true";

	foreach my $line( @{ $config } )
	{
		if ( $line eq "" || $first ne "true" )
		{
			break;
		}

		$first = "false";
		my @l = split ( "\;", $line );

		if ( $param eq 'proto' )
		{
			$output = $l[1];
			break;
		}

		if ( $param eq 'vip' )
		{
			$output = $l[2];
			break;
		}

		if ( $param eq 'vipp' )
		{
			$output = $l[3];
			break;
		}

		if ( $param eq 'mode' )
		{
			$output = $l[4];
			break;
		}

		if ( $param eq 'scheduler' )
		{
			$output = $l[5];
			break;
		}

		if ( $param eq 'persist' )
		{
			$output = $l[6];
			break;
		}

		if ( $param eq 'persist' )
		{
			$output = $l[7];
			break;
		}

		if ( $param eq 'status' )
		{
			if ( $l[8] ne "up" )
			{
				$output = "down";
			}
			else
			{
				$output = "up";
			}
			break;
		}
	}

	return $output;
}

=begin nd
Function: getL4FarmsPorts

	Get all port used of L4xNAT farms in up status and using a protocol

Parameters:
	protocol - protocol used by l4xnat farm

Returns:
	String - return a list with the used ports by all L4xNAT farms. Format: "portList1,portList2,..."

=cut

sub getL4FarmsPorts    # ($protocol)
{
	my $protocol = shift;

	my $port_list       = "";
	my @farms_filenames = &getFarmList();

	unless ( $#farms_filenames > -1 )
	{
		return $port_list;
	}

	foreach my $farm_filename ( @farms_filenames )
	{
		my $farm_name     = &getFarmName( $farm_filename );
		my $farm_type     = &getFarmType( $farm_name );

		next if not ( $farm_type eq "l4xnat" );

		my $farm_protocol = &getL4FarmParam( 'proto', $farm_name );

		next if not ( $protocol eq $farm_protocol );
		next if ( &getL4FarmParam( 'status', $farm_name ) ne "up" );

		my $farm_port = &getL4FarmParam( 'vipp', $farm_name );
		$farm_port = join ( ',', &getFarmPortList( $farm_port ) );
		next if not &validL4ExtPort( $farm_protocol, $farm_port );

		$port_list .= "$farm_port,";
	}

	# remove the las comma
	chop ( $port_list );

	return $port_list;
}

=begin nd
Function: loadL4Modules

	Load sip, ftp or tftp conntrack module for l4 farms

Parameters:
	protocol - protocol module to load

Returns:
	Integer - Always return 0

FIXME:
	1. The maximum number of ports, when the module is loaded, is 8
	2. Always return 0

=cut

sub loadL4Modules    # ($protocol)
{
	my $protocol = shift;

	require Zevenet::Netfilter;

	my $status    = 0;
	my $port_list = &getL4FarmsPorts( $protocol );

	if ( $protocol eq "sip" )
	{
		&removeNfModule( "nf_nat_sip" );
		&removeNfModule( "nf_conntrack_sip" );
		if ( $port_list )
		{
			&loadNfModule( "nf_conntrack_sip", "ports=\"$port_list\"" );
			&loadNfModule( "nf_nat_sip",       "" );
		}
	}
	elsif ( $protocol eq "ftp" )
	{
		&removeNfModule( "nf_nat_ftp" );
		&removeNfModule( "nf_conntrack_ftp" );
		if ( $port_list )
		{
			&loadNfModule( "nf_conntrack_ftp", "ports=\"$port_list\"" );
			&loadNfModule( "nf_nat_ftp",       "" );
		}
	}
	elsif ( $protocol eq "tftp" )
	{
		&removeNfModule( "nf_nat_tftp" );
		&removeNfModule( "nf_conntrack_tftp" );
		if ( $port_list )
		{
			&loadNfModule( "nf_conntrack_tftp", "ports=\"$port_list\"" );
			&loadNfModule( "nf_nat_tftp",       "" );
		}
	}

	return $status;
}

=begin nd
Function: validL4ExtPort

	check if the port is valid for a sip, ftp or tftp farm

Parameters:
	protocol - protocol module to load
	ports - port string

Returns:
	Integer - 1 is valid or 0 is not valid

=cut

sub validL4ExtPort    # ($farm_protocol,$ports)
{
	my ( $farm_protocol, $ports ) = @_;

	my $status = 0;

	if (    $farm_protocol eq "sip"
		 || $farm_protocol eq "ftp"
		 || $farm_protocol eq "tftp" )
	{
		if ( $ports =~ /^\d+$/ || $ports =~ /^((\d+),(\d+))+$/ )
		{
			$status = 1;
		}
	}
	return $status;
}

=begin nd
Function: sendL4ConfChange

	Run a l4xnat farm

Parameters:
	farmname - Farm name

Returns:
	Integer - Error code: 0 on success or other value on failure

FIXME:
	only used in zapi v2. Obsolet

BUG:
	same functionlity than _runL4FarmRestart and runL4FarmRestart

=cut

sub sendL4ConfChange    # ($farm_name)
{
	my $farm_name = shift;

	my $algorithm   = &getL4FarmParam( 'scheduler', $farm_name );
	my $fbootstatus = &getL4FarmParam( 'status', $farm_name );
	my $output      = 0;
	my $pidfile     = "/var/run/l4sd.pid";

	if ( $algorithm eq "leastconn" && -e "$pidfile" )
	{
		# read pid number
		open my $file, "<", "$pidfile";
		my $pid = <$file>;
		close $file;

		kill USR1 => $pid;
		$output = $?;    # FIXME
	}
	else
	{
		&zenlog( "Running L4 restart for $farm_name" );
		&_runL4FarmRestart( $farm_name, "false", "" );
	}

	return $output;      # FIXME
}

=begin nd
Function: setL4FarmSessionType

	Configure type of persistence session

Parameters:
	session - Session type. The options are: "none" not use persistence or "ip" for ip persistencia
	farmname - Farm name

Returns:
	Integer - Error code: 0 on success or other value on failure

FIXME:
	only used in zapi v2. Obsolet

BUG:
	same functionlity than _runL4FarmRestart and runL4FarmRestart

=cut

sub setL4FarmSessionType    # ($session,$farm_name)
{
	my ( $session, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = 0;
	my $i             = 0;

	require Zevenet::FarmGuardian;
	require Tie::File;

	my $farm       = &getL4FarmStruct( $farm_name );
	my $fg_enabled = ( &getFarmGuardianConf( $$farm{ name } ) )[3];
	my $fg_pid     = &getFarmGuardianPid( $farm_name );

	if ( $$farm{ status } eq 'up' )
	{
		if ( $fg_enabled eq 'true' )
		{
			kill 'STOP' => $fg_pid;
		}
	}

	&zlog( "setL4FarmSessionType: SessionType" ) if &debug;

	tie my @configfile, 'Tie::File', "$configdir\/$farm_filename";

	for my $line ( @configfile )
	{
		if ( $line =~ /^$farm_name\;/ )
		{
			my @args = split ( "\;", $line );
			$line =
			  "$args[0]\;$args[1]\;$args[2]\;$args[3]\;$args[4]\;$args[5]\;$session\;$args[7]\;$args[8];$args[9]";
			splice @configfile, $i, $line;
			$output = $?;    # FIXME
		}
		$i++;
	}
	untie @configfile;

	$farm = &getL4FarmStruct( $farm_name );

	if ( $$farm{ status } eq 'up' )
	{
		require Zevenet::Netfilter;

		my @rules;
		my $prio_server = &getL4ServerWithLowestPriority( $farm );

		foreach my $server ( @{ $$farm{ servers } } )
		{
			#~ next if $$server{ status } !~ /up|maintenance/;    # status eq fgDOWN
			next if $$farm{ lbalg } eq 'prio' && $$prio_server{ id } != $$server{ id };

			my $rule = &genIptMarkPersist( $farm, $server );

			$rule =
			  ( $$farm{ persist } eq 'none' )
			  ? &getIptRuleDelete( $rule )
			  : &getIptRuleInsert( $farm, $server, $rule );
			&applyIptRules( $rule );

			$rule = &genIptRedirect( $farm, $server );
			$rule = &getIptRuleReplace( $farm, $server, $rule );

			$output = &applyIptRules( $rule );
		}

		if ( $fg_enabled eq 'true' )
		{
			kill 'CONT' => $fg_pid;
		}
	}

	return $output;
}

=begin nd
Function: setL4FarmAlgorithm

	Set the load balancing algorithm to a farm

Parameters:
	algorithm - Load balancing algorithm. The options are: "leastconn" , "weight" or "prio"
	farmname - Farm name

Returns:
	Integer - always return 0

FIXME:
	do error control

=cut

sub setL4FarmAlgorithm    # ($algorithm,$farm_name)
{
	my ( $algorithm, $farm_name ) = @_;

	require Zevenet::FarmGuardian;
	require Tie::File;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $i             = 0;
	my $prev_alg      = &getL4FarmParam( 'scheduler', $farm_name );    # previous algorithm

	my $farm       = &getL4FarmStruct( $farm_name );
	my $fg_enabled = ( &getFarmGuardianConf( $$farm{ name } ) )[3];
	my $fg_pid     = &getFarmGuardianPid( $farm_name );

	if ( $$farm{ status } eq 'up' )
	{
		if ( $fg_enabled eq 'true' )
		{
			kill 'STOP' => $fg_pid;
		}
	}

	tie my @configfile, 'Tie::File', "$configdir\/$farm_filename";

	for my $line ( @configfile )
	{
		if ( $line =~ /^$farm_name\;/ )
		{
			my @args = split ( "\;", $line );
			$line =
			  "$args[0]\;$args[1]\;$args[2]\;$args[3]\;$args[4]\;$algorithm\;$args[6]\;$args[7]\;$args[8];$args[9]";
			splice @configfile, $i, $line;
			$output = $?;    # FIXME
		}
		$i++;
	}
	untie @configfile;
	$output = $?;            # FIXME

	$farm = &getL4FarmStruct( $farm_name );

	if ( $$farm{ status } eq 'up' )
	{
		require Zevenet::Netfilter;
		my @rules;

		my $prio_server = &getL4ServerWithLowestPriority( $farm );

		foreach my $server ( @{ $$farm{ servers } } )
		{
			my $rule;

			# weight    => leastconn or (many to many)
			# leastconn => weight
			if (    ( $prev_alg eq 'weight' && $$farm{ lbalg } eq 'leastconn' )
				 || ( $prev_alg eq 'leastconn' && $$farm{ lbalg } eq 'weight' ) )
			{
				# replace packet marking rules
				# every thing else stays the same way
				$rule = &genIptMark( $farm, $server );
				my $rule_num = &getIptRuleNumber( $rule, $$farm{ name }, $$server{ id } );
				$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );

				&applyIptRules( $rule );

				if ( $$farm{ persist } ne 'none' )    # persistence
				{
					$rule = &genIptMarkPersist( $farm, $server );
					$rule_num = &getIptRuleNumber( $rule, $$farm{ name }, $$server{ id } );
					$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );
					&applyIptRules( $rule );
				}
			}

			# prio => weight or (one to many)
			# prio => leastconn
			elsif ( ( $$farm{ lbalg } eq 'weight' || $$farm{ lbalg } eq 'leastconn' )
					&& $prev_alg eq 'prio' )
			{
				$rule = &genIptMark( $farm, $server );
				my $rule_num = &getIptRuleNumber( $rule, $$farm{ name }, $$server{ id } );

				# start not started servers
				if ( $rule_num == -1 )    # no rule was found
				{
					&_runL4ServerStart( $$farm{ name }, $$server{ id } );
					$rule = undef;        # changes are already done
				}

				# refresh already started server
				else
				{
					&_runL4ServerStop( $$farm{ name }, $$server{ id } );
					&_runL4ServerStart( $$farm{ name }, $$server{ id } );
					$rule = undef;        # changes are already done
				}
				&applyIptRules( $rule ) if defined ( $rule );
			}

			# weight    => prio or (many to one)
			# leastconn => prio
			elsif ( ( $prev_alg eq 'weight' || $prev_alg eq 'leastconn' )
					&& $$farm{ lbalg } eq 'prio' )
			{
				if ( $server == $prio_server )    # no rule was found
				{
					$rule = &genIptMark( $farm, $server );
					my $rule_num = &getIptRuleNumber( $rule, $$farm{ name }, $$server{ id } );
					$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );

					&applyIptRules( $rule ) if defined ( $rule );
				}
				else
				{
					&_runL4ServerStop( $$farm{ name }, $$server{ id } );
					$rule = undef;                # changes are already done
				}
			}
		}

		# manage l4sd
		my $l4sd_pidfile = '/var/run/l4sd.pid';
		my $l4sd         = &getGlobalConfiguration( 'l4sd' );

		if ( $$farm{ lbalg } eq 'leastconn' && -e "$l4sd" )
		{
			system ( "$l4sd >/dev/null 2>&1 &" );
		}
		elsif ( -e $l4sd_pidfile )
		{
			require Zevenet::Netfilter;
			## lock iptables use ##
			my $iptlock = &getGlobalConfiguration( 'iptlock' );
			open my $ipt_lockfile, '>', $iptlock;
			&setIptLock( $ipt_lockfile );

			# Get the binary of iptables (iptables or ip6tables)
			my $iptables_bin = &getBinVersion( $farm_name );

			my $num_lines = grep { /-m condition --condition/ }
			  `$iptables_bin --numeric --table mangle --list PREROUTING`;

			## unlock iptables use ##
			&setIptUnlock( $ipt_lockfile );
			close $ipt_lockfile;

			if ( $num_lines == 0 )
			{
				# stop l4sd
				if ( open my $pidfile, '<', $l4sd_pidfile )
				{
					my $pid = <$pidfile>;
					close $pidfile;

					# close normally
					kill 'TERM' => $pid;
					&zenlog( "l4sd ended" );
				}
				else
				{
					&zenlog( "Error opening file l4sd_pidfile: $!" ) if !defined $pidfile;
				}
			}
		}

		if ( $fg_enabled eq 'true' )
		{
			kill 'CONT' => $fg_pid;
		}
	}

	return;
}

=begin nd
Function: setL4FarmProto

	Set the protocol to a L4 farm

Parameters:
	protocol - which protocol the farm will use to work. The available options are: "all", "tcp", "udp", "sip", "ftp" and "tftp"
	farmname - Farm name

Returns:
	Integer - Error code: 0 on success or other value in failure

FIXME:
	It is necessary more error control

BUG:
	Before change to sip, ftp or tftp protocol, check if farm port is contability

=cut

sub setL4FarmProto    # ($proto,$farm_name)
{
	my ( $proto, $farm_name ) = @_;

	require Zevenet::FarmGuardian;
	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = 0;

	&zenlog( "setting 'Protocol $proto' for $farm_name farm $farm_type" );

	my $farm       = &getL4FarmStruct( $farm_name );
	my $old_proto  = $$farm{ vproto };
	my $fg_enabled = ( &getFarmGuardianConf( $$farm{ name } ) )[3];
	my $fg_pid     = &getFarmGuardianPid( $farm_name );

	if ( $$farm{ status } eq 'up' )
	{
		if ( $fg_enabled eq 'true' )
		{
			kill 'STOP' => $fg_pid;
		}
	}

	if ( $farm_type eq "l4xnat" )
	{
		require Tie::File;
		tie my @configfile, 'Tie::File', "$configdir\/$farm_filename" or return $output;
		my $i = 0;
		for my $line ( @configfile )
		{
			if ( $line =~ /^$farm_name\;/ )
			{
				my @args = split ( "\;", $line );
				if ( $proto eq "all" )
				{
					$args[3] = "*";
				}
				if ( $proto eq "sip" )
				{
					#~ $args[4] = "nat";
				}
				$line =
				  "$args[0]\;$proto\;$args[2]\;$args[3]\;$args[4]\;$args[5]\;$args[6]\;$args[7]\;$args[8];$args[9]";
				splice @configfile, $i, $line;
			}
			$i++;
		}
		untie @configfile;
	}

	$farm = &getL4FarmStruct( $farm_name );

	if ( $$farm{ status } eq 'up' )
	{
		# Remove required modules
		if ( $old_proto =~ /sip|ftp/ )
		{
			my $status = &loadL4Modules( $old_proto );
		}

		# Load required modules
		if ( $$farm{ vproto } =~ /sip|ftp/ )
		{
			my $status = &loadL4Modules( $$farm{ vproto } );
		}

		$output = &refreshL4FarmRules( $farm );

		if ( $fg_enabled eq 'true' )
		{
			kill 'CONT' => $fg_pid;
		}
	}

	return $output;
}

=begin nd
Function: setFarmNatType

	Set the NAT type for a farm

Parameters:
	nat - Type of nat. The options are: "nat" or "dnat"
	farmname - Farm name

Returns:
	Scalar - 0 on success or other value on failure

=cut

sub setFarmNatType    # ($nat,$farm_name)
{
	my ( $nat, $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = 0;

	require Zevenet::FarmGuardian;

	&zenlog( "setting 'NAT type $nat' for $farm_name farm $farm_type" );

	my $farm       = &getL4FarmStruct( $farm_name );
	my $fg_enabled = ( &getFarmGuardianConf( $$farm{ name } ) )[3];
	my $fg_pid     = &getFarmGuardianPid( $farm_name );

	if ( $$farm{ status } eq 'up' )
	{
		if ( $fg_enabled eq 'true' )
		{
			if ( $0 !~ /farmguardian/ )
			{
				kill 'STOP' => $fg_pid;
			}
		}
	}

	if ( $farm_type eq "l4xnat" )
	{
		require Tie::File;
		tie my @configfile, 'Tie::File', "$configdir\/$farm_filename";
		my $i = 0;
		for my $line ( @configfile )
		{
			if ( $line =~ /^$farm_name\;/ )
			{
				my @args = split ( "\;", $line );
				$line =
				  "$args[0]\;$args[1]\;$args[2]\;$args[3]\;$nat\;$args[5]\;$args[6]\;$args[7]\;$args[8];$args[9]";
				splice @configfile, $i, $line;
			}
			$i++;
		}
		untie @configfile;
	}

	$farm = &getL4FarmStruct( $farm_name );

	if ( $$farm{ status } eq 'up' )
	{
		require Zevenet::Netfilter;

		my @rules;
		my $prio_server = &getL4ServerWithLowestPriority( $farm );

		foreach my $server ( @{ $$farm{ servers } } )
		{
			&zlog( "server:$$server{id}" ) if &debug == 2;

			#~ next if $$server{ status } !~ /up|maintenance/;
			next if $$farm{ lbalg } eq 'prio' && $$prio_server{ id } != $$server{ id };

			my $rule;

			# get the rule 'template'
			$rule = ( $$farm{ vproto } eq 'sip' )
			  ? &genIptSourceNat( $farm, $server )    # SIP protocol
			  : &genIptMasquerade( $farm, $server );  # Masq otherwise

			# apply the desired action to the rule template
			$rule = ( $$farm{ nattype } eq 'nat' )
			  ? &getIptRuleAppend( $rule )            # append for SNAT aka NAT
			  : &getIptRuleDelete( $rule );           # delete for DNAT

			# apply rules as they are generated, so rule numbers are right
			$output = &applyIptRules( $rule );
		}

		if ( $fg_enabled eq 'true' )
		{
			if ( $0 !~ /farmguardian/ )
			{
				kill 'CONT' => $fg_pid;
			}
		}
	}

	return $output;
}

=begin nd
Function: setL4FarmMaxClientTime

	 Set the max client time of a farm

Parameters:
	ttl - Persistence Session Time to Live
	farmname - Farm name

Returns:
	Integer - 0 on success or other value on failure

=cut

sub setL4FarmMaxClientTime    # ($track,$farm_name)
{
	my ( $track, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $i             = 0;

	require Zevenet::FarmGuardian;
	require Tie::File;

	my $farm       = &getL4FarmStruct( $farm_name );
	my $fg_enabled = ( &getFarmGuardianConf( $$farm{ name } ) )[3];
	my $fg_pid     = &getFarmGuardianPid( $farm_name );

	if ( $$farm{ status } eq 'up' )
	{
		if ( $fg_enabled eq 'true' )
		{
			kill 'STOP' => $fg_pid;
		}
	}

	tie my @configfile, 'Tie::File', "$configdir\/$farm_filename";

	for my $line ( @configfile )
	{
		if ( $line =~ /^$farm_name\;/ )
		{
			my @args = split ( "\;", $line );
			$line =
			  "$args[0]\;$args[1]\;$args[2]\;$args[3]\;$args[4]\;$args[5]\;$args[6]\;$track\;$args[8];$args[9]";
			splice @configfile, $i, $line;
			$output = $?;    # FIXME
		}
		$i++;
	}
	untie @configfile;
	$output = $?;            # FIXME

	$farm = &getL4FarmStruct( $farm_name );

	if ( $$farm{ status } eq 'up' && $$farm{ persist } ne 'none' )
	{
		require Zevenet::Netfilter;

		my @rules;
		my $prio_server = &getL4ServerWithLowestPriority( $farm );

		foreach my $server ( @{ $$farm{ servers } } )
		{
			next if $$server{ status } != /up|maintenance/;
			next if $$farm{ lbalg } eq 'prio' && $$prio_server{ id } != $$server{ id };

			my $rule = &genIptMarkPersist( $farm, $server );
			my $rule_num = &getIptRuleNumber( $rule, $$farm{ name }, $$server{ id } );

			$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );

			push ( @rules, $rule );    # collect rule
		}

		require Zevenet::Netfilter;
		$output = &applyIptRules( @rules );

		if ( $fg_enabled eq 'true' )
		{
			kill 'CONT' => $fg_pid;
		}
	}

	return $output;
}

=begin nd
Function: setL4FarmVirtualConf

	Set farm virtual IP and virtual PORT

Parameters:
	vip - Farm virtual IP
	port - Farm virtual port. If the port is not sent, the port will not be changed
	farmname - Farm name

Returns:
	Scalar - 0 on success or other value on failure

=cut

sub setL4FarmVirtualConf    # ($vip,$vip_port,$farm_name)
{
	my ( $vip, $vip_port, $farm_name ) = @_;

	require Tie::File;
	require Zevenet::FarmGuardian;

	my $farm_filename = &getFarmFile( $farm_name );
	my $i             = 0;

	my $farm       = &getL4FarmStruct( $farm_name );
	my $fg_enabled = ( &getFarmGuardianConf( $$farm{ name } ) )[3];
	my $fg_pid     = &getFarmGuardianPid( $farm_name );

	if ( $$farm{ status } eq 'up' )
	{
		if ( $fg_enabled eq 'true' )
		{
			kill 'STOP' => $fg_pid;
		}
	}

	tie my @configfile, 'Tie::File', "$configdir\/$farm_filename";

	for my $line ( @configfile )
	{
		if ( $line =~ /^$farm_name\;/ )
		{
			my @args = split ( "\;", $line );
			$vip_port = $args[3] if ( ! $vip_port );
			$line =
			  "$args[0]\;$args[1]\;$vip\;$vip_port\;$args[4]\;$args[5]\;$args[6]\;$args[7]\;$args[8];$args[9]";
			splice @configfile, $i, $line;
		}
		$i++;
	}
	untie @configfile;

	$farm = &getL4FarmStruct( $farm_name );

	if ( $$farm{ status } eq 'up' )
	{
		require Zevenet::Netfilter;

		my @rules;

		foreach my $server ( @{ $$farm{ servers } } )
		{
			my $rule = &genIptMark( $farm, $server );
			my $rule_num = &getIptRuleNumber( $rule, $$farm{ name }, $$server{ id } );

			$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );

			push ( @rules, $rule );    # collect rule

			if ( $$farm{ persist } eq 'ip' )
			{
				$rule = &genIptMarkPersist( $farm, $server );
				$rule_num = &getIptRuleNumber( $rule, $$farm{ name }, $$server{ id } );

				$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );

				push ( @rules, $rule );    # collect rule
			}
		}

		&applyIptRules( @rules );

		if ( $fg_enabled eq 'true' )
		{
			kill 'CONT' => $fg_pid;
		}

		# Reload required modules
		if ( $$farm{ vproto } =~ /sip|ftp/ )
		{
			my $status = &loadL4Modules( $$farm{ vproto } );
		}
	}

	return 0;    # FIXME?
}

=begin nd
Function: getFarmPortList

	If port is multiport, it removes range port and it passes it to a port list

Parameters:
	port - Port string

Returns:
	array - return a list of ports

=cut

sub getFarmPortList    # ($fvipp)
{
	my $fvipp = shift;

	my @portlist = split ( ',', $fvipp );
	my @retportlist = ();

	if ( !grep ( /\*/, @portlist ) )
	{
		foreach my $port ( @portlist )
		{
			if ( $port =~ /:/ )
			{
				my @intlimits = split ( ':', $port );

				for ( my $i = $intlimits[0] ; $i <= $intlimits[1] ; $i++ )
				{
					push ( @retportlist, $i );
				}
			}
			else
			{
				push ( @retportlist, $port );
			}
		}
	}
	else
	{
		$retportlist[0] = '*';
	}

	return @retportlist;
}

=begin nd
Function: getL4ProtocolTransportLayer

	Return basic transport protocol used by l4 farm protocol

Parameters:
	protocol - L4xnat farm protocol

Returns:
	String - "udp" or "tcp"

=cut

sub getL4ProtocolTransportLayer
{
	my $vproto = shift;

	return
	    ( $vproto =~ /sip|tftp/ ) ? 'udp'
	  : ( $vproto eq 'ftp' )      ? 'tcp'
	  :                             $vproto;
}

=begin nd
Function: getL4FarmStruct

	Return a hash with all data about a l4 farm

Parameters:
	farmname - Farm name

Returns:
	hash ref -
		\%farm = { $name, $filename, $nattype, $lbalg, $vip, $vport, $vproto, $persist, $ttl, $proto, $status, \@servers }
		\@servers = [ \%backend1, \%backend2, ... ]

=cut

sub getL4FarmStruct
{
	my %farm;    # declare output hash

	$farm{ name } = shift;    # input: farm name

	require Zevenet::Farm::L4xNAT::Backend;

	$farm{ filename } = &getFarmFile( $farm{ name } );
	my $config = &getL4FarmPlainInfo( $farm{ name } );

	$farm{ nattype }  = &_getL4ParseFarmConfig( 'mode', undef, $config );
	$farm{ mode }     = $farm{ nattype };
	$farm{ lbalg }    = &_getL4ParseFarmConfig( 'scheduler', undef, $config );
	$farm{ vip }      = &_getL4ParseFarmConfig( 'vip', undef, $config );
	$farm{ vport }    = &_getL4ParseFarmConfig( 'vipp', undef, $config );
	$farm{ vproto }   = &_getL4ParseFarmConfig( 'proto', undef, $config );
	$farm{ persist }  = &_getL4ParseFarmConfig( 'persist', undef, $config );
	$farm{ ttl }      = &_getL4ParseFarmConfig( 'persisttm', undef, $config );
	$farm{ proto }    = &getL4ProtocolTransportLayer( $farm{ vproto } );
	$farm{ status }   = &_getL4ParseFarmConfig( 'status', undef, $config );
	$farm{ logs }   = &getL4FarmLogs( $farm{ name } );
	$farm{ servers }  = &_getL4FarmParseServers( $config );

	# replace port * for all the range
	if ( $farm{ vport } eq '*' )
	{
		$farm{ vport } = '0:65535';
	}

	if ( $farm{ lbalg } eq 'weight' )
	{
		&getL4BackendsWeightProbability( \%farm );
	}

	return \%farm;    # return a hash reference
}

=begin nd
Function: doL4FarmProbability

	Create in the passed hash a new key called "prob". In this key is saved total weight of all backends

Parameters:
	farm - farm hash ref. It is a hash with all information about the farm

Returns:
	none - .

=cut

sub doL4FarmProbability
{
	my $farm = shift;    # input: farm reference

	$$farm{ prob } = 0;

	foreach my $server_ref ( @{ $$farm{ servers } } )
	{
		if ( $$server_ref{ status } eq 'up' )
		{
			$$farm{ prob } += $$server_ref{ weight };
		}
	}

  #~ &zenlog( "doL4FarmProbability($$farm{ name }) => prob:$$farm{ prob }" ); ######
}

=begin nd
Function: refreshL4FarmRules

	Refresh all iptables rule for a l4 farm

Parameters:
	farm - Farm hash ref. It is a hash with all information about the farm

Returns:
	Integer - Error code: 0 on success or -1 on failure

FIXME:
	Send signal to l4sd to reload configuration

=cut

sub refreshL4FarmRules    # AlgorithmRules
{
	my $farm = shift;     # input: reference to farm structure

	require Zevenet::Netfilter;

	my $prio_server;
	my @rules;
	my $return_code = 0;

	$prio_server = &getL4ServerWithLowestPriority( $farm );

	# refresh backends probability values
	&getL4BackendsWeightProbability( $farm ) if ( $$farm{ lbalg } eq 'weight' );

	## lock iptables use ##
	my $iptlock = &getGlobalConfiguration( 'iptlock' );
	open ( my $ipt_lockfile, '>', $iptlock );

	unless ( $ipt_lockfile )
	{
		&zenlog( "Could not open $iptlock: $!" );
		return 1;
	}

	# get new rules
	foreach my $server ( @{ $$farm{ servers } } )
	{
		# skip cycle for servers not running
		next if ( $$farm{ lbalg } eq 'prio' && $$server{ id } != $$prio_server{ id } );

		my $rule;
		my $rule_num;

		# refresh marks
		$rule = &genIptMark( $farm, $server );

		$rule =
		  ( $$farm{ lbalg } eq 'prio' )
		  ? &getIptRuleReplace( $farm, undef,   $rule )
		  : &getIptRuleReplace( $farm, $server, $rule );

		$return_code |= &applyIptRules( $rule );

		if ( $$farm{ persist } ne 'none' )    # persistence
		{
			$rule = &genIptMarkPersist( $farm, $server );

			$rule =
			  ( $$farm{ lbalg } eq 'prio' )
			  ? &getIptRuleReplace( $farm, undef,   $rule )
			  : &getIptRuleReplace( $farm, $server, $rule );

			$return_code |= &applyIptRules( $rule );
		}

		# redirect
		$rule = &genIptRedirect( $farm, $server );

		$rule =
		  ( $$farm{ lbalg } eq 'prio' )
		  ? &getIptRuleReplace( $farm, undef,   $rule )
		  : &getIptRuleReplace( $farm, $server, $rule );

		$return_code |= &applyIptRules( $rule );

		if ( $$farm{ nattype } eq 'nat' )    # nat type = nat
		{
			if ( $$farm{ vproto } eq 'sip' )
			{
				$rule = &genIptSourceNat( $farm, $server );
			}
			else
			{
				$rule = &genIptMasquerade( $farm, $server );
			}

			$rule =
			  ( $$farm{ lbalg } eq 'prio' )
			  ? &getIptRuleReplace( $farm, undef,   $rule )
			  : &getIptRuleReplace( $farm, $server, $rule );

			$return_code |= &applyIptRules( $rule );
		}

		# reset connection mark on udp
		if ( $$farm{ proto } eq 'udp' )
		{
			foreach my $be ( @{ $$farm{ servers } } )
			{
				&resetL4FarmBackendConntrackMark( $be );
			}
		}

	}

	## unlock iptables use ##
	&setIptUnlock( $ipt_lockfile );
	close $ipt_lockfile;

	&reloadL4FarmLogsRule( $$farm{ name } );

	# apply new rules
	return $return_code;
}

=begin nd
Function: reloadL4FarmsSNAT

	Reload iptables rules of all SNAT L4 farms

Parameters:
	farm - Farm hash ref. It is a hash with all information about the farm

Returns:
	none - .

FIXME:
	Send signal to l4sd to reload configuration

=cut

sub reloadL4FarmsSNAT
{
	require Zevenet::Farm::Core;
	require Zevenet::Farm::Base;
	require Zevenet::Netfilter;

	for my $farm_name ( &getFarmNameList() )
	{
		my $farm_type = &getFarmType( $farm_name );

		next if $farm_type ne 'l4xnat';
		next if &getL4FarmParam( 'status', $farm_name ) ne 'up';

		my $l4f_conf = &getL4FarmStruct( $farm_name );

		next if $$l4f_conf{ nattype } ne 'nat';

		foreach my $server ( @{ $$l4f_conf{ servers } } )
		{
			my $rule;

			if ( $$l4f_conf{ vproto } eq 'sip' )
			{
				$rule = &genIptSourceNat( $l4f_conf, $server );
			}
			else
			{
				$rule = &genIptMasquerade( $l4f_conf, $server );
			}

			$rule = &getIptRuleReplace( $l4f_conf, $server, $rule );

			#~ push ( @{ $$rules{ t_snat } }, $rule );
			&applyIptRules( $rule );
		}
	}
}



=begin nd
Function: getL4FarmLogs

	Return if the farm has activated the log tracking

Parameters:
	farmname - Farm name

Returns:
	scalar - return "enable" if log is enabled or "false" if it is not

=cut

sub getL4FarmLogs    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = "false";

	open FI, "<$configdir/$farm_filename";
	while ( my $line = <FI> )
	{
		if ( $line ne "" )
		{
			my @line_a = split ( "\;", $line );
			$output = $line_a[9] // "false";
			chomp ( $output );
			last;
		}
	}
	close FI;

	return $output;
}


sub setL4FarmLogs
{
	my $farmname = shift;
	my $action = shift; 	# true or false
	my $out;

	# execute action
	&reloadL4FarmLogsRule( $farmname, $action );

	# write configuration
	require Tie::File;
	my $farm_filename = &getFarmFile( $farmname );
	tie my @configfile, 'Tie::File', "$configdir\/$farm_filename";

	my $i = 0;
	for my $line ( @configfile )
	{
		if ( $line =~ /^$farmname\;/ )
		{
			my @args = split ( "\;", $line );
			$line =
			  "$args[0]\;$args[1]\;$args[2]\;$args[3]\;$args[4]\;$args[5]\;$args[6]\;$args[7]\;$args[8]\;$action";
			splice @configfile, $i, $line;
		}
		$i++;
	}
	untie @configfile;

	return $out;
}


# if action is false, the rule won't be started
# if farm is in down status, the farm won't be started

sub reloadL4FarmLogsRule
{
	my ( $farmname, $action ) = @_;

	require Zevenet::Netfilter;

	my $error;
	my $table = "mangle";
	my $ipt_hook = "FORWARD";
	my $log_chain = "LOG_CONNS";
	my $bin = &getBinVersion( $farmname );
	my $farm = &getL4FarmStruct( $farmname );

	my $comment = "conns,$farmname";


	# delete current rules
	&runIptDeleteByComment( $comment, $log_chain, $table );

	# delete chain if it was the last rule
	my @ipt_list = `$bin -S $log_chain -t $table 2>/dev/null`;
	unless ( scalar @ipt_list > 1 )
	{
		&iptSystem( "$bin -D $ipt_hook -t $table -j $log_chain" );
		&iptSystem( "$bin -X $log_chain -t $table" );
	}

	return if ( $action eq 'false' );
	return if ( &getL4FarmParam( 'status', $farmname ) ne 'up' );

	my $comment_tag = "-m comment --comment \"$comment\"";
	my $log_tag = "-j LOG --log-prefix \"conn_track,$farmname \" --log-level 4";

	# create chain if it does not exist
	if ( &iptSystem( "$bin -L $log_chain -t $table" ) )
	{
		$error = &iptSystem( "$bin -N $log_chain -t $table" );
		$error = &iptSystem( "$bin -A $ipt_hook -t $table -j $log_chain" );
	}

	my %farm_st        = %{ &getL4FarmStruct( $farmname ) };
	foreach my $bk ( @{ $farm_st{ servers } } )
	{
		my $mark = "-m mark --mark $bk->{tag}";
		$error |= &iptSystem( "$bin -A $log_chain -t $table $mark $log_tag $comment_tag" );
	}

	#~ return $error;
}

=begin nd
Function: getL4FarmPlainInfo

	Return the L4 farm text configuration

Parameters:
	farm_name - farm name to get the status

Returns:
	Scalar - Reference of the file content in plain text

=cut

sub getL4FarmPlainInfo		# ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );

	open FI, "<", "$configdir/$farm_filename";
	chomp(my @content = <FI>);
	close FI;

	return \@content;
}


1;
