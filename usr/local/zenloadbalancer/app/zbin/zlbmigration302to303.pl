#!/usr/bin/perl
###############################################################################
#
#     This file is part of the Zen Load Balancer Enterprise Edition software
#     package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This file cannot be distributed, released in public domain and/or for
#     commercial purposes.
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

