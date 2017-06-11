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
Function: getFarmZones

	Get farm zones list for GSLB farms
	
Parameters:
	farmname - Farm name

Returns:
	Array - list of zone names or -1 on failure
	
=cut
sub getFarmZones    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $output    = -1;
	my $farm_type = &getFarmType( $farm_name );

	opendir ( DIR, "$configdir\/$farm_name\_$farm_type.cfg\/etc\/zones\/" );
	my @files = grep { /^[a-zA-Z]/ } readdir ( DIR );
	closedir ( DIR );

	return @files;
}

=begin nd
Function: remFarmZoneResource

	Remove a resource from a gslb zone
	
Parameters:
	resource - Resource id
	farmname - Farm name
	zone - Zone name

Returns:
	Integer - Error code: 0 on success or different of 0 on failure

=cut
sub remFarmZoneResource    # ($id,$farm_name,$service)
{
	my ( $id, $fname, $service ) = @_;

	my $output = 0;
	my $ftype  = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );

	my @fileconf;
	my $line;
	my $index = 0;
	use Tie::File;
	tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/zones/$service";
	foreach $line ( @fileconf )
	{
		if ( $line =~ /\;index_$id/ )
		{
			splice @fileconf, $index, 1;
		}
		$index++;
	}
	untie @fileconf;
	$output = $?;
	&setFarmZoneSerial( $fname, $service );
	$output = $output + $?;

	return $output;
}

=begin nd
Function: runGSLBFarmServerDelete

	Delete a resource from a zone
	
Parameters:
	farmname - Farm name

Returns:
	Integer - Error code: 0 on success or different of 0 on failure
	
BUG:
	This function has a bad name and is used in wrong way
	It is duplicated with "remFarmZoneResource"
	
