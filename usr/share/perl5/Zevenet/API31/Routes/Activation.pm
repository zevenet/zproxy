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

if ( $ENV{ PATH_INFO } =~ qr{^/certificates/activation$} )
{
	my $mod = 'Zevenet::API31::Certificate::Activation';

	logNewModules("In /certificates/activation");

	GET    qr{^/certificates/activation$}, 'get_activation_certificate_info', $mod;
	POST   qr{^/certificates/activation$}, 'upload_activation_certificate',   $mod;
	DELETE qr{^/certificates/activation$}, 'delete_activation_certificate',   $mod;
}

1;
