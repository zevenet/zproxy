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
Function: getZapiWAFRule

	Adjust the format for zapi of the WAF rule object

Parameters:
	rule - Rule struct

Returns:
	Hash ref - Configuration of a rule

=cut

sub getZapiWAFRule
{
	my $rule = shift;

	include 'Zevenet::IPDS::WAF::Core';
	my $out = {
		'definition' => {
						  'id'          => $rule->{ definition }->{ id }          // '',
						  'description' => $rule->{ definition }->{ description } // '',
		},
		'information' => {
						   'tag'      => $rule->{ information }->{ tag }      // [],
						   'version'  => $rule->{ information }->{ version }  // '',
						   'maturity' => $rule->{ information }->{ maturity } // '',
						   'severity' => $rule->{ information }->{ severity } // '',
						   'accuracy' => $rule->{ information }->{ accuracy } // '',
						   'revision' => $rule->{ information }->{ revision } // '',
		},
		'match' => {
					 'phase'           => $rule->{ match }->{ phase }           // '',
					 'variables'       => $rule->{ match }->{ variables }       // [],
					 'transformations' => $rule->{ match }->{ transformations } // [],
					 'multiMatch'      => $rule->{ match }->{ multiMatch }      // '',
					 'operator'        => $rule->{ match }->{ operator }        // '',
					 'capture'         => $rule->{ match }->{ capture }         // '',
					 'value'           => $rule->{ match }->{ value }           // '',
		},
		'action' => $rule->{ action } // '',
		'logs' => {
					'noLog'      => $rule->{ logs }->{ noLog }      // '',
					'log'        => $rule->{ logs }->{ log }        // '',
					'auditLog'   => $rule->{ logs }->{ auditLog }   // '',
					'noAuditLog' => $rule->{ logs }->{ noAuditLog } // '',
					'logData'    => $rule->{ logs }->{ logData }    // '',
		},
		'setVariables' => {
						'initColection' => $rule->{ setVariables }->{ initColection } // '',
						'setUid'        => $rule->{ setVariables }->{ setUid }        // '',
						'setSid'        => $rule->{ setVariables }->{ setSid }        // '',
						'setVar'        => $rule->{ setVariables }->{ setVar }        // [],
		},
		'flow' => {
					'chain'     => $rule->{ flow }->{ chain }     // '',
					'skip'      => $rule->{ flow }->{ skip }      // '',
					'skipAfter' => $rule->{ flow }->{ skipAfter } // '',
					'exec'      => $rule->{ flow }->{ exec }      // '',
		},
		'control' => $rule->{ control } // '',    # parameter 'ctl' in secrule
	};


	## ?????? debug
	foreach my $key (keys %{$out})
	{
		if ( ref $out->{$key} eq 'HASH' )
		{
			foreach my $key2 ( keys %{$out->{$key}} )
			{
				delete $out->{$key}->{$key2} if( ! $out->{ $key }->{$key2} );
			}
		}
		elsif( ! $out->{ $key } )
		{
			delete $out->{$key};
		}
	}
	### ?????? end debug


	return $out;
}

=begin nd
Function: getZapiRBACUsersAll

	Return a list with all RBAC users and theirs configurations

Parameters:
	None - .

Returns:
	Array ref - User list

=cut

sub getZapiRBACAllUsers
{
	my @allUsers = ();

	foreach my $user ( sort &getRBACUserList() )
	{
		push @allUsers, &getZapiRBACUsers( $user );
	}
	return \@allUsers;
}


sub getZapiWAFSet
{
	my $set = shift;

	include 'Zevenet::IPDS::WAF::Parse';

	my $set_st = &parseWAFSet( $set );

	## ?????? debug
	foreach my $out ( @{ $set_st } )
	{
		foreach my $key ( keys %{$out} )
		{
			if ( ref $out->{$key} eq 'HASH' )
			{
				foreach my $key2 ( keys %{$out->{$key}} )
				{
					delete $out->{$key}->{$key2} if(  ! $out->{ $key }->{$key2} );
				}
			}
			elsif( ! $out->{ $key } )
			{
				delete $out->{$key};
			}
		}
	}
	### ?????? end debug


	return $set_st;
}

1;
