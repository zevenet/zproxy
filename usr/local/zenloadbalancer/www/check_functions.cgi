#!/usr/bin/perl

###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
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



=begin nd
        Function: getCheckParam

        check if a param has correct format

        Parameters:
				param	- type param
				value	- new value
				
        Returns:
				-1	- error
				0	- successful

=cut
# &getCheckParam ( $param, $value );
sub getCheckParam
{
	my ( $param, $value ) = @_;
	my $err = -1;
	
	if ( $param eq 'farm_name' &&
		$value =~ /^[a-zA-Z0-9\-]+$/ )
	{
		$err = 0;
	}
	
	if ( $param eq 'rbl_list_name' &&
		$value =~ /^[a-zA-Z0-9]+$/ )
	{
		$err = 0;
	}
	
	return $err;
}



1;









