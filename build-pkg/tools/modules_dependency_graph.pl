#!/usr/bin/perl

# Description:
#   Get a list of Zevenet functions without documentation

use strict;
use feature 'say';
use Time::Piece;
use Time::Seconds;
use Graph::Easy;
use Data::Dumper;

# Graph::Easy::As_svg;

my $libdir        = "../../usr/share/perl5/Zevenet";
my $moddir        = "../../usr/share/perl5";
my $exclude_regex = "perl5/Zevenet/(API|Cmd)";
my $mod_regex     = '[\w:]+';
my $output_format = "svg";

my $graph_file = "/root/z_code.svg";

# 136 nodes (modules) take 1962 seconds :(
my $graph_timeout = 6000000;

# if it is 0, it has not nodes limit. This limit is because the function fails printing the graph by timeout
my $graph_nodes = 0;

my $func_regex = '[\w]+';

my $modules = {};

if ( grep /^-?-h(elp)$/, @ARGV )
{
	print "$0 options:
	-h,--help  this help
	-m [module_name],  module name to get its dependencies recursively
	-o [output_path],  graph output file. 'STDOUT' is used to print in stdout.
	-n [graph_nodes],  number of nodes, modules iterations. Only when -m parameter is not used
	-t [graph_timeout],  timeout to print the graph
	-f [output_format],  output graph format: svg (it is the default one, but it requires the perl module 'Graph::Easy::As_svg') or ascii
	";
	exit 0;
}

my $mod;
my $size = scalar @ARGV;
for ( my $it = 0 ; $it < $size ; $it++ )
{
	if ( $ARGV[$it] eq '-m' )
	{
		$it++;
		$mod = $ARGV[$it];
	}
	if ( $ARGV[$it] eq '-o' )
	{
		$it++;
		$graph_file = $ARGV[$it];
	}
	if ( $ARGV[$it] eq '-n' )
	{
		$it++;
		$graph_nodes = $ARGV[$it];
	}
	if ( $ARGV[$it] eq '-t' )
	{
		$it++;
		$graph_timeout = $ARGV[$it];
	}
	if ( $ARGV[$it] eq '-f' )
	{
		$it++;
		$output_format = $ARGV[$it];
	}
}

if ( $output_format ne 'ascii' and $graph_file eq 'STDOUT' )
{
	say "Error! SVG cannot be printed in STDOUT.";
	exit 1;
}

my $graph = Graph::Easy->new();

# get all dependencies for all modules
if ( !defined $mod )
{
	my @files = `find $libdir -name "*.pm"`;

	my $it = 0;
	foreach my $f ( @files )
	{
		chomp $f;

		#	next if ( $f =~ /$exclude_regex/ );

		&getDepsByFile( $f );

		$it++;
		last if ( $graph_nodes and $it == $graph_nodes );
	}
}

# get dependencies from a module
else
{
	my $usedMod = [];
	&getDepsByModule( $mod, $usedMod );
}

&printGraph();

### functions

# it gets the module name and returns the file name
sub getModuleFile
{
	my $mod = shift;

	$mod =~ s|::|/|g;
	$mod = $moddir . '/' . $mod . ".pm";

	return $mod;
}

# it gets the file name and returns the module name
sub getModuleName
{
	my $mod = shift;
	$mod =~ s|.*Zevenet|Zevenet|;
	$mod =~ s|/|::|g;
	$mod =~ s|\.pm$||g;

	return $mod;
}

# it usees the getDepsByFile function to iterate
sub getDepsByModule
{
	my $mod = shift;

	# avoid ciclying bucles:
	my $gotMod = shift;

	# get file name
	my $file = &getModuleFile( $mod );

	return () if !-f $file;    # do not iterate for system modules

	my $includes = &getDepsByFile( $file );

	foreach my $module ( @{ $includes } )
	{
		next if ( grep ( /^$module$/, @{ $gotMod } ) );
		push @{ $gotMod }, $module;
		next if ( $module !~ /^Zevenet::/ );

		&getDepsByModule( $module, $gotMod );
	}

	return @{ $includes };
}

sub getDepsByFile
{
	my $f = shift;

	open my $fh, '<', $f
	  or do { print "Error, The file '$f' could not be openned\n"; next };

	my $mod = &getModuleName( $f );

	my @includes;
	my $eload_flag = 0;
	foreach my $line ( <$fh> )
	{
		if ( $line =~ /^\s*(?:include|use|require)\s+['"]?($mod_regex)['"]?/ )
		{
			push @includes, $1;
		}
		elsif ( $line =~ /module\s*=>\s*['"]($mod_regex)['"]/ and $eload_flag )
		{
			push @includes, $1;
			$eload_flag = 0;
		}
		elsif ( $line =~ /&eload/ )
		{
			$eload_flag = 1;
		}
	}

	@includes = &uniq( \@includes );
	@includes = grep ( !/(?:feature|strict|warnings)/, @includes );

	$modules->{ $mod } = \@includes;

	# Difference between system and zevenet modules
	#~ my @sys = grep ( !/^Zevenet::/, @includes );
	#~ my @zev = grep ( /^Zevenet::/,  @includes );

	close $fh;

	return \@includes;
}

sub uniq
{
	my $list = shift;
	my %seen = ();
	foreach my $item ( @{ $list } )
	{
		$seen{ $item } = 1;
	}

	return keys %seen;
}

sub printGraph
{
	my @nodes = ();

	foreach my $mod ( keys %{ $modules } )
	{
		if ( !grep ( /^$mod$/, @nodes ) )
		{
			$graph->add_node( $mod );
			push @nodes, $mod;
		}

		foreach my $dep ( @{ $modules->{ $mod } } )
		{
			if ( !grep ( /^$dep$/, @nodes ) )
			{
				$graph->add_node( $dep );
				push @nodes, $dep;
			}

			$graph->add_edge( $mod, $dep );
		}
	}

	say "printing graph '$graph_file'...";

	my $num_nodes = scalar keys %{ $modules };
	my ( $sec, $min, $hour ) = localtime ();
	print "Printing $num_nodes nodes, it begins at: $hour:$min:$sec\n";

	$graph->timeout( $graph_timeout );

	my $fh;
	if ( $graph_file ne 'STDOUT' )
	{
		open $fh, '>', $graph_file;
	}
	else
	{
		$fh = *STDOUT;
	}

	my $t_ini = localtime;
	if ( $output_format eq 'ascii' )
	{
		print $fh $graph->as_ascii();
	}
	else
	{
		print $fh $graph->as_svg();
	}

	close $fh if ( $graph_file ne 'STDOUT' );

	my $t_end = localtime;
	my $slap  = $t_end - $t_ini;
	say "Done! $num_nodes nodes in $slap seconds";
}

1;
