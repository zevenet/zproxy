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


use warnings;
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


# Get all IPDS rules applied to a farm
sub getIPDSfarmsRules
{
	my $farmName = shift;
	my $rules;
	my @ddosRules;
	my @blacklistsRules;
	my $fileHandle;
	
	my $ddosConf = &getGlobalConfiguration( 'ddosConf' );
	my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
	if ( -e $ddosConf )
	{
		$fileHandle = Config::Tiny->read( $ddosConf );
		foreach my $key ( keys %{ $fileHandle } )
		{
			if ( $fileHandle->{ $key }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
			{
				push @ddosRules, $key;
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
	
	$rules = { ddos => \@ddosRules, blacklists => \@blacklistsRules };
	return $rules;
}

1;









