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

if ( $ENV{ PATH_INFO } =~ qr{^/system/ssh} )
{
	my $mod = 'Zevenet::API40::System::Service::SSH';

	GET qr{^/system/ssh$},  'get_ssh', $mod;
	POST qr{^/system/ssh$}, 'set_ssh', $mod;
}

if ( $ENV{ PATH_INFO } =~ qr{^/system/proxy} )
{
	my $mod = 'Zevenet::API40::System::Service::Proxy';

	GET qr{^/system/proxy$},  'get_proxy', $mod;
	POST qr{^/system/proxy$}, 'set_proxy', $mod;
}

if ( $ENV{ PATH_INFO } =~ qr{^/system/http} )
{
	my $mod = 'Zevenet::API40::System::Service::HTTP';

	GET qr{^/system/http$},  'get_http', $mod;
	POST qr{^/system/http$}, 'set_http', $mod;
}

if ( $ENV{ PATH_INFO } =~ qr{^/system/(?:factory|packages)} )
{
	my $mod = 'Zevenet::API40::System::Ext';

	POST qr{^/system/factory$}, 'set_factory_reset', $mod;
	GET qr{^/system/packages$}, 'get_packages_info', $mod;
	POST qr{^/system/packages/offline$}, 'upload_iso_offline', $mod;
}

1;
