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

	use File::Grep 'fgrep';
	require Tie::File;
	require Zevenet::Farm::Config;

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

	require Tie::File;
	require Zevenet::FarmGuardian;
	require Zevenet::Farm::HTTP::Service;

	my $farm_filename = &getFarmFile( $farm_name );
	my $sw            = 0;
	my $output        = -1;

	# Counter the Service's backends
	my $sindex = &getFarmVSI( $farm_name, $service );
	my $backendsvs = &getHTTPFarmVS( $farm_name, $service, "backends" );
	my @be = split ( "\n", $backendsvs );
	my $counter = -1;

	foreach my $subline ( @be )
	{
		my @subbe = split ( "\ ", $subline );
		$counter++;
	}

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
			require Zevenet::Farm::HTTP::Backend;
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
Function: getHTTPFarmServices

	Get an array containing service name that are configured in a http farm
	
Parameters:
	farmname - Farm name

Returns:
	Array - service names
	
FIXME: 
	&getHTTPFarmVS(farmname) does same but in a string
		
=cut
sub getHTTPFarmServices
{
	my ( $farm_name ) = @_;

	require Zevenet::Farm::Core;

	my $farm_filename = &getFarmFile( $farm_name );
	my $pos  = 0;
	my @output;

	open my $fh, "<$configdir\/$farm_filename";
	my @file = <$fh>;
	close $fh;

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
	my @services = &getHTTPFarmServices( $farmName );
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

	my @services = &getHTTPFarmServices( $farmName );
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
    };

=cut
sub getHTTPServiceStruct
{
	my ( $farmname, $servicename ) = @_;

	require Zevenet::FarmGuardian;
	require Zevenet::Farm::HTTP::Backend;

	my $service = -1;

	#http services
	my $services = &getHTTPFarmVS( $farmname, "", "" );
	my @serv = split ( "\ ", $services );

	foreach my $s ( @serv )
	{
		if ( $s eq $servicename )
		{
			my $vser         = &getHTTPFarmVS( $farmname, $s, "vs" );
			my $urlp         = &getHTTPFarmVS( $farmname, $s, "urlp" );
			my $redirect     = &getHTTPFarmVS( $farmname, $s, "redirect" );
			my $redirecttype = &getHTTPFarmVS( $farmname, $s, "redirecttype" );
			my $session      = &getHTTPFarmVS( $farmname, $s, "sesstype" );
			my $ttl          = &getHTTPFarmVS( $farmname, $s, "ttl" );
			my $sesid        = &getHTTPFarmVS( $farmname, $s, "sessionid" );
			my $dyns         = &getHTTPFarmVS( $farmname, $s, "dynscale" );
			my $httpsbe      = &getHTTPFarmVS( $farmname, $s, "httpsbackend" );
			my $cookiei      = &getHTTPFarmVS( $farmname, $s, "cookieins" );

			if ( $cookiei eq "" )
			{
				$cookiei = "false";
			}

			my $cookieinsname = &getHTTPFarmVS( $farmname, $s, "cookieins-name" );
			my $domainname    = &getHTTPFarmVS( $farmname, $s, "cookieins-domain" );
			my $path          = &getHTTPFarmVS( $farmname, $s, "cookieins-path" );
			my $ttlc          = &getHTTPFarmVS( $farmname, $s, "cookieins-ttlc" );

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

			my $backends = &getHTTPFarmBackends( $farmname, $s);

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
				backends     => $backends,
			};
			last;
		}
	}

	return $service;
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
	my $output        = 0;
	my $line;
	my $sw = 0;
	my $j  = 0;
	my $l;

	require Tie::File;
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
	my @services = &getHTTPFarmServices( $farmname );
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

1;
