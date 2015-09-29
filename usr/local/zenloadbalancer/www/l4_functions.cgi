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
sub getL4FarmsPorts($farmtype)
{
	my ( $farmtype ) = @_;

	my $first  = 1;
	my $fports = "";
	my @files  = &getFarmList();
	if ( $#files > -1 )
	{
		foreach $file ( @files )
		{
			my $fname  = &getFarmName( $file );
			my $ftype  = &getFarmType( $fname );
			my $fproto = &getFarmProto( $fname );
			if ( $ftype eq "l4xnat" && $fproto eq $farmtype )
			{
				my $fport = &getFarmVip( "vipp", $fname );
				if ( &validL4ExtPort( $fproto, $fport ) )
				{
					if ( $first == 1 )
					{
						$fports = $fport;
						$first  = 0;
					}
					else
					{
						$fports = "$fports,$fport";
					}
				}
			}
		}
	}
	return $fports;
}

#
sub loadL4Modules($vproto)
{
	my ( $vproto ) = @_;

	my $status = 0;
	my $fports = &getL4FarmsPorts( $vproto );
	if ( $vproto eq "sip" )
	{
		&removeNfModule( "nf_nat_sip",       "" );
		&removeNfModule( "nf_conntrack_sip", "" );
		&loadNfModule( "nf_conntrack_sip", "ports=$fports" );
		&loadNfModule( "nf_nat_sip",       "" );

		#$status = &ReloadNfModule("nf_conntrack_sip","ports=$fports");
	}
	elsif ( $vproto eq "ftp" )
	{
		&removeNfModule( "nf_nat_ftp",       "" );
		&removeNfModule( "nf_conntrack_ftp", "" );
		&loadNfModule( "nf_conntrack_ftp", "ports=$fports" );
		&loadNfModule( "nf_nat_ftp",       "" );

		#&loadNfModule("nf_nat_ftp","");
		#$status = &ReloadNfModule("nf_conntrack_ftp","ports=$fports");
	}
	elsif ( $vproto eq "tftp" )
	{
		&removeNfModule( "nf_nat_tftp",       "" );
		&removeNfModule( "nf_conntrack_tftp", "" );
		&loadNfModule( "nf_conntrack_tftp", "ports=$fports" );
		&loadNfModule( "nf_nat_tftp",       "" );

		#&loadNfModule("nf_nat_tftp","");
		#$status = &ReloadNfModule("nf_conntrack_tftp","ports=$fports");
	}
	return $status;
}

#
sub validL4ExtPort($fproto,$ports)
{
	my ( $fproto, $ports ) = @_;

	my $status = 0;
	if ( $fproto eq "sip" || $fproto eq "ftp" || $fproto eq "tftp" )
	{
		if ( $ports =~ /\d+/ || $ports =~ /((\d+),(\d+))+/ )
		{
			$status = 1;
		}
	}
	return $status;
}

#
sub runL4FarmRestart($fname,$writeconf,$type)
{
	my ( $fname, $writeconf, $type ) = @_;

	my $alg         = &getFarmAlgorithm( $fname );
	my $fbootstatus = &getFarmBootStatus( $fname );
	my $output      = 0;
	my $pidfile     = "/var/run/l4sd.pid";

	if (    $alg eq "leastconn"
		 && $fbootstatus eq "up"
		 && $writeconf eq "false"
		 && $type eq "hot"
		 && -e "$pidfile" )
	{
		open FILE, "<$pidfile";
		my $pid = <FILE>;
		close FILE;
		kill USR1, $pid;
		$output = $?;
	}
	else
	{
		&runFarmStop( $fname, $writeconf );
		$output = &runFarmStart( $fname, $writeconf );
	}

	return $output;
}

#
sub _runL4FarmRestart($fname,$writeconf,$type)
{
	my ( $fname, $writeconf, $type ) = @_;

	my $alg         = &getFarmAlgorithm( $fname );
	my $fbootstatus = &getFarmBootStatus( $fname );
	my $output      = 0;
	my $pidfile     = "/var/run/l4sd.pid";

	if (    $alg eq "leastconn"
		 && $fbootstatus eq "up"
		 && $writeconf eq "false"
		 && $type eq "hot"
		 && -e "$pidfile" )
	{
		open FILE, "<$pidfile";
		my $pid = <FILE>;
		close FILE;
		kill '-USR1', $pid;
		$output = $?;
	}
	else
	{
		&_runFarmStop( $fname, $writeconf );
		$output = &_runFarmStart( $fname, $writeconf );
	}

	return $output;
}

#
sub sendL4ConfChange($fname)
{
	my ( $fname ) = @_;

	my $alg         = &getFarmAlgorithm( $fname );
	my $fbootstatus = &getFarmBootStatus( $fname );
	my $output      = 0;
	my $pidfile     = "/var/run/l4sd.pid";

	if ( $alg eq "leastconn" && -e "$pidfile" )
	{
		open FILE, "<$pidfile";
		my $pid = <FILE>;
		close FILE;
		kill USR1, $pid;
		$output = $?;
	}
	else
	{
		&logfile( "Running L4 restart for $fname" );
		&_runL4FarmRestart( $fname, "false", "" );
	}

	return $output;
}

#
sub setL4FarmSessionType($session,$ffile)
{
	my ( $session, $ffile ) = @_;
	my $output = -1;

	use Tie::File;
	tie @filelines, 'Tie::File', "$configdir\/$ffile";
	my $i = 0;
	for $line ( @filelines )
	{
		if ( $line =~ /^$fname\;/ )
		{
			my @args = split ( "\;", $line );
			$line =
			  "@args[0]\;@args[1]\;@args[2]\;@args[3]\;@args[4]\;@args[5]\;$session\;@args[7]\;@args[8]";
			splice @filelines, $i, $line;
			$output = $?;
		}
		$i++;
	}
	untie @filelines;
	$output = $?;

	return $output;
}

#
sub getL4FarmSessionType($ffile)
{
	my ( $ffile ) = @_;
	my $output = -1;

	open FI, "<$configdir/$ffile";
	my $first = "true";
	while ( $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line = split ( "\;", $line );
			$output = @line[6];
		}
	}
	close FI;
	return $output;
}

