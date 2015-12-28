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

use Data::Dumper;

#
sub getL4FarmsPorts    # ($farm_type)
{
	my $farm_type = shift;

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
	my $protocol = shift;

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
		&_runL4FarmStop( $farm_name, $writeconf );
		$output = &_runL4FarmStart( $farm_name, $writeconf );
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

		# reload config file
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
	my $farm_name = shift;

	my $algorithm   = &getFarmAlgorithm( $farm_name );
	my $fbootstatus = &getFarmBootStatus( $farm_name );
	my $output      = 0;
	my $pidfile     = "/var/run/l4sd.pid";

	if ( $algorithm eq "leastconn" && -e "$pidfile" )
	{
		# read pid number
		open my $file, "<", "$pidfile";
		my $pid = <$file>;
		close $file;

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

# Persistence mode
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

	my $farm = &getL4FarmStruct( $farm_name );

	if ( $$farm{ status } eq 'up' && $$farm{ lbalg } ne 'prio' )
	{
		my @rules;

		foreach my $server ( @{ $$farm{ servers } } )
		{
			my $rule = &genIptMarkPersist( $farm, $server );

			$rule = ( $$farm{ persist } eq 'none' )
			  ? &getIptRuleDelete( $rule )    # delete
			  : &getIptRuleInsert( $farm, $server, $rule );    # insert second
			push ( @rules, $rule );                            # collect rule
		}

		$output = &applyIptRules( @rules );
	}

	return $output;
}

#
sub getL4FarmSessionType                                       # ($farm_name)
{
	my $farm_name = shift;

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
	my $prev_alg      = getL4FarmAlgorithm( $farm_name );    # previous algorithm

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

	my $farm = &getL4FarmStruct( $farm_name );

	if ( $$farm{ status } eq 'up' )
	{
		my @rules;

		my $prio_server = &getL4ServerWithLowestPriority( $farm );

		foreach my $server ( @{ $$farm{ servers } } )
		{
			my $rule;

			# weight    => leastconn or (many to many)
			# leastconn => weight
			if (    ( $prev_alg eq 'weight' && $$farm{ lbalg } eq 'leastconn' )
				 || ( $prev_alg eq 'leastconn' && $$farm{ lbalg } eq 'weight' ) )
			{
				# replace packet marking rules
				# every thing else stays the same way
				$rule = &genIptMark( $farm, $server );
				my $rule_num = &getIptRuleNumber( $rule, $$farm{ name }, $$server{ id } );

				$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );
				&applyIptRules( $rule );

				if ( $$farm{ persist } ne 'none' )    # persistence
				{
					$rule = &genIptMarkPersist( $farm, $server );
					$rule_num = &getIptRuleNumber( $rule, $$farm{ name }, $$server{ id } );
					$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );
					&applyIptRules( $rule );
				}
			}

			# prio => weight or (one to many)
			# prio => leastconn
			elsif ( ( $$farm{ lbalg } eq 'weight' || $$farm{ lbalg } eq 'leastconn' )
					&& $prev_alg eq 'prio' )
			{
				$rule = &genIptMark( $farm, $server );
				my $rule_num = &getIptRuleNumber( $rule, $$farm{ name }, $$server{ id } );

				# start not started servers
				if ( $rule_num == -1 )    # no rule was found
				{
					&_runL4ServerStart( $$farm{ name }, $$server{ id } );
					$rule = undef;        # changes are already done
				}

				# refresh already started server
				else
				{
					$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );   # replace if found
				}
				&applyIptRules( $rule ) if defined ( $rule );
			}

			# weight    => prio or (many to one)
			# leastconn => prio
			elsif ( ( $prev_alg eq 'weight' || $prev_alg eq 'leastconn' )
					&& $$farm{ lbalg } eq 'prio' )
			{
				$rule = &genIptMark( $farm, $server );
				my $rule_num = &getIptRuleNumber( $rule, $$farm{ name }, $$server{ id } );

				#
				if ( $server == $prio_server )    # no rule was found
				{
					$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );   # replace if found
				}
				else
				{
					&_runL4ServerStop( $$farm{ name }, $$server{ id } );
					$rule = undef;    # changes are already done
				}
			}
		}
	}

	return;

	#~ return $output;
}

