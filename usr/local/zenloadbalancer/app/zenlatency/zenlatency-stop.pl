#!/usr/bin/perl

use Sys::Hostname;
use Tie::File;
require '/usr/local/zenloadbalancer/config/global.conf';

open STDERR, '>>', "$zenlatlog" or die;
open STDOUT, '>>', "$zenlatlog" or die;



#start service
$interface=@ARGV[0];
$vip=@ARGV[1];

#pre run: if down:
$date=`date +%y/%m/%d\\ %H-%M-%S`;
chomp($date);
#chomp($date);
#print "$date: STARTING UP LATENCY SERVICE\n";
#print "Running prestart commands:";
#my @eject = `$ip_bin addr del $vip\/$nmask dev $rinterface label $rinterface:cluster`;
#print "Running: $ip_bin addr del $vip\/$nmask dev $rinterface label $rinterface:cluster\n";



print "$date Running start commands:\n";
if (-e $filecluster)
	{
	open FR, "$filecluster";
	while(<FR>)
		{
		if ($_ =~ /^IPCLUSTER/)
			{
			@line = split(":",$_);
			$ifname = @line[2].":".@line[3];
			}
		}

	} 
	
my @eject =`$ip_bin addr list`;
foreach $line(@eject)
	{
	if ($line =~ /$interface$/)
		{
		@line = split(" ",$line);
		@nmask = split("\/",@line[1]);	
		$nmask = @nmask[1];
		chomp($nmask);
		}
	}


#my @eject = `$ip_bin addr add $vip\/$nmask dev $rinterface label $rinterface:cluster`;
my @eject = `$ip_bin addr del $vip\/$nmask dev $interface label $ifname`;
#print "Running: $ip_bin addr add $vip\/$nmask dev $rinterface label $rinterface:cluster\n";
print "Running: $ip_bin addr del $vip\/$nmask dev $interface label $ifname\n";




tie @array, 'Tie::File', "$filecluster";
#$line = @array[2];
#chomp($line);
#@array[2] = "$line\:DOWN\n";		

if (-e $zeninopid)
        {
        open FO, "<$zeninopid";
        my @inopid = <FO>;
        chomp(@inopid);
        print "Stopping zeninotify with pid @inopid\n";
        close FO;
        kill(9,@inopid);
        unlink($zeninopid);
        #@array[2] =~ s/:DOWN//;
        #@array[2] =~ s/:UP//;
        #$line = @array[2];
        #chomp($line);
        #@array[2] = "$line\:DOWN\n";
        }
	
untie @array;

sleep(5);
my @eject = `/etc/init.d/zenloadbalancer stoplocal`;
