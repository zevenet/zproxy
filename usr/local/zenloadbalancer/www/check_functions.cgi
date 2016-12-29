#!/usr/bin/perl
###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2016 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
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

# Notes about regular expressions:
#
# \w matches the 63 characters [a-zA-Z0-9_] (most of the time)
#

my $UNSIGNED8BITS = qr/(?:25[0-5]|2[0-4]\d|[01]?\d\d?)/;         # (0-255)
my $ipv4_addr     = qr/(?:$UNSIGNED8BITS\.){3}$UNSIGNED8BITS/;
my $ipv6_addr     = qr/(?:[\:\.a-f0-9]+)/;
my $ipv4v6        = qr/(?:$ipv4_addr|$ipv6_addr)/;
my $boolean       = qr/(?:true|false)/;
my $enable        = qr/(?:enable|disable)/;
my $natural = qr/[1-9]\d*/;    # natural number = {1, 2, 3, ...}

my $hostname = qr/[a-z][a-z0-9\-]{0,253}[a-z0-9]/;
my $service  = qr/[a-zA-Z1-9\-]+/;
my $zone     = qr/(?:$hostname\.)+[a-z]{2,}/;

my $vlan_tag    = qr/\d{1,4}/;
my $virtual_tag = qr/[a-zA-Z0-9]{1,13}/;
my $nic_if      = qr/[a-zA-Z0-9]{1,15}/;
my $bond_if     = qr/[a-zA-Z0-9]{1,15}/;
my $vlan_if     = qr/[a-zA-Z0-9]{1,13}\.$vlan_tag/;
my $port_range =
  qr/(?:[1-5]?\d{1,4}|6[0-4]\d{3}|65[1-4]\d{2}|655[1-2]\d{1}|6553[1-5])/;
my $graphsFrequency = qr/(?:daily|weekly|monthly|yearly)/;

my $dos_global= qr/(?:sshbruteforce|dropicmp)/;
my $dos_all 	=	qr/(?:limitconns|limitsec)/;
my $dos_tcp	= qr/(?:bogustcpflags|limitrst)/;


