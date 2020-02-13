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

require Zevenet::Config;
require Zevenet::Debug;

my $debug = &getGlobalConfiguration( 'debug' );

sub eload
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my %req = @_;

	my @required = ( qw(module func) );
	my @params   = ( qw(module func args just_ret ) );

	# check required params
	if ( my ( $required ) = grep { not exists $req{ $_ } } @required )
	{
		my $msg = "Required eload parameter '$required' missing";

		&zenlog( $msg, "error", "SYSTEM" );
		die ( $msg );
	}

	#~ use Carp qw(cluck);
	#~ cluck "[eload]" if $debug > 4; # warn with stack backtrace

	# check not used params
	if ( grep { not exists $req{ $_ } } @required )
	{
		my $params = join ( ', ', @required );
		my $msg = "Detected unused eload parameter: $params";

		&zenlog( $msg, "warning", "SYSTEM" );
	}

	# make sure $req{ args } is always an array reference
	my $validArrayRef = exists $req{ args } && ref $req{ args } eq 'ARRAY';
	$req{ args } = [] unless $validArrayRef;

	# Run directly Already running inside enterprise.bin
	if ( defined &main::include )
	{
		sub include;    # WARNING: DO NOT REMOVE THIS

		include $req{ module };

		my $code_ref = \&{ $req{ func } };
		return $code_ref->( @{ $req{ args } } );
	}

	my $zbin_path = '/usr/local/zevenet/bin';
	my $bin       = "$zbin_path/enterprise.bin";
	my $input;

	require JSON;
	JSON->import( qw( encode_json decode_json ) );

	unless ( ref ( $req{ args } ) eq 'ARRAY' )
	{
		&zenlog( "eload: ARGS is ARRAY ref: Failed!", "info", "SYSTEM" );
	}

	unless ( eval { $input = encode_json( $req{ args } ) } )
	{
		my $msg = "eload: Error encoding JSON: $@";

		&zenlog( $msg, "error", "SYSTEM" );
		die $msg;
	}
	$input =~ s/\\/\\\\/g;

	my $cmd = "$bin $req{ module } $req{ func }";

	if ( $debug )
	{
		&zenlog( "eload: CMD: '$cmd'", "debug", "SYSTEM" );

		#~ &zenlog("eload: INPUT: '$input'", "debug", "SYSTEM") unless $input eq '[]';
	}

	my $ret_output;
	{
		local %ENV = %ENV;
		delete $ENV{ GATEWAY_INTERFACE };
		$ret_output = `echo -n '$input' | $cmd`;
	}
	my $rc = $?;

	chomp $ret_output;

	if ( $rc )
	{
		&zenlog( "enterprise.bin errno: '$rc'" );
		&zenlog( "$req{ module }::$req{ func } output: '$ret_output'" );
	}

	if ( $rc )
	{
		my $msg = "Error loading enterprise module $req{ module }";
		chomp $ret_output;

		#~ zenlog( "rc: '$rc'" );
		#~ zenlog( "ret_output: '$ret_output'" );
		&zenlog( "$msg. $ret_output", "error" . "SYSTEM" );

	  # add exception to bonding module to not die when it is configuring nic interfaces
		exit 1
		  if (     $0 =~ /zevenet$/
			   and exists $req{ func }
			   and $req{ func } ne "getAllBondsSlaves" );
		die ( $msg );
	}

	# condition flags
	my $ret_f = exists $req{ just_ret } && $req{ just_ret };
	my $api_f = ( $req{ module } =~ /^Zevenet::API/ );

	#~ &zenlog( $ret_output ) if $debug;

	my $output =
	  ( not $ret_f && $api_f ) ? decode_json( $ret_output ) : $ret_output;
	my @output = eval { @{ decode_json( $ret_output ) } };

	if ( $@ )
	{
		&zenlog( $@ );
		@output = undef;
	}

	use Data::Dumper;
	&zenlog( "eload $req{ module } $req{ func } output: " . Dumper \@output )
	  if @output && $rc;

	# return function output for non-API functions (service)
	if ( $ret_f || not $api_f )
	{
		return wantarray ? @output : shift @output;
	}

	&httpResponse( @output );
}

1;
