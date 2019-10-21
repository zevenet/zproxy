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
require Zevenet::API40::HTTP;
require Zevenet::Translator;

# default value for variables
my $DEFAULT_PHASE      = 2;
my $DEFAULT_RESOLUTION = 'pass';
my $DEFAULT_SKIP       = 0;

# translate

my $trOperator = &createTRANSLATE(
								  {
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
								  }
);

sub getWafOperators
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	return @{ &getTRANSLATEInputs( $trOperator ) };
}

sub getWafTransformations
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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

sub getWafVariables
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	return (
			 "ARGS_COMBINED_SIZE",           "ARGS",
			 "ARGS_JSON",                    "ARGS_GET",
			 "ARGS_POST",                    "ARGS_NAMES",
			 "ARGS_GET_NAMES",               "ARGS_POST_NAMES",
			 "FILES",                        "FILES_COMBINED_SIZE",
			 "FILES_NAMES",                  "FILES_SIZES",
			 "FILES_TMPNAMES",               "FILES_TMP_CONTENT",
			 "REQBODY_ERROR",                "REQBODY_ERROR_MSG",
			 "REQBODY_PROCESSOR",            "REQUEST_BASENAME",
			 "REQUEST_BODY",                 "REQUEST_BODY_LENGTH",
			 "REQUEST_COOKIES",              "REQUEST_COOKIES_NAMES",
			 "REQUEST_FILENAME",             "REQUEST_HEADERS",
			 "REQUEST_HEADERS_NAMES",        "REQUEST_LINE",
			 "REQUEST_METHOD",               "REQUEST_PROTOCOL",
			 "REQUEST_URI",                  "REQUEST_URI_RAW",
			 "RESPONSE_BODY",                "RESPONSE_CONTENT_LENGTH",
			 "RESPONSE_CONTENT_TYPE",        "RESPONSE_HEADERS",
			 "RESPONSE_HEADERS_NAMES",       "RESPONSE_PROTOCOL",
			 "RESPONSE_STATUS",              "REMOTE_ADDR",
			 "REMOTE_HOST",                  "REMOTE_PORT",
			 "REMOTE_USER",                  "TIME",
			 "TIME_DAY",                     "TIME_EPOCH",
			 "TIME_HOUR",                    "TIME_MIN",
			 "TIME_MON",                     "TIME_SEC",
			 "TIME_WDAY",                    "TIME_YEAR",
			 "MULTIPART_CRLF_LF_LINES",      "MULTIPART_FILENAME",
			 "MULTIPART_NAME",               "MULTIPART_STRICT_ERROR",
			 "MULTIPART_UNMATCHED_BOUNDARY", "MATCHED_VAR",
			 "MATCHED_VARS",                 "MATCHED_VAR_NAME",
			 "MATCHED_VARS_NAMES",           "SESSION",
			 "SESSIONID",                    "SERVER_ADDR",
			 "SERVER_NAME",                  "SERVER_PORT",
			 "AUTH_TYPE",                    "DURATION",
			 "ENV",                          "FULL_REQUEST",
			 "FULL_REQUEST_LENGTH",          "HIGHEST_SEVERITY",
			 "INBOUND_DATA_ERROR",           "MODSEC_BUILD",
			 "OUTBOUND_DATA_ERROR",          "PATH_INFO",
			 "QUERY_STRING",                 "RULE",
			 "TX",                           "UNIQUE_ID",
			 "URLENCODED_ERROR",             "USERID",
			 "XML"
	);
}

sub translateWafVariables
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $var    = shift;
	my $output = shift;
	my @list;

	if ( $output eq 'toApi' )
	{
		foreach my $it ( @{ $var } )
		{
			$it =~ s/ARGS:json\./ARGS_JSON:/;
		}
	}
	elsif ( $output eq 'toLib' )
	{
		foreach my $it ( @{ $var } )
		{
			$it =~ s/ARGS_JSON:/ARGS:json\./;
		}
	}
	else
	{
		&zenlog( 'translating the inputs WAF variables', 'Error', 'Api' );
	}

	return $var;
}

sub translateWafRule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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

		if ( $json_obj->{ audit } eq 'true' )
		{
			$rule->{ audit_log } = 'true';
		}
		elsif ( $json_obj->{ audit } eq 'false' )
		{
			$rule->{ no_audit_log } = 'true';
		}
	}

	# the parameter action has another name in the api
	if ( exists $json_obj->{ resolution } )
	{
		$rule->{ action } = $json_obj->{ resolution };
		$rule->{ action } =~ s/default_action/block/;
	}

	return undef;
}

sub translateWafMatch
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	if ( exists $json_obj->{ operator } )
	{
		my $not = 0;
		if ( $json_obj->{ operator } =~ s/^!// )
		{
			$not = 1;
		}

		$json_obj->{ operator } = $trOperator->{ api }->{ $json_obj->{ operator } };
		$json_obj->{ operator } = "!$json_obj->{ operator }" if ( $not );
	}

	$json_obj->{ variables } =
	  &translateWafVariables( $json_obj->{ variables }, 'toLib' )
	  if ( exists $json_obj->{ variables } );

# add a description, this is needed, because if any action is defined, the rule fails in the creation
	$json_obj->{ description } = 'Custom Match';

	return undef;
}

