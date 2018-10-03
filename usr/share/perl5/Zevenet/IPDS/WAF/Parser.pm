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
use Zevenet::Lock;

my $mark_conf_begin = "## begin conf";
my $mark_conf_end   = "## end conf";

=begin nd
Function: parseWAFRule

	It takes a SecRule and it parsers the data to create a WAF rule struct

Parameters:

	SecRule - It is an array reference with a SecRule

Returns:
	Hash ref - Rule struct

	{

	}

=cut
sub convertWAFLine
{
	my $txt = shift;

	my $line;
	grep ( s/\\$//g,  @{ $txt } );
	grep ( s/^\s*//g, @{ $txt } );
	chomp $_ for ( @{ $txt } );
	$line = join ( '', @{ $txt } );
	return $line;
}


sub parseWAFRule
{
	my $txt          = shift;
	my @nested_rules = @_;      # rest of nested rules
	my $line;
	my $rule;
	my $directive;
	my $act;

	# convert text in a line
	if ( ref $txt eq 'ARRAY' )
	{
		$line = &convertWAFLine( $txt );
	}
	else
	{
		$line = $txt;
	}

	if ( $line =~ /^\s*(Sec\w+)\s+/s )
	{
		$directive = $1;
	}

	if ( $directive =~ /(?:SecRule|SecAction)$/ )
	{
		my $type = ( $directive eq 'SecRule' ) ? 'rule' : 'action';
		$rule = &getWAFRulesStruct( $type );

# example:
#	SecRule REQUEST_METHOD "@streq POST" "id:'9001184',phase:1,t:none,pass,nolog,noauditlog,chain"
#	SecRule REQUEST_FILENAME "@rx /file/ajax/field_asset_[a-z0-9_]+/[ua]nd/0/form-[a-z0-9A-Z_-]+$" chain
# there are 4 mandatory fields: 1:directive 2:variables 3:value 4:actions

		if ( $directive eq 'SecRule' )
		{
			if ( $line !~ /^\s*SecRule\s+"?([^"]+)"?\s+"?([^"]+)"?\s+"?([^"]+)?"?/s )
			{
				return undef;
			}

			my $var = $1;
			my $val = $2;
			$act = $3;

			if ( $val =~ /^(?<operator>!?\@\w+)?\s+?(?<value>[^"]+)$/ )
			{
				$rule->{ operator } = $+{ operator } // "";
				$rule->{ value } = $+{ value };
			}

			my @var_sp = split ( '\|', $var );
			$rule->{ variables } = \@var_sp;

			# set not_operator
			if ( $rule->{ operator } )
			{
				$rule->{ operator } =~ s/^(!)?\@//;
				my $not_op = $1 // '';
				$rule->{ operator } = "${not_op}$rule->{ operator }";
				&zenlog( "Not variable found parsing rule: $line ", "debug1", "waf" )
				  if ( !$rule->{ operator } );
			}
		}

		# parsing SecAction
		else
		{
			$act = $line;
			$act =~ s/^\s*SecAction\s+//;
			$act =~ s/^"//;
			$act =~ s/"\s*$//;

			$rule->{ type } = 'action';

			# delete the exclusive parameters of SecRules
			delete $rule->{ operator };
			delete $rule->{ value };
			delete $rule->{ variables };
		}

		my @options = split ( ',', $act );

		foreach my $param ( @options )
		{
			$param =~ s/^\s*//;
			$param =~ s/\s*$//;

			if ( $param =~ /msg:'?([^']+)'?/ )
			{
				$rule->{ description } = $1;
			}
			elsif ( $param =~ /id:'?([^']+)'?/ )
			{
				$rule->{ rule_id } = $1;
			}
			elsif ( $param =~ /tag:'?([^']+)'?/ )
			{
				push @{ $rule->{ tag } }, $1;
			}
			elsif ( $param =~ /ver:'?([^']+)'?/ )
			{
				$rule->{ version } = $1;
			}
			elsif ( $param =~ /maturity:'?([^']+)'?/ )
			{
				$rule->{ maturity } = $1;
			}
			elsif ( $param =~ /severity:'?([^']+)'?/ )
			{
				$rule->{ severity } = $1;
			}
			elsif ( $param =~ /accuracy:'?([^']+)'?/ )
			{
				$rule->{ accuracy } = $1;
			}
			elsif ( $param =~ /rev:'?([^']+)'?/ )
			{
				$rule->{ revision } = $1;
			}
			elsif ( $param =~ /status:'?([^']+)'?/ )
			{
				$rule->{ http_code } = $1;
			}
			elsif ( $param =~ /phase:'?([^']+)'?/ ) { $rule->{ phase } = $1; }

			# put same format phase
			elsif ( $param =~ /t:'?([^']+)'?/ )
			{
				push @{ $rule->{ transformations } }, $1;
			}
			elsif ( $param =~ /^multimatch$/ )
			{
				$rule->{ multi_match } = "true";
			}
			elsif ( $param =~ /^capture$/ ) { $rule->{ capture } = "true"; }
			elsif ( $param =~ /^(redirect|allow|pass|block|deny)$/ )
			{
				$rule->{ action } = $1;
			}
			elsif ( $param =~ /^nolog$/ )    { $rule->{ no_log }    = "true"; }
			elsif ( $param =~ /^log$/ )      { $rule->{ log }       = "true"; }
			elsif ( $param =~ /^auditlog$/ ) { $rule->{ audit_log } = "true"; }
			elsif ( $param =~ /^noauditlog$/ )
			{
				$rule->{ no_audit_log } = "true";
			}
			elsif ( $param =~ /^logdata:'?([^']+)'?/ )
			{
				$rule->{ log_data } = $1;
			}
			elsif ( $param =~ /initcol:'?([^']+)'?/ )
			{
				push @{ $rule->{ init_colection } }, $1;
			}
			elsif ( $param =~ /setuid:'?([^']+)'?/ )
			{
				$rule->{ set_uid } = $1;
			}
			elsif ( $param =~ /setsid:'?([^']+)'?/ )
			{
				$rule->{ set_sid } = $1;
			}
			elsif ( $param =~ /setvar:'?([^']+)'?/ )
			{
				push @{ $rule->{ set_var } }, $1;
			}
			elsif ( $param =~ /^chain$/ )
			{
				foreach my $ru ( @nested_rules )
				{
					$rule->{ raw } .= "\n" . &convertWAFLine( $ru );
					push @{ $rule->{ chain } }, &parseWAFRule( $ru );
				}
			}
			elsif ( $param =~ /skip:'?([^']+)'?/ ) { $rule->{ skip } = $1; }
			elsif ( $param =~ /skipAfter:'?([^']+)'?/ )
			{
				$rule->{ skip_after } = $1;
			}
			elsif ( $param =~ /exec:'?([^']+)'?/ ) { $rule->{ execute } = $1; }
			elsif ( $param =~ /ctl:'?([^']+)'?/ )
			{
				push @{ $rule->{ modify_directive } }, $1;
			}
		}
	}
	elsif ( $line =~ /^\s*SecMarker\s+(.+)$/s )
	{
		$rule->{ 'type' } = 'marker';
		$rule->{ 'mark' } = $1;
	}
	else
	{
		$rule->{ 'type' } = 'custom';
	}

	# save rule
	$rule->{ raw } //= "";
	$rule->{ raw } = $line . $rule->{ raw };
	chomp $rule->{ raw };

	return $rule;
}

