#!/usr/bin/perl
#    Zen Load Balancer is an entire solution for Load Balancing.
#    Copyright (C) 2011  Emilio Campos Martin
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#this script update global.conf:
#*if vble not exist on global.conf but exist on global.conf.tpl
#then new variable on global.conf.
#*if vble="" on global.conf.tpl do nothing
#*if vble on global.conf.tpl = vble on global.conf.tpl do nothing
#*if vble on global.conf is not equal to vble on global.conf.tpl
#vble on globa.conf persist.
#*if end of line on vble global.conf.tpl is #update, vble is updated
#on global.conf
#emilio campos martin <emilio.campos.martin@gmail.com>

use File::Copy;

$tglobal="/usr/local/zenloadbalancer/app/checkglobalconf/global.conf.tmp";
$global="/usr/local/zenloadbalancer/config/global.conf";
$globaltpl="/usr/local/zenloadbalancer/app/checkglobalconf/global.conf.tpl";
open FW, ">$tglobal";

#use Tie::File;

#tie @gfile, 'Tie::File', "$global";
#tie @tfile, 'Tie::File', "$globaltpl";
open FTPL, "$globaltpl";
while ($linetpl=<FTPL>)
	{
	$newline = $linetpl;
	if ($linetpl =~ /^\$/)
		{
		@vble = split("\=",$linetpl);
		@vble[0] =~ s/\$//;
		open FR, "$global";
		$exit = "true";
		while ($line=<FR> || $exit eq "false")	
			{
			if ($line =~ /^\$@vble[0]\=/)
				{
				#$exit = "false";
				@vblegconf = split("\=",$line);
				#if (@vblegconf[1] !~ /""/ && @vble[1] !~ @vblegconf[1])
				if (@vblegconf[1] !~ /""/ && @vblegconf[1] !~ @vble[1])
					{
					$newline = $line;
					}
				if (@vble[1] =~ /\#update/i)
					{
					$linetpl =~ s/\#update//i;
					$newline = $linetpl;
					}
				}
			}
		
		}
	print FW "$newline";
	}


close FW;
close FR;
close FTPL;

move($tglobal,$global);
print "update global.conf file done...\n";
