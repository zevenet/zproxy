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
	my $description = "List the possible DoS rules";

	my $body = {
		description => $description,
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
	my $description = "List the DoS rules";

	my $fileHandle = Config::Tiny->read( $confFile );
	my %rules      = %{ $fileHandle };
	my @output;

	foreach my $rule ( keys %rules )
	{
		my $aux = &getDOSZapiRule( $rule );
		push @output, $aux;
	}

	my $body = { description => $description, params => \@output };
	&httpResponse( { code => 200, body => $body } );
}

#  POST /ipds/dos
sub create_dos_rule
{
	my $json_obj       = shift;
	my $rule           = $json_obj->{ 'rule' };
	my $description    = "Create the DoS rule $rule";
	my @requiredParams = ( "name", "rule" );
	my $confFile       = &getGlobalConfiguration( 'dosConf' );

	my $errormsg = &getValidReqParams( $json_obj, \@requiredParams );
	if ( !$errormsg )
	{
		if ( &getDOSExists( $json_obj->{ 'name' } ) )
		{
			$errormsg = "$json_obj->{ 'name' } already exists.";
		}
		elsif ( $json_obj->{ 'name' } eq 'rules' )
		{
			$errormsg = 'The name is not valid, it is a reserved word.';
		}
		elsif ( !&getValidFormat( 'dos_name', $json_obj->{ 'name' } ) )
		{
			$errormsg = "rule name hasn't a correct format.";
		}
		elsif ( !&getValidFormat( "dos_rule_farm", $json_obj->{ 'rule' } ) )
		{
			$errormsg = "ID rule isn't correct.";
		}
		else
		{
			require Zevenet::IPDS::DoS::Config;
			$errormsg = &createDOSRule( $json_obj->{ 'name' }, $rule );
			if ( $errormsg )
			{
				$errormsg = "There was a error enabling DoS in $json_obj->{ 'name' }.";
			}
			else
			{
				my $output = &getDOSZapiRule( $json_obj->{ 'name' } );
				&httpResponse(
							   {
								 code => 200,
								 body => { description => $description, params => $output }
							   }
				);
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg, };
	&httpResponse( { code => 400, body => $body } );
}

#GET /ipds/dos/RULE
sub get_dos_rule
{
	my $name        = shift;
	my $description = "Get the DoS rule $name";
	my $refRule     = &getDOSZapiRule( $name );
	my $output;

	if ( ref ( $refRule ) eq 'HASH' )
	{
		$output = &getDOSZapiRule( $name );

		# successful
		my $body = { description => $description, params => $refRule, };
		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		$output = "$name doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $output
		};
		&httpResponse( { code => 404, body => $body } );
	}
}

#PUT /ipds/dos/<rule>
sub set_dos_rule
{
	my $json_obj    = shift;
	my $name        = shift;
	my $description = "Modify the DoS rule $name";
	my @requiredParams;
	my $errormsg;

	if ( !&getDOSExists( $name ) )
	{
		$errormsg = "$name not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	else
	{
		require Zevenet::IPDS::DoS::Config;

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
		$errormsg = &getValidOptParams( $json_obj, \@requiredParams );
		if ( !$errormsg )
		{
			# check input format
			foreach my $param ( keys %{ $json_obj } )
			{
				if ( !&getValidFormat( "dos_$param", $json_obj->{ $param } ) )
				{
					$errormsg = "Error, $param format is wrong.";
					last;
				}
			}

			# output
			if ( !$errormsg )
			{
				require Zevenet::IPDS::DoS::Actions;
				my $status = &getDOSStatusRule( $name );
				&runDOSStopByRule( $name ) if ( $status eq "up" );

				foreach my $param ( keys %{ $json_obj } )
				{
					&setDOSParam( $name, $param, $json_obj->{ $param } );
				}
				&runDOSStartByRule( $name ) if ( $status eq "up" );

				if ( !$errormsg )
				{
					my $refRule = &getDOSZapiRule( $name );

					require Zevenet::Cluster;
					&runZClusterRemoteManager( 'ipds_dos', 'restart', $name );

					&httpResponse(
						{
						   code => 200,
						   body => { description => $description, success => "true", params => $refRule }
						}
					);
				}
			}
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg
	};
	&httpResponse( { code => 400, body => $body } );
}

# DELETE /ipds/dos/RULE
sub del_dos_rule
{
	#~ my $json_obj = shift;
	my $name = shift;
	my $errormsg;
	my $description = "Delete the DoS rule $name";

	if ( !&getDOSExists( $name ) )
	{
		$errormsg = "$name not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( &getDOSParam( $name, 'type' ) eq 'system' )
	{
		$errormsg =
		  "Error, system rules not is possible to delete it, try to disable it.";
	}
	elsif ( @{ &getDOSParam( $name, 'farms' ) } )
	{
		$errormsg = "Error, disable this rule from all farms before than delete it.";
	}
	else
	{
		require Zevenet::IPDS::DoS::Config;
		&deleteDOSRule( $name );
		$errormsg = "Deleted $name successful.";
		my $body = {
					 description => $description,
					 success     => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 200, body => $body } );
	}

	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg
	};
	&httpResponse( { code => 400, body => $body } );
}

#  GET /farms/<farmname>/ipds/dos
sub get_dos_farm
{
	my $farmName = shift;
	my $confFile = &getGlobalConfiguration( 'dosConf' );
	my @output;
	my $description = "Get status DoS $farmName.";

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

	my $body = { description => $description, params => \@output };
	&httpResponse( { code => 200, body => $body } );
}

#  POST /farms/<farmname>/ipds/dos
sub add_dos_to_farm
{
	my $json_obj    = shift;
	my $farmName    = shift;
	my $name        = $json_obj->{ 'name' };
	my $description = "Apply the DoS rule $name to the farm $farmName";
	my $errormsg;

	my $confFile = &getGlobalConfiguration( 'dosConf' );
	my $output   = "down";

	if ( &getFarmFile( $farmName ) eq '-1' )
	{
		$errormsg = "$farmName doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( !&getDOSExists( $name ) )
	{
		$errormsg = "$name not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( &getDOSParam( $name, 'type' ) eq 'system' )
	{
		$errormsg = "System rules not is possible apply to farm.";
	}
	else
	{
		my $fileHandle = Config::Tiny->read( $confFile );
		if ( $fileHandle->{ $name }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
		{
			$errormsg = "This rule already is enabled in $farmName.";
		}
		else
		{
			require Zevenet::IPDS::DoS::Runtime;
			&setDOSApplyRule( $name, $farmName );

			my $confFile = &getGlobalConfiguration( 'dosConf' );

			# check output
			my $output = &getDOSZapiRule( $name );
			if ( grep ( /^$farmName$/, @{ $output->{ 'farms' } } ) )
			{
				$errormsg = "DoS rule $name was applied successful to the farm $farmName.";

				if ( &getFarmStatus( $farmName ) eq 'up' )
				{
					require Zevenet::Cluster;
					&runZClusterRemoteManager( 'ipds_dos', 'start', $name, $farmName );
				}

				&httpResponse(
					{
					   code => 200,
					   body => { description => $description, success => 'true', message => $errormsg }
					}
				);
			}
			else
			{
				$errormsg = "Error, enabling $name rule.";
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg, };
	&httpResponse( { code => 400, body => $body } );
}

# DELETE /farms/<farmname>/ipds/dos/<ruleName>
sub del_dos_from_farm
{
	my $farmName    = shift;
	my $name        = shift;
	my $description = "Unset the DoS rule $name from the farm $farmName";
	my $errormsg;

	my $confFile = &getGlobalConfiguration( 'dosConf' );

	if ( &getFarmFile( $farmName ) eq "-1" )
	{
		$errormsg = "$farmName doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( !&getDOSExists( $name ) )
	{
		$errormsg = "$name not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( &getDOSParam( $name, 'type' ) eq 'system' )
	{
		$errormsg = "System rules not is possible delete from a farm.";
	}
	else
	{
		my $fileHandle = Config::Tiny->read( $confFile );
		if ( $fileHandle->{ $name }->{ 'farms' } !~ /( |^)$farmName( |$)/ )
		{
			$errormsg = "This rule no is enabled in $farmName.";
		}
		else
		{
			require Zevenet::IPDS::DoS::Runtime;
			&setDOSUnsetRule( $name, $farmName );

			# check output
			my $output = &getDOSZapiRule( $name );
			if ( !grep ( /^$farmName$/, @{ $output->{ 'farms' } } ) )
			{
				$errormsg = "DoS rule $name was removed successful from the farm $farmName.";

				if ( &getFarmStatus( $farmName ) eq 'up' )
				{
					require Zevenet::Cluster;
					&runZClusterRemoteManager( 'ipds_dos', 'stop', $name, $farmName );
				}

				&httpResponse(
					{
					   code => 200,
					   body => { description => $description, success => "true", message => $errormsg }
					}
				);
			}
			else
			{
				$errormsg = "Error, removing $name rule from $farmName.";
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg, };
	&httpResponse( { code => 400, body => $body } );
}

# POST /ipds/dos/DOS/actions
sub actions_dos
{
	my $json_obj = shift;
	my $rule     = shift;

	my $description = "Apply a action to the DoS rule $rule";
	my $errormsg;

	if ( !&getDOSExists( $rule ) )
	{
		$errormsg = "$rule doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}

	require Zevenet::IPDS::DoS::Actions;
	my $error;
	if ( $json_obj->{ action } eq 'start' )
	{
		$error = &runDOSStartByRule( $rule );
	}
	elsif ( $json_obj->{ action } eq 'stop' )
	{
		$error = &runDOSStopByRule( $rule );
	}
	elsif ( $json_obj->{ action } eq 'restart' )
	{
		$error = &runDOSRestartByRule( $rule );
	}
	else
	{
		$errormsg = "The action has not a valid value";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 400, body => $body } );
	}

	if ( $error )
	{
		&httpResponse(
					   {
						 code => 400,
						 body => {
								   description => $description,
								   error       => "true",
								   message     => "Error, applying the action to the DoS rule."
						 }
					   }
		);
	}
	else
	{
		require Zevenet::Cluster;
		&runZClusterRemoteManager( 'ipds_dos', $json_obj->{ action }, $rule );
		&httpResponse(
					   {
						 code => 200,
						 body => {
								   description => $description,
								   success     => "true",
								   params      => $json_obj->{ action }
						 }
					   }
		);
	}
}

1;
