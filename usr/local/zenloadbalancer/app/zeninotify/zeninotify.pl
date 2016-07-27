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

use Linux::Inotify2;
use Sys::Hostname;

require '/usr/local/zenloadbalancer/config/global.conf';
require '/usr/local/zenloadbalancer/www/functions_ext.cgi';

my $hostname = hostname();
my $sync     = "firstime";
my @alert;

push ( @alert, $configdir );
push ( @alert, $rttables );

#open file cluster
open FR, "$filecluster";
while ( <FR> )
{
	if ( $_ =~ /^MEMBERS/ )
	{
		@clusterconf = split ( ":", $_ );
		if ( $clusterconf[1] eq $hostname )
		{
			$rip = $clusterconf[4];
		}
		else
		{
			$rip = $clusterconf[2];
		}
		chomp ( $rip );
	}
}
close FR;

#pid file
open my $fo, ">", "$zeninopid";
print $fo "$$";
close $fo;

&zenlog( "Running the first replication..." );
$exclude = &cluster();
if ( $exclude ne "1" )
{
	my $rsync_command =
	  "$rsync $zenrsync $exclude $configdir\/ root\@$rip:$configdir\/";
	&zenlog( "$rsync_command" );
	system ( $rsync_command);

	my $rsync_rttables_command = "$rsync $zenrsync $rttables root\@$rip:$rttables";
	&zenlog( "$rsync_rttables_command" );
	system ( $rsync_rttables_command);
}
&zenlog( "Terminated the first replication..." );

for my $subdir ( &getSubdirectories( $configdir ) )
{
	&zenlog( "Watching directory $subdir" );
	push ( @alert, $subdir );
}

my $inotify = new Linux::Inotify2();

#foreach ($configdir $rttable)
foreach ( @alert )
{
	$inotify->watch( $_, IN_MODIFY | IN_CREATE | IN_DELETE );
}

while ( 1 )
{
	# By default this will block until something is read
	my @events = $inotify->read();
	if ( scalar ( @events ) == 0 )
	{
		&zenlog( "read error: $!" );
		last;
	}

	foreach my $event ( @events )
	{
		if ( $event->name !~ /^\..*/ && $event->name !~ /.*\~$/ )
		{
			$action = sprintf ( "%d", $event->mask );
			$name   = $event->fullname;
			$file   = $event->name;
			if ( $action eq 512 )
			{
				$action = "DELETED";
			}
			if ( $action eq 2 )
			{
				$action = "MODIFIED";
			}
			if ( $action eq 256 )
			{
				$action = "CREATED";
			}
			if ( $action eq 1073742080 )    # create dir
			{
				#~ $action = "CREATED";
				&zenlog( "Watching $event_fullname" );
				$inotify->watch( $event->fullname, IN_MODIFY | IN_CREATE | IN_DELETE );
				next;
			}
			&zenlog( "File: $file; Action: $action Fullname: $name" );

			if ( $name =~ /config/ )
			{
				$exclude = &cluster();

				#if ($fileif =~ "1")
				if ( $exclude eq "1" )
				{
					&zenlog( "File cluster not configured, aborting..." );
					exit 1;
				}
				&zenlog( "Exclude files: $exclude" );
				my $eject = `$rsync $zenrsync $exclude $configdir\/ root\@$rip:$configdir\/`;
				&zenlog( $eject );
				&zenlog(
					"run replication process: $rsync $zenrsync $exclude $configdir\/ root\@$rip:$configdir\/"
				);
			}

			if ( $name =~ /iproute2/ )
			{
				my $eject = `$rsync $zenrsync $rttables root\@$rip:$rttables`;
				&zenlog( $eject );
				&zenlog(
					   "run replication process: $rsync $zenrsync $rttables root\@$rip:$rttables" );
			}
		}
	}
}

sub cluster()
{
	if ( -e $filecluster )
	{
		#exclude file with eth on https gui
		$filehttp = "";
		open FH, "<", $confhttp;
		@filehttp = <FH>;
		$host     = $filehttp[0];
		@host     = split ( "=", $host );
		$iphttp   = $host[1];
		close FH;

		#exclude file with eth on cluster
		$filecl = "";
		open FO, "<$filecluster";
		@file = <FO>;
		if ( grep ( /UP/, @file ) )
		{
			$members = $file[0];
			@members = split ( ":", $members );
			$ip1     = $members[2];
			$ip2     = $members[4];
			chomp ( $ip1 );
			chomp ( $ip2 );

			#the real ip for cluster member
			opendir ( DIR, $configdir );
			@files = grep ( /^if\_.*\_conf$/, readdir ( DIR ) );
			closedir ( DIR );

			#first real interfaces
			foreach $file ( @files )
			{
				if ( $file !~ /:/ )
				{
					open FR, "<$configdir\/$file";
					@fif = <FR>;
					close FR;
					if ( ( grep ( /$ip1/, @fif ) ) || ( grep ( /$ip2/, @fif ) ) )
					{
						$filecl = $file;
					}
					chomp ( $iphttp );
					if ( $iphttp !~ /\*/ && ( grep ( /$iphttp/, @fif ) ) )
					{
						$filehttp = $file;
					}
				}
			}
		}
		close FO;
	}

	if ( $filecl ne "" && $filehttp ne "" && $filecl ne $filehttp )
	{
		$stringtemp = "--exclude=$filehttp --exclude=$filecl";
	}

	if ( $filecl ne "" && $filehttp ne "" && $filecl eq $filehttp )
	{
		$stringtemp = "--exclude=$filecl";
	}

	if ( $filecl ne "" & $filehttp eq "" )
	{
		$stringtemp = "--exclude=$filecl";
	}

	if ( $filecl =~ /^$/ )
	{
		$strikgtemp = "1";
	}

	return $stringtemp;
}

sub getSubdirectories
{
	my $dir_path = shift;

	opendir my $dir_h, $dir_path;

	if ( !$dir_h )
	{
		&zenlog( "Could not open directory $dir_path: $!" );
		return 1;
	}

	my @dir_list;

	while ( my $dir_entry = readdir $dir_h )
	{
		next if $dir_entry eq '.';
		next if $dir_entry eq '..';

		my $subdir = "$dir_path/$dir_entry";

		if ( -d $subdir )
		{
			push ( @dir_list, $subdir );

			my @subdirectories = &getSubdirectories( $subdir );

			push ( @dir_list, @subdirectories );
		}
	}

	closedir $dir_h;

	return @dir_list;
}
