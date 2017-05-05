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

#this script migrates configuration files from v3.02 to v3.03
#only supported for Zen Load Balancer Enterprise Edition.

print
  "This script modifies the configuration files from ZEN Load Balancer Enterprise Edition beyond v3.02...\n";
### migrate http and https configuration files
@httpfarms = `ls /usr/local/zenloadbalancer/config/*_pound.cfg 2> /dev/null`;
foreach $file ( @httpfarms )
{

	chomp ( $file );
	use Tie::File;
	tie @filelines, 'Tie::File', "$file";
	if ( !grep ( /^ConnTO/, @filelines ) )
	{
		print "farm file $file (connection params) needs to be migrated...\n";
		splice @filelines, 14, 0, "ConnTO\t\t20";
		print "param migrated\n";

	}

	if ( !grep ( /\tRewriteLocation/, @filelines ) )
	{
		print "farm file $file (rewrite params) needs to be migrated...\n";
		splice @filelines, 31, 0, "\tRewriteLocation 0";
		print "param migrated\n";
	}

	untie $filelines;

}

### migrate l4 configuration files
my @l4farms = `ls /usr/local/zenloadbalancer/config/*_l4txnat.cfg 2> /dev/null`;
foreach $file ( @l4farms )
{
	chomp ( $file );
	use Tie::File;
	tie @filelines, 'Tie::File', "$file";
	print "farm file $file needs to be migrated...\n";
	my $line = @filelines[0];
	my @args = split ( "\;", $line );
	my $line =
	  "@args[0]\;tcp\;@args[1]\;@args[2]\;@args[3]\;@args[4]\;@args[5]\;@args[6]\;@args[7]";
	@filelines[0] = $line;
	print "file migrated\n";
	untie $file;
	$oldfile = $file;
	$file =~ s/_l4txnat.cfg/_l4xnat.cfg/;
	rename $oldfile, $file;
}
my @l4farms = `ls /usr/local/zenloadbalancer/config/*_l4uxnat.cfg 2> /dev/null`;
foreach $file ( @l4farms )
{
	chomp ( $file );
	use Tie::File;
	tie @filelines, 'Tie::File', "$file";
	print "farm file $file needs to be migrated...\n";
	my $line = @filelines[0];
	my @args = split ( "\;", $line );
	my $line =
	  "@args[0]\;udp\;@args[1]\;@args[2]\;@args[3]\;@args[4]\;@args[5]\;@args[6]\;@args[7]";
	@filelines[0] = $line;
	print "file migrated\n";
	untie $file;
	$oldfile = $file;
	$file =~ s/_l4uxnat.cfg/_l4xnat.cfg/;
	rename $oldfile, $file;
}

### migrate cluster
$clfile = "/usr/local/zenloadbalancer/config/cluster.conf";
if ( -e $clfile )
{

	use Tie::File;
	tie @filelines, 'Tie::File', "$clfile";
	if ( !grep ( /^DEADRATIO/, @filelines ) )
	{
		print "Cluster file $clfile needs to be migrated...\n";
		push ( @filelines, "DEADRATIO:2" );
		print "Cluster file migrated\n";
	}

	untie $clfile;
}

