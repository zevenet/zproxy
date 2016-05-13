#!/usr/bin/perl
###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This library is free software; you can redistribute it and/or modify it
#     under the terms of the GNU Lesser General Public License as published
#     by the Free Software Foundation; either version 2.1 of the License, or
#     (at your option) any later version.
#
#     This library is distributed in the hope that it will be useful, but
#     WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
#     General Public License for more details.
#
#     You should have received a copy of the GNU Lesser General Public License
#     along with this library; if not, write to the Free Software Foundation,
#     Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
###############################################################################

require '/usr/local/zenloadbalancer/config/global.conf';

open STDERR, '>>', "$zenlatlog" or die;
open STDOUT, '>>', "$zenlatlog" or die;

#start service
my $interface = @ARGV[0];
my $vip       = @ARGV[1];

#pre run: if down:
my $date = `date +%y/%m/%d\\ %H-%M-%S`;
chomp ( $date );

#chomp($date);
#print "$date: STARTING UP LATENCY SERVICE\n";
#print "Running prestart commands:";
#my @eject = `$ip_bin addr del $vip\/$nmask dev $rinterface label $rinterface:cluster`;
#print "Running: $ip_bin addr del $vip\/$nmask dev $rinterface label $rinterface:cluster\n";

print "$date Running start commands:\n";

# Get cluster interface name
my $cl_vip;
if ( -e $filecluster )
{
	open my $cluster_fh, '<', "$filecluster";
	while ( <$cluster_fh> )
	{
		if ( $_ =~ /^IPCLUSTER/ )
		{
			my @line = split ( ":", $_ );
			$cl_vip = "$line[2]:$line[3]";
		}
	}
	close $cluster_fh;
}

# Get cluster vip mask
my $nmask;
my @ip_addr_list = `$ip_bin addr list`;
foreach my $line ( @ip_addr_list )
{
	# Example: "inet 192.168.101.16/24 brd 192.168.101.255 scope global eth2"
	if ( $line =~ /$interface$/ )
	{
		my ( undef, $ip_and_mask ) = split ( " ", $line );
		( undef, $nmask ) = split ( "\/", $ip_and_mask );
		chomp ( $nmask );
	}
}

# Add cluster virtual interface to the system
my $ip_cmd = "$ip_bin addr add $vip\/$nmask dev $interface label $cl_vip";
system ( $ip_cmd );
print "Running: $ip_cmd\n";

#if interface vipcl is up then run zininotify service
@ip_addr_list = `$ip_bin addr list`;

if ( grep ( /$cl_vip/, @ip_addr_list ) )
{
	#run zeninotify for syncronization directories

	# Stop zeninotify if already running
	if ( -e $zeninopid )
	{
		open my $zino_fh, "$zeninopid";
		while ( <$zino_fh> )
		{
			$zeninopid = $_;
			chomp ( $zeninopid );
			print "Stoping zeninotify $zeninopid.\n";
			$run = kill 9, $zeninopid;
		}
		close $zino_fh;
	}

	# Start zeninotify
	my @eject = `$zenino &`;
	print "Running Zen inotify syncronization service\n";
	print "$zenino &";

	#@array[2] =~ s/:DOWN//;
	#@array[2] =~ s/:UP//;
	#$line = @array[2];
	#chomp($line);
	#@array[2]="";
	#@array[2] = "$line\:UP\n";

	# Force the first sync
	system (
		"touch $configdir\/sync; rm $configdir\/sync ; cp $rttables $rttables\_sync ; rm $rttables; mv $rttables\_sync $rttables"
	);
}
else
{
	print
	  "Zen inotify is not running because Zen latency is not running over $ifname[6]";

	#@array[2] =~ s/:DOWN//;
	#@array[2] =~ s/:UP//;
	#
	#$line = @array[2];
	#chomp($line);
	#@array[2]="";
	#@array[2] = "$line\:DOWN\n";
}

sleep ( 5 );
exec ( "/etc/init.d/zenloadbalancer startlocal" );