=begin nd
Function: buildWAFRule

	Create a SecRule with the data of a WAF rule

Parameters:
	WAF rule - hash reference with the WAF rule configuration

Returns:
	String - text with the SecRule

=cut

sub buildWAFRule
{
	my $st         = shift;
	my $chain_flag = shift;
	my $secrule    = "";

	if ( $st->{ type } =~ /(?:rule|action)/ )
	{
		if ( $st->{ type } eq 'rule' )
		{
			my $vars = join ( '|', @{ $st->{ variables } } );
			my $operator = $st->{ operator };
			$operator =~ s/^(!)?//;
			my $not_op = $1 // '';
			$secrule =
			    'SecRule '
			  . $vars . ' "'
			  . $not_op . '@'
			  . $operator . ' '
			  . $st->{ value } . '" ';
			$secrule .= "\"\\\n";
		}
		else
		{
			$secrule = "SecAction \"\\\n";
		}

		$secrule .= "\tid:" . $st->{ rule_id } . ",\\\n"
		  if ( $st->{ rule_id } );
		$secrule .= "\tmsg:'" . $st->{ description } . "',\\\n"
		  if ( $st->{ description } );

		foreach my $tag ( @{ $st->{ tag } } )
		{
			$secrule .= "\ttag:$tag,\\\n";
		}
		$secrule .= "\tver:" . $st->{ version } . ",\\\n"
		  if ( $st->{ version } );
		$secrule .= "\tmaturity:" . $st->{ maturity } . ",\\\n"
		  if ( $st->{ maturity } =~ /\d/ );
		$secrule .= "\tseverity:" . $st->{ severity } . ",\\\n"
		  if ( $st->{ severity } =~ /\d/ );
		$secrule .= "\taccuracy:" . $st->{ accuracy } . ",\\\n"
		  if ( $st->{ accuracy } =~ /\d/ );
		$secrule .= "\trev:" . $st->{ revision } . ",\\\n"
		  if ( $st->{ revision } =~ /\d/ );
		$secrule .= "\tphase:" . $st->{ phase } . ",\\\n"
		  if ( $st->{ phase } );
		foreach my $t ( @{ $st->{ transformations } } )
		{
			$secrule .= "\tt:$t,\\\n";
		}
		$secrule .= "\tmultimatch,\\\n"    if ( $st->{ multi_match } eq 'true' );
		$secrule .= "\tcapture,\\\n"       if ( $st->{ capture } eq 'true' );
		$secrule .= "\t$st->{action},\\\n" if ( $st->{ action } );
		$secrule .= "\tstatus:" . $st->{ http_code } . ",\\\n"
		  if ( $st->{ http_code } );
		$secrule .= "\tnolog,\\\n"      if ( $st->{ no_log } eq 'true' );
		$secrule .= "\tlog,\\\n"        if ( $st->{ log } eq 'true' );
		$secrule .= "\tauditlog,\\\n"   if ( $st->{ audit_log } eq 'true' );
		$secrule .= "\tnoauditlog,\\\n" if ( $st->{ no_audit_log } eq 'true' );
		$secrule .= "\tlogdata:" . $st->{ log_data } . ",\\\n"
		  if ( $st->{ log_data } );

		foreach my $t ( @{ $st->{ init_colection } } )
		{
			$secrule .= "\tinitcol:$t,\\\n";
		}
		$secrule .= "\tsetuid:" . $st->{ setUid } . ",\\\n"
		  if ( $st->{ set_uid } );
		$secrule .= "\tsetsid:" . $st->{ set_sid } . ",\\\n"
		  if ( $st->{ set_sid } );

		foreach my $it ( @{ $st->{ set_var } } )
		{
			$secrule .= "\tsetvar:$it,\\\n";
		}
		$secrule .= "\tskip:" . $st->{ skip } . ",\\\n"
		  if ( $st->{ skip } =~ /\d/ );
		$secrule .= "\tskipAfter:" . $st->{ skip_after } . ",\\\n"
		  if ( $st->{ skip_after } );
		$secrule .= "\texec:" . $st->{ execute } . ",\\\n"
		  if ( $st->{ execute } );
		foreach my $it ( @{ $st->{ modify_directive } } )
		{
			$secrule .= "\tctl:$it,\\\n";
		}

		$secrule .= "\tchain,\\\n" if ( @{ $st->{ chain } } or $chain_flag );

		# remove last terminator
		$secrule =~ s/,\\\n$//;
		$secrule .= '"';

		# print all chained rules
		my $num_chain = scalar @{ $st->{ chain } };
		if ( $num_chain )
		{
			foreach my $chained ( @{ $st->{ chain } } )
			{
				$secrule .= "\n\n" . &buildWAFRule( $chained, --$num_chain );
			}
		}
	}

	elsif ( $st->{ type } eq 'marker' )
	{
		$secrule = "SecMarker " . $st->{ mark };
	}

	# custom
	else
	{
		$secrule = $st->{ raw };
	}

	return $secrule;
}

