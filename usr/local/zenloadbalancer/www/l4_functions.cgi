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
sub getL4FarmsPorts($farmtype){
	my ($farmtype) = @_;

	my $first = 1;
	my $fports="";
	my @files = &getFarmList();
	if ($#files > -1){
		foreach $file (@files){
			my $fname = &getFarmName($file);
			my $ftype = &getFarmType($fname);
			if ($ftype eq "l4xnat" && $ftype eq $farmtype){
				my $fproto = &getFarmProto($fname);
				my $fport = &getFarmVip("vipp",$fname);
				if (&validL4ExtPort($fproto,$fport)){
					if ($first == 1){
						$fports = $fport;
						$first = 0;
					} else {
						$fports = "$fports,$fport";
					}
				}
			}
		}
	}
	return $fports;
}

#
sub loadL4Modules($vproto){
	my ($farmtype) = @_;

	my $status = 0;
	my $fports = &getL4FarmsPorts($vproto);
	if ($vproto eq "sip"){
		&loadNfModule("nf_nat_sip","");
		$status = &ReloadNfModule("nf_conntrack_sip","ports=$fports");
	} elsif ($vproto eq "ftp"){
		&loadNfModule("nf_nat_ftp","");
		$status = &ReloadNfModule("nf_conntrack_ftp","ports=$fports");
	} elsif ($vproto eq "tftp"){
		&loadNfModule("nf_nat_tftp","");
		$status = &ReloadNfModule("nf_conntrack_tftp","ports=$fports");
	}
	return $status;
}

#
sub validL4ExtPort($fproto,$ports){
	my ($fproto,$ports) = @_;

	my $status = 0;
	if ($fproto eq "sip" && $fproto eq "ftp" && $fproto eq "tftp"){
		if ($ports =~ /\d+/ || $ports =~ /((\d+),(\d+))+/){
			$status = 1;
		}
	}
	return $status;
}

# do not remove this
1
