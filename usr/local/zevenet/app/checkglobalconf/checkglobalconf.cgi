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

# This script updates or generates the file global.conf:
#
# * If a variable on global.conf does not exist but exists on global.conf.tpl then adds the new variable on global.conf.
# * If a variable on global.conf.tpl equals "" do nothing.
# * If a variable on global.conf.tpl is equal to the variable on global.conf.tpl do nothing
# * If a variable on global.conf is not equal to variable on global.conf.tpl, the variable on globa.conf is not changed.
# * If a valiable's line on global.conf.tpl ends with #update, the variable is updated on global.conf.

use strict;
use warnings;
use File::Copy;

my $tglobal   = "/usr/local/zevenet/app/checkglobalconf/global.conf.tmp";
my $global    = "/usr/local/zevenet/config/global.conf";
my $globaltpl = "/usr/local/zevenet/app/checkglobalconf/global.conf.tpl";

unless ( -f $global )
{
	system( "cp $globaltpl $global" );
	exit 0;
}

open my $fw,            '>', $tmp_global;
open my $file_template, '<', $globaltpl;

while ( my $tpl_line = <$file_template> )
{
	my $newline = $tpl_line;

	if ( $tpl_line =~ /^\$/ )
	{
		my @vble = split ( '=', $tpl_line );
		$vble[0] =~ s/\$//;
		my $exit = 'true';

		open my $fr, '<', $global;

		while ( my $line = <$fr> || $exit eq 'false' )
		{
			if ( $line =~ /^\$$vble[0] ?\=/ )
			{
				my @vblegconf = split ( "\=", $line );
				$vblegconf[1] =~ s/^\s?//g;
				$vble[1] =~ s/^\s?//g;

				if ( $vblegconf[1] !~ /""/ && $vblegconf[1] !~ $vble[1] && $vble[1] !~ /\#update/ )
				{
					$newline = $line;
				}

				if ( $vble[1] =~ /\#update/i )
				{
					$tpl_line =~ s/\#update//i;
					$newline = $tpl_line;
				}
			}
		}

		close $fr;
	}

	print $fw "$newline";
}

close $fw;
close $file_template;

move( $tmp_global, $global );
print "Update global.conf file done...\n";
