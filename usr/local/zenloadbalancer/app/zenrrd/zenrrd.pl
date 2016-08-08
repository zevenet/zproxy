#!/usr/bin/perl
###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2014-2016 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
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

# This script runs all te *-rrd.pl files included in the same folder

require ("/usr/local/zenloadbalancer/config/global.conf");
$lockfile="/tmp/rrd.lock";

if ( -e $lockfile ) {
	print "$0: Warning: RRD Locked by $lockfile, maybe other zenrrd in is being executed\n";
	exit;
} else {
	open LOCK, '>', $lockfile;
	print LOCK "lock rrd";
	close LOCK;
}

opendir(DIR, $rrdap_dir);
@files = grep(/-rrd.pl$/,readdir(DIR));
closedir(DIR);

foreach $file(@files) {
	print "$0: Info: Executing $file...\n";

	if ($log_rrd eq "") {
		my @system =`$rrdap_dir/$file`;
	} else {
		my @system =`$rrdap_dir/$file >> $rrdap_dir/$log_rrd`;
	}
}

if ( -e $lockfile ) {
	unlink($lockfile);
}

