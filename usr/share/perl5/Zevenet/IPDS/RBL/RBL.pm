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
use Tie::File;

use Zevenet::Core;
use Zevenet::Debug;
use Zevenet::IPDS::Core;

# rbl configuration path
my $rblPath              = &getGlobalConfiguration( 'configdir' ) . "/ipds/rbl";
my $rblConfigFile        = "$rblPath/rbl.conf";
my $preloadedDomainsFile = "$rblPath/preloaded_domains.conf";
my $userDomainsFile      = "$rblPath/user_domains.conf";

apply_farm:

=begin nd
Function: getRBLFarm

	Return all farms where the rule is applied

Parameters:
	Rule - Rule name 
				
Returns:
	Array ref - List with all farms where this rule is applied
	
=cut

sub getRBLFarm
{
	my ( $rule ) = @_;

	return &getRBLObjectRuleParam( $rule, 'farms' );
}

=begin nd
Function: addRBLFarm

	Associate a farm with a IPDS object, adding the farm to the configuration file of the rule. If the farm is up, apply the rule 

Parameters:
	Farmname - Farm name 
	Rule - Rule name 
					
Returns:
	None - .
	
=cut

sub addRBLFarm
{
	my ( $farmname, $rule ) = @_;
	my $error;

	# if the farm is in UP status, apply it the rule
	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		# to start a RBL rule it is necessary that the rule has almost one domain
		if ( !@{ &getRBLObjectRuleParam( $rule, 'domains' ) } )
		{
			&zenlog( "RBL rule, $rule, was not started because doesn't have any domain." );
			return -1;
		}

		# if rule is not running, start it
		if ( &getRBLStatusRule( $rule ) eq 'down' )
		{
			$error = &runRBLStartPacketbl( $rule );
		}

		if ( !$error )
		{
			# create iptables rule to link with rbl rule
			$error = &runRBLIptablesRule( $rule, $farmname, 'insert' );
		}
	}

	if ( !$error )
	{
		# Add to configuration file
		&setRBLObjectRuleParam( $rule, 'farms-add', $farmname );
	}

	return $error;
}

=begin nd
Function: delRBLFarm

	Disassociate a farm from a IPDS object, removing the farm from the configuration file of the rule. If the farm is up, stop the rule

Parameters:
	Rule - Rule name 
	Farmname - Farm name 
				
Returns:
	None - .
	
=cut

sub delRBLFarm
{
	my ( $farmname, $rule ) = @_;
	my $error;

	# if the farm is in UP status, apply it the rule
	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		# create iptables rule to link with rbl rule
		$error = &runRBLIptablesRule( $rule, $farmname, 'delete' );

		# if another farm is not using this rule, the rule is stopped
		if ( !$error && !&getRBLRunningFarmList( $rule ) )
		{
			$error = &runRBLStopPacketbl( $rule );
		}
	}

	# Remove from configuration file
	&setRBLObjectRuleParam( $rule, 'farms-del', $farmname );

	return $error;
}

objects:

# A object is defined for its configuration file, there it set up the object parameters and which farm is applied

=begin nd
Function: setRBLCreateDirectory

	This function creates the RBL directory and RBL config file if they are not exist.	

Parameters:
				
Returns:
	none - .
	
=cut

sub setRBLCreateDirectory
{
	if ( !-d $rblPath )
	{
		&logAndRun( &getGlobalConfiguration( 'mkdir' ) . " -p $rblPath" );
		&zenlog( "Created $rblPath directory." );
	}

	# create list config if doesn't exist
	if ( !-e $rblConfigFile )
	{
		&logAndRun( &getGlobalConfiguration( 'touch' ) . " $rblConfigFile" );
		&zenlog( "Created $rblConfigFile file." );
	}

	# create list config if doesn't exist
	if ( !-e $userDomainsFile )
	{
		&logAndRun( &getGlobalConfiguration( 'touch' ) . " $userDomainsFile" );
		&zenlog( "Created $userDomainsFile file." );
	}
}

=begin nd
Function: setRBLInitialParams

	This function return a struct used as template to create a RBL object

Parameters:
				
Returns:
	hash ref - Struct with default values for a rbl rule
	
=cut

