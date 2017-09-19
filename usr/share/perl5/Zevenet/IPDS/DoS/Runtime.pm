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

use Zevenet::Netfilter;
use Zevenet::IPDS::Core;
use Zevenet::IPDS::DoS::Core;

=begin nd
Function: setDOSRunRule

	Wrapper that get the farm values and launch the necessary function to 
	start run the iptables rule

Parameters:
	rule	 - Rule name
	farmname - farm name
				
Returns:
	Integer - Error code: 0 on success or other value on failure

=cut

sub setDOSRunRule
{
	my ( $ruleName, $farmName ) = @_;

	require Zevenet::Farm::Base;

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

	use Switch;
	switch ( &getDOSParam( $ruleName, "rule" ) )
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

	$output = ( @{ &getDOSLookForRule( $ruleName, $farmName ) } ) ? 0 : 1;

	return $output;
}

=begin nd
Function: setDOSStopRule

	Remove iptables rules

Parameters:
	ruleName		- id that indetify a rule, ( rule = 'farms' to remove rules from farm )
	farmname 	- farm name
				
Returns:
	Integer - Error code, 0 on success or other value on failure

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

	$output = ( @{ &getDOSLookForRule( $ruleName, $farmName ) } ) ? 1 : 0;
	return $output;
}

=begin nd
Function: setDOSBogusTcpFlagsRule

	Run the iptables rules necessary to control bogus in tcp flags.
	This rule only can be applied to farms working with TCP protocol.

Parameters:
	ruleName	- Rule name
	farmname 	- Farm name
				
Returns:
	Integer - Error code, 0 on success or other value on failure

=cut

sub setDOSBogusTcpFlagsRule
{
	my ( $ruleName, $ruleOptRef ) = @_;
	my %ruleOpt = %{ $ruleOptRef };

	require Zevenet::IPDS::Core;
	my $chain = &getIPDSChain( 'dos' );
	my $table = "mangle";

	#~ my $rule    = "bogustcpflags";
	my $logMsg = &createLogMsg( "DOS", $ruleName, $ruleOpt{ 'farmName' } );

# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags FIN,SYN,RST,PSH,ACK,URG NONE -j DROP
	my $cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t $table -I $chain "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags FIN,SYN,RST,PSH,ACK,URG NONE "    # rules for block
	  . "-m comment --comment \"DOS,${ruleName},$ruleOpt{ 'farmName' }\""; # comment

	my $output = &setIPDSDropAndLog( $cmd, $logMsg );
	return $output if ( $output );

	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags FIN,SYN FIN,SYN -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t $table -I $chain "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags FIN,SYN FIN,SYN "    # rules for block
	  . "-m comment --comment \"DOS,${ruleName},$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	return $output if ( $output );

	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags SYN,RST SYN,RST -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t $table -I $chain "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags SYN,RST SYN,RST "    # rules for block
	  . "-m comment --comment \"DOS,${ruleName},$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	return $output if ( $output );

	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags SYN,FIN SYN,FIN -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t $table -I $chain "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags SYN,FIN SYN,FIN "    # rules for block
	  . "-m comment --comment \"DOS,${ruleName},$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	return $output if ( $output );

	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags FIN,RST FIN,RST -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t $table -I $chain "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags FIN,RST FIN,RST "    # rules for block
	  . "-m comment --comment \"DOS,${ruleName},$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	return $output if ( $output );

	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags FIN,ACK FIN -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t $table -I $chain "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags FIN,ACK FIN "    # rules for block
	  . "-m comment --comment \"DOS,${ruleName},$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	return $output if ( $output );

	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags ACK,URG URG -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t $table -I $chain "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags ACK,URG URG "    # rules for block
	  . "-m comment --comment \"DOS,${ruleName},$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	return $output if ( $output );

	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags ACK,FIN FIN -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t $table -I $chain "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags ACK,FIN FIN "    # rules for block
	  . "-m comment --comment \"DOS,${ruleName},$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	return $output if ( $output );

	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags ACK,PSH PSH -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t $table -I $chain "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags ACK,PSH PSH "    # rules for block
	  . "-m comment --comment \"DOS,${ruleName},$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	return $output if ( $output );

	#  Christmas tree packet. Used to analyze tcp response and to elaborate a atack
	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags ALL ALL -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t $table -I $chain "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags ALL ALL "    # rules for block
	  . "-m comment --comment \"DOS,${ruleName},$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	return $output if ( $output );

	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags ALL NONE -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t $table -I $chain "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags ALL NONE "    # rules for block
	  . "-m comment --comment \"DOS,${ruleName},$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	return $output if ( $output );

	# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags ALL FIN,PSH,URG -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t $table -I $chain "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags ALL FIN,PSH,URG "    # rules for block
	  . "-m comment --comment \"DOS,${ruleName},$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	return $output if ( $output );

# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags ALL SYN,FIN,PSH,URG -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t $table -I $chain "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags ALL SYN,FIN,PSH,URG "    # rules for block
	  . "-m comment --comment \"DOS,${ruleName},$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	return $output if ( $output );

# /sbin/iptables -t raw -A PREROUTING -p tcp --tcp-flags ALL SYN,RST,ACK,FIN,URG -j DROP
	$cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -t $table -I $chain "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags ALL SYN,RST,ACK,FIN,URG "    # rules for block
	  . "-m comment --comment \"DOS,${ruleName},$ruleOpt{ 'farmName' }\""; # comment

	$output = &setIPDSDropAndLog( $cmd, $logMsg );
	return $output;
}

