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

use Zevenet::Core;
include 'Zevenet::IPDS::WAF::Core';

=begin nd
Function: initWAFModule

	Create configuration files and run all needed commands requested to WAF module

Parameters:
	None - .

Returns:
	None - .

=cut

sub initWAFModule
{
	use File::Path qw(make_path);

	my $touch     = &getGlobalConfiguration( "touch" );
	my $wafSetDir = &getWAFSetDir();
	my $wafConf   = &getWAFFile();

	make_path( $wafSetDir )         if ( !-d $wafSetDir );
	make_path( $deleted_rules )     if ( !-d $wafSetDir );
	&logAndRun( "$touch $wafConf" ) if ( !-f $wafConf );
	if ( !-f $wafConf ) { &createFile( $path ); }
}

my $preload_sets = "/usr/local/zevenet/config/ipds/waf/preload_sets.conf";

sub listWAFSetPreload { }

#??? ??
sub addWAFSetPreload { }
sub delWAFSetPreload { }

#~ eliminar set del paquete:
#~ - si no se esta usando
#~ - directiva en fichero conf que no coincida con share

#~ añadir set del paquete:
#~ - añadir configuracion

#~ modificar set del paquete:

sub migrateWAF
{
	my $pkg_dir = "/usr/local/zevenet/share/waf";
	my $err     = 0;

	use File::Copy qw(copy);

	# deleting deprecated sets
	foreach my $set ( &listWAFSetPreload() )
	{
		# do not to delete it if it is in the package
		next if ( grep ( "^$pkg_dir/${set}\.conf$", ) );

		# Delete it only if it is not used by any farm
		next if ( &listWAFBySet( $set ) );

		# delete it
		$err = &deleteWAFSet( $set );

# delete it from the register log. Only add and delete entries in Preload file the migration process
		$err = &delWAFSetPreload( $set );

		&zenlog( "The WAF set $setname has been deleted properly", 'info', 'waf' );
	}
	return $err if $err;

	# add and modify the sets
	foreach my $pre_set ( &getWAFSetPreload() )
	{
		# get data of the test
		my $setname = "";
		if ( $setname =~ /([\w-]+).conf$/ )
		{
			$setname = $1;
		}
		else
		{
			&zenlog( "Set name does not correct", "debug", "WAF" );
			next;
		}

		my $set_file = &getWAFSetFile( $setname );

		# load the current set
		my $cur_set;
		$cur_set = &getWAFSet( $setname ) if ( -f $set_file );

		# copy template to the config directory, overwritting the set
		copy $pre_set, $set_file;

		# if set already exists, migrate the configuration
		if ( defined $cur_set )
		{
			# open the new created set
			$new_set = &getWAFSet( $setname );

			# delete the deleted rules
			??
			  ? ??

			  # add the configuration
			  $new_set->{ configuration } = $cur_set->{ configuration };

			# add the rules are been created by de user and move it of position
			my $ind   = 0;
			my @rules = @{ $cur_set->{ rules } };
			foreach my $rule ( @rules )
			{
				if ( $rule->{ modified } eq 'yes' )
				{
					push @{ $new_set->{ rules } }, $rule;
					&moveByIndex( $new_set->{ rules }, $#rules, $ind );
				}
				$ind++;
			}

			# save set
			$err = &buildWAFSet( $new_set );

			&zenlog( "The WAF set $setname has been updated properly", 'info', 'waf' );
		}
		else
		{
			# log the new set in the register to know is a preloaded set
			$err = &addWAFSetPreload( $set );
			&zenlog( "The WAF set $setname has been created properly", 'info', 'waf' );
		}
	}

	return $err;

	# ???? controlar;
}

sub getWAFSetPreload
{
	opendir my $dir, $preload_path;
	my @files = readdir $dir;
	closedir $dir

	  return @files;
}

1;
