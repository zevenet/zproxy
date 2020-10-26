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

sub getWafOperators
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	return (
		{
		   name   => 'strBegins',
		   libkey => "beginsWith",
		   description =>
			 'The rule will match if any of the variables begin with the value of operating.'
		},
		{
		   name   => 'strContains',
		   libkey => "contains",
		   description =>
			 'The rule will match if any of the variables contain the value of operating.'
		},
		{
		   name   => 'strContainsWord',
		   libkey => "containsWord",
		   description =>
			 'The rule will match if any of the variables contain a word as the string one.'
		},
		{
		   name   => 'strEnds',
		   libkey => "endsWith",
		   description =>
			 'The rule will match if any of the variables end with the value of operating.'
		},
		{
		   name   => 'strWithin',
		   libkey => "within",
		   description =>
			 'The rule will match if any of the variables match with the value of operating.'
		},
		{
		   name   => 'strMatch',
		   libkey => "strmatch",
		   description =>
			 'The rule will match if any of the variables match with the value of operating.'
		},
		{
		   name   => 'strEq',
		   libkey => "streq",
		   description =>
			 'The rule will match if any of the variables is identical to the value of operating.'
		},
		{
		   name   => 'strRegex',
		   libkey => "rx",
		   description =>
			 'The rule will match if any of the variables matches in the regular expression used in operating.'
		},
		{
		   name   => 'strPhrases',
		   libkey => "pm",
		   description =>
			 'The rule will match if any of the variables match in any of the values of the list operating.'
		},
		{
		   name   => 'strPhrasesFromFile',
		   libkey => "pmFromFile",
		   description =>
			 'It the same that the operator strPhrases but the operating is a file where it is defined a list of phrases.'
		},
		{
		   name   => 'intEQ',
		   libkey => "eq",
		   description =>
			 'The rule will match if any of the variables is equal to the number used in operating.'
		},
		{
		   name   => 'intGE',
		   libkey => "ge",
		   description =>
			 'The rule will match if any of the variables is greater or equal to the number used in operating.'
		},
		{
		   name   => 'intGT',
		   libkey => "gt",
		   description =>
			 'The rule will match if any of the variables is greater than the number used in operating.'
		},
		{
		   name   => 'intLE',
		   libkey => "le",
		   description =>
			 'The rule will match if any of the variables is lower or equal to the number used in operating.'
		},
		{
		   name   => 'intLT',
		   libkey => "lt",
		   description =>
			 'The rule will match if any of the variables is lower than the number used in operating.'
		},
		{
		   name   => 'detectSQLi',
		   libkey => "detectSQLi",
		   description =>
			 'It applies the detection of SQL injection to the list of variables. This operator does not expect any operating.'
		},
		{
		   name   => 'detectXSS',
		   libkey => "detectXSS",
		   description =>
			 'It applies the detection of XSS injection to the list of variables. This operator does not expect any operating.'
		},
		{
		   name   => 'ipMatch',
		   libkey => "ipMatch",
		   description =>
			 'Try to match the IP or network segments of operating with the list of variables.'
		},
		{
		   name   => 'ipMatchFromFile',
		   libkey => "ipMatchFromFile",
		   description =>
			 'It is the same than the operator ipMatch, but this tries the match of the variables against a file with a list of IPs and network segments.'
		},
		{
		   name   => 'validateByteRange',
		   libkey => "validateByteRange",
		   description =>
			 'It checks that the number of byte of the variables are in one of the operating values. An example of operating is "10, 13, 32-126".'
		},
		{
		   name   => 'validateUrlEncoding',
		   libkey => "validateUrlEncoding",
		   description =>
			 'It validates encoded data. This operator must be used only for data that does not encode data commonly or for data are encoded several times.'
		},
		{
		   name   => 'validateUtf8Encoding',
		   libkey => "validateUtf8Encoding",
		   description =>
			 'It validate that variables are UTF-8. This operator does not expect any operating.'
		},
		{
		   name   => 'verifyCreditCard',
		   libkey => "verifyCC",
		   description =>
			 'It verifies if variables are a credit card number. This parameter accepts a regular expression as operating, if it matches then it applies the credit card verified.'
		},
		{
		   name   => 'verifySSN',
		   libkey => "verifySSN",
		   description =>
			 'It verifies if variables are a US Social Security Number. This parameter accepts a regular expression as operating, if it matches then it applies the SSN verify.'
		},
		{
		   name        => 'matchAllways',
		   libkey      => "unconditionalMatch",
		   description => 'It returns true always, forcing a match.'
		},
		{
		   name        => 'matchNever',
		   libkey      => "noMatch",
		   description => 'It returns false always, forcing a non-match.'
		}
	);

}

