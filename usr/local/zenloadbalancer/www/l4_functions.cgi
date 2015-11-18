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
sub getL4FarmsPorts    # ($farm_type)
{
	my ( $farm_type ) = @_;

	my $first           = 1;
	my $port_list       = "";
	my @farms_filenames = &getFarmList();
	if ( $#farms_filenames > -1 )
	{
		foreach my $farm_filename ( @farms_filenames )
		{
			my $farm_name     = &getFarmName( $farm_filename );
			my $farm_type     = &getFarmType( $farm_name );
			my $farm_protocol = &getFarmProto( $farm_name );

			if ( $farm_type eq "l4xnat" && $farm_protocol eq $farm_type )
			{
				my $farm_port = &getFarmVip( "vipp", $farm_name );
				if ( &validL4ExtPort( $farm_protocol, $farm_port ) )
				{
					if ( $first == 1 )
					{
						$port_list = $farm_port;
						$first     = 0;
					}
					else
					{
						$port_list = "$port_list,$farm_port";
					}
				}
			}
		}
	}
	return $port_list;
}

#
sub loadL4Modules    # ($protocol)
{
	my ( $protocol ) = @_;

	my $status    = 0;
	my $port_list = &getL4FarmsPorts( $protocol );
	if ( $protocol eq "sip" )
	{
		&removeNfModule( "nf_nat_sip" );
		&removeNfModule( "nf_conntrack_sip" );
		&loadNfModule( "nf_conntrack_sip", "ports=$port_list" );
		&loadNfModule( "nf_nat_sip",       "" );
	}
	elsif ( $protocol eq "ftp" )
	{
		&removeNfModule( "nf_nat_ftp" );
		&removeNfModule( "nf_conntrack_ftp" );
		&loadNfModule( "nf_conntrack_ftp", "ports=$port_list" );
		&loadNfModule( "nf_nat_ftp",       "" );
	}
	elsif ( $protocol eq "tftp" )
	{
		&removeNfModule( "nf_nat_tftp" );
		&removeNfModule( "nf_conntrack_tftp" );
		&loadNfModule( "nf_conntrack_tftp", "ports=$port_list" );
		&loadNfModule( "nf_nat_tftp",       "" );
	}
	return $status;
}

#
sub validL4ExtPort    # ($farm_protocol,$ports)
{
	my ( $farm_protocol, $ports ) = @_;

	my $status = 0;
	if (    $farm_protocol eq "sip"
		 || $farm_protocol eq "ftp"
		 || $farm_protocol eq "tftp" )
	{
		if ( $ports =~ /\d+/ || $ports =~ /((\d+),(\d+))+/ )
		{
			$status = 1;
		}
	}
	return $status;
}

#
sub runL4FarmRestart    # ($farm_name,$writeconf,$type)
{
	my ( $farm_name, $writeconf, $type ) = @_;

	my $algorithm   = &getFarmAlgorithm( $farm_name );
	my $fbootstatus = &getFarmBootStatus( $farm_name );
	my $output      = 0;
	my $pidfile     = "/var/run/l4sd.pid";

	if (    $algorithm eq "leastconn"
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
		&runFarmStop( $farm_name, $writeconf );
		$output = &runFarmStart( $farm_name, $writeconf );
	}

	return $output;
}

#
sub _runL4FarmRestart    # ($farm_name,$writeconf,$type)
{
	my ( $farm_name, $writeconf, $type ) = @_;

	my $algorithm   = &getFarmAlgorithm( $farm_name );
	my $fbootstatus = &getFarmBootStatus( $farm_name );
	my $output      = 0;
	my $pidfile     = "/var/run/l4sd.pid";

	if (    $algorithm eq "leastconn"
		 && $fbootstatus eq "up"
		 && $writeconf eq "false"
		 && $type eq "hot"
		 && -e $pidfile )
	{
		open FILE, "<$pidfile";
		my $pid = <FILE>;
		close FILE;
		kill '-USR1', $pid;
		$output = $?;
	}
	else
	{
		&_runFarmStop( $farm_name, $writeconf );
		$output = &_runFarmStart( $farm_name, $writeconf );
	}

	return $output;
}

#
sub sendL4ConfChange    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $algorithm   = &getFarmAlgorithm( $farm_name );
	my $fbootstatus = &getFarmBootStatus( $farm_name );
	my $output      = 0;
	my $pidfile     = "/var/run/l4sd.pid";

	if ( $algorithm eq "leastconn" && -e "$pidfile" )
	{
		open FILE, "<$pidfile";
		my $pid = <FILE>;
		close FILE;
		kill USR1, $pid;
		$output = $?;
	}
	else
	{
		&logfile( "Running L4 restart for $farm_name" );
		&_runL4FarmRestart( $farm_name, "false", "" );
	}

	return $output;
}