my %format_re = (

	# generic types
	'natural_num' => $natural,

	# hostname
	'hostname' => $hostname,
	
	# license
	'license_format' => qr/(?:txt|html)/,
	
	# log
	'log' => qr/[\.\-\w]+/,

	#zapi
	'zapi_key'      => qr/[a-zA-Z0-9]+/,
	'zapi_status'   => $enable,
	'zapi_password' => qr/.+/,

	# common
	'port'     => $port_range,
	'user'     => qr/[\w]+/,
	'password' => qr/.+/,

	# system
	'dns_nameserver' => $ipv4_addr,
	'dns'            => qr/(?:primary|secondary)/,
	'ssh_port'       => $port_range,
	'ssh_listen'     => qr/(?:$ipv4v6|\*)/,
	'snmp_status'    => $boolean,
	'snmp_ip'        => qr/(?:$ipv4v6|\*)/,
	'snmp_port'      => $port_range,
	'snmp_community' => qr{[\w]+},
	'snmp_scope'     => qr{(?:\d{1,3}\.){3}\d{1,3}\/\d{1,2}},    # ip/mask
	'ntp'            => qr{[\w\.]+},

	# farms
	'farm_name'    => qr/[a-zA-Z0-9\-]+/,
	'farm_profile' => qr/HTTP|GSLB|L4XNAT|DATALINK/,
	'backend'      => qr/\d+/,
	'service'      => $service,
	'farm_modules' => qr/(?:gslb|dslb|lslb)/,
	'service_position'      => qr/\d+/,

	# backup
	'backup'        => qr/[\w]+/,
	'backup_action' => qr/apply/,

	# graphs
	'graphs_frequency' => $graphsFrequency,
	'graphs_system_id' => qr/(?:cpu|load|ram|swap)/,
	'mount_point'      => qr/root[\w\-\.\/]*/,

	# gslb
	'zone'          => qr/(?:$hostname\.)+[a-z]{2,}/,
	'resource_id'   => qr/\d+/,
	'resource_name' => qr/(?:[\w\-\.]+|\@)/,
	'resource_ttl'  => qr/$natural/,                    # except zero
	'resource_type' => qr/(?:NS|A|AAAA|CNAME|DYNA|MX|SRV|TXT|PTR|NAPTR)/,
	'resource_data'      => qr/.+/,            # alow anything (because of TXT type)
	'resource_data_A'    => $ipv4_addr,
	'resource_data_AAAA' => $ipv6_addr,
	'resource_data_DYNA' => $service,
	'resource_data_NS'   => qr/[a-zA-Z0-9\-]+/,
	'resource_data_CNAME' => qr/[a-z\.]+/,
	'resource_data_MX'    => qr/[a-z\.]+/,
	'resource_data_TXT'   => qr/.+/,            # all characters allow
	'resource_data_SRV'   => qr/[a-z0-9 \.]/,
	'resource_data_PTR'   => qr/[a-z\.]+/,
	'resource_data_NAPTR' => qr/.+/,            # all characters allow

	# interfaces ( WARNING: length in characters < 16  )
	'nic_interface'    => $nic_if,
	'bond_interface'   => $bond_if,
	'vlan_interface'   => $vlan_if,
	'virt_interface'   => qr/[a-zA-Z0-9]{1,13}(?:\.[a-zA-Z0-9]{1,4})?:$virtual_tag/,
	'routed_interface' => qr/(?:$nic_if|$bond_if|$vlan_if)/,
	'interface_type'   => qr/(?:nic|vlan|virtual|bond)/,
	'vlan_tag'         => qr/$vlan_tag/,
	'virtual_tag'      => qr/$virtual_tag/,
	'bond_mode_num'    => qr/[0-6]/,
	'bond_mode_short' =>
	  qr/(?:balance-rr|active-backup|balance-xor|broadcast|802.3ad|balance-tlb|balance-alb)/,

	# notifications
	'notif_alert'  => qr/(?:backends|cluster)/,
	'notif_method' => qr/(?:email)/,
	'notif_tls'    => $boolean,
	'notif_action' => $enable,
	'notif_time'   => $natural,               # this value can't be 0

	# ipds
	'blacklists_name'      => qr{[a-zA-Z0-9]+},
	'blacklists_source'    => qr{(?:\d{1,3}\.){3}\d{1,3}(?:\/\d{1,2})?},
	'blacklists_source_id' => qr{\d+},
	'blacklists_type'  => qr{(?:local|remote)},
	'blacklists_policy'      => qr{(?:allow|deny)},
	'blacklists_url'       => qr{.+},
	'blacklists_hour'   => qr{\d+},
	'blacklists_min'   => qr{\d+},
	'blacklists_month'   => qr{\d+},
	'blacklists_dow'   => qr{\d+},
	'blacklists_dom'   => qr{\d+},
	'dos_name'      => qr/[\w]+/,
	'dos_rule'      => qr/(?:$dos_global|$dos_all|$dos_tcp)/,
	'dos_rule_farm' => qr/(?:$dos_all|$dos_tcp)/,
	'dos_rule_global' => $dos_global,
	'dos_rule_all'       => $dos_all,
	'dos_rule_tcp'      => $dos_tcp,
	# dos params
	'dos_time'      => $natural,
	'dos_limitConns'      => $natural,
	'dos_limit'      => $natural,
	'dos_limit_burst'      => $natural,
	'dos_status'      => qr/(?:down|up)/,
	'dos_port'      => $port_range,
	'dos_hits'      => $natural,	

	# certificates filenames
	'certificate' => qr/\w[\w\.-]*\.(?:pem|csr)/,
	'cert_pem'    => qr/\w[\w\.-]*\.pem/,
	'cert_csr'    => qr/\w[\w\.-]*\.csr/,
	'cert_dh2048' => qr/\w[\w\.-]*_dh2048\.pem/,

	# ips
	'IPv4_addr' => qr/$ipv4_addr/,
	'IPv4_mask' => qr/(?:$ipv4_addr|3[0-2]|[1-2][0-9]|[0-9])/,

	# farm guardian
	'fg_type'    => qr/(?:http|https|l4xnat|gslb)/,
	'fg_enabled' => $boolean,
	'fg_log'     => $boolean,
	'fg_time'    => qr/$natural/,                     # this value can't be 0

);