#
sub getL4FarmAlgorithm                # ($farm_name)
{
	my $farm_name = shift;

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
		tie @configfile, 'Tie::File', "$configdir\/$farm_filename" or return $output;
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
					#~ $args[3] = "5060";    # the port by default for sip protocol
					$args[4] = "nat";
				}
				$line =
				  "$args[0]\;$proto\;$args[2]\;$args[3]\;$args[4]\;$args[5]\;$args[6]\;$args[7]\;$args[8]";
				splice @configfile, $i, $line;

				&logfile( "setFarmProto >> line:$line" );
			}
			$i++;
		}
		untie @configfile or return $output;
	}

	my $farm = &getL4FarmStruct( $farm_name );

	if ( $$farm{ status } eq 'up' )
	{
		&logfile( "setFarmProto >> farm is UP" );

		$output = &refreshL4FarmRules( $farm );
	}

	return;    # $output;
}

#
sub getFarmProto    # ($farm_name)
{
	my $farm_name = shift;

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
	my $farm_name = shift;

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

	my $farm = &getL4FarmStruct( $farm_name );

	if ( $$farm{ status } eq 'up' )
	{
		my @rules;

		foreach my $server ( @{ $$farm{ servers } } )
		{
			my $rule;

			# get the rule 'template'
			$rule = ( $$farm{ vproto } eq 'sip' )
			  ? &genIptSourceNat( $farm, $server )    # SIP protocol
			  : &genIptMasquerade( $farm, $server );  # Masq otherwise

			# apply the desired action to the rule template
			$rule = ( $$farm{ nattype } eq 'nat' )
			  ? &getIptRuleAppend( $rule )            # append for SNAT aka NAT
			  : &getIptRuleDelete( $rule );           # delete for DNAT

			push ( @rules, $rule );                   # collect rule
		}

		$output = &applyIptRules( @rules );
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

	my $farm = &getL4FarmStruct( $farm_name );

	if ( $farm{ status } eq 'up' && $farm{ lbalg } ne 'prio' )
	{
		my @rules;

		foreach my $server ( $farm{ servers } )
		{
			my $rule = &genIptMarkPersist( $farm, $server );

			$rule = ( $$farm{ persist } eq 'none' )
			  ? &getIptRuleDelete( $rule )    # delete
			  : &getIptRuleInsert( $farm, $server, $rule );    # insert second
			push ( @rules, $rule );                            # collect rule
		}

		$output = &applyIptRules( @rules );
	}

	return $output;
}

#
sub getL4FarmPersistence                                       # ($farm_name)
{
	my $farm_name = shift;

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

	my $farm = &getL4FarmStruct( $farm_name );

	if (    $$farm{ status } eq 'up'
		 && $$farm{ lbalg } ne 'prio'
		 && $$farm{ persist } eq 'ip' )
	{
		my @rules;

		foreach my $server ( @{ $$farm{ servers } } )
		{
			my $rule = &genIptMarkPersist( $farm, $server );
			my $rule_num = &getIptRuleNumber( $rule, $$farm{ name }, $$server{ id } );

			$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );

			push ( @rules, $rule );    # collect rule
		}

		$output = &applyIptRules( @rules );
	}

	return $output;
}

