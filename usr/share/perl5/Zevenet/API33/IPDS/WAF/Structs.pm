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

	if ( $rule->{ type } =~ /(?:rule|action)/ )
	{
		$out = {
				 'type'            => $rule->{ type }                              // '',
				 'rule_id'         => $rule->{ rule_id }                           // '',
				 'description'     => $rule->{ description }                       // '',
				 'tag'             => $rule->{ tag }                               // [],
				 'severity'        => $rule->{ severity }                          // '',
				 'phase'           => $rule->{ phase }                             // '',
				 'transformations' => $rule->{ transformations }                   // [],
				 'multi_match'     => $rule->{ multi_match }                       // '',
				 'operator'        => &translateWafOperator( $rule->{ operator } ) // '',
				 'capture'         => $rule->{ capture }                           // '',
				 'value'           => $rule->{ value }                             // '',
				 'action'          => $rule->{ action }                            // '',
				 'log'             => $rule->{ log }                               // '',
				 'audit_log'       => $rule->{ audit_log }                         // '',
				 'log_data'        => $rule->{ log_data }                          // '',
				 'set_var'         => $rule->{ set_var }                           // [],
				 'chain'           => $rule->{ chain }                             // [],
				 'skip'            => $rule->{ skip }                              // '',
				 'skip_after'      => $rule->{ skip_after }                        // '',
				 'http_code'       => $rule->{ http_code }                         // '',
				 'execute'         => $rule->{ execute }                           // '',
		};

		foreach my $chained ( @{ $out->{chain} } )
		{
			delete $chained->{chain};
		}

		$out->{ log } = 'true'  if ( $rule->{ log } eq 'true' );
		$out->{ log } = 'false' if ( $rule->{ no_log } eq 'true' );

		$out->{ auditory } = 'true'  if ( $rule->{ audit_log } eq 'true' );
		$out->{ auditory } = 'false' if ( $rule->{ no_audit_log } eq 'true' );
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

	if ( $rule->{ type } eq 'rule' )
	{
		$out->{ 'variables' } = $rule->{ variables }                         // [];
		$out->{ 'operator' }  = &translateWafOperator( $rule->{ operator } ) // '';
		$out->{ 'value' }     = $rule->{ value }                             // '';
	}
	$out->{ raw } = $rule->{ raw } // '';
	$out->{ id } = $rule->{ id } // '2';

	## ?????? debug
	foreach my $key ( keys %{ $out } )
	{
		if ( !$out->{ $key } )
		{
			delete $out->{ $key };
		}
	}
	### ?????? end debug

	return $out;
}

sub getZapiWAFSet
{
	my $set = shift;

	include 'Zevenet::IPDS::WAF::Parser';

	my $set_st = &getWAFSet( $set );

	$set_st->{ configuration }->{ default_action } =
	  &getZapiWAFRule( $set_st->{ configuration }->{ default_action } );
	delete $set_st->{ configuration }->{ default_action }->{ type };

	foreach my $ru ( @{ $set_st->{ rules } } )
	{
		$ru = &getZapiWAFRule( $ru );
	}

	return $set_st;
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

1;
