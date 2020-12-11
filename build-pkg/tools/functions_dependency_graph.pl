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

my @skip_funct = ( '1', 'zenlog', 'getGlobalConfiguration', 'debug' );

my $libdir        = "../../usr/share/perl5/Zevenet";
my $moddir        = "../../usr/share/perl5";
my $exclude_regex = "perl5/Zevenet/(API|Cmd)";
my $mod_regex     = '[\w:]+';
my $output_format = "svg";

my $graph_file = "/root/funct_depend";

# 136 nodes (modules) take 1962 seconds :(
my $graph_timeout = 6000000;

# if it is 0, it has not nodes limit. This limit is because the function fails printing the graph by timeout
my $graph_nodes = 0;

# maximun number of iterations
my $deep_search = 50;

my $func_regex = '[\w]+';

my $tree = {};

if ( grep /^-?-h(elp)$/, @ARGV )
{
	&printHelp();
}

my $size = scalar @ARGV;
for ( my $it = 0 ; $it < $size ; $it++ )
{
	if ( $ARGV[$it] eq '-d' )
	{
		$it++;
		$deep_search = $ARGV[$it];
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
		if ( !grep ( /^$output_format$/, ( 'ascii', 'svg', 'tree' ) ) )
		{
			say "Error, the output format is not valid";
			&printHelp;
		}
	}
}

my $input_funct = $ARGV[-1];

if ( !$input_funct )
{
	say "Error! A function is required.";
	&printHelp;
	exit 1;
}

if ( $output_format eq 'svg' and $graph_file eq 'STDOUT' )
{
	say "Error! SVG cannot be printed in STDOUT.";
	exit 1;
}

if ( $graph_file ne 'STDOUT' )
{
	$graph_file .= ".$output_format";
}

my $graph = Graph::Easy->new();

# build the tree
$tree = &getFunctionDeps( $input_funct, $deep_search );

&printGraph();

### functions
sub printHelp
{
	print "Usage: $0 [options] <funct_name>
	-h,--help,  this help
	-d [deep],  deep of the search. It finishes the searches if the deep value is reached.
	-o [output_path],  graph output file. 'STDOUT' is used to print in stdout.
	-n [graph_nodes],  number of nodes, modules iterations. Only when -m parameter is not used
	-t [graph_timeout],  timeout to print the graph
	-f [output_format],  output graph format: 'svg' (it is the default one, but it requires the perl module 'Graph::Easy::As_svg'),  'ascii' or 'tree'.

	";
	exit 0;
}

sub getFunctionModule
{
	my $func = shift;

	my @file = `grep -R 'sub $func' $libdir`;

	my @f = split ( ':', $file[0] );

	return $f[0];
}

sub getFunctionCalls
{
	my ( $file, $funct ) = @_;

	my @calls = ();
	my $flag  = 0;
	my $tab   = 0;
	open ( my $fh, '<', $file );
	foreach my $l ( <$fh> )
	{
		if ( $flag )
		{
			if ( $l =~ /^\s*\{/ )
			{
				$tab++;
			}
			elsif ( $l =~ /^\s*\}/ )
			{
				$tab--;
				last if ( $tab == 0 );    # end
			}
			elsif ( $l =~ /\&($func_regex)/ )
			{
				my $f = $1;
				if ( !grep ( /^$f$/, @skip_funct ) )
				{
					if ( !grep ( /^$f$/, @calls ) )
					{
						push @calls, $f;
					}
				}
			}
		}
		elsif ( $l =~ /^\s*sub\s+$funct\b/ )
		{
			$flag = 1;
		}
	}
	close $fh;

	return \@calls;
}

sub getFunctionDeps
{
	my $func       = shift;
	my $deep       = shift;
	my $local_deps = undef;

	# end
	if ( !$deep )
	{
		print "Warning! The deep parameter ($deep_search) was reached\n";
		return undef;
	}
	$deep--;

	my $file = &getFunctionModule( $func );

	my $deps_list = &getFunctionCalls( $file, $func );
	return undef if ( !@$deps_list );    # no more depencies

	foreach my $f ( @$deps_list )
	{
		$local_deps->{ $f } = &getFunctionDeps( $f, $deep );
	}

	return $local_deps;
}

sub printGraph
{
	my @nodes = ();

	# print the struct
	if ( $output_format eq 'tree' )
	{
		print Dumper $tree;
		return;
	}

	# draw and print the scheme
	foreach my $funct ( keys %{ $tree } )
	{
		if ( !grep ( /^$funct$/, @nodes ) )
		{
			$graph->add_node( $funct );
			push @nodes, $funct;
		}

		foreach my $dep ( keys %{ $tree->{ $funct } } )
		{
			if ( !grep ( /^$dep$/, @nodes ) )
			{
				$graph->add_node( $dep );
				push @nodes, $dep;
			}

			$graph->add_edge( $funct, $dep );
		}
	}

	say "printing graph '$graph_file'...";

	my $num_nodes = scalar keys %{ $tree };
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