#
sub getL4FarmMaxClientTime             # ($farm_name)
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
			$sindex++;
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
	my $farm_name = shift;

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
	my $farm_name = shift;    # input
	my $writeconf = shift;    # input
	my $status    = shift;    # input

	# initialize a farm struct
	my $farm = &getL4FarmStruct( $farm_name );

	# exit if wrong status
	return $status if ( $status == -1 );

	if ( $writeconf eq "true" )
	{
		use Tie::File;
		tie @configfile, 'Tie::File', "$configdir\/$$farm{ filename }";
		foreach ( @configfile )
		{
			s/\;down/\;up/g;
			last;
		}
		untie @configfile;
	}

	$status = 0;

	# Load L4 scheduler if needed
	if ( $$farm{ lbalg } eq 'leastconn' && -e "$l4sd" )
	{
		system ( "$l4sd & >/dev/null" );
	}

	# Load required modules
	if ( $$farm{ vport } =~ /sip|ftp/ )
	{
		$status = &loadL4Modules( $$farm{ vproto } );
	}

	# calculate backends probability with Weight values
	&getL4BackendsWeightProbability( $farm );

	my $rules = &getIptRulesStruct();

	my $lowest_prio;
	my $server_prio;    # reference to the selected server for prio algorithm

	foreach my $server ( @{ $$farm{ servers } } )
	{
		# go to next cycle if server must not be up or not a least connection algorithm
		next
		  if not (    $$server{ status } =~ /up|maintenance/
				   || $$farm{ lbalg } eq 'leastconn' );

		# TMP: leastconn dynamic backend status check
		if ( $$farm{ lbalg } =~ /weight|leastconn/ )
		{
			&getL4ServerActionRules( $farm, $server, 'on', $rules );
		}
		elsif ( $$farm{ lbalg } eq 'prio' )
		{
			# find the lowest priority server
			if ( $$server{ priority } ne ''
				 && ( $$server{ priority } < $lowest_prio || !defined $lowest_prio ) )
			{
				$server_prio = $server;
				$lowest_prio = $$server{ priority };
			}
		}
	}

	# prio only apply rules to one server
	if ( $server_prio && $$farm{ lbalg } eq 'prio' )
	{
		system ( "echo 10 > /proc/sys/net/netfilter/nf_conntrack_udp_timeout_stream" );
		system ( "echo 5 > /proc/sys/net/netfilter/nf_conntrack_udp_timeout" );

		&getL4ServerActionRules( $farm, $server_prio, 'on', $rules );
	}

 #~ &logfile( 'dumping rules scruct : ' . Dumper( \%rules ) );   ###################

	# first insert the save rule, then insert on top the restore rule
	&setIptConnmarkSave( 'true' );
	&setIptConnmarkRestore( 'true' );

	# persistence rules if wanted
	# NOTE: persistance must be done before tagging
	$status = &applyIptRules( @{ $$rules{ t_mangle_p } } )
	  if ( $persist ne 'none' );
	$status = &applyIptRules( @{ $$rules{ t_mangle } } );
	$status = &applyIptRules( @{ $$rules{ t_nat } } );
	&applyIptRules( @{ $$rules{ t_snat } } );

	&logfile( "_runL4FarmStart: status => $status" );

	# Enable IP forwarding
	&setIpForward( 'true' );

	# Enable active l4 file
	if ( $status != -1 )
	{
		open FI, ">$piddir\/$$farm{name}\_l4xnat.pid";
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

	# Apply changes online
	if ( $status != -1 )
	{
		# Disable rules
		my @allrules;

		@allrules = &getIptList( "mangle", "PREROUTING" );
		$status =
		  &deleteIptRules( "farm", $farm_name, "mangle", "PREROUTING", @allrules );

		@allrules = &getIptList( "nat", "PREROUTING" );
		$status = &deleteIptRules( "farm", $farm_name, "nat", "PREROUTING", @allrules );

		@allrules = &getIptList( "nat", "POSTROUTING" );
		$status =
		  &deleteIptRules( "farm", $farm_name, "nat", "POSTROUTING", @allrules );

		&setIptConnmarkRestore();    # new
		&setIptConnmarkSave();       # new

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
	my $farm_type = 'l4xnat';

	open FO, ">$configdir\/$farm_name\_$farm_type.cfg";
	print FO "$farm_name\;tcp\;$vip\;80\;nat\;weight\;none\;120\;up\n";
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

	my $farm = &getL4FarmStruct( $farm_name );

	if ( $$farm{ status } eq 'up' )
	{
		my @rules;

		foreach my $server ( @{ $$farm{ servers } } )
		{
			my $rule = &genIptMark( $farm, $server );
			my $rule_num = &getIptRuleNumber( $rule, $$farm{ name }, $$server{ id } );

			$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );

			push ( @rules, $rule );    # collect rule

			if ( $$farm{ persist } eq 'ip' )
			{
				$rule = &genIptMarkPersist( $farm, $server );
				$rule_num = &getIptRuleNumber( $rule, $$farm{ name }, $$server{ id } );

				$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );

				push ( @rules, $rule );    # collect rule
			}
		}

		$output = &applyIptRules( @rules );
	}

	return $stat;
}

