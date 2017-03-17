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

#
sub getFarmCertificatesSNI    #($fname)
{
	my $fname = shift;

	my $type = &getFarmType( $fname );
	my @output;

	if ( $type eq "https" )
	{
		my $file = &getFarmFile( $fname );
		open FI, "<$configdir/$file";
		my @content = <FI>;
		close FI;
		foreach my $line ( @content )
		{
			if ( $line =~ /Cert "/ && $line !~ /\#.*Cert/ )
			{
				my @partline = split ( '\"', $line );
				@partline = split ( "\/", $partline[1] );
				my $lfile = @partline;
				push ( @output, $partline[$lfile - 1] );

			}
		}
	}

	#&zenlog("getting 'Certificate $output' for $fname farm $type");
	return @output;
}

#
sub setFarmCertificateSNI    #($cfile,$fname)
{
	my ( $cfile, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;
	my $sw     = 0;
	my $i      = 0;
	if ( $cfile =~ /^$/ )
	{
		&zenlog ( "Certificate not found." );
		return $output;
	}

	&zenlog( "setting 'Certificate $cfile' for $fname farm $type" );	
	if ( $type eq "https" )
	{
		use Tie::File;
		tie my @array, 'Tie::File', "$configdir/$ffile";
		for ( @array )
		{
			if ( $_ =~ /Cert "/ )
			{

				#s/.*Cert\ .*/\tCert\ \"$configdir\/$cfile\"/g;
				#$output = $?;
				$sw = 1;
			}
			if ( $_ !~ /Cert "/ && $sw eq 1 )
			{
				splice @array, $i, 0, "\tCert\ \"$configdir\/$cfile\"";
				$output = 0;
				last;
			}
			$i++;
		}
		untie @array;
	}
	else
	{
		&zenlog ( "Error, adding certificate to farm $fname. This farm is not https type." );
	}

	return $output;
}

#delete the selected certificate from HTTP farms
sub setFarmDeleteCertSNI    #($certn,$fname)
{
	my ( $certn, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;
	my $i      = 0;
	my $j      = 0;

	&zenlog( "deleting 'Certificate $certn' for $fname farm $type" );
	if ( $type eq "https" )
	{
		use Tie::File;
		tie my @array, 'Tie::File', "$configdir/$ffile";

		for ( @array )
		{
			if ( $_ =~ /Cert "/ )
			{
				$i++;
			}

			if ( $_ =~ /Cert/ && $i eq "$certn" )
			{
				splice @array, $j, 1,;
				$output = 0;
				if ( $array[$j] !~ /Cert/ && $array[$j - 1] !~ /Cert/ )
				{
					splice @array, $j, 0, "\tCert\ \"$configdir\/zencert.pem\"";
					$output = 1;

				}
				last;
			}
			$j++;
		}
		untie @array;
	}

	return $output;
}

#delete the selected certificate from HTTP farms
sub setFarmDeleteCertNameSNI    #($certn,$fname)
{
	my ( $certname, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;
	my $j      = 0;

	&zenlog( "deleting 'Certificate $certname' for $fname farm $type" );

	if ( $type eq "https" )
	{
		use Tie::File;
		tie my @array, 'Tie::File', "$configdir/$ffile";

		for ( @array )
		{
			if ( $_ =~ /Cert "$configdir\/$certname"/ )
			{
				splice @array, $j, 1,;
				$output = 0;

				if ( $array[$j] !~ /Cert/ && $array[$j - 1] !~ /Cert/ )
				{
					splice @array, $j, 0, "\tCert\ \"$configdir\/zencert.pem\"";
					$output = 1;
				}
				last;
			}
			$j++;
		}
		untie @array;
	}

	return $output;
}

# Returns a list of the farm names
sub getFarmNameList
{
	my @farm_names;    # output: returned list

	# take every farm filename
	foreach my $farm_filename ( &getFarmList() )
	{
		# add the farm name to the list
		push ( @farm_names, &getFarmName( $farm_filename ) );
	}

	return @farm_names;
}

sub getNumberOfFarmTypeRunning
{
	my $type    = shift;    # input value
	my $counter = 0;        # return value

	foreach my $farm_name ( &getFarmNameList() )
	{
		# count if requested farm type and running
		my $current_type = &getFarmType( $farm_name );
		my $current_status = &getFarmStatus( $farm_name );

		if ( $current_type eq $type && $current_status eq 'up' )
		{
			$counter++;
		}
	}

	#~ &zenlog( "getNumberOfFarmTypeRunning: $type -> $counter" );  ########

	return $counter;
}

sub getFarmTable
{
	my $farm_name = shift;
	my $farm_type = shift;

	my @table;

	foreach my $name ( getFarmNameList() )
	{
		my $vip  = &getFarmVip( "vip",  $name );
		my $vipp = &getFarmVip( "vipp", $name );
		my $status = &getFarmStatus( $name );
		my $type   = &getFarmType( $name );

		push @table, [$name, $vip, $vipp, $status, $type];
	}

	return \@table;
}

1;
