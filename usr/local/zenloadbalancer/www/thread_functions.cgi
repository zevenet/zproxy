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
use threads;

sub runParallel
{
	# input
	my $code_ref = shift;
	my $arg_list = shift;

	# validate input arguments
	if ( ref $code_ref ne 'CODE' )
	{
		&zenlog( ( caller )[3] . ": Invalid code ref");
		die;
	}

	if ( ref $arg_list ne 'ARRAY' )
	{
		&zenlog( ( caller )[3] . ": Invalid argument list");
		die;
	}

	# output
	my @threads;

	# create threads
	for my $arg ( @{ $arg_list } )
	{
		my %th = (
				   arg     => $arg,
				   thread  => threads->create( $code_ref, $arg ),
				   ret_val => undef,
		);

		$th{tid} = $th{thread}->tid();

		push( @threads, \%th );
	}

	# wait for threads output
	for my $th ( @threads )
	{
		$th->{ret_val} = $th->{thread}->join();
	}

	return \@threads;
}

sub zenlog_thread
{
	my $msg = shift;

	my $tid = threads->self->tid();
	my $prefix_format = "\[$tid\] ";

	$msg =~ s/^/$prefix_format/g;
	$msg =~ s/\n/\n$prefix_format/g;

	return &zenlog( $msg, @_ );
}

### Example:
#
## input
#my $code = \&sub1;
#my $argument_list = [ 1..10 ];
#
#my $threads = &runParallel( \&sub1, $argument_list );
#
#for my $th ( @{ $threads } )
#{
#	print $th->{ret_val} . "\n";
#}
#
#print "End\n";
#
#
#
#sub sub1
#{
#	my $arg = shift;
#	
#	my $r = int(rand(5));
#	sleep $r;
#	
#	print("End of thread $arg\n");
#	return $r;
#}
#

1;