#
sub setL4FarmSessionType    # ($session,$farm_name)
{
	my ( $session, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $i             = 0;

	use Tie::File;
	tie @configfile, 'Tie::File', "$configdir\/$farm_filename";

	for $line ( @configfile )
	{
		if ( $line =~ /^$farm_name\;/ )
		{
			my @args = split ( "\;", $line );
			$line =
			  "$args[0]\;$args[1]\;$args[2]\;$args[3]\;$args[4]\;$args[5]\;$session\;$args[7]\;$args[8]";
			splice @configfile, $i, $line;
			$output = $?;
		}
		$i++;
	}
	untie @configfile;
	$output = $?;

	return $output;
}

#
sub getL4FarmSessionType    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $first         = "true";

	open FI, "<$configdir/$farm_filename";

	while ( my $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line = split ( "\;", $line );
			$output = $line[6];
		}
	}
	close FI;

	return $output;
}

# set the lb algorithm to a farm
sub setL4FarmAlgorithm    # ($algorithm,$farm_name)
{
	my ( $algorithm, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $i             = 0;

	use Tie::File;
	tie @configfile, 'Tie::File', "$configdir\/$farm_filename";

	for my $line ( @configfile )
	{
		if ( $line =~ /^$farm_name\;/ )
		{
			my @args = split ( "\;", $line );
			$line =
			  "$args[0]\;$args[1]\;$args[2]\;$args[3]\;$args[4]\;$algorithm\;$args[6]\;$args[7]\;$args[8]";
			splice @configfile, $i, $line;
			$output = $?;
		}
		$i++;
	}
	untie @configfile;
	$output = $?;

	return $output;
}

#
sub getL4FarmAlgorithm    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $first         = "true";

	open FI, "<$configdir/$farm_filename";

	while ( my $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line = split ( "\;", $line );
			$output = $line[5];
		}
	}
	close FI;

	return $output;
}

# set the protocol to a L4 farm
sub setFarmProto    # ($proto,$farm_name)
{
	my ( $proto, $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	&logfile( "setting 'Protocol $proto' for $farm_name farm $farm_type" );

	if ( $farm_type eq "l4xnat" )
	{
		use Tie::File;
		tie @configfile, 'Tie::File', "$configdir\/$farm_filename";
		my $i = 0;
		for my $line ( @configfile )
		{
			if ( $line =~ /^$farm_name\;/ )
			{
				my @args = split ( "\;", $line );
				if ( $proto eq "all" )
				{
					$args[3] = "*";
				}
				if ( $proto eq "sip" )
				{
					$args[3] = "5060";    # the port by default for sip protocol
					$args[4] = "nat";
				}
				$line =
				  "$args[0]\;$proto\;$args[2]\;$args[3]\;$args[4]\;$args[5]\;$args[6]\;$args[7]\;$args[8]";
				splice @configfile, $i, $line;
				$output = $?;
			}
			$i++;
		}
		untie @configfile;
		$output = $?;
	}

	return $output;
}

#
sub getFarmProto    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	if ( $farm_type eq "l4xnat" )
	{
		open FI, "<$configdir/$farm_filename";
		my $first = "true";
		while ( $line = <FI> )
		{
			if ( $line ne "" && $first eq "true" )
			{
				$first = "false";
				my @line = split ( "\;", $line );
				$output = $line[1];
			}
		}
		close FI;
	}

	return $output;
}

