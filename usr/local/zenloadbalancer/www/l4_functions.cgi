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

### Debug ###
#~ use v5.14;
#~ use strict;

use Tie::File;
use Data::Dumper;

# End Debug ###

require "/usr/local/zenloadbalancer/www/farmguardian_functions.cgi";
require "/usr/local/zenloadbalancer/www/nf_functions.cgi";
require "/usr/local/zenloadbalancer/www/networking_functions.cgi";
require "/usr/local/zenloadbalancer/www/farms_functions.cgi";

my $configdir = &getGlobalConfiguration('configdir');


=begin nd
Function: ismport

	Check if the string is a valid multiport definition
	
Parameters:
	port - Multiport string

Returns:
	String - "true" if port has a correct format or "false" if port has a wrong format
	
FIXME: 
	Define regexp in check_functions.cgi and use it here
	
=cut
sub ismport    # ($string)
{
	my $string = shift;

	chomp ( $string );
	if ( $string eq "*" )
	{
		return "true";
	}
	elsif ( $string =~ /^([1-9][0-9]*|[1-9][0-9]*\:[1-9][0-9]*)(,([1-9][0-9]*|[1-9][0-9]*\:[1-9][0-9]*))*$/ )
	{
		return "true";
	}
	else
	{
		return "false";
	}
}


=begin nd
Function: checkmport

	Check if the port has more than 1 port
	
Parameters:
	port - Port string

Returns:
	String - "true" if port string has more then one port or "false" if port has only a port
	
=cut
sub checkmport    # ($port)
{
	my $port = shift;

	if ( $port =~ /\,|\:|\*/ )
	{
		return "true";
	}
	else
	{
		return "false";
	}
}


=begin nd
Function: getL4FarmsPorts

	Get all port used by L4xNAT farms with a protocol
	
Parameters:
	protocol - protocol used by l4xnat farm

Returns:
	String - return a list with the used ports by all L4xNAT farms. Format: "portList1,portList2,..."
	
