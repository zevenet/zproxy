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

use Zevenet::IPDS::DoS;

# GET /ipds/dos/rules
sub get_dos_rules
{
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

	&httpResponse( { code => 200, body => $body } );
}

#GET /ipds/dos
sub get_dos
{
	my $confFile    = &getGlobalConfiguration( 'dosConf' );
	my $desc = "List the DoS rules";

	my $fileHandle = Config::Tiny->read( $confFile );
	my %rules      = %{ $fileHandle };
	my @output;

	foreach my $rule ( keys %rules )
	{
		my $aux = &getDOSZapiRule( $rule );
		push @output, $aux;
	}

	my $body = { description => $desc, params => \@output };
	&httpResponse( { code => 200, body => $body } );
}

#  POST /ipds/dos
sub create_dos_rule
{
	my $json_obj = shift;

	require Zevenet::IPDS::DoS::Config;

	my $desc     = "Create the DoS rule '$json_obj->{ 'rule' }'";
	my $confFile = &getGlobalConfiguration( 'dosConf' );

	my @requiredParams = ( "name", "rule" );
	my $param_msg = &getValidReqParams( $json_obj, \@requiredParams );

	if ( $param_msg )
	{
		&httpErrorResponse( code => 400, desc => $desc, msg => $param_msg );
	}

	if ( &getDOSExists( $json_obj->{ 'name' } ) )
	{
		my $msg = "$json_obj->{ 'name' } already exists.";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( $json_obj->{ 'name' } eq 'rules' )
	{
		my $msg = 'The name is not valid, it is a reserved word.';
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( !&getValidFormat( 'dos_name', $json_obj->{ 'name' } ) )
	{
		my $msg = "rule name hasn't a correct format.";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( !&getValidFormat( "dos_rule_farm", $json_obj->{ 'rule' } ) )
	{
		my $msg = "ID rule isn't correct.";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $error = &createDOSRule( $json_obj->{ 'name' }, $json_obj->{ 'rule' } );
	if ( $error )
	{
		my $msg = "There was a error enabling DoS in $json_obj->{ 'name' }.";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $output = &getDOSZapiRule( $json_obj->{ 'name' } );
	my $body = { description => $desc, params => $output };

	&httpResponse( { code => 200, body => $body } );
}

#GET /ipds/dos/RULE
sub get_dos_rule
{
	my $name = shift;

	my $desc    = "Get the DoS rule $name";
	my $refRule = &getDOSZapiRule( $name );

	if ( ref ( $refRule ) ne 'HASH' )
	{
		my $msg = "$name doesn't exist.";
		&httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $body = { description => $desc, params => $refRule };
	&httpResponse( { code => 200, body => $body } );
}

#PUT /ipds/dos/<rule>
sub set_dos_rule
{
	my $json_obj = shift;
	my $name     = shift;

	require Zevenet::IPDS::DoS::Config;
	require Zevenet::IPDS::DoS::Actions;

	my $desc = "Modify the DoS rule $name";
	my @requiredParams;

	if ( !&getDOSExists( $name ) )
	{
		my $msg = "$name not found";
		&httpErrorResponse( code => 404, desc => $desc, msg => $msg );
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
		&httpErrorResponse( code => 404, desc => $desc, msg => $param_msg );
	}

	# check input format
	foreach my $param ( keys %{ $json_obj } )
	{
		if ( !&getValidFormat( "dos_$param", $json_obj->{ $param } ) )
		{
			my $msg = "Error, $param format is wrong.";
			&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	my $status = &getDOSStatusRule( $name );
	&runDOSStopByRule( $name ) if ( $status eq "up" );

	foreach my $param ( keys %{ $json_obj } )
	{
		&setDOSParam( $name, $param, $json_obj->{ $param } );
	}

	&runDOSStartByRule( $name ) if ( $status eq "up" );
	my $refRule = &getDOSZapiRule( $name );

	require Zevenet::Cluster;
	&runZClusterRemoteManager( 'ipds_dos', 'restart', $name );

	my $body = { description => $desc, success => "true", params => $refRule };
	&httpResponse( { code => 200, body => $body } );
}

# DELETE /ipds/dos/RULE
sub del_dos_rule
{
	my $name = shift;

	require Zevenet::IPDS::DoS::Config;

	my $desc = "Delete the DoS rule $name";

	if ( !&getDOSExists( $name ) )
	{
		my $msg = "$name not found.";
		&httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}
	elsif ( &getDOSParam( $name, 'type' ) eq 'system' )
	{
		my $msg =
		  "Error, system rules not is possible to delete it, try to disable it.";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
	elsif ( @{ &getDOSParam( $name, 'farms' ) } )
	{
		my $msg = "Error, disable this rule from all farms before than delete it.";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	&deleteDOSRule( $name );

	my $msg = "Deleted $name successful.";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $msg,
	};

	&httpResponse( { code => 200, body => $body } );
}

#  GET /farms/<farmname>/ipds/dos
sub get_dos_farm
{
	my $farmName = shift;
	my $confFile = &getGlobalConfiguration( 'dosConf' );
	my @output;
	my $desc = "Get status DoS $farmName.";

	if ( -e $confFile )
	{
		my $fileHandle = Config::Tiny->read( $confFile );

		foreach my $ruleName ( keys %{ $fileHandle } )
		{
			if ( $fileHandle->{ $ruleName }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
			{
				push @output, $ruleName;
			}
		}
	}

	my $body = { description => $desc, params => \@output };

	&httpResponse( { code => 200, body => $body } );
}

#  POST /farms/<farmname>/ipds/dos
sub add_dos_to_farm
{
	my $json_obj = shift;
	my $farmName = shift;

	require Zevenet::IPDS::DoS::Runtime;

	my $name     = $json_obj->{ 'name' };
	my $confFile = &getGlobalConfiguration( 'dosConf' );
	my $desc     = "Apply the DoS rule $name to the farm $farmName";

	if ( &getFarmFile( $farmName ) eq '-1' )
	{
		my $msg = "$farmName doesn't exist.";
		&httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}
	elsif ( !&getDOSExists( $name ) )
	{
		my $msg = "$name not found.";
		&httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}
	elsif ( &getDOSParam( $name, 'type' ) eq 'system' )
	{
		my $msg = "System rules not is possible apply to farm.";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $fileHandle = Config::Tiny->read( $confFile );
	if ( $fileHandle->{ $name }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
	{
		my $msg = "This rule already is enabled in $farmName.";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	&setDOSApplyRule( $name, $farmName );

	my $output = &getDOSZapiRule( $name );
	if ( grep ( /^$farmName$/, @{ $output->{ 'farms' } } ) )
	{
		my $msg = "Error, enabling $name rule.";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( &getFarmStatus( $farmName ) eq 'up' )
	{
		require Zevenet::Cluster;
		&runZClusterRemoteManager( 'ipds_dos', 'start', $name, $farmName );
	}

	my $msg = "DoS rule $name was applied successful to the farm $farmName.";
	my $body = { description => $desc, success => 'true', message => $msg };

	&httpResponse( { code => 200, body => $body } );
}

# DELETE /farms/<farmname>/ipds/dos/<ruleName>
sub del_dos_from_farm
{
	my $farmName = shift;
	my $name     = shift;

	my $desc     = "Unset the DoS rule $name from the farm $farmName";
	my $confFile = &getGlobalConfiguration( 'dosConf' );

	if ( &getFarmFile( $farmName ) eq "-1" )
	{
		my $msg = "$farmName doesn't exist.";
		&httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( !&getDOSExists( $name ) )
	{
		my $msg = "$name not found.";
		&httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( &getDOSParam( $name, 'type' ) eq 'system' )
	{
		my $msg = "System rules not is possible delete from a farm.";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $fileHandle = Config::Tiny->read( $confFile );
	if ( $fileHandle->{ $name }->{ 'farms' } !~ /( |^)$farmName( |$)/ )
	{
		my $msg = "This rule no is enabled in $farmName.";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	require Zevenet::IPDS::DoS::Runtime;
	&setDOSUnsetRule( $name, $farmName );

	# check output
	my $output = &getDOSZapiRule( $name );
	if ( !grep ( /^$farmName$/, @{ $output->{ 'farms' } } ) )
	{
		my $msg = "Error, removing $name rule from $farmName.";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( &getFarmStatus( $farmName ) eq 'up' )
	{
		require Zevenet::Cluster;
		&runZClusterRemoteManager( 'ipds_dos', 'stop', $name, $farmName );
	}

	my $msg = "DoS rule $name was removed successful from the farm $farmName.";
	my $body = { description => $desc, success => "true", message => $msg };

	&httpResponse( { code => 200, body => $body } );
}

# POST /ipds/dos/DOS/actions
sub actions_dos
{
	my $json_obj = shift;
	my $rule     = shift;

	require Zevenet::IPDS::DoS::Actions;

	my $desc     = "Apply a action to the DoS rule $rule";
	my $msg = "Error, applying the action to the DoS rule.";

	if ( !&getDOSExists( $rule ) )
	{
		my $msg = "$rule doesn't exist.";
		&httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( $json_obj->{ action } eq 'start' )
	{
		my $error = &runDOSStartByRule( $rule );
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg ) if $error;
	}
	elsif ( $json_obj->{ action } eq 'stop' )
	{
		my $error = &runDOSStopByRule( $rule );
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg ) if $error;
	}
	elsif ( $json_obj->{ action } eq 'restart' )
	{
		my $error = &runDOSRestartByRule( $rule );
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg ) if $error;
	}
	else
	{
		my $msg = "The action has not a valid value";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	require Zevenet::Cluster;
	&runZClusterRemoteManager( 'ipds_dos', $json_obj->{ action }, $rule );

	my $body = {
				 description => $desc,
				 success     => "true",
				 params      => $json_obj->{ action }
	};

	&httpResponse( { code => 200, body => $body } );
}

1;
