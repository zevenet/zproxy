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

use MIME::Base64;

my $crypt_key = 'S7hi_krAX_Q1GBCY';

=begin nd
Function: getCodeEncode

	Encode a message

Parameters:
	message - String with the message to encode

Returns:
	String - Encoded message

See Also:
	Notifications password
=cut

sub getCodeEncode
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $clear_msg = shift;    # output
	my $encode_msg;

	if ( $clear_msg )
	{
		# encode fist time
		$encode_msg = encode_base64( $clear_msg, '' );

		# apply a obfuscation the msg
		# sustitute most used characters
		$encode_msg =~ s/a/2f25ed/g;
		$encode_msg =~ s/2/1B21VW/g;
		$encode_msg =~ s/e/lpWvW5/g;
		$encode_msg =~ s/o/Zx1Ce/g;
		$encode_msg =~ s/0/JhDc1cw/g;
		$encode_msg =~ s/9/mN1ffrh/g;
		$encode_msg =~ s/5/8qe4w4/g;
		$encode_msg =~ s/3/8q21NJn/g;
		$encode_msg =~ s/7/Tr54g4V4eN/g;
		chomp $encode_msg;

		# apply prefix and sufix
		$encode_msg = "xh1Q334${encode_msg}0be65aP1";

		# encode the obfuscate msg
		$encode_msg = encode_base64( $encode_msg, '' );
		chomp $encode_msg;
	}

	return $encode_msg;
}

=begin nd
Function: getCodeDecode

	Decode a encoded message

Parameters:
	message - String with a encoded message

Returns:
	String - Clear message

See Also:
	Notifications password
=cut

sub getCodeDecode
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $encode_msg = shift;
	my $clear_msg;    # output

	if ( $encode_msg )
	{
		# decode first time
		$clear_msg = decode_base64( $encode_msg );

		# remove the obfuscate the msg
		# remove code of most used characters
		$clear_msg =~ s/Tr54g4V4eN/7/g;
		$clear_msg =~ s/8q21NJn/3/g;
		$clear_msg =~ s/8qe4w4/5/g;
		$clear_msg =~ s/mN1ffrh/9/g;
		$clear_msg =~ s/JhDc1cw/0/g;
		$clear_msg =~ s/Zx1Ce/o/g;
		$clear_msg =~ s/lpWvW5/e/g;
		$clear_msg =~ s/1B21VW/2/g;
		$clear_msg =~ s/2f25ed/a/g;

		# remove prefix and sufix
		$clear_msg =~ s/^xh1Q334//;
		$clear_msg =~ s/0be65aP1$//;

		# decode
		$clear_msg = decode_base64( $clear_msg );
	}

	return $clear_msg;
}

=begin nd
Function: setCryptString

	Encrypt a string

Parameters:
	clean string - Text to compare

Returns:
	String - It returns encryted the string

=cut

sub setCryptString
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $clearString = shift;

	require Crypt::CBC;

	my $cipher = Crypt::CBC->new( -key    => $crypt_key,
								  -cipher => 'Blowfish', );

	my $out = $cipher->encrypt_hex( $clearString );

	return $out;
}

=begin nd
Function: validateCryptString

	Decript a encrypted string to check if it is the same than a clear string

Parameters:
	encrypted string - Text to decrypt and compare
	clean string - Text to compare

Returns:
	Error code - Return 1 if the two strings are the same or 0 if they aren't not

=cut

sub validateCryptString
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $encryptString = shift;
	my $clearString   = shift;

	require Crypt::CBC;

	my $decrypt = '';
	my $out     = 0;

	my $cipher = Crypt::CBC->new( -key    => $crypt_key,
								  -cipher => 'Blowfish', );

	eval {
		# packet
		$encryptString = pack ( "H*", $encryptString );

		# decrypt
		$decrypt = $cipher->decrypt( $encryptString );
	};

	if ( $clearString eq $decrypt )
	{
		$out = 1;
	}

	return $out;
}

1;
