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
use Zevenet::IPDS::RBL;

# GET /ipds/rbl
sub get_rbl_all_rules
{
	my $rules   = &getRBLZapi();
	my $description = "Get RBL rules";

	&httpResponse(
		  { code => 200, body => { description => $description, params => $rules } } );
}


#GET /ipds/rbl/<name>
sub get_rbl_rule
{
	my $name    = shift;
	my $description = "Get RBL $name";
	my $errormsg;
	
	if ( &getRBLExists( $name ) )
	{
		my $ruleHash = &getRBLZapiRule ( $name );
		
		&httpResponse(
			  { code => 200, body => { description => $description, params => $ruleHash } }
		);
	}
	else
	{
		$errormsg = "Requested rule doesn't exist.";
		my $body =
		  { description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 400, body => $body } );
	}
}


#  POST /ipds/rbl
sub add_rbl_rule
{
	my $json_obj = shift;
	my $errormsg;
	my $name    = $json_obj->{ 'name' };
	my $description = "Create a RBL rule.";

	# A list already exists with this name 
	if ( &getRBLExists( $name ) )
	{
		$errormsg = "A RBL rule already exists with the name '$name'.";
	}
	elsif ( !&getValidFormat( "rbl_name", $name ) )
	{
		$errormsg = "The RBL name has not a valid format.";
	}
	elsif ( $name eq "domains" )
	{
		$errormsg = "Error, \"domains\" is a reserved word.";
	}
	else
	{
		if ( &addRBLCreateObjectRule( $name ) )
		{
			$errormsg = "Error, creating a new RBL rule.";
		}
		
		# All successful
		else
		{
			my $listHash = &getRBLZapiRule ( $name );
			&httpResponse(
				{
						code => 200,
						body => { description => $description, params => $listHash }
				}
			);
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg,
	};
	&httpResponse( { code => 400, body => $body } );
}


#  POST /ipds/rbl/<name>
sub copy_rbl_rule
{
	my $json_obj = shift;
	my $name    = shift;
	my $errormsg;
	my $newrule    = $json_obj->{ 'name' };
	my $description = "Copy a RBL rule.";

	# A list already exists with this name 
	if ( !&getRBLExists( $name ) )
	{
		$errormsg = "The RBL rule '$name' doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( &getRBLExists( $newrule ) )
	{
		$errormsg = "A RBL rule already exists with the name '$newrule'.";
	}
	elsif ( !&getValidFormat( "rbl_name", $newrule ) )
	{
		$errormsg = "The RBL name has not a valid format.";
	}
	elsif ( $newrule eq "domains" )
	{
		$errormsg = "Error, \"domains\" is a reserved word.";
	}
	else
	{
		if ( &addRBLCopyObjectRule( $name, $newrule ) )		
		{
			$errormsg = "Error, copying a RBL rule.";
		}
		
		# All successful
		else
		{
			my $listHash = &getRBLZapiRule ( $newrule );
			&httpResponse(
				{
						code => 200,
						body => { description => $description, params => $listHash }
				}
			);
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg,
	};
	&httpResponse( { code => 400, body => $body } );
}


#  PUT /ipds/rbl/<name>
sub set_rbl_rule
{
	my $json_obj    = shift;
	my $name    = shift;
	my $description = "Modify RBL rule $name.";
	my $errormsg;
	my @allowParams = ( "name", "cache_size", "cache_time", "queue_size", "threadmax", "local_traffic", "only_logging", "log_level" );
	
	if ( !&getRBLExists( $name ) )
	{
		$errormsg = "The RBL rule '$name' doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}
	
	$errormsg = &getValidOptParams( $json_obj, \@allowParams );
	# Rename
	if ( !$errormsg && exists $json_obj->{ 'name' } )
	{
		if ( !&getValidFormat( 'rbl_name', $json_obj->{'name'} ) )
		{
			$errormsg = "The RBL name has not a valid format.";
		}
		elsif ( &getRBLExists( $json_obj->{'name'} ) )
		{
			$errormsg = "A RBL rule already exists with the name '$json_obj->{'name'}'.";
		}
		elsif ( $json_obj->{'name'} eq "domains" )
		{
			$errormsg = "Error, \"domains\" is a reserved word.";
		}
		else
		{
			if ( &setRBLRenameObjectRule($name, $json_obj->{'name'}) )
			{
				$errormsg = "Error, setting name.";
			}
			else 
			{
				$name = $json_obj->{'name'};
			}
		}
	}
	# only_logging
	if ( !$errormsg && exists $json_obj->{ 'only_logging' } )
	{
		if ( !&getValidFormat( 'rbl_only_logging', $json_obj->{'only_logging'} ) )
		{
			$errormsg = "Error, only level must be true or false.";
		}
		else
		{
			my $option='yes';
			$option='no' if( $json_obj->{'only_logging'} eq 'false' );
			if ( &setRBLObjectRuleParam($name, 'only_logging', $option) )
			{
				$errormsg = "Error, setting only logging mode.";
			}
		}
	}
	# log_level
	if ( !$errormsg && exists $json_obj->{ 'log_level' } )
	{
		if ( !&getValidFormat( 'rbl_log_level', $json_obj->{'log_level'} ) )
		{
			$errormsg = "Error, log level must be a number between 0 and 7.";
		}
		else
		{
			if ( &setRBLObjectRuleParam($name, 'log_level', $json_obj->{'log_level'}) )
			{
				$errormsg = "Error, setting log level.";
			}
		}
	}
	# queue_size
	if ( !$errormsg && exists $json_obj->{ 'queue_size' } )
	{
		if ( !&getValidFormat( 'rbl_queue_size', $json_obj->{'queue_size'} ) )
		{
			$errormsg = "Error, queue size must be a number.";
		}
		else
		{
			
			if ( &setRBLObjectRuleParam($name, 'queue_size', $json_obj->{'queue_size'}) )
			{
				$errormsg = "Error, setting queue size.";
			}
		}
	}
	# thread max
	if ( !$errormsg && exists $json_obj->{ 'threadmax' } )
	{
		if ( !&getValidFormat( 'rbl_thread_max', $json_obj->{'threadmax'} ) )
		{
			$errormsg = "Error, thread maximum must be a number.";
		}
		else
		{
			if ( &setRBLObjectRuleParam($name, 'threadmax', $json_obj->{'threadmax'}) )
			{
				$errormsg = "Error, setting thread maximum.";
			}
		}
	}
	# cache size
	if ( !$errormsg && exists $json_obj->{ 'cache_size' } )
	{
		if ( !&getValidFormat( 'rbl_cache_size', $json_obj->{'cache_size'} ) )
		{
			$errormsg = "Error, cache size must be a number.";
		}
		else
		{
			if ( &setRBLObjectRuleParam($name, 'cache_size', $json_obj->{'cache_size'}) )
			{
				$errormsg = "Error, setting cache size.";
			}
		}
	}
	# cache time
	if ( !$errormsg && exists $json_obj->{ 'cache_time' } )
	{
		if ( !&getValidFormat( 'rbl_cache_time', $json_obj->{'cache_time'} ) )
		{
			$errormsg = "Error, cache time must be a number.";
		}
		else
		{
			if ( &setRBLObjectRuleParam($name, 'cache_time', $json_obj->{'cache_time'}) )
			{
				$errormsg = "Error, setting cache time.";
			}
		}
	}
	# local traffic
	if ( !$errormsg && exists $json_obj->{ 'local_traffic' } )
	{
		if ( !&getValidFormat( 'rbl_local_traffic', $json_obj->{'local_traffic'} ) )
		{
			$errormsg = "Error, cache time must be a number.";
		}
		else
		{
			my $option = "no";
			$option = "yes" if ( $json_obj->{'local_traffic'} eq 'true' );
			if ( &setRBLObjectRuleParam($name, 'local_traffic', $option) )
			{
				$errormsg = "Error, setting local time.";
			}
		}
	}
	
	if ( !$errormsg )	
	{
		# all successful
		my $listHash = &getRBLZapiRule( $name );
		my $body = { description => $description, params => $listHash };
	
		&runZClusterRemoteManager( 'ipds', "restart_rbl_$name" );
	
		&httpResponse({ code => 200, body => $body } );
	}

	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg,
	};
	&httpResponse( { code => 400, body => $body } );
}


#  DELETE /ipds/rbl/<name>
sub del_rbl_rule
{
	my $name    = shift;
	my $description = "Delete RBL '$name'",
	my $errormsg;
	
	if ( !&getRBLExists( $name ) )
	{
		$errormsg = "$name doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( @{ &getRBLFarm ($name) }  )
	{
		$errormsg = "Delete this rule from all farms before than delete it.";
	}
	else
	{
		$errormsg = &delRBLDeleteObjectRule( $name );
		if ( !$errormsg )
		{
			$errormsg = "The rule $name has been deleted successful.";
			my $body = {
						 description => $description,
						 success  => "true",
						 message     => $errormsg,
			};
			&httpResponse( { code => 200, body => $body } );
		}
		else
		{
			$errormsg = "Error, deleting the rule $name.";
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg,
	};
	&httpResponse( { code => 400, body => $body } );
}


#  GET /ipds/rbl/domains
sub get_rbl_domains
{
	my $description = "Get RBL domains";

	my $domains = { 'user' => &getRBLUserDomains(), 'preloaded' => &getRBLPreloadedDomains() };
	
	&httpResponse(
				   {
					 code => 200,
					 body => { description => $description, params => $domains }
				   }
	);
}


#  POST /ipds/rbl/domains
sub add_rbl_domain
{
	my $json_obj = shift;
	my $domain = $json_obj->{ 'domain' };
	my $errormsg;
	my $description    = "Post a RBL domain.";
	my @requiredParams = ( "domain" );
	my @optionalParams;

	if ( grep ( /^$domain$/, @{ &getRBLUserDomains() } ) )
	{
		$errormsg = "$domain already exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 400, body => $body } );
	}
	if ( grep ( /^$domain$/, @{ &getRBLPreloadedDomains() } ) )
	{
		$errormsg = "$domain already exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 400, body => $body } );
	}
	
	else
	{
		$errormsg = &getValidReqParams( $json_obj, \@requiredParams, \@optionalParams );
		if ( !$errormsg )
		{
			if ( !&getValidFormat( 'rbl_domain', $domain ) )
			{
				$errormsg = "Error, the RBL domain format is not valid.";
			}
			else
			{
				&addRBLDomains( $domain );
				my $domains = &getRBLUserDomains();
				my $body = {
							 description => $description,
							 params      => { 'domains' => $domains },
							 message     => $errormsg,
				};
				&httpResponse( { code => 200, body => $body } );
			}
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg,
	};
	&httpResponse( { code => 400, body => $body } );
}


#  PUT /ipds/rbl/domains/<domain>
sub set_rbl_domain
{
	my $json_obj    = shift;
	my $domain    = shift;
	my $description = "Replace a domain";
	my $errormsg;
	my @allowParams = ( "domain" );
	my $new_domain = $json_obj->{'domain'};

	# check list exists
	if ( grep ( /^$domain$/, @{ &getRBLPreloadedDomains() } ) )
	{
		$errormsg = "Error, only can be modified the domains created by the user.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 400, body => $body } );
	}
	
	if ( !grep ( /^$domain$/, @{ &getRBLUserDomains() } ) )
	{
		$errormsg = "$domain not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}

	elsif ( grep ( /^$new_domain$/, @{ &getRBLDomains() } ) )
	{
		$errormsg = "$new_domain already exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 400, body => $body } );
	}

	else
	{
		$errormsg = &getValidOptParams( $json_obj, \@allowParams );
		if ( !$errormsg )
		{
			if ( !&getValidFormat( 'rbl_domain', $new_domain ) )
			{
				$errormsg = "Error, Wrong domain format.";
			}
			
			my @rules;
			# get the rules where the domain is applied 
			foreach my $rule ( &getRBLRuleList() )
			{	
				# modify the domain in all rules where it is applied
				if ( grep( /^$domain$/, @{ &getRBLObjectRuleParam( $rule, 'domains' ) } ) )
				{
					&setRBLObjectRuleParam( $rule, "del_domains", $domain );
					&setRBLObjectRuleParam( $rule, "add_domains", $new_domain );
					push @rules, $rule;
				}
			}
			
			&setRBLDomains( $domain, $new_domain );
			my $domains = &getRBLUserDomains(  );
			$errormsg = "RBL domain $new_domain has been modified successful.";
			my $body = {
						 description => $description, message     => $errormsg,
						 params      => { "domains" => $domains } 
			};

			foreach my $rule ( @rules )
			{
				&runZClusterRemoteManager( 'ipds', "restart_rbl_$rule" );
			}

			&httpResponse( { code => 200, body => $body } );
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg,
	};
	&httpResponse( { code => 400, body => $body } );
}


#  DELETE /ipds/rbl/domains/<domain>
sub del_rbl_domain
{
	my $domain = shift;
	my $errormsg;
	my $description = "Delete a RBL domain.";

	if ( grep ( /^$domain$/, @{ &getRBLPreloadedDomains() } ) )
	{
		$errormsg = "Error, only can be deleted the domains created by the user.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 400, body => $body } );
	}
	if ( ! grep ( /^$domain$/, @{ &getRBLDomains() } ) )
	{
		$errormsg = "$domain doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}
	else
	{
		if ( &delRBLDomains( $domain ) )
		{
			$errormsg = "Error deleting the RBL domain $domain";
		}
		else
		{
			my $errormsg = "RBL domain $domain has been deleted successful.";
			my $body = {
						 description => $description,
						 success     => "true",
						 message     => $errormsg,
			};

			# Delete domain from the rules where the domain is applied 
			foreach my $rule ( &getRBLRuleList() )
			{	
				# modify the domain in all rules where it is applied
				if ( grep( /^$domain$/, @{ &getRBLObjectRuleParam( $rule, 'domains' ) } ) )
				{
					&setRBLObjectRuleParam( $rule, "del_domains", $domain );
					&runZClusterRemoteManager( 'ipds', "restart_rbl_$rule" );
				}
			}


			&httpResponse( { code => 200, body => $body } );
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg,
	};
	&httpResponse( { code => 400, body => $body } );
}


#  POST /ipds/rbl/<name>/domains
sub add_domain_to_rbl
{
	my $json_obj = shift;
	my $name = shift;
	my $errormsg;
	my $description    = "Post a domain to a RBL rule.";
	my $domain    = $json_obj->{ 'domain' };
	my @requiredParams = ( "domain" );
	my @optionalParams;

	if ( ! &getRBLExists( $name ) )
	{
		$errormsg = "$name doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( !&getValidFormat ( 'rbl_domain', $domain ) )
	{
		$errormsg = "The domain has not a correct format.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}
	
	else
	{
		$errormsg = &getValidReqParams( $json_obj, \@requiredParams, \@optionalParams );
		if ( !$errormsg )
		{
			if ( grep ( /^$domain$/, @{ &getRBLObjectRuleParam( $name, 'domains' ) } ) )
			{
				$errormsg = "$domain already exists in the rule.";
			}
			else
			{
				$errormsg = &setRBLObjectRuleParam( $name, 'domains-add', $domain );
				if ( !$errormsg )
				{
					$errormsg = "Added $domain successful.";

					&runZClusterRemoteManager( 'ipds', "restart_rbl_$name" );

					my $rule = &getRBLZapiRule( $name );
					my $body = {
								 description => $description,
								 params      => $rule,
								 message     => $errormsg,
					};
					&httpResponse( { code => 200, body => $body } );
				}
				else
				{
					$errormsg = "Error, adding $domain to $name.";
				}
			}
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg,
	};
	&httpResponse( { code => 400, body => $body } );
}


#  DELETE /ipds/rbl/<name>/domains/<domain>
sub del_domain_from_rbl
{
	my $name = shift;
	my $domain = shift;
	my $errormsg;
	my $description = "Delete a domain from a RBL rule.";

	if ( ! &getRBLExists( $name ) )
	{
		$errormsg = "$name doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( ! grep ( /^$domain$/, @{ &getRBLObjectRuleParam( $name, 'domains' ) } ) )
	{
		$errormsg = "The domains is not applied to the RBL rule.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 400, body => $body } );
	}
	else
	{
		if ( &setRBLObjectRuleParam ( $name, 'domains-del', $domain ) )
		{
			$errormsg = "Error deleting a domain from a RBL rule.";
		}
		else
		{
			my $errormsg = "The domain $domain has been deleted successful from the RBL rule $name.";
			my $body = {
						 description => $description,
						 success     => "true",
						 message     => $errormsg,
			};

			&runZClusterRemoteManager( 'ipds', "restart_rbl_$name" );

			&httpResponse( { code => 200, body => $body } );
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg,
	};
	&httpResponse( { code => 400, body => $body } );
}


#  POST /farms/<farmname>/ipds/rbl
sub add_rbl_to_farm
{
	my $json_obj = shift;
	my $farmName = shift;
	my $name = $json_obj->{ 'name' };
	my $errormsg;
	my $description = "Apply a rule to a farm";

	$errormsg = &getValidReqParams( $json_obj, ["name"] );
	if ( !$errormsg )
	{
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
		elsif ( !&getRBLExists( $name ) )
		{
			$errormsg = "$name doesn't exist.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};
			&httpResponse( { code => 404, body => $body } );
		}
		else
		{
			if ( grep ( /^$farmName$/, @{ &getRBLFarm( $name, 'farms' ) } ) )
			{
				$errormsg = "$name is already applied to $farmName.";
			}
			# for start a RBL rule it is necessary that the rule has almost one domain
			elsif ( !@{ &getRBLObjectRuleParam($name, 'domains') } )
			{
				$errormsg = "RBL rule, $name, was not started because doesn't have any domain.";
			}
			else
			{
				$errormsg = &addRBLFarm( $farmName, $name );
				if ( !$errormsg )
				{
					my $errormsg = "RBL rule $name was applied successful to the farm $farmName.";
					my $body = {
								 description => $description,
								 success      => "true",
								 message     => $errormsg
					};

					if ( &getFarmStatus( $farmName ) eq 'up' )
					{
						&runZClusterRemoteManager( 'ipds', "start_rbl_$name,$farmName" );
					}

					&httpResponse( { code => 200, body => $body } );
				}
				else
				{
					$errormsg = "Error, applying $name to $farmName";
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


# DELETE /farms/<farmname>/ipds/rbl/<name>
sub del_rbl_from_farm
{
	my $farmName = shift;
	my $name = shift;
	my $errormsg;
	my $description = "Delete a rule from a farm";

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
	elsif ( ! &getRBLExists( $name ) )
	{
		$errormsg = "$name doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( !grep ( /^$farmName$/, @{ &getRBLFarm( $name, 'farms' ) } ) )
	{
		$errormsg = "Not found a rule associated to $name and $farmName.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	else
	{
		$errormsg = &delRBLFarm( $farmName, $name );
		if ( !$errormsg )
		{
			$errormsg = "RBL rule $name was removed successful from the farm $farmName.";
			my $body = {
						 description => $description,
						 success     => "true",
						 message     => $errormsg,
			};

			if ( &getFarmStatus( $farmName ) eq 'up' )
			{
				&runZClusterRemoteManager( 'ipds', "stop_rbl_$name,$farmName" );
			}

			&httpResponse( { code => 200, body => $body } );
		}
		else
		{
			$errormsg = "Error, removing $name rule from $farmName.";
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg
	};
	&httpResponse( { code => 400, body => $body } );
}


# POST /ipds/rbl/<name>/actions
sub set_rbl_actions
{
	my $json_obj = shift;
	my $name = shift;
	my $action = $json_obj->{ 'action' };
	my $errormsg;
	my $description = "Apply a action to a RBL rule";

	$errormsg = &getValidReqParams( $json_obj, ["action"] );
	if ( !$errormsg )
	{
		if ( !&getRBLExists( $name ) )
		{
			$errormsg = "$name doesn't exist.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};
			&httpResponse( { code => 404, body => $body } );
		}
		else
		{
			if ( !&getValidFormat( 'rbl_actions', $json_obj->{ 'action' } ) )
			{		
				my $errormsg = "Invalid action; the possible actions are stop, start and restart";
			}
			# to start a RBL rule it is necessary that the rule has almost one domain
			elsif ( !@{ &getRBLObjectRuleParam($name, 'domains') } )
			{
				$errormsg = "RBL rule, $name, was not started because doesn't have any domain.";
			}
			else
			{	
				if ( $action eq 'start' )
				{
					$errormsg = &runRBLStartByRule( $name );
				}
				elsif ( $action eq 'stop' )
				{
					$errormsg = &runRBLStopByRule( $name );
				}
				elsif ( $action eq 'restart' )
				{
					$errormsg = &runRBLRestartByRule( $name );
				}
				
				if ( !$errormsg )
				{
					my $body = {
								description => $description,
								params     => { 'action' => $action },
								
					};
		
					&runZClusterRemoteManager( 'ipds', "${action}_rbl_$name" );
		
					&httpResponse( { code => 200, body => $body } );
				}
				else
				{
					$errormsg = "Error, trying to $action the RBL rule, $name";
				}
			}			
		}
	}
	
	my $body = {
				description => $description,
				error       => "true",
				message     => $errormsg,
	};
	
	&httpResponse({ code => 400, body => $body });
}


1;
