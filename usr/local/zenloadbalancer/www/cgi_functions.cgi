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

use CGI;
use CGI::Carp qw(warningsToBrowser fatalsToBrowser);

use feature 'state';

# getCGI returns a cgi object.
# get a cgi object only once per http request and reuse the same object
sub getCGI
{
	state $cgi = CGI->new();
	return $cgi;
}

# &getCgiParam();
#		return = \%cgiVars			// Hash reference
# &getCgiParam( $variableName );
#		return = $varValue
sub getCgiParam
{
	my $variable = shift;

	my $cgi = getCGI();

	return eval { $cgi->param( $variable ) } if $variable;

	return $cgi->Vars;
}

1;