=begin nd
Function: setDOSLimitConnsRule

	Run the iptables rules necessary to reject connections when a source IP reach the limit of connections.
	This rule only can be applied to farms working with TCP protocol.

Parameters:
	ruleName	- Rule name
	farmname 	- Farm name
				
Returns:
	Integer - Error code, 0 on success or other value on failure

=cut

sub setDOSLimitConnsRule
{
	my ( $ruleName, $ruleOptRef ) = @_;
	my %ruleOpt = %{ $ruleOptRef };

	require Zevenet::IPDS::Core;
	my $chain = &getIPDSChain( 'dos' );
	my $table = "mangle";

	#~ my $rule    = "limitconns";
	my $logMsg = &createLogMsg( "DOS", $ruleName, $ruleOpt{ 'farmName' } );

	#~ my $chain = "INPUT";               # default, this chain is for L7 apps
	my $dest = $ruleOpt{ 'vip' };
	my $port = $ruleOpt{ 'vport' };
	my $output;
	my $limit_conns = &getDOSParam( $ruleName, 'limit_conns' );

	# /sbin/iptables -A FORWARD -t filter -d 1.1.1.1,54.12.1.1 -p tcp --dport 5 -m connlimit --connlimit-above 5 -m comment --comment "DOS_limitconns_aa" -j REJECT --reject-with tcp-reset
	my $cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -I $chain -t $table "                           # select iptables struct
	  . "$dest $ruleOpt{ 'protocol' } $port "             # who is destined
	  . "-m connlimit --connlimit-above $limit_conns "    # rules for block
	  . "-m comment --comment \"DOS,${ruleName},$ruleOpt{ 'farmName' }\""; # comment

	# thre rule already exists
	return 0 if ( &getIPDSRuleExists( "$cmd -j DROP" ) );

	$output = &iptSystem( "$cmd -j LOG --log-prefix \"$logMsg\" --log-level 4 " );
	$output = &iptSystem( "$cmd -j DROP" );

	return $output;
}

=begin nd
Function: setDOSLimitRstRule

	Run the iptables rules necessary to limit the number of RST packet for a TCP per second for a connection.
	This rule only can be applied to farms working with TCP protocol.

Parameters:
	ruleName	- Rule name
	farmname 	- Farm name
				
Returns:
	Integer - Error code, 0 on success or other value on failure

=cut

