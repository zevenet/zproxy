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

my %http_status_codes = (

	# 2xx Success codes
	200 => 'OK',
	201 => 'Created',
	204 => 'No Content',

	# 4xx Client Error codes
	400 => 'Bad Request',
	401 => 'Unauthorized',
	403 => 'Forbidden',
	404 => 'Not Found',
	406 => 'Not Acceptable',
	415 => 'Unsupported Media Type',
	422 => 'Unprocessable Entity',
);

sub GET
{
	my ( $path, $code, $mod ) = @_;

	return unless $ENV{ REQUEST_METHOD } eq 'GET' or $ENV{ REQUEST_METHOD } eq 'HEAD';

	my @captures = ( $ENV{ PATH_INFO } =~ $path );
	return unless @captures;

	&zenlog("GET captures( @captures )");

	if ( ref $code eq 'CODE' )
	{
		$code->( @captures );
	}
	else
	{
		&eload( module => $mod, func => $code, args => \@captures );
	}
}

sub POST
{
	my ( $path, $code, $mod ) = @_;

	return unless $ENV{ REQUEST_METHOD } eq 'POST';

	my @captures = ( $ENV{ PATH_INFO } =~ $path );
	return unless @captures;

	&zenlog("POST captures( @captures )");

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
			&zenlog( "json: " . Dumper( $input_ref ) );
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
		$input_ref =~ s/\n/\\n/g; # escape '\n' characters in pem certificates
	}
	else
	{
		&zenlog( "Content-Type not supported: $ENV{ CONTENT_TYPE }" );
		my $body = { message => 'Content-Type not supported', error => 'true' };

		&httpResponse( { code => 415, body => $body } );
	}

	my @args = ( $input_ref, @captures );

	if ( ref $code eq 'CODE' )
	{
		$code->( @args );
	}
	else
	{
		&eload( module => $mod, func => $code, args => \@args );
	}
}