#
sub getFarmNatType    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	if ( $farm_type eq "l4xnat" )
	{
		open FI, "<$configdir/$farm_filename";
		my $first = "true";
		while ( $line = <FI> )
		{
			if ( $line ne "" && $first eq "true" )
			{
				$first = "false";
				my @line = split ( "\;", $line );
				$output = $line[4];
			}
		}
		close FI;
	}

	return $output;
}

# set the NAT type for a farm
sub setFarmNatType    # ($nat,$farm_name)
{
	my ( $nat, $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	&logfile( "setting 'NAT type $nat' for $farm_name farm $farm_type" );

	if ( $farm_type eq "l4xnat" )
	{
		use Tie::File;
		tie @configfile, 'Tie::File', "$configdir\/$farm_filename";
		my $i = 0;
		for $line ( @configfile )
		{
			if ( $line =~ /^$farm_name\;/ )
			{
				my @args = split ( "\;", $line );
				$line =
				  "$args[0]\;$args[1]\;$args[2]\;$args[3]\;$nat\;$args[5]\;$args[6]\;$args[7]\;$args[8]";
				splice @configfile, $i, $line;
				$output = $?;
			}
			$i++;
		}
		untie @configfile;
		$output = $?;
	}

	return $output;
}

# set client persistence to a farm
sub setL4FarmPersistence    # ($persistence,$farm_name)
{
	my ( $persistence, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $i             = 0;

	use Tie::File;
	tie @configfile, 'Tie::File', "$configdir\/$farm_filename";

	for my $line ( @configfile )
	{
		if ( $line =~ /^$farm_name\;/ )
		{
			my @args = split ( "\;", $line );
			$line =
			  "$args[0]\;$args[1]\;$args[2]\;$args[3]\;$args[4]\;$args[5]\;$persistence\;$args[7]\;$args[8]";
			splice @configfile, $i, $line;
			$output = $?;
		}
		$i++;
	}
	untie @configfile;
	$output = $?;

	return $output;
}

#
sub getL4FarmPersistence    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $persistence   = -1;
	my $first         = "true";

	open FI, "<$configdir/$farm_filename";

	while ( my $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line = split ( "\;", $line );
			$persistence = $line[6];
		}
	}
	close FI;

	return $persistence;
}

# set the max clients of a farm
sub setL4FarmMaxClientTime    # ($track,$farm_name)
{
	my ( $track, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $i             = 0;

	use Tie::File;
	tie @configfile, 'Tie::File', "$configdir\/$farm_filename";

	for my $line ( @configfile )
	{
		if ( $line =~ /^$farm_name\;/ )
		{
			my @args = split ( "\;", $line );
			$line =
			  "$args[0]\;$args[1]\;$args[2]\;$args[3]\;$args[4]\;$args[5]\;$args[6]\;$track\;$args[8]";
			splice @configfile, $i, $line;
			$output = $?;
		}
		$i++;
	}
	untie @configfile;
	$output = $?;

	return $output;
}

#
sub getL4FarmMaxClientTime    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $first         = "true";
	my @max_client_time;

	open FI, "<$configdir/$farm_filename";

	while ( my $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line = split ( "\;", $line );
			@max_client_time = $line[7];
		}
	}
	close FI;

	return @max_client_time;
}

#
sub getL4FarmServers    # ($farm_name)
{
	my $farm_name = shift;

	my $farm_filename = &getFarmFile( $farm_name );
	my $sindex        = 0;
	my @servers;

	open FI, "<$configdir/$farm_filename";

	while ( my $line = <FI> )
	{
		if ( $line =~ /^\;server\;/ )
		{
			$line =~ s/^\;server/$sindex/g;    #, $line;
			push ( @servers, $line );
			$sindex = $sindex + 1;
		}
	}
	close FI;

	return @servers;
}

