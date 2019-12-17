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

use Zevenet::API31::HTTP;

include 'Zevenet::IPDS::DoS::Core';

# GET /ipds/dos/rules
sub get_dos_rules
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $desc = "List the possible DoS rules";

	my $body = {
		description => $desc,
		params      => {
			"farm" => [
					   {
						  'rule'        => 'limitsec',
						  'description' => 'Connection limit per second.'
					   },
					   {
						  'rule'        => 'limitconns',
						  'description' => 'Total connections limit per source IP.'
					   },
					   { 'rule' => 'bogustcpflags', 'description' => 'Check bogus TCP flags.' },
					   {
						  'rule'        => 'limitrst',
						  'description' => 'Limit RST request per second.'
					   },
			],
			"system" => [
						 { 'rule' => 'sshbruteforce', 'description' => 'SSH brute force.' },
						 { 'rule' => 'dropicmp',      'description' => 'Drop icmp packets' },
			]
		}
	};

	return &httpResponse( { code => 200, body => $body } );
}

#GET /ipds/dos
sub get_dos
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $confFile = &getGlobalConfiguration( 'dosConf' );
	my $desc     = "List the DoS rules";

	my $fileHandle = Config::Tiny->read( $confFile );
	my %rules      = %{ $fileHandle };
	my @output;

	foreach my $rule ( sort keys %rules )
	{
		my $aux = &getDOSZapiRule( $rule );
		push @output, $aux;
	}

	my $body = { description => $desc, params => \@output };
	return &httpResponse( { code => 200, body => $body } );
}

