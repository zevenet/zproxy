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

# zeninotify version 2.0
use strict;
use warnings;
use Linux::Inotify2;
use Zevenet::Config;
use Zevenet::Log;
include 'Zevenet::Cluster';

my $configdir = &getGlobalConfiguration( 'configdir' );
my $rttables  = &getGlobalConfiguration( 'rttables' );
my $zeninopid = &getGlobalConfiguration( 'zeninopid' );

my $pid;

# Get zeninotify status
if ( -e $zeninopid )
{
	open my $pidfile, "<", "$zeninopid";
	$pid = <$pidfile>;
	close $pidfile;
	my $kill  = &getGlobalConfiguration( 'kill_bin' );
	my $error = &logAndRun( "$kill -0 $pid" );
	if ( $error )
	{
		unlink $zeninopid;
	}
}

if ( @ARGV && $ARGV[0] eq 'stop' )
{
	if ( -e $zeninopid )
	{
		kill ( 'TERM', $pid );
		unlink $zeninopid;
	}
	exit 0;
}

sub abort
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $msg = shift;

	&zenlog( $msg ) if $msg;
	&zenlog( "Aborting zeninotify" );

	exit 1;
}

sub leave_zeninotify
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	unlink $zeninopid;
	&zenlog( "Ending zeninotify" );
	exit 0;
}

# read cluster configuration
my $cl_conf = &getZClusterConfig();
&abort( "Could not load cluster configuration" ) if not $cl_conf;

# handle pidfile
&abort( "zeninotify is already running" ) if ( -e $zeninopid );

{
	open my $pidfile, ">", "$zeninopid";
	print $pidfile "$$";
	close $pidfile;
}

$SIG{ HUP }  = \&leave_zeninotify;  # terminate, Hangup
$SIG{ INT }  = \&leave_zeninotify;  # "interrupt", interactive attention request
$SIG{ TERM } = \&leave_zeninotify;  # termination request

#### target files/directories to watch for changes ####3
my @ino_targets = ( $configdir, $rttables );
my $localconfig = &getGlobalConfiguration( 'localconfig' );

&zenlog( "ino_target:$_" ) for @ino_targets;

for my $subdir ( &getSubdirectories( $configdir ) )
{
	next if ( $localconfig eq $subdir );
	&zenlog( "Watching directory $subdir" );
	push ( @ino_targets, $subdir );
}

#### First zeninotify replication ####
&zenlog( "Running the first replication..." );
&runSync( $configdir );
&runSync( $rttables );
&zenlog( "Terminated the first replication..." );

#### Add watchers ####
my $inotify = new Linux::Inotify2();

foreach my $path ( @ino_targets )
{
	&zenlog( "Watching $path" );
	$inotify->watch( $path, IN_CLOSE_WRITE | IN_CREATE | IN_DELETE | IN_MOVED_TO );
}

#### lock
my $lock_ipds = &getGlobalConfiguration( 'lockIpdsPackage' );
my $ipds_dir  = "$configdir/ipds";