sub getRBLInitialParams
{
	my $initial = {

# save a list of farms split by space character. These farms are the farms where this rule is applied
		'farms' => '',

		# save a list of domains split by space character
		'domains' => '',

# this value is written with a nf_queue is assignate to this rule. The maximum nf_queue value is 256
		'nf_queue_number' => '',

		# Cache size, parameter "CacheSize"
		'cache_size' => 8192,

		# Cache time, parameter "CacheTTL"
		'cache_time' => 3600,

		# maximum number of packet in the queue
		'queue_size' => 64538,

# Log lvl, syslog log levels from 0 to 7: 0 Emergency, 1 Alert, 2 Critical, 3 Error, 4 Warning, 5 Notice, 6 Informational, or 7 Debug
		'log_level' => 5,

		# This mode logs the action but non blocking the packet
		'only_logging' => 'no',

		# maximum number of threads for packetbl
		'threadmax' => 0,

		# Scan local traffic
		'local_traffic' => 'no',
	};

	return $initial;
}

=begin nd
Function: getRBLExists

	Get if a RBL rule with this name exists

Parameters:
	Rule - Rule name
				
Returns:
	Integer - 1 if it exists or 0 if it doesn't exist
	
=cut

sub getRBLExists
{
	my $rule   = shift;
	my $output = 0;

	$output = 1 if ( grep ( /^$rule$/, &getRBLRuleList() ) );

	return $output;
}

=begin nd
Function: getRBLRuleList

	Get an array with all RBL rule names

Parameters:
				
Returns:
	Array - RBL name list
	
=cut

sub getRBLRuleList
{
	use Config::Tiny;
	my $fileHandle = Config::Tiny->read( $rblConfigFile );

	return keys %{ $fileHandle };
}

=begin nd
Function: getRBLObjectRule

	Get parameters of a RBL rule

Parameters:
				
Returns:
	hash ref - Struct with the RBL rule data
	
	{
		domains = [ domain1, domain2... ],
		farms = [ farm1, farm2... ],
		name = rule_name,
		nf_queue_number	= queue_number,			# this parameter is transparent to user
		cache_size	= cache_size,
		cache_time	= cache_time,
		queue_size	= queue_size,
		threadmax	= thread_maximum,
		local_traffic	= local_traffic,
	}
	
=cut

sub getRBLObjectRule
{
	my $rule = shift;

	use Config::Tiny;
	my $fileHandle = Config::Tiny->read( $rblConfigFile );

	my $output  = $fileHandle->{ $rule };
	my @domains = split ( ' ', $fileHandle->{ $rule }->{ 'domains' } );
	my @farms   = split ( ' ', $fileHandle->{ $rule }->{ 'farms' } );

	$output->{ 'domains' } = \@domains;
	$output->{ 'farms' }   = \@farms;

	$output->{ 'status' } = &getRBLStatusRule( $rule );

	return $output;
}

=begin nd
Function: getRBLObjectRuleParam

	Get the value of a parameter (only one).
	The available parameters are: "name" is the RBL rule name, "cache_size" is the size of the cache, "cache_time" is the time that a source is blocked
	by the cache, "nf_queue_number" is the queue where the rule is applied, "domains" are the domains that the RBL rule does requests and "farms" are the farms
	where the RBL rule is applied.

Parameters:
	Rule - Rule name
	Key - Requested parameter
				
Returns:
	String - if the requested parameter is "name"
	Integer - if the requested parameter is "cache_size", "cache_time", "queue_size", "threadmax" or "nf_queue_number"
	yes/no - if the requested parameter is "local_traffic"
	Array ref - if the requested parameter is "domains" of "farms" 
	
=cut

sub getRBLObjectRuleParam
{
	my $rule = shift;
	my $key  = shift;

	my $obj = &getRBLObjectRule( $rule );

	return $obj->{ $key };
}

=begin nd
Function: addRBLCreateObjectRule

	Create a object through its configuration file

Parameters:
	Rule - Rule name
				
Returns:
	Integer - 0 on success or -1 on failure
	
=cut

