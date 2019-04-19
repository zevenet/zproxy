#!/usr/bin/perl

# Description:
#   Get a list of Zevenet functions without documentation

use strict;

my $libdir        = "../../usr/share/perl5/Zevenet";
my $exclude_regex = "perl5/Zevenet/(API|Cmd)";

my @files      = `find $libdir -name "*.pm"`;
my $func_regex = '[\w]+';

foreach my $f ( @files )
{
	chomp $f;

	next if ( $f =~ /$exclude_regex/ );

	open my $fh, '<', $f
	  or do { print "Error, The file '$f' could not be openned\n"; next };

	my @funct = ();
	my $flag  = 0;
	foreach my $line ( <$fh> )
	{
		$flag = 1 if ( $line =~ /^=begin/ );

		if ( $line =~ /^sub ($func_regex)/ )
		{
			push @funct, $1 if ( !$flag );

			$flag = 0;
		}
	}

	# report
	if ( @funct )
	{
		$f =~ s/(\.\.\/)*//;
		print "\n> The file '$f' contains the following functions without doc:\n";
		foreach my $fun ( @funct )
		{
			print "\t$fun\n";
		}
	}

	close $fh;
}

1;
