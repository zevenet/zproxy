#!/usr/bin/perl

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

#~ use strict;
use Config::Tiny;
use Tie::File;

require "/usr/local/zenloadbalancer/www/farms_functions.cgi";
require "/usr/local/zenloadbalancer/www/functions_ext.cgi";
require "/usr/local/zenloadbalancer/config/global.conf";

=begin nd
        Function: getIptListV4

        Obtein IPv4 iptables rules for a couple table-chain

        Parameters:
				table - 
				chain - 
				
        Returns:
				== 0	- don't find any rule
                @out	- Array with rules

=cut

sub getIptListV4
{
	my ( $table, $chain ) = @_;

	if ( $table ne '' )
	{
		$table = "--table $table";
	}

	my $iptables_command = &getGlobalConfiguration( 'iptables' )
	  . " $table -L $chain -n -v --line-numbers";

	&zenlog( $iptables_command );

	## lock iptables use ##
	open my $ipt_lockfile, '>', $iptlock;
	&setIptLock( $ipt_lockfile );

	my @ipt_output = `$iptables_command`;

	## unlock iptables use ##
	&setIptUnlock( $ipt_lockfile );
	close $ipt_lockfile;

	return @ipt_output;
}

=begin nd
        Function: getDDOSLookForRule

        Look for a:
			- gloabl rule 					( key )
			- farm rule 					( key != farms, farmName ), used to check if rule was applied successful
			- set of rules applied a farm 	( key =  farms, farmName )
        
        Parameters:
				key		 - id that indetify a rule
				farmName - farm name
				
        Returns:
				== 0	- don't find any rule
                @out	- Array with reference hashs
						- out[i]= { 
									line  => num,
									table => string,
									chain => string
								  }

=cut

sub getDDOSLookForRule
{
	my ( $key, $farmName ) = @_;

	# table and chain where there are keep ddos rules
	my @table = ( 'filter', 'mangle',     'filter' );
	my @chain = ( 'INPUT',  'PREROUTING', 'PORT_SCANNING' );

	my @output;
	$ind = -1;
	for ( @table )
	{
		$ind++;

		# Get line number
		my @rules = &getIptListV4( $table[$ind], $chain[$ind] );

		# Reverse @rules to delete first last rules
		@rules = reverse ( @rules );

		# Delete DDoS global conf
		foreach my $rule ( @rules )
		{
			my $flag = 0;
			my $lineNum;

			# Look for by farm name
			if ( $key eq 'farms' )
			{
				if ( $rule =~ /^(\d+) .+DDOS_[A-Z]+_$farmName \*/ )
				{
					$lineNum = $1;
					$flag    = 1;
				}
			}

			# Look for by key
			else
			{

				if ( $rule =~ /^(\d+) .+DDOS_$key/ )
				{
					$lineNum = $1;
					$flag    = 1;
				}
			}
			push @output, { line => $lineNum, table => $table[$ind], chain => $chain[$ind] }
			  if ( $flag );
		}
	}
	return \@output;
}

=begin nd
        Function: setDDOSRunRule

        Apply iptables rules to a farm or all balancer

        Parameters:
				key		 - id that indetify a rule, ( key = 'farms' to apply rules to farm )
				farmname - farm name
				
        Returns:

=cut

