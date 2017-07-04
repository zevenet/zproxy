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

use Config::Tiny;
use Tie::File;

use Zevenet::Core;
use Zevenet::IPDS::Core;
use Zevenet::Farm;

sub setDOSCreateFileConf
{
	my $confFile   = &getGlobalConfiguration( 'dosConf' );
	my $dosConfDir = &getGlobalConfiguration( 'dosConfDir' );
	my $output;

	return 0 if ( -e $confFile );

	# create dos directory if it doesn't exist
	if ( !-d $dosConfDir )
	{
		$output = system ( &getGlobalConfiguration( 'mkdir' ) . " -p $dosConfDir" );
		&zenlog( "Created ipds configuration directory: $dosConfDir" );
	}

	# create file conf if doesn't exist
	if ( !$output )
	{
		&zenlog( "Created dos configuration directory: $dosConfDir" );
		$output = system ( &getGlobalConfiguration( 'touch' ) . " $confFile" );
		if ( $output )
		{
			&zenlog( "Error, creating dos configuration directory: $dosConfDir" );
		}
		else
		{
			&zenlog( "Created dos configuration file: $confFile" );
		}
	}

	if ( !$output )
	{
		#~ $output = &createDOSRule( 'drop_icmp', 'dropicmp' )		# Next version
		  #~ if ( &getDOSExists( 'drop_icmp' ) ne "0" );
		$output = &createDOSRule( 'ssh_brute_force', 'sshbruteforce' )
		  if ( &getDOSExists( 'ssh_brute_force' ) ne "0" );
	}
	else
	{
		&zenlog( "Error, creating dos configuration file: $confFile" );
	}

	return $output;
}

sub getDOSInitialParams
{
	my $rule = shift;

	# get ssh port
	require Zevenet::System::SSH;
	
	my $sshconf = &getSsh();
	my $port    = $sshconf->{ 'port' };

	my %initial = (
		'bogustcpflags' => { 'farms' => '', 'type'        => 'farm' },
		'limitconns'    => { 'farms' => '', 'limit_conns' => 20, 'type' => 'farm' },
		'limitrst' =>
		  { 'farms' => '', 'limit' => 10, 'limit_burst' => 5, 'type' => 'farm' },
		'limitsec' =>
		  { 'farms' => '', 'limit' => 20, 'limit_burst' => 15, 'type' => 'farm' },
		'dropicmp' => { 'status' => 'down', 'type' => 'system', 'name' => 'drop_icmp' },
		'sshbruteforce' => {
							 'status' => 'down',
							 'hits'   => 10,
							 'port'   => $port,
							 'time'   => 60,
							 'type'   => 'system',
							 'name'   => 'ssh_brute_force'
		},

		#					'NEWNOSYN' => { 'farms' => '' },
		#					'DROPFRAGMENTS' => { 'farms'  => '' },
		#					'INVALID'       => { 'farms'  => '' },
		#					'SYNPROXY'     => { 'farms' => '', 'mss' => 1460, 'scale' => 7 },
		#					'SYNWITHMSS'   => { 'farms' => '' },
		#					'PORTSCANNING' => {
		#										'farms'    => '',
		#										'portScan' => 15,
		#										'blTime'   => 500,
		#										'time'     => 100,
		#										'hits'     => 3,
		#					},
	);

	return $initial{ $rule };
}

# &getDOSParam( $ruleName, $param );
sub getDOSParam
{
	my $ruleName = shift;
	my $param    = shift;
	my $output;

	my $confFile   = &getGlobalConfiguration( 'dosConf' );
	my $fileHandle = Config::Tiny->read( $confFile );

	if ( $param )
	{
		$output = $fileHandle->{ $ruleName }->{ $param };
		if ( $param eq 'farms' )
		{
			my @aux = split ( ' ', $output );
			$output = \@aux;
		}
	}
	elsif ( $ruleName )
	{
		# get all params
		my %hash = %{ $fileHandle->{ $ruleName } };

		# return in integer format if this value is a number
		# It is neccessary for zapi
		foreach my $key ( keys %hash )
		{
			$hash{ $key } += 0 if ( $hash{ $key } =~ /^\d+$/ );
		}

		# replace farms string for a array reference
		if ( exists $fileHandle->{ $ruleName }->{ 'farms' } )
		{
			my @aux = split ( ' ', $fileHandle->{ $ruleName }->{ 'farms' } );
			$hash{ 'farms' } = \@aux;
		}

		$output = \%hash;
	}
	return $output;
}