# set the lb algorithm to a farm
sub setL4FarmAlgorithm($alg,$ffile)
{
	my ( $alg, $ffile ) = @_;
	my $output = -1;

	use Tie::File;
	tie @filelines, 'Tie::File', "$configdir\/$ffile";
	my $i = 0;
	for $line ( @filelines )
	{
		if ( $line =~ /^$fname\;/ )
		{
			my @args = split ( "\;", $line );
			$line =
			  "@args[0]\;@args[1]\;@args[2]\;@args[3]\;@args[4]\;$alg\;@args[6]\;@args[7]\;@args[8]";
			splice @filelines, $i, $line;
			$output = $?;
		}
		$i++;
	}
	untie @filelines;
	$output = $?;
	return $output;
}

#
sub getL4FarmAlgorithm($ffile)
{
	my ( $ffile ) = @_;
	my $output = -1;

	open FI, "<$configdir/$ffile";
	my $first = "true";
	while ( $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line = split ( "\;", $line );
			$output = @line[5];
		}
	}
	close FI;
	return $output;
}

# set the protocol to a L4 farm
sub setFarmProto($proto,$fname)
{
	my ( $proto, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	&logfile( "setting 'Protocol $proto' for $fname farm $type" );

	if ( $type eq "l4xnat" )
	{
		use Tie::File;
		tie @filelines, 'Tie::File', "$configdir\/$ffile";
		my $i = 0;
		for $line ( @filelines )
		{
			if ( $line =~ /^$fname\;/ )
			{
				my @args = split ( "\;", $line );
				if ( $proto eq "all" )
				{
					@args[3] = "*";
				}
				if ( $proto eq "sip" )
				{
					@args[3] = "5060";    # the port by default for sip protocol
					@args[4] = "nat";
				}
				$line =
				  "@args[0]\;$proto\;@args[2]\;@args[3]\;@args[4]\;@args[5]\;@args[6]\;@args[7]\;@args[8]";
				splice @filelines, $i, $line;
				$output = $?;
			}
			$i++;
		}
		untie @filelines;
		$output = $?;
	}

	return $output;
}

#
sub getFarmProto($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "l4xnat" )
	{
		open FI, "<$configdir/$ffile";
		my $first = "true";
		while ( $line = <FI> )
		{
			if ( $line ne "" && $first eq "true" )
			{
				$first = "false";
				my @line = split ( "\;", $line );
				$output = @line[1];
			}
		}
		close FI;
	}

	return $output;
}

#
sub getFarmNatType($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "l4xnat" )
	{
		open FI, "<$configdir/$ffile";
		my $first = "true";
		while ( $line = <FI> )
		{
			if ( $line ne "" && $first eq "true" )
			{
				$first = "false";
				my @line = split ( "\;", $line );
				$output = @line[4];
			}
		}
		close FI;
	}

	return $output;
}

# set the NAT type for a farm
sub setFarmNatType($nat,$fname)
{
	my ( $nat, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	&logfile( "setting 'NAT type $nat' for $fname farm $type" );

	if ( $type eq "l4xnat" )
	{
		use Tie::File;
		tie @filelines, 'Tie::File', "$configdir\/$ffile";
		my $i = 0;
		for $line ( @filelines )
		{
			if ( $line =~ /^$fname\;/ )
			{
				my @args = split ( "\;", $line );
				$line =
				  "@args[0]\;@args[1]\;@args[2]\;@args[3]\;$nat\;@args[5]\;@args[6]\;@args[7]\;@args[8]";
				splice @filelines, $i, $line;
				$output = $?;
			}
			$i++;
		}
		untie @filelines;
		$output = $?;
	}

	return $output;
}

# set client persistence to a farm
sub setL4FarmPersistence($persistence,$ffile)
{
	my ( $persistence, $ffile ) = @_;
	my $output = -1;
	use Tie::File;
	tie @filelines, 'Tie::File', "$configdir\/$ffile";
	my $i = 0;
	for $line ( @filelines )
	{
		if ( $line =~ /^$fname\;/ )
		{
			my @args = split ( "\;", $line );
			$line =
			  "@args[0]\;@args[1]\;@args[2]\;@args[3]\;@args[4]\;@args[5]\;$persistence\;@args[7]\;@args[8]";
			splice @filelines, $i, $line;
			$output = $?;
		}
		$i++;
	}
	untie @filelines;
	$output = $?;

	return $output;
}

#
sub getL4FarmPersistence($ffile)
{
	my ( $ffile ) = @_;
	my $output = -1;
	open FI, "<$configdir/$ffile";
	my $first = "true";
	while ( $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line = split ( "\;", $line );
			$output = @line[6];
		}
	}
	close FI;
	return $output;
}