=cut
sub getL4FarmsPorts    # ($protocol)
{
	my $protocol = shift;

	my $first           = 1;
	my $port_list       = "";
	my @farms_filenames = &getFarmList();

	if ( $#farms_filenames > -1 )
	{
		foreach my $farm_filename ( @farms_filenames )
		{
			my $farm_name     = &getFarmName( $farm_filename );
			my $farm_type     = &getFarmType( $farm_name );
			my $farm_protocol = &getFarmProto( $farm_name );

			if ( ( $farm_type eq "l4xnat" ) && ( $protocol eq $farm_protocol ) )
			{
				my $farm_port = &getFarmVip( "vipp", $farm_name );

				if ( &validL4ExtPort( $farm_protocol, $farm_port ) )
				{
					if ( $first == 1 )
					{
						$port_list = $farm_port;
						$first     = 0;
					}
					else
					{
						$port_list = "$port_list,$farm_port";
					}
				}
			}
		}
	}
	
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

	my $status    = 0;
	my $port_list = &getL4FarmsPorts( $protocol );

	if ( $protocol eq "sip" )
	{
		&removeNfModule( "nf_nat_sip" );
		&removeNfModule( "nf_conntrack_sip" );
		&loadNfModule( "nf_conntrack_sip", "ports=\"$port_list\"" );
		&loadNfModule( "nf_nat_sip",       "" );
	}
	elsif ( $protocol eq "ftp" )
	{
		&removeNfModule( "nf_nat_ftp" );
		&removeNfModule( "nf_conntrack_ftp" );
		&loadNfModule( "nf_conntrack_ftp", "ports=\"$port_list\"" );
		&loadNfModule( "nf_nat_ftp",       "" );
	}
	elsif ( $protocol eq "tftp" )
	{
		&removeNfModule( "nf_nat_tftp" );
		&removeNfModule( "nf_conntrack_tftp" );
		&loadNfModule( "nf_conntrack_tftp", "ports=\"$port_list\"" );
		&loadNfModule( "nf_nat_tftp",       "" );
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
Function: runL4FarmRestart

	Restart a l4xnat farm
	
Parameters:
	farmname - Farm name
	writeconf - Write start on configuration file
	changes - This field lets to do the changes without stop the farm. The possible values are: "", blank for stop and start the farm, or "hot" for not stop the farm before run it

Returns:
	Integer - Error code: 0 on success or other value on failure

FIXME:
	writeconf is a obsolet parameter

=cut
sub runL4FarmRestart    # ($farm_name,$writeconf,$type)
{
	my ( $farm_name, $writeconf, $type ) = @_;

	my $algorithm   = &getFarmAlgorithm( $farm_name );
	my $fbootstatus = &getFarmBootStatus( $farm_name );
	my $output      = 0;
	my $pidfile     = "/var/run/l4sd.pid";

	if (    $algorithm eq "leastconn"
		 && $fbootstatus eq "up"
		 && $writeconf eq "false"
		 && $type eq "hot"
		 && -e "$pidfile" )
	{
		open FILE, "<$pidfile";
		my $pid = <FILE>;
		close FILE;

		kill USR1 => $pid;
		$output = $?;    # FIXME
	}
	else
	{
		&_runL4FarmStop( $farm_name, $writeconf );
		$output = &_runL4FarmStart( $farm_name, $writeconf );
	}

	return $output;
}


=begin nd
Function: _runL4FarmRestart

	Restart a l4xnat farm
	
Parameters:
	farmname - Farm name
	writeconf - Write start on configuration file
	changes - This field lets to do the changes without stop the farm. The possible values are: "", blank for stop and start the farm, or "hot" for not stop the farm before run it

Returns:
	Integer - Error code: 0 on success or other value on failure

FIXME:
	writeconf is a obsolet parameter
	$type parameter never is used

BUG:
	DUPLICATED FUNCTION, do the same than &runL4FarmRestart function.
	
=cut
sub _runL4FarmRestart    # ($farm_name,$writeconf,$type)
{
	my ( $farm_name, $writeconf, $type ) = @_;

	my $algorithm   = &getFarmAlgorithm( $farm_name );
	my $fbootstatus = &getFarmBootStatus( $farm_name );
	my $output      = 0;
	my $pidfile     = "/var/run/l4sd.pid";

	if (    $algorithm eq "leastconn"
		 && $fbootstatus eq "up"
		 && $writeconf eq "false"
		 && $type eq "hot"
		 && -e $pidfile )
	{
		open FILE, "<$pidfile";
		my $pid = <FILE>;
		close FILE;

		# reload config file
		kill USR1 => $pid;
		$output = $?;    # FIXME
	}
	else
	{
		&_runFarmStop( $farm_name, $writeconf );
		$output = &_runFarmStart( $farm_name, $writeconf );
	}

	return $output;
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
sub sendL4ConfChange     # ($farm_name)
{
	my $farm_name = shift;

	my $algorithm   = &getFarmAlgorithm( $farm_name );
	my $fbootstatus = &getFarmBootStatus( $farm_name );
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
			  "$args[0]\;$args[1]\;$args[2]\;$args[3]\;$args[4]\;$args[5]\;$session\;$args[7]\;$args[8]";
			splice @configfile, $i, $line;
			$output = $?;    # FIXME
		}
		$i++;
	}
	untie @configfile;

	$farm = &getL4FarmStruct( $farm_name );

	if ( $$farm{ status } eq 'up' )
	{
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
Function: getL4FarmSessionType

	Get type of persistence session
	
Parameters:
	farmname - Farm name

Returns:
	Scalar - "none" not use persistence, "ip" for ip persistencia or -1 on failure
	
BUG:
	DUPLICATE with getL4FarmPersistence
	Not used 
	Use get and set with same name

=cut
sub getL4FarmSessionType    # ($farm_name)
{
	my $farm_name = shift;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $first         = "true";

	open FI, "<$configdir/$farm_filename";

	while ( my $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line = split ( "\;", $line );
			$output = $line[6];
		}
	}
	close FI;

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

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $i             = 0;
	my $prev_alg      = getL4FarmAlgorithm( $farm_name );    # previous algorithm

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
			  "$args[0]\;$args[1]\;$args[2]\;$args[3]\;$args[4]\;$algorithm\;$args[6]\;$args[7]\;$args[8]";
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
		my $l4sd = &getGlobalConfiguration('l4sd');

		if ( $$farm{ lbalg } eq 'leastconn' && -e "$l4sd" )
		{
			system ( "$l4sd >/dev/null &" );
		}
		elsif ( -e $l4sd_pidfile )
		{
			## lock iptables use ##
			my $iptlock = &getGlobalConfiguration('iptlock');
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
Function: getL4FarmAlgorithm

	Get the load balancing algorithm for a farm
	
Parameters:
	farmname - Farm name

Returns:
	Scalar - "leastconn" , "weight", "prio" or -1 on failure
	
=cut
sub getL4FarmAlgorithm    # ($farm_name)
{
	my $farm_name = shift;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $first         = 'true';

	open FI, "<", "$configdir/$farm_filename";

	while ( my $line = <FI> )
	{
		if ( $line ne '' && $first eq 'true' )
		{
			$first = 'false';
			my @line = split ( "\;", $line );
			$output = $line[5];
		}
	}
	close FI;

	return $output;
}


=begin nd
Function: setFarmProto

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
sub setFarmProto    # ($proto,$farm_name)
{
	my ( $proto, $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = 0;

	&zenlog( "setting 'Protocol $proto' for $farm_name farm $farm_type" );

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

	if ( $farm_type eq "l4xnat" )
	{
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
				  "$args[0]\;$proto\;$args[2]\;$args[3]\;$args[4]\;$args[5]\;$args[6]\;$args[7]\;$args[8]";
				splice @configfile, $i, $line;
			}
			$i++;
		}
		untie @configfile;
	}

	$farm = &getL4FarmStruct( $farm_name );

	if ( $$farm{ status } eq 'up' )
	{
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
Function: getFarmNatType

	Get the NAT type for a L4 farm
	
Parameters:
	farmname - Farm name

Returns:
	Scalar - "nat", "dnat" or -1 on failure
	
=cut
sub getFarmNatType    # ($farm_name)
{
	my $farm_name = shift;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	if ( $farm_type eq "l4xnat" )
	{
		open FI, "<", "$configdir/$farm_filename";
		my $first = "true";
		while ( my $line = <FI> )
		{
			if ( $line ne "" && $first eq "true" )
			{
				$first = "false";
				my @line = split ( "\;", $line );
				$output = $line[4];
			}
		}
		close FI;
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
	my $output        = -1;

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
		tie my @configfile, 'Tie::File', "$configdir\/$farm_filename";
		my $i = 0;
		for my $line ( @configfile )
		{
			if ( $line =~ /^$farm_name\;/ )
			{
				my @args = split ( "\;", $line );
				$line =
				  "$args[0]\;$args[1]\;$args[2]\;$args[3]\;$nat\;$args[5]\;$args[6]\;$args[7]\;$args[8]";
				splice @configfile, $i, $line;
				$output = $?;    # FIXME
			}
			$i++;
		}
		untie @configfile;
		$output = $?;            # FIXME
	}

	$farm = &getL4FarmStruct( $farm_name );

	if ( $$farm{ status } eq 'up' )
	{
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
Function: getL4FarmPersistence

	Get type of persistence session for a l4 farm
	
Parameters:
	farmname - Farm name

Returns:
	Scalar - "none" not use persistence, "ip" for ip persistencia or -1 on failure
	
=cut
sub getL4FarmPersistence    # ($farm_name)
{
	my $farm_name = shift;

	my $farm_filename = &getFarmFile( $farm_name );
	my $persistence   = -1;
	my $first         = "true";

	open FI, "<", "$configdir/$farm_filename";

	while ( my $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line = split ( "\;", $line );
			$persistence = $line[6];
		}
	}
	close FI;

	return $persistence;
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
			  "$args[0]\;$args[1]\;$args[2]\;$args[3]\;$args[4]\;$args[5]\;$args[6]\;$track\;$args[8]";
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

		$output = &applyIptRules( @rules );

		if ( $fg_enabled eq 'true' )
		{
			kill 'CONT' => $fg_pid;
		}
	}

	return $output;
}


=begin nd
Function: getL4FarmMaxClientTime

	 Get the max client time of a farm
	
Parameters:
	farmname - Farm name

Returns:
	Integer - Time to Live (TTL) or -1 on failure
	
FIXME:
	The returned value must to be a integer. Fit output like in the description
	
=cut
sub getL4FarmMaxClientTime    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $first         = "true";
	my @max_client_time;

	open FI, "<", "$configdir/$farm_filename";

	while ( my $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line = split ( "\;", $line );
			@max_client_time = $line[7];
		}
	}
	close FI;

	return @max_client_time;
}


=begin nd
Function: getL4FarmServers

	 Get all backends and theris configuration 
	
Parameters:
	farmname - Farm name

Returns:
	Array - one backed per line. The line format is: "index;ip;port;mark;weight;priority;status"
	
FIXME:
	Return as array of hash refs
	
=cut
sub getL4FarmServers    # ($farm_name)
{
	my $farm_name = shift;

	my $farm_filename = &getFarmFile( $farm_name );
	my $sindex        = 0;
	my @servers;

	open FI, "<", "$configdir/$farm_filename"
	  or &zenlog( "Error opening file $configdir/$farm_filename: $!" );

	while ( my $line = <FI> )
	{
		chomp ( $line );

		if ( $line =~ /^\;server\;/ )
		{
			$line =~ s/^\;server/$sindex/g;    #, $line;
			push ( @servers, $line );
			$sindex++;
		}
	}
	close FI;

	chomp @servers;

	return @servers;
}


=begin nd
Function: getL4BackendEstConns

	Get all ESTABLISHED connections for a backend
	 
Parameters:
	farmname - Farm name
	ip_backend - IP backend
	netstat - Conntrack -L output

Returns:
	array - Return all ESTABLISHED conntrack lines for the backend
	
FIXME:
	dnat and nat regexp is duplicated
		
=cut
sub getL4BackendEstConns    # ($farm_name,$ip_backend,@netstat)
{
	my ( $farm_name, $ip_backend, @netstat ) = @_;

	my $fvip  = &getFarmVip( "vip",  $farm_name );
	my $fvipp = &getFarmVip( "vipp", $farm_name );
	my $proto = &getFarmProto( $farm_name );
	my $nattype   = &getFarmNatType( $farm_name );
	my @fportlist = &getFarmPortList( $fvipp );
	my $regexp    = "";
	my @nets      = ();

	if ( $fportlist[0] !~ /\*/ )
	{
		$regexp = "\(" . join ( '|', @fportlist ) . "\)";
	}
	else
	{
		$regexp = "\.*";
	}

	if ( $nattype eq "dnat" )
	{
		if ( $proto eq "sip" || $proto eq "all" || $proto eq "tcp" )
		{
			# i.e. 
			# tcp      6 431998 ESTABLISHED src=192.168.0.168 dst=192.168.100.241 sport=40130 dport=81 src=192.168.100.254 dst=192.168.100.241 sport=80 dport=40130 [ASSURED] mark=523 use=1
			#protocol				 status		      client                         vip                                                           vport          backend_ip                   (vip, but can change)    backend_port
			push (
				@nets,
				&getNetstatFilter(
					   "tcp", "",
					   "\.* ESTABLISHED src=\.* dst=$fvip \.* dport=$regexp \.*src=$ip_backend \.*",
					   "", @netstat
				)
			);
		}
		if ( $proto eq "sip" || $proto eq "all" || $proto eq "udp" )
		{
			push (
				   @nets,
				   &getNetstatFilter(
									"udp", "",
									"\.* src=\.* dst=$fvip \.* dport=$regexp .*src=$ip_backend \.*",
									"", @netstat
				   )
			);
		}
	}
	else
	{
		if ( $proto eq "sip" || $proto eq "all" || $proto eq "tcp" )
		{
			push (
				@nets,
				&getNetstatFilter(
					"tcp",
					"",
					"\.*ESTABLISHED src=\.* dst=$fvip sport=\.* dport=$regexp \.*src=$ip_backend \.*",
					"",
					@netstat
				)
			);
		}
		if ( $proto eq "sip" || $proto eq "all" || $proto eq "udp" )
		{
			push (
				   @nets,
				   &getNetstatFilter(
									"udp", "",
									"\.* src=\.* dst=$fvip \.* dport=$regexp .*src=$ip_backend \.*",
									"", @netstat
				   )
			);
		}
	}

	return @nets;
}


=begin nd
Function: getL4FarmEstConns

	Get all ESTABLISHED connections for a farm
	 
Parameters:
	farmname - Farm name
	netstat - Conntrack -L output

Returns:
	array - Return all ESTABLISHED conntrack lines for a farm

FIXME:
	dnat and nat regexp is duplicated

=cut
sub getL4FarmEstConns    # ($farm_name,@netstat)
{
	my ( $farm_name, @netstat ) = @_;

	my $proto     = &getFarmProto( $farm_name );
	my $nattype   = &getFarmNatType( $farm_name );
	my $fvip      = &getFarmVip( "vip", $farm_name );
	my $fvipp     = &getFarmVip( "vipp", $farm_name );
	my @fportlist = &getFarmPortList( $fvipp );
	my $regexp    = "";
	my @nets      = ();

	if ( $fportlist[0] !~ /\*/ )
	{
		$regexp = "\(" . join ( '|', @fportlist ) . "\)";
	}
	else
	{
		$regexp = "\.*";
	}

	my @content = &getFarmBackendStatusCtl( $farm_name );
	my @backends = &getFarmBackendsStatus( $farm_name, @content );

	foreach ( @backends )
	{
		chomp($_);
		my @backends_data = split ( ";", $_ );
		if ( $backends_data[4] eq "up" )
		{
			my $ip_backend = $backends_data[0];
			if ( $nattype eq "dnat" )
			{
				if ( $proto eq "sip" || $proto eq "all" || $proto eq "tcp" )
				{
					push (
						 @nets,
						 &getNetstatFilter(
								"tcp", "",
								"\.* ESTABLISHED src=\.* dst=$fvip \.* dport=$regexp .*src=$ip_backend \.*",
								"", @netstat
						 )
					);
				}
				if ( $proto eq "sip" || $proto eq "all" || $proto eq "udp" )
				{
					push (
						   @nets,
						   &getNetstatFilter(
											"udp", "",
											"\.* src=\.* dst=$fvip \.* dport=$regexp .*src=$ip_backend \.*",
											"", @netstat
						   )
					);
				}
			}
			else
			{
				if ( $proto eq "sip" || $proto eq "all" || $proto eq "tcp" )
				{
					push (
						 @nets,
						 &getNetstatFilter(
								"tcp", "",
								"\.* ESTABLISHED src=\.* dst=$fvip \.* dport=$regexp .*src=$ip_backend \.*",
								"", @netstat
						 )
					);
				}
				if ( $proto eq "sip" || $proto eq "all" || $proto eq "udp" )
				{
					push (
						@nets,
						&getNetstatFilter(
							   "udp", "",
							   "\.* src=\.* dst=$fvip \.* dport=$regexp .*src=$ip_backend",
							   "", @netstat
						)
					);
				}
			}
		}
	}
	return @nets;
}


=begin nd
Function: getL4BackendSYNConns

	Get all SYN connections for a backend. This connection are called "pending". UDP protocol doesn't have pending concept 
	 
Parameters:
	farmname - Farm name
	ip_backend - IP backend
	netstat - Conntrack -L output

Returns:
	array - Return all SYN conntrack lines for a backend of a farm

FIXME:
	dnat and nat regexp is duplicated
	
=cut
sub getL4BackendSYNConns    # ($farm_name,$ip_backend,@netstat)
{
	my ( $farm_name, $ip_backend, @netstat ) = @_;

	my $proto     = &getFarmProto( $farm_name );
	my $nattype   = &getFarmNatType( $farm_name );
	my $fvip      = &getFarmVip( "vip", $farm_name );
	my $fvipp     = &getFarmVip( "vipp", $farm_name );
	my @fportlist = &getFarmPortList( $fvipp );
	my $regexp    = "";
	my @nets      = ();

	if ( $fportlist[0] !~ /\*/ )
	{
		$regexp = "\(" . join ( '|', @fportlist ) . "\)";
	}
	else
	{
		$regexp = "\.*";
	}

	if ( $nattype eq "dnat" )
	{
		if ( $proto eq "sip" || $proto eq "all" || $proto eq "tcp" )
		{
			push (
				   @nets,
				   &getNetstatFilter(
						   "tcp", "",
						   "\.* SYN\.* src=\.* dst=$fvip \.* dport=$regexp \.* src=$ip_backend \.*",
						   "", @netstat
				   )
			);
		}
		# udp doesn't have pending connections
	}
	else
	{
		if ( $proto eq "sip" || $proto eq "all" || $proto eq "tcp" )
		{
			push (
				   @nets,
				   &getNetstatFilter(
						   "tcp", "",
						   "\.* SYN\.* src=\.* dst=$fvip \.* dport=$regexp \.* src=$ip_backend \.*",
						   "", @netstat
				   )
			);
		}
		# udp doesn't have pending connections
	}

	return @nets;
}


=begin nd
Function: getL4FarmSYNConns

	Get all SYN connections for a farm. This connection are called "pending". UDP protocol doesn't have pending concept 
	 
Parameters:
	farmname - Farm name
	netstat - Conntrack -L output

Returns:
	array - Return all SYN conntrack lines for a farm

FIXME:
	dnat and nat regexp is duplicated
	
=cut
sub getL4FarmSYNConns    # ($farm_name,@netstat)
{
	my ( $farm_name, @netstat ) = @_;

	my $fvip  = &getFarmVip( "vip",  $farm_name );
	my $fvipp = &getFarmVip( "vipp", $farm_name );
	my $proto = &getFarmProto( $farm_name );
	my $nattype   = &getFarmNatType( $farm_name );
	my @fportlist = &getFarmPortList( $fvipp );
	my $regexp    = "";
	my @nets      = ();

	if ( $fportlist[0] !~ /\*/ )
	{
		$regexp = "\(" . join ( '|', @fportlist ) . "\)";
	}
	else
	{
		$regexp = "\.*";
	}

	my @content = &getFarmBackendStatusCtl( $farm_name ); 
	my @backends = &getFarmBackendsStatus( $farm_name, @content );
					   
	# tcp      6 299 ESTABLISHED src=192.168.0.186 dst=192.168.100.241 sport=56668 dport=80 src=192.168.0.186 dst=192.168.100.241 sport=80 dport=56668 [ASSURED] mark=517 use=2
	foreach ( @backends )
	{
		my @backends_data = split ( ";", $_ );
		chomp(@backends_data);
		
		if ( $backends_data[4] eq "up" )
		{
			my $ip_backend = $backends_data[0];

			if ( $nattype eq "dnat" )
			{
				if ( $proto eq "sip" || $proto eq "all" || $proto eq "tcp" )
				{
					push (
						   @nets,
						   &getNetstatFilter(
								   "tcp", "",
								   "\.* SYN\.* src=\.* dst=$fvip \.* dport=$regexp \.* src=$ip_backend \.*",
								   "", @netstat
						   )
					);
				}
				# udp doesn't have pending connections
			}
			else
			{
				if ( $proto eq "sip" || $proto eq "all" || $proto eq "tcp" )
				{
					push (
						   @nets,
						   &getNetstatFilter(
								   "tcp", "",
								   "\.* SYN\.* src=\.* dst=$fvip \.* dport=$regexp \.* src=$ip_backend \.*",
								   "", @netstat
						   )
					);
				}
				# udp doesn't have pending connections
			}
		}
	}

	return @nets;
}


=begin nd
Function: getL4FarmBootStatus

	Return the farm status at boot zevenet
	 
Parameters:
	farmname - Farm name

Returns:
	scalar - return "down" if the farm not run at boot or "up" if the farm run at boot

=cut
sub getL4FarmBootStatus    # ($farm_name)
{
	my $farm_name = shift;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = "down";
	my $first         = "true";

	open FI, "<$configdir/$farm_filename";

	while ( my $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line_a = split ( "\;", $line );
			$output = $line_a[8];
			chomp ( $output );
		}
	}
	close FI;

	return $output;
}


=begin nd
Function: _runL4FarmStart

	Run a l4xnat farm
	
Parameters:
	farmname - Farm name
	writeconf - write this change in configuration status "true" or omit it "false"

Returns:
	Integer - return 0 on success or different of 0 on failure
	
FIXME: 
	delete writeconf parameter. It is obsolet
	
=cut
sub _runL4FarmStart    # ($farm_name,$writeconf)
{
	my $farm_name = shift;    # input
	my $writeconf = shift;    # input

	&zlog( "Starting farm $farm_name" ) if &debug == 2;

	my $status = 0;           # output

	&zenlog( "_runL4FarmStart << farm_name:$farm_name writeconf:$writeconf" )
	  if &debug;

	# initialize a farm struct
	my $farm = &getL4FarmStruct( $farm_name );

	if ( $writeconf eq "true" )
	{
		tie my @configfile, 'Tie::File', "$configdir\/$$farm{ filename }";
		foreach ( @configfile )
		{
			s/\;down/\;up/g;
			last;
		}
		untie @configfile;
	}

	my $l4sd = &getGlobalConfiguration('l4sd');

	# Load L4 scheduler if needed
	if ( $$farm{ lbalg } eq 'leastconn' && -e "$l4sd" )
	{
		system ( "$l4sd >/dev/null &" );
	}

	# Load required modules
	if ( $$farm{ vproto } =~ /sip|ftp/ )
	{
		&loadL4Modules( $$farm{ vproto } );
	}

	my $rules;
	my $lowest_prio;
	my $server_prio;    # reference to the selected server for prio algorithm

	&zenlog( "_runL4FarmStart :: farm:" . Dumper( $farm ) ) if &debug == 2;

	## Set ip rule mark ##
	my $ip_bin = &getGlobalConfiguration('ip_bin');
	&zenlog( "farm vip: $farm->{ vip }" );
	my $vip_if_name = &getInterfaceOfIp( $farm->{ vip } );
	&zenlog( "vip_if_name: $vip_if_name" );
	my $vip_if = &getInterfaceConfig( $vip_if_name );
	&zenlog( "name: $vip_if->{ name } - type: $vip_if->{ type } - parent: $vip_if->{ parent }" );
	my $table_if = ( $vip_if->{ type } eq 'virtual' )? $vip_if->{ parent }: $vip_if->{ name };

	foreach my $server ( @{ $$farm{ servers } } )
	{
		&zenlog( "_runL4FarmStart :: server:$server->{id}" ) if &debug;

		my $backend_rules;

		## Set ip rule mark ##
		my $ip_cmd = "$ip_bin rule add fwmark $server->{ tag } table table_$table_if";
		&logAndRun( $ip_cmd );

		# go to next cycle if server must not be up or not a least connection algorithm
		#~ if ( !    $$server{ status } =~ /up|maintenance/
		#~ || $$farm{ lbalg } eq 'leastconn' )
		#~ {
		#~ next;
		#~ }

		# TMP: leastconn dynamic backend status check
		if ( $$farm{ lbalg } =~ /weight|leastconn/ )
		{
			$backend_rules = &getL4ServerActionRules( $farm, $server, 'on' );

			push ( @{ $$rules{ t_mangle_p } }, @{ $$backend_rules{ t_mangle_p } } );
			push ( @{ $$rules{ t_mangle } },   @{ $$backend_rules{ t_mangle } } );
			push ( @{ $$rules{ t_nat } },      @{ $$backend_rules{ t_nat } } );
			push ( @{ $$rules{ t_snat } },     @{ $$backend_rules{ t_snat } } );
		}
		elsif ( $$farm{ lbalg } eq 'prio' && $$server{ status } ne 'fgDOWN' )
		{
			# find the lowest priority server
			if ( $$server{ priority } ne ''
				 && ( $$server{ priority } < $lowest_prio || !defined $lowest_prio ) )
			{
				$server_prio = $server;
				$lowest_prio = $$server{ priority };
			}
		}
	}

	# prio only apply rules to one server
	if ( $server_prio && $$farm{ lbalg } eq 'prio' )
	{
		system ( "echo 10 > /proc/sys/net/netfilter/nf_conntrack_udp_timeout_stream" );
		system ( "echo 5 > /proc/sys/net/netfilter/nf_conntrack_udp_timeout" );

		$rules = &getL4ServerActionRules( $farm, $server_prio, 'on' );
	}

	# insert the save rule, then insert on top the restore rule
	&setIptConnmarkSave( $farm_name, 'true' );
	&setIptConnmarkRestore( $farm_name, 'true' );

	## lock iptables use ##
	my $iptlock = &getGlobalConfiguration('iptlock');
	open ( my $ipt_lockfile, '>', $iptlock );

	unless ( $ipt_lockfile )
	{
		&zenlog("Could not open $iptlock: $!");
		return 1;
	}

	for my $table ( qw(t_mangle_p t_mangle t_nat t_snat) )
	{
		$status = &applyIptRules( @{ $$rules{ $table } } );
		return $status if $status;
	}

	## unlock iptables use ##
	&setIptUnlock( $ipt_lockfile );
	close $ipt_lockfile;

	# Enable IP forwarding
	&setIpForward( 'true' );

	# Enable active l4 file
	if ( $status == 0 )
	{
		my $piddir = &getGlobalConfiguration('piddir');
		open my $fi, '>', "$piddir\/$$farm{name}\_l4xnat.pid";
		close $fi;
	}

	return $status;
}


=begin nd
Function: _runL4FarmStop

	Stop a l4xnat farm
	
Parameters:
	farmname - Farm name
	writeconf - write this change in configuration status "true" or omit it "false"

Returns:
	Integer - return 0 on success or other value on failure
	
FIXME: 
	delete writeconf parameter. It is obsolet
	
=cut
sub _runL4FarmStop    # ($farm_name,$writeconf)
{
	my ( $farm_name, $writeconf ) = @_;

	&zlog( "Stopping farm $farm_name" ) if &debug == 2;

	my $farm_filename = &getFarmFile( $farm_name );
	my $status;       # output

	if ( $writeconf eq 'true' )
	{
		tie my @configfile, 'Tie::File', "$configdir\/$farm_filename";
		foreach ( @configfile )
		{
			s/\;up/\;down/g;
			last;     # run only for the first line
		}
		untie @configfile;
	}

	## lock iptables use ##
	my $iptlock = &getGlobalConfiguration('iptlock');
	open ( my $ipt_lockfile, '>', $iptlock );

	unless ( $ipt_lockfile )
	{
		&zenlog("Could not open $iptlock: $!");
		return 1;
	}

	&setIptLock( $ipt_lockfile );

	# Disable rules
	my @allrules;

	@allrules = &getIptList( $farm_name, "mangle", "PREROUTING" );
	$status =
	  &deleteIptRules( $farm_name,   "farm", $farm_name, "mangle",
					   "PREROUTING", @allrules );

	@allrules = &getIptList( $farm_name, "nat", "PREROUTING" );
	$status = &deleteIptRules( $farm_name,   "farm", $farm_name, "nat",
							   "PREROUTING", @allrules );

	@allrules = &getIptList( $farm_name, "nat", "POSTROUTING" );
	$status =
	  &deleteIptRules( $farm_name, "farm", $farm_name, "nat", "POSTROUTING",
					   @allrules );

	## unlock iptables use ##
	&setIptUnlock( $ipt_lockfile );
	close $ipt_lockfile;

	# Disable active l4xnat file
	my $piddir = &getGlobalConfiguration('piddir');
	unlink ( "$piddir\/$farm_name\_l4xnat.pid" );
	if ( -e "$piddir\/$farm_name\_l4xnat.pid" )
	{
		$status = -1;
	}

	## Delete ip rule mark ##
	my $farm = &getL4FarmStruct( $farm_name );
	my $ip_bin = &getGlobalConfiguration('ip_bin');
	my $vip_if_name = &getInterfaceOfIp( $farm->{ vip } );
	my $vip_if = &getInterfaceConfig( $vip_if_name );
	my $table_if = ( $vip_if->{ type } eq 'virtual' )? $vip_if->{ parent }: $vip_if->{ name };

	foreach my $server ( @{ $$farm{ servers } } )
	{
		my $ip_cmd = "$ip_bin rule del fwmark $server->{ tag } table table_$table_if";
		&logAndRun( $ip_cmd );
	}
	## Delete ip rule mark END ##

	&setIptConnmarkRestore( $farm_name );
	&setIptConnmarkSave( $farm_name );

	return $status;
}


=begin nd
Function: runL4FarmCreate

	Create a l4xnat farm
	
Parameters:
	vip - Virtual IP
	port - Virtual port. In l4xnat it ls possible to define multiport using ',' for add ports and ':' for ranges
	farmname - Farm name

Returns:
	Integer - return 0 on success or other value on failure
	
=cut
sub runL4FarmCreate    # ($vip,$farm_name,$vip_port)
{
	my ( $vip, $farm_name, $vip_port ) = @_;

	my $output    = -1;
	my $farm_type = 'l4xnat';

	$vip_port = 80 if not defined $vip_port;

	open FO, ">$configdir\/$farm_name\_$farm_type.cfg";
	print FO "$farm_name\;tcp\;$vip\;$vip_port\;nat\;weight\;none\;120\;up\n";
	close FO;
	$output = $?;      # FIXME

	my $piddir = &getGlobalConfiguration('piddir');
	if ( !-e "$piddir/${farm_name}_$farm_type.pid" )
	{
		# Enable active l4xnat file
		open FI, ">$piddir\/$farm_name\_$farm_type.pid";
		close FI;
	}

	&_runL4FarmStart( $farm_name );

	return $output;    # FIXME
}


=begin nd
Function: getL4FarmVip

	Returns farm vip or farm port
		
Parameters:
	tag - requested parameter. The options are "vip"for virtual ip or "vipp" for virtual port
	farmname - Farm name

Returns:
	Scalar - return vip, port of farm or -1 on failure
	
FIXME
	vipps parameter is only used in tcp farms. Soon this parameter will be obsolet
			
=cut
sub getL4FarmVip       # ($info,$farm_name)
{
	my ( $info, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $first         = 'true';
	my $output        = -1;

	open FI, "<", "$configdir/$farm_filename";

	while ( my $line = <FI> )
	{
		if ( $line ne '' && $first eq 'true' )
		{
			$first = 'false';
			my @line_a = split ( "\;", $line );

			if ( $info eq 'vip' )   { $output = $line_a[2]; }
			if ( $info eq 'vipp' )  { $output = $line_a[3]; }
			if ( $info eq 'vipps' ) { $output = "$line_a[2]\:$line_a[3]"; }
		}
	}
	close FI;

	return $output;
}


=begin nd
Function: setL4FarmVirtualConf

	Set farm virtual IP and virtual PORT
		
Parameters:
	vip - Farm virtual IP
	port - Farm virtual port
	farmname - Farm name

Returns:
	Scalar - 0 on success or other value on failure
	
=cut
sub setL4FarmVirtualConf    # ($vip,$vip_port,$farm_name)
{
	my ( $vip, $vip_port, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $stat          = -1;
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
			$line =
			  "$args[0]\;$args[1]\;$vip\;$vip_port\;$args[4]\;$args[5]\;$args[6]\;$args[7]\;$args[8]";
			splice @configfile, $i, $line;
			$stat = $?;    # FIXME
		}
		$i++;
	}
	untie @configfile;
	$stat = $?;            # FIXME

	$farm = &getL4FarmStruct( $farm_name );

	if ( $$farm{ status } eq 'up' )
	{
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
	}

	return $stat;
}


=begin nd
Function: setL4FarmServer

	Edit a backend or add a new one if the id is not found
		
Parameters:
	id - Backend id
	ip - Backend IP
	port - Backend port
	weight - Backend weight. The backend with more weight will manage more connections 
	priority - The priority of this backend (between 1 and 9). Higher priority backends will be used more often than lower priority ones
	farmname - Farm name

Returns:
	Integer - return 0 on success or -1 on failure

Returns:
	Scalar - 0 on success or other value on failure
	
=cut
sub setL4FarmServer    # ($ids,$rip,$port,$weight,$priority,$farm_name)
{
	my ( $ids, $rip, $port, $weight, $priority, $farm_name, $max_conns ) = @_;

	&zenlog(
		"setL4FarmServer << ids:$ids rip:$rip port:$port weight:$weight priority:$priority farm_name:$farm_name max_conns:$max_conns"
	) if &debug;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = 0;                            # output: error code
	my $found_server  = 'false';
	my $i             = 0;                            # server ID
	my $l             = 0;                            # line index

	my $farm       = &getL4FarmStruct( $farm_name );
	my $fg_enabled = ( &getFarmGuardianConf( $$farm{ name } ) )[3];
	my $fg_pid     = &getFarmGuardianPid( $farm_name );

	$weight ||= 1;
	$priority ||= 1;

	if ( $$farm{ status } eq 'up' )
	{
		if ( $fg_enabled eq 'true' )
		{
			kill 'STOP' => $fg_pid;
		}
	}

	tie my @contents, 'Tie::File', "$configdir\/$farm_filename";

	# edit the backed line if found
	foreach my $line ( @contents )
	{
		if ( $line =~ /^\;server\;/ && $found_server eq 'false' )
		{
			if ( $i eq $ids )
			{
				my @aline = split ( ';', $line );
				my $dline = "\;server\;$rip\;$port\;$aline[4]\;$weight\;$priority\;up\;$max_conns\n";

				splice @contents, $l, 1, $dline;
				$output       = $?;       # FIXME
				$found_server = 'true';
			}
			else
			{
				$i++;
			}
		}
		$l++;
	}

	my $mark = undef;

	# add a new backend if not found
	if ( $found_server eq 'false' )
	{
		$mark = &getNewMark( $farm_name );
		push ( @contents, "\;server\;$rip\;$port\;$mark\;$weight\;$priority\;up\;$max_conns\n" );
		$output = $?;    # FIXME
	}
	untie @contents;
	### end editing config file ###

	$farm = &getL4FarmStruct( $farm_name );    # FIXME: start using it earlier

	if ( $$farm{ status } eq 'up' )
	{
		# enabling new server
		if ( $found_server eq 'false' )
		{
			if ( $$farm{ lbalg } eq 'weight' || $$farm{ lbalg } eq 'leastconn' )
			{
				$output |= &_runL4ServerStart( $farm_name, $ids );
			}

			## Set ip rule mark ##
			my $ip_bin = &getGlobalConfiguration('ip_bin');
			my $vip_if_name = &getInterfaceOfIp( $farm->{ vip } );
			my $vip_if = &getInterfaceConfig( $vip_if_name );
			my $table_if = ( $vip_if->{ type } eq 'virtual' )? $vip_if->{ parent }: $vip_if->{ name };

			my $ip_cmd = "$ip_bin rule add fwmark $mark table table_$table_if";
			&logAndRun( $ip_cmd );
			## Set ip rule mark END ##
		}

		&refreshL4FarmRules( $farm );

		if ( $fg_enabled eq 'true' )
		{
			kill 'CONT' => $fg_pid;
		}
	}

	return $output;
}


=begin nd
Function: runL4FarmServerDelete

	Delete a backend from a l4 farm
		
Parameters:
	backend - Backend id
	farmname - Farm name

Returns:
	Scalar - 0 on success or other value on failure
	
=cut
sub runL4FarmServerDelete    # ($ids,$farm_name)
{
	my ( $ids, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );

	my $output       = 0;
	my $found_server = 'false';
	my $i            = 0;
	my $l            = 0;

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

	if ( $$farm{ lbalg } eq 'weight' || $$farm{ lbalg } eq 'leastconn' )
	{
		$output |= &_runL4ServerStop( $farm_name, $ids ) if $$farm{ status } eq 'up';
	}

	tie my @contents, 'Tie::File', "$configdir\/$farm_filename";

	foreach my $line ( @contents )
	{
		if ( $line =~ /^\;server\;/ && $found_server eq 'false' )
		{
			if ( $i eq $ids )
			{
				my @sdata = split ( "\;", $line );
				$found_server = 'true';

				splice @contents, $l, 1,;
			}
			else
			{
				$i++;
			}
		}
		$l++;
	}
	untie @contents;

	my $server = $$farm{ servers }[$ids];
	$farm = &getL4FarmStruct( $farm_name );

	# disabling server
	if ( $found_server eq 'true' && $$farm{ status } eq 'up' )
	{
		splice @{ $$farm{ servers } }, $ids, 1;    # remove server from structure

		if ( $$farm{ lbalg } eq 'weight' || $$farm{ lbalg } eq 'prio' )
		{
			$output |= &refreshL4FarmRules( $farm );

			# clear conntrack for udp farms
			if ( $$farm{ proto } eq 'udp' )
			{
				&resetL4FarmBackendConntrackMark( $server );
			}
		}

		## Remove ip rule mark ##
		my $ip_bin = &getGlobalConfiguration('ip_bin');
		my $vip_if_name = &getInterfaceOfIp( $farm->{ vip } );
		my $vip_if = &getInterfaceConfig( $vip_if_name );
		my $table_if = ( $vip_if->{ type } eq 'virtual' )? $vip_if->{ parent }: $vip_if->{ name };

		my $ip_cmd = "$ip_bin rule del fwmark $server->{ tag } table table_$table_if";
		&logAndRun( $ip_cmd );
		## Remove ip rule mark END ##
	}

	if ( $$farm{ status } eq 'up' )
	{
		if ( $fg_enabled eq 'true' )
		{
			kill 'CONT' => $fg_pid;
		}
	}

	return $output;
}


=begin nd
Function: getL4FarmBackendsStatus

	function that return the status information of a farm:
	ip, port, backendstatus, weight, priority, clients
		
Parameters:
	farmname - Farm name

Returns:
	Array - one backed per line. The line format is: "ip;port;weight;priority;status"
	
FIXME:
	Change output to hash	
		
=cut
sub getL4FarmBackendsStatus    # ($farm_name,@content)
{
	my ( $farm_name, @content ) = @_;

	my @backends_data;         # output

	foreach my $server ( @content )
	{
		my @serv = split ( "\;", $server );
		my $port = $serv[3];
		if ( $port eq "" )
		{
			$port = &getFarmVip( "vipp", $farm_name );
		}
		push ( @backends_data, "$serv[2]\;$port\;$serv[5]\;$serv[6]\;$serv[7]" );
	}

	return @backends_data;
}


=begin nd
Function: setL4FarmBackendStatus

	Set backend status for a l4 farm
		
Parameters:
	farmname - Farm name
	backend - Backend id
	status - Backend status. The possible values are: "up" or "down"

Returns:
	Integer - 0 on success or other value on failure
	
=cut
sub setL4FarmBackendStatus    # ($farm_name,$server_id,$status)
{
	my ( $farm_name, $server_id, $status ) = @_;

	my %farm = %{ &getL4FarmStruct( $farm_name ) };

	my $output   = 0;
	my $line_num = 0;         # line index tracker
	my $serverid = 0;         # server index tracker

	&zenlog(
		"setL4FarmBackendStatus(farm_name:$farm_name,server_id:$server_id,status:$status)"
	);

	my $farm        = &getL4FarmStruct( $farm_name );
	my $fg_enabled  = ( &getFarmGuardianConf( $$farm{ name } ) )[3];
	my $caller      = ( caller ( 2 ) )[3];
	my $stopping_fg = ( $caller =~ /runFarmGuardianStop/ );
	my $fg_pid      = &getFarmGuardianPid( $farm_name );

	#~ &zlog("(caller(2))[3]:$caller");

	if ( $$farm{ status } eq 'up' )
	{
		if ( $fg_enabled eq 'true' && !$stopping_fg )
		{
			if ( $0 !~ /farmguardian/ )
			{
				kill 'STOP' => $fg_pid;
			}
		}
	}

	# load farm configuration file
	tie my @configfile, 'Tie::File', "$configdir\/$farm{filename}";

	# look for $server_id backend
	foreach my $line ( @configfile )
	{
		if ( $line =~ /\;server\;/ )
		{
			if ( $serverid eq $server_id )
			{
				# change status in configuration file
				my @lineargs = split ( "\;", $line );
				$lineargs[7] = $status;
				$configfile[$line_num] = join ( "\;", @lineargs );
			}
			$serverid++;
		}
		$line_num++;
	}
	untie @configfile;

	$farm{ servers } = undef;
	#~ %farm = undef;

	%farm   = %{ &getL4FarmStruct( $farm_name ) };
	my %server = %{ $farm{ servers }[$server_id] };

	# do no apply rules if the farm is not up
	if ( $farm{ status } eq 'up' )
	{
		$output |= &refreshL4FarmRules( \%farm );

		if ( $status eq 'fgDOWN' && $farm{ persist } eq 'ip' )
		{
			my $recent_file = "/proc/net/xt_recent/_$farm{name}_$server{tag}_sessions";

			if ( open ( my $file, '>', $recent_file ) )
			{
				print $file "/\n";    # flush recent file!!
				close $file;
			}
			else
			{
				&zenlog( "Could not open file $recent_file: $!" );
			}
		}

		if ( $fg_enabled eq 'true' && !$stopping_fg )
		{
			if ( $0 !~ /farmguardian/ )
			{
				kill 'CONT' => $fg_pid;
			}
		}
	}

	$farm{ servers }  = undef;
	#~ %farm             = undef;
	$$farm{ servers } = undef;
	$farm             = undef;

	return $output;
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

	#~ if ( $portlist[0] !~ /\*/ )
	if ( ! grep ( /\*/, @portlist ) )
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
Function: getL4FarmBackendStatusCtl

	Returns backends information lines
		
Parameters:
	farmname - Farmname 

Returns:
	Array - Each line has the next format: ";server;ip;port;mark;weight;priority;status"
	
Bugfix:
	DUPLICATED, do same than getL4FarmServers
		
=cut
sub getL4FarmBackendStatusCtl    # ($farm_name)
{
	my $farm_name     = shift;
	my $farm_filename = &getFarmFile( $farm_name );
	my @output;

	open my $farm_file, '<', "$configdir\/$farm_filename";
	@output = grep { /^\;server\;/ } <$farm_file>;
	close $farm_file;

	chomp @output;

	return @output;
}


=begin nd
Function: setL4NewFarmName

	Function that renames a farm
		
Parameters:
	newfarmname - New farm name 
	farmname - Farm name 

Returns:
	Array - Each line has the next format: ";server;ip;port;mark;weight;priority;status"
	
Bugfix:
	DUPLICATED, do same than getL4FarmServers
		
=cut
sub setL4NewFarmName    # ($farm_name,$new_farm_name)
{
	my ( $farm_name, $new_farm_name ) = @_;

	my $farm_filename     = &getFarmFile( $farm_name );
	my $farm_type         = &getFarmType( $farm_name );
	my $new_farm_filename = "$new_farm_name\_$farm_type.cfg";
	my $output            = 0;
	my $status            = &getFarmStatus( $farm_name );

	# previous farm info
	my $prev_farm = &getL4FarmStruct( $farm_name );

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

	for ( @configfile )
	{
		s/^$farm_name\;/$new_farm_name\;/g;
	}
	untie @configfile;

	my $piddir = &getGlobalConfiguration('piddir');
	rename ( "$configdir\/$farm_filename", "$configdir\/$new_farm_filename" ) or $output = -1;
	if ( -f "$piddir\/$farm_name\_$farm_type.pid" )
	{
		rename ( "$piddir\/$farm_name\_$farm_type.pid",
			 "$piddir\/$new_farm_name\_$farm_type.pid" ) or $output = -1;
	}	

	# Rename fw marks for this farm
	&renameMarks( $farm_name, $new_farm_name );

	$farm = &getL4FarmStruct( $new_farm_name );
	my $apply_farm = $farm;
	$apply_farm = $prev_farm if $$farm{ lbalg } eq 'prio';

	if ( $$farm{ status } eq 'up' )
	{
		my @rules;

		my $prio_server = &getL4ServerWithLowestPriority( $$farm{ name } )
		  if ( $$farm{ lbalg } eq 'prio' );

		# refresh backends probability values
		&getL4BackendsWeightProbability( $farm ) if ( $$farm{ lbalg } eq 'weight' );

		# get new rules
		foreach my $server ( @{ $$farm{ servers } } )
		{
			# skip cycle for servers not running
			#~ next if ( $$server{ status } !~ /up|maintenance/ );

			next if ( $$farm{ lbalg } eq 'prio' && $$server{ id } != $$prio_server{ id } );

			my $rule;
			my $rule_num;

			# refresh marks
			$rule = &genIptMark( $prev_farm, $server );

			$rule_num =
			  ( $$farm{ lbalg } eq 'prio' )
			  ? &getIptRuleNumber( $rule, $$apply_farm{ name } )
			  : &getIptRuleNumber( $rule, $$apply_farm{ name }, $$server{ id } );
			$rule = &genIptMark( $farm, $server );
			$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );
			push ( @rules, $rule );

			if ( $$farm{ persist } ne 'none' )    # persistence
			{
				$rule = &genIptMarkPersist( $prev_farm, $server );
				$rule_num =
				  ( $$farm{ lbalg } eq 'prio' )
				  ? &getIptRuleNumber( $rule, $$apply_farm{ name } )
				  : &getIptRuleNumber( $rule, $$apply_farm{ name }, $$server{ id } );
				$rule = &genIptMarkPersist( $farm, $server );
				$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );
				push ( @rules, $rule );
			}

			# redirect
			$rule = &genIptRedirect( $prev_farm, $server );
			$rule_num =
			  ( $$farm{ lbalg } eq 'prio' )
			  ? &getIptRuleNumber( $rule, $$apply_farm{ name } )
			  : &getIptRuleNumber( $rule, $$apply_farm{ name }, $$server{ id } );
			$rule = &genIptRedirect( $farm, $server );
			$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );
			push ( @rules, $rule );

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

				$rule_num =
				  ( $$farm{ lbalg } eq 'prio' )
				  ? &getIptRuleNumber( $rule, $$apply_farm{ name } )
				  : &getIptRuleNumber( $rule, $$apply_farm{ name }, $$server{ id } );

				if ( $$farm{ vproto } eq 'sip' )
				{
					$rule = &genIptSourceNat( $farm, $server );
				}
				else
				{
					$rule = &genIptMasquerade( $farm, $server );
				}

				$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );
				push ( @rules, $rule );
			}
		}

		if ( $fg_enabled eq 'true' )
		{
			if ( $0 !~ /farmguardian/ )
			{
				kill 'CONT' => $fg_pid;
			}
		}

		# apply new rules
		$output = &applyIptRules( @rules );
	}

	return $output;
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

	$farm{ filename } = &getFarmFile( $farm{ name } );
	$farm{ nattype }  = &getFarmNatType( $farm{ name } );
	$farm{ lbalg }    = &getL4FarmAlgorithm( $farm{ name } );
	$farm{ vip }      = &getL4FarmVip( 'vip', $farm{ name } );
	$farm{ vport }    = &getL4FarmVip( 'vipp', $farm{ name } );
	$farm{ vproto }   = &getFarmProto( $farm{ name } );
	$farm{ persist }  = &getL4FarmPersistence( $farm{ name } );
	$farm{ ttl }      = ( &getL4FarmMaxClientTime( $farm{ name } ) )[0];
	$farm{ proto }    = &getL4ProtocolTransportLayer( $farm{ vproto } );
	$farm{ status }   = &getFarmStatus( $farm{ name } );
	$farm{ servers }  = [];

	foreach my $server_line ( &getL4FarmServers( $farm{ name } ) )
	{
		push ( @{ $farm{ servers } }, &getL4ServerStruct( \%farm, $server_line ) );
	}

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
Function: getL4ServerStruct

	Return a hash with all data about a backend in a l4 farm
		