# &setDOSParam ($name,$param,$value)
sub setDOSParam
{
	my $name  = shift;
	my $param = shift;
	my $value = shift;
	my @farms;

	my $rule = &getDOSParam( $name, 'rule' );

	#Stop related rules
	&setDOSStopRule( $name );

	my $confFile   = &getGlobalConfiguration( 'dosConf' );
	my $fileHandle = Config::Tiny->read( $confFile );
	$fileHandle = Config::Tiny->read( $confFile );

	$fileHandle->{ $name }->{ $param } = $value;
	$fileHandle->write( $confFile );

	#~ # Rule global for the balancer
	if ( &getDOSParam( $name, 'type' ) eq 'system' )
	{
		if ( &getDOSParam( $name, 'status' ) eq 'up' )
		{
			&setDOSRunRule( $name );
		}
		elsif ( &getDOSParam( $name, 'status' ) eq 'down' )
		{
			&setDOSStopRule( $name );
		}
	}

	# Rule applied to farm
	elsif ( @farms = @{ &getDOSParam( $name, 'farms' ) } )
	{
		foreach my $farm ( @farms )
		{
			&setDOSRunRule( $name, $farm );
		}
	}
}

=begin nd
        Function: getDOSLookForRule

        Look for a:
			- global name 				( key )
			- set of rules applied a farm 	( key, farmName )
        
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

sub getDOSLookForRule
{
	my ( $ruleName, $farmName ) = @_;

	# table and chain where there are keep dos rules

 # active this when port scanning rule will be available
 #~ my @table = ( 'raw', 'filter', 'filter', 'raw', 'mangle' );
 #~ my @chain = ( 'PREROUTING', 'INPUT', 'FORWARD', 'PORT_SCANNING', 'PREROUTING' );

	my @table = ( 'raw',        'filter', 'filter',  'mangle' );
	my @chain = ( 'PREROUTING', 'INPUT',  'FORWARD', 'PREROUTING' );
	my $farmNameRule;

	my @output;
	my $ind = -1;
	for ( @table )
	{
		$ind++;

		# Get line number
		my @rules = &getIptListV4( $table[$ind], $chain[$ind] );

		# Reverse @rules to delete first last rules
		@rules = reverse ( @rules );

		# Delete DoS global conf
		foreach my $rule ( @rules )
		{
			my $flag = 0;
			my $lineNum;

			# Look for farm rule
			if ( $farmName )
			{
				if ( $rule =~ /^(\d+) .+DOS_${ruleName}_$farmName \*/ )
				{
					$lineNum = $1;
					$flag    = 1;
				}
			}

			# Look for global rule
			else
			{
				my $farmNameFormat = &getValidFormat( 'farm_name' );
				if ( $rule =~ /^(\d+) .+DOS_$ruleName/ )
				{
					$lineNum      = $1;
					$flag         = 1;
					$farmNameRule = $2;
				}
			}
			push @output, { line => $lineNum, table => $table[$ind], chain => $chain[$ind] }
			  if ( $flag );
		}
	}
	return \@output;
}

# return -1 if not exists
# return  0 if exists
# return  array with all rules if the function not receive params
# &getDOSExists ( $rule );
sub getDOSExists
{
	my $name       = shift;
	my $output     = -1;
	my $confFile   = &getGlobalConfiguration( 'dosConf' );
	my $fileHandle = Config::Tiny->read( $confFile );
	my @aux;

	if ( $name )
	{
		$output = 0 if ( exists $fileHandle->{ $name } );
	}
	else
	{
		@aux    = keys %{ $fileHandle };
		$output = \@aux;
	}

	return $output;
}

# key is the rule identifier
# &createDOSRule( $rule, $rule );
sub createDOSRule
{
	my $ruleName = shift;
	my $rule     = shift;
	my $params;

	my $confFile   = &getGlobalConfiguration( 'dosConf' );
	my $fileHandle = Config::Tiny->read( $confFile );
	$fileHandle = Config::Tiny->read( $confFile );

	if ( exists $fileHandle->{ $ruleName } )
	{
		&zenlog( "$ruleName rule already exists." );
		return -1;
	}
	$params = &getDOSInitialParams( $rule );

	if ( !$params )
	{
		&zenlog( "Error, saving $ruleName rule." );
		return -2;
	}

	$fileHandle->{ $ruleName } = $params;
	$fileHandle->{ $ruleName }->{ 'rule' } = $rule;
	if ( $params->{ 'type' } eq 'farm' )
	{
		$fileHandle->{ $ruleName }->{ 'rule' } = $rule;
		$fileHandle->{ $ruleName }->{ 'name' } = $ruleName;
	}
	$fileHandle->write( $confFile );
	&zenlog( "$ruleName rule created successful." );

	return 0;
}