sub setDDOSRunRule
{
	my ( $key, $farmName ) = @_;

	# balancer rules (global)
	if ( $key ne 'farms' )
	{
		&setDDOSSshBruteForceRule if ( $key eq 'ssh_bruteForce' );
	}
	else
	{
		# get farm struct
		my %hash = (
					 farmName => $farmName,
					 vip      => "-d " . &getFarmVip( 'vip', $farmName ),
					 vport    => "--dport " . &getFarmVip( 'vpp', $farmName ),
		);

		# -d farmIP -p PROTOCOL --dport farmPORT
		my $protocol = &getFarmProto( $farmName );

		if ( $protocol =~ /UDP/i || $protocol =~ /TFTP/i || $protocol =~ /SIP/i )
		{
			$hash{ 'protocol' } = "-p udp";
		}
		if ( $protocol =~ /TCP/i || $protocol =~ /FTP/i )
		{
			$hash{ 'protocol' } = "-p tcp";
		}

		# farm rules
		&setDDOSInvalidPacketRule( \%hash );
		&setDDOSBlockSpoofedRule( \%hash );
		&setDDOSDropIcmpRule( \%hash );
		&setDDOSDropFragmentsRule( \%hash );

		# Only farms that use tcp protocol
		if ( $protocol =~ /TCP/i || $protocol =~ /FTP/i )
		{
			&setDDOSNewNoSynRule( \%hash );
			&setDDOSSynWithMssRule( \%hash );
			&setDDOSBogusTcpFlagsRule( \%hash );
			&setDDOSLimitRstRule( \%hash );
			&setDDOSLimitSecRule( \%hash );
			&setDDOSLimitConnsRule( \%hash );
			&setDDOSPortScanningRule( \%hash );
		}
	}
}

=begin nd
        Function: setDDOSStopRule

        Remove iptables rules

        Parameters:
				key		 - id that indetify a rule, ( key = 'farms' to remove rules from farm )
				farmname - farm name
				
        Returns:
				== 0	- Successful
                != 0	- Number of rules didn't boot

=cut

sub setDDOSStopRule
{
	my ( $key, $farmName ) = @_;
	my $output;

	my $ind++;
	foreach my $rule ( @{ &getDDOSLookForRule( $key, $farmName ) } )
	{
		my $cmd = &getGlobalConfiguration( 'iptables' )
		  . " --table $rule->{'table'} -D $rule->{'chain'} $rule->{'line'}";
		my $output = &iptSystem( $cmd );
		if ( $output != 0 )
		{
			&zenlog( "Error deleting '$cmd'" );
			$output++;
		}
		else
		{
			&zenlog( "Deleted '$cmd' successful" );
		}
	}
	return $output;
}

=begin nd
        Function: setDDOSBoot

        Boot all DDoS rules

        Parameters:
				
        Returns:
				== 0	- Successful
                != 0	- Number of rules didn't boot

=cut

sub setDDOSBoot
{
	my $confFile = &getGlobalConfiguration( 'ddosConf' );
	my $output;

	if ( -e $confFile )
	{
		my $fileHandle = Config::Tiny->read( $confFile );
		foreach my $key ( keys %{ $fileHandle->{ '_' } } )
		{
			if ( $key eq 'farms' )
			{
				my $farmList = $fileHandle->{ '_' }->{ 'farms' };
				my @farms = split ( ' ', $farmList );
				foreach my $farmName ( @farms )
				{
					$output++ if ( &setDDOSRunRule( $key, $farmName ) != 0 );
				}
			}
			elsif ( $fileHandle->{ '_' }->{ $key } eq 'up' )
			{
				$output++ if ( &setDDOSRunRule( $key ) != 0 );
			}
		}
	}
	return $output;
}

=begin nd
        Function: setDDOSStop

        Stop all DDoS rules

        Parameters:
				
        Returns:
				== 0	- Successful
                != 0	- Number of rules didn't Stop

=cut

sub setDDOSStop
{
	my $confFile = &getGlobalConfiguration( 'ddosConf' );
	my $output;

	if ( -e $confFile )
	{
		my $fileHandle = Config::Tiny->read( $confFile );
		foreach my $key ( keys %{ $fileHandle->{ '_' } } )
		{
			if ( $key eq 'farms' )
			{
				my $farmList = $fileHandle->{ '_' }->{ 'farms' };
				my @farms = split ( ' ', $farmList );
				foreach my $farmName ( @farms )
				{
					$output++ if ( &setDDOSStopRule( $key, $farmName ) != 0 );
				}
			}
			elsif ( $fileHandle->{ '_' }->{ $key } eq 'up' )
			{
				$output++ if ( &setDDOSStopRule( $key ) != 0 );
			}
		}
	}
	return $output;
}

