#!/usr/bin/perl

# This script is for a bugfix moving http services, where the tag '#ZWACL-END' was deleted

use strict;
use Tie::File;

my $dir = '/usr/local/zevenet/config';

foreach my $i ( `ls $dir/*_pound.cfg` )
{
	chomp $i;

	if ( system ( "egrep '\s*#ZWACL-END' $i >/dev/null 2>&1" ) )
	{
		&addline( $i );
	}
}

sub addline
{
	my $file_name = shift;

	return if ( !-f $file_name );
	print "Adding tag to $file_name\n";

	tie my @file, 'Tie::File', $file_name;
	my $flag;

	for ( my $it = -1 ; $file[$it] !~ /^\s*User/ and !$flag ; $it-- )
	{
		if ( $file[$it] =~ /^\s*End/ )
		{
			$flag = 1;
			$file[$it] = "\t#ZWACL-END\nEnd";
		}
	}

	untie @file;
}

exit 0;
