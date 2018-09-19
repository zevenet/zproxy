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

sub parseWAFRule
{
	my $txt          = shift;
	my @nested_rules = @_;      # rest of nested rules
	my $line;
	my $rule;
	my $directive;
	my $act;

	# convert text in a line
	grep ( s/\\$//g,  @{ $txt } );
	grep ( s/^\s*//g, @{ $txt } );
	chomp $_ for ( @{ $txt } );
	$line = join ( '', @{ $txt } );

&zenlog( "??????? line:   $line" );

	if ( $line =~ /^\s*(Sec\w+)\s+/s )
	{
		$directive = $1;
		$rule->{ directive } = $directive;
	}

	if ( $directive =~ /(?:SecRule|SecAction)/ )
	{
		$rule = &getWAFRulesStruct();

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
				$rule->{ match }->{ operator } = $+{ operator } // "";
				$rule->{ match }->{ value } = $+{ value };
			}

			my @var_sp = split ( '\|', $var );
			$rule->{ match }->{ variables } = \@var_sp;

			# set not_operator
			if ( $rule->{ match }->{ operator } )
			{
				$rule->{ match }->{ operator } =~ s/^(!)?\@//;
				my $not_op = $1 // '';
				$rule->{ match }->{ operator } = "${not_op}$rule->{ match }->{ operator }";
				&zenlog( "Not variable found parsing rule: $line ", "debug1", "waf" )
				  if ( !$rule->{ match }->{ operator } );
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
			delete $rule->{ match }->{ operator };
			delete $rule->{ match }->{ value };
			delete $rule->{ match }->{ variables };
		}

		my @options = split ( ',', $act );

		foreach my $param ( @options )
		{
			$param =~ s/^\s*//;
			$param =~ s/\s*$//;

			if ( $param =~ /msg:'?([^']+)'?/ )
			{
				$rule->{ information }->{ description } = $1;
			}
			elsif ( $param =~ /id:'?([^']+)'?/ )
			{
				$rule->{ information }->{ rule_id } = $1;
			}
			elsif ( $param =~ /tag:'?([^']+)'?/ )
			{
				push @{ $rule->{ information }->{ tag } }, $1;
			}
			elsif ( $param =~ /ver:'?([^']+)'?/ )
			{
				$rule->{ information }->{ version } = $1;
			}
			elsif ( $param =~ /maturity:'?([^']+)'?/ )
			{
				$rule->{ information }->{ maturity } = $1;
			}
			elsif ( $param =~ /severity:'?([^']+)'?/ )
			{
				$rule->{ information }->{ severity } = $1;
			}
			elsif ( $param =~ /accuracy:'?([^']+)'?/ )
			{
				$rule->{ information }->{ accuracy } = $1;
			}
			elsif ( $param =~ /rev:'?([^']+)'?/ )
			{
				$rule->{ information }->{ revision } = $1;
			}
			elsif ( $param =~ /status:'?([^']+)'?/ )
			{
				$rule->{ http_code } = $1;
			}
			elsif ( $param =~ /phase:'?([^']+)'?/ ) { $rule->{ match }->{ phase } = $1; }

			# put same format phase
			elsif ( $param =~ /t:'?([^']+)'?/ )
			{
				push @{ $rule->{ match }->{ transformations } }, $1;
			}
			elsif ( $param =~ /^multimatch$/ )
			{
				$rule->{ match }->{ multi_match } = "true";
			}
			elsif ( $param =~ /^capture$/ ) { $rule->{ match }->{ capture } = "true"; }
			elsif ( $param =~ /^(redirect|allow|pass|block|deny)$/ )
			{
				$rule->{ action } = $1;
			}
			elsif ( $param =~ /^nolog$/ )    { $rule->{ logs }->{ no_log }    = "true"; }
			elsif ( $param =~ /^log$/ )      { $rule->{ logs }->{ log }       = "true"; }
			elsif ( $param =~ /^auditlog$/ ) { $rule->{ logs }->{ audit_log } = "true"; }
			elsif ( $param =~ /^noauditlog$/ )
			{
				$rule->{ logs }->{ no_audit_log } = "true";
			}
			elsif ( $param =~ /^logdata:'?([^']+)'?/ )
			{
				$rule->{ logs }->{ log_data } = $1;
			}
			elsif ( $param =~ /initcol:'?([^']+)'?/ )
			{
				push @{ $rule->{ set_variables }->{ init_colection } }, $1;
			}
			elsif ( $param =~ /setuid:'?([^']+)'?/ )
			{
				$rule->{ set_variables }->{ set_uid } = $1;
			}
			elsif ( $param =~ /setsid:'?([^']+)'?/ )
			{
				$rule->{ set_variables }->{ set_sid } = $1;
			}
			elsif ( $param =~ /setvar:'?([^']+)'?/ )
			{
				push @{ $rule->{ set_variables }->{ set_var } }, $1;
			}
			elsif ( $param =~ /^chain$/ )
			{
				foreach my $ru ( @nested_rules )
				{
					push @{ $rule->{ flow }->{ chain } }, &parseWAFRule( $ru );
				}
			}
			elsif ( $param =~ /skip:'?([^']+)'?/ ) { $rule->{ flow }->{ skip } = $1; }
			elsif ( $param =~ /skipAfter:'?([^']+)'?/ )
			{
				$rule->{ flow }->{ skip_after } = $1;
			}
			elsif ( $param =~ /exec:'?([^']+)'?/ ) { $rule->{ exec } = $1; }
			elsif ( $param =~ /ctl:'?([^']+)'?/ )
			{
				push @{ $rule->{ modify_directive } }, $1;
			}
		}
	}
	elsif ( $line =~ /^\s*SecMarker\s+(.+)$/s )
	{
		$rule->{ 'type' }  = 'marker';
		$rule->{ 'value' } = $1;
	}
	else
	{
		$rule->{ 'type' }  = 'custom';
		$rule->{ 'value' } = $line;
		chomp $rule->{ 'value' };
	}

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
	my $st      = shift;
	my $secrule = "";

	if ( $st->{ type } eq 'rule' )
	{
		my $vars = join ( '|', @{ $st->{ match }->{ variables } } );
		my $operator = $st->{ match }->{ operator };
		$operator =~ s/^(!)?//;
		my $not_op = $1 // '';

		$secrule =
		    'SecRule '
		  . $vars . ' "'
		  . $not_op . '@'
		  . $operator . ' '
		  . $st->{ match }->{ value } . '"\\' . "\n";
		$secrule .= "\t \"";
		$secrule .= "rule_id:" . $st->{ information }->{ rule_id } . ",\\\n";
		$secrule .= "\tmsg:'" . $st->{ information }->{ description } . "',\\\n"
		  if ( $st->{ information }->{ description } );

		foreach my $tag ( @{ $st->{ information }->{ tag } } )
		{
			$secrule .= "\ttag:$tag,\\\n";
		}
		$secrule .= "\tver:" . $st->{ information }->{ version } . ",\\\n"
		  if ( $st->{ information }->{ version } );
		$secrule .= "\tmaturity:" . $st->{ information }->{ maturity } . ",\\\n"
		  if ( $st->{ information }->{ maturity } =~ /\d/ );
		$secrule .= "\tseverity:" . $st->{ information }->{ severity } . ",\\\n"
		  if ( $st->{ information }->{ severity } =~ /\d/ );
		$secrule .= "\taccuracy:" . $st->{ information }->{ accuracy } . ",\\\n"
		  if ( $st->{ information }->{ accuracy } =~ /\d/ );
		$secrule .= "\trev:" . $st->{ information }->{ revision } . ",\\\n"
		  if ( $st->{ information }->{ revision } =~ /\d/ );
		$secrule .= "\tphase:" . $st->{ match }->{ phase } . ",\\\n"
		  if ( $st->{ match }->{ phase } );
		foreach my $t ( @{ $st->{ match }->{ transformations } } )
		{
			$secrule .= "\tt:$t,\\\n";
		}
		$secrule .= "\tmultimatch,\\\n"    if ( $st->{ match }->{ multi_match } );
		$secrule .= "\tcapture,\\\n"       if ( $st->{ match }->{ capture } );
		$secrule .= "\t$st->{action},\\\n" if ( $st->{ action } );
		$secrule .= "\tstatus:" . $st->{ http_code } . ",\\\n"
		  if ( $st->{ http_code } );
		$secrule .= "\tnolog,\\\n"      if ( $st->{ logs }->{ no_log } );
		$secrule .= "\tlog,\\\n"        if ( $st->{ logs }->{ log } );
		$secrule .= "\tauditlog,\\\n"   if ( $st->{ logs }->{ audit_log } );
		$secrule .= "\tnoauditlog,\\\n" if ( $st->{ logs }->{ no_audit_log } );
		$secrule .= "\tlogdata:" . $st->{ logs }->{ log_data } . ",\\\n"
		  if ( $st->{ logs }->{ log_data } );
		foreach my $t ( @{ $st->{ set_variables }->{ init_colection } } )
		{
			$secrule .= "\tinitcol:$t,\\\n";
		}
		$secrule .= "\tsetuid:" . $st->{ setVariables }->{ setUid } . ",\\\n"
		  if ( $st->{ set_variables }->{ set_uid } );
		$secrule .= "\tsetsid:" . $st->{ set_variables }->{ set_sid } . ",\\\n"
		  if ( $st->{ set_variables }->{ set_sid } );

		foreach my $it ( @{ $st->{ set_variables }->{ set_var } } )
		{
			$secrule .= "\tsetvar:$it,\\\n";
		}
		$secrule .= "\tchain,\\\n" if ( $st->{ flow }->{ chain } );
		$secrule .= "\tskip:" . $st->{ flow }->{ skip } . ",\\\n"
		  if ( $st->{ flow }->{ skip } =~ /\d/ );
		$secrule .= "\tskipAfter:" . $st->{ flow }->{ skip_after } . ",\\\n"
		  if ( $st->{ flow }->{ skip_after } );
		$secrule .= "\texec:" . $st->{ exec } . ",\\\n"
		  if ( $st->{ exec } );
		foreach my $it ( @{ $st->{ modify_directive } } )
		{
			$secrule .= "\tctl:$it,\\\n";
		}

		# remove last terminator
		$secrule =~ s/,\\\n$//;
		$secrule .= '"';
	}

	else
	{
		$secrule = $st->{ directive } . $st->{ value };
	}

	#~ &zenlog ( "Parsing rule: $secrule", "debug", "waf");

	return $secrule;
}

