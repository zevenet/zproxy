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

use Zevenet::Core;
use Zevenet::Lock;

use Zevenet::Farm::L4xNAT;

use Zevenet::Farm::Core;
use Zevenet::Farm::Base;
use Zevenet::Farm::Stats;
use Zevenet::Farm::Factory;
use Zevenet::Farm::Action;
use Zevenet::Farm::Config;
use Zevenet::Farm::Backend;

#GET /farms
sub farms    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my @out;
	my @files = &getFarmList();

	require Zevenet::Farm::Action;
	foreach my $file ( @files )
	{
		my $name   = &getFarmName( $file );
		my $type   = &getFarmType( $name );
		my $status = &getFarmStatus( $name );
		my $vip    = &getFarmVip( 'vip', $name );
		my $port   = &getFarmVip( 'vipp', $name );

		$status = "needed restart" if $status eq 'up' && &getFarmRestartStatus( $name );

		push @out,
		  {
			farmname => $name,
			profile  => $type,
			status   => $status,
			vip      => $vip,
			vport    => $port
		  };
	}

	my $body = {
				 description => "List farms",
				 params      => \@out,
	};

	# Success
	&httpResponse( { code => 200, body => $body } );
}

# GET /farms/LSLBFARM
sub farms_lslb    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my @out;
	my @files = &getFarmList();

	require Zevenet::Farm::Action;
	foreach my $file ( @files )
	{
		my $name = &getFarmName( $file );
		my $type = &getFarmType( $name );
		next unless $type =~ /^(?:http|https|l4xnat)$/;
		my $status = &getFarmStatus( $name );
		my $vip    = &getFarmVip( 'vip', $name );
		my $port   = &getFarmVip( 'vipp', $name );

		$status = "needed restart" if $status eq 'up' && &getFarmRestartStatus( $name );

		push @out,
		  {
			farmname => $name,
			profile  => $type,
			status   => $status,
			vip      => $vip,
			vport    => $port
		  };
	}

	my $body = {
				 description => "List LSLB farms",
				 params      => \@out,
	};

	# Success
	&httpResponse( { code => 200, body => $body } );
}

# GET /farms/GSLBFARM
sub farms_gslb    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my @out;
	my @files = &getFarmList();

	require Zevenet::Farm::Action;
	foreach my $file ( @files )
	{
		my $name = &getFarmName( $file );
		my $type = &getFarmType( $name );
		next unless $type eq 'gslb';
		my $status = &getFarmStatus( $name );
		my $vip    = &getFarmVip( 'vip', $name );
		my $port   = &getFarmVip( 'vipp', $name );

		$status = "needed restart" if $status eq 'up' && &getFarmRestartStatus( $name );

		push @out, {
			farmname => $name,

			#~ profile  => $type,
			status => $status,
			vip    => $vip,
			vport  => $port
		};
	}

	my $body = {
				 description => "List GSLB farms",
				 params      => \@out,
	};

	# Success
	&httpResponse( { code => 200, body => $body } );
}

# GET /farms/DATALINKFARM
sub farms_dslb    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my @out;
	my @files = &getFarmList();

	foreach my $file ( @files )
	{
		my $name = &getFarmName( $file );
		my $type = &getFarmType( $name );
		next unless $type eq 'datalink';
		my $status = &getFarmStatus( $name );
		my $vip    = &getFarmVip( 'vip', $name );
		my $iface  = &getFarmVip( 'vipp', $name );

		push @out, {
			farmname => $name,

			#~ profile  => $type,
			status    => $status,
			vip       => $vip,
			interface => $iface
		};
	}

	my $body = {
				 description => "List DSLB farms",
				 params      => \@out,
	};

	# Success
	&httpResponse( { code => 200, body => $body } );
}

#GET /farms/<name>
sub farms_name    # ( $farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname = shift;

	# Check that the farm exists
	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exist.";
		my $body = {
					 description => "Get farm",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	my $type = &getFarmType( $farmname );

	if ( $type eq 'http' || $type eq 'https' )
	{
		include 'Zevenet::API3::Farm::Get::HTTP';
		&farms_name_http( $farmname );
	}
	elsif ( $type eq 'gslb' )
	{
		include 'Zevenet::API3::Farm::Get::GSLB';
		&farms_name_gslb( $farmname );
	}
	elsif ( $type eq 'l4xnat' )
	{
		include 'Zevenet::API3::Farm::Get::L4xNAT';
		&farms_name_l4( $farmname );
	}
	elsif ( $type eq 'datalink' )
	{
		include 'Zevenet::API3::Farm::Get::Datalink';
		&farms_name_datalink( $farmname );
	}
}

1;