sub getWafTransformations
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	return (
		{ name => 'base64Decode', description => 'Decodes a Base64-encoded string.' },
		{
		   name        => 'base64DecodeExt',
		   description => 'Decodes a Base64-encoded string ignoring invalid characters.'
		},
		{ name => 'sqlHexDecode', description => 'Decodes SQL hex data.' },
		{ name => 'base64Encode', description => 'Encodes using Base64 encoding.' },
		{
		   name        => 'cmdLine',
		   description => 'Avoids the problem related with the escaped command line.'
		},
		{
		   name => 'compressWhitespace',
		   description =>
			 'Converts any of the whitespace characters (0x20, \\f, \\t, \\n, \\r, \\v, 0xa0) to spaces (ASCII 0x20), compressing multiple consecutive space characters into one.'
		},
		{
		   name => 'cssDecode',
		   description =>
			 'Decodes characters encoded using the CSS 2.x escape rules. This function uses only up to two bytes in the decoding process, meaning that it is useful to uncover ASCII characters encoded using CSS encoding (that wouldn’t normally be encoded), or to counter evasion, which is a combination of a backslash and non-hexadecimal characters (e.g., ja\\vascript is equivalent to javascript).'
		},
		{
		   name => 'escapeSeqDecode',
		   description =>
			 'Decodes ANSI C escape sequences: \\a, \\b, \\f, \\n, \\r, \\t, \\v, \\, \\?, \\’, \\”, \\xHH (hexadecimal), \\0OOO (octal). Invalid encodings are left in the output.'
		},
		{
		   name => 'hexDecode',
		   description =>
			 'Decodes a string that has been encoded using the same algorithm as the one used in hexEncode (see following entry).'
		},
		{
		   name => 'hexEncode',
		   description =>
			 'Encodes string (possibly containing binary characters) by replacing each input byte with two hexadecimal characters. For example, xyz is encoded as 78797a.'
		},
		{
		   name        => 'htmlEntityDecode',
		   description => 'Decodes the characters encoded as HTML entities.'
		},
		{ name => 'jsDecode', description => 'Decodes JavaScript escape sequences.' },
		{
		   name => 'length',
		   description =>
			 'Looks up the length of the input string in bytes, placing it (as string) in output.'
		},
		{
		   name        => 'lowercase',
		   description => 'Converts all characters to lowercase using the current C locale.'
		},
		{
		   name => 'md5',
		   description =>
			 'Calculates an MD5 hash from the data in input. The computed hash is in a raw binary form and may need to be encoded into the text to be printed (or logged). Hash functions are commonly used in combination with hexEncode.'
		},
		{
		   name => 'none',
		   description =>
			 'Not an actual transformation function, but an instruction to remove previous transformation functions associated with the current rule.'
		},
		{
		   name => 'normalizePath',
		   description =>
			 'Removes multiple slashes, directory self-references, and directory back-references (except when at the beginning of the input) from input string.'
		},
		{
		   name => 'normalizePathWin',
		   description =>
			 'Same as normalizePath, but first converts backslash characters to forward slashes.'
		},
		{
		   name => 'parityEven7bit',
		   description =>
			 'Calculates even parity of 7-bit data replacing the 8th bit of each target byte with the calculated parity bit.'
		},
		{
		   name => 'parityOdd7bit',
		   description =>
			 'Calculates odd parity of 7-bit data replacing the 8th bit of each target byte with the calculated parity bit.'
		},
		{
		   name => 'parityZero7bit',
		   description =>
			 'Calculates zero parity of 7-bit data replacing the 8th bit of each target byte with a zero-parity bit, which allows inspection of even/odd parity 7-bit data as ASCII7 data.'
		},
		{ name => 'removeNulls', description => 'Removes all NUL bytes from input.' },
		{
		   name        => 'removeWhitespace',
		   description => 'Removes all whitespace characters from input.'
		},
		{
		   name => 'replaceComments',
		   description =>
			 'Replaces each occurrence of a C-style comment (/* … */) with a single space (multiple consecutive occurrences of which will not be compressed). Unterminated comments will also be replaced with space (ASCII 0x20). However, a standalone termination of a comment (*/) will not be acted upon.'
		},
		{
		   name        => 'removeCommentsChar',
		   description => 'Removes common comments chars (/*, */, –, #).'
		},
		{
		   name        => 'replaceNulls',
		   description => 'Replaces NUL bytes in input with space characters (ASCII 0x20).'
		},
		{
		   name => 'urlDecode',
		   description =>
			 'Decodes a URL-encoded input string. Invalid encodings (i.e., the ones that use non-hexadecimal characters, or the ones that are at the end of the string and have one or two bytes missing) are not converted, but no error is raised.'
		},
		{
		   name        => 'uppercase',
		   description => 'Converts all characters to uppercase using the current C locale.'
		},
		{
		   name => 'urlDecodeUni',
		   description =>
			 'Like urlDecode, but with support for the Microsoft-specific %u encoding.'
		},
		{
		   name        => 'urlEncode',
		   description => 'Encodes input string using URL encoding.'
		},
		{
		   name => 'utf8toUnicode',
		   description =>
			 'Converts all UTF-8 characters sequences to Unicode. This help input normalization especially for non-english languages minimizing false-positives and false-negatives.'
		},
		{
		   name => 'sha1',
		   description =>
			 'Calculates a SHA1 hash from the input string. The computed hash is in a raw binary form and may need to be encoded into the text to be printed (or logged). Hash functions are commonly used in combination with hexEncode.'
		},
		{
		   name        => 'trimLeft',
		   description => 'Removes whitespace from the left side of the input string.'
		},
		{
		   name        => 'trimRight',
		   description => 'Removes whitespace from the right side of the input string.'
		},
		{
		   name => 'trim',
		   description =>
			 'Removes whitespace from both the left and right sides of the input string.'
		}
	);
}

