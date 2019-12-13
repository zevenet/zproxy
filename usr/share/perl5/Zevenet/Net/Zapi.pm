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

=begin nd
Function: checkZapiIfDepsRouting

	This function is for using in the API logic.
	It checks if the interface is beeing deleted or modified has any dependency with some customized route,
	if the force action is applied, those dependence routes will be deleted.

Parameters:
	if - interface name
	method - http method is applying. 'del' or 'put'
	json_obj - sent parameters in the json

Returns:
	none - .

=cut

sub checkZapiIfDepsRouting
{
	my $if = shift;
	my $method = shift;
	my $in = shift;

	my $desc = ($method eq 'del') ? "Deleting interface" : "Modifying interface";

	include 'Zevenet::Net::Routing';
	my $list = &listRoutingDependIface($if);
	if (@{$list})
	{
		unless (exists $in->{force} and $in->{force} eq 'true')
		{
			my $msg = "There are routes in this interface.";

			if ($method eq 'del')
			{
				$msg .= " . Please, delete them before continuing.";
			}
			elsif ($method eq 'put')
			{
				$msg .= " . If you are sure, repeat with the parameter 'force'. All routes that depend on this interface will be deleted.";
			}
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
		&delRoutingDependIface($if);
	}
}

sub checkZapiVirtDepsRouting
{
	# ???????
}




1;
