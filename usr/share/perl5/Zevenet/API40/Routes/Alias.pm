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

# Alias
if ( $ENV{ PATH_INFO } =~ qr{^/aliases} )
{
	my $mod        = 'Zevenet::API40::Alias';
	my $alias_type = &getValidFormat( 'alias_type' );

	# /aliases/(backend)s, not match the charater 's'
	GET qr{^/aliases/($alias_type)s$},            'get_by_type',  $mod;
	POST qr{^/aliases/($alias_type)s$},           'add_alias',    $mod;
	PUT qr{^/aliases/($alias_type)s/([^/]+)$},    'set_alias',    $mod;
	DELETE qr{^/aliases/($alias_type)s/([^/]+)$}, 'delete_alias', $mod;
}

1;