# set the max clients of a farm
sub setL4FarmMaxClientTime($track,$ffile)
{
	my ( $track, $ffile ) = @_;
	my $output = -1;

	use Tie::File;
	tie @filelines, 'Tie::File', "$configdir\/$ffile";
	my $i = 0;

	for $line ( @filelines )
	{
		if ( $line =~ /^$fname\;/ )
		{
			my @args = split ( "\;", $line );
			$line =
			  "@args[0]\;@args[1]\;@args[2]\;@args[3]\;@args[4]\;@args[5]\;@args[6]\;$track\;@args[8]";
			splice @filelines, $i, $line;
			$output = $?;
		}
		$i++;
	}
	untie @filelines;
	$output = $?;
	return $output;
}

#
sub getL4FarmMaxClientTime($ffile)
{
	my ( $ffile ) = @_;
	my @output;

	my $ffile = &getFarmFile( $fname );
	open FI, "<$configdir/$ffile";
	my $first = "true";

	while ( $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line = split ( "\;", $line );
			@output = @line[7];
		}
	}
	close FI;
	return @output;
}

#
sub getL4BackendEstConns($fname,$ip_backend,@netstat)
{
	my ( $fname, $ip_backend, @netstat ) = @_;
	my @nets = ();

	my $proto   = &getFarmProto( $fname );
	my $nattype = &getFarmNatType( $farmname );
	my @fportlist;
	my $regexp = "";
	@fportlist = &getFarmPortList( $fvipp );

	if ( @fportlist[0] !~ /\*/ )
	{
		$regexp = "\(" . join ( '|', @fportlist ) . "\)";
	}
	else
	{
		$regexp = "\.*";
	}

	undef ( @fportlist );

	if ( $nattype eq "dnat" )
	{
		if ( $proto eq "sip" || $proto eq "all" || $proto eq "tcp" )
		{
			push (
				@nets,
				&getNetstatFilter(
					   "tcp", "",
					   "\.* ESTABLISHED src=\.* dst=$fvip \.* dport=$regexp \.*src=$ip_backend \.*",
					   "", @netstat
				)
			);
		}
		if ( $proto eq "sip" || $proto eq "all" || $proto eq "udp" )
		{
			push (
				   @nets,
				   &getNetstatFilter(
									"udp", "",
									"\.* src=\.* dst=$fvip \.* dport=$regexp .*src=$ip_backend \.*",
									"", @netstat
				   )
			);
		}
	}
	else
	{
		if ( $proto eq "sip" || $proto eq "all" || $proto eq "tcp" )
		{
			push (
				@nets,
				&getNetstatFilter(
					"tcp",
					"",
					"\.*ESTABLISHED src=\.* dst=$fvip sport=\.* dport=$regexp \.*src=$ip_backend \.*",
					"",
					@netstat
				)
			);
		}
		if ( $proto eq "sip" || $proto eq "all" || $proto eq "udp" )
		{
			push (
				   @nets,
				   &getNetstatFilter(
									"udp", "",
									"\.* src=\.* dst=$fvip \.* dport=$regexp .*src=$ip_backend \.*",
									"", @netstat
				   )
			);
		}
	}

	return @nets;
}

#
sub getL4FarmEstConns($fname,@netstat)
{
	my ( $fname, @netstat ) = @_;
	my @nets = ();

	my $proto   = &getFarmProto( $fname );
	my $nattype = &getFarmNatType( $farmname );
	my $fvip    = &getFarmVip( "vip", $fname );
	my $fvipp   = &getFarmVip( "vipp", $fname );
	my @fportlist;
	my $regexp = "";
	@fportlist = &getFarmPortList( $fvipp );
	if ( @fportlist[0] !~ /\*/ )
	{
		$regexp = "\(" . join ( '|', @fportlist ) . "\)";
	}
	else
	{
		$regexp = "\.*";
	}
	undef ( @fportlist );
	my @content = &getFarmBackendStatusCtl( $fname );
	my @backends = &getFarmBackendsStatus( $fname, @content );
	foreach ( @backends )
	{
		my @backends_data = split ( ";", $_ );
		if ( $backends_data[4] eq "up" )
		{
			my $ip_backend = $backends_data[0];
			if ( $nattype eq "dnat" )
			{
				if ( $proto eq "sip" || $proto eq "all" || $proto eq "tcp" )
				{
					push (
						 @nets,
						 &getNetstatFilter(
								"tcp", "",
								"\.* ESTABLISHED src=\.* dst=$fvip \.* dport=$regexp .*src=$ip_backend \.*",
								"", @netstat
						 )
					);
				}
				if ( $proto eq "sip" || $proto eq "all" || $proto eq "udp" )
				{
					push (
						   @nets,
						   &getNetstatFilter(
											"udp", "",
											"\.* src=\.* dst=$fvip \.* dport=$regexp .*src=$ip_backend \.*",
											"", @netstat
						   )
					);
				}
			}
			else
			{
				if ( $proto eq "sip" || $proto eq "all" || $proto eq "tcp" )
				{
					push (
						 @nets,
						 &getNetstatFilter(
								"tcp", "",
								"\.* ESTABLISHED src=\.* dst=$fvip \.* dport=$regexp .*src=$ip_backend \.*",
								"", @netstat
						 )
					);
				}
				if ( $proto eq "sip" || $proto eq "all" || $proto eq "udp" )
				{
					push (
						@nets,
						&getNetstatFilter(
							   "udp", "",
							   "\.* src=\.* dst=$fvip \.* dport=$regexp .*[^\[UNREPLIED\]] src=$ip_backend",
							   "", @netstat
						)
					);
				}
			}

		}
	}
	return @nets;
}