#
sub getL4BackendEstConns    # ($farm_name,$ip_backend,@netstat)
{
	my ( $farm_name, $ip_backend, @netstat ) = @_;

	my $fvip  = &getFarmVip( "vip",  $farm_name );
	my $fvipp = &getFarmVip( "vipp", $farm_name );
	my $proto = &getFarmProto( $farm_name );
	my $nattype   = &getFarmNatType( $farm_name );
	my @fportlist = &getFarmPortList( $fvipp );
	my $regexp    = "";
	my @nets      = ();

	if ( $fportlist[0] !~ /\*/ )
	{
		$regexp = "\(" . join ( '|', @fportlist ) . "\)";
	}
	else
	{
		$regexp = "\.*";
	}

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
sub getL4FarmEstConns    # ($farm_name,@netstat)
{
	my ( $farm_name, @netstat ) = @_;

	my $proto     = &getFarmProto( $farm_name );
	my $nattype   = &getFarmNatType( $farm_name );
	my $fvip      = &getFarmVip( "vip", $farm_name );
	my $fvipp     = &getFarmVip( "vipp", $farm_name );
	my @fportlist = &getFarmPortList( $fvipp );
	my $regexp    = "";
	my @nets      = ();

	if ( $fportlist[0] !~ /\*/ )
	{
		$regexp = "\(" . join ( '|', @fportlist ) . "\)";
	}
	else
	{
		$regexp = "\.*";
	}

	my @content = &getFarmBackendStatusCtl( $farm_name );
	my @backends = &getFarmBackendsStatus( $farm_name, @content );

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

sub getL4BackendTWConns    # ($farm_name,$ip_backend,@netstat)
{
	my ( $farm_name, $ip_backend, @netstat ) = @_;

	my $fvip  = &getFarmVip( "vip",  $farm_name );
	my $fvipp = &getFarmVip( "vipp", $farm_name );
	my $proto = &getFarmProto( $farm_name );
	my $nattype   = &getFarmNatType( $farm_name );
	my @fportlist = &getFarmPortList( $fvipp );
	my $regexp    = "";
	my @nets      = ();

	if ( $fportlist[0] !~ /\*/ )
	{
		$regexp = "\(" . join ( '|', @fportlist ) . "\)";
	}
	else
	{
		$regexp = "\.*";
	}

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
sub getL4BackendSYNConns    # ($farm_name,$ip_backend,@netstat)
{
	my ( $farm_name, $ip_backend, @netstat ) = @_;

	my $proto     = &getFarmProto( $farm_name );
	my $nattype   = &getFarmNatType( $farm_name );
	my $fvipp     = &getFarmVip( "vipp", $farm_name );
	my @fportlist = &getFarmPortList( $fvipp );
	my $regexp    = "";
	my @nets      = ();

	if ( $fportlist[0] !~ /\*/ )
	{
		$regexp = "\(" . join ( '|', @fportlist ) . "\)";
	}
	else
	{
		$regexp = "\.*";
	}

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
sub getL4FarmSYNConns    # ($farm_name,@netstat)
{
	my ( $farm_name, @netstat ) = @_;

	my $fvip  = &getFarmVip( "vip",  $farm_name );
	my $fvipp = &getFarmVip( "vipp", $farm_name );
	my $proto = &getFarmProto( $farm_name );
	my $nattype   = &getFarmNatType( $farm_name );
	my @fportlist = &getFarmPortList( $fvipp );
	my $regexp    = "";
	my @nets      = ();

	if ( $fportlist[0] !~ /\*/ )
	{
		$regexp = "\(" . join ( '|', @fportlist ) . "\)";
	}
	else
	{
		$regexp = "\.*";
	}

	my @content = &getFarmBackendStatusCtl( $farm_name );
	my @backends = &getFarmBackendsStatus( $farm_name, @content );

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
		}
	}

	return @nets;
}

# Returns farm status
sub getL4FarmBootStatus    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = "down";
	my $first         = "true";

	open FI, "<$configdir/$farm_filename";

	while ( $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line_a = split ( "\;", $line );
			$output = $line_a[8];
			chomp ( $output );
		}
	}
	close FI;

	return $output;
}

