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
use Zevenet::Core;

my $configdir = &getGlobalConfiguration( 'configdir' );
my $wafDir    = $configdir . "/ipds/waf";
my $wafSetDir = $configdir . "/ipds/waf/sets";
my $wafConf   = $configdir . "/ipds/waf/waf.conf";

sub getWAFFile
{
	return $wafConf;
}

sub getWAFSetDir
{
	return $wafSetDir;
}

sub getWAFSetFile
{
	my $set = shift;
	return "$wafSetDir/${set}.conf";
}

=begin nd
Function: getWAFRuleStruct

	Returns a waf rule struct with all parameters available by default

Parameters:
	None - .

Returns:
	Hash ref - Rule struct

	{

	}

=cut

sub getWAFRulesStruct
{
	return {
		'type'        => 'rule',
		'id'          => '',			# position in set file
		'information' => {
						   'rule_id'     => '',
						   'description' => '',
						   'tag'         => [],
						   'version'     => '',
						   'maturity'    => '',
						   'severity'    => '',
						   'accuracy'    => '',
						   'revision'    => '',
		},
		'match' => {
					 'phase'           => '',
					 'variables'       => [],
					 'transformations' => [],
					 'multi_match'      => '',
					 'operator'        => '',
					 'capture'         => '',
					 'value'           => '',
		},
		'action'   => '',
		'http_code' => '',
		'modify_directive'  => [],    # parameter 'ctl' in secrule
		'exec'     => '',
		'logs'     => {
					'no_log'      => '',
					'log'        => '',
					'audit_log'   => '',
					'no_audit_log' => '',
					'log_data'    => '',
		},
		'set_variables' => {
							'init_colection' => [],
							'set_uid'        => '',
							'set_sid'        => '',
							'set_var'        => [],
							'expire_var'     => [],
		},
		'flow' => {
					'chain'     => [],
					'skip'      => '',
					'skip_after' => '',
					'exec' => '',
		},
	};
}

sub listWAFSet
{
	my @listSet = ();

	opendir ( my $fd, $wafSetDir ) or return @listSet;
	@listSet = readdir ( $fd );
	@listSet = grep ( !/^\./, @listSet );
	closedir $fd;
	@listSet = grep ( s/\.conf$//, @listSet );

	return @listSet;
}

sub existWAFSet
{
	my $set = shift;
	return ( grep ( /^$set$/, &listWAFSet() ) ) ? 1 : 0;
}

sub getWAFSetByRuleId
{
	my $id  = shift;
	my $set = "";
	my $dir = &getWAFSetDir();

	opendir ( my $fd, $dir );

	foreach my $file ( readdir ( $fd ) )
	{
		next if ( $file =~ /^\./ );

		my $fh = &openlock( "$dir/$file", 'r' );
		my $find = grep ( /id:$id\b/, <$fh> );
		close $fh;

		if ( $find ) { $set = $file; last; }
	}

	closedir ( $fd );

	$set =~ s/\·.*$//g;
	return $set;
}

sub existWAFRuleId
{
	my $id = shift;
	return &getWAFSetByRuleId( $id ) ? 1 : 0;
}

1;
