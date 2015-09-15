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
sub getGSLBFarmPidFile($farmname){
	my ($fname) = @_;

	my $pidf = "$configdir\/$fname\_gslb.cfg\/run\/gdnsd.pid";

	return $pidf;
}

#
sub getGSLBStartCommand($farmname){
	my ($fname) = @_;

	my $file = &getFarmFile($fname);
	my $cmd = "$gdnsd -d $configdir\/$file start";

	return $cmd;
}

#
sub getGSLBStopCommand($farmname){
	my ($fname) = @_;

	my $file = &getFarmFile($fname);
	my $cmd = "$gdnsd -d $configdir\/$file stop";

	return $cmd;
}

# Create a new Zone in a GSLB farm
sub setFarmGSLBNewZone($fname,$service){
	my ($fname,$svice) =  @_;

	my $output = -1;
	my $ftype = &getFarmType($fname);

	if ($ftype eq "gslb"){
		opendir(DIR, "$configdir\/$fname\_$ftype.cfg\/etc\/zones\/");
		my @files= grep { /^$svice/ } readdir(DIR);
		closedir(DIR);

		if ( $files == 0 ) {
			open FO, ">$configdir\/$fname\_$ftype.cfg\/etc\/zones\/$svice";
			print FO "@	SOA ns1 hostmaster (\n	1\n	7200\n	1800\n	259200\n	900\n)\n\n";
			print FO "@		NS	ns1 ;index_0\n";
			print FO "ns1		A	0.0.0.0 ;index_1\n";
			close FO;

			$output = 0;
       		} else {
			$output = 1;
       		}
	}
	return $output;
}

# Delete an existing Zone in a GSLB farm
sub setFarmGSLBDeleteZone($fname,$service){
	my ($fname,$svice) =  @_;

	my $output = -1;
	my $ftype = &getFarmType($fname);

	if ($ftype eq "gslb"){
		use File::Path 'rmtree';
		rmtree([ "$configdir\/$fname\_$ftype.cfg\/etc\/zones\/$svice" ]);
		$output = 0;
	}
	return $output;
}

# Create a new Service in a GSLB farm
sub setFarmGSLBNewService($fname,$service,$algorithm){
        my ($fname,$svice,$alg) =  @_;

        my $output = -1;
        my $ftype = &getFarmType($fname);
        my $gsalg = "simplefo";

        if ($ftype eq "gslb"){
                if ($alg eq "roundrobin"){
                        $gsalg = "multifo";
                } else {
                        if ($alg eq "prio"){
                        	$gsalg = "simplefo";
                        }
                }
		opendir(DIR, "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/");
		my @files= grep { /^$svice/ } readdir(DIR);
		closedir(DIR);

		if ( $files == 0 ) {
			open FO, ">$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/$svice.cfg";
			print FO "$gsalg => {\n\tservice_types = up\n";
			print FO "\t$svice => {\n\t\tservice_types = tcp_80\n";
			print FO "\t}\n}\n";
			close FO;
			$output = 0;
			# Include the plugin file in the main configuration
			tie @fileconf, 'Tie::File', "$configdir\/$fname\_$ftype.cfg\/etc\/config";
			my $found=0;
			my $index=0;
			foreach $line(@fileconf){
				if ($line =~ /plugins => /){
					$found=1;
					$index++;
				}
				if ($found==1){
					splice @fileconf,$index,0,"	\$include{plugins\/$svice.cfg},";
					last;
				}
				$index++;
			}
			untie @fileconf;
			&setFarmVS($fname,$svice,"dpc","80");
       		} else {
			$output = -1;
       		}
	}
	return $output;
}

# Delete an existing Service in a GSLB farm
sub setFarmGSLBDeleteService($fname,$service){
	my ($fname,$svice) =  @_;

	my $output = -1;
	my $ftype = &getFarmType($fname);

	if ($ftype eq "gslb"){
		use File::Path 'rmtree';
		rmtree([ "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/$svice.cfg" ]);
		tie @fileconf, 'Tie::File', "$configdir\/$fname\_$ftype.cfg\/etc\/config";
		my $found=0;
		my $index=0;
		foreach $line(@fileconf){
			if ($line =~ /plugins => /){
				$found=1;
				$index++;
			}
			if ($found==1 && $line =~ /plugins\/$svice.cfg/){
				splice @fileconf,$index,1;
				last;
			}
			$index++;
		}
		untie @fileconf;
		$output = 0;
	}
	return $output;
}

# do not remove this
1
