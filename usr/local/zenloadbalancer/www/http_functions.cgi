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

my $configdir = &getGlobalConfiguration('configdir');

=begin nd
Function: setFarmClientTimeout

	Configure the client time parameter for a HTTP farm.
	
Parameters:
	client - It is the time in seconds for the client time parameter
	farmname - Farm name

Returns:
	Integer - Error code: 0 on success, or -1 on failure.

=cut
sub setFarmClientTimeout    # ($client,$farm_name)
{
	my ( $client, $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		tie my @filefarmhttp, 'Tie::File', "$configdir/$farm_filename";

		my $i_f         = -1;
		my $array_count = @filefarmhttp;
		my $found       = "false";

		while ( $i_f <= $array_count && $found eq "false" )
		{
			$i_f++;

			if ( $filefarmhttp[$i_f] =~ /^Client/ )
			{
				&zenlog( "setting 'ClientTimeout $client' for $farm_name farm $farm_type" );
				$filefarmhttp[$i_f] = "Client\t\t $client";
				$output             = $?;
				$found              = "true";
			}
		}
		untie @filefarmhttp;
	}

	return $output;
}

=begin nd
Function: getFarmClientTimeout

	Return the client time parameter for a HTTP farm.
	
Parameters:
	farmname - Farm name

Returns:
	Integer - Return the seconds for client request timeout or -1 on failure.

=cut
sub getFarmClientTimeout    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		open FR, "<$configdir\/$farm_filename";
		my @file = <FR>;

		foreach my $line ( @file )
		{
			if ( $line =~ /^Client\t\t.*\d+/ )
			{
				my @line_aux = split ( "\ ", $line );
				$output = $line_aux[1];
			}
		}
		close FR;
	}

	return $output;
}


=begin nd
Function: setHTTPFarmSessionType

	Configure type of persistence
	
Parameters:
	session - type of session: nothing, HEADER, URL, COOKIE, PARAM, BASIC or IP
	farmname - Farm name

Returns:
	Integer - Error code: 0 on success, or -1 on failure.

