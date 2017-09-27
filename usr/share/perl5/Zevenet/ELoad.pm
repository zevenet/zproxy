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

sub eload
{
	my %req = @_;

	my @required = ( qw(module func) );
	my @params   = ( qw(module func args) );

	# check required params
	if ( my ( $required ) = grep { not exists $req{ $_ } } @required )
	{
		my $msg = "Required eload parameter '$required' missing";

		&zenlog( $msg );
		die( $msg );
	}

	# check not used params
	if ( grep { not exists $req{ $_ } } @required )
	{
		my $params = join( ', ', @required );
		my $msg = "Warning: Detected unused eload parameter: $params";

		&zenlog( $msg );
	}

	my $zbin_path  = '/usr/local/zevenet/app/zbin';
	my $bin        = "$zbin_path/enterprise.bin";
	my $input;

	require JSON;
	JSON->import( qw( encode_json decode_json ) );

	# make sure $req{ args } is always an array reference 
	my $validArrayRef = exists $req{ args } && ref $req{ args } eq 'ARRAY';
	$req{ args } = [] if $validArrayRef && @{ $req{ args } } == ( 1 );
	$req{ args } = [] unless $validArrayRef;


	if ( ref( $req{ args } ) eq 'ARRAY' )
	{
		&zenlog("eload: ARGS is ARRAY ref: [OK]");
	}
	else
	{
		&zenlog("eload: ARGS is ARRAY ref: Failed!");
	}

	unless ( eval { $input = encode_json( $req{ args } ) } )
	{
		my $msg = "eload: Error encoding JSON: $@";

		zenlog( $msg );
		die $msg;
	}

	my $cmd = "$bin $req{ module } $req{ func }";

	&zenlog("eload: CMD: '$cmd'");
	&zenlog("eload: INPUT: '$input'");

	my $ret_output = `echo -n '$input' | $cmd 2>&1`;
	my $rc = $?;

	#~ &zenlog( "rc: '$rc'" );
	#~ &zenlog( "ret_output: '$ret_output'" );

	if ( $rc )
	{
		my $msg = "Error loading enterprise module $req{ module }";
		chomp $ret_output;

		#~ zenlog( "rc: '$rc'" );
		#~ zenlog( "ret_output: '$ret_output'" );
		&zenlog( "$msg. $ret_output" );
		die( $msg );
	}

	#~ my $ref;
	#~ my $out_l = length $ret_output;
	#~ &zenlog( "ret_output: $ret_output" );
	#~ &zenlog( "ret_output length: $out_l" );

	#~ if ( $out_l )
	#~ {
		#~ my $ref = decode_json( $ret_output );
	#~ }

	#~ &httpResponse( $ref ) if ref $ref;
	#~ return $ref;

	return $ret_output if $req{module} !~ /^Zevenet::API/;

	my $ref = decode_json( $ret_output );
	&httpResponse( $ref );
}

1;