sub getL4BackendTWConns($fname,$ip_backend,@netstat)
{
	my ( $fname, $ip_backend, @netstat ) = @_;
	my @nets = ();

	my $proto   = &getFarmProto( $fname );
	my $nattype = &getFarmNatType( $farmname );
	my @fportlist;
	my $regexp = "";
	@fportlist = &getFarmPortList( $fvipp );
	if ( @fportlist[0] !~ /\*/ )
	{
		$regexp = "\(" . join ( '|', @fportlist ) . "\)";
	}
	else
	{
		$regexp = "\.*";
	}
	undef ( @fportlist );
	if ( $proto eq "sip" || $proto eq "all" || $proto eq "tcp" )
	{
		push (
			   @nets,
			   &getNetstatFilter(
					  "tcp", "",
					  "\.*TIME\_WAIT src=\.* dst=$fvip \.* dport=$regexp .*src=$ip_backend \.*",
					  "", @netstat
			   )
		);
	}
	if ( $proto eq "sip" || $proto eq "all" || $proto eq "udp" )
	{
		push (
			   @nets,
			   &getNetstatFilter(
					  "udp", "",
					  "\.*TIME\_WAIT src=\.* dst=$fvip \.* dport=$regexp .*src=$ip_backend .\*",
					  "", @netstat
			   )
		);
	}

	return @nets;
}

#
sub getL4FarmTWConns($fname,@netstat)
{
	my ( $fname, @netstat ) = @_;
	my @nets = ();

	my $proto   = &getFarmProto( $fname );
	my $nattype = &getFarmNatType( $farmname );
	my $fvip    = &getFarmVip( "vip", $fname );
	my $fvipp   = &getFarmVip( "vipp", $fname );
	my @fportlist;
	my $regexp = "";
	@fportlist = &getFarmPortList( $fvipp );
	if ( @fportlist[0] !~ /\*/ )
	{
		$regexp = "\(" . join ( '|', @fportlist ) . "\)";
	}
	else
	{
		$regexp = "\.*";
	}
	undef ( @fportlist );
	my @content = &getFarmBackendStatusCtl( $fname );
	my @backends = &getFarmBackendsStatus( $fname, @content );
	foreach ( @backends )
	{
		my @backends_data = split ( ";", $_ );
		if ( $backends_data[4] eq "up" )
		{
			my $ip_backend   = $backends_data[0];
			my $port_backend = $backends_data[1];
			push (
				   @nets,
				   &getNetstatFilter(
							  "tcp", "",
							  "\.*\_WAIT src=\.* dst=$fvip \.* dport=$regexp .*src=$ip_backend \.*",
							  "", @netstat
				   )
			);
		}
	}

	return @nets;
}

sub getL4BackendSYNConns($fname,$ip_backend,@netstat)
{
	my ( $fname, $ip_backend, @netstat ) = @_;
	my @nets = ();

	my $proto     = &getFarmProto( $fname );
	my $nattype   = &getFarmNatType( $farmname );
	my @fportlist = &getFarmPortList( $fvipp );
	my $regexp    = "";

	if ( @fportlist[0] !~ /\*/ )
	{
		$regexp = "\(" . join ( '|', @fportlist ) . "\)";
	}
	else
	{
		$regexp = "\.*";
	}
	undef ( @fportlist );
	if ( $nattype eq "dnat" )
	{
		if ( $proto eq "sip" || $proto eq "all" || $proto eq "tcp" )
		{
			push (
				   @nets,
				   &getNetstatFilter(
						   "tcp", "",
						   "\.* SYN\.* src=\.* dst=$fvip \.* dport=$regexp \.* src=$ip_backend \.*",
						   "", @netstat
				   )
			);
		}
		if ( $proto eq "sip" || $proto eq "all" || $proto eq "udp" )
		{
			push (
				@nets,
				&getNetstatFilter(
					  "udp", "",
					  "\.* src=\.* dst=$fvip \.* dport=$regexp \.*UNREPLIED\.* src=$ip_backend \.*",
					  "", @netstat
				)
			);
		}
	}
	else
	{
		if ( $proto eq "sip" || $proto eq "all" || $proto eq "tcp" )
		{
			push (
				   @nets,
				   &getNetstatFilter(
						   "tcp", "",
						   "\.* SYN\.* src=\.* dst=$fvip \.* dport=$regexp \.* src=$ip_backend \.*",
						   "", @netstat
				   )
			);
		}
		if ( $proto eq "sip" || $proto eq "all" || $proto eq "udp" )
		{
			push (
				@nets,
				&getNetstatFilter(
					  "udp", "",
					  "\.* src=\.* dst=$fvip \.* dport=$regexp \.*UNREPLIED\.* src=$ip_backend \.*",
					  "", @netstat
				)
			);
		}
	}

	return @nets;
}