# Edit a server/backend or add a new one if the id is not found
sub setL4FarmServer    # ($ids,$rip,$port,$weight,$priority,$farm_name)
{
	my ( $ids, $rip, $port, $weight, $priority, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;                           # output: error code
	my $found_server  = 'false';
	my $i             = 0;                            # server ID
	my $l             = 0;                            # line index

	tie my @contents, 'Tie::File', "$configdir\/$farm_filename";

	# edit the backed line if found
	foreach my $line ( @contents )
	{
		if ( $line =~ /^\;server\;/ && $found_server eq 'false' )
		{
			if ( $i eq $ids )
			{
				my @aline = split ( ';', $line );
				my $dline = "\;server\;$rip\;$port\;$aline[4]\;$weight\;$priority\;up\n";

				splice @contents, $l, 1, $dline;
				$output       = $?;
				$found_server = 'true';
			}
			else
			{
				$i++;
			}
		}
		$l++;
	}

	# add a new backend if not found
	if ( $found_server eq 'false' )
	{
		my $mark = &getNewMark( $farm_name );
		push ( @contents, "\;server\;$rip\;$port\;$mark\;$weight\;$priority\;up\n" );
		$output = $?;
	}
	untie @contents;
	### end editing config file ###

	my $farm = &getL4FarmStruct( $farm_name );    # FIXME: start using it earlier

	# enabling new server
	if ( $found_server eq 'false' )
	{
		if ( $$farm{ lbalg } eq 'weight' || $$farm{ lbalg } eq 'leastconn' )
		{
			&_runL4ServerStart( $farm_name, $ids );
		}
	}

	&refreshL4FarmRules( $farm );

	return $output;
}

#
sub runL4FarmServerDelete    # ($ids,$farm_name)
{
	my ( $ids, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $found_server  = 'false';
	my $i             = 0;
	my $l             = 0;

	my $farm = &getL4FarmStruct( $farm_name );    # yay

	if ( $$farm{ lbalg } eq 'weight' || $$farm{ lbalg } eq 'leastconn' )
	{
		&_runL4ServerStop( $farm_name, $ids );
	}

	tie my @contents, 'Tie::File', "$configdir\/$farm_filename";

	foreach my $line ( @contents )
	{
		if ( $line =~ /^\;server\;/ && $found_server eq 'false' )
		{
			if ( $i eq $ids )
			{
				my @sdata = split ( "\;", $line );

				splice @contents, $l, 1,;

				$output       = $?;
				$found_server = 'true';
			}
			else
			{
				$i++;
			}
		}
		$l++;
	}
	untie @contents;

	# enabling new server
	if ( $found_server eq 'true' )
	{
		splice @{ $$farm{ servers } }, $ids, 1;    # remove server from structure

		if ( $$farm{ lbalg } eq 'weight' || $$farm{ lbalg } eq 'prio' )
		{
			&refreshL4FarmRules( $farm );
		}
	}

	return $output;
}

#function that return the status information of a farm:
#ip, port, backendstatus, weight, priority, clients
sub getL4FarmBackendsStatus    # ($farm_name,@content)
{
	my ( $farm_name, @content ) = @_;

	my @backends_data;         # output

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

sub setL4FarmBackendStatus    # ($farm_name,$server_id,$status)
{
	my ( $farm_name, $server_id, $status ) = @_;

	my %farm = %{ &getL4FarmStruct( $farm_name ) };

	my $output   = -1;
	my $line_num = 0;         # line index tracker
	my $serverid = 0;         # server index tracker

	&logfile(
		"setL4FarmBackendStatus(farm_name:$farm_name,server_id:$server_id,status:$status)"
	);                        ###

	my $off_maintenance = 0;  # false by default

	if ( $farm{ servers }[server_id]{ status } eq 'maintenance' && $status eq 'up' )
	{
		$off_maintenance = 1;    # make it true
	}

	# load farm configuration file
	use Tie::File;
	tie my @configfile, 'Tie::File', "$configdir\/$farm{filename}";

	# look for $server_id backend
	foreach my $line ( @configfile )
	{
		if ( $line =~ /\;server\;/ )
		{
			if ( $serverid eq $server_id )
			{
				# change status in configuration file
				my @lineargs = split ( "\;", $line );
				@lineargs[7] = $status;
				@configfile[$line_num] = join ( "\;", @lineargs );
			}
			$serverid++;
		}
		$line_num++;
	}
	untie @configfile;

	%farm = %{ &getL4FarmStruct( $farm_name ) };

	if ( $status eq 'up' )
	{
		if ( !$off_maintenance )
		{
			$output = &_runL4ServerStart( $farm{ name }, $server_id );
		}

		&refreshL4FarmRules( \%farm );
	}
	elsif ( $status =~ /down|maintenance/ )
	{
		&logfile(
			"setL4FarmBackendStatus(farm_name:$farm_name,server_id:$server_id,status:$status) => status:$farm{servers}[server_id]{ status }"
		);

		&refreshL4FarmRules( \%farm );

		if ( $status ne 'maintenance' )
		{
			$output = &_runL4ServerStop( $farm{ name }, $server_id );
		}
	}
	else
	{
		&logfile( "Backend status requested no recognized: $status" );
	}

	return $output;
}

sub getFarmPortList    # ($fvipp)
{
	my $fvipp = shift;

	my @portlist = split ( ",", $fvipp );
	my $port;
	my @retportlist = ();

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

# returns backends lines
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

	# previous farm info
	my $prev_farm = &getL4FarmStruct( $farm_name );

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

	my @rules;
	my $farm        = &getL4FarmStruct( $new_farm_name );
	my $prio_server = &getL4ServerWithLowestPriority( $$farm{ name } )
	  if ( $$farm{ lbalg } eq 'prio' );

	# refresh backends probability values
	&getL4BackendsWeightProbability( $farm ) if ( $$farm{ lbalg } eq 'weight' );

	# get new rules
	foreach my $server ( @{ $$farm{ servers } } )
	{
		# skip cycle for servers not running
		next if ( $$server{ status } !~ /up|maintenance/ );

		next if ( $$farm{ lbalg } eq 'prio' && $$server{ id } != $$prio_server{ id } );

		my $rule;
		my $rule_num;

		# refresh marks
		$rule = &genIptMark( $prev_farm, $server );

		$rule_num =
		  ( $$farm{ lbalg } eq 'prio' )
		  ? &getIptRuleNumber( $rule, $$prev_farm{ name } )
		  : &getIptRuleNumber( $rule, $$prev_farm{ name }, $$server{ id } );
		$rule = &genIptMark( $farm, $server );
		$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );
		push ( @rules, $rule );

		if ( $$farm{ persist } ne 'none' )    # persistence
		{
			$rule = &genIptMarkPersist( $prev_farm, $server );
			$rule_num =
			  ( $$farm{ lbalg } eq 'prio' )
			  ? &getIptRuleNumber( $rule, $$prev_farm{ name } )
			  : &getIptRuleNumber( $rule, $$prev_farm{ name }, $$server{ id } );
			$rule = &genIptMarkPersist( $farm, $server );
			$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );
			push ( @rules, $rule );
		}

		# redirect
		$rule = &genIptRedirect( $prev_farm, $server );
		$rule_num =
		  ( $$farm{ lbalg } eq 'prio' )
		  ? &getIptRuleNumber( $rule, $$prev_farm{ name } )
		  : &getIptRuleNumber( $rule, $$prev_farm{ name }, $$server{ id } );
		$rule = &genIptRedirect( $farm, $server );
		$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );
		push ( @rules, $rule );

		if ( $$farm{ nattype } eq 'nat' )    # nat type = nat
		{
			if ( $$farm{ vproto } eq 'sip' )
			{
				$rule = &genIptSourceNat( $prev_farm, $server );
			}
			else
			{
				$rule = &genIptMasquerade( $prev_farm, $server );
			}

			$rule_num =
			  ( $$farm{ lbalg } eq 'prio' )
			  ? &getIptRuleNumber( $rule, $$prev_farm{ name } )
			  : &getIptRuleNumber( $rule, $$prev_farm{ name }, $$server{ id } );

			if ( $$farm{ vproto } eq 'sip' )
			{
				$rule = &genIptSourceNat( $farm, $server );
			}
			else
			{
				$rule = &genIptMasquerade( $farm, $server );
			}

			$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );
			push ( @rules, $rule );
		}
	}

	# apply new rules
	return &applyIptRules( @rules );
}