=begin nd
        Function: setDDOSCreateRule

        Create a DDoS rules
        This rules have two types: applied to a farm or applied to the balancer

        Parameters:
				key		 - id that indetify a rule
				farmname - farm name
				
        Returns:
				== 0	- Successful
                != 0	- Error

=cut

sub setDDOSCreateRule
{
	my ( $key, $farmName ) = @_;
	my $confFile = &getGlobalConfiguration( 'ddosConf' );
	my $output;

	if ( !-e $confFile )
	{
		if ( system ( &getGlobalConfiguration( 'touch' ) . " " . $confFile ) != 0 )
		{
			&zenlog( "Error creating " . $confFile );
			return -2;
		}
	}

	my $fileHandle = Config::Tiny->read( $confFile );
	my $farmList   = $fileHandle->{ '_' }->{ 'farms' };

	if ( $key eq 'farms' )
	{
		if ( $farmList !~ /(^| )$farmName( |$)/ )
		{
			$fileHandle->{ '_' }->{ 'farms' } = "$farmList $farmName";
			$fileHandle->write( $confFile );

			$output = &setDDOSRunRule( $key, $farmName );
		}
	}

	# check param is down
	elsif ( $fileHandle->{ '_' }->{ $key } ne "up" )
	{
		$fileHandle->{ '_' }->{ $key } = "up";
		$fileHandle->write( $confFile );

		$output = &setDDOSRunRule( $key );
	}

	return $output;
}

=begin nd
        Function: setDDOSCreateRule

        Create a DDoS rules
        This rules have two types: applied to farm or balancer

        Parameters:
				key		 - id that indetify a rule
				farmname - farm name
				
        Returns:
				== 0	- Successful
                != 0	- Error

=cut

sub setDDOSDeleteRule
{
	my ( $key, $farmName ) = @_;
	my $confFile   = &getGlobalConfiguration( 'ddosConf' );
	my $fileHandle = Config::Tiny->read( $confFile );
	my $output;

	if ( -e $confFile )
	{
		if ( $farmName )
		{
			$fileHandle->{ '_' }->{ 'farms' } =~ s/(^| )$farmName( |$)/ /;
			$fileHandle->write( $confFile );
			$output = &setDDOSStopRule( 'farms', $farmName );
		}
		elsif ( $key eq 'ssh_bruteForce' )
		{
			$fileHandle->{ '_' }->{ 'ssh_bruteForce' } = "down";
			$fileHandle->write( $confFile );
			$output = &setDDOSStopRule( 'SSHBRUTEFORCE' );
		}
	}
	return $output;
}

# permivisve rule
### 1: Drop invalid packets ###
# &setDDOSInvalidPacketRule ( ruleOpt )
sub setDDOSInvalidPacketRule
{
	my ( $ruleOptRef ) = @_;
	my %ruleOpt = %{ $ruleOptRef };

	my $key = "INVALID";

	# /sbin/iptables -t mangle -A PREROUTING -m conntrack --ctstate INVALID -j DROP
	my $cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "    # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "-m conntrack --ctstate INVALID "    # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	my $output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '$key' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	return $output;
}

# Only TCP farms
# restrictive rule
### 2: Drop TCP packets that are new and are not SYN ###
# &setDDOSNewNoSynRule ( ruleOpt )
sub setDDOSNewNoSynRule
{
	my ( $ruleOptRef ) = @_;
	my %ruleOpt = %{ $ruleOptRef };

	my $key = "NEWNOSYN";

# sbin/iptables -t mangle -A PREROUTING -p tcp ! --syn -m conntrack --ctstate NEW -j DROP
	my $cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "    # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "! --syn -m conntrack --ctstate NEW "    # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	my $output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '$key' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	return $output;
}

# Only TCP farms
### 3: Drop SYN packets with suspicious MSS value ###
# &setDDOSSynWithMssRule ( ruleOpt )
sub setDDOSSynWithMssRule
{
	my ( $ruleOptRef ) = @_;
	my %ruleOpt = %{ $ruleOptRef };

	my $key = "SYNWITHMSS";

# /sbin/iptables -t mangle -A PREROUTING -p tcp -m conntrack --ctstate NEW -m tcpmss ! --mss 536:65535 -j DROP
	my $cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "    # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "-m conntrack --ctstate NEW -m tcpmss ! --mss 536:65535 "  # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	my $output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '$key' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	return $output;
}