# $event->w			The watcher object for this event.
# $event->{w}
# $event->name		The path of the file system object, relative to the watched name.
# $event->{name}
# $event->fullname	Returns the "full" name of the relevant object, i.e. including the name
#					member of the watcher (if the watch object is on a directory and a directory
#					entry is affected), or simply the name member itself when the object is the
#					watch object itself.
# $event->mask		The received event mask.
# $event->{mask}
# $event->IN_xxx	Returns a boolean that returns true if the event mask contains
#					any events specified by the mask. All of the IN_xxx constants
#					can be used as methods.
# $event->cookie
# $event->{cookie}	The event cookie to "synchronize two events". Normally zero,
#					this value is set when two events relating to the same file are generated.
#					As far as I know, this only happens for IN_MOVED_FROM and IN_MOVED_TO events,
#					to identify the old and new name of a file.
#
#/* the following are legal, implemented events that user-space can watch for */
#define IN_ACCESS			0x00000001	/* File was accessed */
#define IN_MODIFY			0x00000002	/* File was modified */
#define IN_ATTRIB			0x00000004	/* Metadata changed */
#define IN_CLOSE_WRITE		0x00000008	/* Writtable file was closed */
#define IN_CLOSE_NOWRITE	0x00000010	/* Unwrittable file closed */
#define IN_OPEN				0x00000020	/* File was opened */
#define IN_MOVED_FROM		0x00000040	/* File was moved from X */
#define IN_MOVED_TO			0x00000080	/* File was moved to Y */
#define IN_CREATE			0x00000100	/* Subfile was created */
#define IN_DELETE			0x00000200	/* Subfile was deleted */
#define IN_DELETE_SELF		0x00000400	/* Self was deleted */
#
#/* the following are legal events.  they are sent as needed to any watch */
#define IN_UNMOUNT			0x00002000	/* Backing fs was unmounted */
#define IN_Q_OVERFLOW		0x00004000	/* Event queued overflowed */
#define IN_IGNORED			0x00008000	/* File was ignored */
#
#/* helper events */
#define IN_CLOSE			(IN_CLOSE_WRITE | IN_CLOSE_NOWRITE) /* close */
#define IN_MOVE				(IN_MOVED_FROM | IN_MOVED_TO) /* moves */
#
#/* special flags */
#define IN_ISDIR			0x40000000	/* event occurred against dir */
#define IN_ONESHOT			0x80000000	/* only send event once */
#
# using:
# IN_CLOSE_WRITE	0x00000008
# IN_CREATE			0x00000100
# IN_DELETE			0x00000200

while ( 1 )
{
	# By default this will block until something is read
	my @events = $inotify->read();

	if ( scalar ( @events ) == 0 )
	{
		&zenlog( "File descriptor in non-blocking mode or error happened: $!" );
		last;
	}

	for my $event ( @events )
	{
		next if ( $event->name =~ /^\..*/ );    # skip hidden files
		next if ( $event->name =~ /.*\~$/ );    # skip files ending with ~
		next
		  if ( -f $lock_ipds and $event->fullname =~ "$ipds_dir" )
		  ;                                     # ipds package is been updating

		my $event_fullname = $event->fullname;
		my $event_mask = sprintf ( "%#.8x", $event->mask );    # hexadecimal string

		&zenlog( "Event: $event_mask File: '$event_fullname'" );

		# watch new subdirectories
		if ( $event->IN_CREATE )
		{
			if ( -d $event->fullname )
			{
				foreach my $path ( &getSubdirectories( $event_fullname ) )
				{
					&zenlog( "Watching $path" );
					push ( @ino_targets, $path );
					$inotify->watch( $path, IN_CLOSE_WRITE | IN_CREATE | IN_DELETE | IN_MOVED_TO );
				}
				&runSync( $configdir );
			}
			next;
		}

		if ( $event->fullname =~ /^$configdir/ )
		{
			my @excluded_patterns = &getClusterExcludedFiles();

			# run sync if it's not an excluded file
			my $matched;

			# does not sync ipds dir while it is been updating
			push @excluded_patterns, "$ipds_dir" if ( -f $lock_ipds );
			for my $pattern ( @excluded_patterns )
			{
				if ( $event->fullname =~ /$pattern/ or $event->fullname eq $pattern )
				{
					if ( $event->fullname !~ /$configdir\/if.+:.+_conf/ )
					{
						&zenlog( "matched pattern $pattern with $event_fullname" );
						$matched = 1;
						last;
					}
				}
			}
			&runSync( $configdir ) if !$matched;
		}

		if ( $event->fullname =~ /^$rttables/ )
		{
			&runSync( $rttables );
		}
	}

	#~ system("grep RSS /proc/$$/status");
}

sub getSubdirectories
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $dir_path = shift;

	opendir ( my $dir_h, $dir_path );

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