sub addRBLCreateObjectRule
{
	my $rule = shift;

	# check that the rule is not exist
	if ( &getRBLExists( $rule ) )
	{
		return -1;
	}

	# Get default parameters
	my $params = &getRBLInitialParams();

	# Add rule name
	$params->{ 'name' } = $rule;

	use Config::Tiny;
	my $fileHandle = Config::Tiny->read( $rblConfigFile );

	$fileHandle->{ $rule } = $params;

	$fileHandle->write( $rblConfigFile );

	&zenlog( "The RBL rule \"$rule\" was successfully created." );

	return 0;
}

=begin nd
Function: setRBLObjectRule

	Modify an object, receive a hash with all parameters to modify.

Parameters:
	Rule - Rule name
	Hash ref - Hash with the value to change and its values
				
Returns:
	Integer - 0 on success or -1 on failure
	
=cut

sub setRBLObjectRule
{
	my $rule   = shift;
	my $params = shift;

	use Config::Tiny;
	my $fileHandle = Config::Tiny->read( $rblConfigFile );

	foreach my $key ( keys %{ $params } )
	{
		$fileHandle->{ $rule }->{ $key } = $params->{ $key };
	}

	$fileHandle->write( $rblConfigFile );

	return 0;
}

=begin nd
Function: setRBLObjectRuleParam

	Set the value of a parameter (only one)     

Parameters:
	Rule - Rule name
	Key - Parameter to set a value
	Value - Value for the parameter
				
Returns:
	Integer - 0 on success or -1 on failure
	
=cut

sub setRBLObjectRuleParam
{
	my $name  = shift;
	my $key   = shift;
	my $value = shift;

	use Config::Tiny;
	my $fileHandle = Config::Tiny->read( $rblConfigFile );

	my $action;

	# if command has a action, split it
	# key-action
	# possible actions are 'add' or 'delete'
	if ( $key =~ /(\w+)(?:-(\w+))?/ )
	{
		$key    = $1;
		$action = $2;
	}

	if ( 'add' eq $action )
	{
		if ( $fileHandle->{ $name }->{ $key } !~ /(^| )$value( |$)/ )
		{
			$fileHandle->{ $name }->{ $key } .= " $value";
		}
	}
	elsif ( 'del' eq $action )
	{
		$fileHandle->{ $name }->{ $key } =~ s/(^| )$value( |$)/ /;
	}
	else
	{
		$fileHandle->{ $name }->{ $key } = $value;
	}

	$fileHandle->write( $rblConfigFile );

	return 0;
}

=begin nd
Function: addRBLCopyObjectRule

	Copy a object through its configuration file but deleting its associated farms

Parameters:
	Rule - Rule name
				
Returns:
	Integer - 0 on success or -1 on failure
	
=cut

sub addRBLCopyObjectRule
{
	my $rule    = shift;
	my $newrule = shift;

	# check if the rule already exists
	if ( &getRBLExists( $newrule ) )
	{
		return -1;
	}

	# Get default parameters
	my $params = &getRBLObjectRule( $rule );

	# Add rule name
	$params->{ 'name' }            = $newrule;
	$params->{ 'farms' }           = '';
	$params->{ 'nf_queue_number' } = '';
	$params->{ 'domains' }         = join ( " ", @{ $params->{ 'domains' } } );

	use Config::Tiny;
	my $fileHandle = Config::Tiny->read( $rblConfigFile );
	$fileHandle->{ $newrule } = $params;

	$fileHandle->write( $rblConfigFile );

	return 0;
}

=begin nd
Function: setRBLRenameObjectRule 

	Rename a RBL rule. The farm must be stopped.

Parameters:
	Rule - Rule name
	NewRule - New name for the rule
				
Returns:
	Integer - 0 on success or -1 on failure
	
=cut

sub setRBLRenameObjectRule
{
	my $rule    = shift;
	my $newname = shift;

	# check that the rule is not exist
	if ( &getRBLExists( $newname ) )
	{
		return -1;
	}

	# get applied farms
	my @farms = @{ &getRBLObjectRuleParam( $rule, 'farms' ) };

	# copy object
	&addRBLCopyObjectRule( $rule, $newname );

	# apply to farms
	foreach my $farm ( @farms )
	{
		&addRBLFarm( $farm, $newname );
	}

	# Remove old object
	&delRBLDeleteObjectRule( $rule );

	return 0;
}

