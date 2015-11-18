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

#
sub loadNfModule    # ($modname,$params)
{
	my ( $modname, $params ) = @_;

	my $status  = 0;
	my @modules = `$lsmod`;

	if ( !grep /^$modname /, @modules )
	{
		my $modprobe_command = "$modprobe $modname $params";

		&logfile( "L4 loadNfModule: $modprobe_command" );
		system ( "$modprobe_command >/dev/null 2>&1" );
		$status = $?;
	}

	return $status;
}

#
sub removeNfModule    # ($modname)
{
	my $modname = shift;

	my $modprobe_command = "$modprobe -r $modname";

	&logfile( "L4 removeNfModule: $modprobe_command" );
	return system ( "$modprobe_command >/dev/null 2>&1" );
}

#
sub getIptFilter      # ($type, $desc, @iptables)
{
	my ( $type, $desc, @iptables ) = @_;

	return grep { / FARM\_$desc\_.* / } @iptables if ( $type eq "farm" );
}

#
sub getIptList        # ($table,$chain)
{
	my ( $table, $chain ) = @_;

	if ( $table ne "" )
	{
		$table = "-t $table";
	}

	my $iptables_command = "$iptables $table -L $chain -n -v --line-numbers";

	&logfile( $iptables_command );

	return `$iptables_command`;
}

#
sub deleteIptRules    # ($type,$desc,$table,$chain,@allrules)
{
	my ( $type, $desc, $table, $chain, @allrules ) = @_;

	my $status = 0;
	my @rules = &getIptFilter( $type, $desc, @allrules );

	# do not change rules id starting by the end
	chomp ( @rules = reverse ( @rules ) );
	foreach $rule ( @rules )
	{
		my @sprule = split ( "\ ", $rule );
		if ( $type eq "farm" )
		{
			my $iptables_command = "$iptables -t $table -D $chain $sprule[0]";

			&logfile( "deleteIptRules:: running '$iptables_command'" );
			system ( "$iptables_command >/dev/null 2>&1" );
			&logfile( "deleteIptRules:: delete netfilter rule '$rule'" );

			$status = $status + $?;
		}
	}

	return $status;
}

#
sub getNewMark    # ($fname)
{
	my ( $fname ) = @_;

	my $found   = "false";
	my $marknum = 0x200;
	my $i;

	tie my @contents, 'Tie::File', "$fwmarksconf";
	for ( $i = 512 ; $i < 1024 && $found eq "false" ; $i++ )
	{
		my $num = sprintf ( "0x%x", $i );
		if ( !grep /^$num/, @contents )
		{
			$found   = "true";
			$marknum = $num;
		}
	}
	untie @contents;

	if ( $found == "true" )
	{
		open ( MARKSFILE, ">>$fwmarksconf" );
		print MARKSFILE "$marknum // FARM\_$fname\_\n";
		close MARKSFILE;
	}

	return $marknum;
}

#
sub delMarks    # ($fname,$mark)
{
	my ( $fname, $mark ) = @_;

	my $status = 0;
	if ( $fname ne "" )
	{
		tie my @contents, 'Tie::File', "$fwmarksconf";
		@contents = grep !/ \/\/ FARM\_$fname\_$/, @contents;
		$status = $?;
		untie @contents;
	}

	if ( $mark ne "" )
	{
		tie my @contents, 'Tie::File', "$fwmarksconf";
		@contents = grep !/^$mark \/\//, @contents;
		$status = $?;
		untie @contents;
	}

	return $status;
}

#
sub renameMarks    # ($fname,$newfname)
{
	my ( $fname, $newfname ) = @_;

	my $status = 0;
	if ( $fname ne "" )
	{
		tie my @contents, 'Tie::File', "$fwmarksconf";
		foreach $line ( @contents )
		{
			$line =~ s/ \/\/ FARM\_$fname\_/ \/\/ FARM\_$newfname\_/;
		}
		$status = $?;
		untie @contents;
	}

	return $status;
}

# genIptMarkReturn is not used
#~ sub genIptMarkReturn    # ($fname,$vip,$vport,$proto,$index)
#~ {
#~ my ( $fname, $vip, $vport, $proto, $index ) = @_;
#~
#~ my $iptables_command =
#~ "$iptables -t mangle -A PREROUTING -d $vip -p $proto -m multiport --dports $vport -j RETURN -m comment --comment ' FARM\_$fname\_$index\_ '";
#~
#~ &logfile( $iptables_command );
#~
#~ return $iptables_command;
#~ }

#
sub genIptMarkPersist    # ($fname,$vip,$vport,$proto,$ttl,$index,$mark)
{
	my ( $fname, $vip, $vport, $proto, $ttl, $index, $mark ) = @_;

	my $layer = "";
	my $iptables_command =
	    "$iptables "
	  . "-t mangle "
	  . "-A PREROUTING "
	  . "-m recent "
	  . "--name \"\_$fname\_$mark\_sessions\" "
	  . "--rcheck "
	  . "--seconds $ttl "
	  . "-d $vip "
	  . "$layer "
	  . "-j MARK "
	  . "--set-mark $mark "
	  . "-m comment "
	  . "--comment ' FARM\_$fname\_$index\_ '";

	if ( $proto ne "all" )
	{
		$layer = "-p $proto -m multiport --dports $vport";
	}

	&logfile( $iptables_command );

	return $iptables_command;
}

