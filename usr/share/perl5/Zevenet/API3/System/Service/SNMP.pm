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

use Zevenet::SNMP;

# GET /system/snmp
sub get_snmp
{
	my $description = "Get snmp";
	my %snmp        = %{ &getSnmpdConfig() };
	$snmp{ 'status' } = &getSnmpdStatus();
	
	
	&httpResponse(
		   { code => 200, body => { description => $description, params => \%snmp } } );
}

#  POST /system/snmp
sub set_snmp
{
	my $json_obj    = shift;
	my $description = "Post snmp";
	my $errormsg;
	my @allowParams = ( "port", "status", "ip", "community", "scope" );

	$errormsg = &getValidOptParams( $json_obj, \@allowParams );
	if ( !$errormsg )
	{
		# Check key format
		foreach my $key ( keys %{ $json_obj } )
		{
			if ( !&getValidFormat( "snmp_$key", $json_obj->{ $key } ) )
			{
				$errormsg = "$key hasn't a correct format.";
				last;
			}
		}
		#~ # check if listen exists
		#~ if ( exists $json_obj->{ 'ip' } && $json_obj->{ 'ip' } ne '*'
				#~ && !$errormsg )
		#~ {
			#~ my $flag;
			#~ foreach my $iface ( @{ &getActiveInterfaceList() } )
			#~ {
				#~ if ( $json_obj->{ 'ip' } eq $iface->{ addr } )
				#~ {
					#~ $flag = 1;
					#~ if ( $iface->{ vini } ne '' )    # discard virtual interfaces
					#~ {
						#~ $errormsg = "Virtual interface canot be configurate as http interface.";
					#~ }
					#~ else
					#~ {
						#~ $interface = $iface;
					#~ }
					#~ last;
				#~ }
			#~ }
			#~ $errormsg = "Ip $json_obj->{ 'ip' } not found in system." if ( !$flag );
		#~ }
		
		if ( !$errormsg )
		{
			my $status = $json_obj->{ 'status' };
			delete $json_obj->{ 'status' };
			my $snmp = &getSnmpdConfig();
			
			foreach my $key ( keys %{ $json_obj } )
			{
				$snmp->{ $key } = $json_obj->{ $key };
			}
			
			$errormsg = &setSnmpdConfig( $snmp );
			if ( !$errormsg )
			{
				if ( !$status && &getSnmpdStatus() eq 'true' )
				{
					&setSnmpdStatus( 'false' );    # stopping snmp
					&setSnmpdStatus( 'true' );     # starting snmp
				}
				elsif ( $status eq 'true' && &getSnmpdStatus() eq 'false' )
				{
					&setSnmpdStatus( 'true' );     # starting snmp
				}
				elsif ( $status eq 'false' && &getSnmpdStatus() eq 'true' )
				{
					&setSnmpdStatus( 'false' );    # stopping snmp
				}
				if ( !$errormsg )
				{
					$snmp->{ status } = &getSnmpdStatus();
					&httpResponse(
							{ code => 200, body => { description => $description, params => $snmp } } );
				}
			}
			else
			{
				$errormsg = "There was a error modifying ssh.";
			}
		}
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

1;
