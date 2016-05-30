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
require "/usr/local/zenloadbalancer/www/functions_ext.cgi";

#start service
my $interface = $ARGV[0];
my $vip       = $ARGV[1];

#pre run: if down:
my $date = `date +%y/%m/%d\\ %H-%M-%S`;
chomp ( $date );

&zenlog( "$date Running start commands:" );

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

# Remove cluster virtual interface from the system
my $ip_cmd = "$ip_bin addr del $vip\/$nmask dev $interface label $cl_vip";

system ( $ip_cmd );

if ( -e $zeninopid )
{
	open my $zino_fh, "<", "$zeninopid";
	my @inopid = <$zino_fh>;
	chomp ( @inopid );
	&zenlog( "Stopping zeninotify with pid @inopid" );
	close $zino_fh;
	kill ( 9, @inopid );
	unlink ( $zeninopid );
}

sleep ( 5 );
exec ( "/etc/init.d/zenloadbalancer stoplocal" );