sub getL4ProtocolTransportLayer
{
	my $vproto = shift;

	return
	    ( $vproto =~ /sip|tftp/ ) ? 'udp'
	  : ( $vproto eq 'ftp' )      ? 'tcp'
	  :                             $vproto;
}

########################## new l4 functions ###########################

sub getL4FarmStruct
{
	my %farm;    # declare output hash

	$farm{ name } = shift;    # input: farm name

	$farm{ filename } = &getFarmFile( $farm{ name } );                # not used yet
	$farm{ nattype }  = &getFarmNatType( $farm{ name } );
	$farm{ lbalg }    = &getFarmAlgorithm( $farm{ name } );
	$farm{ vip }      = &getFarmVip( 'vip', $farm{ name } );
	$farm{ vport }    = &getFarmVip( 'vipp', $farm{ name } );
	$farm{ vproto }   = &getFarmProto( $farm{ name } );
	$farm{ persist }  = &getFarmPersistence( $farm{ name } );
	$farm{ ttl }      = ( &getFarmMaxClientTime( $farm{ name } ) )[0];
	$farm{ proto }   = &getL4ProtocolTransportLayer( $farm{ vproto } );
	$farm{ status }  = &getFarmStatus( $farm{ name } );
	$farm{ servers } = [];

	foreach my $server_line ( &getFarmServers( $farm{ name } ) )
	{
		push ( @{ $farm{ servers } }, &getL4ServerStruct( \%farm, $server_line ) );
	}

	# replace port * for all the range
	if ( $farm{ vport } eq '*' )
	{
		$farm{ vport } = '0:65535';
	}

	if ( $farm{ lbalg } eq 'weight' )
	{
		&getL4BackendsWeightProbability( \%farm );
	}

	return \%farm;    # return a hash reference
}

