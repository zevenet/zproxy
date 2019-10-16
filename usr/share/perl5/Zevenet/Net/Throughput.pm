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
use Config::Tiny;

use Zevenet::Netfilter;
use Zevenet::Config;

my $throughput_bin = &getGlobalConfiguration( 'zbindir' ) . "/if_throughput.pl";

#~ my $iptables       = &getGlobalConfiguration( 'iptables' );

my $tmpfile        = "/tmp/if_throughput";
my $in_chain       = "INTHROUGHPUT";
my $out_chain      = "OUTTHROUGHPUT";
my $table          = "mangle";
my $in_hook_chain  = "PREROUTING";
my $out_hook_chain = "POSTROUTING";

# create the chain where the counters are
sub createTHROUChain
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $error;

	#~ # create chain
	#~ if ( &iptSystem( "$iptables -N $in_chain -t $table" ) )
	#~ {
	#~ # if it returned error, clean the chain
	#~ &iptSystem( "$iptables -F $in_chain -t $table" );
	#~ }
	#~ if ( &iptSystem( "$iptables -N $out_chain -t $table" ) )
	#~ {
	#~ # if it returned error, clean the chain
	#~ &iptSystem( "$iptables -F $out_chain -t $table" );
	#~ }

	#~ # link chain
	#~ if ( &iptSystem( "$iptables -C $in_hook_chain -t $table -j $in_chain" ) )
	#~ {
	#~ &iptSystem( "$iptables -A $in_hook_chain -t $table -j $in_chain" );
	#~ }

	#~ if ( &iptSystem( "$iptables -C $out_hook_chain -t $table -j $out_chain" ) )
	#~ {
	#~ &iptSystem( "$iptables -A $out_hook_chain -t $table -j $out_chain" );
	#~ }

	return $error;
}

# remove the chain where the counters are
sub deleteTHROUChain
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	#~ # un link chain
	#~ &iptSystem( "$iptables -D $in_hook_chain -t $table -j $in_chain" );
	#~ &iptSystem( "$iptables -D $out_hook_chain -t $table -j $out_chain" );

	#~ # flush chain
	#~ &iptSystem( "$iptables -F $in_chain -t $table" );
	#~ &iptSystem( "$iptables -F $out_chain -t $table" );

	#~ # remove chain
	#~ &iptSystem( "$iptables -X $in_chain -t $table" );
	#~ &iptSystem( "$iptables -X $out_chain -t $table" );
}

# apply input and output rules
sub startTHROUIface
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	#~ my $iface = shift;
	#~ if ( &iptSystem( "$iptables -C $in_chain -t $table -i $iface" ) )
	#~ {
	#~ &iptSystem( "$iptables -A $in_chain -t $table -i $iface" );
	#~ &iptSystem( "$iptables -A $out_chain -t $table -o $iface" );
	#~ }
}

sub stopTHROUIface
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	#~ my $iface = shift;
	#~ &iptSystem( "$iptables -D $in_chain -t $table -i $iface" );
	#~ &iptSystem( "$iptables -D $out_chain -t $table -o $iface" );
}

sub createTHROUFile
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $fh;
	open ( $fh, '>', $tmpfile );
	close $fh;
}

sub getTHROUPid
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $pid;
	my $cmd = "ps aux |grep $throughput_bin | grep -v grep";

	my @cmd_out = `$cmd`;
	if ( $cmd_out[0] =~ /^\s*[^\s]+\s+(\d+)\s/ ) { $pid = $1; }

	return $pid;
}

sub getTHROUStatus
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $pid = &getTHROUPid();
	my $status = kill ( 0, $pid );

	return $status;
}

sub startTHROUTask
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	return if ( &getGlobalConfiguration( "throughput_enabled" ) ne "true" );

	# create iptables chain
	&createTHROUChain();

	# add UP interfaces
	require Zevenet::Net::Interface;
	foreach my $if_type ( 'nic', 'bond', 'vlan' )
	{
		foreach my $if_ref ( &getInterfaceTypeList( $if_type ) )
		{
			if ( &getInterfaceSystemStatus( $if_ref ) eq 'up' )
			{
				&startTHROUIface( $if_ref->{ name } );
			}
		}
	}

	# create the tmp file
	&createTHROUFile();

	# stop process if it is running
	my $pid = &getTHROUPid();
	if ( $pid ) { kill 9, $pid; }

	# run the process
	require Zevenet::Log;
	my $err = &logAndRunBG( "$throughput_bin" );
	if ( $err )
	{
		&zenlog( "Fail executing $throughput_bin", "error", "monitor" );
	}

	return $err;
}

sub stopTHROUTask
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	# kill the process
	my $pid = &getTHROUPid();
	if ( $pid ) { kill 9, $pid; }

	#~ &zenlog("kill $pid, $throughput_bin" );

	# remove the iptables chain
	&deleteTHROUChain();
}

sub resetTHROUCounter
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	#~ &iptSystem( "$iptables -Z $in_chain -t $table" );
	#~ &iptSystem( "$iptables -Z $out_chain -t $table" );
}

sub saveTHROUCounters
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	# reset file to delete stopped interfaces
	&createTHROUFile();

	my $fh = Config::Tiny->read( $tmpfile );

	my @counters;

	#~ my @ipt_out = `$iptables -vL $in_chain -t $table 2>/dev/null`;
	#~ push @counters, @ipt_out;
	#~ @ipt_out = `$iptables -vL $out_chain -t $table 2>/dev/null`;
	#~ push @counters, @ipt_out;

	my $if;
	my $io;
	foreach my $line ( @counters )
	{
		# pkts bytes target     prot opt in     out     source      destination
		# 903K   69M            all  --  any    any     anywhere    anywhere
		if ( $line !~ /^\s*\d/ ) { next; }

		$line =~ s/\s+/ /g;
		my @params = split ( ' ', $line );

		if    ( $params[4] ne 'any' ) { $if = $params[4]; $io = 'in'; }
		elsif ( $params[5] ne 'any' ) { $if = $params[5]; $io = 'out'; }
		else                          { next; }

		# $fh->{ eth0 }->{ in } = "packets bytes";
		$fh->{ $if }->{ $io } = "$params[0] $params[1]";
	}

	$fh->write( $tmpfile );
}

# return a struct from the tmp file with the throutput of all interfaces
sub getTHROUStruct
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $fh = Config::Tiny->read( $tmpfile );

	return $fh;
}

sub getTHROUStats
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Config;

	my $throughput_file = &getTHROUStruct();
	my $time            = &getGlobalConfiguration( 'throughput_period' );
	my $out;

	foreach my $if ( keys %{ $throughput_file } )
	{
		foreach my $io ( 'in', 'out' )
		{
			my $val = $throughput_file->{ $if }->{ $io };
			my @par = split ( ' ', $val );
			$out->{ $if }->{ $io }->{ 'packets' } = $par[0] / $time;
			$out->{ $if }->{ $io }->{ 'bytes' }   = $par[1] / $time;
		}
	}

	return $out;
}

1;