sub PUT
{
	my ( $path, $code, $mod ) = @_;

	return unless $ENV{ REQUEST_METHOD } eq 'PUT';

	my @captures = ( $ENV{ PATH_INFO } =~ $path );
	return unless @captures;

	&zenlog("PUT captures( @captures )");

	my $data = &getCgiParam( 'PUTDATA' );
	my $input_ref;

	if ( exists $ENV{ CONTENT_TYPE } && $ENV{ CONTENT_TYPE } eq 'application/json' )
	{
		require JSON::XS;
		JSON::XS->import;

		$input_ref = eval { decode_json( $data ) };

		if ( &debug() )
		{
			use Data::Dumper;
			&zenlog( "json: " . Dumper( $input_ref ) );
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
		&zenlog( "Content-Type not supported: $ENV{ CONTENT_TYPE }" );
		my $body = { message => 'Content-Type not supported', error => 'true' };

		&httpResponse( { code => 415, body => $body } );
	}

	my @args = ( $input_ref, @captures );

	if ( ref $code eq 'CODE' )
	{
		$code->( @args );
	}
	else
	{
		&eload( module => $mod, func => $code, args => \@args );
	}
}

sub DELETE
{
	my ( $path, $code, $mod ) = @_;

	return unless $ENV{ REQUEST_METHOD } eq 'DELETE';

	my @captures = ( $ENV{ PATH_INFO } =~ $path );
	return unless @captures;

	&zenlog("DELETE captures( @captures )");

	if ( ref $code eq 'CODE' )
	{
		$code->( @captures );
	}
	else
	{
		&eload( module => $mod, func => $code, args => \@captures );
	}
}

sub OPTIONS
{
	my ( $path, $code ) = @_;

	return unless $ENV{ REQUEST_METHOD } eq 'OPTIONS';

	my @captures = ( $ENV{ PATH_INFO } =~ $path );
	return unless @captures;

	&zenlog("OPTIONS captures( @captures )");

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
sub httpResponse    # ( \%hash ) hash_keys->( $code, %headers, $body )
{
	my $self = shift;

	return $self if &_isRunningEnterprise();

	#~ &zenlog("DEBUG httpResponse input: " . Dumper $self ); # DEBUG

	die 'httpResponse: Bad input' if !defined $self or ref $self ne 'HASH';

	die
	  if !defined $self->{ code }
	  or !exists $http_status_codes{ $self->{ code } };

	my $q = &getCGI();

	logNewModules("HTTP Response 1");

	# Headers included in _ALL_ the responses, any method, any URI, sucess or error
	my @headers = (
					'Access-Control-Allow-Origin'      => "https://$ENV{ HTTP_HOST }/",
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

	logNewModules("HTTP Response 2");

	if ( exists $ENV{HTTP_COOKIE} && $ENV{HTTP_COOKIE} =~ /CGISESSID/ )
	{
		if ( &validCGISession() )
		{
			my $session = CGI::Session->load( $q );
			logNewModules("HTTP Response 2.1");
			my $session_cookie = $q->cookie( CGISESSID => $session->id );

			push @headers,
			  'Set-Cookie'                    => $session_cookie,
			  'Access-Control-Expose-Headers' => 'Set-Cookie',
			  ;
		}
	}

	logNewModules("HTTP Response 3");

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
		-status  => "$self->{ code } $http_status_codes{ $self->{ code } }",

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

	#~ &zenlog( "Response:$output<" ); # DEBUG
	print $output;

	if ( &debug )
	{
		# log request if debug is enabled
		my $req_msg = "STATUS: $self->{ code } REQUEST: $ENV{REQUEST_METHOD} $ENV{SCRIPT_URL}";
		# include memory usage if debug is 2 or higher
		$req_msg .= " " . &getMemoryUsage() if &debug() > 1;
		&zenlog( $req_msg );

		logNewModules("HTTP Response");

		# log error message on error.
		if ( ref $self->{ body } eq 'HASH' )
		{
			&zenlog( "Error Message: $self->{ body }->{ message }" )
			  if ( exists $self->{ body }->{ message } );
		}
	}

	exit;
}

sub httpErrorResponse
{
	my $args;

	eval { $args = @_ == 1? shift @_: { @_ }; };

	# check errors loading the hash reference
	if ( $@ )
	{
		&zdie( "httpErrorResponse: Wrong argument received" );
	}

	# verify we have a hash reference
	unless ( ref( $args ) eq 'HASH' )
	{
		&zdie( "httpErrorResponse: Argument is not a hash reference." );
	}

	# check required arguments: code, desc and msg
	unless ( $args->{ code } && $args->{ desc } && $args->{ msg } )
	{
		&zdie( "httpErrorResponse: Missing required argument" );
	}

	# check the status code is in a valid range
	unless ( $args->{ code } =~ /^4[0-9][0-9]$/ )
	{
		&zdie( "httpErrorResponse: Non-supported HTTP status code: $args->{ code }" );
	}

	my $body = {
				 description => $args->{ desc },
				 error       => "true",
				 message     => $args->{ msg },
	};

	&zenlog( "[Error] $args->{ desc }: $args->{ msg }" );
	&zenlog( $args->{ log_msg } ) if exists $args->{ log_msg };

	my $response = { code => $args->{ code }, body => $body };

	if ( $0 =~ m!app/zbin/enterprise\.bin$! )
	{
		return $response;
	}

	&httpResponse( $response );
}

# WARNING: Function unfinished.
sub httpSuccessResponse
{
	my ( $args ) = @_;

	unless ( ref( $args ) eq 'HASH' )
	{
		&zdie( "httpSuccessResponse: Argument is not a hash reference" );
	}

	unless ( $args->{ code } && $args->{ desc } && $args->{ msg } )
	{
		&zdie( "httpSuccessResponse: Missing required argument" );
	}

	unless ( $args->{ code } =~ /^2[0-9][0-9]$/ )
	{
		&zdie( "httpSuccessResponse: Non-supported HTTP status code: $args->{ code }" );
	}

	my $body = {
				 description => $args->{ desc },
				 success     => "true",
				 message     => $args->{ msg },
	};

	&zenlog( $args->{ log_msg } ) if exists $args->{ log_msg };
	&httpResponse({ code => $args->{ code }, body => $body });
}

sub httpDownloadResponse
{
	my $args;

	eval { $args = @_ == 1? shift @_: { @_ }; };

	# check errors loading the hash reference
	if ( $@ )
	{
		&zdie( "httpDownloadResponse: Wrong argument received" );
	}

	unless ( ref( $args ) eq 'HASH' )
	{
		&zdie( "httpDownloadResponse: Argument is not a hash reference" );
	}

	unless ( $args->{ desc } && $args->{ dir } && $args->{ file } )
	{
		&zdie( "httpDownloadResponse: Missing required argument" );
	}

	unless ( -d $args->{ dir } )
	{
		my $msg = "Invalid directory '$args->{ dir }'";
		&httpErrorResponse( code => 400, desc => $args->{ desc }, msg => $msg );
	}

	my $path = "$args->{ dir }/$args->{ file }";
	unless ( -f $path )
	{
		my $msg = "The requested file $path could not be found.";
		&httpErrorResponse( code => 400, desc => $args->{ desc }, msg => $msg );
	}

	open ( my $fh, '<', $args->{ path } );
	unless ( $fh )
	{
		my $msg = "Could not open file $path: $!";
		&httpErrorResponse( code => 400, desc => $args->{ desc }, msg => $msg );
	}

	# make headers
	my $headers = {
					-type            => 'application/x-download',
					-attachment      => $args->{ file },
					'Content-length' => -s $path,
	};

	# make body
	my $body;
	binmode $fh;
	{
		local $/ = undef;
		$body = <$fh>;
	}
	close $fh;

	# optionally, remove the downloaded file, useful for temporal files
	unlink $path if $args->{ remove } eq 'true';

	&zenlog( "[Download] $args->{ desc }: $path" );

	&httpResponse({ code => 200, headers => $headers, body => $body });
}

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
	if ( grep { not exists $req{ $_ } } @params )
	{
		my $params = join( ', ', @required );
		my $msg = "Warning: Detected unused eload parameter: $params";

		&zenlog( $msg );
	}

	my $zbin_path  = '/usr/local/zevenet/app/zbin';
	my $enterprise = 'enterprise.bin';
	my $bin        = "$zbin_path/$enterprise";
	my $input;

	require JSON;
	JSON->import( qw( encode_json decode_json ) );

	my $validArrayRef = exists $req{ args } && ref $req{ args } eq 'ARRAY';
	my @args = $validArrayRef ? @{ $req{ args } }: ();

	if ( ref( $req{ args } ) eq 'ARRAY' )
	{
		&zenlog("req{ args }: is an ARRAY ref. OK");
		#~ &zenlog("function args: '@args'");
		#~ &zenlog("first arg: '$args[0]'");
	}
	else
	{
		&zenlog("req{ args }: is not an ARRAY ref. ERROR");
	}

	unless ( eval { $input = encode_json( $req{ args } ) } )
	{
		my $msg = "eload: Error encoding JSON: $@";

		zenlog( $msg );
		die $msg;
	}

	my $cmd = "$bin $req{ module } $req{ func }";

	&zenlog("CMD: '$cmd'");
	&zenlog("INPUT: '$input'");

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

	my $ref = decode_json( $ret_output );

	&httpResponse( $ref );
}

sub _isRunningEnterprise
{
	return ( $0 =~ m!(?:\/|^)enterprise\.bin$! );
}

1;