#
sub getL4FarmSYNConns($fname,@netstat)
{
	my ( $fname, @netstat ) = @_;
	my @nets = ();

	my $proto     = &getFarmProto( $fname );
	my $nattype   = &getFarmNatType( $farmname );
	my $fvip      = &getFarmVip( "vip", $fname );
	my $fvipp     = &getFarmVip( "vipp", $fname );
	my @fportlist = &getFarmPortList( $fvipp );
	my $regexp    = "";

	if ( @fportlist[0] !~ /\*/ )
	{
		$regexp = "\(" . join ( '|', @fportlist ) . "\)";
	}
	else
	{
		$regexp = "\.*";
	}
	undef ( @fportlist );
	my @content = &getFarmBackendStatusCtl( $fname );
	my @backends = &getFarmBackendsStatus( $fname, @content );
	foreach ( @backends )
	{
		my @backends_data = split ( ";", $_ );
		if ( $backends_data[4] eq "up" )
		{
			my $ip_backend = $backends_data[0];

			if ( $nattype eq "dnat" )
			{
				if ( $proto eq "sip" || $proto eq "all" || $proto eq "tcp" )
				{
					push (
						   @nets,
						   &getNetstatFilter(
								   "tcp", "",
								   "\.* SYN\.* src=\.* dst=$fvip \.* dport=$regexp \.* src=$ip_backend \.*",
								   "", @netstat
						   )
					);

#push(@nets, &getNetstatFilter("tcp","","\.* SYN\.* src=\.* dst=$fvip \.* src=$ip_backend \.*","",@netstat)); # TCP
				}
				if ( $proto eq "sip" || $proto eq "all" || $proto eq "udp" )
				{
					push (
						@nets,
						&getNetstatFilter(
							  "udp", "",
							  "\.* src=\.* dst=$fvip \.* dport=$regexp \.*UNREPLIED\.* src=$ip_backend \.*",
							  "", @netstat
						)
					);

#push(@nets, &getNetstatFilter("udp","","\.* src=\.* dst=$fvip \.*UNREPLIED\.* src=$ip_backend \.*","",@netstat)); # UDP
				}
			}
			else
			{
				if ( $proto eq "sip" || $proto eq "all" || $proto eq "tcp" )
				{
					push (
						   @nets,
						   &getNetstatFilter(
								   "tcp", "",
								   "\.* SYN\.* src=\.* dst=$fvip \.* dport=$regexp \.* src=$ip_backend \.*",
								   "", @netstat
						   )
					);

#push(@nets, &getNetstatFilter("tcp","","\.* SYN\.* src=\.* dst=$fvip \.* src=$ip_backend \.*","",@netstat)); # TCP
				}
				if ( $proto eq "sip" || $proto eq "all" || $proto eq "udp" )
				{
					push (
						@nets,
						&getNetstatFilter(
							  "udp", "",
							  "\.* src=\.* dst=$fvip \.* dport=$regexp \.*UNREPLIED\.* src=$ip_backend \.*",
							  "", @netstat
						)
					);
				}

			}

		}
	}

	return @nets;
}

# Returns farm status
sub getL4FarmBootStatus($file)
{
	my ( $file ) = @_;
	my $output = "down";

	open FI, "<$configdir/$file";
	my $first = "true";
	while ( $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line_a = split ( "\;", $line );
			$output = @line_a[8];
			chomp ( $output );
		}
	}
	close FI;
	return $output;
}

