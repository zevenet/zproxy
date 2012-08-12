#This file config is part of Zen Load Balancer, is a Web GUI integrated with binary systems that
#create Highly Effective Bandwidth Managemen
#Copyright (C) 2010  Emilio Campos Martin / Laura Garcia Liebana
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You can read license.txt file for more information.

#File that create the Zen Load Balancer GUI


# 
sub getIptFilter($type, $desc, @iptables){
	($type,$desc,@iptables) = @_;

	my $output;
	if ($type eq "farm"){
		@output = grep{ / FARM\_$desc\_.* / } @iptables;
	}
	return @output;
}

#
sub getIptList($table,$chain){
	($table,$chain)= @_;

	my $ttable = $table;
	if ($ttable ne ""){
		$ttable = "-t $ttable";
	}
	my @iptables = `$iptables $ttable -L $chain -n -v --line-numbers`;

	return @iptables;
}

#
sub deleteIptRules($type,$desc,$chain,@allrules){
	($type,$desc,@allrules) = @_;

	my $status = 0;
	my @rules = &getIptFilter($type,$desc,@allrules);
	# do not change rules id starting by the end
	@rules = reverse(@rules);
	foreach $rule(@rules){
		my @sprule = split("\ ",$rule);
		if ($type eq "farm"){
			&logfile("deleteIptRules:: running '$iptables -t $table -D $chain @sprule[0]'");
			my @run = `$iptables -t $table -D $chain @sprule[0]`;
			&logfile("deleteIptRules:: delete netfilter rule '$rule'");
			$status = $status + $?;
		}
	}

	return $status;
}

#
sub getNewMark($fname){
	my $found = "false";
	my $marknum = 0x200;
	my $i;
	tie my @contents, 'Tie::File', "$fwmarksconf";
	for ( $i = 512; $i < 1024 && $found eq "false"; $i++ ) {
		my $num = sprintf("0x%x", $i);
		if (! grep /^$num/, @contents) {
			$found = "true";
			$marknum = $num;
		}
	}
	untie @contents;

	if ($found = "true"){
		open(MARKSFILE,">>$fwmarksconf");
		print MARKSFILE "$marknum // FARM\_$fname\_\n";
		close MARKSFILE;
	}

	return $marknum;
}

#
sub delMarks($fname,$mark){
	($fname,$mark) = @_;

	my $status = 0;
	if ($fname ne ""){
		tie my @contents, 'Tie::File', "$fwmarksconf";
		@contents = grep !/ \/\/ FARM\_$fname\_$/, @contents;
		$status = $?;
		untie @contents;
	}

	if ($mark ne ""){
		tie my @contents, 'Tie::File', "$fwmarksconf";
		@contents = grep !/^$mark \/\//, @contents;
		$status = $?;
		untie @contents;
	}

	return $status;
}

#
sub renameMarks($fname,$newfname){
	($fname,$newfname) = @_;

	my $status = 0;
	if ($fname ne ""){
		tie my @contents, 'Tie::File', "$fwmarksconf";
		foreach $line(@contents){
			$line =~ s/ \/\/ FARM\_$fname\_/ \/\/ FARM\_$newfname\_/ ;
		}
		$status = $?;
		untie @contents;
	}

	return $status;
}

#
sub genIptMarkReturn($fname,$vip,$vport,$proto,$index,$state){
	($fname,$vip,$vport,$proto,$index,$state)= @_;

	my $rule;

	if ($state !~ /^up$/){
		return $rule;
	}

	$rule = "$iptables -t mangle -A PREROUTING -d $vip -p $proto -m multiport --dports $vport -j RETURN -m comment --comment ' FARM\_$fname\_$index\_ '";

	return $rule;

}

#
sub genIptMarkPersist($fname,$vip,$vport,$proto,$ttl,$index,$mark,$state){
	($fname,$vip,$vport,$proto,$ttl,$index,$mark,$state)= @_;

	my $rule;

	if ($state !~ /^up$/){
		return $rule;
	}

	$rule = "$iptables -t mangle -A PREROUTING -m recent --name \"\_$fname\_$mark\_\" --rcheck --seconds $ttl -d $vip -p $proto -m multiport --dports $vport -j MARK --set-mark $mark -m comment --comment ' FARM\_$fname\_$index\_ '";

	return $rule;
}

#
sub genIptMark($fname,$nattype,$lbalg,$vip,$vport,$proto,$index,$mark,$weight,$state,$prob){
	($fname,$nattype,$lbalg,$vip,$vport,$proto,$index,$mark,$weight,$state,$prob)= @_;

	my $rule;

	if ($state !~ /^up$/){
		return $rule;
	}

	if ($lbalg eq "weight"){
		if ($prob == 0){
			$prob = $weight;
		}
		$prob = $weight / $prob;
		$rule = "$iptables -t mangle -A PREROUTING -m statistic --mode random --probability $prob -d $vip -p $proto -m multiport --dports $vport -j MARK --set-mark $mark -m comment --comment ' FARM\_$fname\_$index\_ '";
	}

	return $rule;
}

#
sub genIptRedirect($fname,$nattype,$index,$rip,$proto,$mark,$weight,$persist,$state){
	($fname,$nattype,$index,$rip,$proto,$mark,$weight,$persist,$state)= @_;

	my $rule;

	if ($state !~ /^up$/){
		return $rule;
	}

	if ($persist ne "none"){
		$persist = "-m recent --name \"\_$fname\_$mark\_\" --set";
	} else {
		$persist = "";
	}

	$rule = "$iptables -t nat -A PREROUTING -m mark --mark $mark -j DNAT -p $proto --to-destination $rip $persist -m comment --comment ' FARM\_$fname\_$index\_ '";

	return $rule;
}

#
sub genIptSourceNat($fname,$vip,$nattype,$index,$proto,$mark,$state){
	($fname,$vip,$nattype,$index,$proto,$mark,$state)= @_;

	my $rule;

	if ($state !~ /^up$/){
		return $rule;
	}

	$rule = "$iptables -t nat -A POSTROUTING -m mark --mark $mark -j SNAT -p $proto --to-source $vip -m comment --comment ' FARM\_$fname\_$index\_ '";

	return $rule;
}

# do not remove this
1
