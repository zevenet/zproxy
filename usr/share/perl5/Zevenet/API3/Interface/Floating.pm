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

sub delete_interface_floating # ( $floating )
{
	my $floating = shift;

	require Zevenet::Net::Floating;

	my $description = "Remove floating interface";
	my $floatfile = &getGlobalConfiguration('floatfile');
	my $float_ifaces_conf = &getConfigTiny( $floatfile );

	# validate BOND
	unless ( $float_ifaces_conf->{_}->{ $floating } )
	{
		# Error
		my $errormsg = "Floating interface not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	require Zevenet::Farm::L4xNAT::Config;

	eval {
		delete $float_ifaces_conf->{_}->{ $floating };

		&setConfigTiny( $floatfile, $float_ifaces_conf ) or die;

		# refresh l4xnat rules
		&reloadL4FarmsSNAT();
	};
	if ( ! $@ )
	{
		# Success
		my $message = "The floating interface has been removed.";
		my $body = {
					 description => $description,
					 success     => "true",
					 message     => $message,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		# Error
		my $errormsg = "The floating interface could not be removed";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
}

# address or interface
sub modify_interface_floating # ( $json_obj, $floating )
{
	my $json_obj = shift;
	my $interface = shift;

	my $description = "Modify floating interface";

	#~ &zenlog("modify_interface_floating interface:$interface json_obj:".Dumper $json_obj );

	if ( grep { $_ ne 'floating_ip' } keys %{$json_obj} )
	{
		# Error
		my $errormsg = "Parameter not recognized";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	unless ( keys %{ $json_obj } )
	{
		# Error
		my $errormsg = "Need to use floating_ip parameter";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	require Zevenet::Net::Interface;

	my $ip_v = 4;
	my $if_ref = &getInterfaceConfig( $interface, $ip_v );

	unless ( $if_ref )
	{
		# Error
		my $errormsg = "Floating interface not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	$if_ref = undef;

	if ( exists $json_obj->{ floating_ip } )
	{
		# validate ADDRESS format
		unless ( $json_obj->{ floating_ip } && &getValidFormat( 'IPv4_addr', $json_obj->{ floating_ip } ) )
		{
			# Error
			my $errormsg = "Invalid floating address format";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		my @interfaces = &getInterfaceTypeList( 'virtual' );
		( $if_ref ) = grep { $json_obj->{ floating_ip } eq $_->{ addr } && $_->{ parent } eq $interface } @interfaces;

		# validate ADDRESS in system
		unless ( $if_ref )
		{
			# Error
			my $errormsg = "Virtual interface with such address not found";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 404, body => $body });
		}
	}

	require Zevenet::Net::Floating;
	require Zevenet::Farm::L4xNAT::Config;

	eval {
		my $floatfile = &getGlobalConfiguration('floatfile');
		my $float_ifaces_conf = &getConfigTiny( $floatfile );

		$float_ifaces_conf->{ _ }->{ $interface } = $if_ref->{ name };

		&setConfigTiny( $floatfile, $float_ifaces_conf ) or die;

		# refresh l4xnat rules
		&reloadL4FarmsSNAT();
	};

	unless ( $@ )
	{
		# Error
		my $message = "Floating interface modification done";
		my $body = {
					 description => $description,
					 success       => "true",
					 message     => $message
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		# Error
		my $errormsg = "Floating interface modification failed";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub get_interfaces_floating
{
	require Zevenet::Net::Interface;
	require Zevenet::Net::Floating;

	my $description = "List floating interfaces";

	# Interfaces
	my @output;
	my @ifaces = @{ &getSystemInterfaceList() };
	my $floatfile = &getGlobalConfiguration('floatfile');
	my $float_ifaces_conf = &getConfigTiny( $floatfile );

	for my $iface ( @ifaces )
	{
		#~ &zenlog( "getActiveInterfaceList: $iface->{ name }" );
		next unless $iface->{ ip_v } == 4;
		next if $iface->{ type } eq 'virtual';
		next unless $iface->{ addr };

		my $floating_ip = undef;
		my $floating_interface = undef;

		if ( $float_ifaces_conf->{_}->{ $iface->{ name } } )
		{
			$floating_interface = $float_ifaces_conf->{_}->{ $iface->{ name } };
			my $if_ref = &getInterfaceConfig( $floating_interface );
			$floating_ip = $if_ref->{ addr };
		}

		push @output,
		  {
			interface   => $iface->{ name },
			floating_ip => $floating_ip,
			interface_virtual => $floating_interface,
		  };

		#~ $output{ $iface->{name} } = $iface->{name} unless $output{ $iface->{name} };
	}

	my $body = {
				 description => $description,
				 params      => \@output,
	};

	&httpResponse({ code => 200, body => $body });
}

sub get_floating
{
	my $floating = shift;

	require Zevenet::Net::Interface;
	require Zevenet::Net::Floating;

	my $description = "Show floating interface";

	# Interfaces
	my $output;
	my @ifaces = @{ &getSystemInterfaceList() };
	my $floatfile = &getGlobalConfiguration('floatfile');
	my $float_ifaces_conf = &getConfigTiny( $floatfile );

	for my $iface ( @ifaces )
	{
		#~ &zenlog( "getActiveInterfaceList: $iface->{ name }" );
		next unless $iface->{ ip_v } == 4;
		next if $iface->{ type } eq 'virtual';
		next unless $iface->{ name } eq $floating;

		my $floating_ip = undef;
		my $floating_interface = undef;

		unless ( $iface->{ addr } )
		{
			# Error
			my $errormsg = "This interface has no address configured";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse({ code => 400, body => $body });
		}

		$floating_ip = undef;

		if ( $float_ifaces_conf->{_}->{ $iface->{ name } } )
		{
			$floating_interface = $float_ifaces_conf->{_}->{ $iface->{ name } };
			my $if_ref = &getInterfaceConfig( $floating_interface );
			$floating_ip = $if_ref->{ addr };
		}

		$output = {
					interface   => $iface->{ name },
					floating_ip => $floating_ip,
					interface_virtual => $floating_interface,
		};

		#~ $output{ $iface->{name} } = $iface->{name} unless $output{ $iface->{name} };
	}

	my $body = {
				 description => $description,
				 params      => $output,
	};

	&httpResponse({ code => 200, body => $body });
}

1;