# Only TCP farms
### 4: Block packets with bogus TCP flags ###
# &setDDOSBogusTcpFlagsRule ( ruleOpt )
sub setDDOSBogusTcpFlagsRule
{
	my ( $ruleOptRef ) = @_;
	my %ruleOpt = %{ $ruleOptRef };

	my $key = "BOGUSTCPFLAGS";

# /sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags FIN,SYN,RST,PSH,ACK,URG NONE -j DROP
	my $cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "    # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "--tcp-flags FIN,SYN,RST,PSH,ACK,URG NONE "    # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	my $output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${key}_1' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

 # /sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags FIN,SYN FIN,SYN -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "    # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "--tcp-flags FIN,SYN FIN,SYN "    # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	$output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${key}_2' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

 # /sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags SYN,RST SYN,RST -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "    # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "--tcp-flags SYN,RST SYN,RST "    # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	$output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${key}_3' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

 # /sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags SYN,FIN SYN,FIN -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "    # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "--tcp-flags SYN,FIN SYN,FIN "    # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	$output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${key}_4' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

 # /sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags FIN,RST FIN,RST -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "    # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "--tcp-flags FIN,RST FIN,RST "    # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	$output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${key}_5' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	# /sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags FIN,ACK FIN -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "    # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "--tcp-flags FIN,ACK FIN "    # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	$output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${key}_6' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	# /sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags ACK,URG URG -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "    # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "--tcp-flags ACK,URG URG "    # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	$output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${key}_7' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	# /sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags ACK,FIN FIN -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "    # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "--tcp-flags ACK,FIN FIN "    # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	$output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${key}_8' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	# /sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags ACK,PSH PSH -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "    # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "--tcp-flags ACK,PSH PSH "    # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	$output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${key}_9' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	# /sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags ALL ALL -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "    # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "--tcp-flags ALL ALL "    # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	$output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${key}_10' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	# /sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags ALL NONE -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "    # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "--tcp-flags ALL NONE "    # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	$output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${key}_11' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

 # /sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags ALL FIN,PSH,URG -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "    # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "--tcp-flags ALL FIN,PSH,URG "    # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	$output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${key}_12' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

# /sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags ALL SYN,FIN,PSH,URG -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "    # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "--tcp-flags ALL SYN,FIN,PSH,URG "    # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	$output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${key}_13' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

# /sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags ALL SYN,RST,ACK,FIN,URG -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "    # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "--tcp-flags ALL SYN,RST,ACK,FIN,URG "    # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	$output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${key}_14' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	return $output;
}

### 5: Block spoofed packets ###
# &setDDOSBlockSpoofedRule ( ruleOpt )
sub setDDOSBlockSpoofedRule
{
	my ( $ruleOptRef ) = @_;
	my %ruleOpt = %{ $ruleOptRef };

	my $key = "BLOCKSPOOFED";

	# /sbin/iptables -t mangle -A PREROUTING -s 224.0.0.0/3 -j DROP
	my $cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "    # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "-s 192.0.2.0/24,192.168.0.0/16,10.0.0.0/8,0.0.0.0/8,240.0.0.0/5 " # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";     # comment

	my $output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${key}_1' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	# /sbin/iptables -t mangle -A PREROUTING -s 127.0.0.0/8 ! -i lo -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "    # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "-s 127.0.0.0/8 ! -i lo "    # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	my $output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${key}_2' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	return $output;
}

# All balancer
### 6: Drop ICMP ###
# &setDDOSDropIcmpRule ( ruleOpt )
sub setDDOSDropIcmpRule
{
	my ( $ruleOptRef ) = @_;
	my %ruleOpt = %{ $ruleOptRef };

	my $key = "DROPICMP";

	# /sbin/iptables -t mangle -A PREROUTING -p icmp -j DROP
	my $cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "     # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } "    # who is destined
	  . "-p icmp "                      # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	my $output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '$key' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	return $output;
}