sub setDOSLimitRstRule
{
	my ( $ruleName, $ruleOptRef ) = @_;
	my %ruleOpt = %{ $ruleOptRef };

	require Zevenet::IPDS::Core;
	my $chain = &getIPDSChain( 'dos' );
	my $table = "mangle";

	#~ my $rule        = "limitrst";
	my $logMsg = &createLogMsg( "DOS", $ruleName, $ruleOpt{ 'farmName' } );
	my $limit       = &getDOSParam( $ruleName, 'limit' );
	my $limit_burst = &getDOSParam( $ruleName, 'limit_burst' );

# /sbin/iptables -A PREROUTING -t mangle -p tcp --tcp-flags RST RST -m limit --limit 2/s --limit-burst 2 -j ACCEPT
	my $cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -I $chain -t $table "    # select iptables struct
	  . "-j ACCEPT $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags RST RST -m limit --limit $limit/s --limit-burst $limit_burst " # rules for block
	  . "-m comment --comment \"DOS,${ruleName},$ruleOpt{ 'farmName' }\"";          # comment

	# /sbin/iptables -I PREROUTING -t mangle -p tcp --tcp-flags RST RST -j DROP
	my $cmd2 = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -I $chain -t $table "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "--tcp-flags RST RST "    # rules for block
	  . "-m comment --comment \"DOS,${ruleName},$ruleOpt{ 'farmName' }\""; # comment

	# thre rule already exists
	return 0 if ( &getIPDSRuleExists( $cmd ) );

	my $output = &setIPDSDropAndLog( $cmd2, $logMsg );
	return $output if ( $output );

	$output = &iptSystem( $cmd );
	return $output;
}

=begin nd
Function: setDOSLimitSecRule

	Run the iptables rules necessary to limit the number of new connections per second.

Parameters:
	ruleName	- Rule name
	farmname 	- Farm name
				
Returns:
	Integer - Error code, 0 on success or other value on failure

=cut

sub setDOSLimitSecRule
{
	my ( $ruleName, $ruleOptRef ) = @_;
	my %ruleOpt = %{ $ruleOptRef };

	require Zevenet::IPDS::Core;
	my $chain = &getIPDSChain( 'dos' );
	my $table = "mangle";

	#~ my $rule        = "limitsec";
	my $logMsg = &createLogMsg( "DOS", $ruleName, $ruleOpt{ 'farmName' } );
	my $limit       = &getDOSParam( $ruleName, 'limit' );
	my $limit_burst = &getDOSParam( $ruleName, 'limit_burst' );

# /sbin/iptables -I PREROUTING -t mangle -p tcp -m conntrack --ctstate NEW -m limit --limit 60/s --limit-burst 20 -j ACCEPT
	my $cmd = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -I $chain -t $table "    # select iptables struct
	  . "-j ACCEPT $ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "-m conntrack --ctstate NEW -m limit --limit $limit/s --limit-burst $limit_burst " # rules for block
	  . "-m comment --comment \"DOS,${ruleName},$ruleOpt{ 'farmName' }\"";                 # comment

  # /sbin/iptables -I PREROUTING -t mangle -p tcp -m conntrack --ctstate NEW -j DROP
	my $cmd2 = &getBinVersion( $ruleOpt{ 'farmName' } )
	  . " -I $chain -t $table "    # select iptables struct
	  . "$ruleOpt{ 'vip' } $ruleOpt{ 'protocol' } $ruleOpt{ 'vport' } " # who is destined
	  . "-m conntrack --ctstate NEW "    # rules for block
	  . "-m comment --comment \"DOS,${ruleName},$ruleOpt{ 'farmName' }\""; # comment

	# thre rule already exists
	return 0 if ( &getIPDSRuleExists( $cmd ) );

	my $output = &setIPDSDropAndLog( $cmd2, $logMsg );
	return $output if ( $output );

	$output = &iptSystem( $cmd );

	return $output;
}

=begin nd
Function: setDOSDropIcmpRule

	This rule applies the necessary rules to desable the ping response
	This rule applies to the balancer.

Parameters:
	none -.

Returns:
	Integer - Code error: 0 on success or other value on failure

=cut

