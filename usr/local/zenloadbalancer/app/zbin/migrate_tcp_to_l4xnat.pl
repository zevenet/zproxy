#!/usr/bin/perl 

use strict;
use Tie::File;

my $dir = "/usr/local/zenloadbalancer/config";

# get TCP files
my @files = `ls $dir | egrep '.*_pen.cfg\$'`;
# remove TCP config file extension
@files = grep ( s/(.+)_pen.cfg/$1/, @files);

foreach my $farm ( @files )
{
	chomp ($farm);
	print( "'${dir}/${farm}_l4xnat.cfg'\n");	
	if ( ! -f "${dir}/${farm}_l4xnat.cfg" )	
	{
		#open l4xnat file
		tie my @l4file, 'Tie::File', "${dir}/${farm}_l4xnat.cfg";
		#open TCP file
		tie my @tcpfile, 'Tie::File', "${dir}/${farm}_pen.cfg";

		my $vip;
		my $vport;
		my $algorithm;
		my $l4_persistence;
		my $l4_timeout;
		my $l4_status;

		# Get config parameters
		# get algorithm
		$algorithm = "weight";
		if ( grep ( /^prio/, @tcpfile ) )
		{
			$algorithm = "prio";
		}
		
		my @l4_backends;
		# get backends
		foreach my  $tcpline ( @tcpfile )
		{
			#tcp
			# server 6 acl 0 address 0.0.0.0 port 0 max 0 hard 0 prio 0
			if ( $tcpline =~ /server \d+ acl 0 address 0.0.0.0 port 0 max 0 hard 0/ )
			{
				next;
			}
			if ( $tcpline =~ /server (\d+) acl (\d+) address (\d+\.\d+\.\d+\.\d+) port (\d+) max (\d+) hard (\d+) prio (\d+)/ )
			{
				my $id=$1;
				my $acl=$2;
				my $ip=$3;
				my $port=$4;
				my $maxconns=$5;
				my $weight=$6;
				my $priority=$7;		

				my $status="up";
				my $status="maintenance" if ( $acl==9 );

				# l4
				#	;server;192.168.0.168;80;0x209;1;1;up
				my $mark=&getNewMark ( $farm );
				my $l4_back = ";server;$ip;$port;$mark;$weight;$priority;$status";
				push @l4_backends, $l4_back;
			}
		}
		
		# pen -S 10 -c 2049 -x 257 -F '/usr/local/zenloadbalancer/config/tcpfarm_pen.cfg' -C 127.0.0.1:16802 192.168.100.249:41
		print ">$tcpfile[1]\n";
		if ( $tcpfile[1] =~ /^# pen .+ (\d+\.\d+\.\d+\.\d+):(\d+)$/)
		{
			$vip=$1;
			$vport=$2;
		}
		else
		{
			untie @tcpfile;
			untie @l4file;
			print "Error matching.\n";
			exit 1;
		}
		
		$l4_status="up";
		$l4_status="down" if ( grep ( /^\#down/, @tcpfile ) );
		
		
		$l4_persistence="";
		$l4_persistence="ip" if ( grep ( /^no roundrobin/, @tcpfile ) );
		
		$l4_timeout=120;
		
		# save config parameter in l4 format
		#l4farm;tcp;192.168.100.102;70;nat;weight;none;125;up
		$l4file[0] = "$farm;tcp;$vip;$vport;nat;$algorithm;$l4_persistence;$l4_timeout;$l4_status";
		
		# save backends
		push @l4file, @l4_backends;			
	
		# close l4xnat file
		untie @l4file;
		# close tcp file
		untie @tcpfile;
		# it is copied and remove the old TCP farm	
		unlink "$dir/${farm}_pen.cfg"; 
	}
	
	else 
	{
		my $errormsg = "Error migrating TCP farm $farm because already exists a L4xNAT farm with this name.";
		print "$errormsg\n";
		system ( "logger -i migrate $errormsg" );
	}
	
}


#
sub getNewMark    # ($farm_name)
{
	my $farm_name = shift;

	my $found;
	my $marknum = 0x200;
	my $fwmarksconf = "/usr/local/zenloadbalancer/config/fwmarks.conf";

	tie my @contents, 'Tie::File', "$fwmarksconf";

	for my $i ( 512 .. 1023 )
	{
		# end loop if found
		last if defined $found;

		my $num = sprintf ( "0x%x", $i );
		if ( !grep { /^$num/x } @contents )
		{
			$found   = 'true';
			$marknum = $num;
		}
	}

	untie @contents;

	if ( $found eq 'true' )
	{
		open ( my $marksfile, '>>', "$fwmarksconf" );
		print $marksfile "$marknum // FARM\_$farm_name\_\n";
		close $marksfile;
	}

	return $marknum;
}