sub getL4ServerStruct
{
	my $farm        = shift;
	my $server_line = shift;    # input example: ;0;192.168.101.252;80;0x20a;1;1;up

	my @server_args = split ( "\;", $server_line );    # split server line
	chomp ( @server_args );

	# server args example: ( 0, 192.168.101.252, 80, 0x20a, 1, 1 ,up )
	my %server;                                        # output hash

	$server{ id }       = shift @server_args;          # input 0
	$server{ vip }      = shift @server_args;          # input 1
	$server{ vport }    = shift @server_args;          # input 2
	$server{ tag }      = shift @server_args;          # input 3
	$server{ weight }   = shift @server_args;          # input 4
	$server{ priority } = shift @server_args;          # input 5
	$server{ status }   = shift @server_args;          # input 6
	$server{ rip }      = $server{ vip };

	if ( $server{ vport } ne '' && $$farm{ proto } ne 'all' )
	{
		chomp ( $server{ rip } = "$server{vip}\:$server{vport}" );
	}

	return \%server;                                   # return reference
}

sub doL4FarmProbability
{
	my $farm = shift;                                  # input: farm reference

	$$farm{ prob } = 0;

	foreach my $server_ref ( @{ $$farm{ servers } } )
	{
		if ( $$server_ref{ status } eq 'up' )
		{
			$$farm{ prob } += $$server_ref{ weight };
		}
	}
	&logfile( "doL4FarmProbability($$farm{ name }) => prob:$$farm{ prob }" )
	  ;                                                ##############
}