sub setDOSDropIcmpRule
{
	my $rule = "drop_icmp";

	#~ my $rule    = "dropicmp";
	my $logMsg = &createLogMsg( $rule );

	# /sbin/iptables -t raw -A PREROUTING -p icmp -j DROP
	my $cmd = &getGlobalConfiguration( 'iptables' )
	  . " -t raw -I PREROUTING "                   # select iptables struct
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
	none -.

Returns:
	Integer - Code error: 0 on success or other value on failure

=cut

sub setDOSSshBruteForceRule
{
	require Zevenet::System::SSH;

	require Zevenet::IPDS::Core;
	my $chain = &getIPDSChain( 'dos' );
	my $table = "mangle";

	my $rule = 'ssh_brute_force';
	my $hits = &getDOSParam( $rule, 'hits' );
	my $time = &getDOSParam( $rule, 'time' );

	#~ my $port = &getDOSParam( $rule, 'port' );
	my $sshconf = &getSsh();
	my $port    = $sshconf->{ 'port' };
	my $logMsg  = &createLogMsg( $rule );
	my $output;

# /sbin/iptables -I PREROUTING -t mangle -p tcp --dport ssh -m conntrack --ctstate NEW -m recent --set
	my $cmd =
	  &getGlobalConfiguration( 'iptables' )
	  . " -I $chain -t $table "                          # select iptables struct
	  . "-p tcp --dport $port "                          # who is destined
	  . "-m conntrack --ctstate NEW -m recent --set "    # rules for block
	  . "-m comment --comment \"DOS,$rule\"";            # comment

# /sbin/iptables -I PREROUTING -t mangle -p tcp --dport ssh -m conntrack --ctstate NEW -m recent --update --seconds 60 --hitcount 10 -j DROP
	my $cmd2 =
	  &getGlobalConfiguration( 'iptables' )
	  . " -I $chain -t $table "                          # select iptables struct
	  . "-p tcp --dport $port "                          # who is destined
	  . "-m conntrack --ctstate NEW -m recent --update --seconds $time --hitcount $hits " # rules for block
	  . "-m comment --comment \"DOS,$rule\"";                                             # comment

	# thre rule already exists
	return 0 if ( &getIPDSRuleExists( $cmd ) );

	$output = &setIPDSDropAndLog( $cmd2, $logMsg );
	return $output if ( $output );

	$output = &iptSystem( $cmd );
	return $output;
}

=begin nd
Function: setDOSApplyRule
	
	Enable a DoS rule for rules of farm or system type
	Farm type: Link a DoS rule with a farm
	System type: Put rule in up status

Parameters:
	rule	- Rule name
	farmname - Farm name
				
Returns:
	Integer - Error code. 0 on succes or other value on failure.

=cut

sub setDOSApplyRule
{
	my ( $ruleName, $farmName ) = @_;

	require Zevenet::Farm::Base;
	require Config::Tiny;

	my $confFile = &getGlobalConfiguration( 'dosConf' );
	my $output;
	my $rule = &getDOSParam( $ruleName, 'rule' );
	my $protocol = &getFarmProto( $farmName );

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

	my $fileHandle = Config::Tiny->read( $confFile );

	if ( $farmName )
	{
		my $farmList = $fileHandle->{ $ruleName }->{ 'farms' };
		if ( $farmList !~ /(^| )$farmName( |$)/ )
		{
			$fileHandle = Config::Tiny->read( $confFile );
			$fileHandle->{ $ruleName }->{ 'farms' } = "$farmList $farmName";
			$fileHandle->write( $confFile );
		}
		else
		{
			&zenlog( "Rule $ruleName only is available for TCP protocol" );
		}

		if ( &getFarmBootStatus( $farmName ) eq "up" )
		{
			$output = &setDOSRunRule( $ruleName, $farmName );
			if ( $output )
			{
				&zenlog( "Error, running rule $ruleName to farm $farmName" );
			}
		}
	}

	# check param is down
	elsif ( $fileHandle->{ $ruleName }->{ 'status' } ne "up" )
	{
		$fileHandle->{ $ruleName }->{ 'status' } = "up";
		$fileHandle->write( $confFile );

		$output = &setDOSRunRule( $ruleName );
		if ( $output )
		{
			&zenlog( "Error, running rule $ruleName" );
		}
	}

	return $output;
}

=begin nd

Function: setDOSUnsetRule
	
	Enable a DoS rule for rules of farm or system type
	Farm type: Unlink a DoS rule with a farm
	System type: Put rule in down status

Parameters:
	rule	- Rule name
	farmname - Farm name
				
Returns:
	Integer - Error code. 0 on succes or other value on failure.

=cut

sub setDOSUnsetRule
{
	my ( $ruleName, $farmName ) = @_;

	require Config::Tiny;

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

1;