=begin nd
Function: addRBLCopyObjectRule

	Delete a object through its configuration file

Parameters:
	Rule - Rule name
				
Returns:
	Integer - 0 on success or -1 on failure
	
=cut

sub delRBLDeleteObjectRule
{
	my $rule = shift;

	# check that the rule is not exist
	if ( !&getRBLExists( $rule ) )
	{
		&zenlog( "Error, the RBL rule \"$rule\" doesn't exist." );
		return -1;
	}

	use Config::Tiny;
	my $fileHandle = Config::Tiny->read( $rblConfigFile );
	delete $fileHandle->{ $rule };
	$fileHandle->write( $rblConfigFile );

	&zenlog( "The RBL rule \"$rule\" was successfully removed." );

	return 0;
}

=begin nd
Function: getRBLFarmApplied

	Return a list with all rules where the farm is applied

Parameters:
	Farmname -  Farm name
				
Returns:
	Array - list of RBL rules
	
=cut

sub getRBLFarmApplied
{
	my $farmname = shift;

	my @rules;

	foreach my $rule ( @{ &getRBLRuleList() } )
	{
		if ( grep ( /^$farmname$/, @{ &getRBLObjectRuleParam( $rule, 'farms' ) } ) )
		{
			push @rules, $rule;
		}
	}
	return \@rules;
}

=begin nd
Function: getRBLRunningFarmList

	Return a list with all farms that are using currently this rule. Looking and greping iptables list

Parameters:
	Rule - Rule name 
				
Returns:
	Array - List of farm names 
	
=cut

sub getRBLRunningFarmList
{
	my $rule = shift;

	my @farms;
	my $table           = "raw";
	my $chain           = &getIPDSChain( "rbl" );
	my @iptables_output = &getIptListV4( $table, $chain );
	my $farm_re         = &getValidFormat( 'farm_name' );

	foreach my $line ( @iptables_output )
	{
		if ( $line =~ /RBL,${rule},($farm_re)/ )
		{
			push @farms, $1;
		}
	}

	return @farms;
}

rules:

# To work with the rule status, exist a /tmp/IPDS/<module> directory where exist a file foreach rule applied to the system
# /tmp/IPDS/<module> is useful to control the active rules and create complex logs with more information and be able to restart status of blocking connections
# To apply to the system a rule the farm has to be in UP status
# adding log level, add a log rule before then drop rule (optional)

=begin nd
Function: getRBLStatusRule

	Check if a RBL rule is running. Check packetbl pid file.

Parameters:
	String - Rule name 
				
Returns:
	String - "up" if the rule is running or "down" if it is not running
	
=cut

sub getRBLStatusRule
{
	my $rule   = shift;
	my $status = "down";
	if ( &getRBLPacketblPid( $rule ) )
	{
		$status = "up";
	}

	return $status;
}

=begin nd
Function: runRBLIptablesRule

	Create a iptables for a farm with a action ( -A, -I, -D )

Parameters:
	Rulename -  Rule name
	Farmname -  Farm name. If farm name is in blank, the rule applies to all destine IPs and ports
	Action - Action to apply to iptables. The available options are: 'append', create the rule the last in the iptables list;
	  'insert', create the rule the first in the iptables list; or 'delete' delete the rule from iptables list
				
Returns:
	Integer - 0 on success or other value on failure
	
FIXME: Define the chain and the table for iptables
	
=cut