# only ipv4
### 7: Drop fragments in all chains ###
# &setDDOSDropFragmentsRule ( ruleOpt )
sub setDDOSDropFragmentsRule
{
	my ( $ruleOptRef ) = @_;
	my %ruleOpt = %{ $ruleOptRef };

	my $key = "DROPFRAGMENTS";

	# only in IPv4
	if ( &getBinVersion( $ruleOpt{ 'farmName' } ) =~ /6/ )
	{
		return 0;
	}

	# /sbin/iptables -t mangle -A PREROUTING -f -j DROP
	my $cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t mangle -A PREROUTING "    # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "-f "    # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	my $output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '$key' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	return $output;
}

# Only TCP farms
### 8: Limit connections per source IP ###
# &setDDOSLimitConnsRule ( ruleOpt )
sub setDDOSLimitConnsRule
{
	my ( $ruleOptRef ) = @_;
	my %ruleOpt = %{ $ruleOptRef };

	my $key = "LIMITCONNS";

	my $limitConns = 100;    # ???

# /sbin/iptables -A INPUT -p tcp -m connlimit --connlimit-above 111 -j REJECT --reject-with tcp-reset
	my $cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -A INPUT "         # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "-m connlimit --connlimit-above $limitConns "    # rules for block
	  . "-j REJECT --reject-with tcp-reset "
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

	my $output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '$key' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	return $output;
}

# Only TCP farms
### 9: Limit RST packets ###
# &setDDOSLimitRstRule ( ruleOpt )
sub setDDOSLimitRstRule
{
	my ( $ruleOptRef ) = @_;
	my %ruleOpt = %{ $ruleOptRef };

	my $key = "LIMITRST";

	my $limit      = 2;    # ???;
	my $limitBurst = 2;    # ???;

# /sbin/iptables -A INPUT -p tcp --tcp-flags RST RST -m limit --limit 2/s --limit-burst 2 -j ACCEPT
	my $cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -A INPUT "       # select iptables struct
	  . "-j ACCEPT $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "--tcp-flags RST RST -m limit --limit $limit/s --limit-burst $limitBurst " # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";             # comment

	my $output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${key}_1' rule to farm '$ruleOpt{ 'farmName' }'." );
	}
	else
	{
		# /sbin/iptables -A INPUT -p tcp --tcp-flags RST RST -j DROP
		$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
		  . " -A INPUT "    # select iptables struct
		  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
		  . "--tcp-flags RST RST "    # rules for block
		  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

		my $output = &iptSystem( $cmd );
		if ( $output != 0 )
		{
			&zenlog( "Error appling '${key}_2' rule to farm '$ruleOpt{ 'farmName' }'." );
		}
	}
	return $output;
}

# Only TCP farms
### 10: Limit new TCP connections per second per source IP ###
# &setDDOSLimitSecRule ( ruleOpt )
sub setDDOSLimitSecRule
{
	my ( $ruleOptRef ) = @_;
	my %ruleOpt = %{ $ruleOptRef };

	my $key = "LIMITSEC";

	my $limitNew      = 60;    # ???
	my $limitBurstNew = 20;    # ???

# /sbin/iptables -A INPUT -p tcp -m conntrack --ctstate NEW -m limit --limit 60/s --limit-burst 20 -j ACCEPT
	my $cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -A INPUT "           # select iptables struct
	  . "-j ACCEPT $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "-m conntrack --ctstate NEW -m limit --limit $limitBurstNew/s --limit-burst $limitBurstNew " # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";                               # comment

	my $output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${key}_1' rule to farm '$ruleOpt{ 'farmName' }'." );
	}
	else
	{
		# /sbin/iptables -A INPUT -p tcp -m conntrack --ctstate NEW -j DROP
		$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
		  . " -A INPUT "    # select iptables struct
		  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
		  . "-m conntrack --ctstate NEW "    # rules for block
		  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment

		my $output = &iptSystem( $cmd );
		if ( $output != 0 )
		{
			&zenlog( "Error appling '${key}_2' rule to farm '$ruleOpt{ 'farmName' }'." );
		}
	}
	return $output;
}

