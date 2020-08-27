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
Function: moveByIndex

	This function moves an element of an list to another position using its index.
	This funcion uses the original array to apply the changes, so it does not return anything.

Parameters:
	Array - Array reference with the list to modify.
	Origin index - Index of the element will be moved.
	Destination index - Position in the list that the element will have.

Returns:
	None - .

=cut

sub moveByIndex
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $list, $ori_index, $dst_index ) = @_;

	my $elem = $list->[$ori_index];

	# delete item
	splice ( @{ $list }, $ori_index, 1 );

	# add item
	splice ( @{ $list }, $dst_index, 0, $elem );
}

=begin nd
Function: getARRIndex

	It retuns the index of for a value of a list. It retunrs the first index where the value appears.

Parameters:
	Array ref - Array reference with the list to look for.
	Value - Value to get its index

Returns:
	Integer - index for an array value

=cut

sub getARRIndex
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $list, $item ) = @_;
	my $ind;

	my $id = 0;
	foreach my $it ( @{ $list } )
	{
		if ( $it eq $item )
		{
			$ind = $id;
			last;
		}
		$id++;
	}

	# fixme:  return undef when the index is not found

	return $ind;
}

=begin nd
Function: uniqueArray

	It gets an array for reference and it removes the items that are repated.
	The original input array is modified. This function does not return anything

Parameters:
	Array ref - It is the array is going to be managed

Returns:
	None - .

=cut

sub uniqueArray
{
	my $arr = shift;

	my %hold = ();

	foreach my $v ( @{ $arr } )
	{
		$hold{ $v } = 1 unless exists $hold{ $v };
	}

	@{ $arr } = keys %hold;
}

1;

