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

#~ use Zevenet::Core;
#~ use Zevenet::Debug;
use Zevenet::IPDS::RBL;
use Zevenet::IPDS::Blacklist;
use Zevenet::IPDS::DoS;



=begin nd
Function: addIPDSIptablesChain

	This function create the iptables chains where the IPDS rules will be created

Parameters:
	none - .			
				
Returns:
	Integer - Error code: 0 on success or other value on failure
	
=cut

sub addIPDSIptablesChain
{
	my $whitelist_chain = &getIPDSChain("whitelist");
	my $blacklist_chain = &getIPDSChain("blacklist");
	my $rbl_chain = &getIPDSChain("rbl");
	
	# create chains
	my $error = &iptSystem( "iptables -N $whitelist_chain -t raw" );
	$error = &iptSystem( "iptables -N $blacklist_chain -t raw" ) if (!$error);
	$error = &iptSystem( "iptables -N $rbl_chain -t raw" ) if (!$error);
	
	# link this chains
	$error = &iptSystem( "iptables -A PREROUTING -t raw -j $whitelist_chain" ) if (!$error);
	$error = &iptSystem( "iptables -A $whitelist_chain -t raw -j $blacklist_chain" ) if (!$error);
	$error = &iptSystem( "iptables -A $blacklist_chain -t raw -j $rbl_chain" ) if (!$error);
	
	# last sentence in each chain is return to above chain
	$error = &iptSystem( "iptables -A $whitelist_chain -t raw -j RETURN" ) if (!$error);
	$error = &iptSystem( "iptables -A $blacklist_chain -t raw -j RETURN" ) if (!$error);
	$error = &iptSystem( "iptables -A $rbl_chain -t raw -j RETURN" ) if (!$error);
	
	if ($error)
	{
		&zenlog( "Error creating iptables chains" );
	}
	
	return $error;
}


=begin nd
Function: delIPDSIptablesChain

	This function delete the iptables chains where the IPDS rules are created

Parameters:
	none - .			
				
Returns:
	Integer - Error code: 0 on success or other value on failure
	
=cut

sub delIPDSIptablesChain
{
	my $whitelist_chain = &getIPDSChain("whitelist");
	my $blacklist_chain = &getIPDSChain("blacklist");
	my $rbl_chain = &getIPDSChain("rbl");
	
	my $error = &iptSystem( "iptables -F $whitelist_chain -t raw" );
	my $error = &iptSystem( "iptables -F $blacklist_chain -t raw" );
	my $error = &iptSystem( "iptables -F $rbl_chain -t raw" );

	$error = &iptSystem( "iptables -D PREROUTING -t raw -j $whitelist_chain" ) if (!$error);

	$error = &iptSystem( "iptables -X $blacklist_chain -t raw" ) if (!$error);
	$error = &iptSystem( "iptables -X $whitelist_chain -t raw" ) if (!$error);
	$error = &iptSystem( "iptables -X $rbl_chain -t raw" ) if (!$error);
	
	return $error;
}



=begin nd
Function: runIPDSStartModule

        Boot the IPDS module

Parameters:
				
Returns:
	none - .
	
=cut

sub runIPDSStartModule
{
	&addIPDSIptablesChain();
	
	&runBLStartModule();
	&runRBLStartModule();
	&runDOSStartModule();
}

=begin nd
Function: runIPDSStopModule

        Stop the IPDS module

Parameters:
				
Returns:
	none - .

=cut

sub runIPDSStopModule
{
	&runRBLStopModule();
	&runBLStopModule();
	&runDOStopModule();
	
	&delIPDSIptablesChain();
}


1;
