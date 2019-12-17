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

include 'Zevenet::IPDS::DoS::Core';
include 'Zevenet::IPDS::DoS::Config';

# GET /ipds/dos/rules
sub get_dos_rules
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $description = "Get DoS settings.";

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $confFile    = &getGlobalConfiguration( 'dosConf' );
	my $description = "Get DoS settings.";

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj       = shift;
	my $description    = "Post a DoS rule";
	my $rule           = $json_obj->{ 'rule' };
	my @requiredParams = ( "name", "rule" );
	my $confFile       = &getGlobalConfiguration( 'dosConf' );

	my $errormsg = &getValidReqParams( $json_obj, \@requiredParams );
	if ( !$errormsg )
	{
		if ( &getDOSExists( $json_obj->{ 'name' } ) )
		{
			$errormsg = "$json_obj->{ 'name' } already exists.";
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $name        = shift;
	my $description = "Get DoS $name settings";

	if ( !&getDOSExists( $name ) )
	{
		my $output = "$name does not exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $output
		};
		&httpResponse( { code => 404, body => $body } );
	}

	my $refRule = &getDOSZapiRule( $name );

	# successful
	my $body = { description => $description, params => $refRule, };
	&httpResponse( { code => 200, body => $body } );
}

#PUT /ipds/dos/<rule>
sub set_dos_rule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj    = shift;
	my $name        = shift;
	my $description = "Put DoS rule settings";
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
				foreach my $param ( keys %{ $json_obj } )
				{
					&setDOSParam( $name, $param, $json_obj->{ $param } );
				}

				if ( !$errormsg )
				{
					my $refRule = &getDOSZapiRule( $name );

					include 'Zevenet::Cluster';
					&runZClusterRemoteManager( 'ipds', 'restart_dos' );

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	#~ my $json_obj = shift;
	my $name = shift;
	my $errormsg;
	my $description = "Delete DoS rule from a farm";

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
		&deleteDOSRule( $name );
		$errormsg = "Deleted $name successfully.";
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

#  POST /farms/<farmname>/ipds/dos
sub add_dos_to_farm
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj    = shift;
	my $farmName    = shift;
	my $description = "Apply a rule to a farm";
	my $name        = $json_obj->{ 'name' };
	my $errormsg;

	my $confFile = &getGlobalConfiguration( 'dosConf' );
	my $output   = "down";

	if ( !&getFarmExists( $farmName ) )
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
			include 'Zevenet::IPDS::DoS::Runtime';
			&setDOSApplyRule( $farmName, $name );

			my $confFile = &getGlobalConfiguration( 'dosConf' );

			# check output
			my $output = &getDOSParam( $name, 'farms' );
			if ( grep ( /^$farmName$/, @{ $output } ) )
			{
				$errormsg = "DoS rule $name was applied successfully to the farm $farmName.";

				if ( &getFarmStatus( $farmName ) eq 'up' )
				{
					include 'Zevenet::Cluster';
					&runZClusterRemoteManager( 'ipds', 'restart_dos' );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmName    = shift;
	my $name        = shift;
	my $description = "Delete a rule from a farm";
	my $errormsg;

	my $confFile = &getGlobalConfiguration( 'dosConf' );

	if ( !&getFarmExists( $farmName ) )
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
			include 'Zevenet::IPDS::DoS::Runtime';
			include 'Zevenet::IPDS::Core';

			&setDOSUnsetRule( $name, $farmName );

			# Call to remove service if possible
			&delIPDSFarmService( $farmName );

			# check output
			my $output = &getDOSZapiRule( $name );
			if ( !grep ( /^$farmName$/, @{ $output->{ 'farms' } } ) )
			{
				$errormsg = "DoS rule $name was removed successfully from the farm $farmName.";

				if ( &getFarmStatus( $farmName ) eq 'up' )
				{
					include 'Zevenet::Cluster';
					&runZClusterRemoteManager( 'ipds', 'restart_dos' );
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

1;
