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

use Zevenet::API40::HTTP;

include 'Zevenet::IPDS::RBL::Core';

# GET /ipds/rbl
sub get_rbl_all_rules
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $rules = &getRBLZapi();
	my $desc  = "List the RBL rules";

	return &httpResponse(
				  { code => 200, body => { description => $desc, params => $rules } } );
}

#GET /ipds/rbl/<name>
sub get_rbl_rule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $name = shift;

	my $desc = "Get the RBL $name";

	unless ( &getRBLExists( $name ) )
	{
		my $msg = "Requested rule doesn't exist.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $ruleHash = &getRBLZapiRule( $name );
	my $body = { description => $desc, params => $ruleHash };

	return &httpResponse( { code => 200, body => $body } );
}

#  POST /ipds/rbl
sub add_rbl_rule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	include 'Zevenet::IPDS::RBL::Config';

	my $desc = "Create the RBL rule '$json_obj->{ 'name' }'";
	my $name = $json_obj->{ 'name' };

	my $params = {
				   "name" => {
							   'valid_format' => 'rbl_name',
							   'non_blank'    => 'true',
							   'required'     => 'true',
							   'exceptions'   => ['domains', '0'],
				   },
				   "copy_from" => {
									'valid_format' => 'rbl_name',
									'non_blank'    => 'true',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# A list already exists with this name
	if ( &getRBLExists( $name ) )
	{
		my $msg = "A RBL rule already exists with the name '$name'.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# copy rule
	if ( exists $json_obj->{ copy_from } )
	{
		if ( !&getRBLExists( $json_obj->{ copy_from } ) )
		{
			my $msg = "The RBL rule '$json_obj->{copy_from}' does not exist.";
			return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
		}
		if ( &addRBLCopyObjectRule( $json_obj->{ copy_from }, $name ) )
		{
			my $msg = "Error, copying a RBL rule.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# create a new one
	else
	{
		if ( &addRBLCreateObjectRule( $name ) )
		{
			my $msg = "Error, creating a new RBL rule.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	my $listHash = &getRBLZapiRule( $name );
	my $body = { description => $desc, params => $listHash };

	return &httpResponse( { code => 200, body => $body } );
}

#  PUT /ipds/rbl/<name>
sub set_rbl_rule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $name     = shift;

	include 'Zevenet::IPDS::RBL::Config';

	my $desc = "Modify the RBL rule $name.";

	my $params = {
				   "name" => {
							   'valid_format' => 'rbl_name',
							   'non_blank'    => 'true',
							   'exceptions'   => ['domains', '0'],
				   },
				   "threadmax" => {
									'valid_format' => 'integer',
									'non_blank'    => 'true',
				   },
				   "only_logging" => {
									   'values'    => ['true', 'false'],
									   'non_blank' => 'true',
				   },
				   "log_level" => {
									'interval'  => '0,7',
									'non_blank' => 'true',
				   },
				   "queue_size" => {
									 'valid_format' => 'natural_num',
									 'non_blank'    => 'true',
				   },
				   "cache_size" => {
									 'valid_format' => 'natural_num',
									 'non_blank'    => 'true',
				   },
				   "cache_time" => {
									 'valid_format' => 'natural_num',
									 'non_blank'    => 'true',
				   },
				   "local_traffic" => {
										'values'    => ['true', 'false'],
										'non_blank' => 'true',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	if ( !&getRBLExists( $name ) )
	{
		my $msg = "The RBL rule '$name' doesn't exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( exists $json_obj->{ 'name' } )
	{
		if ( &getRBLExists( $json_obj->{ 'name' } ) )
		{
			my $msg = "A RBL rule already exists with the name '$json_obj->{'name'}'.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
		else
		{
			include 'Zevenet::Cluster';
			&runZClusterRemoteManager( 'ipds_rbl', "stop", $name );

			include 'Zevenet::IPDS::RBL::Actions';
			&runRBLStopByRule( $name );

			if ( &setRBLRenameObjectRule( $name, $json_obj->{ 'name' } ) )
			{
				my $msg = "Error, setting name.";
				return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}

			$name = $json_obj->{ 'name' };
		}
	}

	# only_logging
	if ( exists $json_obj->{ 'only_logging' } )
	{
		my $option = 'yes';
		$option = 'no' if ( $json_obj->{ 'only_logging' } eq 'false' );
		if ( &setRBLObjectRuleParam( $name, 'only_logging', $option ) )
		{
			my $msg = "Error, setting only logging mode.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# log_level
	if ( exists $json_obj->{ 'log_level' } )
	{
		if ( &setRBLObjectRuleParam( $name, 'log_level', $json_obj->{ 'log_level' } ) )
		{
			my $msg = "Error, setting log level.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# queue_size
	if ( exists $json_obj->{ 'queue_size' } )
	{
		if (
			 &setRBLObjectRuleParam( $name, 'queue_size', $json_obj->{ 'queue_size' } ) )
		{
			my $msg = "Error, setting queue size.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# thread max
	if ( exists $json_obj->{ 'threadmax' } )
	{
		if ( &setRBLObjectRuleParam( $name, 'threadmax', $json_obj->{ 'threadmax' } ) )
		{
			my $msg = "Error, setting thread maximum.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# cache size
	if ( exists $json_obj->{ 'cache_size' } )
	{
		if (
			 &setRBLObjectRuleParam( $name, 'cache_size', $json_obj->{ 'cache_size' } ) )
		{
			my $msg = "Error, setting cache size.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# cache time
	if ( exists $json_obj->{ 'cache_time' } )
	{
		if (
			 &setRBLObjectRuleParam( $name, 'cache_time', $json_obj->{ 'cache_time' } ) )
		{
			my $msg = "Error, setting cache time.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# local traffic
	if ( exists $json_obj->{ 'local_traffic' } )
	{
		my $option = "no";
		$option = "yes" if ( $json_obj->{ 'local_traffic' } eq 'true' );
		if ( &setRBLObjectRuleParam( $name, 'local_traffic', $option ) )
		{
			my $msg = "Error, setting local time.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	include 'Zevenet::IPDS::RBL::Actions';
	&runRBLRestartByRule( $name );

	# all successful
	my $listHash = &getRBLZapiRule( $name );
	my $body = { description => $desc, params => $listHash };

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_rbl', "restart", $name );

	return &httpResponse( { code => 200, body => $body } );
}

#  DELETE /ipds/rbl/<name>
sub del_rbl_rule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $name = shift;

	include 'Zevenet::IPDS::RBL::Config';

	my $desc = "Delete the RBL rule $name";

	if ( !&getRBLExists( $name ) )
	{
		my $msg = "$name doesn't exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}
	elsif ( @{ &getRBLFarm( $name ) } )
	{
		my $msg = "Delete this rule from all farms before than delete it.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $error = &delRBLDeleteObjectRule( $name );
	if ( $error )
	{
		my $msg = "Error, deleting the rule $name.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $msg = "The rule $name has been deleted successfully.";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $msg,
	};

	return &httpResponse( { code => 200, body => $body } );
}

#  GET /ipds/rbl/domains
sub get_rbl_domains
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $desc = "List the available RBL domains";

	my @user;
	my $id = 0;
	foreach my $it ( @{ &getRBLUserDomains() } )
	{
		push @user, { 'id' => $id, 'domain' => $it };
		$id++;
	}

	my @preload;
	$id = 0;
	foreach my $it ( @{ &getRBLPreloadedDomains() } )
	{
		push @preload, { 'id' => $id, 'domain' => $it };
		$id++;
	}

	my $domains = { 'user' => \@user, 'preloaded' => \@preload };

	my $body = { description => $desc, params => $domains };

	return &httpResponse( { code => 200, body => $body } );
}

#  POST /ipds/rbl/domains
sub add_rbl_domain
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	include 'Zevenet::IPDS::RBL::Config';

	my $desc   = "Add the domain '$json_obj->{ 'domain' }'";
	my $domain = $json_obj->{ 'domain' };

	my $params = {
				   "domain" => {
								 'valid_format' => 'rbl_domain',
								 'non_blank'    => 'true',
								 'required'     => 'true',
								 'exceptions'   => ['0'],
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	if ( grep ( /^$domain$/, @{ &getRBLUserDomains() } ) )
	{
		my $msg = "$domain already exists.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( grep ( /^$domain$/, @{ &getRBLPreloadedDomains() } ) )
	{
		my $msg = "$domain already exists.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	&addRBLDomains( $domain );

	my $domains = &getRBLUserDomains();
	my $msg     = "Added RBL domain '$json_obj->{ 'domain' }'";
	my $body = {
				 description => $desc,
				 params      => { 'domains' => $domains },
				 message     => $msg,
	};

	return &httpResponse( { code => 200, body => $body } );
}

#  PUT /ipds/rbl/domains/<domain>
sub set_rbl_domain
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj  = shift;
	my $domain_id = shift;

	include 'Zevenet::IPDS::RBL::Config';

	my $desc             = "Replace the domain $domain_id";
	my $new_domain       = $json_obj->{ 'domain' };
	my @user_domain_list = @{ &getRBLUserDomains() };

	if ( $domain_id >= scalar @user_domain_list )
	{
		my $msg = "$domain_id not found";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $params = {
				   "domain" => {
								 'valid_format' => 'rbl_domain',
								 'non_blank'    => 'true',
								 'required'     => 'true',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	if ( grep ( /^$new_domain$/, @{ &getRBLDomains() } ) )
	{
		my $msg = "$new_domain already exists.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my @rules;
	my $domain = $user_domain_list[$domain_id];

	# get the rules where the domain is applied
	foreach my $rule ( &getRBLRuleList() )
	{
		# modify the domain in all rules where it is applied
		if ( grep ( /^$domain$/, @{ &getRBLObjectRuleParam( $rule, 'domains' ) } ) )
		{
			&setRBLObjectRuleParam( $rule, "del_domains", $domain );
			&setRBLObjectRuleParam( $rule, "add_domains", $new_domain );
			push @rules, $rule;
		}
	}

	&setRBLDomains( $domain, $new_domain );

	# Get response
	my @user;
	my $id = 0;
	foreach my $it ( @{ &getRBLUserDomains() } )
	{
		push @user, { 'id' => $id, 'domain' => $it };
		$id++;
	}

	my $msg = "RBL domain $new_domain has been modified successfully.";
	my $body = {
				 description => $desc,
				 message     => $msg,
				 params      => { "domains" => \@user }
	};

	include 'Zevenet::Cluster';
	foreach my $rule ( @rules )
	{
		&runZClusterRemoteManager( 'ipds_rbl', "restart", $rule );
	}

	return &httpResponse( { code => 200, body => $body } );
}

#  DELETE /ipds/rbl/domains/<domain>
sub del_rbl_domain
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $domain_id = shift;

	include 'Zevenet::IPDS::RBL::Config';

	my $desc = "Delete the domain $domain_id";

	my @user_domain_list = @{ &getRBLUserDomains() };
	if ( $domain_id >= scalar @user_domain_list )
	{
		my $msg = "$domain_id not found";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $domain = $user_domain_list[$domain_id];
	if ( &delRBLDomains( $domain ) )
	{
		my $msg = "Error deleting the RBL domain $domain_id";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $msg = "RBL domain $domain_id has been deleted successfully.";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $msg,
	};

	# Delete domain from the rules where the domain is applied
	foreach my $rule ( &getRBLRuleList() )
	{
		# modify the domain in all rules where it is applied
		if ( grep ( /^$domain$/, @{ &getRBLObjectRuleParam( $rule, 'domains' ) } ) )
		{
			include 'Zevenet::Cluster';

			&setRBLObjectRuleParam( $rule, "del_domains", $domain );
			&runZClusterRemoteManager( 'ipds_rbl', "restart", $rule );
		}
	}

	return &httpResponse( { code => 200, body => $body } );
}

#  POST /ipds/rbl/<name>/domains
sub add_domain_to_rbl
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $name     = shift;

	include 'Zevenet::IPDS::RBL::Config';

	my $desc   = "Add the domain '$json_obj->{ 'domain' }' to the RBL rule $name";
	my $domain = $json_obj->{ 'domain' };

	my $params = {
				   "domain" => {
								 'valid_format' => 'rbl_domain',
								 'non_blank'    => 'true',
								 'required'     => 'true',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	if ( !&getRBLExists( $name ) )
	{
		my $msg = "$name doesn't exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( grep ( /^$domain$/, @{ &getRBLObjectRuleParam( $name, 'domains' ) } ) )
	{
		my $msg = "$domain already exists in the rule.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $error = &setRBLObjectRuleParam( $name, 'domains-add', $domain );
	if ( $error )
	{
		my $msg = "Error, adding $domain to $name.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( &getRBLObjectRuleParam( $name, 'status' ) eq 'up' )
	{
		include 'Zevenet::IPDS::RBL::Actions';
		&runRBLRestartByRule( $name );
	}

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_rbl', "restart", $name );

	my $msg  = "Added $domain domain successfully.";
	my $rule = &getRBLZapiRule( $name );
	my $body = {
				 description => $desc,
				 params      => $rule,
				 message     => $msg,
	};

	return &httpResponse( { code => 200, body => $body } );
}

#  DELETE /ipds/rbl/<name>/domains/<domain>
sub del_domain_from_rbl
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $name   = shift;
	my $domain = shift;

	include 'Zevenet::IPDS::RBL::Config';

	my $desc = "Delete the domain '$domain' from a RBL rule '$name'";

	if ( !&getRBLExists( $name ) )
	{
		my $msg = "'$name' doesn't exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( !grep ( /^$domain$/, @{ &getRBLObjectRuleParam( $name, 'domains' ) } ) )
	{
		my $msg = "The '$domain' domain is not applied to the '$name' RBL rule.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	include 'Zevenet::Cluster';
	if ( &setRBLObjectRuleParam( $name, 'domains-del', $domain ) )
	{
		my $msg = "Error deleting a domain from a RBL rule.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( &getRBLObjectRuleParam( $name, 'status' ) eq 'up' )
	{
		include 'Zevenet::IPDS::RBL::Actions';
		&runRBLRestartByRule( $name );
	}

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_rbl', "restart", $name );

	my $msg =
	  "The domain '$domain' has been deleted successfully from the RBL rule '$name'.";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $msg,
	};

	return &httpResponse( { code => 200, body => $body } );
}

#  POST /farms/<farmname>/ipds/rbl
sub add_rbl_to_farm
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmName = shift;

	include 'Zevenet::IPDS::RBL::Config';

	my $desc = "Apply the RBL rule $json_obj->{ 'name' } to the farm $farmName";
	my $name = $json_obj->{ 'name' };

	my $params = {
				   "name" => {
							   'valid_format' => 'rbl_name',
							   'non_blank'    => 'true',
							   'required'     => 'true',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	require Zevenet::Farm::Core;
	if ( !&getFarmExists( $farmName ) )
	{
		my $msg = "$farmName doesn't exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( !&getRBLExists( $name ) )
	{
		my $msg = "$name doesn't exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# it is necessary that the rule has almost one domain to start a RBL rule
	if ( !@{ &getRBLObjectRuleParam( $name, 'domains' ) } )
	{
		my $msg =
		  "The RBL rule '$name' was not started because it has not got any domain.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# only allow a RBL rule for farm. It's currently a nftlb limitation
	&lockResource( "rbl-$farmName", 'l' );
	if ( &listRBLByFarm( $farmName ) )
	{
		&lockResource( "rbl-$farmName", 'ud' );
		my $msg = "The '$farmName' farm already is linked with a RBL rule.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	&addRBLFarm( $farmName, $name );
	&lockResource( "rbl-$farmName", 'ud' );
	if ( !grep ( /^$farmName$/, @{ &getRBLFarm( $name, 'farms' ) } ) )
	{
		my $msg = "Error, applying $name to $farmName";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $msg = "RBL rule $name was applied successfully to the farm $farmName.";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $msg
	};

	require Zevenet::Farm::Base;
	if ( &getFarmStatus( $farmName ) eq 'up' )
	{
		include 'Zevenet::Cluster';
		&runZClusterRemoteManager( 'ipds_rbl', "start", $name, $farmName );
	}

	return &httpResponse( { code => 200, body => $body } );
}

# DELETE /farms/<farmname>/ipds/rbl/<name>
sub del_rbl_from_farm
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmName = shift;
	my $name     = shift;

	include 'Zevenet::IPDS::RBL::Config';
	include 'Zevenet::IPDS::Core';
	require Zevenet::Farm::Core;

	my $desc = "Delete the RBL rule $name from the farm $farmName";

	if ( !&getFarmExists( $farmName ) )
	{
		my $msg = "'$farmName' doesn't exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( !&getRBLExists( $name ) )
	{
		my $msg = "'$name' doesn't exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( !grep ( /^$farmName$/, @{ &getRBLFarm( $name, 'farms' ) } ) )
	{
		my $msg = "Not found a rule associated to '$name' and '$farmName'.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	&delRBLFarm( $farmName, $name );

	# Call to remove service if possible
	&delIPDSFarmService( $farmName );

	if ( grep ( /^$farmName$/, @{ &getRBLFarm( $name, 'farms' ) } ) )
	{
		my $msg = "Error, removing '$name' rule from '$farmName'.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $msg =
	  "RBL rule '$name' was removed successfully from the farm '$farmName'.";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $msg,
	};

	if ( &getFarmStatus( $farmName ) eq 'up' )
	{
		include 'Zevenet::Cluster';
		&runZClusterRemoteManager( 'ipds_rbl', "stop", $name, $farmName );
	}

	return &httpResponse( { code => 200, body => $body } );
}

# POST /ipds/rbl/<name>/actions
sub set_rbl_actions
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $name     = shift;

	include 'Zevenet::IPDS::RBL::Actions';

	my $desc   = "Apply an action to the RBL rule $name";
	my $action = $json_obj->{ 'action' };

	my $params = {
				   "action" => {
								 'non_blank' => 'true',
								 'values'    => ['stop', 'start'],
								 'required'  => 'true',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	if ( !&getRBLExists( $name ) )
	{
		my $msg = "$name doesn't exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# to start a RBL rule it is necessary that the rule has almost one domain
	if ( !@{ &getRBLObjectRuleParam( $name, 'domains' ) } )
	{
		my $msg = "RBL rule '$name' was not started because it has not got any domain.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# Error message in case the following action fails
	my $msg = "Error, trying to $action the RBL rule, $name";

	if ( $action eq 'start' )
	{
		if ( !@{ &getRBLFarm( $name ) } )
		{
			$msg = "The rule has to be applied to some farm to be started it.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		include 'Zevenet::IPDS::RBL::Config';

		&setRBLObjectRuleParam( $name, 'status', 'up' );
		my $error = &runRBLStartByRule( $name );

		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg ) if $error;
	}
	elsif ( $action eq 'stop' )
	{
		include 'Zevenet::IPDS::RBL::Config';

		&setRBLObjectRuleParam( $name, 'status', 'down' );
		my $error = &runRBLStopByRule( $name );

		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg ) if $error;
	}
	elsif ( $action eq 'restart' )
	{
		include 'Zevenet::IPDS::RBL::Config';

		my $error = &runRBLRestartByRule( $name );
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg ) if $error;
		&setRBLObjectRuleParam( $name, 'status', 'up' );
	}

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_rbl', $action, $name );

	my $status = &getRBLObjectRuleParam( $name, 'status' );
	if (    ( $action eq 'start' and $status ne 'up' )
		 or ( $action eq 'stop' and $status ne 'down' ) )
	{
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $body = {
				 description => $desc,
				 success     => "true",
				 params      => { status => $status }
	};

	return &httpResponse( { code => 200, body => $body } );
}

1;

