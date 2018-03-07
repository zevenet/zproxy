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
Function: getIPDSChain

	Return the name of a iptables chain where there are rules of a module.

Parameters:
	Module - It is a IPDS module. The possible values are "blacklist", "whitelist", "dos" or "rbl"
				
Returns:
	String - Name for the chain of a IPDS module
	
=cut

sub getIPDSChain
{
	my $ipds_module = shift;
	my %ipds_chains = (
		'blacklist' => 'BLACKLIST',
		'whitelist' => 'WHITELIST',
		'rbl'       => 'RBL',

		'dos' => 'DOS',	# DoS uses different chains of netfilter
	);

	return $ipds_chains{ $ipds_module };
}

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
	my $iptlock = &getGlobalConfiguration( 'iptlock' );

	if ( $table ne '' )
	{
		$table = "--table $table";
	}

	my $iptables_command = &getGlobalConfiguration( 'iptables' )
	  . " $table -L $chain -n -v --line-numbers 2>/dev/null";

	## lock iptables use ##
	open my $ipt_lockfile, '>', $iptlock;
	&setIptLock( $ipt_lockfile );

	my @ipt_output = `$iptables_command`;
	&zenlog( "failed: $iptables_command", "error", "IPDS" ) if $?;

	## unlock iptables use ##
	&setIptUnlock( $ipt_lockfile );
	close $ipt_lockfile;

	return @ipt_output;
}

# LOGS
# &setIPDSDropAndLog ( $cmd, $logMsg );
sub setIPDSDropAndLog
{
	my ( $cmd, $logMsg ) = @_;
	my $output;

	return 0 if ( &getIPDSRuleExists( "$cmd -j DROP" ) );

	# Always LOG rule has to be above than DROP rule
	if ( $cmd =~ / -I / )
	{
		$output = &iptSystem( "$cmd -j DROP" );
		$output = &iptSystem( "$cmd -j LOG  --log-prefix \"$logMsg\" --log-level 4 " );
	}

	# $cmd =~ / -A /
	else
	{
		$output = &iptSystem( "$cmd -j LOG  --log-prefix \"$logMsg\" --log-level 4 " );
		$output = &iptSystem( "$cmd -j DROP" );
	}

	return $output;
}

# check if a rule exists. Return 1 if it exists or 0 if it is not
sub getIPDSRuleExists
{
	my $check_cmd = shift;
	my $output    = 0;
	$check_cmd =~ s/ \-[AI] / --check /;

	$output = 1 if ( !&iptSystem( $check_cmd ) );

	return $output;
}

#
# &createLogMsg ( module, rule, farm );
sub createLogMsg
{
	my $module   = shift;
	my $rule     = shift;
	my $farmname = shift;

	my $max_size = 29;

	my $msg  = "[$module,$rule,$farmname]";
	my $size = length $msg;
	if ( $size > $max_size )
	{
		$farmname = substr ( $farmname, 0, 9 );
		chop $farmname;
		$farmname = "$farmname#";
		$rule     = substr ( $rule, 0, 9 );
		$msg      = "[$module,$rule,$farmname]";
	}

	return $msg;
}

# Get all IPDS rules applied to a farm
sub getIPDSfarmsRules
{
	my $farmName = shift;

	require Config::Tiny;

	my $rules;
	my $fileHandle;
	my @dosRules        = ();
	my @blacklistsRules = ();
	my @rblRules        = ();

	my $dosConf        = &getGlobalConfiguration( 'dosConf' );
	my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
	my $rblPath        = &getGlobalConfiguration( 'configdir' ) . "/ipds/rbl";
	my $rblConf        = "$rblPath/rbl.conf";

	if ( -e $dosConf )
	{
		$fileHandle = Config::Tiny->read( $dosConf );
		foreach my $key ( keys %{ $fileHandle } )
		{
			if ( exists $fileHandle->{ $key }->{'farms'} && $fileHandle->{ $key }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
			{
				my $status = $fileHandle->{ $key }->{ 'status' } || "down";
				push @dosRules, { 'name' => $key, 'status' => $status };
			}
		}
	}

	if ( -e $blacklistsConf )
	{
		$fileHandle = Config::Tiny->read( $blacklistsConf );
		foreach my $key ( keys %{ $fileHandle } )
		{
			if ( $fileHandle->{ $key }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
			{
				my $status = $fileHandle->{ $key }->{ 'status' } || "down";
				push @blacklistsRules, { 'name' => $key, 'status' => $status };
			}
		}
	}

	if ( -e $rblConf )
	{
		$fileHandle = Config::Tiny->read( $rblConf );
		foreach my $key ( keys %{ $fileHandle } )
		{
			if ( $fileHandle->{ $key }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
			{
				my $status = $fileHandle->{ $key }->{ 'status' } || "down";
				push @rblRules, { 'name' => $key, 'status' => $status };
			}
		}
	}

	$rules =
	  { dos => \@dosRules, blacklists => \@blacklistsRules, rbl => \@rblRules };
	return $rules;
}

# Get all IPDS rules
sub getIPDSRules
{
	require Config::Tiny;

	my @rules;
	my $fileHandle;

	my $dosConf        = &getGlobalConfiguration( 'dosConf' );
	my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
	my $rblPath        = &getGlobalConfiguration( 'configdir' ) . "/ipds/rbl";
	my $rblConf        = "$rblPath/rbl.conf";

	if ( -e $dosConf )
	{
		$fileHandle = Config::Tiny->read( $dosConf );
		foreach my $key ( keys %{ $fileHandle } )
		{
			push @rules,
			  {
				'name' => $key,
				'rule' => 'dos',
				'type' => $fileHandle->{ $key }->{ type }
			  };
		}
	}

	if ( -e $blacklistsConf )
	{
		$fileHandle = Config::Tiny->read( $blacklistsConf );
		foreach my $key ( keys %{ $fileHandle } )
		{
			push @rules, { 'name' => $key, 'rule' => 'blacklist' };
		}
	}

	if ( -e $rblConf )
	{
		$fileHandle = Config::Tiny->read( $rblConf );
		foreach my $key ( keys %{ $fileHandle } )
		{
			push @rules, { 'name' => $key, 'rule' => 'rbl' };
		}
	}

	return \@rules;
}

1;
