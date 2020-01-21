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

#~ use Zevenet::CGI;

sub GET
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $path, $code ) = @_;

	my $q = getCGI();

	return unless $q->request_method eq 'GET' or $q->request_method eq 'HEAD';

	my @captures = $q->path_info =~ $path;
	return unless @captures;

	$code->( @captures );
}

sub POST
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $path, $code ) = @_;

	my $q = getCGI();

	return unless $q->request_method eq 'POST';

	my @captures = $q->path_info =~ $path;
	return unless @captures;

	my $data = &getCgiParam( 'POSTDATA' );
	my $input_ref;

	if ( exists $ENV{ CONTENT_TYPE } && $ENV{ CONTENT_TYPE } eq 'application/json' )
	{
		require JSON::XS;
		JSON::XS->import;

		$input_ref = eval { decode_json( $data ) };

		if ( &debug() )
		{
			use Data::Dumper;
			&zenlog( "json: " . Dumper( $input_ref ), "debug", "ZAPI" );
		}
	}
	elsif ( exists $ENV{ CONTENT_TYPE } && $ENV{ CONTENT_TYPE } eq 'text/plain' )
	{
		$input_ref = $data;
	}
	elsif ( exists $ENV{ CONTENT_TYPE }
			&& $ENV{ CONTENT_TYPE } eq 'application/x-pem-file' )
	{
		$input_ref = $data;
	}
	else
	{
		&zenlog( "Content-Type not supported: $ENV{ CONTENT_TYPE }", "error", "ZAPI" );
		my $body = { message => 'Content-Type not supported', error => 'true' };

		&httpResponse( { code => 415, body => $body } );
	}

	$code->( $input_ref, @captures );
}

sub PUT
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $path, $code ) = @_;

	my $q = getCGI();

	return unless $q->request_method eq 'PUT';

	my @captures = $q->path_info =~ $path;
	return unless @captures;

	my $data = &getCgiParam( 'PUTDATA' );
	my $input_ref;

	if ( exists $ENV{ CONTENT_TYPE } && $ENV{ CONTENT_TYPE } eq 'application/json' )
	{
		require JSON::XS;
		JSON::XS->import;

		$input_ref = eval { decode_json( $data ) };

		if ( &debug() )
		{
			require Data::Dumper;
			Data::Dumper->import;
			&zenlog( "json: " . Dumper $input_ref, "debug", "ZAPI" );
		}
	}
	elsif ( exists $ENV{ CONTENT_TYPE } && $ENV{ CONTENT_TYPE } eq 'text/plain' )
	{
		$input_ref = $data;
	}
	elsif ( exists $ENV{ CONTENT_TYPE }
			&& $ENV{ CONTENT_TYPE } eq 'application/x-pem-file' )
	{
		$input_ref = $data;
	}
	else
	{
		&zenlog( "Content-Type not supported: $ENV{ CONTENT_TYPE }", "error", "ZAPI" );
		my $body = { message => 'Content-Type not supported', error => 'true' };

		&httpResponse( { code => 415, body => $body } );
	}

	$code->( $input_ref, @captures );
}

sub DELETE
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $path, $code ) = @_;

	my $q = getCGI();

	return unless $q->request_method eq 'DELETE';

	my @captures = $q->path_info =~ $path;
	return unless @captures;

	$code->( @captures );
}

sub OPTIONS
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $path, $code ) = @_;

	my $q = getCGI();

	return unless $q->request_method eq 'OPTIONS';

	my @captures = $q->path_info =~ $path;
	return unless @captures;

	$code->( @captures );
}

=begin nd
	Function: httpResponse

	Render and print zapi response fron data input.

	Parameters:

		Hash reference with these key-value pairs:

		code - HTTP status code digit
		headers - optional hash reference of extra http headers to be included
		body - optional hash reference with data to be sent as JSON

	Returns:

		This function exits the execution uf the current process.
=cut

sub httpResponse    # ( \%hash ) hash_keys->( code, headers, body )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $self = shift;

  #~ &zenlog("DEBUG httpResponse input: " . Dumper $self, "debug", "ZAPI" ); # DEBUG

	die 'httpResponse: Bad input' if !defined $self or ref $self ne 'HASH';

	die
	  if !defined $self->{ code }
	  or !exists $GLOBAL::http_status_codes->{ $self->{ code } };

	my $q = &getCGI();

	# Headers included in _ALL_ the responses, any method, any URI, sucess or error
	my @headers = (
					  'Access-Control-Allow-Origin' => ( exists $ENV{ HTTP_ZAPI_KEY } )
					? '*'
					: "https://$ENV{ HTTP_HOST }/",
					'Access-Control-Allow-Credentials' => 'true',
	);

	if ( $ENV{ 'REQUEST_METHOD' } eq 'OPTIONS' )    # no session info received
	{
		push @headers,
		  'Access-Control-Allow-Methods' => 'GET, POST, PUT, DELETE, OPTIONS',
		  'Access-Control-Allow-Headers' =>
		  'ZAPI_KEY, Authorization, Set-cookie, Content-Type, X-Requested-With',
		  ;
	}

	if ( exists $ENV{ HTTP_COOKIE } && $ENV{ HTTP_COOKIE } =~ /CGISESSID/ )
	{
		if ( &validCGISession() )
		{
			my $session = CGI::Session->load( $q );
			my $session_cookie = $q->cookie( CGISESSID => $session->id );

			push @headers,
			  'Set-Cookie'                    => $session_cookie,
			  'Access-Control-Expose-Headers' => 'Set-Cookie',
			  ;
		}
	}

	if ( $q->path_info =~ '/session' )
	{
		push @headers,
		  'Access-Control-Expose-Headers' => 'Set-Cookie',
		  ;
	}

	# add possible extra headers
	if ( exists $self->{ headers } && ref $self->{ headers } eq 'HASH' )
	{
		push @headers, %{ $self->{ headers } };
	}

	# header
	my $content_type = 'application/json';
	$content_type = $self->{ type } if $self->{ type } && $self->{ body };

	my $output = $q->header(
		-type    => $content_type,
		-charset => 'utf-8',
		-status  => "$self->{ code } $GLOBAL::http_status_codes->{ $self->{ code } }",

		# extra headers
		@headers,
	);

	# body

	#~ my ( $body_ref ) = shift @_; # opcional
	if ( exists $self->{ body } )
	{
		if ( ref $self->{ body } eq 'HASH' )
		{
			require JSON::XS;
			JSON::XS->import;

			my $json           = JSON::XS->new->utf8->pretty( 1 );
			my $json_canonical = 1;
			$json->canonical( [$json_canonical] );

			$output .= $json->encode( $self->{ body } );
		}
		else
		{
			$output .= $self->{ body };
		}
	}

	#~ &zenlog( "Response:$output<", "debug", "ZAPI" ); # DEBUG
	print $output;

	if ( &debug )
	{
		# log request if debug is enabled
		my $req_msg =
		  "STATUS: $self->{ code } REQUEST: $ENV{REQUEST_METHOD} $ENV{SCRIPT_URL}";

		# include memory usage if debug is 2 or higher
		$req_msg .= " " . &getMemoryUsage() if &debug() > 1;
		&zenlog( $req_msg, "debug", "ZAPI" );

		# log error message on error.
		if ( ref $self->{ body } eq 'HASH' )
		{
			my $tag = ( $self->{ code } =~ /^2/ ) ? 'info' : 'error';
			&zenlog( "$self->{ body }->{ message }", $tag, "ZAPI" )
			  if ( exists $self->{ body }->{ message } );
		}
	}

	exit;
}

1;