#
sub genIptMark    # ($fname,$lbalg,$vip,$vport,$proto,$index,$mark,$value,$prob)
{
	my ( $fname, $lbalg, $vip, $vport, $proto, $index, $mark, $value, $prob ) = @_;

	my $rule;

	my $layer = "";
	if ( $proto ne "all" )
	{
		$layer = "-p $proto -m multiport --dports $vport";
	}

	if ( $lbalg eq "weight" )
	{
		if ( $prob == 0 )
		{
			$prob = $value;
		}
		$prob = $value / $prob;
		$rule =
		    "$iptables "
		  . "-t mangle "
		  . "-A PREROUTING "
		  . "-m statistic "
		  . "--mode random "
		  . "--probability $prob "
		  . "-d $vip $layer "
		  . "-j MARK "
		  . "--set-mark $mark "
		  . "-m comment "
		  . "--comment ' FARM\_$fname\_$index\_ '";
	}

	if ( $lbalg eq "leastconn" )
	{
		$rule =
		    "$iptables "
		  . "-t mangle "
		  . "-A PREROUTING "
		  . "-m condition "
		  . "--condition '\_$fname\_$mark\_' "
		  . "-d $vip $layer "
		  . "-j MARK "
		  . "--set-mark $mark "
		  . "-m comment "
		  . "--comment ' FARM\_$fname\_$index\_ '";
	}

	if ( $lbalg eq "prio" )
	{
		$rule =
		    "$iptables "
		  . "-t mangle "
		  . "-A PREROUTING "
		  . "-d $vip $layer "
		  . "-j MARK "
		  . "--set-mark $mark "
		  . "-m comment "
		  . "--comment ' FARM\_$fname\_$index\_ '";
	}

	&logfile( $rule );

	return $rule;
}

#
sub genIptRedirect    # ($fname,$index,$rip,$proto,$mark,$persist)
{
	my ( $fname, $index, $rip, $proto, $mark, $persist ) = @_;

	my $layer =
	  ( $proto ne "all" )
	  ? "-p $proto"
	  : '';

	$persist =
	  ( $persist ne "none" )
	  ? "-m recent --name \"\_$fname\_$mark\_sessions\" --set"
	  : '';

	my $iptables_command =
	    "$iptables "
	  . "-t nat "
	  . "-A PREROUTING "
	  . "-m mark "
	  . "--mark $mark "
	  . "-j DNAT "
	  . "$layer "
	  . "--to-destination $rip "
	  . "$persist "
	  . "-m comment "
	  . "--comment ' FARM\_$fname\_$index\_ '";

	&logfile( $iptables_command );

	return $iptables_command;
}

#
sub genIptSourceNat    # ($fname,$vip,$index,$proto,$mark)
{
	my ( $fname, $vip, $index, $proto, $mark ) = @_;

	my $layer = "";
	my $iptables_command =
	    "$iptables "
	  . "-t nat "
	  . "-A POSTROUTING "
	  . "-m mark "
	  . "--mark $mark "
	  . "-j SNAT $layer "
	  . "--to-source $vip "
	  . "-m comment "
	  . "--comment ' FARM\_$fname\_$index\_ '";

	if ( $proto ne "all" )
	{
		$layer = "-p $proto";
	}

	&logfile( $iptables_command );

	return $iptables_command;
}

#
sub genIptMasquerade    # ($fname,$index,$proto,$mark)
{
	my ( $fname, $index, $proto, $mark ) = @_;

	my $layer = "";
	my $iptables_command =
	    "$iptables "
	  . "-t nat "
	  . "-A POSTROUTING "
	  . "-m mark "
	  . "--mark $mark "
	  . "-j MASQUERADE $layer "
	  . "-m comment "
	  . "--comment ' FARM\_$fname\_$index\_ '";

	if ( $proto ne "all" )
	{
		$layer = "-p $proto";
	}

	&logfile( $iptables_command );

	return $iptables_command;
}

#
sub getConntrack    # ($orig_src, $orig_dst, $reply_src, $reply_dst, $proto)
{
	( $orig_src, $orig_dst, $reply_src, $reply_dst, $proto ) = @_;

	chomp ( $orig_src );
	chomp ( $orig_dst );
	chomp ( $reply_src );
	chomp ( $reply_dst );
	chomp ( $proto );

	if ( $orig_src )
	{
		$orig_src = "-s $orig_src";
	}
	if ( $orig_dst )
	{
		$orig_dst = "-d $orig_dst";
	}
	if ( $reply_src )
	{
		$reply_src = "-r $reply_src";
	}
	if ( $reply_dst )
	{
		$reply_dst = "-q $reply_dst";
	}
	if ( $proto )
	{
		$proto = "-p $proto";
	}
	&logfile(
		 "$conntrack -L $orig_src $orig_dst $reply_src $reply_dst $proto 2>/dev/null" );

	return
	  `$conntrack -L $orig_src $orig_dst $reply_src $reply_dst $proto 2>/dev/null`;
}

# do not remove this
1
