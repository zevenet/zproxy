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

my $routeparams = "initcwnd 10 initrwnd 10";
use Data::Dumper;
$Data::Dumper::Sortkeys = 1;

# send gratuitous ICMP packets for L3 aware
sub sendGPing # ($pif)
{
	my ( $pif ) = @_;

	my $gw = &gwofif( $pif );
	if ( $gw ne "" )
	{
		&logfile( "sending '$ping_bin -c $pingc $gw' " );
		my @eject = `$ping_bin -c $pingc $gw > /dev/null &`;
	}
}

# get conntrack sessions
sub getConntrackExpect # ($args)
{
	my ( $args ) = @_;
	open CONNS, "</proc/net/nf_conntrack_expect";

	#open CONNS, "</proc/net/nf_conntrack";
	my @expect = <CONNS>;
	close CONNS;
	return @expect;
}

sub getInterfaceConfig    # \%iface ($if_name, $ip_version)
{
	my ($if_name, $ip_version) = @_;

	my $if_line;
	my $if_status;
	my $config_filename = "$configdir/if_${if_name}_conf";
	$ip_version = 4 if ! $ip_version;

	if (open my $file, '<', "$config_filename")
	{
		my @lines = grep {!/^(\s*#|$)/} <$file>;
		for my $line (@lines)
		{
			my (undef, $ip) = split ';', $line;
			my $line_ipversion =	( $ip =~ /:/ ) ?	6
								:	( $ip =~ /\./ ) ?	4
								:						undef;
			
			if ($ip_version == $line_ipversion && !$if_line )
			{
				$if_line = $line;
			}
			elsif ( $line =~ /^status=/ )
			{
				$if_status = $line;
				$if_status =~ s/^status=//;
				chomp $if_status;
			}
		}
		close $file;
	}
	
	if ( ! $if_line || ! $if_status )
	{
		return undef;
	}

	chomp ( $if_line );
	my @if_params = split (';', $if_line);
	# Example: eth0;10.0.0.5;255.255.255.0;up;10.0.0.1;
	
	use IO::Socket;
	my $socket = IO::Socket::INET->new( Proto => 'udp' );

	my %iface;

	$iface{ name }    = shift @if_params;
	$iface{ addr }    = shift @if_params;
	$iface{ mask }    = shift @if_params;
	$iface{ gateway } = shift @if_params;                        # optional
	$iface{ status }   = $if_status;
	$iface{ ip_v }    = ( $iface{ addr } =~ /:/ ) ? '6' : '4';
	$iface{ dev }     = $iface{ name };
	$iface{ vini }    = undef;
	$iface{ vlan }    = undef;
	$iface{ mac }     = undef;

	if ( $iface{ dev } =~ /:/ )
	{
		( $iface{ dev }, $iface{ vini } ) = split ':', $iface{ dev };
	}

	if ( $iface{ dev } =~ /./ )
	{
		# dot must be escaped
		( $iface{ dev }, $iface{ vlan } ) = split '\.', $iface{ dev };
	}

	$iface{ mac } = $socket->if_hwaddr( $iface{ dev } );

	return \%iface;
}

# returns 1 if it was sucessfull
# returns 0 if it wasn't sucessfull
sub setInterfaceConfig # $bool ($if_ref)
{
	my $if_ref = shift;

	if (ref $if_ref ne 'HASH')
	{
		&logfile("Input parameter is not a hash reference");
		return undef;
	}

	&logfile("setInterfaceConfig: " . Dumper $if_ref);
	my @if_params = qw( name addr mask gateway );

	#~ my $if_line = join (';', @if_params);
	my $if_line = join (';', @{$if_ref}{name, addr, mask, gateway} ) . ';';
	my $config_filename = "$configdir/if_$$if_ref{ name }_conf";

	if ( ! -f $config_filename )
	{
		open my $fh, '>', $config_filename;
		print $fh "status=up\n";
		close $fh;
	}

	# Example: eth0;10.0.0.5;255.255.255.0;up;10.0.0.1;
	if (tie my @file_lines, 'Tie::File', "$config_filename")
	{
		my $ip_line_found; 

		for my $line (@file_lines)
		{
			# skip commented and empty lines
			if (grep {/^(\s*#|$)/} $line)
			{
				next;
			}

			my (undef, $ip) = split ';', $line;
			
			if ($$if_ref{ ip_v } == &ipversion( $ip ) && ! $ip_line_found)
			{
				# replace line
				$line = $if_line;
				$ip_line_found = 'true';
			}
			elsif ( $line =~ /^status=/ )
			{
				$line = "status=$$if_ref{status}";
			}
		}

		&logfile("setInterfaceConfig: if_line:$if_line status:$$if_ref{status}");
		
		if ( ! $ip_line_found )
		{
			&logfile("setInterfaceConfig: push  if_line:$if_line");
			push ( @file_lines, $if_line );
		}

		untie @file_lines;
	}
	else
	{
		&logfile("$config_filename: $!");

		return 0;
	}

	return 1;
}

sub getDevVlanVini # ($if_name)
{
	my %if;
	$if{dev} = shift;
	
	if ( $if{dev} =~ /:/ )
	{
		($if{dev}, $if{vini}) = split ':', $if{dev};
	}

	if ( $if{dev} =~ /\./ ) # dot must be escaped
	{
		($if{dev}, $if{vlan}) = split '\.', $if{dev};
	}
	
	return \%if;
}

sub getInterfaceSystemStatus # ($if_ref)
{
	my $if_ref = shift;

	$sw = $$if_ref{name} eq 'eth0.3';
	#~ &logfile("getInterfaceSystemStatus $$if_ref{name}:$$if_ref{status}");

	my $parent_if_name = &getParentInterfaceName( $if_ref->{name} );
	my $status_if_name = $if_ref->{name};
	
	if ( $if_ref->{vini} ne '' ) # vini
	{
		$status_if_name = $parent_if_name;
	}
	
	my $ip_output = `$ip_bin link show $status_if_name`;
	$ip_output =~ / state (\w+) /;
	my $if_status = lc $1;

	# Set as down vinis not available
	$ip_output = `$ip_bin addr show $status_if_name`;

	if ( $ip_output !~ /$$if_ref{ addr }/ && $if_ref->{vini} ne '' )
	{
		$$if_ref{ status } = 'down';
		return $$if_ref{ status };
	}

	unless ( $if_ref->{vini} ne '' && $if_ref->{status} eq 'down' ) # vini
	#~ if ( not ( $if_ref->{vini} ne '' && $if_ref->{status} ne 'up' ) ) # vini
	# if   ( $if_ref->{vini} eq '' || $if_ref->{status} eq 'up' ) ) # vini
	{
		$if_ref->{status} = $if_status;
	}
	
	#~ &logfile("getInterfaceSystemStatus $$if_ref{name}:$$if_ref{status}");
	
	return $if_ref->{status} if $if_ref->{status} eq 'down';

	#~ &logfile("getInterfaceSystemStatus parent_if_name:$parent_if_name");

	my $parent_if_ref = &getInterfaceConfig( $parent_if_name, $if_ref->{ip_v} );

	# 2) vlans do not require the parent interface to be configured
	if ( !$parent_if_name || !$parent_if_ref )
	{
		return $if_ref->{status};
	}
	
	#~ &logfile("getInterfaceSystemStatus $$parent_if_ref{name}:$$parent_if_ref{status}");

	return &getInterfaceSystemStatus( $parent_if_ref );
}

sub getParentInterfaceName # ($if_name)
{
	my $if_name = shift;

	my $if_ref = &getDevVlanVini( $if_name );
	my $parent_if_name;

	# child interface: eth0.100:virtual => eth0.100
	if ( $if_ref->{vini} ne '' && $if_ref->{vlan} ne '' )
	{
		$parent_if_name = "$$if_ref{dev}.$$if_ref{vlan}";
	}
	# child interface: eth0:virtual => eth0
	elsif ( $if_ref->{vini} ne '' && $if_ref->{vlan} eq '' )
	{
		$parent_if_name = $if_ref->{dev};
	}
	# child interface: eth0.100 => eth0
	elsif ( $if_ref->{vini} eq '' && $if_ref->{vlan} ne '' )
	{
		$parent_if_name = $if_ref->{dev};
	}
	# child interface: eth0 => undef
	elsif ( $if_ref->{vini} eq '' && $if_ref->{vlan} eq '' )
	{
		$parent_if_name = undef;
	}

	#~ &logfile("if_name:$if_name parent_if_name:$parent_if_name");

	return $parent_if_name;
}

sub getActiveInterfaceList
{
	my @configured_interfaces = @{ &getConfigInterfaceList() };

	# sort list
	@configured_interfaces = sort { $a->{name} cmp $b->{name} } @configured_interfaces;

	# apply device status heritage
	$_->{status} = &getInterfaceSystemStatus( $_ ) for @configured_interfaces;

	# discard interfaces down
	@configured_interfaces = grep { $_->{status} eq 'up' } @configured_interfaces;

	# find maximun lengths for padding
	my $max_dev_length;
	my $max_ip_length;

	for my $iface ( @configured_interfaces )
	{
		if ( $iface->{status} == 'up' )
		{
			my $dev_length = length $iface->{name};
			$max_dev_length = $dev_length if $dev_length > $max_dev_length;
			
			my $ip_length = length $iface->{addr};
			$max_ip_length = $ip_length if $ip_length > $max_ip_length;
		}
	}

	# make padding
	for my $iface ( @configured_interfaces )
	{
		my $dev_ip_padded = sprintf( "%-${max_dev_length}s -> %-${max_ip_length}s", $$iface{name}, $$iface{addr} );
		$dev_ip_padded =~ s/ +$//;
		$dev_ip_padded =~ s/ /&nbsp;/g;

		#~ &logfile("padded interface:$dev_ip_padded");
		$iface->{dev_ip_padded} = $dev_ip_padded;
	}

	return \@configured_interfaces;
}

sub getSystemInterfaceList
{
	my @interfaces; # output
	my @configured_interfaces = @{ &getConfigInterfaceList() };

	my $socket = IO::Socket::INET->new( Proto => 'udp' );
	my @system_interfaces = $socket->if_list;
	
	## Build system device "tree"
	for my $if_name ( @system_interfaces ) # list of interface names
	{
		# ignore loopback device, ipv6 tunnel, vlans and vinis
		next if $if_name =~ /^lo$|^sit\d+$/;
		next if $if_name =~ /\./;
		next if $if_name =~ /:/;

		my %if_parts = %{ &getDevVlanVini( $if_name ) };

		my $if_ref;
		my $if_flags = $socket->if_flags( $if_name );

		# run for IPv4 and IPv6
		for my $ip_stack (4, 6)
		{
			$if_ref = &getInterfaceConfig($if_name, $ip_stack);

			if (!$$if_ref{addr})
			{
				# populate not configured interface
				$$if_ref{ status } = ( $if_flags & IFF_UP ) ? "up" : "down";
				$$if_ref{ mac }    = $socket->if_hwaddr( $if_name );
				$$if_ref{ name }   = $if_name;
				$$if_ref{ addr }   = '';
				$$if_ref{ mask }   = '';
				$$if_ref{ dev }    = $if_parts{ dev };
				$$if_ref{ vlan }   = $if_parts{ vlan };
				$$if_ref{ vini }   = $if_parts{ vini };
				$$if_ref{ ip_v }   = $ip_stack;
			}

			# setup for configured and unconfigured interfaces
			#~ $$if_ref{ gateway } = '-' if ! $$if_ref{ gateway };
			
			if ( !( $if_flags & IFF_RUNNING ) && ( $if_flags & IFF_UP ) )
			{
				$if_ref{link} = "off";
			}

			# add interface to the list
			push (@interfaces, $if_ref);

			# add vlans
			for my $vlan_if_conf (@configured_interfaces)
			{
				next if $$vlan_if_conf{dev} ne $$if_ref{dev};
				next if $$vlan_if_conf{vlan} eq '';
				next if $$vlan_if_conf{vini} ne '';
				
				if ($$vlan_if_conf{ip_v} == $ip_stack)
				{
					#~ $$vlan_if_conf{ gateway } = '-' if ! $$vlan_if_conf{ gateway };

					push (@interfaces, $vlan_if_conf);

					# add vini of vlan
					for my $vini_if_conf (@configured_interfaces)
					{
						next if $$vini_if_conf{dev} ne $$if_ref{dev};
						next if $$vini_if_conf{vlan} ne $$vlan_if_conf{vlan};
						next if $$vini_if_conf{vini} eq '';
						
						if ($$vini_if_conf{ip_v} == $ip_stack)
						{
							#~ $$vini_if_conf{ gateway } = '-' if ! $$vini_if_conf{ gateway };
							push (@interfaces, $vini_if_conf);
						}
					}
				}
			}
			
			# add vini of nic
			for my $vini_if_conf (@configured_interfaces)
			{
				next if $$vini_if_conf{dev} ne $$if_ref{dev};
				next if $$vini_if_conf{vlan} ne '';
				next if $$vini_if_conf{vini} eq '';

				if ($$vini_if_conf{ip_v} == $ip_stack)
				{
					#~ $$vini_if_conf{ gateway } = '-' if ! $$vini_if_conf{ gateway };
					push (@interfaces, $vini_if_conf);
				}
			}
		}
	}

	@interfaces = sort { $a->{name} cmp $b->{name} } @interfaces;
	$_->{status} = &getInterfaceSystemStatus( $_ ) for @interfaces;

	return \@interfaces;
}

sub getSystemInterface # ($if_name)
{
	my $if_ref = {};
	$$if_ref{ name } = shift;
	#~ $$if_ref{ ip_v } = shift;
	
	my %if_parts = %{ &getDevVlanVini( $$if_ref{ name } ) };
	my $socket = IO::Socket::INET->new( Proto => 'udp' );
	my $if_flags = $socket->if_flags( $$if_ref{ name } );
	
	$$if_ref{ mac }    = $socket->if_hwaddr( $$if_ref{ name } );

	return undef if not $$if_ref{ mac };
	$$if_ref{ status } = ( $if_flags & IFF_UP ) ? "up" : "down";
	$$if_ref{ addr }   = '';
	$$if_ref{ mask }   = '';
	$$if_ref{ dev }    = $if_parts{ dev };
	$$if_ref{ vlan }   = $if_parts{ vlan };
	$$if_ref{ vini }   = $if_parts{ vini };

	return $if_ref;
}

1;
