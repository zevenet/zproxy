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

my $farm_re    = &getValidFormat( 'farm_name' );
my $service_re = &getValidFormat( 'service' );
my $cert_re    = &getValidFormat( 'certificate' );

if ( $ENV{ PATH_INFO } =~ qr{^/farms/$farm_re/services/$service_re/actions$} )
{
	my $mod = 'Zevenet::API40::Farm::MoveService';

	POST qr{^/farms/($farm_re)/services/($service_re)/actions$}, 'move_services',
	  $mod;
}

if ( $ENV{ PATH_INFO } =~
	qr{^/farms/$farm_re/(?:addheader|headremove|addresponseheader|removeresponseheader)(:?/\d+)?$}
  )
{
	my $mod     = 'Zevenet::API40::Farm::HTTP::Ext';
	my $cert_re = &getValidFormat( 'certificate' );

	POST qr{^/farms/($farm_re)/addheader$},          'add_addheader',  $mod;
	DELETE qr{^/farms/($farm_re)/addheader/(\d+)$},  'del_addheader',  $mod;
	POST qr{^/farms/($farm_re)/headremove$},         'add_headremove', $mod;
	DELETE qr{^/farms/($farm_re)/headremove/(\d+)$}, 'del_headremove', $mod;

	POST qr{^/farms/($farm_re)/addresponseheader$}, 'add_addResponseheader', $mod;
	DELETE qr{^/farms/($farm_re)/addresponseheader/(\d+)$},
	  'del_addResponseheader', $mod;
	POST qr{^/farms/($farm_re)/removeresponseheader$}, 'add_removeResponseheader',
	  $mod;
	DELETE qr{^/farms/($farm_re)/removeresponseheader/(\d+)$},
	  'del_removeResponseHeader', $mod;
}

if (
	 $ENV{ PATH_INFO } =~ qr{^/farms/$farm_re/certificates/($cert_re)/actions$} )
{
	my $mod = 'Zevenet::API40::Farm::HTTP::Ext';
	POST qr{^/farms/($farm_re)/certificates/($cert_re)/actions$},
	  'farm_move_certs', $mod;
}

1;