# Start Farm rutine
sub _runL4FarmStart($file,$writeconf,$status)
{
	my ( $file, $writeconf, $status ) = @_;

	if ( $writeconf eq "true" )
	{
		use Tie::File;
		tie @filelines, 'Tie::File', "$configdir\/$file";
		my $first = 1;
		foreach ( @filelines )
		{
			if ( $first eq 1 )
			{
				s/\;down/\;up/g;
				$first = 0;
			}
		}
		untie @filelines;
	}

	# Apply changes online
	if ( $status != -1 )
	{

		# Set fw rules calculating the $nattype and $protocol
		# for every server of the farm do:
		#   set mark rules for matched connections
		#   set rule for nattype
		my $status  = 0;
		my $nattype = &getFarmNatType( $fname );
		my $lbalg   = &getFarmAlgorithm( $fname );
		my $vip     = &getFarmVip( "vip", $fname );
		my $vport   = &getFarmVip( "vipp", $fname );
		my $vproto  = &getFarmProto( $fname );
		my $persist = &getFarmPersistence( $fname );
		my @pttl    = &getFarmMaxClientTime( $fname );
		my $ttl     = @pttl[0];
		my $proto   = "";

		my @run = &getFarmServers( $fname );
		my @tmangle;
		my @tnat;
		my @tmanglep;
		my @tsnat;
		my @traw;

		my $prob = 0;
		foreach $lservers ( @run )
		{
			my @serv = split ( "\;", $lservers );
			if ( @serv[6] =~ /up/ )
			{
				$prob = $prob + @serv[4];
			}
		}

		if ( $vport eq "*" )
		{
			$vport = "0:65535";
		}

		# Load L4 scheduler if needed
		if ( $lbalg eq "leastconn" && -e "$l4sd" )
		{
			system ( "$l4sd & > /dev/null" );
		}

		# Load required modules
		if ( $vproto eq "sip" || $vproto eq "tftp" )
		{
			$status = &loadL4Modules( $vproto );
			$proto  = "udp";
		}
		elsif ( $vproto eq "ftp" )
		{
			$status = &loadL4Modules( $vproto );
			$proto  = "tcp";
		}
		else
		{
			$proto = $vproto;
		}
		my $bestprio = 1000;
		my @srvprio;

		foreach $lservers ( @run )
		{
			my @serv = split ( "\;", $lservers );
			if ( @serv[6] =~ /up/ || $lbalg eq "leastconn" )
			{    # TMP: leastconn dynamic backend status check
				if ( $lbalg eq "weight" || $lbalg eq "leastconn" )
				{
					my $port = @serv[2];
					my $rip  = @serv[1];
					if ( @serv[2] ne "" && $proto ne "all" )
					{
						$rip = "$rip\:$port";
					}
					my $tag = &genIptMark( $fname,   $nattype, $lbalg,   $vip,     $vport, $proto,
										   @serv[0], @serv[3], @serv[4], @serv[6], $prob );

					if ( $persist ne "none" )
					{
						my $tagp =
						  &genIptMarkPersist( $fname, $vip, $vport, $proto, $ttl, @serv[0], @serv[3],
											  @serv[6] );
						push ( @tmanglep, $tagp );

						#my $tagp2 = &genIptMarkReturn($fname,$vip,$vport,$proto,@serv[0],@serv[6]);
						#push(@tmanglep,$tagp2);
					}

					# dnat rules
					#if ($vproto ne "sip"){
					my $red = &genIptRedirect( $fname,   $nattype, @serv[0], $rip, $proto,
											   @serv[3], @serv[4], $persist, @serv[6] );
					push ( @tnat, $red );

					#}

					if ( $nattype eq "nat" )
					{
						my $ntag;
						if ( $vproto eq "sip" )
						{
							$ntag = &genIptSourceNat( $fname, $vip,     $nattype, @serv[0],
													  $proto, @serv[3], @serv[6] );
						}
						else
						{
							$ntag =
							  &genIptMasquerade( $fname, $nattype, @serv[0], $proto, @serv[3], @serv[6] );
						}

						push ( @tsnat, $ntag );
					}

					push ( @tmangle, $tag );

					$prob = $prob - @serv[4];
				}

				if ( $lbalg eq "prio" )
				{
					if ( @serv[5] ne "" && @serv[5] < $bestprio )
					{
						@srvprio  = @serv;
						$bestprio = @serv[5];
					}
				}
			}
		}

		if ( @srvprio && $lbalg eq "prio" )
		{
			my @run = `echo 10 > /proc/sys/net/netfilter/nf_conntrack_udp_timeout_stream`;
			my @run = `echo 5 > /proc/sys/net/netfilter/nf_conntrack_udp_timeout`;

			#&logfile("BESTPRIO $bestprio");
			my $port = @srvprio[2];
			my $rip  = @srvprio[1];
			if ( @srvprio[2] ne "" )
			{
				$rip = "$rip\:$port";
			}
			my $tag = &genIptMark(
								   $fname,      $nattype,    $lbalg,      $vip,
								   $vport,      $proto,      @srvprio[0], @srvprio[3],
								   @srvprio[4], @srvprio[6], $prob
			);

			# dnat rules
			#if ($vproto ne "sip"){
			my $red = &genIptRedirect(
									   $fname,      $nattype, @srvprio[0],
									   $rip,        $proto,   @srvprio[3],
									   @srvprio[4], $persist, @srvprio[6]
			);

			#}

			if ( $persist ne "none" )
			{
				my $tagp =
				  &genIptMarkPersist( $fname, $vip, $vport, $proto, $ttl, @srvprio[0],
									  @srvprio[3], @srvprio[6] );
				push ( @tmanglep, $tagp );

			  #my $tagp2 = &genIptMarkReturn($fname,$vip,$vport,$proto,@srvprio[0],@srvprio[6]);
			  #push(@tmanglep,$tagp2);
			}

			if ( $nattype eq "nat" )
			{
				my $ntag;
				if ( $vproto eq "sip" )
				{
					$ntag =
					  &genIptSourceNat( $fname, $vip, $nattype, @srvprio[0], $proto, @srvprio[3],
										@srvprio[6] );
				}
				else
				{
					$ntag =
					  &genIptMasquerade( $fname, $nattype, @srvprio[0], $proto, @srvprio[3],
										 @srvprio[6] );
				}
				push ( @tsnat, $ntag );
			}

#my $nraw = "$iptables -t raw -A OUTPUT -j NOTRACK -p $proto -d $vip --dport $vport -m comment --comment ' FARM\_$fname\_@srvprio[0]\_ '";
#my $nnraw = "$iptables -t raw -A OUTPUT -j NOTRACK -p $proto -s $vip -m comment --comment ' FARM\_$fname\_@srvprio[0]\_ '";
			push ( @tmangle, $tag );
			push ( @tnat,    $red );

			#push(@traw,$nraw);
			#push(@traw,$nnraw);
		}

		foreach $nraw ( @traw )
		{
			if ( $nraw ne "" )
			{
				&logfile( "running $nraw" );
				my @run = `$nraw`;
				if ( $? != 0 )
				{
					&logfile( "last command failed!" );
					$status = -1;
				}
			}
		}

		@tmangle = reverse ( @tmangle );
		foreach $ntag ( @tmangle )
		{
			if ( $ntag ne "" )
			{
				&logfile( "running $ntag" );
				my @run = `$ntag`;
				if ( $? != 0 )
				{
					&logfile( "last command failed!" );
					$status = -1;
				}
			}
		}

		if ( $persist ne "none" )
		{
			foreach $ntag ( @tmanglep )
			{
				if ( $ntag ne "" )
				{
					&logfile( "running $ntag" );
					my @run = `$ntag`;
					if ( $? != 0 )
					{
						&logfile( "last command failed!" );
						$status = -1;
					}
				}
			}
		}

		foreach $nred ( @tnat )
		{
			if ( $nred ne "" )
			{
				&logfile( "running $nred" );
				my @run = `$nred`;
				if ( $? != 0 )
				{
					&logfile( "last command failed!" );
					$status = -1;
				}
			}
		}

		foreach $nred ( @tsnat )
		{
			if ( $nred ne "" )
			{
				&logfile( "running $nred" );
				my @run = `$nred`;
				if ( $? != 0 )
				{
					&logfile( "last command failed!" );
					$status = -1;
				}
			}
		}

		# Enable IP forwarding
		&setIpForward( "true" );

		# Enable active l4 file
		if ( $status != -1 )
		{
			open FI, ">$piddir\/$fname\_$type.pid";
			close FI;
		}
	}

	return $status;
}

