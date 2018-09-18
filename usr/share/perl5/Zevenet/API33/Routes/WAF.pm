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


my $set_name  = &getValidFormat( 'waf_set_name' );
my $rule_id  = &getValidFormat( 'waf_rule_id' );

if ( $ENV{ PATH_INFO } =~ qr{/ipds/waf/$set_name/rules} )
{
	my $mod = 'Zevenet::API33::IPDS::WAF::Rules';

	#  POST /ipds/waf/<set>/rules
	POST qr{^/ipds/waf/($set_name)/rules$}, 'create_waf_rule', $mod;

	#  PUT /ipds/waf/<set>/rules/<id>
	PUT qr{^/ipds/waf/($set_name)/rules/($rule_id)$}, 'modify_waf_rule', $mod;

	#  DELETE /ipds/waf/<set>/rules/<id>
	DELETE qr{^/ipds/waf/($set_name)/rules/($rule_id)$}, 'delete_waf_rule', $mod;
}

if ( $ENV{ PATH_INFO } =~ qr{/ipds/waf} )
{
	my $mod = 'Zevenet::API33::IPDS::WAF::Sets';

	my $farmname_re  = &getValidFormat( 'waf_rule_id' );

	#  GET /ipds/waf
	GET qr{^/ipds/waf$}, 'list_waf_sets', $mod;

	#  POST /ipds/waf
	POST qr{^/ipds/waf$}, 'create_waf_sets', $mod;
	# ????? crear mandando 'name'
	# opcionalmente 'copy_from'

	#  GET /ipds/waf/<set>
	GET qr{^/ipds/waf/($set_name)$}, 'get_waf_set', $mod;

	#  PUT /ipds/waf/<set>
	#~ PUT qr{^/ipds/waf/$set_name$}, 'modify_waf_set', $mod;
	# ???? modificar directivas globales, añadiendo encima del fichero

	#~ PUT qr{^/ipds/waf/$set_name$}, 'modify_waf_set', $mod;
	# ????

	#  DELETE /ipds/waf/<set>
	DELETE qr{^/ipds/waf/($set_name)$}, 'delete_waf_set', $mod;

	#~ #  POST /farms/<farm>/ipds/waf
	#~ POST qr{^/farms/$farmname_re/ipds/waf$}, 'add_farm_waf_set', $mod;

	#~ #  DELETE /farms/<farm>/ipds/waf
	#~ DELETE qr{^/farms/$farmname_re/ipds/waf$}, 'remove_farm_waf_rule', $mod;
}


1;

