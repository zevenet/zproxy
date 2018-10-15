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

my $farm_re  = &getValidFormat( 'farm_name' );
my $set_name = &getValidFormat( 'waf_set_name' );
my $rule_id  = &getValidFormat( 'waf_rule_id' );
my $index    = &getValidFormat( 'waf_chain_id' );

if ( $ENV{ PATH_INFO } =~ qr{^/ipds/waf/$set_name/rules} )
{
	my $mod = 'Zevenet::API40::IPDS::WAF::Rules';

	#  GET /ipds/waf/<set>/rules/<id>
	GET qr{^/ipds/waf/($set_name)/rules/($rule_id)$}, 'get_waf_rule', $mod;

	#  POST /ipds/waf/<set>/rules
	POST qr{^/ipds/waf/($set_name)/rules$}, 'create_waf_rule', $mod;

	#  PUT /ipds/waf/<set>/rules/<id>
	PUT qr{^/ipds/waf/($set_name)/rules/($rule_id)$}, 'modify_waf_rule', $mod;

	#  DELETE /ipds/waf/<set>/rules/<id>
	DELETE qr{^/ipds/waf/($set_name)/rules/($rule_id)$}, 'delete_waf_rule', $mod;

	#  POST /ipds/waf/<set>/rules/<id>/actions
	POST qr{^/ipds/waf/($set_name)/rules/($rule_id)/actions$}, 'move_waf_rule',
	  $mod;

	#  POST /ipds/waf/<set>/rules/<id>/chain
	POST qr{^/ipds/waf/($set_name)/rules/($rule_id)/chains$},
	  'create_waf_rule_chain', $mod;

	#  PUT /ipds/waf/<set>/rules/<id>/chain/($index)
	PUT qr{^/ipds/waf/($set_name)/rules/($rule_id)/chains/($index)$},
	  'modify_waf_rule_chain', $mod;

	#  DELETE /ipds/waf/<set>/rules/<id>/chain/index
	DELETE qr{^/ipds/waf/($set_name)/rules/($rule_id)/chains/($index)$},
	  'delete_waf_rule_chain', $mod;
}

if ( $ENV{ PATH_INFO } =~ qr{/ipds/waf} )
{
	my $mod = 'Zevenet::API40::IPDS::WAF::Sets';

	#  GET /ipds/waf
	GET qr{^/ipds/waf$}, 'list_waf_sets', $mod;

	#  POST /ipds/waf
	POST qr{^/ipds/waf$}, 'create_waf_set', $mod;

	#  GET /ipds/waf/<set>
	GET qr{^/ipds/waf/($set_name)$}, 'get_waf_set', $mod;

	#  PUT /ipds/waf/<set>
	PUT qr{^/ipds/waf/($set_name)$}, 'modify_waf_set', $mod;

	#  DELETE /ipds/waf/<set>
	DELETE qr{^/ipds/waf/($set_name)$}, 'delete_waf_set', $mod;

	#  POST /farms/<farm>/ipds/waf
	POST qr{^/farms/($farm_re)/ipds/waf$}, 'add_farm_waf_set', $mod;

	#  DELETE /farms/<farm>/ipds/waf/<set>
	DELETE qr{^/farms/($farm_re)/ipds/waf/($set_name)$}, 'remove_farm_waf_set',
	  $mod;

	#  POST /farms/<farm>/ipds/waf/<set>/actions
	POST qr{^/farms/($farm_re)/ipds/waf/($set_name)/actions$}, 'move_farm_waf_set',
	  $mod;
}

1;