sub runRBLIptablesRule
{
	my ( $rule, $farmname, $action ) = @_;
	my $error;
	my $nfqueue = &getRBLObjectRuleParam( $rule, 'nf_queue_number' );
	my $rbl_chain = &getIPDSChain( "rbl" );

	my @farmMatch = &getIPDSFarmMatch( $farmname );

	if ( $action eq "insert" )
	{
		$action = "-I";
	}
	elsif ( $action eq "append" )
	{
		$action = "-A";
	}
	elsif ( $action eq "delete" )
	{
		$action = "-D";
	}
	else
	{
		$error = -1;
		&zenlog( "Wrong action to create the rule " );
	}

	# only check packets with SYN flag: "--tcp-flags SYN SYN"
	# if packetbl is not running, return packet to netfilter flow: "--queue-bypass"

# iptables -I INPUT -p tcp --tcp-flags SYN SYN -i eth0 --dport 80 -j NFQUEUE --queue-num 0 --queue-bypass

	# execute without interblock
	foreach my $ruleParam ( @farmMatch )
	{
		&zenlog( "rule param:$ruleParam " );
		my $tcp;
		my $cmd;

		# not add rules to UDP ports
		if ( $ruleParam !~ /\-\-protocol udp/ )
		{
			# It is necessary specific the tcp protocol to check add SYN flag option
			if ( $ruleParam !~ /\-\-protocol tcp/ )
			{
				$tcp = "--protocol tcp";
			}
			else
			{
				$tcp = "";
			}
			$cmd =
			    &getGlobalConfiguration( 'iptables' )
			  . " $action $rbl_chain -t raw $ruleParam $tcp --tcp-flags SYN SYN -j NFQUEUE --queue-num $nfqueue --queue-bypass"
			  . " -m comment --comment \"RBL,${rule},$farmname\"";

			# thre rule already exists
			return 0 if ( &getIPDSRuleExists( $cmd ) );

			$error = &iptSystem( $cmd );
		}
	}

	return $error;
}

functions:

# Specific functions for the module

=begin nd
Function: setRBLCreateNfqueue

	Looking for a not used nf queue and assigned it to a RBL rule

Parameters:
	String - Rule name 
	
Returns:
	integer - netfilter queue number
	
=cut

sub setRBLCreateNfqueue
{
	my $rule = shift;

	my $queue_num = 0;
	my @rules     = &getRBLRuleList();
	use Config::Tiny;
	my $fileHandle = Config::Tiny->read( $rblConfigFile );
	my @queue_list;

	foreach my $rule ( @rules )
	{
		if ( $fileHandle->{ $rule }->{ 'nf_queue_number' } ne "" )
		{
			push @queue_list, $fileHandle->{ $rule }->{ 'nf_queue_number' };
		}
	}

	# Increase $queue_num until to find one is not used
	while ( $queue_num < 65000 )
	{
		last if ( !grep ( /^$queue_num$/, @queue_list ) );
		$queue_num = $queue_num + 1;
	}

	# Save this queue
	&setRBLObjectRuleParam( $rule, 'nf_queue_number', $queue_num );

	return $queue_num;
}

=begin nd
Function: setRBLRemoveNfqueue

	Remove the associated netfilter queue for a rule

Parameters:
	String - Rule name 
	
Returns:
	none - .
	
=cut

sub setRBLRemoveNfqueue
{
	my $rule = shift;
	&setRBLObjectRuleParam( $rule, 'nf_queue_number', '' );
}

=begin nd
Function: runRBLStart

	Run packetbl binary

Parameters:
	String - Rule name 
	
Returns:
	integer - 0 on success or other value on failure
	
=cut

sub runRBLStartPacketbl
{
	my $rule = shift;

	# Get packetbl bin
	my $packetbl = &getGlobalConfiguration( "packetbl_bin" );

	# Look for a not used nf queue and assign it to this rule
	&setRBLCreateNfqueue( $rule );

	# Create packetbl config file
	&setRBLPacketblConfig( $rule );

	# Get packetbl configuration file
	my $configfile = &getRBLPacketblConfig( $rule );

	# Run packetbl
	my $error = system ( "bash", "-c",
						 ". /etc/profile_packetbl && $packetbl -f $configfile" );
	&zenlog( "Error, starting packetbl" ) if ( $error );
	return $error;
}

=begin nd
Function: runRBLStopPacketbl

	Stop packetbl bin

Parameters:
	String - Rule name 
	
Returns:

FIXME:
	if packetbl is stopped without delete its pid file, the rule will appear in UP status
	
=cut

sub runRBLStopPacketbl
{
	my $rule = shift;

	# Remove associated nfqueue from configfile
	&setRBLRemoveNfqueue( $rule );

	# exec kill
	my $pid = &getRBLPacketblPid( $rule );

	return &logAndRun( "kill $pid" );
}

=begin nd
Function: runRBLRestartPacketbl

	Restart packetbl bin. It is useful to reload configuration

Parameters:
	String - Rule name 
	
