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

include 'Zevenet::IPDS::Core';

########### GET L4XNAT
# GET /farms/<farmname> Request info of a l4xnat Farm

sub farms_name_l4 # ( $farmname )
{
	my $farmname = shift;

	my $out_p;
	my @out_b;

	my $farm_st = &getL4FarmStruct( $farmname );

	if ( $farm_st{ vport } =~ /^\d+$/ )
	{
		$farm_st{ vport } = $farm_st{ vport } + 0;
	}

	############ FG
	my @fgconfig    = &getFarmGuardianConf( $farmname, "" );
	my $fguse       = $fgconfig[3];
	my $fgcommand   = $fgconfig[2];
	my $fgtimecheck = $fgconfig[1];
	my $fglog       = $fgconfig[4];
	
	if ( !$fgtimecheck ) { $fgtimecheck = 5; }
	if ( !$fguse ) { $fguse = "false"; }
	if ( !$fglog  ) { $fglog = "false"; }
	if ( !$fgcommand ) { $fgcommand = ""; }

	$out_p = {
			status      => $farm_st{ status },
			vip         => $farm_st{ vip },
			vport       => $farm_st{ vport },
			algorithm   => $farm_st{ lbalg },
			nattype     => $farm_st{ mode },
			persistence => $farm_st{ persist },
			protocol    => $farm_st{ vproto },
			ttl         => $farm_st{ ttl },
			fgenabled   => $fguse,
			fgtimecheck => $fgtimecheck + 0,
			fgscript    => $fgcommand,
			fglog       => $fglog,
			listener    => 'l4xnat',
	};

	########### backends
	my @out_b = $farm_st{ servers };

	include 'Zevenet::IPDS';
	my $ipds = &getIPDSfarmsRules_zapiv3( $farmname );

	my $body = {
			description	=> "List farm $farmname",
			params		=> $out_p,
			backends	=> \@out_b,
			ipds		=> $ipds,
	};

	&httpResponse({ code => 200, body => $body });
}


# Get all IPDS rules applied to a farm
sub getIPDSfarmsRules_zapiv3
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
			if ( defined $fileHandle->{ $key }->{ 'farms' } && $fileHandle->{ $key }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
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
			if ( defined $fileHandle->{ $key }->{ 'farms' } && $fileHandle->{ $key }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
			{
				push @blacklistsRules, $key;
			}
		}
	}

	if ( -e $rblConf )
	{
		$fileHandle = Config::Tiny->read( $rblConf );
		foreach my $key ( keys %{ $fileHandle } )
		{
			if ( defined $fileHandle->{ $key }->{ 'farms' } && $fileHandle->{ $key }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
			{
				push @rblRules, $key;
			}
		}
	}

	$rules =
	  { dos => \@dosRules, blacklists => \@blacklistsRules, rbl => \@rblRules };
	return $rules;
}

1;
