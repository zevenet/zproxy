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

my $q = getCGI();
my $farm_re    = &getValidFormat( 'farm_name' );


if ( $q->path_info =~ qr{/ipds/blacklists} )
{
	require Zevenet::API3::IPDS::Blacklist;

	my $blacklists_list      = &getValidFormat( 'blacklists_name' );
	my $blacklists_source_id = &getValidFormat( 'blacklists_source_id' );

	# BLACKLISTS
	#  GET all blacklists
	GET qr{^/ipds/blacklists$} => \&get_blacklists_all_lists;

	#  POST blacklists list
	POST qr{^/ipds/blacklists$} => \&add_blacklists_list;

	#  GET blacklists lists
	GET qr{^/ipds/blacklists/($blacklists_list)$} => \&get_blacklists_list;

	#  PUT blacklists list
	PUT qr{^/ipds/blacklists/($blacklists_list)$} => \&set_blacklists_list;

	#  DELETE blacklists list
	DELETE qr{^/ipds/blacklists/($blacklists_list)$} => \&del_blacklists_list;

	#  UPDATE a remote blacklists
	POST qr{^/ipds/blacklists/($blacklists_list)/actions$} => \&update_remote_blacklists;

	#  GET a source from a blacklists
	GET qr{^/ipds/blacklists/($blacklists_list)/sources$} => \&get_blacklists_source;

	#  POST a source from a blacklists
	POST qr{^/ipds/blacklists/($blacklists_list)/sources$} => \&add_blacklists_source;

	#  PUT a source from a blacklists
	PUT qr{^/ipds/blacklists/($blacklists_list)/sources/($blacklists_source_id)$} => \&set_blacklists_source;

	#  DELETE a source from a blacklists
	DELETE
	  qr{^/ipds/blacklists/($blacklists_list)/sources/($blacklists_source_id)$}
	  => \&del_blacklists_source;

	#  POST list to farm
	POST qr{^/farms/($farm_re)/ipds/blacklists$} => \&add_blacklists_to_farm;

	#  DELETE list from farm
	DELETE qr{^/farms/($farm_re)/ipds/blacklists/($blacklists_list)$} => \&del_blacklists_from_farm;
}

1;