# All backends
### Protection against port scanning ###
# &setDDOSPortScanningRule ( ruleOpt )
sub setDDOSPortScanningRule
{
	my ( $ruleOptRef ) = @_;
	my %ruleOpt = %{ $ruleOptRef };

	my $key = "PORTSCANNING";

	# /sbin/iptables -N port-scanning
	my $cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -N PORT_SCANNING ";    # select iptables struct
	my $output = &iptSystem( $cmd );

# iptables -A PORT_SCANNING -p tcp --tcp-flags SYN,ACK,FIN,RST RST -m limit --limit 1/s -j RETURN
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -A PORT_SCANNING "     # select iptables struct
	  . "-j DROP $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vpp' } " # who is destined
	  . "-m conntrack --ctstate NEW "    # rules for block
	  . "-m comment --comment \"DDOS_${key}_$ruleOpt{ 'farmName' }\"";    # comment
	my $output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '$key' rule to farm '$ruleOpt{ 'farmName' }'." );

	}

	return $output;
}

=begin nd
        Function: setDDOSSshBruteForceRule

        This rule is a protection against brute-force atacks to ssh protocol.
        This rule applies to the balancer

        Parameters:
				
        Returns:
				== 0	- successful
                != 0	- error

=cut

# balancer
### SSH brute-force protection ###
# &setDDOSSshBruteForceRule
sub setDDOSSshBruteForceRule
{

	my $time = 180;    # ???
	my $hits = 5;      # ???

	my $key = "SSHBRUTEFORCE";

# /sbin/iptables -A INPUT -p tcp --dport ssh -m conntrack --ctstate NEW -m recent --set
	my $cmd =
	  &getGlobalConfiguration( 'iptables' ) . " -A INPUT "  # select iptables struct
	  . "-p tcp --dport ssh "                               # who is destined
	  . "-m conntrack --ctstate NEW -m recent --set "       # rules for block
	  . "-m comment --comment \"DDOS_$key\"";               # comment

	my $output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${key}_1' rule." );
	}

# /sbin/iptables -A INPUT -p tcp --dport ssh -m conntrack --ctstate NEW -m recent --update --seconds 60 --hitcount 10 -j DROP
	my $cmd =
	  &getGlobalConfiguration( 'iptables' ) . " -A INPUT "  # select iptables struct
	  . "-j DROP -p tcp --dport ssh "                       # who is destined
	  . "-m conntrack --ctstate NEW -m recent --update --seconds $time --hitcount $hits " # rules for block
	  . "-m comment --comment \"DDOS_$key\"";                                             # comment

	my $output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${key}_2' rule." );
	}

	return $output;
}

1;

### 11: Use SYNPROXY on all ports (disables connection limiting rule) ###
#/sbin/iptables -t raw -D PREROUTING -p tcp -m tcp --syn -j CT --notrack
#/sbin/iptables -D INPUT -p tcp -m tcp -m conntrack --ctstate INVALID,UNTRACKED -j SYNPROXY --sack-perm --timestamp --wscale 7 --mss 1460
#/sbin/iptables -D INPUT -m conntrack --ctstate INVALID -j DROP

=begin nd

### 1: Drop invalid packets ###
/sbin/iptables -t mangle -A PREROUTING -m conntrack --ctstate INVALID -j DROP

### 2: Drop TCP packets that are new and are not SYN ###
/sbin/iptables -t mangle -A PREROUTING -p tcp ! --syn -m conntrack --ctstate NEW -j DROP

### 3: Drop SYN packets with suspicious MSS value ###
/sbin/iptables -t mangle -A PREROUTING -p tcp -m conntrack --ctstate NEW -m tcpmss ! --mss 536:65535 -j DROP