=cut
sub runGSLBFarmServerDelete    # ($ids,$farm_name,$service)
{
	my ( $ids, $farm_name, $service ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $index         = 0;

	use Tie::File;
	tie my @configfile, 'Tie::File', "$configdir/$farm_filename/etc/zones/$service";

	foreach my $line ( @configfile )
	{
		if ( $line =~ /\;index_/ )
		{
			my @linesplt = split ( "\;index_", $line );
			my $param = $linesplt[1];
			if ( $ids !~ /^$/ && $ids eq $param )
			{
				splice @configfile, $index, 1,;
			}
		}
		$index++;
	}
	untie @configfile;
	$output = $?;

	return $output;
}

=begin nd
Function: setFarmZoneResource

	Modify or create a resource in a zone
	
Parameters:
	id - Resource id. It is the resource to modify, if it is blank, a new resource will be created
	resource - Resource name
	ttl - Time to live
	type - Type of resource. The possible values are: "A", "NS", "AAAA", "CNAME", "MX", "SRV", "TXT", "PTR", "NAPTR" or "DYN" (service)
	rdata - Resource data. Depend on "type" parameter
	farmname - Farm name
	zone - Zone name

Returns:
	Integer - Error code: 0 on success or different of 0 on failure
	
=cut
sub setFarmZoneResource  # ($id,$resource,$ttl,$type,$rdata,$farm_name,$service)
{
	my ( $id, $resource, $ttl, $type, $rdata, $farm_name, $service ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $line;
	my $param;
	my $index = 0;
	my $lb    = "";
	my $flag  = "false";

	if ( $type =~ /DYN./ )
	{
		$lb = &getFarmVS( $farm_name, $rdata, "plugin" );
		$lb = "$lb!";
	}
	use Tie::File;
	tie my @configfile, 'Tie::File', "$configdir/$farm_filename/etc/zones/$service";

	foreach my $line ( @configfile )
	{
		if ( $line =~ /\;index_/ )
		{
			my @linesplt = split ( "\;index_", $line );
			$param = $linesplt[1];

			if ( $id !~ /^$/ && $id eq $param )
			{
				$line = "$resource\t$ttl\t$type\t$lb$rdata ;index_$param";
				$flag = "true";
			}
			else
			{
				$index = $param + 1;
			}
		}
	}
	if ( $id =~ /^$/ )
	{
		push @configfile, "$resource\t$ttl\t$type\t$lb$rdata ;index_$index";
	}
	untie @configfile;
	&setFarmZoneSerial( $farm_name, $service );

	my $output = $?;

	if ( $flag eq "false" )
	{
		$output = -2;
	}

	return $output;
}

=begin nd
Function: setFarmZoneSerial

	Update gslb zone serial, to register that a zone has been modified
	
Parameters:
	farmname - Farm name
	zone - Zone name

Returns:
	Integer - Error code: 0 on success or different of 0 on failure
	
=cut
sub setFarmZoneSerial    # ($farm_name,$zone)
{
	my ( $fname, $zone ) = @_;
	my $ftype  = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	my @fileconf;
	use Tie::File;
	tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/zones/$zone";
	my $index;
	foreach my $line ( @fileconf )
	{
		if ( $line =~ /@\tSOA / )
		{
			my $date = `date +%s`;
			splice @fileconf, $index + 1, 1, "\t$date";
		}
		$index++;
	}
	untie @fileconf;
	$output = $?;

	return $output;
}

=begin nd
Function: setGSLBFarmDeleteZone

	Delete an existing Zone in a GSLB farm
	 
Parameters:
	farmname - Farm name
	zone - Zone name

Returns:
	Integer - Error code: 0 on success or -1 on failure

=cut
sub setGSLBFarmDeleteZone    # ($farm_name,$service)
{
	my ( $farm_name, $service ) = @_;

	my $output = -1;

	use File::Path 'rmtree';
	rmtree( ["$configdir\/$farm_name\_gslb.cfg\/etc\/zones\/$service"] );
	$output = 0;

	return $output;
}

=begin nd
Function: setGSLBFarmNewZone

	Create a new Zone in a GSLB farm
	 
Parameters:
	farmname - Farm name
	zone - Zone name

Returns:
	Integer - Error code: 0 on success, 1 if it already exists or -1 on failure

=cut
sub setGSLBFarmNewZone    # ($farm_name,$service)
{
	my ( $fname, $zone ) = @_;

	my $output = -1;
	my $ftype  = &getFarmType( $fname );
	my $fvip   = &getFarmVip( "vip", $fname );

	opendir ( DIR, "$configdir\/$fname\_$ftype.cfg\/etc\/zones\/" );
	my @files = grep { /^$zone/ } readdir ( DIR );
	closedir ( DIR );

	if ( scalar @files == 0 )
	{
		open ( my $file, ">", "$configdir\/$fname\_$ftype.cfg\/etc\/zones\/$zone" )
		  or warn "cannot open > $configdir\/$fname\_$ftype.cfg\/etc\/zones\/$zone: $!";
		print $file "@	SOA ns1 hostmaster (\n" . "	1\n"
		  . "	7200\n"
		  . "	1800\n"
		  . "	259200\n"
		  . "	900\n" . ")\n\n";
		print $file "@		NS	ns1 ;index_0\n";
		print $file "ns1		A	$fvip ;index_1\n";
		close $file;

		$output = 0;
	}
	else
	{
		$output = 1;
	}

	return $output;
}

=begin nd
Function: getGSLBResources

	Get a array with all resource of a zone in a gslb farm

Parameters:
	farmname - Farm name
	Zone - Zone name

Returns:
	Array ref - Each array element is a hash reference to a hash that has the keys: rname, id, ttl, type and rdata
	i.e.  \@resourcesArray = ( \%resource1,  \%resource2, ...)
	\%resource1 = { rname = $name, id  =$id, ttl = $ttl, type = $type, rdata = $rdata }
	
=cut
sub getGSLBResources	# ( $farmname, $zone )
{
	my ( $farmname, $zone ) = @_;
	my $backendsvs = &getFarmVS( $farmname, $zone, "resources" );
	my @resourcesArray;

	my @be = split ( "\n", $backendsvs );

	my $ind;
	foreach my $subline ( @be )
	{
		$ind++;
		my %resources;

		if ( $subline =~ /^$/ )
		{
			next;
		}

		my @subbe  = split ( " \;", $subline );
		my @subbe1 = split ( "\t",  $subbe[0] );
		my @subbe2 = split ( "_",   $subbe[1] );

		$resources{ rname } = $subbe1[0];
		$resources{ id }    = $subbe2[1] + 0;
		$resources{ ttl }   = $subbe1[1];
		$resources{ type }  = $subbe1[2];
		$resources{ rdata } = $subbe1[3];

		push @resourcesArray, \%resources;
	}

	return \@resourcesArray;
}

1;