sub deleteDOSRule
{
	my $name = shift;

	my $confFile   = &getGlobalConfiguration( 'dosConf' );
	my $fileHandle = Config::Tiny->read( $confFile );
	$fileHandle = Config::Tiny->read( $confFile );

	if ( !exists $fileHandle->{ $name } )
	{
		&zenlog( "$name rule doesn't exist." );
		return -1;
	}

	delete $fileHandle->{ $name };
	$fileHandle->write( $confFile );

	return 0;
}

=begin nd
        Function: setDOSRunRule

        Apply iptables rules to a farm or all balancer

        Parameters:
				rule		 - id that indetify a rule, ( rule = 'farms' to apply rules to farm )
				farmname - farm name
				
        Returns:

=cut

sub setDOSRunRule
{
	my ( $ruleName, $farmName ) = @_;
	my %hash;
	my $output = -2;
	my $protocol;

	# return if this rule already is applied
	if ( @{ &getDOSLookForRule( $ruleName, $farmName ) } )
	{
		&zenlog( "This rule already is applied." );
		return -1;
	}

	if ( $farmName )
	{
		# get farm struct
		%hash = (
				  farmName => $farmName,
				  vip      => "-d " . &getFarmVip( 'vip', $farmName ),
				  vport    => "--dport " . &getFarmVip( 'vipp', $farmName ),
		);

		# -d farmIP -p PROTOCOL --dport farmPORT
		$protocol = &getFarmProto( $farmName );

		if ( $protocol =~ /UDP/i || $protocol =~ /TFTP/i || $protocol =~ /SIP/i )
		{
			$hash{ 'protocol' } = "-p udp";
		}
		if ( $protocol =~ /TCP/i || $protocol =~ /FTP/i )
		{
			$hash{ 'protocol' } = "-p tcp";
		}
	}

	my $rule = &getDOSParam( $ruleName, 'rule' );

	if (    ( $rule eq 'DROPFRAGMENTS' )
		 || ( $rule eq 'NEWNOSYN' )
		 || ( $rule eq 'SYNWITHMSS' )
		 || ( $rule eq 'bogustcpflags' )
		 || ( $rule eq 'limitrst' )
		 || ( $rule eq 'SYNPROXY' ) )
	{
		if ( $protocol !~ /TCP/i && $protocol !~ /FTP/i )
		{
			&zenlog(
					 "$rule rule is only available in farms based in protocol TCP or FTP." );
			return -1;
		}
	}

	use Switch;
	switch ( $rule )
	{
		# comented rules aren't finished
		# global rules
		case 'sshbruteforce' { $output = &setDOSSshBruteForceRule(); }
		case 'dropicmp'      { $output = &setDOSDropIcmpRule(); }

		#~ case 'PORTSCANNING'		{ $output = &setDOSPortScanningRule();		}

		# rules for farms
		case 'limitconns' { $output = &setDOSLimitConnsRule( $ruleName, \%hash ); }
		case 'limitsec' { $output = &setDOSLimitSecRule( $ruleName, \%hash ); }

		#~ case 'INVALID'				{ $output = &setDOSInvalidPacketRule();	}
		#~ case 'BLOCKSPOOFED'	{ $output = &setDOSBlockSpoofedRule();	}

		# rules for tcp farms
		case 'bogustcpflags'
		{
			$output = &setDOSBogusTcpFlagsRule( $ruleName, \%hash );
		}
		case 'limitrst' { $output = &setDOSLimitRstRule( $ruleName, \%hash ); }

		#~ case 'DROPFRAGMENTS'	{ $output = &setDOSDropFragmentsRule(); }
		#~ case 'NEWNOSYN'				{ $output = &setDOSNewNoSynRule();		 }
		#~ case 'SYNWITHMSS'			{ $output = &setDOSSynWithMssRule();	 }
		#~ case 'SYNPROXY'				{ $output = &setDOSynProxyRule();			 }
	}

	return $output;
}

=begin nd
        Function: setDOSStopRule

        Remove iptables rules

        Parameters:
				ruleName		- id that indetify a rule, ( rule = 'farms' to remove rules from farm )
				farmname 	- farm name
				
        Returns:
				== 0	- Successful
             != 0	- Number of rules didn't boot