sub getWafVariables
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	return (
		{
		   name        => "ARGS",
		   type        => 'collection',
		   description => 'It is a collection with the values of arguments in a request.',
		},
		{
		   name => "ARGS_JSON",
		   type => 'collection',
		   description =>
			 'It is a collection with the values of arguments in a JSON request. This variable will be available in the case that WAF parses the JSON arguments, for it, the rule set REQUEST-901-INITIALIZATION should be enabled.',
		},
		{
		   name        => "ARGS_COMBINED_SIZE",
		   type        => 'scalar',
		   description => 'Total size of the request parameters. The files are excluded.',
		},
		{
		   name => "ARGS_NAMES",
		   type => 'collection',
		   description =>
			 'It is a collection with the names of the of arguments in a request.',
		},

		{
		   name => "FILES",
		   type => 'collection',
		   description =>
			 'It contains the file names in the user filesys. Only when the data is multipart/form-data.',
		},
		{
		   name => "FILES_COMBINED_SIZE",
		   type => 'scalar',
		   description =>
			 'It is the total size of the files in a request. Only when the data is multipart/form-data.',
		},
		{
		   name => "FILES_NAMES",
		   type => 'collection',
		   description =>
			 'It is a list of file names used to upload the files. Only when the data is multipart/form-data.',
		},
		{
		   name => "FILES_SIZES",
		   type => 'collection',
		   description =>
			 'It contains a list of individual file sizes. Only when the data is multipart/form-data.',
		},

		{
		   name => "REQBODY_ERROR",
		   type => 'scalar',
		   description =>
			 'This variable is 1 if the request body format is not correct for a JSON or XML, else it has the value 0.',
		},
		{
		   name => "REQUEST_BODY",
		   type => 'scalar',
		   description =>
			 'It is the raw body request. If the request has not the "application/x-www-form-urlencoded" header, it is necessary to use "ctl:forceRequestBodyVariable" in the REQUEST_HEADER phase.',
		},
		{
		   name        => "REQUEST_BODY_LENGTH",
		   type        => 'scalar',
		   description => 'It is the number of bytes of the request body.',
		},
		{
		   name        => "REQUEST_COOKIES",
		   type        => 'collection',
		   description => 'It is a list with all request cookies values.',
		},
		{
		   name        => "REQUEST_COOKIES_NAMES",
		   type        => 'collection',
		   description => 'It is a list with all request cookies names.',
		},
		{
		   name        => "REQUEST_HEADERS",
		   type        => 'collection',
		   description => 'This variable has all request headers.',
		},
		{
		   name        => "REQUEST_HEADERS_NAMES",
		   type        => 'collection',
		   description => 'This variable has a list with the request headers names.',
		},
		{
		   name        => "REQUEST_METHOD",
		   type        => 'scalar',
		   description => 'It is the request method.',
		},
		{
		   name        => "REQUEST_PROTOCOL",
		   type        => 'scalar',
		   description => 'This variable holds the request HTTP version protocol.',
		},
		{
		   name        => "REQUEST_URI",
		   type        => 'scalar',
		   description => 'It is the URI request path. The virtual host is excluded.',
		},

		{
		   name        => "RESPONSE_BODY",
		   type        => 'scalar',
		   description => 'It is the raw body response.',
		},
		{
		   name        => "RESPONSE_CONTENT_LENGTH",
		   type        => 'scalar',
		   description => 'It is the number of bytes of the response body.',
		},
		{
		   name        => "RESPONSE_HEADERS",
		   type        => 'collection',
		   description => 'This variable has all response headers.',
		},
		{
		   name        => "RESPONSE_HEADERS_NAMES",
		   type        => 'collection',
		   description => 'This variable has a list with the response headers names.',
		},
		{
		   name        => "RESPONSE_PROTOCOL",
		   type        => 'scalar',
		   description => 'This variable holds the response HTTP version protocol.',
		},
		{
		   name        => "RESPONSE_STATUS",
		   type        => 'scalar',
		   description => 'It is the response HTTP code.',
		},

		{
		   name        => "REMOTE_ADDR",
		   type        => 'scalar',
		   description => 'It is the IP address of the client.',
		},
		{
		   name        => "REMOTE_PORT",
		   type        => 'scalar',
		   description => 'It is the port where the client initializes the connection.',
		},
		{
		   name        => "REMOTE_USER",
		   type        => 'scalar',
		   description => 'It is the name of the authenticated user.',
		},

		{
		   name => "DURATION",
		   type => 'scalar',
		   description =>
			 'It is the number of milliseconds since the beginning of the current transaction.',
		},
		{
		   name        => "TIME",
		   type        => 'scalar',
		   description => 'It is the server time. The format is hours:minutes:seconds.',
		},

		{
		   name        => "MULTIPART_FILENAME",
		   type        => 'scalar',
		   description => 'It is the field filename in a multipart request.',
		},
		{
		   name        => "MULTIPART_NAME",
		   type        => 'scalar',
		   description => 'It is the field name in a multipart request.',
		},

		{
		   name => "MATCHED_VAR",
		   type => 'scalar',
		   description =>
			 'It is the matched value in the last match operation. This value does not need the capture option but it is replaced in each match operation.',
		},
		{
		   name        => "MATCHED_VARS",
		   type        => 'collection',
		   description => 'It is a list of all matched values.',
		},

		{
		   name        => "SERVER_ADDR",
		   type        => 'scalar',
		   description => 'It is the IP address of the server.',
		},
		{
		   name        => "SERVER_NAME",
		   type        => 'scalar',
		   description => 'It is the virtual host, it gets from the request URI.',
		},

		{
		   name        => "FULL_REQUEST",
		   type        => 'scalar',
		   description => 'It is the full request.',
		},
		{
		   name        => "FULL_REQUEST_LENGTH",
		   type        => 'scalar',
		   description => 'It is the number of bytes that full request can have.',
		},
		{
		   name        => "PATH_INFO",
		   type        => 'scalar',
		   description => 'It is the information before than the URI path.',
		},

		{
		   name        => "ENV",
		   type        => 'collection',
		   description => 'It is the environment variables of the WAF.',
		},
		{
		   name => "TX",
		   type => 'collection',
		   description =>
			 'It is a collection of variables for the current transaction. These variables will be removed when the transaction ends. The variables TX:0-TX:9 saves the values captured with the strRegex or strPhrases operators.',
		},
	);
}

# translate

my $trOperator = {};
foreach my $it ( &getWafOperators() )
{
	$trOperator->{ $it->{ name } } = $it->{ libkey };
}
$trOperator = &createTRANSLATE( $trOperator );

sub translateWafVariables
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $var    = shift;
	my $output = shift;

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

my @transformations = ();
foreach my $t ( &getWafTransformations() )
{
	push @transformations, $t->{ name };
}

sub getWafMatchParameters
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my @operators = @{ &getTRANSLATEInputs( $trOperator ) };

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