sub parseWAFSetConf
{
	my $txt  = shift;
	my $conf = &getWAFSetStructConf();

	foreach my $line ( @{ $txt } )
	{
		if ( $line =~ /^\s*SecAuditEngine\s+(on|off)/ )
		{
			my $value = $1;
			$conf->{ auditory } = 'true'  if ( $value eq 'on' );
			$conf->{ auditory } = 'false' if ( $value eq 'off' );
		}
		if ( $line =~ /^\s*SecRequestBodyAccess\s+(on|off)/ )
		{
			my $value = $1;
			$conf->{ process_request_body } = 'true'  if ( $value eq 'on' );
			$conf->{ process_request_body } = 'false' if ( $value eq 'off' );
		}
		if ( $line =~ /^\s*SecResponseBodyAccess\s+(on|off)/ )
		{
			my $value = $1;
			$conf->{ process_response_body } = 'true'  if ( $value eq 'on' );
			$conf->{ process_response_body } = 'false' if ( $value eq 'off' );
		}
		if ( $line =~ /^\s*SecRequestBodyNoFilesLimit\s+(\d+)/ )
		{
			$conf->{ request_body_limit } = $1;
		}
		if ( $line =~ /^\s*SecRuleEngine\s+(on|off|DetectionOnly)/ )
		{
			my $value = $1;
			$conf->{ status } = 'on'        if ( $value eq 'on' );
			$conf->{ status } = 'off'       if ( $value eq 'off' );
			$conf->{ status } = 'detection' if ( $value eq 'DetectionOnly' );
		}
		if ( $line =~ /^\s*SecDefaultAction\s+(on|off)/ )
		{
			my $value = $1;
			$value =~ s/SecDefaultAction/SecAction/;
			$conf->{ default_action } = &parseWAFRule( $value );
		}
		if ( $line =~ /^\s*SecRuleRemoveById\s+(.*)/ )
		{
			my @ids = split ( ' ', $1 );
			$conf->{ disable_rules } = \@ids;
		}
	}

	return $conf;
}

