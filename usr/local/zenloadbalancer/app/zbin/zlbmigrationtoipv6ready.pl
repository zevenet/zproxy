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

# This script migrates interfaces configuration files to IPv6 ready version.
# Only supported for Zevenet Load Balancer Enterprise Edition.

my $configdir="/usr/local/zenloadbalancer/config";

opendir my $config_dh, $configdir
  or die "Error opening $configdir directory: $!";

foreach my $dir_entry ( readdir $config_dh )
{
	# skip any entry that is not an interface configuration file
	next if $dir_entry !~ /^if_(.+)_conf$/;

	my $if_name = $1;
	my $migrated_file;    # boolean
	my $old_filepath = "$configdir/$dir_entry";
	my $new_filepath = "$old_filepath.new";

	# check if the file was already migrated
	open my $input_fh, '<', $old_filepath
	  or warn "Error opening file $old_filepath: $!";
	my @file_content = <$input_fh>;
	close $input_fh;

	if ( @file_content && grep( /^status=(up|down)/, @file_content ) == 0 )
	{
		print "Migrating interface $if_name\n";

		unlink $new_filepath if -f $new_filepath;
		open my $output_fh, '>', $new_filepath;

		foreach my $line ( @file_content )
		{
			#~ print $line;
			chomp $line;
			next if !$line;

			# $dev can be a nic or vlan
			my ( $dev, $vini, $addr, $mask, $status, $gateway ) = split ':', $line;

			# start file with interface status
			print $output_fh "status=$status\n";

			if ( $vini ne '' )
			{
				$dev = "$dev:$vini";
			}

			my $new_line = ( join ';', ( $dev, $addr, $mask, $gateway ) ) . ';';
			print $output_fh "$new_line\n";

			$migrated_file = 1;
		}

		close $output_fh;
	}

	if ( $migrated_file )
	{
		# replace old file for new one
		rename $new_filepath, $old_filepath;
	}
}