=cut

sub setDOSStopRule
{
	my ( $ruleName, $farmName ) = @_;
	my $output = 0;

	my $ind++;
	foreach my $rule ( @{ &getDOSLookForRule( $ruleName, $farmName ) } )
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

sub setDOSReloadFarmRules
{
	my $farmName = shift;

	# get all lists
	my $dosConf     = &getGlobalConfiguration( 'dosConf' );
	my $allRulesRef = Config::Tiny->read( $dosConf );
	my %allRules    = %{ $allRulesRef };

	foreach my $dosRule ( keys %allRules )
	{
		if ( grep ( /^$farmName$/, @{ &getDOSParam( $dosRule, "farms" ) } ) )
		{
			&setDOSRunRule( $dosRule, $farmName );
			&setDOSStopRule( $dosRule, $farmName );
		}
	}

	#~ return $output;
}

=begin nd
        Function: runDOSStartModule

        Boot all DoS rules-

        Parameters:
				
        Returns:
				== 0	- Successful
             != 0	- Number of rules didn't boot

=cut

sub runDOSStartModule
{
	my $confFile = &getGlobalConfiguration( 'dosConf' );
	my $output;

	&zenlog( "Booting dos system... " );
	&setDOSCreateFileConf();

	#create  PORT_SCANNING chain
	# /sbin/iptables -N PORT_SCANNING

	if ( -e $confFile )
	{
		
		# This block is a bugfix. When ssh_brute_force rule doesn't show the port
		if ( ! &setDOSParam ( 'ssh_brute_force', 'port' ) )
		{
			require Zevenet::System::SSH;
			my $sshconf = &getSsh();
			my $port    = $sshconf->{ 'port' };
			&setDOSParam ( 'ssh_brute_force', 'port', $port);
		}
		
		my $fileHandle = Config::Tiny->read( $confFile );
		foreach my $ruleName ( keys %{ $fileHandle } )
		{
			if ( $fileHandle->{ $ruleName }->{ 'type' } eq 'farm' )
			{
				my $farmList = $fileHandle->{ $ruleName }->{ 'farms' };
				my @farms = split ( ' ', $farmList );
				foreach my $farmName ( @farms )
				{
					# run rules of running farms
					if ( &getFarmBootStatus( $farmName ) eq 'up' )
					{
						if ( &setDOSRunRule( $ruleName, $farmName ) != 0 )
						{
							&zenlog ("Error running the rule $ruleName in the farm $farmName.");
						}
					}
				}
			}
			elsif ( $fileHandle->{ $ruleName }->{ 'type' } eq 'system' )
			{
				if ( $fileHandle->{ $ruleName }->{ 'status' } eq "up" )
				{
					if ( &setDOSRunRule( $ruleName, 'status' ) != 0 )
					{
						&zenlog ("Error, running the rule $ruleName.");
					}
				}
			}
		}
	}
	return $output;
}

=begin nd
        Function: runDOStopModule

        Stop all DoS rules

        Parameters:
				
        Returns:
			== 0	- Successful
            != 0	- Number of rules didn't Stop

=cut

sub runDOStopModule
{
	my $output   = 0;
	my $confFile = &getGlobalConfiguration( 'dosConf' );

	if ( -e $confFile )
	{
		my $fileHandle = Config::Tiny->read( $confFile );
		foreach my $rule ( keys %{ $fileHandle } )
		{
			# Applied to farm
			if ( $fileHandle->{ $rule }->{ 'type' } eq "farm" )
			{
				if ( $fileHandle->{ $rule }->{ 'farms' } )
				{
					my $farmList = $fileHandle->{ $rule }->{ 'farms' };
					my @farms = split ( ' ', $farmList );
					foreach my $farmName ( @farms )
					{
						$output++ if ( &setDOSStopRule( $rule, $farmName ) != 0 );
					}
				}
			}

			# Applied to balancer
			elsif ( $fileHandle->{ $rule }->{ 'type' } eq 'system' )
			{
				if ( $fileHandle->{ $rule }->{ 'status' } eq 'up' )
				{
					$output++ if ( &setDOSStopRule( $rule ) != 0 );
				}
			}
		}
	}
	return $output;
}

=begin nd
        Function: setDOSCreateRule

        Create a DoS rules
        This rules have two types: applied to a farm or applied to the balancer

        Parameters:
				rule		 		- id that indetify a rule
				farmname - farm name
				
        Returns:
				== 0	- Successful
             != 0	- Error

=cut

sub setDOSCreateRule
{
	my ( $ruleName, $farmName ) = @_;
	my $confFile = &getGlobalConfiguration( 'dosConf' );
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

	if ( $farmName )
	{
		my $farmList = $fileHandle->{ $ruleName }->{ 'farms' };
		if ( $farmList !~ /(^| )$farmName( |$)/ )
		{
			$output = &setDOSRunRule( $ruleName, $farmName );

			if ( $output != -2 )
			{
				$fileHandle = Config::Tiny->read( $confFile );
				$fileHandle->{ $ruleName }->{ 'farms' } = "$farmList $farmName";
				$fileHandle->write( $confFile );
			}
			else
			{
				&zenlog( "Rule $ruleName only is available for TCP protocol" );
			}
		}
	}

	# check param is down
	elsif ( $fileHandle->{ $ruleName }->{ 'status' } ne "up" )
	{
		$fileHandle->{ $ruleName }->{ 'status' } = "up";
		$fileHandle->write( $confFile );

		$output = &setDOSRunRule( $ruleName );
	}

	return $output;
}

=begin nd
        Function: setDOSCreateRule

        Create a DoS rules
        This rules have two types: applied to farm or balancer

        Parameters:
				rule		 - id that indetify a rule
				farmname - farm name
				
        Returns:
				== 0	- Successful
             != 0	- Error

=cut

sub setDOSDeleteRule
{
	my ( $ruleName, $farmName ) = @_;
	my $confFile   = &getGlobalConfiguration( 'dosConf' );
	my $fileHandle = Config::Tiny->read( $confFile );
	my $output;

	if ( -e $confFile )
	{
		if ( $farmName )
		{
			$fileHandle->{ $ruleName }->{ 'farms' } =~ s/(^| )$farmName( |$)/ /;
			$fileHandle->write( $confFile );
			$output = &setDOSStopRule( $ruleName, $farmName );
		}
		else
		{
			$fileHandle->{ $ruleName }->{ 'status' } = "down";
			$fileHandle->write( $confFile );
			$output = &setDOSStopRule( $ruleName );
		}
	}
	return $output;
}

# Only TCP farms
### Block packets with bogus TCP flags ###
# &setDOSBogusTcpFlagsRule ( ruleOpt )
sub setDOSBogusTcpFlagsRule
{
	my ( $ruleName, $ruleOptRef ) = @_;
	my %ruleOpt = %{ $ruleOptRef };

	#~ my $rule    = "bogustcpflags";
	my $logMsg = &createLogMsg( $ruleName, $ruleOpt{ 'farmName' } );

# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags FIN,SYN,RST,PSH,ACK,URG NONE -j DROP
	my $cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t raw -A PREROUTING "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags FIN,SYN,RST,PSH,ACK,URG NONE "    # rules for block
	  . "-m comment --comment \"DOS_${ruleName}_$ruleOpt{ 'farmName' }\""; # comment

	my $output = &setIPDSDropAndLog( $cmd, $logMsg );
	if ( $output != 0 )
	{
		&zenlog(
				 "Error appling '${ruleName}_1' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags FIN,SYN FIN,SYN -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t raw -A PREROUTING "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags FIN,SYN FIN,SYN "    # rules for block
	  . "-m comment --comment \"DOS_${ruleName}_$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	if ( $output != 0 )
	{
		&zenlog(
				 "Error appling '${ruleName}_2' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags SYN,RST SYN,RST -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t raw -A PREROUTING "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags SYN,RST SYN,RST "    # rules for block
	  . "-m comment --comment \"DOS_${ruleName}_$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	if ( $output != 0 )
	{
		&zenlog(
				 "Error appling '${ruleName}_3' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags SYN,FIN SYN,FIN -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t raw -A PREROUTING "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags SYN,FIN SYN,FIN "    # rules for block
	  . "-m comment --comment \"DOS_${ruleName}_$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	if ( $output != 0 )
	{
		&zenlog(
				 "Error appling '${ruleName}_4' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags FIN,RST FIN,RST -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t raw -A PREROUTING "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags FIN,RST FIN,RST "    # rules for block
	  . "-m comment --comment \"DOS_${ruleName}_$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	if ( $output != 0 )
	{
		&zenlog(
				 "Error appling '${ruleName}_5' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags FIN,ACK FIN -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t raw -A PREROUTING "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags FIN,ACK FIN "    # rules for block
	  . "-m comment --comment \"DOS_${ruleName}_$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	if ( $output != 0 )
	{
		&zenlog(
				 "Error appling '${ruleName}_6' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags ACK,URG URG -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t raw -A PREROUTING "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags ACK,URG URG "    # rules for block
	  . "-m comment --comment \"DOS_${ruleName}_$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	if ( $output != 0 )
	{
		&zenlog(
				 "Error appling '${ruleName}_7' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags ACK,FIN FIN -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t raw -A PREROUTING "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags ACK,FIN FIN "    # rules for block
	  . "-m comment --comment \"DOS_${ruleName}_$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	if ( $output != 0 )
	{
		&zenlog(
				 "Error appling '${ruleName}_8' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags ACK,PSH PSH -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t raw -A PREROUTING "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags ACK,PSH PSH "    # rules for block
	  . "-m comment --comment \"DOS_${ruleName}_$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	if ( $output != 0 )
	{
		&zenlog(
				 "Error appling '${ruleName}_9' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	#  Christmas tree packet. Used to analyze tcp response and to elaborate a atack
	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags ALL ALL -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t raw -A PREROUTING "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags ALL ALL "    # rules for block
	  . "-m comment --comment \"DOS_${ruleName}_$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	if ( $output != 0 )
	{
		&zenlog(
				 "Error appling '${ruleName}_10' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags ALL NONE -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t raw -A PREROUTING "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags ALL NONE "    # rules for block
	  . "-m comment --comment \"DOS_${ruleName}_$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	if ( $output != 0 )
	{
		&zenlog(
				 "Error appling '${ruleName}_11' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags ALL FIN,PSH,URG -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t raw -A PREROUTING "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags ALL FIN,PSH,URG "    # rules for block
	  . "-m comment --comment \"DOS_${ruleName}_$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	if ( $output != 0 )
	{
		&zenlog(
				 "Error appling '${ruleName}_12' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags ALL SYN,FIN,PSH,URG -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t raw -A PREROUTING "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags ALL SYN,FIN,PSH,URG "    # rules for block
	  . "-m comment --comment \"DOS_${ruleName}_$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	if ( $output != 0 )
	{
		&zenlog(
				 "Error appling '${ruleName}_13' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags ALL SYN,RST,ACK,FIN,URG -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t raw -A PREROUTING "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags ALL SYN,RST,ACK,FIN,URG "    # rules for block
	  . "-m comment --comment \"DOS_${ruleName}_$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	if ( $output != 0 )
	{
		&zenlog(
				 "Error appling '${ruleName}_14' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	return $output;
}

### Limit connections per source IP ###
# &setDOSLimitConnsRule ( ruleOpt )
sub setDOSLimitConnsRule
{
	my ( $ruleName, $ruleOptRef ) = @_;
	my %ruleOpt = %{ $ruleOptRef };

	#~ my $rule    = "limitconns";
	my $logMsg = &createLogMsg( $ruleName, $ruleOpt{ 'farmName' } );
	my $chain = "INPUT";               # default, this chain is for L7 apps
	my $dest  = $ruleOpt{ 'vip' };
	my $port  = $ruleOpt{ 'vport' };
	my $output;
	my $limit_conns = &getDOSParam( $ruleName, 'limit_conns' );

	# especific values to L4 farm
	if ( &getFarmType( $ruleOpt{ 'farmName' } ) eq "l4xnat" )
	{
		$chain = "FORWARD";
		my @run = &getFarmServers( $ruleOpt{ 'farmName' } );
		for my $l4Backends ( @run )
		{
			my @l_serv = split ( "\;", $l4Backends );
			$dest = "-d $l_serv[1]";
			$port = "--dport $l_serv[2]";

# /sbin/iptables -A FORWARD -t filter -d 1.1.1.1,54.12.1.1 -p tcp --dport 5 -m connlimit --connlimit-above 5 -m comment --comment "DOS_limitconns_aa" -j REJECT --reject-with tcp-reset
			my $cmd = &getBinVersion( $ruleOpt{ 'farmName' } )

			  #~ . " -A INPUT -t filter "         # select iptables struct
			  . " -A $chain -t filter "                           # select iptables struct
			  . "$dest $ruleOpt{ 'protocol' } $port "             # who is destined
			  . "-m connlimit --connlimit-above $limit_conns "    # rules for block
			  . "-m comment --comment \"DOS_${ruleName}_$ruleOpt{ 'farmName' }\""; # comment

			$output = &iptSystem( "$cmd -j LOG  --log-prefix \"$logMsg\" --log-level 4 " );

			$output = &iptSystem( "$cmd -j REJECT --reject-with tcp-reset" );
		}
	}

	else
	{
# /sbin/iptables -A FORWARD -t filter -d 1.1.1.1,54.12.1.1 -p tcp --dport 5 -m connlimit --connlimit-above 5 -m comment --comment "DOS_limitconns_aa" -j REJECT --reject-with tcp-reset
		my $cmd = &getBinVersion( $ruleOpt{ 'farmName' } )

		  #~ . " -A INPUT -t filter "         # select iptables struct
		  . " -A $chain -t filter "                           # select iptables struct
		  . "$dest $ruleOpt{ 'protocol' } $port "             # who is destined
		  . "-m connlimit --connlimit-above $limit_conns "    # rules for block
		  . "-m comment --comment \"DOS_${ruleName}_$ruleOpt{ 'farmName' }\""; # comment

		my $output =
		  &iptSystem( "$cmd -j LOG  --log-prefix \"$logMsg\" --log-level 4 " );

		$output = &iptSystem( "$cmd -j REJECT --reject-with tcp-reset" );
	}
	if ( $output != 0 )
	{
		&zenlog( "Error appling '$ruleName' rule to farm '$ruleOpt{ 'farmName' }'." );
	}

	return $output;
}

# Only TCP farms
### Limit RST packets ###
# &setDOSLimitRstRule ( ruleOpt )
sub setDOSLimitRstRule
{
	my ( $ruleName, $ruleOptRef ) = @_;
	my %ruleOpt = %{ $ruleOptRef };

	#~ my $rule        = "limitrst";
	my $logMsg = &createLogMsg( $ruleName, $ruleOpt{ 'farmName' } );
	my $limit       = &getDOSParam( $ruleName, 'limit' );
	my $limit_burst = &getDOSParam( $ruleName, 'limit_burst' );

# /sbin/iptables -A PREROUTING -t mangle -p tcp --tcp-flags RST RST -m limit --limit 2/s --limit-burst 2 -j ACCEPT
	my $cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -A PREROUTING -t mangle "    # select iptables struct
	  . "-j ACCEPT $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags RST RST -m limit --limit $limit/s --limit-burst $limit_burst " # rules for block
	  . "-m comment --comment \"DOS_${ruleName}_$ruleOpt{ 'farmName' }\"";          # comment

	my $output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog(
				 "Error appling '${ruleName}_1' rule to farm '$ruleOpt{ 'farmName' }'." );
	}
	else
	{
		# /sbin/iptables -I PREROUTING -t mangle -p tcp --tcp-flags RST RST -j DROP
		$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
		  . " -A PREROUTING -t mangle "    # select iptables struct
		  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
		  . "--tcp-flags RST RST "    # rules for block
		  . "-m comment --comment \"DOS_${ruleName}_$ruleOpt{ 'farmName' }\""; # comment

		my $output = &setIPDSDropAndLog( $cmd, $logMsg );
		if ( $output != 0 )
		{
			&zenlog(
					 "Error appling '${ruleName}_2' rule to farm '$ruleOpt{ 'farmName' }'." );
		}
	}
	return $output;
}

### Limit new TCP connections per second per source IP ###
# &setDOSLimitSecRule ( ruleOpt )
sub setDOSLimitSecRule
{
	my ( $ruleName, $ruleOptRef ) = @_;
	my %ruleOpt = %{ $ruleOptRef };

	#~ my $rule        = "limitsec";
	my $logMsg = &createLogMsg( $ruleName, $ruleOpt{ 'farmName' } );
	my $limit       = &getDOSParam( $ruleName, 'limit' );
	my $limit_burst = &getDOSParam( $ruleName, 'limit_burst' );

# /sbin/iptables -I PREROUTING -t mangle -p tcp -m conntrack --ctstate NEW -m limit --limit 60/s --limit-burst 20 -j ACCEPT
	my $cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -A PREROUTING -t mangle "    # select iptables struct
	  . "-j ACCEPT $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "-m conntrack --ctstate NEW -m limit --limit $limit/s --limit-burst $limit_burst " # rules for block
	  . "-m comment --comment \"DOS_${ruleName}_$ruleOpt{ 'farmName' }\"";                 # comment

	my $output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog(
				 "Error appling '${ruleName}_1' rule to farm '$ruleOpt{ 'farmName' }'." );
	}
	else
	{
	  # /sbin/iptables -I PREROUTING -t mangle -p tcp -m conntrack --ctstate NEW -j DROP
		$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
		  . " -A PREROUTING -t mangle "    # select iptables struct
		  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
		  . "-m conntrack --ctstate NEW "    # rules for block
		  . "-m comment --comment \"DOS_${ruleName}_$ruleOpt{ 'farmName' }\""; # comment

		my $output = &setIPDSDropAndLog( $cmd, $logMsg );
		if ( $output != 0 )
		{
			&zenlog(
					 "Error appling '${ruleName}_2' rule to farm '$ruleOpt{ 'farmName' }'." );
		}
	}
	return $output;
}

# All balancer
###  Drop ICMP ###
# &setDOSDropIcmpRule ( ruleOpt )
sub setDOSDropIcmpRule
{
	my $rule = "drop_icmp";

	#~ my $rule    = "dropicmp";
	my $logMsg = &createLogMsg( $rule );

	# /sbin/iptables -t raw -A PREROUTING -p icmp -j DROP
	my $cmd = &getGlobalConfiguration( 'iptables' )
	  . " -t raw -A PREROUTING "                   # select iptables struct
	  . "-p icmp "                                 # rules for block
	  . "-m comment --comment \"DOS_${rule}\"";    # comment

	my $output = &setIPDSDropAndLog( $cmd, $logMsg );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '$rule' rule." );
	}

	return $output;
}

=begin nd
        Function: setDOSSshBruteForceRule

        This rule is a protection against brute-force atacks to ssh protocol.
        This rule applies to the balancer

        Parameters:
				
        Returns:
				== 0	- successful
                != 0	- error

=cut

# balancer
### SSH brute-force protection ###
# &setDOSSshBruteForceRule
sub setDOSSshBruteForceRule
{
	my $rule = 'ssh_brute_force';

	#~ my $rule    = "sshbruteforce";
	my $hits = &getDOSParam( $rule, 'hits' );
	my $time = &getDOSParam( $rule, 'time' );

	#~ my $port = &getDOSParam( $rule, 'port' );
	require Zevenet::System::SSH;
	my $sshconf = &getSsh();
	my $port    = $sshconf->{ 'port' };
	my $logMsg  = &createLogMsg( $rule );
	my $output;
	my $cmd;

	# If the cluster is configurated, will add an exception to the remote node
	# /sbin/iptables -A PREROUTING -t mangle -s $clusterIP -j ACCEPT
	require "/usr/local/zenloadbalancer/www/zcluster_functions.cgi";
	if ( &getZClusterStatus() )
	{
		my $remoteHost        = getZClusterRemoteHost();
		my $cl_conf           = &getZClusterConfig();
		my $remoteClusterNode = $cl_conf->{ $remoteHost }->{ ip };

		$cmd =
		  &getGlobalConfiguration( 'iptables' )
		  . " -A PREROUTING -t mangle "                        # select iptables struct
		  . "-s $remoteClusterNode -j ACCEPT "                 # who is destined
		  . "-m comment --comment \"DOS_${rule}_cluster\"";    # comment

		$output = &iptSystem( $cmd );
		if ( $output != 0 )
		{
			&zenlog( "Error appling '${rule}_cluster' rule." );
		}
	}

# /sbin/iptables -I PREROUTING -t mangle -p tcp --dport ssh -m conntrack --ctstate NEW -m recent --set
	$cmd =
	  &getGlobalConfiguration( 'iptables' )
	  . " -A PREROUTING -t mangle "                      # select iptables struct
	  . "-p tcp --dport $port "                          # who is destined
	  . "-m conntrack --ctstate NEW -m recent --set "    # rules for block
	  . "-m comment --comment \"DOS_$rule\"";            # comment

	$output = &iptSystem( $cmd );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${rule}_1' rule." );
	}

# /sbin/iptables -I PREROUTING -t mangle -p tcp --dport ssh -m conntrack --ctstate NEW -m recent --update --seconds 60 --hitcount 10 -j DROP
	$cmd =
	  &getGlobalConfiguration( 'iptables' )
	  . " -A PREROUTING -t mangle "                      # select iptables struct
	  . "-p tcp --dport $port "                          # who is destined
	  . "-m conntrack --ctstate NEW -m recent --update --seconds $time --hitcount $hits " # rules for block
	  . "-m comment --comment \"DOS_$rule\"";                                             # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	if ( $output != 0 )
	{
		&zenlog( "Error appling '${rule}_2' rule." );
	}

	return $output;
}

1;