Returns:
	integer - 0 on success or other value on failure

=cut

sub runRBLRestartPacketbl
{
	my $rule = shift;
	&runRBLStopPacketbl( $rule );
	my $error = &runRBLStartPacketbl( $rule );
	return $error;
}

=begin nd
Function: getRBLPacketblPid

	Get the packetbl pid file of a RBL rule

Parameters:
	String - Rule name 
	
Returns:
	Integer - Return the packetbl pid

=cut

sub getRBLPacketblPid
{
	my $rule = shift;
	my $pid;

	my $ps      = &getGlobalConfiguration( 'ps' );
	my @process = `$ps -x`;
	if ( @process = grep ( /\/packetbl_$rule\.conf/, @process ) )
	{
		$pid = $1 if ( $process[0] =~ /^\s*(\d+)\s/ );
	}
	return $pid;
}

=begin nd
Function: getRBLPacketblConfig

	Get the configuration file of a RBL rule

Parameters:
	String - Rule name 
	
Returns:
	String - Return a chain with packetbl configuration file of a RBL rule

=cut

sub getRBLPacketblConfig
{
	my $rule = shift;
	return "$rblPath/packetbl_$rule.conf";
}

=begin nd
Function: setRBLPacketblConfig

	before than exec packetbl, configure a new config file with rule configuration and overwrite the existing one

Parameters:
	String - Rule name 
	
Returns:
	Integer - 0 on success or other value on failure

=cut

sub setRBLPacketblConfig
{
	my $rule   = shift;
	my $params = &getRBLObjectRule( $rule );
	my $error  = 0;

	# filling config file
	my $fileContent = "
<host>";

	# not review local traffic
	if ( $params->{ 'local_traffic' } eq 'no' )
	{
		$fileContent .= "
	whitelist	192.168.0.0/16
	whitelist	169.254.0.0/16
	whitelist	172.16.0.0/12
	whitelist	10.0.0.0/8";
	}

	foreach my $domain ( @{ $params->{ 'domains' } } )
	{
		$fileContent .= "\n\tblacklistbl\t$domain";
	}

	$fileContent .= "	
</host>
FallthroughAccept	yes
AllowNonPort25		yes
AllowNonSyn			no
DryRun			$params->{'only_logging'}
CacheSize	$params->{'cache_size'}
CacheTTL		$params->{'cache_time'}
LogFacility	daemon
AlternativeDomain		rbl.zevenet.com
AlternativeResolveFile	usr/local/zevenet/config/ipds/rbl/zevenet_nameservers.conf
Queueno		$params->{'nf_queue_number'}
Queuesize	$params->{'queue_size'}
Threadmax	$params->{'threadmax'}
LogLevel	$params->{'log_level'}
";

	# save file
	my $fh;
	my $filename = &getRBLPacketblConfig( $rule );
	$fh = &openlock( '>', $filename );
	unless ( $fh )
	{
		&zenlog( "Could not open file $filename: $!" );
		return -1;
	}
	print $fh $fileContent;
	&closelock( $fh );

	return $error;
}

domains:

=begin nd
Function: getRBLUserDomains

	Get a list with the domains added by the user

Parameters:
	
Returns:
	Array ref - Domain list

=cut

sub getRBLUserDomains
{
	my @domains;

	tie my @list, 'Tie::File', $userDomainsFile;
	@domains = @list;
	untie @list;

	return \@domains;
}

=begin nd
Function: getRBLPreloadedDomains

	Get a list with the preloaded domains

Parameters:
	
Returns:
	Array ref - Domain list

=cut

sub getRBLPreloadedDomains
{
	my @domains;

	tie my @list, 'Tie::File', $preloadedDomainsFile;
	@domains = @list;
	untie @list;

	return \@domains;
}

=begin nd
Function: getRBLDomains

	Get a list with all existing domains.

Parameters:
	
Returns:
	Array ref - Domain list

=cut

sub getRBLDomains
{
	my @domains;

	push @domains, @{ &getRBLPreloadedDomains };
	push @domains, @{ &getRBLUserDomains };

	return \@domains;
}

=begin nd
Function: addRBLDomains

	Get a list with the preloaded domains. Only it is possible to add a new domain of the user domain list