=begin nd
        Function: getValidFormat

        Validates a data format matching a value with a regular expression.
        If no value is passed as an argument the regular expression is returned.

        Usage:
			# validate exact data
			if ( ! &getValidFormat( "farm_name", $input_farmname ) ) {
				print "error";
			}

			# use the regular expression as a component for another regular expression 
			my $file_regex = &getValidFormat( "certificate" );
			if ( $file_path =~ /$configdir\/$file_regex/ ) { ... }

        Parameters:
				format_name	- type of format
				value		- value to be validated (optional)
				
        Returns:
				false	- If value failed to be validated
				true	- If value was successfuly validated
				regex	- If no value was passed to be matched

=cut

# &getValidFormat ( $format_name, $value );
sub getValidFormat
{
	my ( $format_name, $value ) = @_;

	#~ print "getValidFormat type:$format_name value:$value\n"; # DEBUG

	if ( exists $format_re{ $format_name } )
	{
		if ( defined $value )
		{
			#~ print "$format_re{ $format_name }\n"; # DEBUG
			return $value =~ /^$format_re{ $format_name }$/;
		}
		else
		{
			#~ print "$format_re{ $format_name }\n"; # DEBUG
			return $format_re{ $format_name };
		}
	}
	else
	{
		my $message = "getValidFormat: format $format_name not found.";
		&zenlog( $message );
		die ( $message );
	}
}

# validate port format and check if available when possible
sub getValidPort    # ( $ip, $port, $profile )
{
	my $ip      = shift;    # mandatory for HTTP, GSLB or no profile
	my $port    = shift;
	my $profile = shift;    # farm profile, optional

	#~ &zenlog("getValidPort( ip:$ip, port:$port, profile:$profile )");# if &debug;

	if ( $profile =~ /^(?:HTTP|GSLB)$/i )
	{
		return &isValidPortNumber( $port ) eq 'true'
		  && &checkport( $ip, $port ) eq 'false';
	}
	elsif ( $profile =~ /^(?:L4XNAT)$/i )
	{
		return &ismport( $port ) eq 'true';
	}
	elsif ( $profile =~ /^(?:DATALINK)$/i )
	{
		return $port eq undef;
	}
	elsif ( !defined $profile )
	{
		return &isValidPortNumber( $port ) eq 'true'
		  && &checkport( $ip, $port ) eq 'false';
	}
	else    # profile not supported
	{
		return 0;
	}
}

# check parameters when all params are optional
# before called:	getValidPutParams
sub getValidOptParams    # ( \%json_obj, \@allowParams )
{
	my $params         = shift;
	my $allowParamsRef = shift;
	my @allowParams    = @{ $allowParamsRef };
	my $output;
	my $pattern;

	if ( !keys %{ $params } )
	{
		return "Not found any param.";
	}

	# Check if any param isn't for this call
	$pattern .= "$_|" for ( @allowParams );
	chop ( $pattern );
	my @errorParams = grep { !/^(?:$pattern)$/ } keys %{ $params };
	if ( @errorParams )
	{
		$output .= "$_, " for ( @errorParams );
		chop ( $output );
		chop ( $output );
		$output = "The param(s) $output are not correct for this call.";
	}

	return $output;
}

# check parameters when there are required params
# before called:	getValidPostParams
sub getValidReqParams    # ( \%json_obj, \@requiredParams, \@optionalParams )
{
	my $params            = shift;
	my $requiredParamsRef = shift;
	my $allowParamsRef    = shift;
	my @allowParams       = @{ $allowParamsRef };
	my @requiredParams    = @{ $requiredParamsRef };
	push @allowParams, @requiredParams;
	my $output;
	my $pattern;

	# Check all required params are in called
	$pattern .= "$_|" for ( @requiredParams );

	chop ( $pattern );
	my $aux = grep { /^(?:$pattern)$/ } keys %{ $params };
	if ( $aux != scalar @requiredParams )
	{
		$aux = scalar @requiredParams - $aux;
		$output = "Missing required parameters. Parameters missed: $aux.";
	}

	# Check if any param isn't for this call
	if ( !$output )
	{
		$output  = "";
		$pattern = "";
		$pattern .= "$_|" for ( @allowParams );
		chop ( $pattern );
		my @errorParams = grep { !/^(?:$pattern)$/ } keys %{ $params };
		if ( @errorParams )
		{
			$output .= "$_, " for ( @errorParams );
			chop ( $output );
			chop ( $output );
			$output = "The param(s) $output are not correct for this call.";
		}
	}

	return $output;
}

1;
