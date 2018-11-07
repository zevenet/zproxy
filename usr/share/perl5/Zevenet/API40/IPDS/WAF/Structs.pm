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
	my $out;

	if ( $rule->{ type } =~ /(?:match_action|action)/ )
	{
		$out = {
				 'type'            => $rule->{ type }            // '',
				 'rule_id'         => $rule->{ rule_id }         // '',
				 'description'     => $rule->{ description }     // '',
				 'tag'             => $rule->{ tag }             // [],
				 'severity'        => $rule->{ severity }        // '',
				 'phase'           => $rule->{ phase }           // '',
				 'transformations' => $rule->{ transformations } // [],
				 'multi_match'     => $rule->{ multi_match }     // '',
				 'capture'         => $rule->{ capture }         // '',
				 'action'          => $rule->{ action }          // '',
				 'log'             => $rule->{ log }             // '',
				 'audit'           => $rule->{ audit_log }       // '',
				 'log_data'        => $rule->{ log_data }        // '',
				 'set_variable'    => $rule->{ set_variable }    // [],
				 'chain'           => $rule->{ chain }           // [],
				 'skip'            => $rule->{ skip }            // '',
				 'skip_after'      => $rule->{ skip_after }      // '',
				 'http_code'       => $rule->{ http_code }       // '',
				 'execute'         => $rule->{ execute }         // '',
		};

		my @chains = @{ $out->{ chain } };
		$out->{ chain } = [];
		foreach my $chained ( @chains )
		{
			my $ch_rule = {};

			# the parameters must match with the list of getWAFChainParameters
			push @{ $out->{ chain } },
			  {
				'transformations' => $chained->{ transformations } // [],
				'multi_match'     => $chained->{ multi_match }     // '',
				'capture'         => $chained->{ capture }         // '',
				'execute'         => $chained->{ execute }         // '',
				'set_variable'    => $chained->{ set_variable }    // [],
				'variables'       => $chained->{ variables }       // [],
				'operator'        => $chained->{ operator }        // '',
				'operating'       => $chained->{ operating }       // '',
			  };
		}

		$out->{ log } = 'true'  if ( $rule->{ log } eq 'true' );
		$out->{ log } = 'false' if ( $rule->{ no_log } eq 'true' );

		$out->{ audit } = 'true'  if ( $rule->{ audit_log } eq 'true' );
		$out->{ audit } = 'false' if ( $rule->{ no_audit_log } eq 'true' );
	}

	elsif ( $rule->{ type } eq 'marker' )
	{
		$out->{ mark } = $rule->{ mark } // '';
		$out->{ type } = 'marker';
	}
	else
	{
		$out->{ type } = 'custom';
	}

	if ( $rule->{ type } eq 'match_action' )
	{
		$out->{ 'variables' } = $rule->{ variables }                         // [];
		$out->{ 'operator' }  = &translateWafOperator( $rule->{ operator } ) // '';
		$out->{ 'operating' } = $rule->{ operating }                         // '';
	}
	$out->{ raw } = $rule->{ raw } // [];
	$out->{ id }  = $rule->{ id }  // 0;

	return $out;
}

sub getZapiWAFSet
{
	my $set = shift;

	include 'Zevenet::IPDS::WAF::Parser';

	my $set_st = &getWAFSet( $set );

	my $conf = $set_st->{ configuration };
	$conf->{ default_action }        //= '';
	$conf->{ default_log }           //= '';
	$conf->{ default_phase }         //= '';
	$conf->{ audit }                 //= '';
	$conf->{ process_request_body }  //= '';
	$conf->{ process_response_body } //= '';
	$conf->{ request_body_limit }    //= '';
	$conf->{ status }                //= '';
	$conf->{ disable_rules }         //= [];

	foreach my $ru ( @{ $set_st->{ rules } } )
	{
		$ru = &getZapiWAFRule( $ru );
	}

	return $set_st;
}

sub getWAFChainParameters
{
	return [
			'transformations', 'multi_match', 'capture',  'execute',
			'set_variable',    'variables',   'operator', 'operating'
	];
}

sub getWafTransformations
{
	return (
			 "base64Decode",     "sqlHexDecode",     "base64DecodeExt",
			 "base64Encode",     "cmdLine",          "compressWhitespace",
			 "cssDecode",        "escapeSeqDecode",  "hexDecode",
			 "hexEncode",        "htmlEntityDecode", "jsDecode",
			 "length",           "lowercase",        "md5",
			 "none",             "normalisePath",    "normalizePath",
			 "normalisePathWin", "normalizePathWin", "parityEven7bit",
			 "parityOdd7bit",    "parityZero7bit",   "removeNulls",
			 "removeWhitespace", "replaceComments",  "removeCommentsChar",
			 "removeComments",   "replaceNulls",     "urlDecode",
			 "uppercase",        "urlDecodeUni",     "urlEncode",
			 "utf8toUnicode",    "sha1",             "trimLeft",
			 "trimRight",        "trim",
	);
}

sub getWafOperators
{
	return {
			 strBegins            => "beginsWith",
			 strContains          => "contains",
			 strContainsWord      => "containsWord",
			 strEnds              => "endsWith",
			 strWithin            => "within",
			 strMatch             => "strmatch",
			 strEq                => "streq",
			 strRegex             => "rx",
			 strPhrases           => "pm",
			 strPhrasesFromFile   => "pmFromFile",
			 intEQ                => "eq",
			 intGE                => "ge",
			 intGT                => "gt",
			 intLE                => "le",
			 intLT                => "lt",
			 detectSQLi           => "detectSQLi",
			 detectXSS            => "detectXSS",
			 geoLookup            => "geoLookup",
			 ipMatch              => "ipMatch",
			 ipMatchFromFile      => "ipMatchFromFile",
			 validateByteRange    => "validateByteRange",
			 validateDTD          => "validateDTD",
			 validateSchema       => "validateSchema",
			 validateUrlEncoding  => "validateUrlEncoding",
			 validateUtf8Encoding => "validateUtf8Encoding",
			 verifyCreditCard     => "verifyCC",
			 verifySSN            => "verifySSN",
			 matchAllways         => "unconditionalMatch",
			 matchNever           => "noMatch",
	};
}

