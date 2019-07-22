#!/usr/bin/perl

use strict;
use Zevenet::Validate;
use Zevenet::Log;
use feature qw( say );
my $eload = 0;

my @main_farm = "
{
        \"farms\": [
                {
                        \"name\": \"NAME\",
                        \"family\": \"FAMILY\",
                        \"virtual-addr\": \"VIP\",
                        \"virtual-ports\": \"VPORTS\",
                        \"source-addr\": \"\",
                        \"mode\": \"LMODE\",
                        \"protocol\": \"PROTO\",
                        \"scheduler\": \"weight\",
                        \"sched-param\": \"none\",
                        \"persistence\": \"PER\",
                        \"persist-ttl\": \"PTTL\",
                        \"helper\": \"HELPER\",
                        \"log\": \"LOG\",
                        \"mark\": \"0x0\",
                        \"priority\": \"1\",
                        \"state\": \"STATUS\",
			\"backends\": [";

my @backend_farm = "
 				{
                                        \"name\": \"BCKNAME\",
                                        \"ip-addr\": \"BEIP\",
                                        \"port\": \"BEPORT\",
                                        \"weight\": \"WEIGHT\",
                                        \"priority\": \"PRIO\",
                                        \"mark\": \"MARK\",
                                        \"est-connlimit\": \"0\",
                                        \"state\": \"STATUS\"
                                },";

my @backend_farm_cp;
my @main_farm_cp;
my @no_backends = "]";

my @end = "
                }
        ]
}";

my $n            = 0;
my $l4_files_dir = "/usr/local/zevenet/config";
my @l4_files;
my $farmname;
opendir ( my $dir, $l4_files_dir );
@l4_files =
  grep ( /^.*_l4xnat.cfg$/, readdir ( $dir ) );
closedir $dir;

my $backend = "0";
foreach my $file ( @l4_files )
{
	my @run = `grep "{" $l4_files_dir/$file`;
	if ( $? != 0 )
	{
		print "\n\nOld format for l4xnat config file $file\n";
		open ( my $fd, '<', "$l4_files_dir/$file" );
		while ( my $row = <$fd> )
		{
			$n++;
			if ( $n == 1 )
			{
				@main_farm_cp = @main_farm;

				#we are in the server config.
				my @server = split ( /;/, $row );

				#my @main_farm =~ s/NAME/@server[0]/;
				for ( @main_farm_cp )
				{
					s/NAME/@server[0]/;
					$farmname = @server[0];
					s/VIP/@server[2]/;
					s/VPORTS/@server[3]/;
					chomp ( @server[8] );
					s/STATUS/@server[8]/;
					if ( @server[9] == "true" )
					{
						s/LOG/input/;
					}
					else
					{
						s/LOG/none/;
					}
					if ( @server[1] =~ /^tcp$|^udp$|^all$/ )
					{
						s/PROTO/@server[1]/;
						s/HELPER/none/;
					}
					else
					{
						if ( @server[1] == "ftp" )
						{
							s/HELPER/ftp/;
							s/PROTO/tcp/;
						}
						if ( @server[1] == "tftp" )
						{
							s/HELPER/tftp/;
							s/PROTO/udp/;
						}
						if ( @server[1] == "sip" )
						{
							s/HELPER/sip/;
							s/PROTO/all/;
						}

					}
					if ( @server[6] == "ip" )
					{
						s/PER/@server[6]/;
						s/PTTL/@server[7]/;
					}
					else
					{
						s/PER/none/;
						s/PTTL/70/;
					}
					if ( @server[4] == "nat" )
					{
						s/LMODE/snat/;
					}
					else
					{
						s/LMODE/dnat/;
					}
					if ( @server[2] =~ m/^(\d\d?\d?)\.(\d\d?\d?)\.(\d\d?\d?)\.(\d\d?\d?)$/ )
					{
						s/FAMILY/ipv4/;
					}
					else
					{
						s/FAMILY/ipv6/;
					}

				}

				#from following line to eof we will find servers
			}
			else
			{
				#next line:
				my @server = split ( /;/, $row );
				@backend_farm_cp = @backend_farm;
				for ( @backend_farm_cp )
				{
					$backend++;
					s/BCKNAME/bck${backend}/;
					s/BEIP/@server[2]/;
					s/BEPORT/@server[3]/;
					s/WEIGHT/@server[5]/;
					s/PRIO/@server[6]/;
					s/MARK/@server[4]/;
					s/STATUS/@server[7]/;
				}
				push ( @main_farm_cp, @backend_farm_cp );
			}

		}
		close $fd;
		if ( $n eq "1" )
		{
			push ( @main_farm_cp, @no_backends );

		}
		else
		{
			chop ( $main_farm_cp[-1] );
			push ( @main_farm_cp, "\n\t\t\t]" );
		}
		$n = 0;
		print "OUTPUT CONFIG FILE FOR nftlb:\n";
		push ( @main_farm_cp, @end );
		print @main_farm_cp;
		print "file generation: /tmp/${farmname}_l4xnat.cfg\n";

		#create file and add content
		open ( my $fd, '>', '/tmp/' . ${ farmname } . '_l4xnat.cfg' );
		print $fd "@main_farm_cp";
		close $fd;
		print "cp $l4_files_dir/$file /tmp/bck_${farmname}_l4xnat.cfg\n";
		my @run = `cp $l4_files_dir/$file /tmp/bck_${farmname}_l4xnat.cfg`;
		sleep 1;
		print "cp /tmp/${farmname}_l4xnat.cfg $l4_files_dir\n";
		my @run = `cp /tmp/${farmname}_l4xnat.cfg $l4_files_dir/`;
		sleep 1;

	}

}