# Start Farm rutine
sub _runL4FarmStart    # ($farm_name,$writeconf,$status)
{
	my ( $farm_name, $writeconf, $status ) = @_;

	# exit if wrong status
	return $status if ( $status == -1 );

	my $farm_filename = &getFarmFile( $farm_name );

	if ( $writeconf eq "true" )
	{
		use Tie::File;
		tie @configfile, 'Tie::File', "$configdir\/$farm_filename";
		foreach ( @configfile )
		{
			s/\;down/\;up/g;
			last;
		}
		untie @configfile;
	}

	# Apply changes online

	# Set fw rules calculating the $nattype and $protocol
	# for every server of the farm do:
	#   set mark rules for matched connections
	#   set rule for nattype
	$status = 0;
	my $nattype = &getFarmNatType( $farm_name );
	my $lbalg   = &getFarmAlgorithm( $farm_name );
	my $vip     = &getFarmVip( "vip", $farm_name );
	my $vport   = &getFarmVip( "vipp", $farm_name );
	my $vproto  = &getFarmProto( $farm_name );
	my $persist = &getFarmPersistence( $farm_name );
	my @pttl    = &getFarmMaxClientTime( $farm_name );
	my $ttl     = $pttl[0];
	my $proto   = &getL4ProtocolTransportLayer( $vproto );

	my @server_lines = &getFarmServers( $farm_name );
	&logfile( '_runL4FarmStart: @server_lines: ' . "@server_lines" );    ########
	my @tmangle;
	my @tnat;
	my @tmanglep;
	my @tsnat;
	my @traw;

	# calculate backends probability with Weight values
	my $prob = 0;
	foreach my $server_line ( @server_lines )
	{
		my @server_args = split ( "\;", $server_line );
		if ( $server_args[6] =~ /up/ )
		{
			$prob = $prob + $server_args[4];
		}
	}

	# replace port * for all the range
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
	if ( $vproto =~ /sip|ftp/ )
	{
		$status = &loadL4Modules( $vproto );
	}

	my $bestprio = 1000;
	my @srvprio;

	foreach my $server_line ( @server_lines )
	{
		# separate every argument in the line
		my @server_args = split ( "\;", $server_line );
		if ( $server_args[6] =~ /up/ || $lbalg eq "leastconn" )
		{
			# TMP: leastconn dynamic backend status check
			if ( $lbalg eq "weight" || $lbalg eq "leastconn" )
			{
				my $port = $server_args[2];
				my $rip  = $server_args[1];
				if ( $server_args[2] ne "" && $proto ne "all" )
				{
					$rip = "$rip\:$port";
				}

				# packet marking rules
				my $tag = &genIptMark(
									   $farm_name,      $lbalg,          $vip,
									   $vport,          $proto,          $server_args[0],
									   $server_args[3], $server_args[4], $prob
				);
				push ( @tmangle, $tag );

				# dnat (redirect) rules
				my $red =
				  &genIptRedirect( $farm_name, $server_args[0], $rip, $proto, $server_args[3],
								   $persist );
				push ( @tnat, $red );

				# persistence rules
				if ( $persist ne "none" )
				{
					my $tagp =
					  &genIptMarkPersist( $farm_name, $vip, $vport, $proto, $ttl, $server_args[0],
										  $server_args[3] );
					push ( @tmanglep, $tagp );
				}

				# rules for nat_type = nat
				if ( $nattype eq "nat" )
				{
					my $ntag;
					if ( $vproto eq "sip" )
					{
						$ntag =
						  &genIptSourceNat( $farm_name, $vip, $server_args[0],
											$proto, $server_args[3] );
					}
					else
					{
						$ntag =
						  &genIptMasquerade( $farm_name, $server_args[0], $proto, $server_args[3] );
					}

					push ( @tsnat, $ntag );
				}

				$prob = $prob - $server_args[4];
			}

			if ( $lbalg eq "prio" )
			{
				if ( $server_args[5] ne "" && $server_args[5] < $bestprio )
				{
					@srvprio  = @server_args;
					$bestprio = $server_args[5];
				}
			}
		}
	}

	if ( @srvprio && $lbalg eq "prio" )
	{
		system ( "echo 10 > /proc/sys/net/netfilter/nf_conntrack_udp_timeout_stream" );
		system ( "echo 5 > /proc/sys/net/netfilter/nf_conntrack_udp_timeout" );

		my $port = $srvprio[2];
		my $rip  = $srvprio[1];
		if ( $srvprio[2] ne "" )
		{
			$rip = "$rip\:$port";
		}

		# packet marking rules
		my $tag = &genIptMark(
							   $farm_name,  $lbalg,      $vip,
							   $vport,      $proto,      $srvprio[0],
							   $srvprio[3], $srvprio[4], $prob
		);
		push ( @tmangle, $tag );

		# dnat (redirect) rules
		my $red =
		  &genIptRedirect( $farm_name, $srvprio[0], $rip, $proto, $srvprio[3],
						   $persist );
		push ( @tnat, $red );

		# persistence rules
		if ( $persist ne "none" )
		{
			my $tagp =
			  &genIptMarkPersist( $farm_name, $vip, $vport, $proto, $ttl, $srvprio[0],
								  $srvprio[3] );
			push ( @tmanglep, $tagp );
		}

		if ( $nattype eq "nat" )
		{
			my $ntag;
			if ( $vproto eq "sip" )
			{
				$ntag = &genIptSourceNat( $farm_name, $vip, $srvprio[0], $proto, $srvprio[3] );
			}
			else
			{
				$ntag = &genIptMasquerade( $farm_name, $srvprio[0], $proto, $srvprio[3] );
			}
			push ( @tsnat, $ntag );
		}

	}

	foreach $nraw ( @traw )
	{
		next if !$nraw;

		&logfile( "running $nraw" );
		system ( "$nraw >/dev/null 2>&1" );
		if ( $? != 0 )
		{
			&logfile( "last command failed!" );
			$status = -1;
		}
	}

	@tmangle = reverse ( @tmangle );
	foreach $ntag ( @tmangle )
	{
		next if !$ntag;

		&logfile( "running $ntag" );
		system ( "$ntag >/dev/null 2>&1" );
		if ( $? != 0 )
		{
			&logfile( "last command failed!" );
			$status = -1;
		}
	}

	if ( $persist ne "none" )
	{
		foreach $ntag ( @tmanglep )
		{
			next if !$ntag;

			&logfile( "running $ntag" );
			system ( "$ntag >/dev/null 2>&1" );
			if ( $? != 0 )
			{
				&logfile( "last command failed!" );
				$status = -1;
			}
		}
	}

	foreach $nred ( @tnat )
	{
		next if !$nred;

		&logfile( "running $nred" );
		system ( "$nred >/dev/null 2>&1" );
		if ( $? != 0 )
		{
			&logfile( "last command failed!" );
			$status = -1;
		}
	}

	foreach $nred ( @tsnat )
	{
		next if !$nred;

		&logfile( "running $nred" );
		system ( "$nred >/dev/null 2>&1" );
		if ( $? != 0 )
		{
			&logfile( "last command failed!" );
			$status = -1;
		}
	}

	# Enable IP forwarding
	&setIpForward( "true" );

	# Enable active l4 file
	if ( $status != -1 )
	{
		open FI, ">$piddir\/$farm_name\_l4xnat.pid";
		close FI;
	}

	return $status;
}

