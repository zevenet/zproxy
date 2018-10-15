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
	my $type = shift;
	my $out = {
				'type'             => $type,
				'id'               => '',        # position in set file
				'rule_id'          => '',        # id of the rule
				'description'      => '',
				'tag'              => [],
				'version'          => '',
				'maturity'         => '',
				'severity'         => '',
				'accuracy'         => '',
				'revision'         => '',
				'phase'            => '',
				'transformations'  => [],
				'multi_match'      => 'false',
				'capture'          => 'false',
				'action'           => '',
				'http_code'        => '',
				'modify_directive' => [],        # parameter 'ctl' in secrule
				'execute'          => '',
				'no_log'           => 'false',
				'log'              => 'false',
				'audit_log'        => 'false',
				'no_audit_log'     => 'false',
				'log_data'         => '',
				'init_colection'   => [],
				'set_uid'          => '',
				'set_sid'          => '',
				'set_variable'     => [],
				'expire_var'       => [],
				'chain'            => [],
				'skip'             => '',
				'skip_after'       => '',
	};

	if ( $type eq 'match_action' )
	{
		$out->{ 'operating' } = '';
		$out->{ 'operator' }  = '';
		$out->{ 'variables' } = [];
	}

	return $out;
}

sub getWAFSetStructConf
{
	return {
		audit                 => 'false',    #SecAuditEngine: on|off|RelevantOnly
		process_request_body  => 'false',    # SecRequestBodyAccess on|off
		process_response_body => 'false',    # SecResponseBodyAccess on|off
		request_body_limit    => '',         # SecRequestBodyNoFilesLimit SIZE
		status                => 'false',    # SecRuleEngine on|off|DetectionOnly
		disable_rules  => [],                                # SecRuleRemoveById
		default_action => 'allow',
		default_log => '',
		default_phase => '1',
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
	$set =~ s/\..*$//g;
	return $set;
}

sub existWAFRuleId
{
	my $id = shift;
	return &getWAFSetByRuleId( $id ) ? 1 : 0;
}

sub listWAFByFarm
{
	my $farm  = shift;
	my @rules = ();

	require Zevenet::Farm::Core;
	require Zevenet::Lock;

	my $configdir = &getGlobalConfiguration( 'configdir' );
	my $farm_file = &getFarmFile( $farm );

	my $fh = &openlock( "$configdir/$farm_file", 'r' );
	my @rules = grep ( s/^WafRules\s+\".+\/([^\/]+).conf\".*$/$1/, <$fh> );
	chomp @rules;
	close $fh;

	return @rules;
}

# Get all farms where a WAF set is applied
sub listWAFBySet
{
	my $set   = shift;
	my @farms = ();
	my $farm_file;
	my $fh;
	my $find;

	require Zevenet::Farm::Core;
	require Zevenet::Lock;

	my $confdir   = &getGlobalConfiguration( 'configdir' );
	my $set_file  = &getWAFSetFile( $set );
	my @httpfarms = &getFarmsByType( 'http' );
	push @httpfarms, &getFarmsByType( 'https' );

	foreach my $farm ( @httpfarms )
	{
		$farm_file = &getFarmFile( $farm );
		$fh        = &openlock( "$confdir/$farm_file", 'r' );
		$find      = grep ( /WafRules\s+$set_file/, <$fh> );
		close $fh;

		push @farms, $farm if $find;
	}

	return @farms;
}

1;
