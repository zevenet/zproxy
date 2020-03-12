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
use warnings;

use Zevenet::Log;
use Zevenet::Debug;
use Zevenet::CGI;
use Zevenet::API32::HTTP;
use Crypt::CBC;
use POSIX 'strftime';
use Zevenet::SystemInfo;

&setEnv();

my $q = &getCGI();

##### Debugging messages #############################################
#
#~ use Data::Dumper;
#~ $Data::Dumper::Sortkeys = 1;
#
#~ if ( debug() )
#~ {
#~ &zenlog( "REQUEST: $ENV{REQUEST_METHOD} $ENV{SCRIPT_URL}" ) if &debug;
#~ &zenlog( ">>>>>> CGI REQUEST: <$ENV{REQUEST_METHOD} $ENV{SCRIPT_URL}> <<<<<<" ) if &debug;
#~ &zenlog( "HTTP HEADERS: " . join ( ', ', $q->http() ) );
#~ &zenlog( "HTTP_AUTHORIZATION: <$ENV{HTTP_AUTHORIZATION}>" )
#~ if exists $ENV{ HTTP_AUTHORIZATION };
#~ &zenlog( "HTTP_ZAPI_KEY: <$ENV{HTTP_ZAPI_KEY}>" )
#~ if exists $ENV{ HTTP_ZAPI_KEY };
#~
#~ #my $session = new CGI::Session( $q );
#~
#~ my $param_zapikey = $ENV{'HTTP_ZAPI_KEY'};
#~ my $param_session = new CGI::Session( $q );
#~
#~ my $param_client = $q->param('client');
#~
#~
#~ &zenlog("CGI PARAMS: " . Dumper $params );
#~ &zenlog("CGI OBJECT: " . Dumper $q );
#~ &zenlog("CGI VARS: " . Dumper $q->Vars() );
#~ &zenlog("PERL ENV: " . Dumper \%ENV );
#~
#~
#~ my $post_data = $q->param( 'POSTDATA' );
#~ my $put_data  = $q->param( 'PUTDATA' );
#~
#~ &zenlog( "CGI POST DATA: " . $post_data ) if $post_data && &debug && $ENV{ CONTENT_TYPE } eq 'application/json';
#~ &zenlog( "CGI PUT DATA: " . $put_data )   if $put_data && &debug && $ENV{ CONTENT_TYPE } eq 'application/json';
#~ }

##### OPTIONS method request #########################################
require Zevenet::API32::Routes::Options
  if ( $ENV{ REQUEST_METHOD } eq 'OPTIONS' );

##### Load more basic modules ########################################
require Zevenet::Config;
require Zevenet::Validate;

##### Authentication #################################################
require Zevenet::API32::Auth;
require Zevenet::Zapi;

# Session request
require Zevenet::API32::Routes::Session if ( $q->path_info eq '/session' );

# Verify authentication
unless (    ( exists $ENV{ HTTP_ZAPI_KEY } && &validZapiKey() )
		 or ( exists $ENV{ HTTP_COOKIE } && &validCGISession() ) )
{
	&httpResponse(
				   { code => 401, body => { message => 'Authorization required' } } );
}

##### Verify RBAC permissions ########################################
require Zevenet::Core;

my $eload;
if ( eval { require Zevenet::ELoad; } )
{
	$eload = 1;
}

my $rbac_msg = &eload(
					   module => 'Zevenet::RBAC::Core',
					   func   => 'getRBACPermissionsMsg',
					   args   => [$q->path_info, $ENV{ REQUEST_METHOD }],
);
if ( $rbac_msg )
{
	my $desc = "Authentication";
	&httpErrorResponse(
						code => 403,
						desc => $desc,
						msg  => $rbac_msg
	);
}

##### Activation certificates ########################################
require Zevenet::API32::Routes::Activation
  if ( $q->path_info eq '/certificates/activation' );

# Check activation certificate
&checkActivationCertificate();

##### Load API routes ################################################
require Zevenet::API32::Routes;

my $desc = 'Request not found';
my $req  = $ENV{ PATH_INFO };

&httpErrorResponse( code => 404, desc => $desc, msg => "$desc: $req" );

