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

sub getFile
{
	my $path = shift;

	unless ( -f $path )
	{
		&zenlog("Could not find file '$path'");
	}

	open ( my $fh, '<', $path );

	unless ( $fh )
	{
		&zenlog("Could not open file '$path': $!");
		return;
	}

	my $content;

	binmode $fh;
	{
		local $/ = undef;
		$content = <$fh>;
	}

	close $fh;

	return $content;
}

sub setFile
{
	my $path = shift;
	my $content = shift;

	open ( my $fh, '>', $path );

	unless ( $fh )
	{
		&zenlog("Could not open file '$path': $!");
		return 0;
	}

	binmode $fh;
	print $content $fh;

	unless ( close $fh )
	{
		&zenlog("Could not save file '$path': $!");
		return 0;
	}

	return 1;
}

1;
