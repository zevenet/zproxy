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

my $configdir = &getGlobalConfiguration( 'configdir' );

=begin nd
Function: getGSLBFarmZones

	Get farm zones list for GSLB farms

Parameters:
	farmname - Farm name

Returns:
	Array - list of zone names or -1 on failure
=cut

sub getGSLBFarmZones    # ($farm_name)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name ) = @_;

	my $output = -1;

	opendir ( DIR, "$configdir\/$farm_name\_gslb.cfg\/etc\/zones\/" );
	my @files = grep { /^[a-zA-Z]/ } readdir ( DIR );
	closedir ( DIR );

	return @files;
}

=begin nd
Function: remGSLBFarmZoneResource

	Remove a resource from a gslb zone

Parameters:
	resource - Resource id
	farmname - Farm name
	zone - Zone name

Returns:
	none - No returned value
=cut

sub remGSLBFarmZoneResource    # ($id,$farm_name,$service)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $id, $fname, $service ) = @_;

	my $ffile = &getFarmFile( $fname );

	my @fileconf;
	my $index = 0;

	require Tie::File;
	tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/zones/$service";

	foreach my $line ( @fileconf )
	{
		if ( $line =~ /\;index_$id/ )
		{
			splice @fileconf, $index, 1;
		}
		$index++;
	}
	untie @fileconf;
	&setGSLBFarmZoneSerial( $fname, $service );
}

=begin nd
Function: setGSLBFarmZoneResource

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

sub setGSLBFarmZoneResource # ($id,$resource,$ttl,$type,$rdata,$farm_name,$service)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $id, $resource, $ttl, $type, $rdata, $farm_name, $service ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $param;
	my $index = 0;
	my $lb    = "";
	my $flag  = "false";

	if ( $type =~ /DYN./ )
	{
		require Zevenet::Farm::Config;

		$lb = &getFarmVS( $farm_name, $rdata, "plugin" );
		$lb = "$lb!";
	}

	require Tie::File;
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
	&setGSLBFarmZoneSerial( $farm_name, $service );

	my $output = 0;

	if ( $flag eq "false" )
	{
		$output = -2;
	}

	return $output;
}

=begin nd
Function: setGSLBFarmZoneSerial

	Update gslb zone serial, to register that a zone has been modified

Parameters:
	farmname - Farm name
	zone - Zone name

Returns:
	none - No returned value.
=cut

sub setGSLBFarmZoneSerial    # ($farm_name,$zone)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname, $zone ) = @_;

	my $ffile = &getFarmFile( $fname );
	my $index = 0;

	require Tie::File;
	tie my @fileconf, 'Tie::File', "$configdir/$ffile/etc/zones/$zone";

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
}

=begin nd
Function: setGSLBFarmDeleteZone

	Delete an existing Zone in a GSLB farm

Parameters:
	farmname - Farm name
	zone - Zone name

Returns:
	Scalar - 1 on success, 0 or false on failure.
=cut

sub setGSLBFarmDeleteZone    # ($farm_name,$zone)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $zone ) = @_;

	return unlink "$configdir\/$farm_name\_gslb.cfg\/etc\/zones\/$zone";
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname, $zone ) = @_;

	require Zevenet::Farm::Base;

	my $output = -1;
	my $fvip = &getFarmVip( "vip", $fname );

	opendir ( my $dirh, "$configdir\/$fname\_gslb.cfg\/etc\/zones\/" );
	my @files = grep { /^$zone/ } readdir ( $dirh );
	closedir ( $dirh );

	if ( scalar @files == 0 )
	{
		open ( my $file, ">", "$configdir\/$fname\_gslb.cfg\/etc\/zones\/$zone" )
		  or warn "cannot open > $configdir\/$fname\_gslb.cfg\/etc\/zones\/$zone: $!";

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

sub getGSLBResources    # ( $farmname, $zone )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farmname, $zone ) = @_;

	require Zevenet::Farm::Config;

	my $backendsvs = &getFarmVS( $farmname, $zone, "resources" );
	my @resourcesArray;
	my $ind;

	my @be = split ( "\n", $backendsvs );

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

sub getGSLBFarmZonesStruct
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname = shift;

	my @zones   = &getGSLBFarmZones( $farmname );
	my $first   = 0;
	my $vserver = 0;
	my $pos     = 0;

	my @out_z = ();

	foreach my $zone ( @zones )
	{
		$pos++;
		$first = 1;
		my $ns         = &getFarmVS( $farmname, $zone, "ns" );
		my $backendsvs = &getFarmVS( $farmname, $zone, "resources" );
		my @be = split ( "\n", $backendsvs );
		my @out_re;
		my $resources = &getGSLBResources( $farmname, $zone );

		for my $resource ( @{ $resources } )
		{
			$resource->{ ttl } = undef if !$resource->{ ttl };
			$resource->{ ttl } += 0 if $resource->{ ttl };
		}

		push (
			   @out_z,
			   {
				 id        => $zone,
				 defnamesv => $ns,
				 resources => $resources,
			   }
		);
	}

	return \@out_z;
}

1;