# Stop Farm rutine
sub _runL4FarmStop    # ($farm_name,$writeconf)
{
	my ( $farm_name, $writeconf ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $status =
	  ( $writeconf eq "true" )
	  ? -1
	  : 0;

	if ( $writeconf eq "true" )
	{
		use Tie::File;
		tie @configfile, 'Tie::File', "$configdir\/$farm_filename";
		my $first = 1;
		foreach ( @configfile )
		{
			if ( $first == 1 )
			{
				s/\;up/\;down/g;
				$status = $?;
				$first  = 0;
			}
		}
		untie @configfile;
	}

	my $falg = &getFarmAlgorithm( $farm_name );

	# Apply changes online
	if ( $status != -1 )
	{
		# Disable rules
		my @allrules;

		@allrules = &getIptList( "raw", "OUTPUT" );
		$status = &deleteIptRules( "farm", $farm_name, "raw", "OUTPUT", @allrules );

		@allrules = &getIptList( "mangle", "PREROUTING" );
		$status =
		  &deleteIptRules( "farm", $farm_name, "mangle", "PREROUTING", @allrules );

		@allrules = &getIptList( "nat", "PREROUTING" );
		$status = &deleteIptRules( "farm", $farm_name, "nat", "PREROUTING", @allrules );

		@allrules = &getIptList( "nat", "POSTROUTING" );
		$status =
		  &deleteIptRules( "farm", $farm_name, "nat", "POSTROUTING", @allrules );

		# Disable active l4xnat file
		unlink ( "$piddir\/$farm_name\_l4xnat.pid" );
		if ( -e "$piddir\/$farm_name\_l4xnat.pid" )
		{
			$status = -1;
		}
	}

	return $status;
}

#
sub runL4FarmCreate    # ($vip,$farm_name)
{
	my ( $vip, $farm_name ) = @_;

	my $output    = -1;
	my $farm_type = "l4xnat";

	open FO, ">$configdir\/$farm_name\_$farm_type.cfg";
	print FO "$farm_name\;all\;$vip\;*\;dnat\;weight\;none\;120\;up\n";
	close FO;
	$output = $?;

	if ( !-e "$piddir/${farm_name}_$farm_type.pid" )
	{
		# Enable active l4xnat file
		open FI, ">$piddir\/$farm_name\_$farm_type.pid";
		close FI;
	}

	return $output;
}

# Returns farm vip
sub getL4FarmVip    # ($info,$farm_name)
{
	my ( $info, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $first         = "true";
	my $output        = -1;

	open FI, "<$configdir/$farm_filename";

	while ( my $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line_a = split ( "\;", $line );

			if ( $info eq "vip" )   { $output = $line_a[2]; }
			if ( $info eq "vipp" )  { $output = $line_a[3]; }
			if ( $info eq "vipps" ) { $output = "$line_a[2]\:$line_a[3]"; }
		}
	}
	close FI;

	return $output;
}

# Set farm virtual IP and virtual PORT
sub setL4FarmVirtualConf    # ($vip,$vip_port,$farm_name)
{
	my ( $vip, $vip_port, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $stat          = -1;
	my $i             = 0;

	use Tie::File;
	tie @configfile, 'Tie::File', "$configdir\/$farm_filename";

	for my $line ( @configfile )
	{
		if ( $line =~ /^$farm_name\;/ )
		{
			my @args = split ( "\;", $line );
			$line =
			  "$args[0]\;$args[1]\;$vip\;$vip_port\;$args[4]\;$args[5]\;$args[6]\;$args[7]\;$args[8]";
			splice @configfile, $i, $line;
			$stat = $?;
		}
		$i++;
	}
	untie @configfile;
	$stat = $?;

	return $stat;
}

#
sub setL4FarmServer    # ($ids,$rip,$port,$weight,$priority,$farm_name)
{
	my ( $ids, $rip, $port, $weight, $priority, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $end           = "false";
	my $i             = 0;
	my $l             = 0;

	tie my @contents, 'Tie::File', "$configdir\/$farm_filename";

	foreach my $line ( @contents )
	{
		if ( $line =~ /^\;server\;/ && $end ne "true" )
		{
			if ( $i eq $ids )
			{
				my @aline = split ( "\;", $line );
				my $dline = "\;server\;$rip\;$port\;$aline[4]\;$weight\;$priority\;up\n";

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
		my $mark = &getNewMark( $farm_name );
		push ( @contents, "\;server\;$rip\;$port\;$mark\;$weight\;$priority\;up\n" );
		$output = $?;
	}
	untie @contents;

	return $output;
}

#
sub runL4FarmServerDelete    # ($ids,$farm_name)
{
	my ( $ids, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $end           = "false";
	my $i             = 0;
	my $l             = 0;

	tie my @contents, 'Tie::File', "$configdir\/$farm_filename";

	foreach my $line ( @contents )
	{
		if ( $line =~ /^\;server\;/ && $end ne "true" )
		{
			if ( $i eq $ids )
			{
				my @sdata = split ( "\;", $line );

				#~ my $mark = &delMarks( "", @sdata[4] ); ## used??

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
sub getL4FarmBackendsStatus    # ($farm_name,@content)
{
	my ( $farm_name, @content ) = @_;

	my @backends_data;

	foreach my $server ( @content )
	{
		my @serv = split ( "\;", $server );
		my $port = $serv[3];
		if ( $port eq "" )
		{
			$port = &getFarmVip( "vipp", $farm_name );
		}
		push ( @backends_data, "$serv[2]\;$port\;$serv[5]\;$serv[6]\;$serv[7]" );
	}

	return @backends_data;
}

sub setL4FarmBackendStatus    # ($farm_name,$index,$stat)
{
	my ( $farm_name, $index, $stat ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );

	# check output !!!
	#	my $output   = -1;
	my $fileid   = 0;
	my $serverid = 0;

	# load farm configuration file
	use Tie::File;
	tie my @configfile, 'Tie::File', "$configdir\/$farm_filename";

	# look for $index backend
	foreach my $line ( @configfile )
	{
		if ( $line =~ /\;server\;/ )
		{
			if ( $serverid eq $index )
			{
				# change status in configuration file
				my @lineargs = split ( "\;", $line );
				@lineargs[7] = $stat;
				@configfile[$fileid] = join ( "\;", @lineargs );
			}
			$serverid++;
		}
		$fileid++;
	}
	untie @configfile;

	#	return $output;
}

sub getFarmPortList    # ($fvipp)
{
	my $fvipp = shift;
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
				for ( my $i = $intlimits[0] ; $i <= $intlimits[1] ; $i++ )
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
sub getL4FarmBackendStatusCtl    # ($farm_name)
{
	my $farm_name = shift;

	my $farm_filename = &getFarmFile( $farm_name );
	my @output;

	tie my @content, 'Tie::File', "$configdir\/$farm_filename";
	@output = grep /^\;server\;/, @content;
	untie @content;

	return @output;
}

#function that renames a farm
sub setL4NewFarmName    # ($farm_name,$new_farm_name)
{
	my ( $farm_name, $new_farm_name ) = @_;

	my $farm_filename     = &getFarmFile( $farm_name );
	my $farm_type         = &getFarmType( $farm_name );
	my $new_farm_filename = "$new_farm_name\_$farm_type.cfg";
	my $output            = -1;
	my $status            = &getFarmStatus( $farm_name );

	# stop farm if it was up
	&runFarmStop( $farm_name, "false" ) if ( $status eq 'up' );

	use Tie::File;
	tie @configfile, 'Tie::File', "$configdir\/$farm_filename";

	for ( @configfile )
	{
		s/^$farm_name\;/$new_farm_name\;/g;
	}
	untie @configfile;

	rename ( "$configdir\/$farm_filename", "$configdir\/$new_farm_filename" );
	rename ( "$piddir\/$farm_name\_$farm_type.pid",
			 "$piddir\/$new_farm_name\_$farm_type.pid" );
	$output = $?;

	# Rename fw marks for this farm
	&renameMarks( $farm_name, $new_farm_name );

	# start farm if it was up before
	&runFarmStart( $new_farm_name, "false" ) if ( $status eq 'up' );
	$output = $?;

	return $output;
}

sub getL4ProtocolTransportLayer
{
	my $vproto = shift;

	return
	    ( $vproto =~ /sip|tftp/ ) ? 'udp'
	  : ( $vproto eq 'ftp' )      ? 'tcp'
	  :                             $vproto;
}

# do not remove this
1