sub parseWAFSet
{
	my $set         = shift;
	my @file_parsed = ();
	my $flag;
	my @rules_nested;
	my $rule = [];
	my $fh = &openlock( &getWAFSetFile( $set ), 'r' ) or return \@file_parsed;
	my $id = 0;

	my $chain = 0;    # if chain is found, sent the next rule too
	while ( my $line = <$fh> )
	{
		next if ( $line =~ /^\s*$/ );    # skip blank lines
		next if ( $line =~ /^\s*#/ );    # skip commentaries

		$chain = 1 if ( $line =~ /[\"\s,]chain[\"\s,]/ );
		push @{ $rule }, $line;

		if ( $line !~ /\\\s*$/ )    # if the line is not splitted '\', it is the final
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
				push @file_parsed, $hash_rule
				  if @rules_nested;    # add the last rule
				$rule = [];
				@rules_nested = ();
			}
		}
	}

	close $fh;

	return \@file_parsed;
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
	foreach my $rule_st ( @{ $struct } )
	{
		my $rule = &buildWAFRule( $rule_st );
		print $fh $rule . "\n\n";
	}
	close $fh;

	# check syntax
	my $err = &checkWAFSetSyntax( $tmp );

	# copy to definitive
	if ( not defined $err )
	{
		$err = &copyLock( $tmp, $set_file );

		# restart rule
		# ?????

	}
	else
	{
		&zenlog( "Error checking set syntax $set: $err", "error", "waf" );
		$err = 1;
	}

	# remove tmp file
	#~ unlink $tmp;

	return $err;
}

sub checkWAFSetSyntax
{
	my $file = shift;
	my $err_msg;

	# is it necessary change rule format? ?????
	# ...

	my $pound   = &getGlobalConfiguration( 'pound' );
	my @out     = `$pound -W $file 2>&1`;
	my $err_msg = $out[1];
	chomp $err_msg;

	#parse response and return field that failed ???
	# ...

	return $err_msg;
}

sub checkWAFRuleSyntax
{
	my $rule  = shift;
	my $pound = &getGlobalConfiguration( 'pound' );

	# is it necessary change rule format
	my $rule =~ s/"/\\"/g;

	my @out     = `$pound -w "$rule" 2>&1`;
	my $err_msg = $out[1];
	chomp $err_msg;

	#parse response and return fields that failed ???
	# ...

	return $err_msg;
}

1;
