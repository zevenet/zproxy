#!/usr/bin/perl

use Fcntl ':flock';

use Zevenet::Core;
include 'Zevenet::IPDS::Blacklist';
include 'Zevenet::IPDS::Base';

&runIPDSStopModule();


#lock iptables
my $iptlock = "/tmp/iptables.lock";
my $open_rc = open ( my $ipt_lockfile, ">", $iptlock );
my $program = 'migrate_ipds_to_51: ';

if ( $open_rc )
{
	flock ( $ipt_lockfile, LOCK_EX )
}
else
{
	print( $program . "Cannot open $iptlock: $!" );
}

my @setbox = (
			   { chain => "PREROUTING", table => "raw" },
			   { chain => "PREROUTING", table => "mangle" },
			   { chain => "INPUT",      table => "filter" },
			   { chain => "FORWARDING", table => "filter" },
);

foreach my $point ( @setbox )
{
	my $chain=$point->{ chain };
	my $table=$point->{ table };

	my @rules	= `iptables -L $chain -t $table --line-numbers 2>/dev/null`;
	chomp (@rules);
	my $size	= scalar @rules;

	# clean iptables rules
	for ( ; $size >= 0 ; $size-- )
	{
		if ( $rules[$size] =~ /^(\d+) .* (BL|DOS)[,_]/ )
		{
			my $lineNum = $1;
			#	iptables -D PREROUTING -t raw 3
			my $out = system( "iptables --table $table -D $chain $lineNum" );
		}
	}
}

## unlock iptables use ##
if ( $open_rc )
{
	flock ( $ipt_lockfile, LOCK_UN );
	close $ipt_lockfile;
}

# remove ipset
my @ipsets = `ipset list --name`;
chomp (@ipsets);
foreach my $set ( @ipsets )
{
	system("ipset destroy $set");
}

&runIPDSStartModule();

exit 0;