### 4: Block packets with bogus TCP flags ###
/sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags FIN,SYN,RST,PSH,ACK,URG NONE -j DROP
/sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags FIN,SYN FIN,SYN -j DROP
/sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags SYN,RST SYN,RST -j DROP
/sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags SYN,FIN SYN,FIN -j DROP
/sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags FIN,RST FIN,RST -j DROP
/sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags FIN,ACK FIN -j DROP
/sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags ACK,URG URG -j DROP
/sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags ACK,FIN FIN -j DROP
/sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags ACK,PSH PSH -j DROP
/sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags ALL ALL -j DROP
/sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags ALL NONE -j DROP
/sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags ALL FIN,PSH,URG -j DROP
/sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags ALL SYN,FIN,PSH,URG -j DROP
/sbin/iptables -t mangle -A PREROUTING -p tcp --tcp-flags ALL SYN,RST,ACK,FIN,URG -j DROP

### 5: Block spoofed packets ###
/sbin/iptables -t mangle -A PREROUTING -s 224.0.0.0/3 -j DROP
/sbin/iptables -t mangle -A PREROUTING -s 169.254.0.0/16 -j DROP
/sbin/iptables -t mangle -A PREROUTING -s 172.16.0.0/12 -j DROP
/sbin/iptables -t mangle -A PREROUTING -s 192.0.2.0/24 -j DROP
/sbin/iptables -t mangle -A PREROUTING -s 192.168.0.0/16 -j DROP
/sbin/iptables -t mangle -A PREROUTING -s 10.0.0.0/8 -j DROP
/sbin/iptables -t mangle -A PREROUTING -s 0.0.0.0/8 -j DROP
/sbin/iptables -t mangle -A PREROUTING -s 240.0.0.0/5 -j DROP
/sbin/iptables -t mangle -A PREROUTING -s 127.0.0.0/8 ! -i lo -j DROP

### 6: Drop ICMP (you usually don't need this protocol) ###
/sbin/iptables -t mangle -A PREROUTING -p icmp -j DROP

### 7: Drop fragments in all chains ###
/sbin/iptables -t mangle -A PREROUTING -f -j DROP

### 8: Limit connections per source IP ###
/sbin/iptables -A INPUT -p tcp -m connlimit --connlimit-above 111 -j REJECT --reject-with tcp-reset

### 9: Limit RST packets ###
/sbin/iptables -A INPUT -p tcp --tcp-flags RST RST -m limit --limit 2/s --limit-burst 2 -j ACCEPT
/sbin/iptables -A INPUT -p tcp --tcp-flags RST RST -j DROP

### 10: Limit new TCP connections per second per source IP ###
/sbin/iptables -A INPUT -p tcp -m conntrack --ctstate NEW -m limit --limit 60/s --limit-burst 20 -j ACCEPT
/sbin/iptables -A INPUT -p tcp -m conntrack --ctstate NEW -j DROP

### 11: Use SYNPROXY on all ports (disables connection limiting rule) ###
#/sbin/iptables -t raw -D PREROUTING -p tcp -m tcp --syn -j CT --notrack
#/sbin/iptables -D INPUT -p tcp -m tcp -m conntrack --ctstate INVALID,UNTRACKED -j SYNPROXY --sack-perm --timestamp --wscale 7 --mss 1460
#/sbin/iptables -D INPUT -m conntrack --ctstate INVALID -j DROP

Bonus Rules

Here are some more iptables rules that are useful to increase the overall security of a Linux server:

### SSH brute-force protection ###
/sbin/iptables -A INPUT -p tcp --dport ssh -m conntrack --ctstate NEW -m recent --set
/sbin/iptables -A INPUT -p tcp --dport ssh -m conntrack --ctstate NEW -m recent --update --seconds 60 --hitcount 10 -j DROP

### Protection against port scanning ###
/sbin/iptables -N port-scanning
/sbin/iptables -A port-scanning -p tcp --tcp-flags SYN,ACK,FIN,RST RST -m limit --limit 1/s --limit-burst 2 -j RETURN
/sbin/iptables -A port-scanning -j DROP

=cut