Parameters:
	farmname - Farm name
	backend - Backend id

Returns:
	hash ref - 
		\%backend = { $id, $vip, $vport, $tag, $weight, $priority, $status, $rip = $vip }
	
=cut
sub getL4ServerStruct
{
	my $farm        = shift;
	my $server_line = shift;    # input example: ;0;192.168.101.252;80;0x20a;1;1;up

	my @server_args = split ( "\;", $server_line );    # split server line
	chomp ( @server_args );

	# server args example: ( 0, 192.168.101.252, 80, 0x20a, 1, 1 ,up )
	my %server;                                        # output hash

	$server{ id }       = shift @server_args;          # input 0
	$server{ vip }      = shift @server_args;          # input 1
	$server{ vport }    = shift @server_args;          # input 2
	$server{ tag }      = shift @server_args;          # input 3
	$server{ weight }   = shift @server_args;          # input 4
	$server{ priority } = shift @server_args;          # input 5
	$server{ status }   = shift @server_args;          # input 6
	$server{ max_conns } = shift @server_args // 0;    # input 7
	$server{ rip }      = $server{ vip };

	if ( $server{ vport } ne '' && $$farm{ proto } ne 'all' )
	{
		if ( &ipversion( $server{ rip } ) == 4 )
		{
			$server{ rip } = "$server{vip}\:$server{vport}";
		}
		elsif ( &ipversion( $server{ rip } ) == 6 )
		{
			$server{ rip } = "[$server{vip}]\:$server{vport}";
		}
	}

	return \%server;    # return reference
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
Function: getL4ServerActionRules

	???
		
Parameters:
	farm - Farm hash ref. It is a hash with all information about the farm
	backend - Backend id
	switch - "on" or "off" ???

Returns:
	???
	
=cut
sub getL4ServerActionRules
{
	my $farm   = shift;    # input: farm reference
	my $server = shift;    # input: server reference
	my $switch = shift;    # input: on/off

	my $rules = &getIptRulesStruct();
	my $rule;

	## persistence rules ##
	if ( $$farm{ persist } ne 'none' )
	{
		# remove if the backend is not under maintenance
		# but if algorithm is set to prio remove anyway
		if (
			 $switch eq 'on'
			 || ( $switch eq 'off'
				  && ( $$farm{ lbalg } eq 'prio' || $$server{ status } ne 'maintenance' ) )
		  )
		{
			$rule = &genIptMarkPersist( $farm, $server );

			$rule = ( $switch eq 'off' )
			  ? &getIptRuleDelete( $rule )    # delete
			  : &getIptRuleInsert( $farm, $server, $rule );    # insert second

			push ( @{ $$rules{ t_mangle_p } }, $rule );
		}
	}

	## dnat (redirect) rules ##
	$rule = &genIptRedirect( $farm, $server );

	$rule = ( $switch eq 'off' )
	  ? &getIptRuleDelete( $rule )                             # delete
	  : &getIptRuleAppend( $rule );

	push ( @{ $$rules{ t_nat } }, $rule );

	## rules for source nat or nat ##
	if ( $$farm{ nattype } eq 'nat' )
	{
		if ( $$farm{ vproto } eq 'sip' )
		{
			$rule = &genIptSourceNat( $farm, $server );
		}
		else
		{
			$rule = &genIptMasquerade( $farm, $server );
		}

		$rule = ( $switch eq 'off' )
		  ? &getIptRuleDelete( $rule )    # delete
		  : &getIptRuleAppend( $rule );

		push ( @{ $$rules{ t_snat } }, $rule );
	}

	## packet marking rules ##
	$rule = &genIptMark( $farm, $server );

	$rule = ( $switch eq 'off' )
	  ? &getIptRuleDelete( $rule )        # delete
	  : &getIptRuleInsert( $farm, $server, $rule );    # insert second

	push ( @{ $$rules{ t_mangle } }, $rule );

	return $rules;
}


=begin nd
Function: _runL4ServerStart

	called from setL4FarmBackendStatus($farm_name,$server_id,$status)
	Run rules to enable a backend
		
Parameters:
	farmname - Farm name
	backend - Backend id

Returns:
	Integer - Error code: 0 on success or other value on failure 
	
=cut
sub _runL4ServerStart    # ($farm_name,$server_id)
{
	my $farm_name = shift;    # input: farm name string
	my $server_id = shift;    # input: server id number

	my $status = 0;
	my $rules;

	&zenlog( "_runL4ServerStart << farm_name:$farm_name server_id:$server_id" )
	  if &debug;

	my $fg_enabled = ( &getFarmGuardianConf( $farm_name ) )[3];

	# if calling function is setL4FarmAlgorithm
	my $caller             = ( caller ( 2 ) )[3];
	my $changing_algorithm = ( $caller =~ /setL4FarmAlgorithm/ );
	my $setting_be         = ( $caller =~ /setFarmServer/ );
	my $fg_pid             = &getFarmGuardianPid( $farm_name );

	#~ &zlog("(caller(2))[3]:$caller");

	if ( $fg_enabled eq 'true' && !$changing_algorithm && !$setting_be )
	{
		kill 'STOP' => $fg_pid;
	}

	# initialize a farm struct
	my %farm   = %{ &getL4FarmStruct( $farm_name ) };
	my %server = %{ $farm{ servers }[$server_id] };

	## Applying all rules ##
	$rules = &getL4ServerActionRules( \%farm, \%server, 'on' );

	$status |= &applyIptRules( @{ $$rules{ t_mangle_p } } );
	$status |= &applyIptRules( @{ $$rules{ t_mangle } } );
	$status |= &applyIptRules( @{ $$rules{ t_nat } } );
	$status |= &applyIptRules( @{ $$rules{ t_snat } } );
	## End applying rules ##

	if ( $fg_enabled eq 'true' && !$changing_algorithm && !$setting_be )
	{
		kill 'CONT' => $fg_pid;
	}

	return $status;
}


=begin nd
Function: _runL4ServerStop

	Delete rules to disable a backend
		
Parameters:
	farmname - Farm name
	backend - Backend id

Returns:
	Integer - Error code: 0 on success or other value on failure 
	
=cut
sub _runL4ServerStop    # ($farm_name,$server_id)
{
	my $farm_name = shift;    # input: farm name string
	my $server_id = shift;    # input: server id number

	my $output = 0;
	my $rules;

	my $farm       = &getL4FarmStruct( $farm_name );
	my $fg_enabled = ( &getFarmGuardianConf( $farm_name ) )[3];

	# check calls
	my $caller             = ( caller ( 2 ) )[3];
	my $changing_algorithm = ( $caller =~ /setL4FarmAlgorithm/ );
	my $removing_be        = ( $caller =~ /runL4FarmServerDelete/ );
	my $fg_pid             = &getFarmGuardianPid( $farm_name );

	#~ &zlog("(caller(2))[3]:$caller");

	if ( $fg_enabled eq 'true' && !$changing_algorithm && !$removing_be )
	{
		kill 'STOP' => $fg_pid;
	}

	$farm = &getL4FarmStruct( $farm_name );
	my $server = $$farm{ servers }[$server_id];

	## Applying all rules ##
	$rules = &getL4ServerActionRules( $farm, $server, 'off' );

	$output |= &applyIptRules( @{ $$rules{ t_mangle_p } } );
	$output |= &applyIptRules( @{ $$rules{ t_mangle } } );
	$output |= &applyIptRules( @{ $$rules{ t_nat } } );
	$output |= &applyIptRules( @{ $$rules{ t_snat } } );
	## End applying rules ##

	if ( $fg_enabled eq 'true' && !$changing_algorithm && !$removing_be )
	{
		kill 'CONT' => $fg_pid;
	}

	return $output;
}


=begin nd
Function: getL4ServerWithLowestPriority

	Look for backend with the lowest priority
		
Parameters:
	farm - Farm hash ref. It is a hash with all information about the farm

Returns:
	hash ref - reference to the selected server for prio algorithm
	
=cut
sub getL4ServerWithLowestPriority    # ($farm)
{
	my $farm = shift;                # input: farm reference

	my $prio_server;    # reference to the selected server for prio algorithm

	foreach my $server ( @{ $$farm{ servers } } )
	{
		if ( $$server{ status } eq 'up' )
		{
			# find the lowest priority server
			$prio_server = $server if not defined $prio_server;
			$prio_server = $server if $$prio_server{ priority } > $$server{ priority };
		}
	}

	return $prio_server;
}


=begin nd
Function: getL4FarmBackendMaintenance

	Check if a backend on a farm is on maintenance mode
		
Parameters:
	farmname - Farm name
	backend - Backend id

Returns:
	Integer - 0 for backend in maintenance or 1 for backend not in maintenance
	
=cut
sub getL4FarmBackendMaintenance
{
	my ( $farm_name, $backend ) = @_;

	my @servers = &getL4FarmServers( $farm_name );
	my @backend_args = split "\;", $servers[$backend];
	chomp ( @backend_args );

	return (    # parentheses required
		$backend_args[6] eq 'maintenance'
		? 0                                 # in maintenance
		: 1                                 # not in maintenance
	);
}


=begin nd
Function: setL4FarmBackendMaintenance

	Enable the maintenance mode for backend
		
Parameters:
	farmname - Farm name
	backend - Backend id

Returns:
	Integer - 0 on success or other value on failure
	
=cut
sub setL4FarmBackendMaintenance             # ( $farm_name, $backend )
{
	my ( $farm_name, $backend ) = @_;

	return &setL4FarmBackendStatus( $farm_name, $backend, 'maintenance' );
}


=begin nd
Function: setL4FarmBackendNoMaintenance

	Disable the maintenance mode for backend
		
Parameters:
	farmname - Farm name
	backend - Backend id

Returns:
	Integer - 0 on success or other value on failure
	
=cut
sub setL4FarmBackendNoMaintenance
{
	my ( $farm_name, $backend ) = @_;

	return &setL4FarmBackendStatus( $farm_name, $backend, 'up' );
}


=begin nd
Function: getL4BackendsWeightProbability

	Get probability for every backend
		
Parameters:
	farm - Farm hash ref. It is a hash with all information about the farm

Returns:
	none - .
	
=cut
sub getL4BackendsWeightProbability
{
	my $farm = shift;    # input: farm reference

	my $weight_sum = 0;

	&doL4FarmProbability( $farm );    # calculate farm weight sum

	foreach my $server ( @{ $$farm{ servers } } )
	{
		# only calculate probability for servers running
		if ( $$server{ status } eq 'up' )
		{
			my $delta = $$server{ weight };
			$weight_sum += $$server{ weight };
			$$server{ prob } = $weight_sum / $$farm{ prob };
		}
		else
		{
			$$server{ prob } = 0;
		}
	}
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
	my $prio_server;
	my @rules;
	my $return_code = 0;

	$prio_server = &getL4ServerWithLowestPriority( $farm );

	# refresh backends probability values
	&getL4BackendsWeightProbability( $farm ) if ( $$farm{ lbalg } eq 'weight' );

	## lock iptables use ##
	my $iptlock = &getGlobalConfiguration('iptlock');
	open ( my $ipt_lockfile, '>', $iptlock );

	unless ( $ipt_lockfile )
	{
		&zenlog("Could not open $iptlock: $!");
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
	for my $farm_name ( &getFarmNameList() )
	{
		my $farm_type = &getFarmType( $farm_name );

		next if $farm_type ne 'l4xnat';
		next if &getFarmStatus( $farm_name ) ne 'up';

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

# reset connection tracking for a backend
# used in udp protocol
# called by: refreshL4FarmRules, runL4FarmServerDelete
sub resetL4FarmBackendConntrackMark
{
	my $server = shift;

	my $conntrack = &getGlobalConfiguration('conntrack');
	my $cmd = "$conntrack -D -m $server->{ tag }";

	&zenlog("running: $cmd") if &debug();

	# return_code = 0 -> deleted
	# return_code = 1 -> not found/deleted
	# WARNIG: STDOUT must be null so cherokee does not receive this output
	# as http headers.
	my $return_code = system( "$cmd 1>/dev/null" );

	if ( &debug() )
	{
		if ( $return_code )
		{
			&zenlog( "Connection tracking for $server->{ vip } not found." );
		}
		else
		{
			&zenlog( "Connection tracking for $server->{ vip } removed." );
		}
	}

	return $return_code;
}

1;
