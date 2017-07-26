#!/usr/bin/perl 
###############################################################################
#
#    Zevenet Software License
#    This file is part of the Zevenet Load Balancer software package.
#
#    Copyright (C) 2014-today ZEVENET SL, Sevilla (Spain)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

use strict;
use Tie::File;

my $dir = "/usr/local/zevenet/config";
my $backup_dir = "/opt/farm_tcp";

# get TCP files
my @files = `ls $dir | egrep '.*_pen.cfg\$'`;
# remove TCP config file extension
@files = grep ( s/(.+)_pen.cfg/$1/, @files);

mkdir $backup_dir if( ! -d $backup_dir );

foreach my $farm ( @files )
{
	chomp $farm;
	# the original config file is copied
	system ("cp ${dir}/${farm}_pen.cfg ${backup_dir}/${farm}_pen.cfg");
	
	chomp ($farm);
	print( "Migrating farm \"${farm}\" to l4xnat profile\n");	
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
			#server 0 acl 0 address 192.168.100.254 port 22 max 0 hard 0
			if ( $tcpline =~ /server \d+ acl 0 address 0.0.0.0 port 0 max 0 hard 0/ )
			{
				next;
			}
			#server 0 acl 0 address 192.168.100.254 port 22 max 0 hard 0
			if ( $tcpline =~ /server (\d+) acl (\d+) address (\d+\.\d+\.\d+\.\d+) port (\d+) max (\d+) hard (\d+)/ )
			{
				my $id=$1;
				my $acl=$2;
				my $ip=$3;
				my $port=$4;
				my $maxconns=$5;
				
				my $weight="1";
				$weight = $1 if ( $tcpline =~ /weight (\d+)/);
				
				my $priority="1";
				$priority = $1 if ( $tcpline =~ /prio (\d+)/);
				
				my $status="up";
				$status="maintenance" if ( $acl==9 );

				# l4
				#	;server;192.168.0.168;80;0x209;1;1;up
				my $mark=&getNewMark ( $farm );
				my $l4_back = ";server;$ip;$port;$mark;$weight;$priority;$status";
				push @l4_backends, $l4_back;
			}
		}
		
		# pen -S 10 -c 2049 -x 257 -F '/usr/local/zevenet/config/tcpfarm_pen.cfg' -C 127.0.0.1:16802 192.168.100.249:41
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
		
		
		$l4_persistence="ip";
		$l4_persistence="none" if ( grep ( /^roundrobin/, @tcpfile ) );
		
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
		
		unlink "${dir}/${farm}_pen.cfg";
		
		# create a farmguardian service if it is not exist or if it is stopped
		my $farmguardian_file = "${dir}/${farm}_guardian.conf";
		if ( ! -f "$farmguardian_file" )
		{
			system ( "echo '${farm}:::5:::check_tcp -H HOST -p PORT -t 5:::true:::false' > $farmguardian_file" );
		}
		else
		{
			my @farmguardianConf = `cat $farmguardian_file`;
			# check farm guardian
			if ( $farmguardianConf[0] =~ /.+:::.+:::.+:::.+:::.+/ )
			{
				my @fgParams = split ( ':::', $farmguardianConf[0] );
				my $fgtime = $fgParams[1];
				my $fgcmd = $fgParams[2];
				my $fgstatus = $fgParams[3];
				my $fglogs = $fgParams[4];
				
				if ( $fgstatus ne "true" )
				{
					$fgstatus = "true";
				}
				system ( "echo '${farm}:::${fgtime}:::${fgcmd}:::${fgstatus}:::$fglogs' > $farmguardian_file" );
				
			}
			# no correct farmguardian. Put a default farmguardian
			else
			{
				system ( "echo '${farm}:::5:::check_tcp -H HOST -p PORT -t 5:::true:::false' > $farmguardian_file" );
			}
		}
		
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
	my $fwmarksconf = "/usr/local/zevenet/config/fwmarks.conf";

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
