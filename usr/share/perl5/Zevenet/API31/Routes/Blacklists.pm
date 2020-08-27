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

if ( $ENV{ PATH_INFO } =~ qr{/ipds/blacklists} )
{
	my $mod = 'Zevenet::API31::IPDS::Blacklist';

	my $farm_re              = &getValidFormat( 'farm_name' );
	my $blacklists_list      = &getValidFormat( 'blacklists_name' );
	my $blacklists_source_id = '\d+';

	# BLACKLISTS
	#  GET all blacklists
	GET qr{^/ipds/blacklists$}, 'get_blacklists_all_lists', $mod;

	#  POST blacklists list
	POST qr{^/ipds/blacklists$}, 'add_blacklists_list', $mod;

	#  GET blacklists lists
	GET qr{^/ipds/blacklists/($blacklists_list)$}, 'get_blacklists_list', $mod;

	#  PUT blacklists list
	PUT qr{^/ipds/blacklists/($blacklists_list)$}, 'set_blacklists_list', $mod;

	#  DELETE blacklists list
	DELETE qr{^/ipds/blacklists/($blacklists_list)$}, 'del_blacklists_list', $mod;

	#  action for a blacklists
	POST qr{^/ipds/blacklists/($blacklists_list)/actions$}, 'actions_blacklists',
	  $mod;

	#  GET a source from a blacklists
	GET qr{^/ipds/blacklists/($blacklists_list)/sources$}, 'get_blacklists_source',
	  $mod;

	#  POST a source from a blacklists
	POST qr{^/ipds/blacklists/($blacklists_list)/sources$},
	  'add_blacklists_source', $mod;

	#  PUT a source from a blacklists
	PUT qr{^/ipds/blacklists/($blacklists_list)/sources/($blacklists_source_id)$},
	  'set_blacklists_source', $mod;

	#  DELETE a source from a blacklists
	DELETE
	  qr{^/ipds/blacklists/($blacklists_list)/sources/($blacklists_source_id)$},
	  'del_blacklists_source', $mod;

	#  POST list to farm
	POST qr{^/farms/($farm_re)/ipds/blacklists$}, 'add_blacklists_to_farm', $mod;

	#  DELETE list from farm
	DELETE qr{^/farms/($farm_re)/ipds/blacklists/($blacklists_list)$},
	  'del_blacklists_from_farm', $mod;
}

1;