#  POST /ipds/dos
sub create_dos_rule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	include 'Zevenet::IPDS::DoS::Config';

	my $desc     = "Create the DoS rule '$json_obj->{ 'rule' }'";
	my $confFile = &getGlobalConfiguration( 'dosConf' );

	my @requiredParams = ( "name", "rule" );
	my $param_msg = &getValidReqParams( $json_obj, \@requiredParams );

	if ( $param_msg )
	{
		return &httpErrorResponse( code => 400, desc => $desc, msg => $param_msg );
	}

	if ( &getDOSExists( $json_obj->{ 'name' } ) )
	{
		my $msg = "$json_obj->{ 'name' } already exists.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( $json_obj->{ 'name' } eq 'rules' )
	{
		my $msg = 'The name is not valid, it is a reserved word.';
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( !&getValidFormat( 'dos_name', $json_obj->{ 'name' } ) )
	{
		my $msg = "rule name hasn't a correct format.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( !&getValidFormat( "dos_rule_farm", $json_obj->{ 'rule' } ) )
	{
		my $msg = "ID rule isn't correct.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $error = &createDOSRule( $json_obj->{ 'name' }, $json_obj->{ 'rule' } );
	if ( $error )
	{
		my $msg = "There was a error enabling DoS in $json_obj->{ 'name' }.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $output = &getDOSZapiRule( $json_obj->{ 'name' } );
	my $body = { description => $desc, params => $output };

	return &httpResponse( { code => 200, body => $body } );
}

#GET /ipds/dos/RULE
sub get_dos_rule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $name = shift;

	my $desc    = "Get the DoS rule $name";
	my $refRule = &getDOSZapiRule( $name );

	if ( ref ( $refRule ) ne 'HASH' )
	{
		my $msg = "$name doesn't exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $body = { description => $desc, params => $refRule };
	return &httpResponse( { code => 200, body => $body } );
}

#PUT /ipds/dos/<rule>
sub set_dos_rule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $name     = shift;

	include 'Zevenet::IPDS::DoS::Config';
	include 'Zevenet::IPDS::DoS::Actions';

	my $desc = "Modify the DoS rule $name";
	my @requiredParams;

	if ( !&getDOSExists( $name ) )
	{
		my $msg = "$name not found";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# Get allowed params for a determinated rule
	my $rule = &getDOSParam( $name, 'rule' );
	my %hashRuleConf = %{ &getDOSInitialParams( $rule ) };

	# delete 'type' key
	delete $hashRuleConf{ 'type' };

	# delete 'key' key
	delete $hashRuleConf{ 'rule' };

	# delete 'farms' key
	if ( exists $hashRuleConf{ 'farms' } )
	{
		delete $hashRuleConf{ 'farms' };
	}

	# not allow change ssh port. To change it call PUT /system/ssh
	if ( $name eq 'ssh_brute_force' )
	{
		delete $hashRuleConf{ 'port' };
	}

	@requiredParams = keys %hashRuleConf;
	my $param_msg = &getValidOptParams( $json_obj, \@requiredParams );

	if ( $param_msg )
	{
		return &httpErrorResponse( code => 404, desc => $desc, msg => $param_msg );
	}

	# check input format
	foreach my $param ( keys %{ $json_obj } )
	{
		if ( !&getValidFormat( "dos_$param", $json_obj->{ $param } ) )
		{
			my $msg = "Error, $param format is wrong.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	my $status = &getDOSParam( $name, 'status' );
	&runDOSStopByRule( $name ) if ( $status eq "up" );

	foreach my $param ( keys %{ $json_obj } )
	{
		&setDOSParam( $name, $param, $json_obj->{ $param } );
	}

	&runDOSStartByRule( $name ) if ( $status eq "up" );
	my $refRule = &getDOSZapiRule( $name );

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_dos', 'restart', $name );

	my $body = { description => $desc, success => "true", params => $refRule };
	return &httpResponse( { code => 200, body => $body } );
}

# DELETE /ipds/dos/RULE
sub del_dos_rule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $name = shift;

	include 'Zevenet::IPDS::DoS::Config';

	my $desc = "Delete the DoS rule $name";

	if ( !&getDOSExists( $name ) )
	{
		my $msg = "$name not found.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}
	elsif ( &getDOSParam( $name, 'type' ) eq 'system' )
	{
		my $msg =
		  "Error, system rules not is possible to delete it, try to disable it.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
	elsif ( @{ &getDOSParam( $name, 'farms' ) } )
	{
		my $msg = "Error, disable this rule from all farms before than delete it.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	&deleteDOSRule( $name );

	my $msg = "Deleted $name successfully.";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $msg,
	};

	return &httpResponse( { code => 200, body => $body } );
}

#  POST /farms/<farmname>/ipds/dos
sub add_dos_to_farm
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmName = shift;

	include 'Zevenet::IPDS::DoS::Runtime';

	my $name     = $json_obj->{ 'name' };
	my $confFile = &getGlobalConfiguration( 'dosConf' );
	my $desc     = "Apply the DoS rule $name to the farm $farmName";

	require Zevenet::Farm::Core;
	require Zevenet::Farm::Base;

	if ( !&getFarmExists( $farmName ) )
	{
		my $msg = "$farmName doesn't exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}
	elsif ( !&getDOSExists( $name ) )
	{
		my $msg = "$name not found.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}
	elsif ( &getDOSParam( $name, 'type' ) eq 'system' )
	{
		my $msg = "System rules not is possible apply to farm.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $fileHandle = Config::Tiny->read( $confFile );
	if ( $fileHandle->{ $name }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
	{
		my $msg = "This rule already is enabled in $farmName.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# A farm can not simultaneasly have a "limitsec" and "limitrst" rule
	# or two dos rules with the same type
	include 'Zevenet::IPDS::Core';

	my $farm_rules = &getIPDSfarmsRules( $farmName );
	foreach my $rule_dos ( @{ $farm_rules->{ 'dos' } } )
	{
		$rule_dos = $rule_dos->{ 'name' };

		if ( $fileHandle->{ $rule_dos }->{ 'farms' } =~ /(^| )$farmName($| )/ )
		{
			if (
				 $fileHandle->{ $rule_dos }->{ 'rule' } eq $fileHandle->{ $name }->{ 'rule' } )
			{
				my $msg =
				  "Error, a DoS rule $fileHandle->{$name}->{'rule'} already is applied to the farm.";
				return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}
		}
	}

	&setDOSApplyRule( $farmName, $name );

	my $output = &getDOSZapiRule( $name );
	if ( !grep ( /^$farmName$/, @{ $output->{ 'farms' } } ) )
	{
		my $msg = "Error, enabling $name rule.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( &getFarmStatus( $farmName ) eq 'up' )
	{
		include 'Zevenet::Cluster';
		&runZClusterRemoteManager( 'ipds_dos', 'start', $name, $farmName );
	}

	my $msg = "DoS rule $name was applied successfully to the farm $farmName.";
	my $body = { description => $desc, success => 'true', message => $msg };

	return &httpResponse( { code => 200, body => $body } );
}

# DELETE /farms/<farmname>/ipds/dos/<ruleName>
sub del_dos_from_farm
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmName = shift;
	my $name     = shift;

	my $desc     = "Unset the DoS rule $name from the farm $farmName";
	my $confFile = &getGlobalConfiguration( 'dosConf' );

	require Zevenet::Farm::Core;
	require Zevenet::Farm::Base;

	if ( !&getFarmExists( $farmName ) )
	{
		my $msg = "$farmName doesn't exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( !&getDOSExists( $name ) )
	{
		my $msg = "$name not found.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( &getDOSParam( $name, 'type' ) eq 'system' )
	{
		my $msg = "System rules not is possible delete from a farm.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $fileHandle = Config::Tiny->read( $confFile );
	if ( $fileHandle->{ $name }->{ 'farms' } !~ /( |^)$farmName( |$)/ )
	{
		my $msg = "This rule no is enabled in $farmName.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	include 'Zevenet::IPDS::DoS::Runtime';
	include 'Zevenet::IPDS::Core';

	&setDOSUnsetRule( $name, $farmName );

	# Call to remove service if possible
	&delIPDSFarmService( $farmName );

	# check output
	my $output = &getDOSZapiRule( $name );

	if ( grep ( /^$farmName$/, @{ $output->{ 'farms' } } ) )
	{
		my $msg = "Error, removing $name rule from $farmName.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( &getFarmStatus( $farmName ) eq 'up' )
	{
		include 'Zevenet::Cluster';
		&runZClusterRemoteManager( 'ipds_dos', 'stop', $name, $farmName );
	}

	my $msg = "DoS rule $name was removed successfully from the farm $farmName.";
	my $body = { description => $desc, success => "true", message => $msg };

	return &httpResponse( { code => 200, body => $body } );
}

# POST /ipds/dos/DOS/actions
sub actions_dos
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $rule     = shift;

	include 'Zevenet::IPDS::DoS::Actions';
	include 'Zevenet::IPDS::DoS::Config';

	my $desc = "Apply a action to the DoS rule $rule";
	my $msg  = "Error, applying the action to the DoS rule.";

	if ( !&getDOSExists( $rule ) )
	{
		my $msg = "$rule doesn't exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( $json_obj->{ action } eq 'start' )
	{
		if ( &getDOSParam( $rule, 'type' ) eq 'farm' )
		{
			if ( !@{ &getDOSParam( $rule, 'farms' ) } )
			{
				$msg = "The rule has to be applied to some farm to start it.";
				return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}
		}

		&setDOSParam( $rule, 'status', 'up' );

		my $error = &runDOSStartByRule( $rule );
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg ) if $error;
	}
	elsif ( $json_obj->{ action } eq 'stop' )
	{
		&setDOSParam( $rule, 'status', 'down' );
		my $error = &runDOSStopByRule( $rule );
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg ) if $error;
	}
	elsif ( $json_obj->{ action } eq 'restart' )
	{
		my $error = &runDOSRestartByRule( $rule );
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg ) if $error;
		&setDOSParam( $rule, 'status', 'up' );
	}
	else
	{
		my $msg = "The action has not a valid value";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_dos', $json_obj->{ action }, $rule );

	my $body = {
				 description => $desc,
				 success     => "true",
				 params      => $json_obj->{ action }
	};

	return &httpResponse( { code => 200, body => $body } );
}

1;
