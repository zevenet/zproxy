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
sub setFarmClientTimeout($client,$fname)
{
	my ( $client, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "http" || $type eq "https" )
	{
		tie @filefarmhttp, 'Tie::File', "$configdir/$ffile";
		my $i_f         = -1;
		my $array_count = @filefarmhttp;
		my $found       = "false";
		while ( $i_f <= $array_count && $found eq "false" )
		{
			$i_f++;
			if ( @filefarmhttp[$i_f] =~ /^Client/ )
			{
				&logfile( "setting 'ClientTimeout $client' for $fname farm $type" );
				@filefarmhttp[$i_f] = "Client\t\t $client";
				$output             = $?;
				$found              = "true";
			}
		}
		untie @filefarmhttp;
	}

	return $output;
}

#
sub getFarmClientTimeout($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "http" || $type eq "https" )
	{
		open FR, "<$configdir\/$ffile";
		my @file = <FR>;
		foreach $line ( @file )
		{
			if ( $line =~ /Client/i )
			{
				@line = split ( "\ ", $line );
				$output = @line[1];
			}
		}
		close FR;
	}

	#&logfile("getting 'ClientTimeout $output' for $fname farm $type");
	return $output;
}

#
sub setHTTPFarmSessionType($session,$ffile)
{
	my ( $session, $ffile ) = @_;
	my $output = -1;

	&logfile( "setting 'Session type $session' for $fname farm $type" );
	tie @contents, 'Tie::File', "$configdir\/$ffile";
	my $i     = -1;
	my $found = "false";
	foreach $line ( @contents )
	{
		$i++;
		if ( $session ne "nothing" )
		{
			if ( $line =~ "Session" )
			{
				@contents[$i] = "\t\tSession";
				$found = "true";
			}
			if ( $found eq "true" && $line =~ "End" )
			{
				@contents[$i] = "\t\tEnd";
				$found = "false";
			}
			if ( $line =~ "Type" )
			{
				@contents[$i] = "\t\t\tType $session";
				$output = $?;
				@contents[$i + 1] =~ s/#//g;
				if (    $session eq "URL"
					 || $session eq "COOKIE"
					 || $session eq "HEADER" )
				{
					@contents[$i + 2] =~ s/#//g;
				}
				else
				{
					if ( @contents[$i + 2] !~ /#/ )
					{
						@contents[$i + 2] =~ s/^/#/;
					}
				}
			}
		}
		if ( $session eq "nothing" )
		{
			if ( $line =~ "Session" )
			{
				@contents[$i] = "\t\t#Session $session";
				$found = "true";
			}
			if ( $found eq "true" && $line =~ "End" )
			{
				@contents[$i] = "\t\t#End";
				$found = "false";
			}
			if ( $line =~ "TTL" )
			{
				@contents[$i] = "#@contents[$i]";
			}
			if ( $line =~ "Type" )
			{
				@contents[$i] = "#@contents[$i]";
				$output = $?;
			}
			if ( $line =~ "ID" )
			{
				@contents[$i] = "#@contents[$i]";
			}
		}
	}
	untie @contents;
	return $output;
}

#
sub getHTTPFarmSessionType($fname)
{
	my ( $fname ) = @_;
	my $output = -1;

	open FR, "<$configdir\/$fname";
	my @file = <FR>;
	foreach $line ( @file )
	{
		if ( $line =~ /Type/ && $line !~ /#/ )
		{
			@line = split ( "\ ", $line );
			$output = @line[1];
		}
	}
	close FR;

	return $output;
}

#sub setFarmSessionId($sessionid,$fname,$service)
#{
#my ( $sessionid, $fname, $svice ) = @_;

#my $type   = &getFarmType( $fname );
#my $ffile  = &getFarmFile( $fname );
#my $output = -1;

#if ( $type eq "http" || $type eq "https" )
#{
#tie @filefarmhttp, 'Tie::File', "$configdir/$ffile";
#my $i_f         = -1;
#my $array_count = @filefarmhttp;
#my $found       = "false";
#while ( $i_f <= $array_count && $found eq "false" )
#{
#$i_f++;
#if ( @filefarmhttp[$i_f] =~ /ID/ )
#{
#&logfile( "setting 'Session id $sessionid' for $fname farm $type" );
#@filefarmhttp[$i_f] = "\t\t\tID \"$sessionid\"";
#$output             = $?;
#$found              = "true";
#}
#}

#untie @filefarmhttp;
#}

#return $output;
#}

#sub getFarmSessionId($fname,$service)
#{
#my ( $fname, $svice ) = @_;

#my $type   = &getFarmType( $fname );
#my $ffile  = &getFarmFile( $fname );
#my $output = -1;

#if ( $type eq "http" || $type eq "https" )
#{
#open FR, "<$configdir\/$ffile";
#my @file = <FR>;
#foreach $line ( @file )
#{
#if ( $line =~ /ID/ )
#{
#@line = split ( "\ ", $line );
#$output = @line[1];
#$output =~ s/\"//g;
#}
#}
#close FR;
#}

##&logfile("getting 'Session id $output' for $fname farm $type");
#return $output;
#}

#
sub setHTTPFarmBlacklistTime($fbltime,$fname,$ffile)
{
	my ( $fbltime, $fname, $ffile ) = @_;
	my $output = -1;

	tie @filefarmhttp, 'Tie::File', "$configdir/$ffile";
	my $i_f         = -1;
	my $array_count = @filefarmhttp;
	my $found       = "false";
	while ( $i_f <= $array_count && $found eq "false" )
	{
		$i_f++;
		if ( @filefarmhttp[$i_f] =~ /^Alive/ )
		{
			&logfile( "setting 'Blacklist time $fbltime' for $fname farm $type" );
			@filefarmhttp[$i_f] = "Alive\t\t $fbltime";
			$output             = $?;
			$found              = "true";
		}
	}
	untie @filefarmhttp;

	return $output;
}

#
sub getHTTPFarmBlacklistTime($ffile)
{
	my ( $ffile ) = @_;
	my $output = -1;

	open FR, "<$configdir\/$ffile";
	my @file = <FR>;
	foreach $line ( @file )
	{
		if ( $line =~ /Alive/i )
		{
			@line = split ( "\ ", $line );
			$output = @line[1];
		}
	}
	close FR;

	return $output;
}

#
sub setFarmHttpVerb($verb,$fname)
{
	my ( $verb, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "http" || $type eq "https" )
	{
		tie @filefarmhttp, 'Tie::File', "$configdir/$ffile";
		my $i_f         = -1;
		my $array_count = @filefarmhttp;
		my $found       = "false";
		while ( $i_f <= $array_count && $found eq "false" )
		{
			$i_f++;
			if ( @filefarmhttp[$i_f] =~ /xHTTP/ )
			{
				&logfile( "setting 'Http verb $verb' for $fname farm $type" );
				@filefarmhttp[$i_f] = "\txHTTP $verb";
				$output             = $?;
				$found              = "true";
			}
		}
		untie @filefarmhttp;
	}

	return $output;
}

#
sub getFarmHttpVerb($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "http" || $type eq "https" )
	{
		open FR, "<$configdir\/$ffile";
		my @file = <FR>;
		foreach $line ( @file )
		{
			if ( $line =~ /xHTTP/ )
			{
				@line = split ( "\ ", $line );
				$output = @line[1];
			}
		}
		close FR;
	}

	#&logfile("getting 'Http verb $output' for $fname farm $type");
	return $output;
}

#change HTTP or HTTP listener
sub setFarmListen($farmlisten)
{
	my ( $fname, $flisten ) = @_;

	my $ffile = &getFarmFile( $fname );
	tie @filefarmhttp, 'Tie::File', "$configdir/$ffile";
	my $i_f         = -1;
	my $array_count = @filefarmhttp;
	my $found       = "false";
	while ( $i_f <= $array_count && $found eq "false" )
	{
		$i_f++;
		if ( @filefarmhttp[$i_f] =~ /^ListenHTTP/ && $flisten eq "http" )
		{
			@filefarmhttp[$i_f] = "ListenHTTP";
		}
		if ( @filefarmhttp[$i_f] =~ /^ListenHTTP/ && $flisten eq "https" )
		{
			@filefarmhttp[$i_f] = "ListenHTTPS";
		}

		#
		if ( @filefarmhttp[$i_f] =~ /.*Cert\ \"/ && $flisten eq "http" )
		{
			@filefarmhttp[$i_f] =~ s/Cert\ \"/#Cert\ \"/;
		}
		if ( @filefarmhttp[$i_f] =~ /.*Cert\ \"/ && $flisten eq "https" )
		{
			@filefarmhttp[$i_f] =~ s/#//g;

		}

		#
		if ( @filefarmhttp[$i_f] =~ /.*Ciphers\ \"/ && $flisten eq "http" )
		{
			@filefarmhttp[$i_f] =~ s/Ciphers\ \"/#Ciphers\ \"/;
		}
		if ( @filefarmhttp[$i_f] =~ /.*Ciphers\ \"/ && $flisten eq "https" )
		{
			@filefarmhttp[$i_f] =~ s/#//g;

		}

		# Enable 'Disable SSLv3'
		if ( @filefarmhttp[$i_f] =~ /.*Disable SSLv3$/ && $flisten eq "http" )
		{
			@filefarmhttp[$i_f] =~ s/Disable SSLv3/#Disable SSLv3/;
		}
		elsif ( @filefarmhttp[$i_f] =~ /.*DisableSSLv3$/ && $flisten eq "http" )
		{
			@filefarmhttp[$i_f] =~ s/DisableSSLv3/#DisableSSLv3/;
		}
		if ( @filefarmhttp[$i_f] =~ /.*Disable SSLv3$/ && $flisten eq "https" )
		{
			@filefarmhttp[$i_f] =~ s/#//g;
		}
		elsif (    @filefarmhttp[$i_f] =~ /.*DisableSSLv3$/
				&& $flisten eq "https" )
		{
			@filefarmhttp[$i_f] =~ s/#//g;
		}

		# Enable SSLHonorCipherOrder
		if (    @filefarmhttp[$i_f] =~ /.*SSLHonorCipherOrder/
			 && $flisten eq "http" )
		{
			@filefarmhttp[$i_f] =~ s/SSLHonorCipherOrder/#SSLHonorCipherOrder/;
		}
		if (    @filefarmhttp[$i_f] =~ /.*SSLHonorCipherOrder/
			 && $flisten eq "https" )
		{
			@filefarmhttp[$i_f] =~ s/#//g;
		}

		# Enable StrictTransportSecurity
		if (    @filefarmhttp[$i_f] =~ /.*StrictTransportSecurity/
			 && $flisten eq "http" )
		{
			@filefarmhttp[$i_f] =~ s/StrictTransportSecurity/#StrictTransportSecurity/;
		}
		if (    @filefarmhttp[$i_f] =~ /.*StrictTransportSecurity/
			 && $flisten eq "https" )
		{
			@filefarmhttp[$i_f] =~ s/#//g;
		}

		if ( @filefarmhttp[$i_f] =~ /ZWACL-END/ )
		{
			$found = "true";
		}

	}
	untie @filefarmhttp;
}

#asign a RewriteLocation vaue to a farm HTTP or HTTPS
sub setFarmRewriteL($fname,$rewritelocation)
{
	my ( $fname, $rewritelocation ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;
	&logfile( "setting 'Rewrite Location' for $fname to $rewritelocation" );

	if ( $type eq "http" || $type eq "https" )
	{
		tie @filefarmhttp, 'Tie::File', "$configdir/$ffile";
		my $i_f         = -1;
		my $array_count = @filefarmhttp;
		my $found       = "false";
		while ( $i_f <= $array_count && $found eq "false" )
		{
			$i_f++;
			if ( @filefarmhttp[$i_f] =~ /RewriteLocation\ .*/ )
			{
				@filefarmhttp[$i_f] = "\tRewriteLocation $rewritelocation";
				$output             = $?;
				$found              = "true";
			}
		}
		untie @filefarmhttp;
	}

}

#Get RewriteLocation Header configuration HTTP and HTTPS farms
sub getFarmRewriteL($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "http" || $type eq "https" )
	{
		open FR, "<$configdir\/$ffile";
		my @file = <FR>;
		foreach $line ( @file )
		{
			if ( $line =~ /RewriteLocation\ .*/ )
			{
				@line = split ( "\ ", $line );
				$output = @line[1];
			}
		}
		close FR;
	}

	#&logfile("getting 'Timeout $output' for $fname farm $type");
	return $output;
}

#set ConnTo value to a farm HTTP or HTTPS
sub setFarmConnTO($tout,$fname)
{
	my ( $tout, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	&logfile( "setting 'ConnTo timeout $tout' for $fname farm $type" );

	if ( $type eq "http" || $type eq "https" )
	{
		tie @filefarmhttp, 'Tie::File', "$configdir/$ffile";
		my $i_f         = -1;
		my $array_count = @filefarmhttp;
		my $found       = "false";
		while ( $i_f <= $array_count && $found eq "false" )
		{
			$i_f++;
			if ( @filefarmhttp[$i_f] =~ /^ConnTO.*/ )
			{
				@filefarmhttp[$i_f] = "ConnTO\t\t $tout";
				$output             = $?;
				$found              = "true";
			}
		}
		untie @filefarmhttp;
	}
	return $output;
}

#get farm ConnTO value for http and https farms
sub getFarmConnTO($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "http" || $type eq "https" )
	{
		open FR, "<$configdir\/$ffile";
		my @file = <FR>;
		foreach $line ( @file )
		{
			if ( $line =~ /^ConnTO/ )
			{
				@line = split ( "\ ", $line );
				$output = @line[1];
			}
		}
		close FR;
	}

	return $output;
}

#asign a timeout value to a farm
sub setHTTPFarmTimeout($tout,$ffile)
{
	my ( $tout, $ffile ) = @_;
	my $output = -1;

	tie @filefarmhttp, 'Tie::File', "$configdir/$ffile";
	my $i_f         = -1;
	my $array_count = @filefarmhttp;
	my $found       = "false";
	while ( $i_f <= $array_count && $found eq "false" )
	{
		$i_f++;
		if ( @filefarmhttp[$i_f] =~ /^Timeout/ )
		{
			@filefarmhttp[$i_f] = "Timeout\t\t $tout";
			$output             = $?;
			$found              = "true";
		}
	}
	untie @filefarmhttp;

	return $output;
}

#
sub getHTTPFarmTimeout($ffile)
{
	my ( $ffile ) = @_;
	my $output = -1;

	open FR, "<$configdir\/$ffile";
	my @file = <FR>;
	foreach $line ( @file )
	{
		if ( $line =~ /^Timeout/ )
		{
			@line = split ( "\ ", $line );
			$output = @line[1];
		}
	}
	close FR;

	return $output;
}

# set the max clients of a farm
sub setHTTPFarmMaxClientTime($track,$ffile)
{
	my ( $track, $ffile ) = @_;
	my $output = -1;

	tie @filefarmhttp, 'Tie::File', "$configdir/$ffile";
	my $i_f         = -1;
	my $array_count = @filefarmhttp;
	my $found       = "false";
	while ( $i_f <= $array_count && $found eq "false" )
	{
		$i_f++;
		if ( @filefarmhttp[$i_f] =~ /TTL/ )
		{
			@filefarmhttp[$i_f] = "\t\t\tTTL $track";
			$output             = $?;
			$found              = "true";
		}
	}
	untie @filefarmhttp;

	return $output;
}

#
sub getHTTPFarmMaxClientTime($fname)
{
	my ( $fname ) = @_;
	my @output;

	push ( @output, "" );
	push ( @output, "" );
	$ffile = &getFarmFile( $fname );
	open FR, "<$configdir\/$ffile";
	my @file = <FR>;
	foreach $line ( @file )
	{
		if ( $line =~ /TTL/ )
		{
			@line = split ( "\ ", $line );
			@output[0] = "";
			@output[1] = @line[1];
		}
	}
	close FR;

	return @output;
}

# set the max conn of a farm
sub setHTTPFarmMaxConn($maxc,$ffile)
{
	my ( $maxc, $ffile ) = @_;
	my $output = -1;

	use Tie::File;
	tie @array, 'Tie::File', "$configdir/$ffile";
	for ( @array )
	{
		if ( $_ =~ "Threads" )
		{
			#s/^Threads.*/Threads   $maxc/g;
			$_      = "Threads\t\t$maxc";
			$output = $?;
		}
	}
	untie @array;

	return $output;
}

#
sub getFarmCertificate($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $output = -1;

	if ( $type eq "https" )
	{
		my $file = &getFarmFile( $fname );
		open FI, "<$configdir/$file";
		my @content = <FI>;
		close FI;
		foreach $line ( @content )
		{
			if ( $line =~ /Cert/ && $line !~ /\#.*Cert/ )
			{
				my @partline = split ( '\"', $line );
				@partline = split ( "\/", @partline[1] );
				my $lfile = @partline;
				$output = @partline[$lfile - 1];
			}
		}
	}

	#&logfile("getting 'Certificate $output' for $fname farm $type");
	return $output;
}

#
sub setFarmCertificate($cfile,$fname)
{
	my ( $cfile, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	&logfile( "setting 'Certificate $cfile' for $fname farm $type" );
	if ( $type eq "https" )
	{
		use Tie::File;
		tie @array, 'Tie::File', "$configdir/$ffile";
		for ( @array )
		{
			if ( $_ =~ /Cert/ )
			{
				s/.*Cert\ .*/\tCert\ \"$configdir\/$cfile\"/g;
				$output = $?;
			}
		}
		untie @array;
	}

	return $output;
}

sub getHTTPFarmGlobalStatus($fname)
{
	my ( $fname ) = @_;

	return `$poundctl -c "/tmp/$fname\_pound.socket"`;
}

# getBackendEstConns ???

#
sub getHTTPFarmEstConns(@nets,@netstat,$fvip,$fvipp)
{
	my ( @nets, @netstat, $fvip, $fvipp ) = @_;

	push (
		   @nets,
		   &getNetstatFilter(
					   "tcp", "",
					   "\.* ESTABLISHED src=\.* dst=$fvip sport=\.* dport=$fvipp .*src=\.*",
					   "", @netstat
		   )
	);

	return @nets;
}

# getFarmTWConns ???
# getBackendSYNConns ???

#
sub getHTTPFarmSYNConns(@nets,@netstat,$fvip,$fvipp)
{
	my ( @nets, @netstat, $fvip, $fvipp ) = @_;

	push (
		   @nets,
		   &getNetstatFilter(
							  "tcp", "",
							  "\.* SYN\.* src=\.* dst=$fvip \.* dport=$fvipp \.* src=\.*",
							  "", @netstat
		   )
	);

	return @nets;
}

#
sub setFarmErr($fname,$content,$nerr)
{
	my ( $fname, $content, $nerr ) = @_;

	my $type   = &getFarmType( $fname );
	my $output = -1;

	&logfile( "setting 'Err $nerr' for $fname farm $type" );
	if ( $type eq "http" || $type eq "https" )
	{
		if ( -e "$configdir\/$fname\_Err$nerr.html" && $nerr != "" )
		{
			$output = 0;
			my @err = split ( "\n", "$content" );
			print "<br><br>";
			open FO, ">$configdir\/$fname\_Err$nerr.html";
			foreach $line ( @err )
			{
				$line =~ s/\r$//;
				print FO "$line\n";
				$output = $? || $output;
			}
			close FO;
		}
	}

	return $output;
}

#
sub getFarmErr($fname,$nerr)
{
	my ( $fname, $nerr ) = @_;

	my $type  = &getFarmType( $fname );
	my $ffile = &getFarmFile( $fname );
	my @output;

	if ( $type eq "http" || $type eq "https" )
	{
		open FR, "<$configdir\/$ffile";
		my @file = <FR>;
		foreach $line ( @file )
		{
			if ( $line =~ /Err$nerr/ )
			{
				@line = split ( "\ ", $line );
				my $err = @line[1];
				$err =~ s/"//g;
				if ( -e $err )
				{
					open FI, "$err";
					while ( <FI> )
					{
						push ( @output, $_ );
					}
					close FI;
				}
			}
		}
		close FR;
	}

	#&logfile("getting 'Err $nerr' for $fname farm $type");
	return @output;
}

# Start Farm rutine
sub _runHTTPFarmStart($fname,$file,$status)
{
	my ( $fname, $file, $status ) = @_;

	unlink ( "/tmp/$fname.lock" );
	&logfile( "running $pound -f $configdir\/$file -p $piddir\/$fname\_pound.pid" );
	zsystem(
			 "$pound -f $configdir\/$file -p $piddir\/$fname\_pound.pid 2>/dev/null" );
	$status = $?;
	if ( $status == 0 )
	{
		&setFarmHttpBackendStatus( $fname );
	}

	return $status;
}

# Stop Farm rutine
sub _runHTTPFarmStop($fname,$status)
{
	my ( $fname, $status ) = @_;

	&runFarmGuardianStop( $fname, "" );
	my $checkfarm = &getFarmConfigIsOK( $fname );
	if ( $checkfarm == 0 )
	{
		$pid = &getFarmPid( $fname );
		&logfile( "running 'kill 15, $pid'" );
		$run = kill 15, $pid;
		$status = $?;
		unlink ( "$piddir\/$fname\_pound.pid" );
		unlink ( "\/tmp\/$fname\_pound.socket" );
	}
	else
	{
		&errormsg(
			  "Farm $fname can't be stopped, check the logs and modify the configuration" );
		return 1;
	}

	return $status;
}

#
sub runHTTPFarmCreate($fproto,$fvip,$fvipp,$fname)
{
	my ( $fproto, $fvip, $fvipp, $fname ) = @_;
	my $output = -1;

	#copy template modyfing values
	use File::Copy;
	&logfile( "copying pound tpl file on $fname\_pound.cfg" );
	copy( "$poundtpl", "$configdir/$fname\_pound.cfg" );

	#modify strings with variables
	use Tie::File;
	tie @file, 'Tie::File', "$configdir/$fname\_pound.cfg";
	foreach $line ( @file )
	{
		$line =~ s/\[IP\]/$fvip/;
		$line =~ s/\[PORT\]/$fvipp/;
		$line =~ s/\[DESC\]/$fname/;
		$line =~ s/\[CONFIGDIR\]/$configdir/;
		if ( $fproto eq "HTTPS" )
		{
			$line =~ s/ListenHTTP/ListenHTTPS/;
			$line =~ s/#Cert/Cert/;
		}
	}
	untie @file;

	#create files with personalized errors
	open FERR, ">$configdir\/$fname\_Err414.html";
	print FERR "Request URI is too long.\n";
	close FERR;
	open FERR, ">$configdir\/$fname\_Err500.html";
	print FERR "An internal server error occurred. Please try again later.\n";
	close FERR;
	open FERR, ">$configdir\/$fname\_Err501.html";
	print FERR "This method may not be used.\n";
	close FERR;
	open FERR, ">$configdir\/$fname\_Err503.html";
	print FERR "The service is not available. Please try again later.\n";
	close FERR;

	#run farm
	&logfile(
		 "running $pound -f $configdir\/$fname\_pound.cfg -p $piddir\/$fname\_pound.pid"
	);
	zsystem(
		"$pound -f $configdir\/$fname\_pound.cfg -p $piddir\/$fname\_pound.pid 2>/dev/null"
	);
	$output = $?;

	return $output;
}

# Returns farm max connections
sub getHTTPFarmMaxConn($fname)
{
	my ( $fname ) = @_;
	my $output = -1;

	my ( $fname ) = @_;
	my $output = -1;

	my $ffile = &getFarmFile( $fname );
	open FR, "<$configdir\/$ffile";
	my @file = <FR>;
	foreach $line ( @file )
	{
		if ( $line =~ /^Threads/ )
		{
			@line = split ( "\ ", $line );
			my $maxt = @line[1];
			$maxt =~ s/\ //g;
			chomp ( $maxt );
			$output = $maxt;
		}
	}
	close FR;

	return $output;
}

# Returns farm listen port
sub getHTTPFarmPort($fname)
{
	my ( $fname ) = @_;
	return "/tmp/" . $fname . "_pound.socket";
}

# Returns farm PID
sub getHTTPFarmPid($fname)
{
	my ( $fname ) = @_;
	my $output = -1;

	@fname = split ( /\_/, $file );
	my $pidfile = "$piddir\/$fname\_pound.pid";
	if ( -e $pidfile )
	{
		open FPID, "<$pidfile";
		@pid = <FPID>;
		close FPID;
		$pid_hprof = @pid[0];
		chomp ( $pid_hprof );
		if ( $pid_hprof =~ /^[1-9].*/ )
		{
			$output = "$pid_hprof";
		}
		else
		{
			$output = "-";
		}
	}
	else
	{
		$output = "-";
	}

	return $output;
}

# Returns farm Child PID (ONLY HTTP Farms)
sub getFarmChildPid($fname)
{
	my ( $fname ) = @_;
	use File::Grep qw( fgrep fmap fdo );

	my $type   = &getFarmType( $fname );
	my $fpid   = &getFarmPid( $fname );
	my $output = -1;

	if ( $type eq "http" || $type eq "https" )
	{
		my $pids = `pidof -o $fpid pound`;
		my @pids = split ( " ", $pids );
		foreach $pid ( @pids )
		{
			if ( fgrep { /^PPid:.*${fpid}$/ } "/proc/$pid/status" )
			{
				$output = $pid;
				last;
			}
		}
	}

	return $output;
}

# Returns farm vip
sub getHTTPFarmVip($info,$file)
{
	my ( $info, $file ) = @_;
	my $output = -1;

	open FI, "<$configdir/$file";
	my @file = <FI>;
	my $i    = 0;
	close FI;
	foreach $line ( @file )
	{
		if ( $line =~ /^ListenHTTP/ )
		{
			my $vip  = @file[$i + 5];
			my $vipp = @file[$i + 6];
			chomp ( $vip );
			chomp ( $vipp );
			my @vip  = split ( "\ ", $vip );
			my @vipp = split ( "\ ", $vipp );
			if ( $info eq "vip" )   { $output = @vip[1]; }
			if ( $info eq "vipp" )  { $output = @vipp[1]; }
			if ( $info eq "vipps" ) { $output = "@vip[1]\:@vipp[1]"; }
		}
		$i++;
	}

	return $output;
}

# Set farm virtual IP and virtual PORT
sub setHTTPFarmVirtualConf($vip,$vipp,$fconf)
{
	my ( $vip, $vipp, $fconf ) = @_;

	my $stat  = 0;
	my $enter = 2;
	use Tie::File;
	tie @array, 'Tie::File', "$configdir\/$fconf";
	my $size = @array;
	for ( $i = 0 ; $i < $size && $enter > 0 ; $i++ )
	{
		if ( @array[$i] =~ /Address/ )
		{
			@array[$i] =~ s/.*Address\ .*/\tAddress\ $vip/g;
			$stat = $? || $stat;
			$enter--;
		}
		if ( @array[$i] =~ /Port/ )
		{
			@array[$i] =~ s/.*Port\ .*/\tPort\ $vipp/g;
			$stat = $? || $stat;
			$enter--;
		}
	}
	untie @array;

	return $stat;
}

#
sub setHTTPFarmServer($ids,$rip,$port,$priority,$timeout,$fname,$service,$file,$nsflag,$backend,$idservice)
{
	my (
		 $ids,     $rip,  $port,   $priority, $timeout, $fname,
		 $service, $file, $nsflag, $backend,  $idservice
	) = @_;
	my $output = -1;

	tie @contents, 'Tie::File', "$configdir\/$file";
	my $be_section = -1;
	if ( $ids !~ /^$/ )
	{
		my $index_count = -1;
		my $i           = -1;
		my $sw          = 0;
		foreach $line ( @contents )
		{
			$i++;

			#search the service to modify
			if ( $line =~ /Service \"$service\"/ )
			{
				$sw = 1;
			}
			if ( $line =~ /BackEnd/ && $line !~ /#/ && $sw eq 1 )
			{
				$index_count++;
				if ( $index_count == $ids )
				{
					#server for modify $ids;
					#HTTPS
					my $httpsbe = &getFarmVS( $fname, $service, "httpsbackend" );
					if ( $httpsbe eq "true" )
					{
						#add item
						$i++;
					}
					$output           = $?;
					@contents[$i + 1] = "\t\t\tAddress $rip";
					@contents[$i + 2] = "\t\t\tPort $port";
					my $p_m = 0;
					if ( @contents[$i + 3] =~ /TimeOut/ )
					{
						@contents[$i + 3] = "\t\t\tTimeOut $timeout";
						&logfile( "Modified current timeout" );
					}
					if ( @contents[$i + 4] =~ /Priority/ )
					{
						@contents[$i + 4] = "\t\t\tPriority $priority";
						&logfile( "Modified current priority" );
						$p_m = 1;
					}
					if ( @contents[$i + 3] =~ /Priority/ )
					{
						@contents[$i + 3] = "\t\t\tPriority $priority";
						$p_m = 1;
					}

					#delete item
					if ( $timeout =~ /^$/ )
					{
						if ( @contents[$i + 3] =~ /TimeOut/ )
						{
							splice @contents, $i + 3, 1,;
						}
					}
					if ( $priority =~ /^$/ )
					{
						if ( @contents[$i + 3] =~ /Priority/ )
						{
							splice @contents, $i + 3, 1,;
						}
						if ( @contents[$i + 4] =~ /Priority/ )
						{
							splice @contents, $i + 4, 1,;
						}
					}

					#new item
					if (
						 $timeout !~ /^$/
						 && (    @contents[$i + 3] =~ /End/
							  || @contents[$i + 3] =~ /Priority/ )
					  )
					{
						splice @contents, $i + 3, 0, "\t\t\tTimeOut $timeout";
					}
					if (
						    $p_m eq 0
						 && $priority !~ /^$/
						 && (    @contents[$i + 3] =~ /End/
							  || @contents[$i + 4] =~ /End/ )
					  )
					{
						if ( @contents[$i + 3] =~ /TimeOut/ )
						{
							splice @contents, $i + 4, 0, "\t\t\tPriority $priority";
						}
						else
						{
							splice @contents, $i + 3, 0, "\t\t\tPriority $priority";
						}
					}
				}
			}
		}
	}
	else
	{
		#add new server
		$nsflag = "true";
		my $index   = -1;
		my $backend = 0;
		foreach $line ( @contents )
		{
			$index++;
			if ( $be_section == 1 && $line =~ /Address/ )
			{
				$backend++;
			}
			if ( $line =~ /Service \"$service\"/ )
			{
				$be_section++;
			}
			if ( $line =~ /#BackEnd/ && $be_section == 0 )
			{
				$be_section++;
			}
			if ( $be_section == 1 && $line =~ /#End/ )
			{
				splice @contents, $index, 0, "\t\tBackEnd";
				$output = $?;
				$index++;
				splice @contents, $index, 0, "\t\t\tAddress $rip";
				my $httpsbe = &getFarmVS( $fname, $service, "httpsbackend" );
				if ( $httpsbe eq "true" )
				{
					#add item
					splice @contents, $index, 0, "\t\t\tHTTPS";
					$index++;
				}
				$index++;
				splice @contents, $index, 0, "\t\t\tPort $port";
				$index++;

				#Timeout?
				if ( $timeout )
				{
					splice @contents, $index, 0, "\t\t\tTimeOut $timeout";
					$index++;
				}

				#Priority?
				if ( $priority )
				{
					splice @contents, $index, 0, "\t\t\tPriority $priority";
					$index++;
				}
				splice @contents, $index, 0, "\t\tEnd";
				$be_section = -1;
			}

			# if backend added then go out of form
		}
		if ( $nsflag eq "true" )
		{
			$idservice = &getFarmVSI( $fname, $service );
			if ( $idservice ne "" )
			{
				&getFarmHttpBackendStatus( $fname, $backend, "active", $idservice );
			}
		}
	}
	untie @contents;

	return $output;
}

#
sub runHTTPFarmServerDelete($ids,$fname,$ffile)
{
	my ( $ids, $fname, $ffile ) = @_;
	my $output = -1;
	my $i      = -1;
	my $j      = -1;
	my $sw     = 0;

	tie @contents, 'Tie::File', "$configdir\/$ffile";
	foreach $line ( @contents )
	{
		$i++;
		if ( $line =~ /Service \"$svice\"/ )
		{
			$sw = 1;
		}
		if ( $line =~ /BackEnd/ && $line !~ /#/ && $sw == 1 )
		{
			$j++;
			if ( $j == $ids )
			{
				splice @contents, $i, 1,;
				$output = $?;
				while ( @contents[$i] !~ /End/ )
				{
					splice @contents, $i, 1,;
				}
				splice @contents, $i, 1,;
			}
		}
	}
	untie @contents;
	if ( $output != -1 )
	{
		&runRemovehttpBackend( $fname, $ids, $svice );
	}

	return $output;
}

#
sub getHTTPFarmBackendStatusCtl($fname)
{
	my ( $fname ) = @_;
	return `$poundctl -c  /tmp/$fname\_pound.socket`;
}

#function that return the status information of a farm:
#ip, port, backendstatus, weight, priority, clients
sub getHTTPFarmBackendsStatus($fname,@content)
{
	my ( $fname, @content ) = @_;
	my @output = -1;

	if ( !@content )
	{
		@content = &getFarmBackendStatusCtl( $fname );
	}
	my @backends;
	my @b_data;
	my $line;
	my @serviceline;
	foreach ( @content )
	{
		if ( $_ =~ /Service/ )
		{
			@serviceline = split ( "\ ", $_ );
			@serviceline[2] =~ s/"//g;
			chomp ( @serviceline[2] );
		}
		if ( $_ =~ /Backend/ )
		{
			#backend ID
			@backends = split ( "\ ", $_ );
			@backends[0] =~ s/\.//g;
			$line = @backends[0];

			#backend IP,PORT
			@backends_ip  = split ( ":", @backends[2] );
			$ip_backend   = @backends_ip[0];
			$port_backend = @backends_ip[1];
			$line         = $line . "\t" . $ip_backend . "\t" . $port_backend;

			#status
			$status_backend = @backends[7];
			my $backend_disabled = @backends[3];
			if ( $backend_disabled eq "DISABLED" )
			{
				#Checkstatusfile
				$status_backend =
				  &getBackendStatusFromFile( $fname, @backends[0], @serviceline[2] );
			}
			elsif ( $status_backend eq "alive" )
			{
				$status_backend = "up";
			}
			elsif ( $status_backend eq "DEAD" )
			{
				$status_backend = "down";
			}
			$line = $line . "\t" . $status_backend;

			#priority
			$priority_backend = @backends[4];
			$priority_backend =~ s/\(//g;
			$line = $line . "\t" . "-\t" . $priority_backend;
			my $clients = &getFarmBackendsClients( @backends[0], @content, $fname );
			if ( $clients != -1 )
			{
				$line = $line . "\t" . $clients;
			}
			else
			{
				$line = $line . "\t-";
			}
			push ( @b_data, $line );
		}
	}
	@output = @b_data;

	return @output;
}

#function that return if a pound backend is active, down by farmguardian or it's in maintenance mode
sub getHTTPBackendStatusFromFile($fname,$backend,$svice)
{
	my ( $fname, $backend, $svice ) = @_;
	my $index;
	my $line;
	my $stfile = "$configdir\/$fname\_status.cfg";
	my $output = -1;
	if ( -e "$stfile" )
	{
		$index = &getFarmVSI( $fname, $svice );
		open FG, "$stfile";
		while ( $line = <FG> )
		{
			#service index
			if ( $line =~ /\ 0\ ${index}\ ${backend}/ )
			{
				if ( $line =~ /maintenance/ )
				{
					$output = "maintenance";
				}
				elsif ( $line =~ /fgDOWN/ )
				{
					$output = "fgDOWN";
				}
				else
				{
					$output = "active";
				}
			}
		}
		close FG;
	}
	return $output;
}

#function that return the status information of a farm:
sub getHTTPFarmBackendsClients($idserver,@content,$fname)
{
	my ( $idserver, @content, $fname ) = @_;

	if ( !@content )
	{
		@content = &getFarmBackendStatusCtl( $fname );
	}
	my $numclients = 0;
	foreach ( @content )
	{
		if ( $_ =~ / Session .* -> $idserver$/ )
		{
			$numclients++;
		}
	}

	return $numclients;
}

#function that return the status information of a farm:
sub getHTTPFarmBackendsClientsList($fname,@content)
{
	my ( $fname, @content ) = @_;

	if ( !@content )
	{
		@content = &getFarmBackendStatusCtl( $fname );
	}
	my @sess;
	my @s_data;
	my @service;
	my $s;

	foreach ( @content )
	{
		my $line;
		if ( $_ =~ /Service/ )
		{
			@service = split ( "\ ", $_ );
			$s = @service[2];
			$s =~ s/"//g;
		}
		if ( $_ =~ / Session / )
		{
			@sess = split ( "\ ", $_ );
			my $id = @sess[0];
			$id =~ s/\.//g;
			$line = $s . "\t" . $id . "\t" . @sess[2] . "\t" . @sess[4];
			push ( @s_data, $line );
		}
	}

	return @s_data;
}

#function that renames a farm
sub setHTTPNewFarmName($fname,$newfname)
{
	my ( $fname, $newfname ) = @_;

	my $output = -1;
	my @ffiles = (
				   "$configdir\/$fname\_status.cfg",
				   "$configdir\/$fname\_pound.cfg",
				   "$configdir\/$fname\_Err414.html",
				   "$configdir\/$fname\_Err500.html",
				   "$configdir\/$fname\_Err501.html",
				   "$configdir\/$fname\_Err503.html",
				   "$fname\_guardian.conf"
	);
	my @newffiles = (
					  "$configdir\/$newfname\_status.cfg",
					  "$configdir\/$newfname\_pound.cfg",
					  "$configdir\/$newfname\_Err414.html",
					  "$configdir\/$newfname\_Err500.html",
					  "$configdir\/$newfname\_Err501.html",
					  "$configdir\/$newfname\_Err503.html",
					  "$fname\_guardian.conf"
	);

	if ( -e "\/tmp\/$fname\_pound.socket" )
	{
		unlink ( "\/tmp\/$fname\_pound.socket" );
	}
	foreach $ffile ( @ffiles )
	{
		if ( -e "$ffile" )
		{
			use Tie::File;
			tie @filelines, 'Tie::File', "$ffile";
			for ( @filelines )
			{
				s/$fname/$newfname/g;
			}
			untie @filelines;
			rename ( "$ffile", "$newffiles[0]" );
			$output = $?;
			&logfile( "configuration saved in $newffiles[0] file" );
		}
		shift ( @newffiles );
	}

	return $output;
}

# HTTPS
# Set Farm Ciphers vale
sub setFarmCiphers($fname,$ciphers)
{
	( $fname, $ciphers, $cipherc ) = @_;
	my $type   = &getFarmType( $fname );
	my $output = -1;
	if ( $type eq "https" )
	{
		my $file = &getFarmFile( $fname );
		tie @array, 'Tie::File', "$configdir/$file";
		for ( @array )
		{
			if ( $_ =~ /Ciphers/ )
			{
				if ( $ciphers eq "cipherglobal" )
				{
					$_ =~ s/\tCiphers/\t#Ciphers/g;
					$output = 0;
				}
				if ( $ciphers eq "cipherpci" )
				{
					$_ =~ s/#//g;
					$_      = "\tCiphers \"$cipher_pci\"";
					$output = 0;
				}
				if ( $ciphers eq "ciphercustom" )
				{
					$_ =~ s/#//g;
					$_      = "\tCiphers \"$cipher_pci\"";
					$output = 0;
				}
				if ( $cipherc )
				{
					$_ =~ s/#//g;
					$_      = "\tCiphers \"$cipherc\"";
					$output = 0;
				}
			}
		}
		untie @array;
	}
	return $output;
}

# HTTPS
# Get Farm Ciphers value
sub getFarmCipher($fname)
{
	( $fname ) = @_;
	my $type   = &getFarmType( $fname );
	my $output = -1;
	if ( $type eq "https" )
	{
		my $file = &getFarmFile( $fname );
		open FI, "<$configdir/$file";
		my @content = <FI>;
		close FI;
		foreach $line ( @content )
		{
			if ( $line =~ /Ciphers/ )
			{
				my @partline = split ( '\ ', $line );
				$lfile = @partline[1];
				$lfile =~ s/\"//g;
				chomp ( $lfile );
				if ( $line =~ /#/ )
				{
					$output = "cipherglobal";
				}
				else
				{
					$output = $lfile;
				}
			}
		}
	}
	return $output;
}

#function that check if the config file is OK.
sub getHTTPFarmConfigIsOK($ffile)
{
	my ( $ffile ) = @_;
	my $output = -1;

	&logfile( "running: $pound -f $configdir\/$ffile -c " );

	my $run = `$pound -f $configdir\/$ffile -c 2>&1`;
	$output = $?;
	&logfile( "output: $run " );

	return $output;
}

#function that check if a backend on a farm is on maintenance mode
sub getHTTPFarmBackendMaintenance($fname,$backend,$service)
{
	my ( $fname, $backend, $service ) = @_;

	$output = -1;

	@run = `$poundctl -c "/tmp/$fname\_pound.socket"`;
	my $sw = 0;
	foreach my $line ( @run )
	{
		if ( $line =~ /Service \"$service\"/ )
		{
			$sw = 1;
		}
		if ( $line =~ /$backend\. Backend/ && $sw == 1 )
		{
			my @line = split ( "\ ", $line );
			my $backendstatus = @line[3];
			if ( $backendstatus eq "DISABLED" )
			{
				$backendstatus = &getBackendStatusFromFile( $fname, $backend, $service );
				if ( $backendstatus =~ /maintenance/ )
				{
					$output = 0;
				}
			}
			last;
		}
	}

	return $output;
}

#function that enable the maintenance mode for backend
sub setHTTPFarmBackendMaintenance($fname,$backend,$service)
{
	my ( $fname, $backend, $service ) = @_;
	my $output = -1;

	&logfile(
			  "setting Maintenance mode for $fname service $service backend $backend" );

	#find the service number
	my $idsv = &getFarmVSI( $fname, $service );
	@run    = `$poundctl -c /tmp/$fname\_pound.socket -b 0 $idsv $backend`;
	$output = $?;
	&logfile(
			  "running '$poundctl -c /tmp/$fname\_pound.socket -b 0 $idsv $backend'" );
	&getFarmHttpBackendStatus( $farmname, $backend, "maintenance", $idsv );

	return $output;
}

#function that disable the maintenance mode for backend
sub setHTTPFarmBackendNoMaintenance($fname,$backend,$service)
{
	my ( $fname, $backend, $service ) = @_;
	my $output = -1;

	&logfile( "setting Disabled maintenance mode for $fname backend $backend" );

	#find the service number
	my $idsv = &getFarmVSI( $fname, $service );
	@run    = `$poundctl -c /tmp/$fname\_pound.socket -B 0 $idsv $backend`;
	$output = $?;
	&logfile(
			  "running '$poundctl -c /tmp/$fname\_pound.socket -B 0 $idsv $backend'" );
	&getFarmHttpBackendStatus( $fname, $backend, "active", $idsv );

	return $output;
}

#function that save in a file the backend status (maintenance or not)
sub getFarmHttpBackendStatus($fname,$backend,$status,$idsv)
{
	( $fname, $backend, $status, $idsv ) = @_;
	my $line;
	my @sw;
	my @bw;
	my $changed    = "false";
	my $statusfile = "$configdir\/$fname\_status.cfg";

	#&logfile("Saving backends status in farm $fname");
	if ( !-e $statusfile )
	{
		open FW, ">$statusfile";
		@run = `$poundctl -c /tmp/$fname\_pound.socket`;
		foreach $line ( @run )
		{
			if ( $line =~ /\.\ Service\ / )
			{
				@sw = split ( "\ ", $line );
				@sw[0] =~ s/\.//g;
				chomp @sw[0];
			}
			if ( $line =~ /\.\ Backend\ / )
			{
				@bw = split ( "\ ", $line );
				@bw[0] =~ s/\.//g;
				chomp @bw[0];
				if ( @bw[3] eq "active" )
				{
					print FW "-B 0 @sw[0] @bw[0] active\n";
				}
				else
				{
					print FW "-b 0 @sw[0] @bw[0] fgDOWN\n";
				}
			}
		}
		close FW;
	}
	use Tie::File;
	tie @filelines, 'Tie::File', "$statusfile";
	for ( @filelines )
	{
		if ( $_ =~ /\ 0\ $idsv\ $backend/ )
		{
			if ( $status =~ /maintenance/ || $status =~ /fgDOWN/ )
			{
				$_       = "-b 0 $idsv $backend $status";
				$changed = "true";
			}
			else
			{
				$_       = "-B 0 $idsv $backend $status";
				$changed = "true";
			}
		}
	}
	untie @filelines;
	if ( $changed eq "false" )
	{
		open FW, ">>$statusfile";
		if ( $status =~ /maintenance/ || $status =~ /fgDOWN/ )
		{
			print FW "-b 0 $idsv $backend $status\n";
		}
		else
		{
			print FW "-B 0 $idsv $backend active\n";
		}
		close FW;
	}
}

#Function that removes a backend from the status file
sub runRemovehttpBackend($fname,$backend,$service)
{
	( $fname, $backend, $service ) = @_;
	my $i      = -1;
	my $j      = -1;
	my $change = "false";
	my $sindex = &getFarmVSI( $fname, $service );
	tie @contents, 'Tie::File', "$configdir\/$fname\_status.cfg";
	foreach $line ( @contents )
	{
		$i++;
		if ( $line =~ /0\ ${sindex}\ ${backend}/ )
		{
			splice @contents, $i, 1,;
		}
	}
	untie @contents;
	my $index = -1;
	tie @filelines, 'Tie::File', "$configdir\/$fname\_status.cfg";
	for ( @filelines )
	{
		$index++;
		if ( $_ !~ /0\ ${sindex}\ $index/ )
		{
			$jndex = $index + 1;
			$_ =~ s/0\ ${sindex}\ $jndex/0\ ${sindex}\ $index/g;
		}
	}
	untie @filelines;
}

sub setFarmHttpBackendStatus($fname)
{
	( $fname ) = @_;
	my $line;
	&logfile( "Setting backends status in farm $fname" );
	open FR, "<$configdir\/$fname\_status.cfg";
	while ( <FR> )
	{
		@line = split ( "\ ", $_ );
		@run =
		  `$poundctl -c /tmp/$fname\_pound.socket @line[0] @line[1] @line[2] @line[3]`;
	}
	close FR;
}

#Create a new Service in a HTTP farm
sub setFarmHTTPNewService($fname,$service)
{
	my ( $fname, $service ) = @_;
	my $output = -1;

	#first check if service name exist
	if ( $service =~ /(?=)/ && $service =~ /^$/ )
	{
		#error 2 eq $service is empty
		$output = 2;
		return $output;
	}

	#check the correct string in the service
	my $newservice = &checkFarmnameOK( $service );
	if ( $newservice ne 0 )
	{
		$output = 3;
		return $output;
	}
	use File::Grep qw( fgrep fmap fdo );
	if ( !fgrep { /Service "$service"/ } "$configdir/$fname\_pound.cfg" )
	{
		#create service
		my @newservice;
		my $sw    = 0;
		my $count = 0;
		tie @poundtpl, 'Tie::File', "$poundtpl";
		my $countend = 0;
		foreach $line ( @poundtpl )
		{

			if ( $line =~ /Service \"\[DESC\]\"/ )
			{
				$sw = 1;
			}

			if ( $sw eq "1" )
			{
				push ( @newservice, $line );
			}

			if ( $line =~ /End/ )
			{
				$count++;
			}

			if ( $count eq "4" )
			{
				last;
			}
		}
		untie @poundtpl;

		@newservice[0] =~ s/#//g;
		@newservice[$#newservice] =~ s/#//g;

		my @fileconf;
		tie @fileconf, 'Tie::File', "$configdir/$fname\_pound.cfg";
		my $i    = 0;
		my $type = "";
		$type = &getFarmType( $farmname );
		foreach $line ( @fileconf )
		{
			if ( $line =~ /#ZWACL-END/ )
			{
				foreach $lline ( @newservice )
				{
					if ( $lline =~ /\[DESC\]/ )
					{
						$lline =~ s/\[DESC\]/$service/;
					}
					if (    $lline =~ /StrictTransportSecurity/
						 && $type eq "https" )
					{
						$lline =~ s/#//;
					}
					splice @fileconf, $i, 0, "$lline";
					$i++;
				}
				last;
			}
			$i++;
		}
		untie @fileconf;
		$output = 0;
	}
	else
	{
		$output = 1;
	}

	return $output;
}

#Create a new farm service
sub setFarmNewService($fname,$service)
{
	my ( $fname, $svice ) = @_;

	my $type   = &getFarmType( $fname );
	my $output = -1;

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &setFarmHTTPNewService( $fname, $svice );
	}

	return $output;
}

#delete a service in a Farm
sub deleteFarmService($farmname,$service)
{
	my ( $fname, $service ) = @_;

	my $ffile = &getFarmFile( $fname );
	my @fileconf;
	my $line;
	use Tie::File;
	tie @fileconf, 'Tie::File', "$configdir/$ffile";
	my $sw     = 0;
	my $output = -1;

	# Stop FG service
	&runFarmGuardianStop( $farmname, $service );

	my $i = 0;
	for ( $i = 0 ; $i < $#fileconf ; $i++ )
	{
		$line = @fileconf[$i];
		if ( $sw eq "1" && ( $line =~ /ZWACL-END/ || $line =~ /Service/ ) )
		{
			$output = 0;
			last;
		}

		if ( $sw == 1 )
		{
			splice @fileconf, $i, 1,;
			$i--;
		}

		if ( $line =~ /Service "$service"/ )
		{
			$sw = 1;
			splice @fileconf, $i, 1,;
			$i--;
		}
	}
	untie @fileconf;

	return $output;
}

#function that return indicated value from a HTTP Service
#vs return virtual server
sub getHTTPFarmVS($ffile,$service,$tag)
{
	my ( $ffile, $service, $tag ) = @_;
	my $output = "";

	my @fileconf;
	my $line;
	use Tie::File;
	tie @fileconf, 'Tie::File', "$configdir/$ffile";
	my $sw = 0;
	my @return;
	my $be_section = 0;
	my $be         = -1;
	my @output;
	my $sw_ti     = 0;
	my $output_ti = "";
	my $sw_pr     = 0;
	my $output_pr = "";

	foreach $line ( @fileconf )
	{
		if ( $line =~ /^\tService/ )
		{
			$sw = 0;
		}
		if ( $line =~ /^\tService \"$service\"/ )
		{
			$sw = 1;
		}

		# returns all services for this farm
		if ( $tag eq "" && $service eq "" )
		{
			if ( $line =~ /^\tService\ \"/ && $line !~ "#" )
			{
				@return = split ( "\ ", $line );
				@return[1] =~ s/\"//g;
				@return[1] =~ s/^\s+//;
				@return[1] =~ s/\s+$//;
				$output = "$output @return[1]";
			}
		}

		#vs tag
		if ( $tag eq "vs" )
		{
			if ( $line =~ "HeadRequire" && $sw == 1 && $line !~ "#" )
			{
				@return = split ( "Host:", $line );
				@return[1] =~ s/\"//g;
				@return[1] =~ s/^\s+//;
				@return[1] =~ s/\s+$//;
				$output = @return[1];
				last;

			}
		}

		#url pattern
		if ( $tag eq "urlp" )
		{
			if ( $line =~ "Url \"" && $sw == 1 && $line !~ "#" )
			{
				@return = split ( "Url", $line );
				@return[1] =~ s/\"//g;
				@return[1] =~ s/^\s+//;
				@return[1] =~ s/\s+$//;
				$output = @return[1];
				last;
			}
		}

		#redirect
		if ( $tag eq "redirect" )
		{
			if (    ( $line =~ "Redirect \"" || $line =~ "RedirectAppend \"" )
				 && $sw == 1
				 && $line !~ "#" )
			{
				if ( $line =~ "Redirect \"" )
				{
					@return = split ( "Redirect", $line );
				}
				elsif ( $line =~ "RedirectAppend \"" )
				{
					@return = split ( "RedirectAppend", $line );
				}
				@return[1] =~ s/\"//g;
				@return[1] =~ s/^\s+//;
				@return[1] =~ s/\s+$//;
				$output = @return[1];
				last;
			}
		}
		if ( $tag eq "redirecttype" )
		{
			if (    ( $line =~ "Redirect \"" || $line =~ "RedirectAppend \"" )
				 && $sw == 1
				 && $line !~ "#" )
			{
				if ( $line =~ "Redirect \"" )
				{
					$output = "default";
				}
				elsif ( $line =~ "RedirectAppend \"" )
				{
					$output = "append";
				}
				last;
			}
		}

		#cookie insertion
		if ( $tag eq "cookieins" )
		{
			if ( $line =~ "BackendCookie \"" && $sw == 1 && $line !~ "#" )
			{
				$output = "true";
				last;
			}
		}

		#cookie insertion name
		if ( $tag eq "cookieins-name" )
		{
			if ( $line =~ "BackendCookie \"" && $sw == 1 && $line !~ "#" )
			{
				$l = $line;
				$l =~ s/\t\t//g;
				$l =~ s/\"//g;
				my @values = split ( "\ ", $l );
				$output = @values[1];
				chomp ( $output );
				last;
			}
		}

		#cookie insertion Domain
		if ( $tag eq "cookieins-domain" )
		{
			if ( $line =~ "BackendCookie \"" && $sw == 1 && $line !~ "#" )
			{
				$l = $line;
				$l =~ s/\t\t//g;
				$l =~ s/\"//g;
				my @values = split ( "\ ", $l );
				$output = @values[2];
				chomp ( $output );
				last;
			}
		}

		#cookie insertion Path
		if ( $tag eq "cookieins-path" )
		{
			if ( $line =~ "BackendCookie \"" && $sw == 1 && $line !~ "#" )
			{
				$l = $line;
				$l =~ s/\t\t//g;
				$l =~ s/\"//g;
				my @values = split ( "\ ", $l );
				$output = @values[3];
				chomp ( $output );
				last;
			}
		}

		#cookie insertion TTL
		if ( $tag eq "cookieins-ttlc" )
		{
			if ( $line =~ "BackendCookie \"" && $sw == 1 && $line !~ "#" )
			{
				$l = $line;
				$l =~ s/\t\t//g;
				$l =~ s/\"//g;
				my @values = split ( "\ ", $l );
				$output = @values[4];
				chomp ( $output );
				last;
			}
		}

		#dynscale
		if ( $tag eq "dynscale" )
		{
			if ( $line =~ "DynScale\ " && $sw == 1 && $line !~ "#" )
			{
				$output = "true";
				last;
			}

		}

		#sesstion type
		if ( $tag eq "sesstype" )
		{
			if ( $line =~ "Type" && $sw == 1 && $line !~ "#" )
			{
				@return = split ( "\ ", $line );
				@return[1] =~ s/\"//g;
				@return[1] =~ s/^\s+//;
				@return[1] =~ s/\s+$//;
				$output = @return[1];
				last;
			}
		}

		#ttl
		if ( $tag eq "ttl" )
		{
			if ( $line =~ "TTL" && $sw == 1 && $line !~ "#" )
			{
				@return = split ( "\ ", $line );
				@return[1] =~ s/\"//g;
				@return[1] =~ s/^\s+//;
				@return[1] =~ s/\s+$//;
				$output = @return[1];
				last;
			}
		}

		#session id
		if ( $tag eq "sessionid" )
		{
			if ( $line =~ "\t\t\tID" && $sw == 1 && $line !~ "#" )
			{
				@return = split ( "\ ", $line );
				@return[1] =~ s/\"//g;
				@return[1] =~ s/^\s+//;
				@return[1] =~ s/\s+$//;
				$output = @return[1];
				last;
			}
		}

		#HTTPS tag
		if ( $tag eq "httpsbackend" )
		{
			if ( $line =~ "##True##HTTPS-backend##" && $sw == 1 )
			{
				$output = "true";
				last;
			}
		}

		#backends
		if ( $tag eq "backends" )
		{
			if ( $line =~ /#BackEnd/ && $sw == 1 )
			{
				$be_section = 1;
			}
			if ( $be_section == 1 )
			{

				#if ($line =~ /Address/ && $be >=1){
				if (    $line =~ /End/
					 && $line !~ /#/
					 && $sw == 1
					 && $be_section == 1
					 && $line !~ /BackEnd/ )
				{
					if ( $sw_ti == 0 )
					{
						$output_ti = "TimeOut -";
					}
					if ( $sw_pr == 0 )
					{
						$output_pr = "Priority -";
					}
					$output    = "$output $outputa $outputp $output_ti $output_pr\n";
					$output_ti = "";
					$output_pr = "";
					$sw_ti     = 0;
					$sw_pr     = 0;
				}
				if ( $line =~ /Address/ )
				{
					$be++;
					chomp ( $line );
					$outputa = "Server $be $line";
				}
				if ( $line =~ /Port/ )
				{
					chomp ( $line );
					$outputp = "$line";
				}
				if ( $line =~ /TimeOut/ )
				{
					chomp ( $line );

					#$output = $output . "$line";
					$output_ti = $line;
					$sw_ti     = 1;
				}
				if ( $line =~ /Priority/ )
				{
					chomp ( $line );

					#$output = $output . "$line";
					$output_pr = $line;
					$sw_pr     = 1;
				}
			}
			if ( $sw == 1 && $be_section == 1 && $line =~ /#End/ )
			{
				last;
			}
		}
	}
	untie @fileconf;

	return $output;
}

#set values for a service
sub setHTTPFarmVS($ffile,$service,$tag,$string)
{
	my ( $ffile, $service, $tag, $string ) = @_;
	my $output = "";

	my @fileconf;
	my $line;
	use Tie::File;
	tie @fileconf, 'Tie::File', "$configdir/$ffile";
	my $sw = 0;
	my @vserver;

	$j = -1;
	foreach $line ( @fileconf )
	{
		$j++;
		if ( $line =~ /Service \"$service\"/ )
		{
			$sw = 1;
		}
		$string =~ s/^\s+//;
		$string =~ s/\s+$//;

		#vs tag
		if ( $tag eq "vs" )
		{
			if ( $line =~ "HeadRequire" && $sw == 1 && $string ne "" )
			{
				$line = "\t\tHeadRequire \"Host: $string\"";
				last;
			}
			if ( $line =~ "HeadRequire" && $sw == 1 && $string eq "" )
			{
				$line = "\t\t#HeadRequire \"Host:\"";
				last;
			}
		}

		#url pattern
		if ( $tag eq "urlp" )
		{
			if ( $line =~ "Url" && $sw == 1 && $string ne "" )
			{
				$line = "\t\tUrl \"$string\"";
				last;
			}
			if ( $line =~ "Url" & $sw == 1 && $string eq "" )
			{
				$line = "\t\t#Url \"\"";
				last;
			}
		}

		#dynscale
		if ( $tag eq "dynscale" )
		{
			if ( $line =~ "DynScale" && $sw == 1 && $string ne "" )
			{
				$line = "\t\tDynScale 1";
				last;
			}
			if ( $line =~ "DynScale" && $sw == 1 && $string eq "" )
			{
				$line = "\t\t#DynScale 1";
				last;
			}
		}

		#client redirect default
		if ( $tag eq "redirect" )
		{
			if (    ( $line =~ "Redirect\ \"" || $line =~ "RedirectAppend\ \"" )
				 && $sw == 1
				 && $string ne "" )
			{
				$line = "\t\tRedirect \"$string\"";
				last;
			}
			if (    ( $line =~ "Redirect\ \"" || $line =~ "RedirectAppend\ \"" )
				 && $sw == 1
				 && $string eq "" )
			{
				$line = "\t\t#Redirect \"\"";
				last;
			}
		}

		#client redirect append
		if ( $tag eq "redirectappend" )
		{
			if (    ( $line =~ "Redirect\ \"" || $line =~ "RedirectAppend\ \"" )
				 && $sw == 1
				 && $string ne "" )
			{
				$line = "\t\tRedirectAppend \"$string\"";
				last;
			}
			if (    ( $line =~ "Redirect\ \"" || $line =~ "RedirectAppend\ \"" )
				 && $sw == 1
				 && $string eq "" )
			{
				$line = "\t\t#Redirect \"\"";
				last;
			}
		}

		#cookie ins
		if ( $tag eq "cookieins" )
		{
			if ( $line =~ "BackendCookie" && $sw == 1 && $string ne "" )
			{
				$line =~ s/#//g;
				last;
			}
			if ( $line =~ "BackendCookie" && $sw == 1 && $string eq "" )
			{
				$line =~ s/\t\t//g;
				$line = "\t\t#$line";
				last;
			}
		}

		#cookie insertion name
		if ( $tag eq "cookieins-name" )
		{
			if ( $line =~ "BackendCookie" && $sw == 1 && $string ne "" )
			{
				$l = $line;
				$l =~ s/\t\t//g;
				my @values = split ( "\ ", $l );
				@values[1] =~ s/\"//g;
				$line = "\t\tBackendCookie \"$string\" @values[2] @values[3] @values[4]";
				last;
			}
		}

		#cookie insertion domain
		if ( $tag eq "cookieins-domain" )
		{
			if ( $line =~ "BackendCookie" && $sw == 1 && $string ne "" )
			{
				$l = $line;
				$l =~ s/\t\t//g;
				my @values = split ( "\ ", $l );
				@values[2] =~ s/\"//g;
				$line = "\t\tBackendCookie @values[1] \"$string\" @values[3] @values[4]";
				last;
			}
		}

		#cookie insertion path
		if ( $tag eq "cookieins-path" )
		{
			if ( $line =~ "BackendCookie" && $sw == 1 && $string ne "" )
			{
				$l = $line;
				$l =~ s/\t\t//g;
				my @values = split ( "\ ", $l );
				@values[3] =~ s/\"//g;
				$line = "\t\tBackendCookie @values[1] @values[2] \"$string\" @values[4]";
				last;
			}
		}

		#cookie insertion TTL
		if ( $tag eq "cookieins-ttlc" )
		{
			if ( $line =~ "BackendCookie" && $sw == 1 && $string ne "" )
			{
				$l = $line;
				$l =~ s/\t\t//g;
				my @values = split ( "\ ", $l );
				@values[4] =~ s/\"//g;
				$line = "\t\tBackendCookie @values[1] @values[2] @values[3] $string";
				last;
			}
		}

		#TTL
		if ( $tag eq "ttl" )
		{
			if ( $line =~ "TTL" && $sw == 1 && $string ne "" )
			{
				$line = "\t\t\tTTL $string";
				last;
			}
			if ( $line =~ "TTL" && $sw == 1 && $string eq "" )
			{
				$line = "\t\t\t#TTL 120";
				last;
			}
		}

		#session id
		if ( $tag eq "sessionid" )
		{
			if ( $line =~ "\t\t\tID|\t\t\t#ID" && $sw == 1 && $string ne "" )
			{
				$line = "\t\t\tID \"$string\"";
				last;
			}
			if ( $line =~ "\t\t\tID|\t\t\t#ID" && $sw == 1 && $string eq "" )
			{
				$line = "\t\t\t#ID \"$string\"";
				last;
			}
		}

		#HTTPS Backends tag
		if ( $tag eq "httpsbackend" )
		{
			if ( $line =~ "##HTTPS-backend##" && $sw == 1 && $string ne "" )
			{
				#turn on
				$line = "\t\t##True##HTTPS-backend##";
			}

			#
			if ( $line =~ "##HTTPS-backend##" && $sw == 1 && $string eq "" )
			{
				#turn off
				$line = "\t\t##False##HTTPS-backend##";
			}

			#Delete HTTPS tag in a BackEnd
			if ( $sw == 1 && $line =~ /HTTPS$/ && $string eq "" )
			{
				#Delete HTTPS tag
				splice @fileconf, $j, 1,;
			}

			#Add HTTPS tag
			if ( $sw == 1 && $line =~ /BackEnd$/ && $string ne "" )
			{
				if ( @fileconf[$j + 1] =~ /Address\ .*/ )
				{
					#add new line with HTTPS tag
					splice @fileconf, $j + 1, 0, "\t\t\tHTTPS";
				}
			}

			#go out of curret Service
			if (    $line =~ /Service \"/
				 && $sw == 1
				 && $line !~ /Service \"$service\"/ )
			{
				$tag = "";
				$sw  = 0;
				last;
			}
		}

		#session type
		if ( $tag eq "session" )
		{
			if ( $session ne "nothing" && $sw == 1 )
			{
				if ( $line =~ "Session" )
				{
					$line = "\t\tSession";
				}
				if ( $line =~ "End" )
				{
					$line = "\t\tEnd";
				}
				if ( $line =~ "Type" )
				{
					$line = "\t\t\tType $session";
				}
				if ( $line =~ "TTL" )
				{
					$line =~ s/#//g;
				}
				if (    $session eq "URL"
					 || $session eq "COOKIE"
					 || $session eq "HEADER" )
				{
					if ( $line =~ "\t\t\tID |\t\t\t#ID " )
					{
						$line =~ s/#//g;
					}
				}
				if ( $session eq "IP" )
				{
					if ( $line =~ "\t\t\tID |\t\t\t#ID " )
					{
						$line = "\#$line";
					}
				}
				$output = $?;
			}
			if ( $session eq "nothing" && $sw == 1 )
			{
				if ( $line =~ "Session" )
				{
					$line = "\t\t#Session";
				}
				if ( $line =~ "End" )
				{
					$line = "\t\t#End";
				}
				if ( $line =~ "TTL" )
				{
					$line = "\t\t\t#TTL 120";
				}
				if ( $line =~ "Type" )
				{
					$line = "\t\t\t#Type nothing";
				}
				if ( $line =~ "\t\t\tID |\t\t\t#ID " )
				{
					$line = "\t\t\t#ID \"sessionname\"";
				}
			}
			if ( $sw == 1 && $line =~ /End/ )
			{
				last;
			}
		}
	}
	untie @fileconf;

	return $output;
}

#get index of a service in a http farm
sub getFarmVSI($farmname,$sv)
{
	my ( $fname, $svice ) = @_;
	my $output;
	my @line;
	my $index;
	my $l;
	my @content = &getFarmBackendStatusCtl( $fname );

	foreach ( @content )
	{
		if ( $_ =~ /Service \"$svice\"/ )
		{
			$l     = $_;
			@line  = split ( '\.', $l );
			$index = @line[0];
		}
	}
	$index =~ s/\"//g;
	$index =~ s/^\s+//;
	$index =~ s/\s+$//;
	$output = $index;

	return $output;
}

# setFarmBackendsSessionsRemove not in use???
#function that removes all the active sessions enabled to a backend in a given service
#needed: farmname, serviceid, backendid
#~ sub setFarmBackendsSessionsRemove($fname,$svice,$backendid)
#~ {
#~ ( $fname, $svice, $backendid ) = @_;
#~
#~ my @content = &getFarmBackendStatusCtl( $fname );
#~ my @sessions = &getFarmBackendsClientsList( $fname, @content );
#~ my @service;
#~ my $sw = 0;
#~ my $sviceid;
#~ my @sessionid;
#~ my $sessid;
#~
#~ &logfile(
#~ "Deleting established sessions to a backend $backendid from farm $fname in service $svice"
#~ );
#~
#~ foreach ( @content )
#~ {
#~ if ( $_ =~ /Service/ && $sw eq 1 )
#~ {
#~ $sw = 0;
#~ }
#~
#~ if ( $_ =~ /Service\ \"$svice\"/ && $sw eq 0 )
#~ {
#~ $sw      = 1;
#~ @service = split ( /\./, $_ );
#~ $sviceid = @service[0];
#~ }
#~
#~ if ( $_ =~ /Session.*->\ $backendid/ && $sw eq 1 )
#~ {
#~ @sessionid  = split ( /Session/, $_ );
#~ $sessionid2 = @sessionid[1];
#~ @sessionid  = split ( /\ /, $sessionid2 );
#~ $sessid     = @sessionid[1];
#~ @output     = `$poundctl -c  /tmp/$fname\_pound.socket -n 0 $sviceid $sessid`;
#~ &logfile(
#~ "Executing:  $poundctl -c /tmp/$fname\_pound.socket -n 0 $sviceid $sessid" );
#~ }
#~ }
#~ }

# do not remove this
1
