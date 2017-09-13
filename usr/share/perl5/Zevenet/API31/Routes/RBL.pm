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


if ( $q->path_info =~ qr{/ipds/rbl} )
{
	require Zevenet::API31::IPDS::RBL;

	my $rbl_name   = &getValidFormat( 'rbl_name' );
	my $rbl_domain = &getValidFormat( 'rbl_domain' );

	#GET /ipds/rbl/domains
	GET qr{^/ipds/rbl/domains$} => \&get_rbl_domains;

	#  POST /ipds/rbl/domains
	POST qr{^/ipds/rbl/domains$} => \&add_rbl_domain;

	#  PUT /ipds/rbl/domains/<domain>
	PUT qr{^/ipds/rbl/domains/($rbl_domain)$} => \&set_rbl_domain;

	#  DELETE /ipds/rbl/domains/<domain>
	DELETE qr{^/ipds/rbl/domains/($rbl_domain)$} => \&del_rbl_domain;

	# GET /ipds/rbl
	GET qr{^/ipds/rbl$} => \&get_rbl_all_rules;

	# GET /ipds/rbl/<name>
	GET qr{^/ipds/rbl/($rbl_name)$} => \&get_rbl_rule;

	#  POST /ipds/rbl
	POST qr{^/ipds/rbl$} => \&add_rbl_rule;

	#  POST /ipds/rbl/<name>
	POST qr{^/ipds/rbl/($rbl_name)$} => \&copy_rbl_rule;

	#  PUT /ipds/rbl/<name>
	PUT qr{^/ipds/rbl/($rbl_name)$} => \&set_rbl_rule;

	#  DELETE /ipds/rbl/<name>
	DELETE qr{^/ipds/rbl/($rbl_name)$} => \&del_rbl_rule;

	#  POST /ipds/rbl/<name>/domains
	POST qr{^/ipds/rbl/($rbl_name)/domains$} => \&add_domain_to_rbl;

	#  DELETE /ipds/rbl/<name>/domains/<domain>
	DELETE qr{^/ipds/rbl/($rbl_name)/domains/($rbl_domain)$} => \&del_domain_from_rbl;

	#  POST /farms/<farmname>/ipds/rbl
	POST qr{^/farms/($farm_re)/ipds/rbl$} => \&add_rbl_to_farm;

	# DELETE /farms/<farmname>/ipds/rbl/<name>
	DELETE qr{^/farms/($farm_re)/ipds/rbl/($rbl_name)$} => \&del_rbl_from_farm;

	# POST /ipds/rbl/<name>/actions
	POST qr{^/ipds/rbl/($rbl_name)/actions$} => \&set_rbl_actions;
}

1;