sub translateWafOperator
{
	my $req       = shift;
	my $operators = &getWafOperators();

	foreach my $key ( keys %{ $operators } )
	{
		return $key if ( $operators->{ $key } eq $req );
	}

	return '';
}

sub getWafRuleModel
{
	my $type = shift;
	my $out;

	$out = {
			 'rule_id'         => { 'valid_format' => 'waf_rule_id' },
			 'description'     => {},
			 'tag'             => {},
			 'severity'        => { 'valid_format' => 'waf_severity' },
			 'phase'           => { 'valid_format' => 'waf_phase' },
			 'transformations' => {},
			 'multi_match'     => { 'valid_format' => 'boolean' },
			 'capture'         => { 'valid_format' => 'boolean' },
			 'action'          => { 'valid_format' => 'waf_action' },
			 'http_code'       => { 'valid_format' => 'http_code' },
			 'execute'         => {},
			 'log'             => { 'valid_format' => 'waf_log' },
			 'audit'           => { 'valid_format' => 'waf_audit_log' },
			 'log_data'        => {},
			 'set_variable'    => {},
			 'skip'            => { 'valid_format' => 'waf_skip' },
			 'skip_after'      => { 'valid_format' => 'waf_skip_after' },
	};

	if ( $type eq 'match_action' )
	{
		$out->{ variables } = { 'non_blank' => 'true' };
		$out->{ operator }  = { 'non_blank' => 'true' };
		$out->{ operating } = {};
	}

	return $out;
}

sub translateWafInputs
{
	my $json_obj = shift;
	my $rule     = shift;

	if ( exists $json_obj->{ log } )
	{
		$rule->{ log }    = '';
		$rule->{ no_log } = '';

		if    ( $json_obj->{ log } eq 'true' )  { $rule->{ log }    = 'true'; }
		elsif ( $json_obj->{ log } eq 'false' ) { $rule->{ no_log } = 'true'; }
	}
	if ( exists $json_obj->{ audit } )
	{
		$rule->{ audit_log }    = '';
		$rule->{ no_audit_log } = '';

		if ( $json_obj->{ audit } eq 'true' ) { $rule->{ audit_log } = 'true'; }
		elsif ( $json_obj->{ audit } eq 'false' )
		{
			$rule->{ no_audit_log } = 'true';
		}
	}

	if ( exists $json_obj->{ transformations } )
	{
		my @transf = &getWafTransformations();
		foreach my $tr ( @{ $json_obj->{ transformations } } )
		{
			if ( !grep ( /^$tr$/, @transf ) )
			{
				return "The transformation $tr is not recognized.";
			}
		}
		$rule->{ transformations } = $json_obj->{ transformations };
	}

	if ( exists $json_obj->{ operator } )
	{
		my $not  = 0;
		my $oper = &getWafOperators();
		if ( $json_obj->{ operator } =~ s/^!// )
		{
			$not = 1;
		}

		if ( !exists $oper->{ $json_obj->{ operator } } )
		{
			return "The operator $json_obj->{ operator } is not recognized.";
		}

		$rule->{ operator } = $oper->{ $json_obj->{ operator } };
		$rule->{ operator } = "!$rule->{ operator }" if ( $not );
	}

	$rule->{ rule_id } = $json_obj->{ rule_id }
	  if ( exists $json_obj->{ rule_id } );
	$rule->{ description } = $json_obj->{ description }
	  if ( exists $json_obj->{ description } );
	$rule->{ tag } = $json_obj->{ tag } if ( exists $json_obj->{ tag } );
	$rule->{ severity } = $json_obj->{ severity }
	  if ( exists $json_obj->{ severity } );
	$rule->{ phase } = $json_obj->{ phase } if ( exists $json_obj->{ phase } );
	$rule->{ operating } = $json_obj->{ operating }
	  if ( exists $json_obj->{ operating } );
	$rule->{ variables } = $json_obj->{ variables }
	  if ( exists $json_obj->{ variables } );
	$rule->{ multi_match } = $json_obj->{ multi_match }
	  if ( exists $json_obj->{ multi_match } );
	$rule->{ capture } = $json_obj->{ capture }
	  if ( exists $json_obj->{ capture } );
	$rule->{ action } = $json_obj->{ action } if ( exists $json_obj->{ action } );
	$rule->{ http_code } = $json_obj->{ http_code }
	  if ( exists $json_obj->{ http_code } );
	$rule->{ execute } = $json_obj->{ execute }
	  if ( exists $json_obj->{ execute } );
	$rule->{ log_data } = $json_obj->{ log_data }
	  if ( exists $json_obj->{ log_data } );
	$rule->{ set_variable } = $json_obj->{ set_variable }
	  if ( exists $json_obj->{ set_variable } );
	$rule->{ skip } = $json_obj->{ skip } if ( exists $json_obj->{ skip } );
	$rule->{ skip_after } = $json_obj->{ skip_after }
	  if ( exists $json_obj->{ skip_after } );

	return undef;
}

1;