=cut
sub setHTTPFarmSessionType    # ($session,$farm_name)
{
	my ( $session, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $farm_type     = &getFarmType( $farm_name );
	my $output        = -1;

	&zenlog( "setting 'Session type $session' for $farm_name farm $farm_type" );
	tie my @contents, 'Tie::File', "$configdir\/$farm_filename";
	my $i     = -1;
	my $found = "false";
	foreach my $line ( @contents )
	{
		$i++;
		if ( $session ne "nothing" )
		{
			if ( $line =~ "Session" )
			{
				$contents[$i] = "\t\tSession";
				$found = "true";
			}
			if ( $found eq "true" && $line =~ "End" )
			{
				$contents[$i] = "\t\tEnd";
				$found = "false";
			}
			if ( $line =~ "Type" )
			{
				$contents[$i] = "\t\t\tType $session";
				$output = $?;
				$contents[$i + 1] =~ s/#//g;
				if (    $session eq "URL"
					 || $session eq "COOKIE"
					 || $session eq "HEADER" )
				{
					$contents[$i + 2] =~ s/#//g;
				}
				else
				{
					if ( $contents[$i + 2] !~ /#/ )
					{
						$contents[$i + 2] =~ s/^/#/;
					}
				}
			}
		}
		if ( $session eq "nothing" )
		{
			if ( $line =~ "Session" )
			{
				$contents[$i] = "\t\t#Session $session";
				$found = "true";
			}
			if ( $found eq "true" && $line =~ "End" )
			{
				$contents[$i] = "\t\t#End";
				$found = "false";
			}
			if ( $line =~ "TTL" )
			{
				$contents[$i] = "#$contents[$i]";
			}
			if ( $line =~ "Type" )
			{
				$contents[$i] = "#$contents[$i]";
				$output = $?;
			}
			if ( $line =~ "ID" )
			{
				$contents[$i] = "#$contents[$i]";
			}
		}
	}
	untie @contents;
	return $output;
}


=begin nd
Function: getHTTPFarmSessionType

	Return the type of session persistence for a HTTP farm.
	
Parameters:
	farmname - Farm name

Returns:
	scalar - type of persistence or -1 on failure.

=cut
sub getHTTPFarmSessionType    # ($farm_name)
{
	my ( $farm_name ) = @_;
	my $output = -1;

	open FR, "<$configdir\/$farm_name";
	my @file = <FR>;
	foreach my $line ( @file )
	{
		if ( $line =~ /Type/ && $line !~ /#/ )
		{
			my @line_aux = split ( "\ ", $line );
			$output = $line_aux[1];
		}
	}
	close FR;

	return $output;
}


=begin nd
Function: setHTTPFarmBlacklistTime

	Configure check time for resurected back-end. It is a HTTP farm paramter.
	
Parameters:
	checktime - time for resurrected checks
	farmname - Farm name

Returns:
	Integer - Error code: 0 on success, or -1 on failure.

=cut
sub setHTTPFarmBlacklistTime    # ($blacklist_time,$farm_name)
{
	my ( $blacklist_time, $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	tie my @filefarmhttp, 'Tie::File', "$configdir/$farm_filename";
	my $i_f         = -1;
	my $array_count = @filefarmhttp;
	my $found       = "false";

	while ( $i_f <= $array_count && $found eq "false" )
	{
		$i_f++;
		if ( $filefarmhttp[$i_f] =~ /^Alive/ )
		{
			&zenlog(
					"setting 'Blacklist time $blacklist_time' for $farm_name farm $farm_type" );
			$filefarmhttp[$i_f] = "Alive\t\t $blacklist_time";
			$output             = $?;
			$found              = "true";
		}
	}
	untie @filefarmhttp;

	return $output;
}


=begin nd
Function: getHTTPFarmBlacklistTime

	Return  time for resurrected checks for a HTTP farm.
	
Parameters:
	farmname - Farm name

Returns:
	integer - seconds for check or -1 on failure.

=cut
sub getHTTPFarmBlacklistTime    # ($farm_filename)
{
	my ( $farm_filename ) = @_;
	my $blacklist_time = -1;

	open FR, "<$configdir\/$farm_filename";
	my @file = <FR>;
	foreach my $line ( @file )
	{
		if ( $line =~ /Alive/i )
		{
			my @line_aux = split ( "\ ", $line );
			$blacklist_time = $line_aux[1];
		}
	}
	close FR;

	return $blacklist_time;
}


=begin nd
Function: setFarmHttpVerb

	Configure the accepted HTTP verb for a HTTP farm.
	The accepted verb sets are: 
		0. standardHTTP, for the verbs GET, POST, HEAD.
		1. extendedHTTP, add the verbs PUT, DELETE.
		2. standardWebDAV, add the verbs LOCK, UNLOCK, PROPFIND, PROPPATCH, SEARCH, MKCOL, MOVE, COPY, OPTIONS, TRACE, MKACTIVITY, CHECKOUT, MERGE, REPORT.
		3. MSextWebDAV, add the verbs SUBSCRIBE, UNSUBSCRIBE, NOTIFY, BPROPFIND, BPROPPATCH, POLL, BMOVE, BCOPY, BDELETE, CONNECT.
		4. MSRPCext, add the verbs RPC_IN_DATA, RPC_OUT_DATA.
	
Parameters:
	verb - accepted verbs: 0, 1, 2, 3 or 4
	farmname - Farm name

Returns:
	Integer - Error code: 0 on success, or -1 on failure.

=cut
sub setFarmHttpVerb    # ($verb,$farm_name)
{
	my ( $verb, $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		tie my @filefarmhttp, 'Tie::File', "$configdir/$farm_filename";
		my $i_f         = -1;
		my $array_count = @filefarmhttp;
		my $found       = "false";
		while ( $i_f <= $array_count && $found eq "false" )
		{
			$i_f++;
			if ( $filefarmhttp[$i_f] =~ /xHTTP/ )
			{
				&zenlog( "setting 'Http verb $verb' for $farm_name farm $farm_type" );
				$filefarmhttp[$i_f] = "\txHTTP $verb";
				$output             = $?;
				$found              = "true";
			}
		}
		untie @filefarmhttp;
	}

	return $output;
}


=begin nd
Function: getFarmHttpVerb

	Return the available verb set for a HTTP farm.
	The possible verb sets are: 
		0. standardHTTP, for the verbs GET, POST, HEAD.
		1. extendedHTTP, add the verbs PUT, DELETE.
		2. standardWebDAV, add the verbs LOCK, UNLOCK, PROPFIND, PROPPATCH, SEARCH, MKCOL, MOVE, COPY, OPTIONS, TRACE, MKACTIVITY, CHECKOUT, MERGE, REPORT.
		3. MSextWebDAV, add the verbs SUBSCRIBE, UNSUBSCRIBE, NOTIFY, BPROPFIND, BPROPPATCH, POLL, BMOVE, BCOPY, BDELETE, CONNECT.
		4. MSRPCext, add the verbs RPC_IN_DATA, RPC_OUT_DATA.
	
Parameters:
	farmname - Farm name

Returns:
	integer - return the verb set identier or -1 on failure.

=cut
sub getFarmHttpVerb    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		open FR, "<$configdir\/$farm_filename";
		my @file = <FR>;
		foreach my $line ( @file )
		{
			if ( $line =~ /xHTTP/ )
			{
				my @line_aux = split ( "\ ", $line );
				$output = $line_aux[1];
			}
		}
		close FR;
	}

	return $output;
}


=begin nd
Function: setFarmListen

	Change a HTTP farm between HTTP and HTTPS listener
	
Parameters:
	farmname - Farm name
	listener - type of listener: http or https

Returns:
	none - .
	
FIXME 
	not return nothing, use $found variable to return success or error

=cut
sub setFarmListen    # ( $farm_name, $farmlisten )
{
	my ( $farm_name, $flisten ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	tie my @filefarmhttp, 'Tie::File', "$configdir/$farm_filename";
	my $i_f         = -1;
	my $array_count = @filefarmhttp;
	my $found       = "false";
	while ( $i_f <= $array_count && $found eq "false" )
	{
		$i_f++;
		if ( $filefarmhttp[$i_f] =~ /^ListenHTTP/ && $flisten eq "http" )
		{
			$filefarmhttp[$i_f] = "ListenHTTP";
		}
		if ( $filefarmhttp[$i_f] =~ /^ListenHTTP/ && $flisten eq "https" )
		{
			$filefarmhttp[$i_f] = "ListenHTTPS";
		}

		#
		if ( $filefarmhttp[$i_f] =~ /.*Cert\ \"/ && $flisten eq "http" )
		{
			$filefarmhttp[$i_f] =~ s/Cert\ \"/#Cert\ \"/;
		}
		if ( $filefarmhttp[$i_f] =~ /.*Cert\ \"/ && $flisten eq "https" )
		{
			$filefarmhttp[$i_f] =~ s/#//g;

		}

		#
		if ( $filefarmhttp[$i_f] =~ /.*Ciphers\ \"/ && $flisten eq "http" )
		{
			$filefarmhttp[$i_f] =~ s/Ciphers\ \"/#Ciphers\ \"/;
		}
		if ( $filefarmhttp[$i_f] =~ /.*Ciphers\ \"/ && $flisten eq "https" )
		{
			$filefarmhttp[$i_f] =~ s/#//g;

		}

		# Enable 'Disable SSLv3'
		if ( $filefarmhttp[$i_f] =~ /.*Disable SSLv3$/ && $flisten eq "http" )
		{
			$filefarmhttp[$i_f] =~ s/Disable SSLv3/#Disable SSLv3/;
		}
		elsif ( $filefarmhttp[$i_f] =~ /.*DisableSSLv3$/ && $flisten eq "http" )
		{
			$filefarmhttp[$i_f] =~ s/DisableSSLv3/#DisableSSLv3/;
		}
		if ( $filefarmhttp[$i_f] =~ /.*Disable SSLv3$/ && $flisten eq "https" )
		{
			$filefarmhttp[$i_f] =~ s/#//g;
		}
		elsif (    $filefarmhttp[$i_f] =~ /.*DisableSSLv3$/
				&& $flisten eq "https" )
		{
			$filefarmhttp[$i_f] =~ s/#//g;
		}

		# Enable SSLHonorCipherOrder
		if (    $filefarmhttp[$i_f] =~ /.*SSLHonorCipherOrder/
			 && $flisten eq "http" )
		{
			$filefarmhttp[$i_f] =~ s/SSLHonorCipherOrder/#SSLHonorCipherOrder/;
		}
		if (    $filefarmhttp[$i_f] =~ /.*SSLHonorCipherOrder/
			 && $flisten eq "https" )
		{
			$filefarmhttp[$i_f] =~ s/#//g;
		}

		# Enable StrictTransportSecurity
		if (    $filefarmhttp[$i_f] =~ /.*StrictTransportSecurity/
			 && $flisten eq "http" )
		{
			$filefarmhttp[$i_f] =~ s/StrictTransportSecurity/#StrictTransportSecurity/;
		}
		if (    $filefarmhttp[$i_f] =~ /.*StrictTransportSecurity/
			 && $flisten eq "https" )
		{
			$filefarmhttp[$i_f] =~ s/#//g;
		}

		# Check for ECDHCurve cyphers
		if ( $filefarmhttp[$i_f] =~ /^\#*ECDHCurve/ && $flisten eq "http" )
		{
			$filefarmhttp[$i_f] =~ s/.*ECDHCurve/\#ECDHCurve/;
		}
		if ( $filefarmhttp[$i_f] =~ /^\#*ECDHCurve/ && $flisten eq "https" )
		{
			$filefarmhttp[$i_f] =~ s/.*ECDHCurve.*/ECDHCurve\t"prime256v1"/;
		}

		# Generate DH Keys if needed
		#my $dhfile = "$configdir\/$farm_name\_dh2048.pem";
		if ( $filefarmhttp[$i_f] =~ /^\#*DHParams/ && $flisten eq "http" )
		{
			$filefarmhttp[$i_f] =~ s/.*DHParams/\#DHParams/;
			#&setHTTPFarmDHStatus( $farm_name, "off" );
		}
		if ( $filefarmhttp[$i_f] =~ /^\#*DHParams/ && $flisten eq "https" )
		{
			$filefarmhttp[$i_f] =~ s/.*DHParams/DHParams/;
			#$filefarmhttp[$i_f] =~ s/.*DHParams.*/DHParams\t"$dhfile"/;
			#&setHTTPFarmDHStatus( $farm_name, "on" );
			#&genDHFile ( $farm_name );
		}

		if ( $filefarmhttp[$i_f] =~ /ZWACL-END/ )
		{
			$found = "true";
		}

	}
	untie @filefarmhttp;
}


=begin nd
Function: getHTTPFarmDHStatus

	Obtain the status of the DH file

Parameters:
	farmname - Farm name

Returns:
	scalar - on, if it is actived or off, if it is desactived

=cut
sub getHTTPFarmDHStatus    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = "off";

	my $dhfile = "$configdir\/$farm_name\_dh2048.pem";
	tie my @filefarmhttp, 'Tie::File', "$configdir/$farm_filename";
	# my $match =~ /^DHParams.*/, @filefarmhttp; 
	my @match = grep ( /^DHParams.*/, @filefarmhttp ); 
	untie @filefarmhttp;

	if ($match[0] ne "" && -e "$dhfile"){
		$output = "on";
	}

	return $output;
}


=begin nd
Function: setHTTPFarmDHStatus

	[NOT USED] Configure the status of the DH file
	
Parameters:
	farmname - Farm name
	status - set a status for the DH file

Returns:
	Integer - Error code: 1 on success, or 0 on failure.

=cut
sub setHTTPFarmDHStatus    # ($farm_name, $newstatus)
{
	my ( $farm_name, $newstatus ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $dhfile = "$configdir\/$farm_name\_dh2048.pem";
	my $output        = 0;

	tie my @filefarmhttp, 'Tie::File', "$configdir/$farm_filename";
	foreach my $row (@filefarmhttp)
	{
		if ($row =~ /.*DHParams.*/)
		{
			$row =~ s/.*DHParams.*/DHParams\t"$dhfile"/ if $newstatus eq "on";
			$row =~ s/.*DHParams/\#DHParams/ if $newstatus eq "off";
			$output = 1;
		}
	}
	untie @filefarmhttp;

	unlink ( "$dhfile" ) if -e "$dhfile" && $newstatus eq "off";

	return $output;
}


=begin nd
Function: setFarmRewriteL

	Asign a RewriteLocation vaue to a farm HTTP or HTTPS
	
Parameters:
	farmname - Farm name
	rewritelocation - The options are: disabled, enabled or enabled-backends

Returns:
	none - .

=cut
sub setFarmRewriteL    # ($farm_name,$rewritelocation)
{
	my ( $farm_name, $rewritelocation ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	&zenlog( "setting 'Rewrite Location' for $farm_name to $rewritelocation" );

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		tie my @filefarmhttp, 'Tie::File', "$configdir/$farm_filename";
		my $i_f         = -1;
		my $array_count = @filefarmhttp;
		my $found       = "false";
		while ( $i_f <= $array_count && $found eq "false" )
		{
			$i_f++;
			if ( $filefarmhttp[$i_f] =~ /RewriteLocation\ .*/ )
			{
				$filefarmhttp[$i_f] = "\tRewriteLocation $rewritelocation";
				$output             = $?;
				$found              = "true";
			}
		}
		untie @filefarmhttp;
	}

}


=begin nd
Function: getFarmRewriteL

	Return RewriteLocation Header configuration HTTP and HTTPS farms

Parameters:
	farmname - Farm name

Returns:
	scalar - The possible values are: disabled, enabled, enabled-backends or -1 on failure

=cut
sub getFarmRewriteL    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		open FR, "<$configdir\/$farm_filename";
		my @file = <FR>;
		foreach my $line ( @file )
		{
			if ( $line =~ /RewriteLocation\ .*/ )
			{
				my @line_aux = split ( "\ ", $line );
				$output = $line_aux[1];
			}
		}
		close FR;
	}

	return $output;
}


=begin nd
Function: setFarmConnTO

	Configure connection time out value to a farm HTTP or HTTPS
	
Parameters:
	connectionTO - Conection time out in seconds
	farmname - Farm name

Returns:
	Integer - Error code: 0 on success, or -1 on failure.

=cut
sub setFarmConnTO    # ($tout,$farm_name)
{
	my ( $tout, $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	&zenlog( "setting 'ConnTo timeout $tout' for $farm_name farm $farm_type" );

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		tie my @filefarmhttp, 'Tie::File', "$configdir/$farm_filename";
		my $i_f         = -1;
		my $array_count = @filefarmhttp;
		my $found       = "false";
		while ( $i_f <= $array_count && $found eq "false" )
		{
			$i_f++;
			if ( $filefarmhttp[$i_f] =~ /^ConnTO.*/ )
			{
				$filefarmhttp[$i_f] = "ConnTO\t\t $tout";
				$output             = $?;
				$found              = "true";
			}
		}
		untie @filefarmhttp;
	}
	return $output;
}


=begin nd
Function: getFarmConnTO

	Return farm connecton time out value for http and https farms

Parameters:
	farmname - Farm name

Returns:
	integer - return the connection time out or -1 on failure

=cut
sub getFarmConnTO    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		open FR, "<$configdir\/$farm_filename";
		my @file = <FR>;
		foreach my $line ( @file )
		{
			if ( $line =~ /^ConnTO/ )
			{
				my @line_aux = split ( "\ ", $line );
				$output = $line_aux[1];
			}
		}
		close FR;
	}

	return $output;
}


=begin nd
Function: setHTTPFarmTimeout

	Asign a timeout value to a farm
	
Parameters:
	timeout - Time out in seconds
	farmname - Farm name

Returns:
	Integer - Error code: 0 on success, or -1 on failure.

=cut
sub setHTTPFarmTimeout    # ($timeout,$farm_name)
{
	my ( $timeout, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	tie my @filefarmhttp, 'Tie::File', "$configdir/$farm_filename";
	my $i_f         = -1;
	my $array_count = @filefarmhttp;
	my $found       = "false";

	while ( $i_f <= $array_count && $found eq "false" )
	{
		$i_f++;
		if ( $filefarmhttp[$i_f] =~ /^Timeout/ )
		{
			$filefarmhttp[$i_f] = "Timeout\t\t $timeout";
			$output             = $?;
			$found              = "true";
		}
	}
	untie @filefarmhttp;

	return $output;
}


=begin nd
Function: getHTTPFarmTimeout

	Return the farm time out
	
Parameters:
	farmname - Farm name

Returns:
	Integer - Return time out, or -1 on failure.

=cut
sub getHTTPFarmTimeout    # ($farm_filename)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	open FR, "<$configdir\/$farm_filename";
	my @file = <FR>;

	foreach my $line ( @file )
	{
		if ( $line =~ /^Timeout/ )
		{
			my @line_aux = split ( "\ ", $line );
			$output = $line_aux[1];
		}
	}
	close FR;

	return $output;
}


=begin nd
Function: setHTTPFarmMaxClientTime

	Set the maximum time for a client
	
Parameters:
	maximumTO - Maximum client time
	farmname - Farm name

Returns:
	Integer - Error code: 0 on success, or -1 on failure.

=cut
sub setHTTPFarmMaxClientTime    # ($track,$farm_name)
{
	my ( $track, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $i_f           = -1;
	my $found         = "false";

	tie my @filefarmhttp, 'Tie::File', "$configdir/$farm_filename";
	my $array_count = @filefarmhttp;

	while ( $i_f <= $array_count && $found eq "false" )
	{
		$i_f++;
		if ( $filefarmhttp[$i_f] =~ /TTL/ )
		{
			$filefarmhttp[$i_f] = "\t\t\tTTL $track";
			$output             = $?;
			$found              = "true";
		}
	}
	untie @filefarmhttp;

	return $output;
}


=begin nd
Function: getHTTPFarmMaxClientTime

	Return the maximum time for a client
	
Parameters:
	farmname - Farm name

Returns:
	Integer - Return maximum time, or -1 on failure.

=cut
sub getHTTPFarmMaxClientTime    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my @max_client_time;

	push ( @max_client_time, "" );
	push ( @max_client_time, "" );
	open FR, "<$configdir\/$farm_filename";
	my @configfile = <FR>;

	foreach my $line ( @configfile )
	{
		if ( $line =~ /TTL/ )
		{
			my @line_aux = split ( "\ ", $line );
			@max_client_time[0] = "";
			@max_client_time[1] = $line_aux[1];
		}
	}
	close FR;

	return @max_client_time;
}


=begin nd
Function: setHTTPFarmMaxConn

	set the max conn of a farm
	
Parameters:
	none - .

Returns:
	Integer - always return 0

FIXME:
	This function is in blank

=cut
sub setHTTPFarmMaxConn    # ($max_connections,$farm_name)
{
	return 0;
}


=begin nd
Function: getFarmCertificate

	Return the certificate applied to the farm
	
Parameters:
	farmname - Farm name

Returns:
	scalar - Return the certificate file, or -1 on failure.

FIXME:
	If are there more than one certificate, only return the last one

=cut
sub getFarmCertificate    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "https" )
	{
		my $farm_filename = &getFarmFile( $farm_name );
		open FI, "<$configdir/$farm_filename";
		my @content = <FI>;
		close FI;
		foreach my $line ( @content )
		{
			if ( $line =~ /Cert/ && $line !~ /\#.*Cert/ )
			{
				my @partline = split ( '\"', $line );
				@partline = split ( "\/", $partline[1] );
				my $lfile = @partline;
				$output = $partline[$lfile - 1];
			}
		}
	}

	return $output;
}


=begin nd
Function: setFarmCertificate

	[NOT USED] Configure a certificate for a HTTP farm
	
Parameters:
	certificate - certificate file name
	farmname - Farm name

Returns:
	Integer - Error code: 0 on success, or -1 on failure.

FIXME:
	There is other function for this action: setFarmCertificateSNI

=cut
sub setFarmCertificate    # ($cfile,$farm_name)
{
	my ( $cfile, $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	&zenlog( "setting 'Certificate $cfile' for $farm_name farm $farm_type" );
	if ( $farm_type eq "https" )
	{
		use Tie::File;
		tie my @array, 'Tie::File', "$configdir/$farm_filename";
		for ( @array )
		{
			if ( $_ =~ /Cert "/ )
			{
				s/.*Cert\ .*/\tCert\ \"$configdir\/$cfile\"/g;
				$output = $?;
			}
		}
		untie @array;
	}

	return $output;
}


=begin nd
Function: getHTTPFarmGlobalStatus

	Get the status of a farm and its backends through pound command.
	
Parameters:
	farmname - Farm name

Returns:
	array - Return poundctl output 

=cut
sub getHTTPFarmGlobalStatus    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $poundctl = &getGlobalConfiguration('poundctl');

	return `$poundctl -c "/tmp/$farm_name\_pound.socket"`;
}


=begin nd
Function: getHTTPBackendEstConns

	Get all ESTABLISHED connections for a backend
	 
Parameters:
	farmname - Farm name
	ip_backend - IP backend
	port_backend - backend port
	netstat - Conntrack -L output

Returns:
	array - Return all ESTABLISHED conntrack lines for the backend
	
BUG:
	it is possible filter using farm Vip and port too. If a backend if defined in more than a farm, here it appers all them
	
=cut
sub getHTTPBackendEstConns     # ($farm_name,$ip_backend,$port_backend,@netstat)
{
	my ( $farm_name, $ip_backend, $port_backend, @netstat ) = @_;

	return
	  &getNetstatFilter(
		"tcp",
		"",
		"\.*ESTABLISHED src=\.* dst=.* sport=\.* dport=$port_backend \.*src=$ip_backend \.*",
		"",
		@netstat
	  );
}


=begin nd
Function: getHTTPFarmEstConns

	Get all ESTABLISHED connections for a farm
	 
Parameters:
	farmname - Farm name
	netstat - Conntrack -L output

Returns:
	array - Return all ESTABLISHED conntrack lines for a farm

=cut
sub getHTTPFarmEstConns    # ($farm_name,@netstat)
{
	my ( $farm_name, @netstat ) = @_;

	my $vip      = &getFarmVip( "vip",  $farm_name );
	my $vip_port = &getFarmVip( "vipp", $farm_name );

	return &getNetstatFilter(
		"tcp", "",

		".* ESTABLISHED src=.* dst=$vip sport=.* dport=$vip_port src=.*",
		"", @netstat
	);
}


=begin nd
Function: getHTTPBackendSYNConns

	Get all SYN connections for a backend
	 
Parameters:
	farmname - Farm name
	ip_backend - IP backend
	port_backend - backend port
	netstat - Conntrack -L output

Returns:
	array - Return all SYN conntrack lines for a backend of a farm

BUG:
	it is possible filter using farm Vip and port too. If a backend if defined in more than a farm, here it appers all them
	
=cut
sub getHTTPBackendSYNConns  # ($farm_name, $ip_backend, $port_backend, @netstat)
{
	my ( $farm_name, $ip_backend, $port_backend, @netstat ) = @_;

	return
	  &getNetstatFilter( "tcp", "",
				"\.*SYN\.* src=\.* dst=$ip_backend sport=\.* dport=$port_backend\.*",
				"", @netstat );
}


=begin nd
Function: getHTTPFarmSYNConns

	Get all SYN connections for a farm
	 
Parameters:
	farmname - Farm name
	netstat - Conntrack -L output

Returns:
	array - Return all SYN conntrack lines for a farm

=cut
sub getHTTPFarmSYNConns     # ($farm_name, @netstat)
{
	my ( $farm_name, @netstat ) = @_;

	my $vip      = &getFarmVip( "vip",  $farm_name );
	my $vip_port = &getFarmVip( "vipp", $farm_name );

	return
	  &getNetstatFilter( "tcp", "",
					   "\.* SYN\.* src=\.* dst=$vip \.* dport=$vip_port \.* src=\.*",
					   "", @netstat );
}


=begin nd
Function: setFarmErr

	Configure a error message for http error: 414, 500, 501 or 503
	 
Parameters:
	farmname - Farm name
	message - Message body for the error
	error_number - Number of error to set, the options are 414, 500, 501 or 503

Returns:
	Integer - Error code: 0 on success, or -1 on failure.

=cut
sub setFarmErr    # ($farm_name,$content,$nerr)
{
	my ( $farm_name, $content, $nerr ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	&zenlog( "setting 'Err $nerr' for $farm_name farm $farm_type" );
	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		if ( -e "$configdir\/$farm_name\_Err$nerr.html" && $nerr != "" )
		{
			$output = 0;
			my @err = split ( "\n", "$content" );
			open FO, ">$configdir\/$farm_name\_Err$nerr.html";
			foreach my $line ( @err )
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


=begin nd
Function: getFarmErr

	Return the error message for a http error: 414, 500, 501 or 503
	 
Parameters:
	farmname - Farm name
	error_number - Number of error to set, the options are 414, 500, 501 or 503

Returns:
	Array - Message body for the error

=cut
# Only http function
sub getFarmErr    # ($farm_name,$nerr)
{
	my ( $farm_name, $nerr ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my @output;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		open FR, "<$configdir\/$farm_filename";
		my @file = <FR>;
		foreach my $line ( @file )
		{
			if ( $line =~ /Err$nerr/ )
			{
				my @line_aux = split ( "\ ", $line );
				my $err = $line_aux[1];
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

	return @output;
}


=begin nd
Function: getHTTPFarmBootStatus

	Return the farm status at boot zevenet
	 
Parameters:
	farmname - Farm name

Returns:
	scalar - return "down" if the farm not run at boot or "up" if the farm run at boot

=cut
sub getHTTPFarmBootStatus    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = "down";
	my $lastline;
	my $line;

	open FO, "<$configdir/$farm_filename";
	while ( $line = <FO> )
	{
		$lastline = $line;
	}
	close FO;

	if ( $lastline !~ /^#down/ )
	{
		$output = "up";
	}

	return $output;
}


=begin nd
Function: validateHTTPFarmDH

	[NOT USED] Validate the farm Diffie Hellman configuration	 
	
Parameters:
	farmname - Farm name

Returns:
	Integer - always return -1
	
BUG
	Not finish

=cut
sub validateHTTPFarmDH    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	my $dhstatus = &getHTTPFarmDHStatus($farm_name);
	if ( $farm_type eq "https" && $dhstatus ne "on" )
	{
		my $lockstatus = &getFarmLock( $farm_name );
		if ( $lockstatus !~ /Diffie-Hellman/ ) {
			#$output = &setHTTPFarmDHStatus( $farm_name, "on" );
			#&genDHFile( $farm_name );
		}
	}

	if ( $farm_type eq "http" && $dhstatus ne "on" )
	{
		#$output = &setHTTPFarmDHStatus( $farm_name, "off" );
	}

	return $output;
}


=begin nd
Function: genDHFile

	[NOT USED] Generate the Diffie Hellman keys file
	
Parameters:
	farmname - Farm name

Returns:
	Integer - return 0 on success or different of 0 on failure
	
=cut
sub genDHFile    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = 0;

	my $dhfile = "$configdir\/$farm_name\_dh2048.pem";

	if ( ! -e "$dhfile" )
	{
		&zenlog( "Generating DH keys in $dhfile ..." );
		&setFarmLock( $farm_name, "on", "<a href=\"https://www.zenloadbalancer.com/knowledge-base/misc/diffie-hellman-keys-generation-important/\" target=\"_blank\">Generating SSL Diffie-Hellman 2048 keys</a> <img src=\"img/loading.gif\"/>" );

		my $openssl = &getGlobalConfiguration('openssl');
		system("$openssl dhparam -5 2048 -out $dhfile &");
		$output = $?;
	}

	return $output
}


=begin nd
Function: _runHTTPFarmStart

	Run a HTTP farm
	
Parameters:
	farmname - Farm name

Returns:
	Integer - return 0 on success or different of 0 on failure
	
FIXME: 
	Control error if fail when restore backend status
	
=cut
sub _runHTTPFarmStart    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $status        = -1;
	my $pound = &getGlobalConfiguration('pound');
	my $piddir = &getGlobalConfiguration('piddir');

	&zenlog( "Checking $farm_name farm configuration" );
	&getHTTPFarmConfigIsOK( $farm_name );

	&zenlog(
		"running $pound -f $configdir\/$farm_filename -p $piddir\/$farm_name\_pound.pid"
	);
	$status = &zsystem(
		"$pound -f $configdir\/$farm_filename -p $piddir\/$farm_name\_pound.pid 2>/dev/null"
	);

	if ( $status == 0 )
	{
		# set backend at status before that the farm stopped
		&setFarmHttpBackendStatus( $farm_name );
	}
	else
	{
		&zenlog( "Error, running $farm_name farm." );
	}

	return $status;
}


=begin nd
Function: _runHTTPFarmStop

	Stop a HTTP farm
	
Parameters:
	farmname - Farm name

Returns:
	Integer - return 0 on success or different of 0 on failure
		
=cut
sub _runHTTPFarmStop    # ($farm_name)
{
	my ( $farm_name ) = @_;
	my $status = -1;

	&runFarmGuardianStop( $farm_name, "" );

	if ( &getHTTPFarmConfigIsOK( $farm_name ) == 0 )
	{
		my $pid = &getFarmPid( $farm_name );
		my $piddir = &getGlobalConfiguration('piddir');

		&zenlog( "running 'kill 15, $pid'" );
		my $run = kill 15, $pid;
		$status = $?;

		unlink ( "$piddir\/$farm_name\_pound.pid" ) if -e "$piddir\/$farm_name\_pound.pid";
		unlink ( "\/tmp\/$farm_name\_pound.socket" ) if -e "\/tmp\/$farm_name\_pound.socket";
		&setFarmLock( $farm_name, "off" );
	}
	else
	{
		&zenlog(
			 "Farm $farm_name can't be stopped, check the logs and modify the configuration"
		);
		return 1;
	}

	return $status;
}


=begin nd
Function: runHTTPFarmCreate

	Create a HTTP farm
	
Parameters:
	vip - Virtual IP where the virtual service is listening
	port - Virtual port where the virtual service is listening
	farmname - Farm name
	type - Specify if farm is HTTP or HTTPS

Returns:
	Integer - return 0 on success or different of 0 on failure
		
=cut
sub runHTTPFarmCreate    # ( $vip, $vip_port, $farm_name, $farm_type )
{
	my ( $vip, $vip_port, $farm_name, $farm_type ) = @_;

	my $output = -1;

	#copy template modyfing values
	use File::Copy;
	&zenlog( "copying pound tpl file on $farm_name\_pound.cfg" );
	my $poundtpl = &getGlobalConfiguration('poundtpl');
	copy( "$poundtpl", "$configdir/$farm_name\_pound.cfg" );

	#modify strings with variables
	use Tie::File;
	tie my @file, 'Tie::File', "$configdir/$farm_name\_pound.cfg";
	foreach my $line ( @file )
	{
		$line =~ s/\[IP\]/$vip/;
		$line =~ s/\[PORT\]/$vip_port/;
		$line =~ s/\[DESC\]/$farm_name/;
		$line =~ s/\[CONFIGDIR\]/$configdir/;
		if ( $farm_type eq "HTTPS" )
		{
			$line =~ s/ListenHTTP/ListenHTTPS/;
			$line =~ s/#Cert/Cert/;
		}
	}
	untie @file;

	#create files with personalized errors
	open FERR, ">$configdir\/$farm_name\_Err414.html";
	print FERR "Request URI is too long.\n";
	close FERR;
	open FERR, ">$configdir\/$farm_name\_Err500.html";
	print FERR "An internal server error occurred. Please try again later.\n";
	close FERR;
	open FERR, ">$configdir\/$farm_name\_Err501.html";
	print FERR "This method may not be used.\n";
	close FERR;
	open FERR, ">$configdir\/$farm_name\_Err503.html";
	print FERR "The service is not available. Please try again later.\n";
	close FERR;

	my $pound = &getGlobalConfiguration('pound');
	my $piddir = &getGlobalConfiguration('piddir');

	#run farm
	&zenlog(
		"running $pound -f $configdir\/$farm_name\_pound.cfg -p $piddir\/$farm_name\_pound.pid"
	);
	&zsystem(
		"$pound -f $configdir\/$farm_name\_pound.cfg -p $piddir\/$farm_name\_pound.pid 2>/dev/null"
	);
	$output = $?;

	return $output;
}


=begin nd
Function: getHTTPFarmMaxConn

	Returns farm max connections
	
Parameters:
	none - .

Returns:
	Integer - always return 0
	
FIXME:
	This function do nothing
		
=cut
sub getHTTPFarmMaxConn    # ($farm_name)
{
	return 0;
}


=begin nd
Function: getHTTPFarmPort

	Returns socket for HTTP farm
		
Parameters:
	farmname - Farm name

Returns:
	Integer - return socket file
	
FIXME:
	This funcion is only used in farmguardian functions. The function name must be called getHTTPFarmSocket, this function dont return the port
		
=cut
sub getHTTPFarmPort       # ($farm_name)
{
	my ( $farm_name ) = @_;

	return "/tmp/" . $farm_name . "_pound.socket";
}


=begin nd
Function: getHTTPFarmPid

	Returns farm PID
		
Parameters:
	farmname - Farm name

Returns:
	Integer - return pid of farm, '-' if pid not exist or -1 on failure
			
=cut
sub getHTTPFarmPid        # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $output = -1;
	my $piddir = &getGlobalConfiguration('piddir');

	my $pidfile = "$piddir\/$farm_name\_pound.pid";
	if ( -e $pidfile )
	{
		open FPID, "<$pidfile";
		my @pid = <FPID>;
		close FPID;

		my $pid_hprof = $pid[0];
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


=begin nd
Function: getFarmChildPid

	Returns farm Child PID 
		
Parameters:
	farmname - Farm name

Returns:
	Integer - return child pid of farm or -1 on failure
			
=cut
sub getFarmChildPid    # ($farm_name)
{
	my ( $farm_name ) = @_;
	use File::Grep qw( fgrep fmap fdo );

	my $farm_type = &getFarmType( $farm_name );
	my $fpid      = &getFarmPid( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		my $pids = `pidof -o $fpid pound`;
		my @pids = split ( " ", $pids );
		foreach my $pid ( @pids )
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


=begin nd
Function: getHTTPFarmVip

	Returns farm vip or farm port
		
Parameters:
	tag - requested parameter. The options are vip, for virtual ip or vipp, for virtual port
	farmname - Farm name

Returns:
	Scalar - return vip or port of farm or -1 on failure
	
FIXME
	vipps parameter is only used in tcp farms. Soon this parameter will be obsolet
			
=cut
sub getHTTPFarmVip    # ($info,$farm_name)
{
	my ( $info, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $i             = 0;

	open FI, "<$configdir/$farm_filename";
	my @file = <FI>;
	close FI;

	foreach my $line ( @file )
	{
		if ( $line =~ /^ListenHTTP/ )
		{
			my $vip  = $file[$i + 5];
			my $vipp = $file[$i + 6];

			chomp ( $vip );
			chomp ( $vipp );

			my @vip  = split ( "\ ", $vip );
			my @vipp = split ( "\ ", $vipp );

			if ( $info eq "vip" )   { $output = $vip[1]; }
			if ( $info eq "vipp" )  { $output = $vipp[1]; }
			if ( $info eq "vipps" ) { $output = "$vip[1]\:$vipp[1]"; }
		}
		$i++;
	}

	return $output;
}


=begin nd
Function: setHTTPFarmVirtualConf

	Set farm virtual IP and virtual PORT		
	
Parameters:
	vip - virtual ip
	port - virtual port
	farmname - Farm name

Returns:
	Integer - return 0 on success or different on failure
	
=cut
sub setHTTPFarmVirtualConf    # ($vip,$vip_port,$farm_name)
{
	my ( $vip, $vip_port, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $stat          = 0;
	my $enter         = 2;

	use Tie::File;
	tie my @array, 'Tie::File', "$configdir\/$farm_filename";
	my $size = @array;

	for ( my $i = 0 ; $i < $size && $enter > 0 ; $i++ )
	{
		if ( $array[$i] =~ /Address/ )
		{
			$array[$i] =~ s/.*Address\ .*/\tAddress\ $vip/g;
			$stat = $? || $stat;
			$enter--;
		}
		if ( $array[$i] =~ /Port/ )
		{
			$array[$i] =~ s/.*Port\ .*/\tPort\ $vip_port/g;
			$stat = $? || $stat;
			$enter--;
		}
	}
	untie @array;

	return $stat;
}


=begin nd
Function: setHTTPFarmServer

	Add a new backend to a HTTP service or modify if it exists
	
Parameters:
	ids - backend id
	rip - backend ip
	port - backend port
	priority - The priority of this backend (between 1 and 9). Higher priority backends will be used more often than lower priority ones
	timeout - Override the global time out for this backend
	farmname - Farm name
	service - service name

Returns:
	Integer - return 0 on success or -1 on failure
	
=cut
sub setHTTPFarmServer # ($ids,$rip,$port,$priority,$timeout,$farm_name,$service)
{
	my ( $ids, $rip, $port, $priority, $timeout, $farm_name, $service ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	tie my @contents, 'Tie::File', "$configdir\/$farm_filename";

	if ( $ids !~ /^$/ )
	{
		my $index_count = -1;
		my $i           = -1;
		my $sw          = 0;
		foreach my $line ( @contents )
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
					my $httpsbe = &getFarmVS( $farm_name, $service, "httpsbackend" );
					if ( $httpsbe eq "true" )
					{
						#add item
						$i++;
					}
					$output           = $?;
					$contents[$i + 1] = "\t\t\tAddress $rip";
					$contents[$i + 2] = "\t\t\tPort $port";
					my $p_m = 0;
					if ( $contents[$i + 3] =~ /TimeOut/ )
					{
						$contents[$i + 3] = "\t\t\tTimeOut $timeout";
						&zenlog( "Modified current timeout" );
					}
					if ( $contents[$i + 4] =~ /Priority/ )
					{
						$contents[$i + 4] = "\t\t\tPriority $priority";
						&zenlog( "Modified current priority" );
						$p_m = 1;
					}
					if ( $contents[$i + 3] =~ /Priority/ )
					{
						$contents[$i + 3] = "\t\t\tPriority $priority";
						$p_m = 1;
					}

					#delete item
					if ( $timeout =~ /^$/ )
					{
						if ( $contents[$i + 3] =~ /TimeOut/ )
						{
							splice @contents, $i + 3, 1,;
						}
					}
					if ( $priority =~ /^$/ )
					{
						if ( $contents[$i + 3] =~ /Priority/ )
						{
							splice @contents, $i + 3, 1,;
						}
						if ( $contents[$i + 4] =~ /Priority/ )
						{
							splice @contents, $i + 4, 1,;
						}
					}

					#new item
					if (
						 $timeout !~ /^$/
						 && (    $contents[$i + 3] =~ /End/
							  || $contents[$i + 3] =~ /Priority/ )
					  )
					{
						splice @contents, $i + 3, 0, "\t\t\tTimeOut $timeout";
					}
					if (
						    $p_m eq 0
						 && $priority !~ /^$/
						 && (    $contents[$i + 3] =~ /End/
							  || $contents[$i + 4] =~ /End/ )
					  )
					{
						if ( $contents[$i + 3] =~ /TimeOut/ )
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
		my $nsflag     = "true";
		my $index      = -1;
		my $backend    = 0;
		my $be_section = -1;

		foreach my $line ( @contents )
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
				my $httpsbe = &getFarmVS( $farm_name, $service, "httpsbackend" );
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
			my $idservice = &getFarmVSI( $farm_name, $service );
			if ( $idservice ne "" )
			{
				&getFarmHttpBackendStatus( $farm_name, $backend, "active", $idservice );
			}
		}
	}
	untie @contents;

	return $output;
}


=begin nd
Function: runHTTPFarmServerDelete

	Delete a backend in a HTTP service
	
Parameters:
	ids - backend id to delete it
	farmname - Farm name
	service - service name where is the backend

Returns:
	Integer - return 0 on success or -1 on failure
	
=cut
sub runHTTPFarmServerDelete    # ($ids,$farm_name,$service)
{
	my ( $ids, $farm_name, $service ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $i             = -1;
	my $j             = -1;
	my $sw            = 0;

	tie my @contents, 'Tie::File', "$configdir\/$farm_filename";

	foreach my $line ( @contents )
	{
		$i++;
		if ( $line =~ /Service \"$service\"/ )
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
				while ( $contents[$i] !~ /End/ )
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
		&runRemoveHTTPBackendStatus( $farm_name, $ids, $service );
	}

	return $output;
}


=begin nd
Function: getHTTPFarmBackendStatusCtl

	Get status of a HTTP farm and its backends
	
Parameters:
	farmname - Farm name

Returns:
	array - return the output of poundctl command for a farm
	
=cut
sub getHTTPFarmBackendStatusCtl    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $poundctl = &getGlobalConfiguration('poundctl');

	return `$poundctl -c  /tmp/$farm_name\_pound.socket`;
}


=begin nd
Function: getHTTPFarmBackendsStatus

	Function that return the status information of a farm: ip, port, backend status, weight, priority, clients, connections and service
	
Parameters:
	farmname - Farm name
	content - command output where parsing backend status

Returns:
	array - backends_data, each line is: "id" . "\t" . "ip" . "\t" . "port" . "\t" . "status" . "\t-\t" . "priority" . "\t" . "clients" . "\t" . "connections" . "\t" . "service"
	usage - @backend = split ( '\t', $backend_data )
				backend[0] = id, 
				backend[1] = ip, 
				backend[2] = port, 
				backend[3] = status,
				backend[4] = -, 
				backend[5] = priority, 
				backend[6] = clients, 
				backend[7] = connections, 
				backend[8] = service 
		
FIXME:
	Sustitute by getHTTPFarmBackendsStats function
	
=cut
sub getHTTPFarmBackendsStatus    # ($farm_name,@content)
{
	my ( $farm_name, @content ) = @_;

	my @backends_data;
	my @serviceline;
	my $service;
	my $connections;

	if ( !@content )
	{
		@content = &getFarmBackendStatusCtl( $farm_name );
	}

	foreach ( @content )
	{
		my @serviceline;
		if ( $_ =~ /Service/ )
		{
			@serviceline = split ( "\ ", $_ );
			$serviceline[2] =~ s/"//g;
			chomp ( $serviceline[2] );
			$service = $serviceline[2];
		}
		if ( $_ =~ /Backend/ )
		{
			#backend ID
			my @backends = split ( "\ ", $_ );
			$backends[0] =~ s/\.//g;
			my $line = $backends[0];

			#backend IP,PORT
			my @backends_ip  = split ( ":", $backends[2] );
			my $ip_backend   = $backends_ip[0];
			my $port_backend = $backends_ip[1];
			$line         = $line . "\t" . $ip_backend . "\t" . $port_backend;

			#status
			my $status_backend = $backends[7];
			my $backend_disabled = $backends[3];
			if ( $backend_disabled eq "DISABLED" )
			{
				#Checkstatusfile
				$status_backend =
				  &getHTTPBackendStatusFromFile( $farm_name, $backends[0], $service );
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
			my $priority_backend = $backends[4];
			$priority_backend =~ s/\(//g;
			$line = $line . "\t" . "-\t" . $priority_backend;
			my $clients = &getFarmBackendsClients( $backends[0], @content, $farm_name );
			if ( $clients != -1 )
			{
				$line = $line . "\t" . $clients;
			}
			else
			{
				$line = $line . "\t-";
			}

			$connections = $backends[8];
			$connections =~ s/[\(\)]//g;			
			if ( !( $connections >= 0 ) )
			{
				$connections = 0;
			}
			$line = $line . "\t" . $connections . "\t" . $service;
			
			push ( @backends_data, $line );
		}
	}
	return @backends_data;
}


=begin nd
Function: getHTTPFarmBackendsStats

	This function is the same than getHTTPFarmBackendsStatus but return a hash with http farm information
	This function take data from pounctl and it gives hash format 
	
Parameters:
	farmname - Farm name

Returns:
	hash ref - hash with backend farm stats
		
		backendStats = 
		{
			"farmname" = $farmname
			"queue" = $pending_conns
			"services" = \@services
		}
		
		\@servcies = 
		[
			{
				"id" = $service_id		# it is the index in the service array too
				"service" = $service_name
				"backends" = \@backends
				"sessions" = \@sessions
			}
		]
		
		\@backends = 
		[
			{
				"id" = $backend_id		# it is the index in the backend array too
				"ip" = $backend_ip
				"port" = $backend_port
				"status" = $backend_status
				"established" = $established_connections
			}
		]
		
		\@sessions = 
		[
			{
				"client" = $client_id 		# it is the index in the session array too
				"id" = $session_id		# id associated to a bacckend, it can change depend of session type
				"backends" = $backend_id
			}
		]
		
FIXME: 
		Put output format same format than "GET /stats/farms/BasekitHTTP"
		
=cut
sub getHTTPFarmBackendsStats    # ($farm_name,@content)
{
	my ( $farm_name ) = @_;

	my $stats;
	my @sessions;
	my $serviceName;
	my $hashService;
	my $firstService = 1;
	
	my $service_re = &getValidFormat( 'service' );

	#i.e. of poundctl:
	
	#Requests in queue: 0
	#0. http Listener 185.76.64.223:80 a
		#0. Service "HTTP" active (4)
		#0. Backend 172.16.110.13:80 active (1 0.780 sec) alive (61)
		#1. Backend 172.16.110.14:80 active (1 0.878 sec) alive (90)
		#2. Backend 172.16.110.11:80 active (1 0.852 sec) alive (99)
		#3. Backend 172.16.110.12:80 active (1 0.826 sec) alive (75)
	my @poundctl = &getHTTPFarmGlobalStatus ($farm_name);

	foreach my $line ( @poundctl )
	{
		#i.e.
		#Requests in queue: 0
		#~ if ( $line =~ /Requests in queue: (\d+)/ )
		#~ {
			#~ $stats->{ "queue" } = $1;
		#~ }
		
		# i.e.
		#     0. Service "HTTP" active (10)
		if ( $line =~ /(\d+)\. Service "($service_re)"/ )
		{
				$serviceName = $2;
		}
			
		# i.e.
		#      0. Backend 192.168.100.254:80 active (5 0.000 sec) alive (0)
		if ( $line =~ /(\d+)\. Backend (\d+\.\d+\.\d+\.\d+):(\d+) (\w+) .+ (\w+) \((\d+)\)/ )
		{
			my $backendHash =
 				{ 
					id => $1+0,
					ip => $2,
					port => $3+0,
					status => $5,
					established => $6+0,
					service => $serviceName,
				};
				
			my $backend_disabled = $4;
			if ( $backend_disabled eq "DISABLED" )
			{
				#Checkstatusfile
				$backendHash->{ "status" } =
				  &getHTTPBackendStatusFromFile( $farm_name, $backendHash->{id}, $serviceName );
			}
			elsif ( $backendHash->{ "status" } eq "alive" )
			{
				$backendHash->{ "status" } = "up";
			}
			elsif ( $backendHash->{ "status" } eq "DEAD" )
			{
				$backendHash->{ "status" } = "down";
			}
			
			push @{ $stats->{backends} }, $backendHash;
		}

		# i.e.
		#      1. Session 107.178.194.117 -> 1
		if ( $line =~ /(\d+)\. Session (.+) \-\> (\d+)/ )
		{
			push @{ $stats->{sessions} },
				{ 
					client => $1+0,
					session => $2,
					id => $3+0,
					service => $serviceName,
				};
		}
		
	}
	
	return $stats;
}


=begin nd
Function: getHTTPBackendStatusFromFile

	Function that return if a pound backend is active, down by farmguardian or it's in maintenance mode
	
Parameters:
	farmname - Farm name
	backend - backend id
	service - service name

Returns:
	scalar - return backend status: "maintentance", "fgDOWN", "active" or -1 on failure
		
=cut
sub getHTTPBackendStatusFromFile    # ($farm_name,$backend,$service)
{
	my ( $farm_name, $backend, $service ) = @_;
	my $index;
	my $line;
	my $stfile = "$configdir\/$farm_name\_status.cfg";
	# if the status file does not exist the backend is ok
	my $output = "active";

	if ( -e "$stfile" )
	{
		$index = &getFarmVSI( $farm_name, $service );
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


=begin nd
Function: getHTTPFarmBackendsClients

	Function that return number of clients with session in a backend server
	
Parameters:
	backend - backend id
	content - command output where parsing backend status
	farmname - Farm name

Returns:
	Integer - return number of clients in the backend
		
=cut
sub getHTTPFarmBackendsClients    # ($idserver,@content,$farm_name)
{
	my ( $idserver, @content, $farm_name ) = @_;

	if ( !@content )
	{
		@content = &getFarmBackendStatusCtl( $farm_name );
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


=begin nd
Function: getHTTPFarmBackendsClientsList

	Function that return sessions of clients
	
Parameters:
	farmname - Farm name
	content - command output where it must be parsed backend status

Returns:
	array - return information about existing sessions. The format for each line is: "service" . "\t" . "session_id" . "\t" . "session_value" . "\t" . "backend_id"
		
FIXME:
	will be useful change output format to hash format
	
=cut
sub getHTTPFarmBackendsClientsList    # ($farm_name,@content)
{
	my ( $farm_name, @content ) = @_;

	my @client_list;
	my $s;

	if ( !@content )
	{
		@content = &getFarmBackendStatusCtl( $farm_name );
	}

	foreach ( @content )
	{
		my $line;
		if ( $_ =~ /Service/ )
		{
			my @service = split ( "\ ", $_ );
			$s = $service[2];
			$s =~ s/"//g;
		}
		if ( $_ =~ / Session / )
		{
			my @sess = split ( "\ ", $_ );
			my $id = $sess[0];
			$id =~ s/\.//g;
			$line = $s . "\t" . $id . "\t" . $sess[2] . "\t" . $sess[4];
			push ( @client_list, $line );
		}
	}

	return @client_list;
}

=begin nd
Function: setHTTPNewFarmName

	Function that renames a farm. Before call this function, stop the farm.
	
Parameters:
	farmname - Farm name
	newfarmname - New farm name

Returns:
	Integer - return 0 on success or -1 on failure
		
=cut
sub setHTTPNewFarmName    # ($farm_name,$new_farm_name)
{
	my ( $farm_name, $new_farm_name ) = @_;

	my $output = 0;
	my @farm_configfiles = (
							 "$configdir\/$farm_name\_status.cfg",
							 "$configdir\/$farm_name\_pound.cfg",
							 "$configdir\/$farm_name\_Err414.html",
							 "$configdir\/$farm_name\_Err500.html",
							 "$configdir\/$farm_name\_Err501.html",
							 "$configdir\/$farm_name\_Err503.html",
							 "$farm_name\_guardian.conf"
	);
	my @new_farm_configfiles = (
								 "$configdir\/$new_farm_name\_status.cfg",
								 "$configdir\/$new_farm_name\_pound.cfg",
								 "$configdir\/$new_farm_name\_Err414.html",
								 "$configdir\/$new_farm_name\_Err500.html",
								 "$configdir\/$new_farm_name\_Err501.html",
								 "$configdir\/$new_farm_name\_Err503.html",
								 "$farm_name\_guardian.conf"
	);

	if ( -e "\/tmp\/$farm_name\_pound.socket" )
	{
		unlink ( "\/tmp\/$farm_name\_pound.socket" );
	}

	foreach my $farm_filename ( @farm_configfiles )
	{
		if ( -e "$farm_filename" )
		{
			use Tie::File;
			tie my @configfile, 'Tie::File', "$farm_filename";

			# Lines to change: 
			#Name		BasekitHTTP
			#Control 	"/tmp/BasekitHTTP_pound.socket"
			#\tErr414 "/usr/local/zenloadbalancer/config/BasekitHTTP_Err414.html"
			#\tErr500 "/usr/local/zenloadbalancer/config/BasekitHTTP_Err500.html"
			#\tErr501 "/usr/local/zenloadbalancer/config/BasekitHTTP_Err501.html"
			#\tErr503 "/usr/local/zenloadbalancer/config/BasekitHTTP_Err503.html"
			#\t#Service "BasekitHTTP"
			grep (s/Name\t\t$farm_name/Name\t\t$new_farm_name/, @configfile );
			grep (s/Control \t"\/tmp\/${farm_name}_pound.socket"/Control \t"\/tmp\/${new_farm_name}_pound.socket"/, @configfile );
			grep (s/\tErr414 "\/usr\/local\/zenloadbalancer\/config\/${farm_name}_Err414.html"/\tErr414 "\/usr\/local\/zenloadbalancer\/config\/${new_farm_name}_Err414.html"/, @configfile );
			grep (s/\tErr500 "\/usr\/local\/zenloadbalancer\/config\/${farm_name}_Err500.html"/\tErr500 "\/usr\/local\/zenloadbalancer\/config\/${new_farm_name}_Err500.html"/, @configfile );
			grep (s/\tErr501 "\/usr\/local\/zenloadbalancer\/config\/${farm_name}_Err501.html"/\tErr501 "\/usr\/local\/zenloadbalancer\/config\/${new_farm_name}_Err501.html"/, @configfile );
			grep (s/\tErr503 "\/usr\/local\/zenloadbalancer\/config\/${farm_name}_Err503.html"/\tErr503 "\/usr\/local\/zenloadbalancer\/config\/${new_farm_name}_Err503.html"/, @configfile );
			grep (s/\t#Service "$farm_name"/\t#Service "$new_farm_name"/, @configfile );

			untie @configfile;

			rename ( "$farm_filename", "$new_farm_configfiles[0]" ) or $output = -1;

			&zenlog( "configuration saved in $new_farm_configfiles[0] file" );
		}
		shift ( @new_farm_configfiles );
	}

	return $output;
}


=begin nd
Function: setFarmCipherList

	Set Farm Ciphers value
	
Parameters:
	farmname - Farm name
	ciphers - The options are: cipherglobal, cipherpci or ciphercustom
	cipherc - Cipher custom, this field is used when ciphers is ciphercustom

Returns:
	Integer - return 0 on success or -1 on failure
		
=cut
sub setFarmCipherList    # ($farm_name,$ciphers,$cipherc)
{
	# assign first/second/third argument or take global value
	my $farm_name = shift;
	my $ciphers   = shift;
	my $cipherc   = shift;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	tie my @array, 'Tie::File', "$configdir/$farm_filename";
	for my $line ( @array )
	{
		# takes the first Ciphers line only
		next if ( $line !~ /Ciphers/ );

		if ( $ciphers eq "cipherglobal" )
		{
			$line =~ s/#//g;
			$line   = "\tCiphers \"ALL\"";
			$output = 0;
		}
		elsif ( $ciphers eq "cipherpci" )
		{
			my $cipher_pci = &getGlobalConfiguration('cipher_pci');
			$line =~ s/#//g;
			$line   = "\tCiphers \"$cipher_pci\"";
			$output = 0;
		}
		elsif ( $ciphers eq "ciphercustom" )
		{
			$cipherc = 'DEFAULT' if not defined $cipherc;
			$line =~ s/#//g;
			$line   = "\tCiphers \"$cipherc\"";
			$output = 0;
		}

		# default cipher
		else
		{
			$line =~ s/#//g;
			$line   = "\tCiphers \"ALL\"";
			$output = 0;
		}

		last;
	}
	untie @array;

	return $output;
}


=begin nd
Function: getFarmCipherList

	Get Cipher value defined in pound configuration file 
	
Parameters:
	farmname - Farm name

Returns:
	scalar - return a string with cipher value or -1 on failure 
		
=cut
sub getFarmCipherList    # ($farm_name)
{
	my $farm_name = shift;
	my $output = -1;

	my $farm_filename = &getFarmFile( $farm_name );

	open FI, "<$configdir/$farm_filename";
	my @content = <FI>;
	close FI;

	foreach my $line ( @content )
	{
		next if ( $line !~ /Ciphers/ );

		$output = ( split ( '\"', $line ) )[1];

		last;
	}

	return $output;
}


=begin nd
Function: getFarmCipherSet

	Get Ciphers value defined in pound configuration file. Possible values are: cipherglobal, cipherpci or ciphercustom.
	
Parameters:
	farmname - Farm name

Returns:
	scalar - return a string with cipher set (ciphers) or -1 on failure 
		
=cut
sub getFarmCipherSet    # ($farm_name)
{
	my $farm_name = shift;

	my $output = -1;

	my $cipher_list = &getFarmCipherList( $farm_name );

	if ( $cipher_list eq 'ALL' )
	{
		$output = "cipherglobal";
	}
	elsif ( $cipher_list eq &getGlobalConfiguration('cipher_pci') )
	{
		$output = "cipherpci";
	}
	else
	{
		$output = "ciphercustom";
	}

	return $output;
}


=begin nd
Function: getHTTPFarmConfigIsOK

	Function that check if the config file is OK.
	
Parameters:
	farmname - Farm name

Returns:
	scalar - return 0 on success or different on failure
		
=cut
sub getHTTPFarmConfigIsOK    # ($farm_name)
{
	my $farm_name = shift;

	my $pound = &getGlobalConfiguration( 'pound' );
	my $farm_filename = &getFarmFile( $farm_name );
	my $pound_command = "$pound -f $configdir\/$farm_filename -c";
	my $output        = -1;

	#&validateHTTPFarmDH( $farm_name );

	&zenlog( "running: $pound_command" );

	my $run = `$pound_command 2>&1`;
	$output = $?;

	&zenlog( "output: $run " );

	return $output;
}


=begin nd
Function: getHTTPFarmBackendMaintenance

	Function that check if a backend on a farm is on maintenance mode
	
Parameters:
	farmname - Farm name
	backend - Backend id
	service - Service name

Returns:
	scalar - if backend is in maintenance mode, return 0 else return -1
		
=cut
sub getHTTPFarmBackendMaintenance    # ($farm_name,$backend,$service)
{
	my ( $farm_name, $backend, $service ) = @_;

	my $output = -1;
	
	# if the farm is running, take status from poundctl
	if ( &getFarmStatus ($farm_name) eq 'up' )
	{
		my $poundctl = &getGlobalConfiguration('poundctl');
		my @run    = `$poundctl -c "/tmp/$farm_name\_pound.socket"`;
		
		my $sw     = 0;
	
		foreach my $line ( @run )
		{
			if ( $line =~ /Service \"$service\"/ )
			{
				$sw = 1;
			}
	
			if ( $line =~ /$backend\. Backend/ && $sw == 1 )
			{
				my @line = split ( "\ ", $line );
				my $backendstatus = $line[3];
	
				if ( $backendstatus eq "DISABLED" )
				{
					$backendstatus =
					&getHTTPBackendStatusFromFile( $farm_name, $backend, $service );
	
					if ( $backendstatus =~ /maintenance/ )
					{
						$output = 0;
					}
				}
				last;
			}
		}
	}
	# if the farm is not running, take status from status file
	else
	{
		my $statusfile = "$configdir\/$farm_name\_status.cfg";

		if ( -e $statusfile )
		{
			use Tie::File;
			tie my @filelines, 'Tie::File', "$statusfile";
			
			my @sol;
			my $service_index = &getFarmVSI( $farm_name, $service );
			if ( @sol = grep ( /0 $service_index $backend maintenance/, @filelines ) )
			{
				$output = 0;
			}
			untie @filelines;
		}
	}

	return $output;
}


=begin nd
Function: setHTTPFarmBackendMaintenance

	Function that enable the maintenance mode for backend
	
Parameters:
	farmname - Farm name
	backend - Backend id
	service - Service name

Returns:
	Integer - return 0 on success or -1 on failure
		
=cut
sub setHTTPFarmBackendMaintenance    # ($farm_name,$backend,$service)
{
	my ( $farm_name, $backend, $service ) = @_;

	my $output = -1;

	#find the service number
	my $idsv = &getFarmVSI( $farm_name, $service );

	&zenlog(
		  "setting Maintenance mode for $farm_name service $service backend $backend" );

	if ( &getFarmStatus( $farm_name ) eq 'up' )
	{
		my $poundctl = &getGlobalConfiguration('poundctl');
		my $poundctl_command =
		"$poundctl -c /tmp/$farm_name\_pound.socket -b 0 $idsv $backend";
	
		&zenlog( "running '$poundctl_command'" );
		my @run = `$poundctl_command`;
		$output = $?;
	}

	&getFarmHttpBackendStatus( $farm_name, $backend, "maintenance", $idsv );

	return $output;
}


=begin nd
Function: setHTTPFarmBackendMaintenance

	Function that disable the maintenance mode for backend
	
Parameters:
	farmname - Farm name
	backend - Backend id
	service - Service name

Returns:
	Integer - return 0 on success or -1 on failure
		
=cut
sub setHTTPFarmBackendNoMaintenance    # ($farm_name,$backend,$service)
{
	my ( $farm_name, $backend, $service ) = @_;

	my $output = -1;

	#find the service number
	my $idsv = &getFarmVSI( $farm_name, $service );

	&zenlog(
		"setting Disabled maintenance mode for $farm_name service $service backend $backend"
	);

	if ( &getFarmStatus( $farm_name ) eq 'up' ) 
	{
		my $poundctl = &getGlobalConfiguration('poundctl');
		my $poundctl_command =
			"$poundctl -c /tmp/$farm_name\_pound.socket -B 0 $idsv $backend";

		&zenlog( "running '$poundctl_command'" );
		my @run    = `$poundctl_command`;
		$output = $?;
	}
	
	# save backend status in status file
	&getFarmHttpBackendStatus( $farm_name, $backend, "active", $idsv );

	return $output;
}


=begin nd
Function: getFarmHttpBackendStatus

	Function that save in a file the backend status (maintenance or not)
	
Parameters:
	farmname - Farm name
	backend - Backend id
	status - backend status to save in the status file
	service_id - Service id

Returns:
	none - .
		
FIXME:
	Rename the function, something like saveFarmHTTPBackendstatus, not is "get", this function makes changes in the system
	Not return nothing, do error control
		
=cut
sub getFarmHttpBackendStatus    # ($farm_name,$backend,$status,$idsv)
{
	my ( $farm_name, $backend, $status, $idsv ) = @_;

	my $statusfile = "$configdir\/$farm_name\_status.cfg"; 
	my $changed    = "false";

	if ( !-e $statusfile )
	{
		open FW, ">$statusfile";
		my $poundctl = &getGlobalConfiguration('poundctl');
		my @run = `$poundctl -c /tmp/$farm_name\_pound.socket`;
		my @sw;
		my @bw;

		foreach my $line ( @run )
		{
			if ( $line =~ /\.\ Service\ / )
			{
				@sw = split ( "\ ", $line );
				$sw[0] =~ s/\.//g;
				chomp $sw[0];
			}
			if ( $line =~ /\.\ Backend\ / )
			{
				@bw = split ( "\ ", $line );
				$bw[0] =~ s/\.//g;
				chomp $bw[0];
				if ( $bw[3] eq "active" )
				{
					#~ print FW "-B 0 $sw[0] $bw[0] active\n";
				}
				else
				{
					print FW "-b 0 $sw[0] $bw[0] fgDOWN\n";
				}
			}
		}
		close FW;
	}
	use Tie::File;
	tie my @filelines, 'Tie::File', "$statusfile";

	my $i;
	foreach my $linea ( @filelines )
	{
		if ( $linea =~ /\ 0\ $idsv\ $backend/ )
		{
			if ( $status =~ /maintenance/ || $status =~ /fgDOWN/ )
			{
				$linea   = "-b 0 $idsv $backend $status";
				$changed = "true";
			}
			else
			{
				splice @filelines, $i, 1,;
				$changed = "true";
			}
		}
		$i++;
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
			splice @filelines, $i, 1,;
		}
		close FW;
	}

}


=begin nd
Function: runRemoveHTTPBackendStatus

	Function that removes a backend from the status file
	
Parameters:
	farmname - Farm name
	backend - Backend id
	service - Service name

Returns:
	none - .
		
FIXME:
	This function returns nothing, do error control
		
=cut
sub runRemoveHTTPBackendStatus    # ($farm_name,$backend,$service)
{
	#~ my ( $farm_name, $backend, $service ) = @_;

	#~ my $i      = -1;
	#~ my $j      = -1;
	#~ my $change = "false";
	#~ my $sindex = &getFarmVSI( $farm_name, $service );
	#~ tie my @contents, 'Tie::File', "$configdir\/$farm_name\_status.cfg";
	#~ foreach my $line ( @contents )
	#~ {
		#~ $i++;
		#~ if ( $line =~ /0\ ${sindex}\ ${backend}/ )
		#~ {
			#~ splice @contents, $i, 1,;
		#~ }
	#~ }
	#~ untie @contents;
	#~ my $index = -1;
	#~ tie my @filelines, 'Tie::File', "$configdir\/$farm_name\_status.cfg";
	#~ for ( @filelines )
	#~ {
		#~ $index++;
		#~ if ( $_ !~ /0\ ${sindex}\ $index/ )
		#~ {
			#~ my $jndex = $index + 1;
			#~ $_ =~ s/0\ ${sindex}\ $jndex/0\ ${sindex}\ $index/g;
		#~ }
	#~ }
	#~ untie @filelines;

	my ( $farm_name, $backend, $service ) = @_;

	my $i      = -1;
	my $serv_index = &getFarmVSI( $farm_name, $service );
	tie my @contents, 'Tie::File', "$configdir\/$farm_name\_status.cfg";
	foreach my $line ( @contents )
	{
		$i++;
		if ( $line =~ /0\ ${serv_index}\ ${backend}/ )
		{
			splice @contents, $i, 1,;
			last;
		}
	}
	untie @contents;
	
	tie my @filelines, 'Tie::File', "$configdir\/$farm_name\_status.cfg";
	# decrease backend index in greater backend ids
	foreach my $line ( @filelines )
	{
		if ( $line =~ /0\ ${serv_index}\ (\d+) (\w+)/ )
		{
			my $backend_index = $1 ;
			my $status = $2;
			if ( $backend_index > $backend )
			{
				$backend_index = $backend_index -1;
				$line = "-b 0 $serv_index $backend_index $status";
			}
		}
	}
	untie @filelines;
		
}


=begin nd
Function: setFarmHttpBackendStatus

	For a HTTP farm, it gets each backend status from status file and set it in pound daemon
	
Parameters:
	farmname - Farm name

Returns:
	none - .
		
FIXME:
	This function returns nothing, do error control
		
=cut
sub setFarmHttpBackendStatus    # ($farm_name)
{
	my $farm_name = shift;

	&zenlog( "Setting backends status in farm $farm_name" );

	my $be_status_filename = "$configdir\/$farm_name\_status.cfg";

	unless ( -f $be_status_filename )
	{
		open my $fh, ">", $be_status_filename;
		close $fh;
	}

	open my $fh, "<", $be_status_filename;

	unless ( $fh )
	{
		my $msg = "Error opening $be_status_filename: $!. Aborting execution.";

		&zenlog( $msg );
		die $msg;
	}

	my $poundctl = &getGlobalConfiguration('poundctl');
	
	while ( my $line_aux = <$fh> )
	{
		my @line = split ( "\ ", $line_aux );
		my @run =
		  `$poundctl -c /tmp/$farm_name\_pound.socket $line[0] $line[1] $line[2] $line[3]`;
	}
	close $fh;
}


=begin nd
Function: setFarmHTTPNewService

	Create a new Service in a HTTP farm
	
Parameters:
	farmname - Farm name
	service - Service name

Returns:
	Integer - Error code: 0 on success, other value on failure
		
FIXME:
	This function returns nothing, do error control
		
=cut
sub setFarmHTTPNewService    # ($farm_name,$service)
{
	my ( $farm_name, $service ) = @_;
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
	if ( !fgrep { /Service "$service"/ } "$configdir/$farm_name\_pound.cfg" )
	{
		#create service
		my @newservice;
		my $sw    = 0;
		my $count = 0;
		my $poundtpl = &getGlobalConfiguration('poundtpl');
		tie my @poundtpl, 'Tie::File', "$poundtpl";
		my $countend = 0;
		foreach my $line ( @poundtpl )
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

		$newservice[0] =~ s/#//g;
		$newservice[$#newservice] =~ s/#//g;

		my @fileconf;
		tie @fileconf, 'Tie::File', "$configdir/$farm_name\_pound.cfg";
		my $i         = 0;
		my $farm_type = "";
		$farm_type = &getFarmType( $farm_name );
		foreach my $line ( @fileconf )
		{
			if ( $line =~ /#ZWACL-END/ )
			{
				foreach my $lline ( @newservice )
				{
					if ( $lline =~ /\[DESC\]/ )
					{
						$lline =~ s/\[DESC\]/$service/;
					}
					if (    $lline =~ /StrictTransportSecurity/
						 && $farm_type eq "https" )
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


=begin nd
Function: setFarmNewService

	[Not used] Create a new Service in a HTTP farm
	
Parameters:
	farmname - Farm name
	service - Service name

Returns:
	Integer - Error code: 0 on success, other value on failure
		
FIXME:
	Exist another function, setFarmHttpBackendStatus, with same function.
		
=cut
sub setFarmNewService    # ($farm_name,$service)
{
	my ( $farm_name, $service ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &setFarmHTTPNewService( $farm_name, $service );
	}

	return $output;
}


=begin nd
Function: deleteFarmService

	Delete a service in a Farm
	
Parameters:
	farmname - Farm name
	service - Service name

Returns:
	Integer - Error code: 0 on success, -1 on failure
		
FIXME:
	Rename function to delHTTPFarmService
		
=cut
sub deleteFarmService    # ($farm_name,$service)
{
	my ( $farm_name, $service ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $sw            = 0;
	my $output        = -1;

	# Counter the Service's backends
	my $sindex = &getFarmVSI( $farm_name, $service );
	my $backendsvs = &getFarmVS( $farm_name, $service, "backends" );
	my @be = split ( "\n", $backendsvs );
	my $counter = -1;
	foreach my $subline ( @be )
	{
		my @subbe = split ( "\ ", $subline );
		$counter++;
	}

	use Tie::File;
	tie my @fileconf, 'Tie::File', "$configdir/$farm_filename";

	# Stop FG service
	&runFarmGuardianStop( $farm_name, $service );
	&runFarmGuardianRemove( $farm_name, $service );
	unlink "$configdir/$farm_name\_$service\_guardian.conf";

	my $i = 0;
	for ( $i = 0 ; $i < $#fileconf ; $i++ )
	{
		my $line = $fileconf[$i];
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

	# delete service's backends  in status file
	if ( $counter > -1 )
	{
		while ( $counter > -1 )
		{
			&runRemoveHTTPBackendStatus( $farm_name, $counter, $service );
			$counter--;
		}
	}

	# change the ID value of services with an ID higher than the service deleted (value - 1)
	tie my @contents, 'Tie::File', "$configdir\/$farm_name\_status.cfg";
	foreach my $line ( @contents )
	{
		my @params = split ( "\ ", $line );
		my $newval = $params[2] - 1;

		if ( $params[2] > $sindex )
		{
			$line =~
			  s/$params[0]\ $params[1]\ $params[2]\ $params[3]\ $params[4]/$params[0]\ $params[1]\ $newval\ $params[3]\ $params[4]/g;
		}
	}
	untie @contents;

	return $output;
}


=begin nd
Function: getHTTPFarmVS

	Return virtual server parameter
	
Parameters:
	farmname - Farm name
	service - Service name
	tag - Indicate which field will be returned. The options are: vs, urlp, redirect, redirecttype, cookieins, cookieins-name, cookieins-domain,
	cookieins-path, cookieins-ttlc, dynscale, sesstype, ttl, sessionid, httpsbackend or backends

Returns:
	scalar - if service and tag is blank, return all services in a string: "service0 service1 ..." else return the parameter value

FIXME:
	return a hash with all parameters
				
=cut
sub getHTTPFarmVS    # ($farm_name,$service,$tag)
{
	my ( $farm_name, $service, $tag ) = @_;

	$service = "" unless $service;
	$tag = "" unless $tag;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = "";
	my $l;

	open my $fileconf, '<', "$configdir/$farm_filename";

	my $sw         = 0;
	my $be_section = 0;
	my $be         = -1;
	my $sw_ti      = 0;
	my $output_ti  = "";
	my $sw_pr      = 0;
	my $output_pr  = "";
	my $outputa;
	my $outputp;
	my @return;

	foreach my $line ( <$fileconf> )
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
				$return[1] =~ s/\"//g;
				$return[1] =~ s/^\s+//;
				$return[1] =~ s/\s+$//;
				$output = "$output $return[1]";
			}
		}

		#vs tag
		if ( $tag eq "vs" )
		{
			if ( $line =~ "HeadRequire" && $sw == 1 && $line !~ "#" )
			{
				@return = split ( "Host:", $line );
				$return[1] =~ s/\"//g;
				$return[1] =~ s/^\s+//;
				$return[1] =~ s/\s+$//;
				$output = $return[1];
				last;

			}
		}

		#url pattern
		if ( $tag eq "urlp" )
		{
			if ( $line =~ "Url \"" && $sw == 1 && $line !~ "#" )
			{
				@return = split ( "Url", $line );
				$return[1] =~ s/\"//g;
				$return[1] =~ s/^\s+//;
				$return[1] =~ s/\s+$//;
				$output = $return[1];
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
				$return[1] =~ s/\"//g;
				$return[1] =~ s/^\s+//;
				$return[1] =~ s/\s+$//;
				$output = $return[1];
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
				$output = $values[1];
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
				$output = $values[2];
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
				$output = $values[3];
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
				$output = $values[4];
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
				$return[1] =~ s/\"//g;
				$return[1] =~ s/^\s+//;
				$return[1] =~ s/\s+$//;
				$output = $return[1];
				last;
			}
		}

		#ttl
		if ( $tag eq "ttl" )
		{
			if ( $line =~ "TTL" && $sw == 1 && $line !~ "#" )
			{
				@return = split ( "\ ", $line );
				$return[1] =~ s/\"//g;
				$return[1] =~ s/^\s+//;
				$return[1] =~ s/\s+$//;
				$output = $return[1];
				last;
			}
		}

		#session id
		if ( $tag eq "sessionid" )
		{
			if ( $line =~ "\t\t\tID" && $sw == 1 && $line !~ "#" )
			{
				@return = split ( "\ ", $line );
				$return[1] =~ s/\"//g;
				$return[1] =~ s/^\s+//;
				$return[1] =~ s/\s+$//;
				$output = $return[1];
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
	close $fileconf;

	return $output;
}


=begin nd
Function: setHTTPFarmVS

	Set values for service parameters. The parameters are: vs, urlp, redirect, redirectappend, cookieins, cookieins-name, cookieins-domain,
	cookieins-path, cookieins-ttlc, dynscale, sesstype, ttl, sessionid, httpsbackend or backends
	
	A blank string comment the tag field in config file
	
Parameters:
	farmname - Farm name
	service - Service name
	tag - Indicate which parameter modify
	string - value for the field "tag"

Returns:
	Integer - Error code: 0 on success or -1 on failure
		
=cut
sub setHTTPFarmVS    # ($farm_name,$service,$tag,$string)
{
	my ( $farm_name, $service, $tag, $string ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = "";
	my $line;
	my $sw = 0;
	my $j  = 0;
	my $l;

	use Tie::File;
	tie my @fileconf, 'Tie::File', "$configdir/$farm_filename";

	foreach $line ( @fileconf )
	{
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
			if ( $line =~ "Url" && $sw == 1 && $string eq "" )
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
				$values[1] =~ s/\"//g;
				$line = "\t\tBackendCookie \"$string\" $values[2] $values[3] $values[4]";
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
				$values[2] =~ s/\"//g;
				$line = "\t\tBackendCookie $values[1] \"$string\" $values[3] $values[4]";
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
				$values[3] =~ s/\"//g;
				$line = "\t\tBackendCookie $values[1] $values[2] \"$string\" $values[4]";
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
				$values[4] =~ s/\"//g;
				$line = "\t\tBackendCookie $values[1] $values[2] $values[3] $string";
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
				if ( $fileconf[$j + 1] =~ /Address\ .*/ )
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
			if ( $string ne "nothing" && $sw == 1 )
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
					$line = "\t\t\tType $string";
				}
				if ( $line =~ "TTL" )
				{
					$line =~ s/#//g;
				}
				if (    $string eq "URL"
					 || $string eq "COOKIE"
					 || $string eq "HEADER" )
				{
					if ( $line =~ "\t\t\tID |\t\t\t#ID " )
					{
						$line =~ s/#//g;
					}
				}
				if ( $string eq "IP" )
				{
					if ( $line =~ "\t\t\tID |\t\t\t#ID " )
					{
						$line = "\#$line";
					}
				}
				$output = $?;
			}
			if ( $string eq "nothing" && $sw == 1 )
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
		$j++;
	}
	untie @fileconf;

	return $output;
}


=begin nd
Function: getFarmVSI

	Get the index of a service in a http farm
	
Parameters:
	farmname - Farm name
	service - Service name

Returns:
	integer - Service index 
	
FIXME: 
	Initialize output to -1 and do error control
	Rename with intuitive name, something like getHTTPFarmServiceIndex
		
=cut
sub getFarmVSI    # ($farm_name,$service)
{
	my ( $farmname, $service ) = @_;
	
	# get service position
	my $srv_position = 0;
	my @services = &getFarmServices( $farmname );
	foreach my $srv ( @services )
	{
		if  ( $srv eq $service )
		{
			# found
			last;
		}
		else
		{
			$srv_position++;
		}
	}
	
	return $srv_position;	
}

 
=begin nd
Function: getFarmServices

	Get an array containing service name that are configured in a http farm
	
Parameters:
	farmname - Farm name

Returns:
	Array - service names
	
FIXME: 
	rename to getHTTPFarmServices
	&getHTTPFarmVS(farmname) does same but in a string
		
=cut
sub getFarmServices
{
	my ( $farm_name ) = @_;
	my @output;
	my $farm_filename = &getFarmFile( $farm_name );

	open FR, "<$configdir\/$farm_filename";
	my @file = <FR>;
	my $pos  = 0;

	foreach my $line ( @file )
	{
		if ( $line =~ /\tService\ \"/ )
		{
			$pos++;
			my @line_aux = split ( "\"", $line );
			my $service = $line_aux[1];
			push ( @output, $service );
		}
	}

	return @output;
}


=begin nd
Function: setFarmBackendsSessionsRemove

	Remove all the active sessions enabled to a backend in a given service
	Used by farmguardian
	
Parameters:
	farmname - Farm name
	service - Service name
	backend - Backend id

Returns:
	none - .
	
FIXME: 
		
=cut
sub setFarmBackendsSessionsRemove    #($farm_name,$service,$backendid)
{
	my ( $farm_name, $service, $backendid ) = @_;

	my @content = &getFarmBackendStatusCtl( $farm_name );
	my @sessions = &getFarmBackendsClientsList( $farm_name, @content );
	my @service;
	my $sw = 0;
	my $serviceid;
	my @sessionid;
	my $sessid;
	my $sessionid2;
	my $poundctl = &getGlobalConfiguration('poundctl');
	my @output;

	&zenlog(
		"Deleting established sessions to a backend $backendid from farm $farm_name in service $service"
	);

	foreach ( @content )
	{
		if ( $_ =~ /Service/ && $sw eq 1 )
		{
			$sw = 0;
		}

		if ( $_ =~ /Service\ \"$service\"/ && $sw eq 0 )
		{
			$sw        = 1;
			@service   = split ( /\./, $_ );
			$serviceid = $service[0];
		}

		if ( $_ =~ /Session.*->\ $backendid/ && $sw eq 1 )
		{
			@sessionid  = split ( /Session/, $_ );
			$sessionid2 = $sessionid[1];
			@sessionid  = split ( /\ /, $sessionid2 );
			$sessid     = $sessionid[1];
			@output = `$poundctl -c  /tmp/$farm_name\_pound.socket -n 0 $serviceid $sessid`;
			&zenlog(
				"Executing:  $poundctl -c /tmp/$farm_name\_pound.socket -n 0 $serviceid $sessid"
			);
		}
	}
}


=begin nd
Function: setFarmNameParam

	[NOT USED] Rename a HTTP farm
	
Parameters:
	farmname - Farm name
	newfarmname - New farm name

Returns:
	none - Error code: 0 on success or -1 on failure
	
BUG: 
	this function is duplicated
		
=cut
sub setFarmNameParam    # &setFarmNameParam( $farm_name, $new_name );
{
	my ( $farmName, $newName ) = @_;

	my $farmType     = &getFarmType( $farmName );
	my $farmFilename = &getFarmFile( $farmName );
	my $output       = -1;

	&zenlog( "setting 'farm name $newName' for $farmName farm $farmType" );

	if ( $farmType eq "http" || $farmType eq "https" )
	{
		tie my @filefarmhttp, 'Tie::File', "$configdir/$farmFilename";
		my $i_f        = -1;
		my $arrayCount = @filefarmhttp;
		my $found      = "false";
		while ( $i_f <= $arrayCount && $found eq "false" )
		{
			$i_f++;
			if ( $filefarmhttp[$i_f] =~ /^Name.*/ )
			{
				$filefarmhttp[$i_f] = "Name\t\t$newName";
				$output             = $?;
				$found              = "true";
			}
		}
		untie @filefarmhttp;
	}

	return $output;
}


=begin nd
Function: moveService

	Move a HTTP service to change its preference. This function changes the possition of a service in farm config file
	
Parameters:
	farmname - Farm name
	move - Direction where it moves the service. The possbile value are: "down", decrease the priority or "up", increase the priority
	service - Service to move

Returns:
	integer - Always return 0
	
FIXME: 
	Rename function to setHTTPFarmMoveService
	Always return 0, create error control
		
=cut
sub moveService    # moveService ( $farmName, $move, $serviceSelect);
{
	# Params
	my $farmName      = shift;
	my $move          = shift;
	my $serviceSelect = shift;

	my $farm_filename = &getFarmFile( $farmName );
	$farm_filename = "$configdir\/$farm_filename";

	my @file;
	my @services = &getFarmServices( $farmName );
	my @serviceIndex;
	my $selectServiceInd;
	my $size = scalar @services;
	my @aux;
	my $lastService;

	# loop
	my $ind        = 0;
	my $serviceNum = 0;
	my $flag       = 0;
	my @definition;    # Service definition

	if (    ( ( $move eq 'up' ) && ( $services[0] ne $serviceSelect ) )
		 || ( ( $move eq 'down' ) && ( $services[$size - 1] ne $serviceSelect ) ) )
	{
		#~ system ( "cp $farm_filename $farm_filename.bak" );
		tie @file, 'Tie::File', $farm_filename;

		# Find service indexs
		foreach my $line ( @file )
		{
			# Select service index
			if ( $line =~ /^\tService \"$serviceSelect\"$/ )
			{
				$flag             = 1;
				$selectServiceInd = $serviceNum;
			}

			# keep service definition and delete it from configuration file
			if ( $flag == 1 )
			{
				push @definition, $line;

				# end service definition
				if ( $line =~ /^\tEnd$/ )
				{
					$flag = 0;
					$ind -= 1;
				}
			}
			else
			{
				push @aux, $line;
			}

			# add a new index to the index table
			if ( $line =~ /^\tService \"$services[$serviceNum]\"$/ )
			{
				push @serviceIndex, $ind;
				$serviceNum += 1;
			}

			# index of last service
			if ( $line =~ /^\tEnd$/ )
			{
				$lastService = $ind + 1;
			}

			if ( !$flag )
			{
				$ind += 1;
			}

		}
		@file = @aux;

		# move up service
		if ( $move eq 'up' )
		{
			splice ( @file, $serviceIndex[$selectServiceInd - 1], 0, @definition );
		}

		# move down service
		elsif ( $move eq 'down' )
		{
			if ( $selectServiceInd == ( $size - 2 ) )
			{
				unshift @definition, "\n";
				splice ( @file, $lastService + 1, 0, @definition );
			}
			else
			{
				splice ( @file, $serviceIndex[$selectServiceInd + 2], 0, @definition );
			}
		}
		untie @file;
	}

	return 0;
}


=begin nd
Function: moveServiceFarmStatus

	Modify the service index in status file ( farmname_status.cfg ). For updating farmguardian backend status.
	
Parameters:
	farmname - Farm name
	move - Direction where it moves the service. The possbile value are: "down", decrease the priority or "up", increase the priority
	service - Service to move

Returns:
	integer - Always return 0
	
FIXME: 
	Rename function to setHTTPFarmMoveServiceStatusFile
	Always return 0, create error control
		
=cut
sub moveServiceFarmStatus
{
	my ( $farmName, $moveService, $serviceSelect ) = @_;
	my @file;

	my $fileName = "$configdir\/${farmName}_status.cfg";

	my @services = &getFarmServices( $farmName );
	my $size     = scalar @services;
	my $ind      = -1;
	my $auxInd;
	my $serviceNum;

	# Find service select index
	foreach my $se ( @services )
	{
		$ind += 1;
		last if ( $services[$ind] eq $serviceSelect );
	}

	#~ system ( "cp $fileName $fileName.bak" );

	tie @file, 'Tie::File', $fileName;

	# change server id
	foreach my $line ( @file )
	{
		$line =~ /(^-[bB] 0 )(\d+)/;
		my $cad        = $1;
		$serviceNum = $2;

		#	&main::zenlog("$moveService::$ind::$serviceNum");
		if ( ( $moveService eq 'up' ) && ( $serviceNum == $ind ) )
		{
			$auxInd = $serviceNum - 1;
			$line =~ s/^-[bB] 0 (\d+)/${cad}$auxInd/;
		}

		if ( ( $moveService eq 'up' ) && ( $serviceNum == $ind - 1 ) )
		{
			$auxInd = $serviceNum + 1;
			$line =~ s/^-[bB] 0 (\d+)/${cad}$auxInd/;
		}

		if ( ( $moveService eq 'down' ) && ( $serviceNum == $ind ) )
		{
			$auxInd = $serviceNum + 1;
			$line =~ s/^-[bB] 0 (\d+)/${cad}$auxInd/;
		}

		if ( ( $moveService eq 'down' ) && ( $serviceNum == $ind + 1 ) )
		{
			$auxInd = $serviceNum - 1;
			$line =~ s/^-[bB] 0 (\d+)/${cad}$auxInd/;
		}
	}

	untie @file;

	&zenlog(
		"The service \"$serviceSelect\" from farm \"$farmName\" has been moved $moveService"
	);

	return 0;
}


=begin nd
Function: getHttpFarmService

	Get a struct with all parameters of a service and theirs values
	
	@{ $out_ba }, $backend_ref
			  
	$backend_ref = {
				  id            => $id,
				  backendstatus => $backendstatus,
				  ip            => $ip,
				  port          => $port,
				  timeout       => $tout,
				  weight        => $prio
	}

	$service_ref = {
					 id           => $service,
					 vhost        => $vser,
					 urlp         => $urlp,
					 redirect     => $redirect,
					 redirecttype => $redirecttype,
					 cookieinsert => $cookiei,
					 cookiename   => $cookieinsname,
					 cookiedomain => $domainname,
					 cookiepath   => $path,
					 cookiettl    => $ttlc + 0,
					 persistence  => $session,
					 ttl          => $ttl + 0,
					 sessionid    => $sesid,
					 leastresp    => $dyns,
					 httpsb       => $httpsbe,
					 fgtimecheck  => $fgttcheck + 0,
					 fgscript     => $fgscript,
					 fgenabled    => $fguse,
					 fglog        => $fglog,
					 backends     => $out_ba
	};
	
Parameters:
	farmname - Farm name
	service - Service to move

Returns:
	hash ref - $service_ref
			
=cut
sub getHttpFarmService
{
	my $farmname    = shift;    # input
	my $service     = shift;    # input
	my $service_ref = {};       # output

	my $vser         = &getFarmVS( $farmname, $service, "vs" );
	my $urlp         = &getFarmVS( $farmname, $service, "urlp" );
	my $redirect     = &getFarmVS( $farmname, $service, "redirect" );
	my $redirecttype = &getFarmVS( $farmname, $service, "redirecttype" );
	my $session      = &getFarmVS( $farmname, $service, "sesstype" );
	my $ttl          = &getFarmVS( $farmname, $service, "ttl" );
	my $sesid        = &getFarmVS( $farmname, $service, "sessionid" );
	my $dyns         = &getFarmVS( $farmname, $service, "dynscale" );
	my $httpsbe      = &getFarmVS( $farmname, $service, "httpsbackend" );
	my $cookiei      = &getFarmVS( $farmname, $service, "cookieins" );

	if ( $cookiei eq "" )
	{
		$cookiei = "false";
	}

	my $cookieinsname = &getFarmVS( $farmname, $service, "cookieins-name" );
	my $domainname    = &getFarmVS( $farmname, $service, "cookieins-domain" );
	my $path          = &getFarmVS( $farmname, $service, "cookieins-path" );
	my $ttlc          = &getFarmVS( $farmname, $service, "cookieins-ttlc" );

	if ( $dyns =~ /^$/ )
	{
		$dyns = "false";
	}

	if ( $httpsbe =~ /^$/ )
	{
		$httpsbe = "false";
	}

	my @fgconfig  = &getFarmGuardianConf( $farmname, $service );
	my $fgttcheck = $fgconfig[1];
	my $fgscript  = $fgconfig[2];
	$fgscript =~ s/\n//g;
	$fgscript =~ s/\"/\'/g;

	my $fguse = $fgconfig[3];
	$fguse =~ s/\n//g;

	my $fglog = $fgconfig[4];

	# Default values for farm guardian parameters
	if ( !$fgttcheck ) { $fgttcheck = 5; }
	if ( !$fguse )     { $fguse     = "false"; }
	if ( !$fglog )     { $fglog     = "false"; }
	if ( !$fgscript )  { $fgscript  = ""; }

	my $out_ba     = [];
	my $backendsvs = &getFarmVS( $farmname, $service, "backends" );
	my @be         = split ( "\n", $backendsvs );

	foreach my $subl ( @be )
	{
		my $backendstatus;
		my @subbe       = split ( "\ ", $subl );
		my $id          = $subbe[1] + 0;
		my $maintenance = &getFarmBackendMaintenance( $farmname, $id, $service );

		if ( $maintenance != 0 )
		{
			$backendstatus = "up";
		}
		else
		{
			$backendstatus = "maintenance";
		}

		my $ip   = $subbe[3];
		my $port = $subbe[5] + 0;
		my $tout = $subbe[7] + 0;
		my $prio = $subbe[9] + 0;

		push (
			   @{ $out_ba },
			   {
				  id            => $id,
				  backendstatus => $backendstatus,
				  ip            => $ip,
				  port          => $port,
				  timeout       => $tout,
				  weight        => $prio
			   }
		);
	}

	$service_ref = {
					 id           => $service,
					 vhost        => $vser,
					 urlp         => $urlp,
					 redirect     => $redirect,
					 redirecttype => $redirecttype,
					 cookieinsert => $cookiei,
					 cookiename   => $cookieinsname,
					 cookiedomain => $domainname,
					 cookiepath   => $path,
					 cookiettl    => $ttlc + 0,
					 persistence  => $session,
					 ttl          => $ttl + 0,
					 sessionid    => $sesid,
					 leastresp    => $dyns,
					 httpsb       => $httpsbe,
					 fgtimecheck  => $fgttcheck + 0,
					 fgscript     => $fgscript,
					 fgenabled    => $fguse,
					 fglog        => $fglog,
					 backends     => $out_ba
	};

	return $service_ref;
}


=begin nd
Function: getHTTPServiceStruct

	Get a struct with all parameters of a HTTP service
	
Parameters:
	farmname - Farm name
	service - Farm name

Returns:
	hash ref - hash with service configuration
	
	Example output:
	{
   "services" : {
      "backends" : [
         {
            "id" : 0,
            "ip" : "48.5.25.5",
            "port" : 70,
            "status" : "up",
            "timeout" : null,
            "weight" : null
         }
      ],
      "cookiedomain" : "",
      "cookieinsert" : "false",
      "cookiename" : "",
      "cookiepath" : "",
      "cookiettl" : 0,
      "fgenabled" : "false",
      "fglog" : "false",
      "fgscript" : "",
      "fgtimecheck" : 5,
      "httpsb" : "false",
      "id" : "srv3",
      "leastresp" : "false",
      "persistence" : "",
      "redirect" : "",
      "redirecttype" : "",
      "sessionid" : "",
      "ttl" : 0,
      "urlp" : "",
      "vhost" : ""
   }

=cut
sub getHTTPServiceStruct
{
	my ( $farmname, $servicename ) = @_;
	my $service = -1;
	
	#http services
	my $services = &getFarmVS( $farmname, "", "" );
	my @serv = split ( "\ ", $services );
	
	foreach my $s ( @serv )
	{
		if ( $s eq $servicename )
		{
			my $vser         = &getFarmVS( $farmname, $s, "vs" );
			my $urlp         = &getFarmVS( $farmname, $s, "urlp" );
			my $redirect     = &getFarmVS( $farmname, $s, "redirect" );
			my $redirecttype = &getFarmVS( $farmname, $s, "redirecttype" );
			my $session      = &getFarmVS( $farmname, $s, "sesstype" );
			my $ttl          = &getFarmVS( $farmname, $s, "ttl" );
			my $sesid        = &getFarmVS( $farmname, $s, "sessionid" );
			my $dyns         = &getFarmVS( $farmname, $s, "dynscale" );
			my $httpsbe      = &getFarmVS( $farmname, $s, "httpsbackend" );
			my $cookiei      = &getFarmVS( $farmname, $s, "cookieins" );
	
			if ( $cookiei eq "" )
			{
				$cookiei = "false";
			}
	
			my $cookieinsname = &getFarmVS( $farmname, $s, "cookieins-name" );
			my $domainname    = &getFarmVS( $farmname, $s, "cookieins-domain" );
			my $path          = &getFarmVS( $farmname, $s, "cookieins-path" );
			my $ttlc          = &getFarmVS( $farmname, $s, "cookieins-ttlc" );
	
			if ( $dyns =~ /^$/ )
			{
				$dyns = "false";
			}
			if ( $httpsbe =~ /^$/ )
			{
				$httpsbe = "false";
			}
	
			my @fgconfig  = &getFarmGuardianConf( $farmname, $s );
			my $fgttcheck = $fgconfig[1];
			my $fgscript  = $fgconfig[2];
			my $fguse     = $fgconfig[3];
			my $fglog     = $fgconfig[4];
	
			# Default values for farm guardian parameters
			if ( !$fgttcheck ) { $fgttcheck = 5; }
			if ( !$fguse )     { $fguse     = "false"; }
			if ( !$fglog )     { $fglog     = "false"; }
			if ( !$fgscript )  { $fgscript  = ""; }
	
			$fgscript =~ s/\n//g;
			$fgscript =~ s/\"/\'/g;
			$fguse =~ s/\n//g;
	
			my @out_ba;
			my $backendsvs = &getFarmVS( $farmname, $s, "backends" );
			my @be         = split ( "\n", $backendsvs );
	
			foreach my $subl ( @be )
			{
				my @subbe       = split ( "\ ", $subl );
				my $id          = $subbe[1] + 0;
				my $maintenance = &getFarmBackendMaintenance( $farmname, $id, $s );
	
				my $backendstatus;
				if ( $maintenance != 0 )
				{
					$backendstatus = "up";
				}
				else
				{
					$backendstatus = "maintenance";
				}
	
				my $ip   = $subbe[3];
				my $port = $subbe[5] + 0;
				my $tout = $subbe[7];
				my $prio = $subbe[9];
	
				$tout = $tout eq '-' ? undef: $tout+0;
				$prio = $prio eq '-' ? undef: $prio+0;
	
				push @out_ba,
				{
					id      => $id,
					status  => $backendstatus,
					ip      => $ip,
					port    => $port,
					timeout => $tout,
					weight  => $prio
				};
			}
	
			$ttlc      = 0 unless $ttlc;
			$ttl       = 0 unless $ttl;
			$fgttcheck = 0 unless $fgttcheck;
	
			$service =
			{
				id           => $s,
				vhost        => $vser,
				urlp         => $urlp,
				redirect     => $redirect,
				redirecttype => $redirecttype,
				cookieinsert => $cookiei,
				cookiename   => $cookieinsname,
				cookiedomain => $domainname,
				cookiepath   => $path,
				cookiettl    => $ttlc + 0,
				persistence  => $session,
				ttl          => $ttl + 0,
				sessionid    => $sesid,
				leastresp    => $dyns,
				httpsb       => $httpsbe,
				fgtimecheck  => $fgttcheck + 0,
				fgscript     => $fgscript,
				fgenabled    => $fguse,
				fglog        => $fglog,
				backends     => \@out_ba,
			};
			last;
		}
		
	}

	return $service;
}



1;