Parameters:
	Domain - String with a domain
	
Returns:
	none - .

=cut

sub addRBLDomains
{
	my $new_domain = shift;

	tie my @domains, 'Tie::File', $userDomainsFile;
	push @domains, $new_domain;
	untie @domains;
}

=begin nd
Function: setRBLDomains

	Modify a domain of the domain list. Only it is possible to replace a domain of the user domain list

Parameters:
	Domain - Domain to remove from the list
	Domain_new - New domain for the list
	
Returns:
	none - .

=cut

sub setRBLDomains
{
	my $domain     = shift;
	my $new_domain = shift;

	&delRBLDomains( $domain );
	&addRBLDomains( $new_domain );
}

=begin nd
Function: delRBLDomains

	Modify a domain of the domain list. Only it is possible to remove a domain of the user domain list

Parameters:
	Domain - Domain to remove from the list
	Domain_new - New domain for the list
	
Returns:
	Integer - Error code, 0 on success or -1 on failure.

=cut

sub delRBLDomains
{
	my $domain = shift;
	my $error  = -1;
	my $it     = 0;

	tie my @domains, 'Tie::File', $userDomainsFile;
	foreach my $item ( @domains )
	{
		if ( $item =~ /^$domain$/ )
		{
			splice @domains, $it, 1;
			$error = 0;
			last;
		}
		$it += 1;
	}
	untie @domains;

	return $error;
}

zapi_format:

=begin nd
Function: getRBLZapiRule

	Create zapi output formats of a rbl rule for ZAPI

Parameters:
	Rule - rule name
	
Returns:
	Hash ref - Hash with the rbl parameters
	
	{
		"cache_size" : 8192,
		"cache_time" : 3600,
		"domains" : [
			"ssh.rbl.zevenet.com",
			"sip.rbl.zevenet.com"
		],
		"farms" : [
			"cookiefarm"
		],
		"local_traffic" : "false",
		"log_level" : 4,
		"name" : "protection_ssh",
		"only_logging" : "false",
		"queue_size" : 64538,
		"status" : "down",
		"threadmax" : 700
	}

=cut

sub getRBLZapiRule
{
	my $rule = shift;

	use Config::Tiny;
	my $fileHandle = Config::Tiny->read( $rblConfigFile );

	my $output = $fileHandle->{ $rule };

	my @domains = split ( ' ', $fileHandle->{ $rule }->{ 'domains' } );
	my @farms   = split ( ' ', $fileHandle->{ $rule }->{ 'farms' } );

	$output->{ 'domains' } = \@domains;
	$output->{ 'farms' }   = \@farms;

	$output->{ 'name' }   = $rule;
	$output->{ 'status' } = &getRBLStatusRule( $rule );

	if ( $output->{ 'local_traffic' } eq 'yes' )
	{
		$output->{ 'local_traffic' } = "true";
	}
	else
	{
		$output->{ 'local_traffic' } = "false";
	}
	if ( $output->{ 'only_logging' } eq 'yes' )
	{
		$output->{ 'only_logging' } = "true";
	}
	else
	{
		$output->{ 'only_logging' } = "false";
	}

	foreach my $key ( keys %{ $output } )
	{
		$output->{ $key } += 0 if ( $output->{ $key } =~ /^\d+$/ );
	}

	delete $output->{ 'nf_queue_number' };

	return $output;
}

=begin nd
Function: getRBLZapi

	Create a array with zapi output formats of all rbl rules

Parameters:
	
Returns:
	Array ref - 
	
	{
		"cache_size" : 8192,
		"cache_time" : 3600,
		"domains" : [
			"ssh.rbl.zevenet.com",
			"sip.rbl.zevenet.com"
		],
		"farms" : [
			"cookiefarm"
		],
		"local_traffic" : "false",
		"log_level" : 4,
		"name" : "protection_ssh",
		"only_logging" : "false",
		"queue_size" : 64538,
		"status" : "down",
		"threadmax" : 700
	}

=cut

sub getRBLZapi
{
	my @all_rules;

	foreach my $rule ( &getRBLRuleList )
	{
		my $output = &getRBLZapiRule( $rule );

		push @all_rules, $output;
	}

	return \@all_rules;
}

1;
