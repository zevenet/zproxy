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

use Fcntl ':flock';    #use of lock functions

# generate a lock file based on a input path
sub getLockFile
{
	my $path = shift;
	my $lock = $path;

	my $lock_dir = "/tmp/locks";
	mkdir $lock_dir if !-d $lock_dir;

	$lock =~ s/\//_/g;
	$lock = "$lock_dir/$lock.lock";

	return $lock;
}

sub lockfile
{
	my $lockfile = shift;

	require Zevenet::Debug;
	## lock iptables use ##
	my $open_rc = open ( my $lock_fd, '>', $lockfile );

	if ( $open_rc )
	{
		if ( flock ( $lock_fd, LOCK_EX ) )
		{
			&zenlog( "Success locking IPTABLES", "info", "SYSTEM" ) if &debug == 3;
		}
		else
		{
			&zenlog( "Cannot lock iptables: $!", "error", "SYSTEM" );
		}
	}
	else
	{
		&zenlog( "Cannot open $lockfile: $!", "error", "SYSTEM" );
	}

	return $lock_fd;
}

=begin nd
Function: openlock

	Open file and lock it, return the filehandle.

	Usage:

		my $filehandle = &openlock( $path );
		my $filehandle = &openlock( $path, 'r' );

	Lock is exclusive when the file is openend for writing.
	Lock is shared when the file is openend for reading.
	So only opening for writing is blocking the file for other uses.

	Opening modes:
		r - Read
		w - Write
		a - Append

		t - text mode. To enforce encoding UTF-8.
		b - binary mode. To make sure no information is lost.

	'r', 'w' and 'a' are mutually exclusive.
	't' and 'b' are mutually exclusive.

	If neither 't' or 'b' are used on the mode parameter, the default Perl mode is used.

Parameters:
	path - Absolute or relative path to the file to be opened.
	mode - Mode used to open the file.

Returns:
	scalar - Filehandle
=cut

sub openlock    # ( $path, $mode )
{
	my $path = shift;
	my $mode = shift // '';

	$mode =~ s/a/>>/;	# append
	$mode =~ s/w/>/;	# write
	$mode =~ s/r/</;	# read

	my $binmode  = $mode =~ s/b//;
	my $textmode = $mode =~ s/t//;

	my $encoding = '';
	$encoding = ":encoding(UTF-8)" if $textmode;
	$encoding = ":raw :bytes"      if $binmode;

	open ( my $fh, "$mode $encoding", $path ) || die "Could not open '$path': $!";

	binmode $fh if $fh && $binmode;

	if ( $mode =~ />/ )
	{
		# exclusive lock for writing
		flock $fh, LOCK_EX;
	}
	#~ elsif ( $mode =~ /</ )
	else
	{
		# shared lock for reading
		flock $fh, LOCK_SH;
	}

	return $fh;
}

=begin nd
Function: ztielock

	tie aperture with lock

	Usage:

		$handleArray = &tielock($file);

	Examples:

		$handleArray = &tielock("test.dat");
		$handleArray = &tielock($filename);

Parameters:
	file_name - Path to File.

Returns:
	scalar - Reference to the array with the content of the file.

Bugs:
	Not used yet.
=cut

sub ztielock    # ($file_name)
{
	my $array_ref = shift;    #parameters
	my $file_name = shift;    #parameters

	require Tie::File;

	my $o = tie @{ $array_ref }, "Tie::File", $file_name;
	$o->flock;
}

1;