# standardize outputs

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $rule = shift;

	include 'Zevenet::IPDS::WAF::Core';
	my $out;
	my $id = $rule->{ id } // 0;

	if ( $rule->{ type } =~ /(?:match_action|action)/ )
	{
		$out = {
				 'type'        => 'action',
				 'rule_id'     => $rule->{ rule_id } // '',
				 'description' => $rule->{ description } // "The ID is $id",
				 'tag'         => $rule->{ tag } // [],
				 'phase'       => $rule->{ phase } // $DEFAULT_PHASE,
				 'resolution'  => ( $rule->{ action } eq 'block' )
				 ? 'default_action'
				 : $rule->{ action } // $DEFAULT_RESOLUTION,
				 'log'          => $rule->{ log }          // '',
				 'audit'        => $rule->{ audit_log }    // '',
				 'skip'         => $rule->{ skip }         // $DEFAULT_SKIP,
				 'skip_after'   => $rule->{ skip_after }   // '',
				 'execute'      => $rule->{ execute }      // '',
				 'modified'     => $rule->{ modified }     // '',
				 'redirect_url' => $rule->{ redirect_url } // '',
				 'matches'      => [],
		};

		my $operator;
		my $not_match;

		# add match condition to the first place
		if ( $rule->{ type } eq 'match_action' )
		{
			push @{ $out->{ matches } },
			  {
				'match_index'     => 0,
				'transformations' => $rule->{ transformations } // [],
				'not_match'       => $rule->{ not_match } // 'false',
				'multi_match'     => $rule->{ multi_match } // '',
				'capture'         => $rule->{ capture } // '',
				'variables'       => &translateWafVariables( $rule->{ variables }, 'toApi' ),
				'operator'        => $trOperator->{ lib }->{ $rule->{ operator } } // '',
				'operating'       => $rule->{ operating } // '',
			  };
		}

		my $index = 1;
		foreach my $chained ( @{ $rule->{ chain } } )
		{
			# the parameters must match with the list of getWAFChainParameters
			push @{ $out->{ matches } },
			  {
				'match_index'     => $index,
				'transformations' => $chained->{ transformations } // [],
				'not_match'       => $rule->{ not_match } // 'false',
				'multi_match'     => $chained->{ multi_match } // '',
				'capture'         => $chained->{ capture } // '',
				'variables'       => &translateWafVariables( $chained->{ variables }, 'toApi' ),
				'operator'        => $trOperator->{ lib }->{ $chained->{ operator } } // '',
				'operating'       => $chained->{ operating } // '',
			  };
			$index++;
		}

		$out->{ log } = 'true'  if ( $rule->{ log } eq 'true' );
		$out->{ log } = 'false' if ( $rule->{ no_log } eq 'true' );

		$out->{ audit } = 'true'  if ( $rule->{ audit_log } eq 'true' );
		$out->{ audit } = 'false' if ( $rule->{ no_audit_log } eq 'true' );

		$rule->{ type } = 'action';
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

	# return 'raw' as string
	$out->{ raw } =
	  ( @{ $rule->{ raw } } ) ? join ( "\n", @{ $rule->{ raw } } ) : "";

	$out->{ id } = $id;

	return $out;
}

sub getZapiWAFSet
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $set = shift;

	include 'Zevenet::IPDS::WAF::Parser';

	my $set_st = &getWAFSet( $set );

	my $conf = $set_st->{ configuration };
	$conf->{ default_action } //= 'pass';
	$conf->{ default_log } =
	  ( $conf->{ default_log } ne 'false' ) ? 'true' : 'false';
	$conf->{ default_phase }         //= 2;
	$conf->{ audit }                 //= 'true';
	$conf->{ process_request_body }  //= 'false';
	$conf->{ process_response_body } //= 'false';
	$conf->{ request_body_limit }    //= 0;
	$conf->{ status } = ( $conf->{ status } eq 'false' ) ? 'down' : 'up';
	$conf->{ only_logging } = $conf->{ only_logging };
	$conf->{ disable_rules } //= [];

	foreach my $ru ( @{ $set_st->{ rules } } )
	{
		$ru = &getZapiWAFRule( $ru );
	}

	return $set_st;
}

# input models

sub getWafRuleParameters
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $out;

	$out = {
			 'rule_id'     => { 'valid_format' => 'waf_rule_id' },
			 'description' => {},
			 'tag'         => { 'ref'          => 'array' },
			 'severity'    => { 'valid_format' => 'waf_severity' },
			 'phase'       => { 'valid_format' => 'waf_phase' },
			 'resolution' =>
			   { 'values' => ['pass', 'allow', 'deny', 'redirect', 'default_action'] },
			 'execute'      => {},
			 'log'          => { 'valid_format' => 'waf_log' },
			 'audit'        => { 'valid_format' => 'waf_audit_log' },
			 'skip'         => { 'valid_format' => 'waf_skip' },
			 'skip_after'   => { 'valid_format' => 'waf_skip_after' },
			 'redirect_url' => {},
	};

	return $out;
}

my @transformations = &getWafTransformations();

sub getWafMatchParameters
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my @operators = &getWafOperators();

	return {
			 'not_match' => { 'valid_format' => 'boolean' },
			 'variables' => { 'ref'          => 'array' },
			 'operator'  => { 'non_blank'    => 'true', 'values' => \@operators },
			 'operating'       => {},
			 'transformations' => {
									'ref'        => 'array',
									'non_blank'  => 'true',
									'function'   => \&validateTransformations,
									'format_msg' => "accepts the following values: \""
									  . join ( '", "', @transformations ) . '"'
			 },
			 'multi_match' => { 'valid_format' => 'boolean' },
			 'capture'     => { 'valid_format' => 'boolean' },
	};
}

sub validateTransformations
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $transf = shift;

	foreach my $t ( @{ $transf } )
	{
		return 0 if !( grep ( /^$t$/, @transformations ) );
	}

	return 1;
}

1;