sub getL4ServerActionRules
{
	my $farm   = shift;    # input: farm reference
	my $server = shift;    # input: server reference
	my $switch = shift;    # input: on/off
	my $rules  = shift;    # input/output: reference to rules hash structure

	my $rule;

	## packet marking rules ##
	$rule = &genIptMark( $farm, $server );

	$rule = ( $switch eq 'off' )
	  ? &getIptRuleDelete( $rule )    # delete
	  : &getIptRuleInsert( $farm, $server, $rule );    # insert second

	push ( @{ $$rules{ t_mangle } }, $rule );          # collect rule

	## persistence rules ##
	if ( $$farm{ persist } ne 'none' )
	{
		$rule = &genIptMarkPersist( $farm, $server );

		$rule = ( $switch eq 'off' )
		  ? &getIptRuleDelete( $rule )                 # delete
		  : &getIptRuleInsert( $farm, $server, $rule );    # insert second
		push ( @{ $$rules{ t_mangle_p } }, $rule );        # collect rule
	}

	## dnat (redirect) rules ##
	$rule = &genIptRedirect( $farm, $server );

	$rule = ( $switch eq 'off' )
	  ? &getIptRuleDelete( $rule )                         # delete
	  : &getIptRuleAppend( $rule );

	push ( @{ $$rules{ t_nat } }, $rule );                 # collect rule

	## rules for source nat or nat ##
	if ( $$farm{ nattype } eq 'nat' )
	{
		if ( $$farm{ vproto } eq 'sip' )
		{
			$rule = &genIptSourceNat( $farm, $server );
		}
		else
		{
			$rule = &genIptMasquerade( $farm, $server );
		}

		$rule = ( $switch eq 'off' )
		  ? &getIptRuleDelete( $rule )    # delete
		  : &getIptRuleAppend( $rule );
		push ( @{ $$rules{ t_snat } }, $rule );    # collect rule
	}

	return;
}

# Start Farm rutine
# called from setL4FarmBackendStatus($farm_name,$server_id,$status)
sub _runL4ServerStart    # ($farm_name,$server_id)
{
	my $farm_name = shift;    # input: farm name string
	my $server_id = shift;    # input: server id number

	# initialize a farm struct
	my %farm   = %{ &getL4FarmStruct( $farm_name ) };
	my %server = %{ $farm{ servers }[$server_id] };
	my %rules  = %{ &getIptRulesStruct() };

	&getL4ServerActionRules( \%farm, \%server, 'on', \%rules );

	## Applying all rules ##
	&setIptConnmarkRestore( 'true' );

	# persistence rules if apply.
	# NOTE: persistance must be done before tagging
	$status = &applyIptRules( @{ $rules{ t_mangle_p } } ) if ( $persist ne 'none' );
	$status = &applyIptRules( @{ $rules{ t_mangle } } );  # mangle rules for tagging
	$status = &applyIptRules( @{ $rules{ t_nat } } );     # rules for dnat
	$status = &applyIptRules( @{ $rules{ t_snat } } );    # source nat or nat
	&setIptConnmarkSave( 'true' );
	## End applying rules ##

	return;
}

# Stop Farm rutine
# called from setL4FarmBackendStatus($farm_name,$server_id,$status)
sub _runL4ServerStop    # ($farm_name,$server_id)
{
	my $farm_name = shift;    # input: farm name string
	my $server_id = shift;    # input: server id number

	my $farm   = &getL4FarmStruct( $farm_name );
	my $server = $$farm{ servers }[$server_id];
	my %rules  = %{ &getIptRulesStruct() };

	&getL4ServerActionRules( $farm, $server, 'off', \%rules );

	## Applying all rules ##
	&setIptConnmarkRestore( 'true' );

	# persistence rules if apply.
	# NOTE: persistance must be done before tagging
	if ( $$farm{ persist } ne 'none' && $$server{ status } ne 'maintenance' )
	{
		$status = &applyIptRules( @{ $rules{ t_mangle_p } } );
	}
	$status = &applyIptRules( @{ $rules{ t_mangle } } );  # mangle rules for tagging
	$status = &applyIptRules( @{ $rules{ t_nat } } );     # rules for dnat
	$status = &applyIptRules( @{ $rules{ t_snat } } );    # source nat or nat
	&setIptConnmarkSave( 'true' );
	## End applying rules ##

	return $status;
}

# Start Farm rutine
sub getL4ServerWithLowestPriority                         # ($farm)
{
	my $farm = shift;                                     # input: farm reference

	my $server_prio;    # reference to the selected server for prio algorithm

	foreach my $server ( @{ $farm{ servers } } )
	{
		# find the lowest priority server
		$server_prio = $server if not defined $server_prio;
		$server_prio = $server if $server_prio{ priority } > $server{ priority };
	}

	return $server_prio;
}

# function that check if a backend on a farm is on maintenance mode
sub getL4FarmBackendMaintenance
{
	my ( $farm_name, $backend ) = @_;

	my @servers = &getL4FarmServers( $farm_name );
	my @backend_args = split "\;", $servers[$backend];
	chomp ( @backend_args );

	return (    # parentheses required
		$backend_args[6] eq 'maintenance'
		? 0                                 # in maintenance
		: 1                                 # not in maintenance
	);
}