sub buildWAFSetConf
{
	my $conf = shift;
	my @txt  = ();

	push @txt, $mark_conf_begin;

	if ( $conf->{ auditory } eq 'true' )
	{
		push @txt, "SecAuditEngine on";
	}
	if ( $conf->{ process_request_body } eq 'true' )
	{
		push @txt, "SecRequestBodyAccess on";
	}
	if ( $conf->{ process_response_body } eq 'true' )
	{
		push @txt, "SecResponseBodyAccess on";
	}
	if ( $conf->{ request_body_limit } )
	{
		push @txt, "SecRequestBodyNoFilesLimit $conf->{ request_body_limit }";
	}

	if ( $conf->{ status } eq 'true' ) { push @txt, "SecRuleEngine on"; }
	if ( $conf->{ status } eq 'detection' )
	{
		push @txt, "SecRuleEngine DetectionOnly";
	}

	if ( $conf->{ default_action } )
	{
		my $rule = &buildWAFRule( $conf->{ default_action } );
		$rule =~ s/SecAction/SecDefaultAction/g;

		#~ push @txt, $rule;	# ?????
	}

	if ( exists $conf->{ disable_rules } )
	{
		if ( @{ $conf->{ disable_rules } } )
		{
			my $ids = join ( ' ', @{ $conf->{ disable_rules } } );
			push @txt, "SecRuleRemoveById $ids";
		}
	}

	push @txt, $mark_conf_end . "\n";

	return @txt;
}

sub buildWAFSet
{
	my $set      = shift;
	my $struct   = shift;
	my $set_file = &getWAFSetFile( $set );
	my $tmp      = '/tmp/waf_rules.build';
	my $err;

	# create tmp file
	my $fh = &openlock( $tmp, 'w' ) or return 1;

	#write set conf
	if ( exists $struct->{ configuration } )
	{
		my @conf = &buildWAFSetConf( $struct->{ configuration } );
		foreach my $line ( @conf )
		{
			print $fh $line . "\n";
		}
	}

	my $index = -1;
	foreach my $rule_st ( @{ $struct->{ rules } } )
	{
		my $index++;
		my $rule = &buildWAFRule( $rule_st );

		if ( $rule )
		{
			print $fh $rule . "\n\n";
		}
		else
		{
			$err = "Error in rule $index";
			last;
		}
	}
	close $fh;

	return $err if $err;

	# check syntax
	$err = &checkWAFSetSyntax( $tmp );

	# copy to definitive
	if ( not $err )
	{
		$err = &copyLock( $tmp, $set_file );
		include 'Zevenet::IPDS::WAF::Runtime';

		# restart rule
		$err = &reloadWAFByRule( $set );
	}
	else
	{
		&zenlog( "Error checking set syntax $set: $err", "error", "waf" );
	}

	# remove tmp file
	#~ unlink $tmp;   # ?????? uncomment

	return $err;
}

