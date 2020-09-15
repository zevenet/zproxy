#!/usr/bin/perl

# Description:
#   Get a list of Zevenet functions without documentation

use strict;
use feature 'say';
use Time::Piece;
use Time::Seconds;
use Graph::Easy;

# Graph::Easy::As_svg;

my $libdir        = "../../usr/share/perl5/Zevenet";
my $exclude_regex = "perl5/Zevenet/(API|Cmd)";
my $mod_regex     = '[\w:]+';

my $graph_file = "/root/z_code.svg";

# 600 seconds is not enough for 136 nodes :(
my $graph_timeout = 6000000;

# if it is 0, it has not nodes limit. This limit is because the function fails printing the graph by timeout
my $graph_nodes = 0;

my @files      = `find $libdir -name "*.pm"`;
my $func_regex = '[\w]+';

my $modules = {};

my $graph = Graph::Easy->new();

my $it = 0;
foreach my $f ( @files )
{
	chomp $f;

	next if ( $f =~ /$exclude_regex/ );

	$it++;
	last if ( $graph_nodes and $it == $graph_nodes );

	open my $fh, '<', $f
	  or do { print "Error, The file '$f' could not be openned\n"; next };

	my $mod = $f;
	$mod =~ s|.*Zevenet|Zevenet|;
	$mod =~ s|/|::|g;
	$mod =~ s|\.pm$||g;

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

	# report
	$graph->add_node( $mod );

	close $fh;
}

foreach my $mod ( keys %{ $modules } )
{
	foreach my $dep ( @{ $modules->{ $mod } } )
	{
		$graph->add_edge( $mod, $dep );
	}
}

say "printing graph '$graph_file'...";

my $num_nodes = scalar keys %{ $modules };
my ( $sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst ) =
  localtime ();
print "Printing $num_nodes nodes, it begins at: $hour:$min:$sec\n";

$graph->timeout( $graph_timeout );

open my $fh, '>', $graph_file;
my $t_ini = localtime;
print $fh $graph->as_svg();
close $fh;

my $t_end = localtime;
my $slap  = $t_end - $t_ini;
say "Done! $num_nodes nodes in $slap seconds";

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

1;