# Stop Farm rutine
sub _runL4FarmStop($filename,$writeconf,$status)
{
	my ( $filename, $writeconf, $status ) = @_;

	if ( $writeconf eq "true" )
	{
		use Tie::File;
		tie @filelines, 'Tie::File', "$configdir\/$filename";
		my $first = 1;
		foreach ( @filelines )
		{
			if ( $first eq 1 )
			{
				s/\;up/\;down/g;
				$status = $?;
				$first  = 0;
			}
		}
		untie @filelines;
	}

	#&runFarmGuardianStop($fname,"");
	my $falg = &getFarmAlgorithm( $fname );

	# Apply changes online
	if ( $status != -1 )
	{
		# Disable rules
		my @allrules = &getIptList( "raw", "OUTPUT" );
		$status = &deleteIptRules( "farm", $fname, "raw", "OUTPUT", @allrules );
		my @allrules = &getIptList( "mangle", "PREROUTING" );
		$status = &deleteIptRules( "farm", $fname, "mangle", "PREROUTING", @allrules );
		my @allrules = &getIptList( "nat", "PREROUTING" );
		$status = &deleteIptRules( "farm", $fname, "nat", "PREROUTING", @allrules );
		my @allrules = &getIptList( "nat", "POSTROUTING" );
		$status = &deleteIptRules( "farm", $fname, "nat", "POSTROUTING", @allrules );

		# Disable active l4xnat file
		unlink ( "$piddir\/$fname\_$type.pid" );
		if ( -e "$piddir\/$fname\_$type.pid" )
		{
			$status = -1;
		}
		else
		{
			$status = 0;
		}
	}

	return $status;
}

#
sub runL4FarmCreate($fvip,$fname)
{
	my ( $fvip, $fname ) = @_;
	my $output = -1;
	my $type   = "l4xnat";

	open FO, ">$configdir\/$fname\_$type.cfg";
	print FO "$fname\;all\;$fvip\;*\;dnat\;weight\;none\;120\;up\n";
	close FO;
	$output = $?;

	if ( !-e "$piddir/$fname_$type.pid" )
	{

		# Enable active l4xnat file
		open FI, ">$piddir\/$fname\_$type.pid";
		close FI;
	}

	return $output;
}

# Returns farm vip
sub getL4FarmVip($info,$file)
{
	my ( $info, $file ) = @_;
	my $output = -1;

	open FI, "<$configdir/$file";
	my $first = "true";
	while ( $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line_a = split ( "\;", $line );
			if ( $info eq "vip" )   { $output = @line_a[2]; }
			if ( $info eq "vipp" )  { $output = @line_a[3]; }
			if ( $info eq "vipps" ) { $output = "@line_a[2]\:@line_a[3]"; }
		}
	}
	close FI;

	return $output;
}

