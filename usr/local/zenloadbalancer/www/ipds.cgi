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
	my $iptlock = &getGlobalConfiguration ( 'iptlock' );

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


# LOGS
# &setIPDSDropAndLog ( $cmd, $logMsg );
sub setIPDSDropAndLog
{
	my ( $cmd, $logMsg ) = @_;

	my $output = &iptSystem( "$cmd -j LOG  --log-prefix \"$logMsg\" --log-level 4 " );
	$output = &iptSystem( "$cmd -j DROP" );

	return $output;
}

# 
# &createLogMsg ( rule, farm );
sub createLogMsg
{
	my $rule = shift;
	my $farmname = shift;
	
	my $max_size = 29;
	
	my $msg = "[IPDS, $rule $farmname]";
	my $size = length $msg;
	if ( $size > $max_size  )
	{
		$farmname = substr($farmname,0,9);
		chop $farmname;
		$farmname = "$farmname#";
		$rule = substr($rule,0,9);
		$msg = "[IPDS, $rule $farmname]";
	}
	
	return $msg;
}


# Get all IPDS rules applied to a farm
sub getIPDSfarmsRules
{
	my $farmName = shift;
	my $rules;
	my @dosRules;
	my @blacklistsRules;
	my $fileHandle;
	
	my $dosConf = &getGlobalConfiguration( 'dosConf' );
	my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
	if ( -e $dosConf )
	{
		$fileHandle = Config::Tiny->read( $dosConf );
		foreach my $key ( keys %{ $fileHandle } )
		{
			if ( $fileHandle->{ $key }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
			{
				push @dosRules, $key;
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
				push @blacklistsRules, $key;
			}
		}
	}
	
	$rules = { dos => \@dosRules, blacklists => \@blacklistsRules };
	return $rules;
}

1;
