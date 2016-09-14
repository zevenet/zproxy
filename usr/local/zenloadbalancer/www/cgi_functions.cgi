###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2016 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This library is free software; you can redistribute it and/or modify it
#     under the terms of the GNU Lesser General Public License as published
#     by the Free Software Foundation; either version 2.1 of the License, or
#     (at your option) any later version.
#
#     This library is distributed in the hope that it will be useful, but
#     WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
#     General Public License for more details.
#
#     You should have received a copy of the GNU Lesser General Public License
#     along with this library; if not, write to the Free Software Foundation,
#     Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
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

# &getCgiData();
#		return = \%cgiVars			// Object
# &getCgiData( $variableName );
#		return = $varValue
sub getCgiData
{
	my ( $variable ) = @_;

	my $cgi = getCGI();

	my $value = $cgi->param( $variable )
	  if ( defined ( $cgi->param( $variable ) ) );

	$value = $cgi->Vars if ( $value eq "" );

	return $value;
}

1;