# Set farm virtual IP and virtual PORT
sub setL4FarmVirtualConf($vip,$vipp,$fname,$fconf)
{
	my ( $vip, $vipp, $fname, $fconf ) = @_;
	my $stat = -1;

	use Tie::File;
	tie @filelines, 'Tie::File', "$configdir\/$fconf";
	my $i = 0;
	for $line ( @filelines )
	{
		if ( $line =~ /^$fname\;/ )
		{
			my @args = split ( "\;", $line );
			$line =
			  "@args[0]\;@args[1]\;$vip\;$vipp\;@args[4]\;@args[5]\;@args[6]\;@args[7]\;@args[8]";
			splice @filelines, $i, $line;
			$stat = $?;
		}
		$i++;
	}
	untie @filelines;
	$stat = $?;

	return $stat;
}

#
sub setL4FarmServer($ids,$rip,$port,$weight,$priority,$fname,$file)
{
	my ( $ids, $rip, $port, $weight, $priority, $fname, $file );
	my $output = -1;

	tie my @contents, 'Tie::File', "$configdir\/$file";
	my $i   = 0;
	my $l   = 0;
	my $end = "false";
	foreach $line ( @contents )
	{
		if ( $line =~ /^\;server\;/ && $end ne "true" )
		{
			if ( $i eq $ids )
			{
				my @aline = split ( "\;", $line );
				my $dline = "\;server\;$rip\;$port\;@aline[4]\;$weight\;$priority\;up\n";
				splice @contents, $l, 1, $dline;
				$output = $?;
				$end    = "true";
			}
			else
			{
				$i++;
			}
		}
		$l++;
	}
	if ( $end eq "false" )
	{
		my $mark = &getNewMark( $fname );
		push ( @contents, "\;server\;$rip\;$port\;$mark\;$weight\;$priority\;up\n" );
		$output = $?;
	}
	untie @contents;

	return $output;
}

#
sub runL4FarmServerDelete($ids,$ffile)
{
	my ( $ids, $ffile ) = @_;
	my $output = -1;

	tie my @contents, 'Tie::File', "$configdir\/$ffile";
	my $i   = 0;
	my $l   = 0;
	my $end = "false";
	my $mark;

	foreach $line ( @contents )
	{
		if ( $line =~ /^\;server\;/ && $end ne "true" )
		{
			if ( $i eq $ids )
			{
				my @sdata = split ( "\;", $line );
				$mark = &delMarks( "", @sdata[4] );
				splice @contents, $l, 1,;
				$output = $?;
				$end    = "true";
			}
			else
			{
				$i++;
			}
		}
		$l++;
	}
	untie @contents;

	return $output;
}

#function that return the status information of a farm:
#ip, port, backendstatus, weight, priority, clients
sub getL4FarmBackendsStatus($fname,@content)
{
	my ( $fname, @content ) = @_;
	my @servers;

	foreach $server ( @content )
	{
		my @serv = split ( "\;", $server );
		my $port = @serv[3];
		if ( $port eq "" )
		{
			$port = &getFarmVip( "vipp", $fname );
		}
		push ( @servers, "@serv[2]\;$port\;@serv[5]\;@serv[6]\;@serv[7]" );
	}

	return @servers;
}

sub setL4FarmBackendStatus($file,$index,$stat)
{
	my ( $file, $index, $stat ) = @_;

	# check output !!!
	my $output = -1;

	use Tie::File;
	tie @filelines, 'Tie::File', "$configdir\/$file";
	my $fileid   = 0;
	my $serverid = 0;
	foreach $line ( @filelines )
	{
		if ( $line =~ /\;server\;/ )
		{
			if ( $serverid eq $index )
			{
				my @lineargs = split ( "\;", $line );
				@lineargs[7] = $stat;
				@filelines[$fileid] = join ( "\;", @lineargs );
			}
			$serverid++;
		}
		$fileid++;
	}
	untie @filelines;

	return $output;
}

sub getFarmPortList($fvipp)
{
	my ( $fvipp ) = @_;
	my @portlist;
	my $port;
	my @retportlist = ();
	@portlist = split ( ",", $fvipp );

	if ( $portlist[0] !~ /\*/ )
	{

		foreach $port ( @portlist )
		{
			if ( $port =~ /:/ )
			{
				my @intlimits = split ( ":", $port );
				for ( my $i = @intlimits[0] ; $i <= @intlimits[1] ; $i++ )
				{
					push ( @retportlist, $i );
				}
			}
			else
			{
				push ( @retportlist, $port );
			}

		}
	}
	else
	{
		$retportlist[0] = '*';
	}
	return @retportlist;
}

#
sub getL4FarmBackendStatusCtl($fname)
{
	my ( $fname ) = @_;
	my @output = -1;

	my $ffile = &getFarmFile( $fname );
	my @content;

	tie my @content, 'Tie::File', "$configdir\/$ffile";
	@output = grep /^\;server\;/, @content;
	untie @content;

	return @output;
}

# do not remove this
1