# function that enable the maintenance mode for backend
sub setL4FarmBackendMaintenance             # ( $farm_name, $backend )
{
	my ( $farm_name, $backend ) = @_;

	return &setL4FarmBackendStatus( $farm_name, $backend, 'maintenance' );
}

# function that disable the maintenance mode for backend
sub setL4FarmBackendNoMaintenance
{
	my ( $farm_name, $backend ) = @_;

	return &setL4FarmBackendStatus( $farm_name, $backend, 'up' );
}

# get probability for every backend
sub getL4BackendsWeightProbability
{
	my $farm = shift;    # input: farm reference

	my $weight_sum = 0;

	&doL4FarmProbability( $farm );    # calculate farm weight sum

	foreach my $server ( @{ $$farm{ servers } } )
	{
		# only calculate probability for servers running
		if ( $$server{ status } eq 'up' )
		{
			my $delta = $$server{ weight };
			$weight_sum += $$server{ weight };
			$$server{ prob } = $weight_sum / $$farm{ prob };
		}
		elsif ( $$server{ status } eq 'maintenance' )
		{
			$$server{ prob } = 0;
		}
	}
}

# FIXME: send signal to l4sd to reload configuration
sub refreshL4FarmRules    # AlgorithmRules
{
	my $farm = shift;     # input: reference to farm structure
	my $prio_server;

	$prio_server = &getL4ServerWithLowestPriority( $$farm{ name } )
	  if ( $$farm{ lbalg } eq 'prio' );

	&logfile( "refreshL4FarmRules >> prio_server:$prio_server" );

	my @rules;

	# refresh backends probability values
	&getL4BackendsWeightProbability( $farm ) if ( $$farm{ lbalg } eq 'weight' );

	# get new rules
	foreach my $server ( @{ $$farm{ servers } } )
	{
		# skip cycle for servers not running
		next if ( $$server{ status } !~ /up|maintenance/ );
		&logfile( "refreshL4FarmRules >> hola 1" );

		next if ( $$farm{ lbalg } eq 'prio' && $$server{ id } != $$prio_server{ id } );
		&logfile( "refreshL4FarmRules >> hola 2" );

		my $rule;
		my $rule_num;

		# refresh marks
		$rule = &genIptMark( $farm, $server );

		$rule_num =
		  ( $$farm{ lbalg } eq 'prio' )
		  ? &getIptRuleNumber( $rule, $$farm{ name } )
		  : &getIptRuleNumber( $rule, $$farm{ name }, $$server{ id } );
		$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );
		push ( @rules, $rule );

		if ( $$farm{ persist } ne 'none' )    # persistence
		{
			$rule = &genIptMarkPersist( $farm, $server );
			$rule_num =
			  ( $$farm{ lbalg } eq 'prio' )
			  ? &getIptRuleNumber( $rule, $$farm{ name } )
			  : &getIptRuleNumber( $rule, $$farm{ name }, $$server{ id } );
			$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );
			push ( @rules, $rule );
		}

		# redirect
		$rule = &genIptRedirect( $farm, $server );
		$rule_num =
		  ( $$farm{ lbalg } eq 'prio' )
		  ? &getIptRuleNumber( $rule, $$farm{ name } )
		  : &getIptRuleNumber( $rule, $$farm{ name }, $$server{ id } );
		$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );
		push ( @rules, $rule );

		if ( $$farm{ nattype } eq 'nat' )    # nat type = nat
		{
			if ( $$farm{ vproto } eq 'sip' )
			{
				$rule = &genIptSourceNat( $farm, $server );
			}
			else
			{
				$rule = &genIptMasquerade( $farm, $server );
			}

			$rule_num =
			  ( $$farm{ lbalg } eq 'prio' )
			  ? &getIptRuleNumber( $rule, $$farm{ name } )
			  : &getIptRuleNumber( $rule, $$farm{ name }, $$server{ id } );
			$rule = &applyIptRuleAction( $rule, 'replace', $rule_num );
			push ( @rules, $rule );
		}
	}

	# apply new rules
	return &applyIptRules( @rules );
}

# do not remove this
1;