sub checkWAFSetSyntax
{
	my $file = shift;

	my $pound = &getGlobalConfiguration( 'pound' );
	my $out   = `$pound -W $file 2>&1`;
	my $err   = $?;
	&zenlog( "cmd: $pound -W $file", "debug1", "waf" );

	if ( $err )
	{
		&zenlog( $out, "Error", "waf" ) if $out;
		chomp $out;

		#parse response and return field that failed
		my @aux = split ( '\n', $out );
		$out = $aux[1];
		$out =~ s/^.+Column: \d+. //;
	}
	else
	{
		$out = "";
	}
	return $out;
}

sub checkWAFRuleSyntax
{
	my $rule  = shift;
	my $pound = &getGlobalConfiguration( 'pound' );

	# is it necessary change rule format
	$rule =~ s/"/\\"/g;

	my $out = `$pound -w "$rule" 2>&1`;
	my $err = $?;
	&zenlog( "cmd: $pound -w \"$rule\"", "debug1", "waf" );

	if ( $err )
	{
		&zenlog( $out, "Error", "waf" ) if $out;
		chomp $out;

		#parse response and return fields that failed
		my @aux = split ( '\n', $out );
		$out = $aux[1];
		$out =~ s/^.+Column: \d+. //;
	}
	else
	{
		$out = "";
	}

	return $out;
}

sub getWAFRule
{
	my $set   = shift;
	my $index = shift;

	my $set_st = &getWAFSet( $set );
	return undef if ( $index >= scalar @{ $set_st->{ rules } } );

	return $set_st->{ rules }->[$index];
}

sub parseWAFBatch
{
	my $batch = shift;
	my @rules = ();

	my @rules_nested;
	my $rule = [];
	my $id   = 0;
	my $chain = 0;    # if chain is found, sent the next rule too

	foreach my $line ( @{ $batch } )
	{
		$chain = 1 if ( $line =~ /[\"\s,]chain[\"\s,]/ );
		push @{ $rule }, $line;

		# if the line is not splitted '\', it is the final
		if ( $line !~ /\\\s*$/ )
		{
			push @rules_nested, $rule;
			if ( $chain )
			{
				$rule  = [];
				$chain = 0;
			}
			else
			{
				my $hash_rule = &parseWAFRule( @rules_nested );
				$hash_rule->{ id } = $id;
				$id++;
				push @rules, $hash_rule
				  if @rules_nested;    # add the last rule
				$rule         = [];
				@rules_nested = ();
			}
		}
	}

	return \@rules;
}

# parse the file and returns a struct with the configuration and its rules
sub getWAFSet
{
	my $set = shift;

	my $fh = &openlock( &getWAFSetFile( $set ), 'r' ) or return undef;
	my @conf_arr;
	my @batch;
	my $conf_flag = 0;

	while ( my $line = <$fh> )
	{
		# get global configuration of the set
		if ( $line =~ /^$mark_conf_begin/ )
		{
			$conf_flag = 1;
			next;
		}
		if ( $conf_flag )
		{
			push @conf_arr, $line;

			# end conf
			if ( $line =~ /^$mark_conf_end/ )
			{
				$conf_flag = 0;
			}
			next;
		}

		next if ( $line =~ /^\s*$/ );    # skip blank lines
		next if ( $line =~ /^\s*#/ );    # skip commentaries

		push @batch, $line;
	}

	close $fh;

	my $conf  = &parseWAFSetConf( \@conf_arr );
	my $rules = &parseWAFBatch( \@batch );

	return { rules => $rules, configuration => $conf };
}

1;
