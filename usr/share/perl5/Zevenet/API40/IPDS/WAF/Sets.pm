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
require Zevenet::API40::HTTP;

include 'Zevenet::IPDS::WAF::Core';
include 'Zevenet::API40::IPDS::WAF::Structs';

sub get_waf_options
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $desc = "List the available options to create a rule match";

	my @operators = &getWafOperators();
	delete $_->{ libkey } for ( @operators );    # remove the 'libkey' key
	my @variables       = &getWafVariables();
	my @transformations = &getWafTransformations();

	my $params = {
				   operators       => \@operators,
				   variables       => \@variables,
				   transformations => \@transformations,
	};

	my $body = { description => $desc, params => $params };

	return &httpResponse( { code => 200, body => $body } );
}

#GET /ipds/waf
sub list_waf_sets
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my @sets = &listWAFSet();
	my $desc = "List the WAF sets";

	my @out = ();

	foreach my $set ( sort @sets )
	{
		my $status = &getWAFSetStatus( $set );
		my @farms  = &listWAFBySet( $set );
		push @out, { status => $status, name => $set, farms => \@farms };
	}

	return &httpResponse(
				   { code => 200, body => { description => $desc, params => \@out } } );
}

#  GET /ipds/waf/<set>
sub get_waf_set
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $set = shift;

	my $desc = "Get the WAF set $set";

	unless ( &existWAFSet( $set ) )
	{
		my $msg = "Requested set $set does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $set_st = &getZapiWAFSet( $set );
	my @farms  = &listWAFBySet( $set );
	$set_st->{ farms } = \@farms;
	my $body = { description => $desc, params => $set_st };

	return &httpResponse( { code => 200, body => $body } );
}

#  POST ipds/waf
sub create_waf_set
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	include 'Zevenet::IPDS::WAF::Config';

	my $desc = "Create the WAF set, $json_obj->{ 'name' }";
	my $params = {
				   "name" => {
							   'valid_format' => 'waf_set_name',
							   'non_blank'    => 'true',
							   'required'     => 'true',
							   'exceptions'   => ['options', 'files', '0'],
				   },
				   "copy_from" => {
									'valid_format' => 'waf_set_name',
									'non_blank'    => 'true',
				   },
	};

	# Check if it exists
	if ( &existWAFSet( $json_obj->{ 'name' } ) )
	{
		my $msg = "$json_obj->{ 'name' } already exists.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# executing the action
	if ( exists $json_obj->{ 'copy_from' } )
	{
		unless ( &existWAFSet( $json_obj->{ 'copy_from' } ) )
		{
			my $msg = "$json_obj->{ 'copy_from' } does not exist.";
			return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
		}

		&copyWAFSet( $json_obj->{ 'name' }, $json_obj->{ 'copy_from' } );
	}
	else
	{
		&createWAFSet( $json_obj->{ 'name' } );
	}

	my $output = &getZapiWAFSet( $json_obj->{ 'name' } );

	# check result and return success or failure
	if ( $output )
	{
		my $msg = "Added the WAF set $json_obj->{ 'name' }";
		my $body = {
					 description => $desc,
					 params      => $output,
					 message     => $msg,
		};
		return &httpResponse( { code => 201, body => $body } );
	}
	else
	{
		my $msg = "Error, trying to create the WAF set $json_obj->{ name }";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
}

#  PUT ipds/waf/<set>
sub modify_waf_set
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $set      = shift;

	include 'Zevenet::IPDS::WAF::Config';

	my $desc = "Modify the WAF set $set";
	my $params = {
				   "audit" => {
								'valid_format' => 'boolean',
								'non_blank'    => 'true',
				   },
				   "process_request_body" => {
											   'valid_format' => 'boolean',
											   'non_blank'    => 'true',
				   },
				   "process_response_body" => {
												'valid_format' => 'boolean',
												'non_blank'    => 'true',
				   },
				   "request_body_limit" => {
											 'valid_format' => 'natural_num',
				   },
				   "only_logging" => {
									   'valid_format' => 'boolean',
									   'non_blank'    => 'true',
				   },
				   "default_action" => {
									   'values'    => ["allow", "redirect", "pass", "deny"],
									   'non_blank' => 'true',
				   },
				   "default_log" => {
									  'valid_format' => 'waf_log',
				   },
				   "default_phase" => {
										'valid_format' => 'waf_phase',
										'non_blank'    => 'true',
				   },
				   "disable_rules" => { 'ref'       => 'array' },
				   "redirect_url"  => { 'non_blank' => 'true', },
	};

	unless ( &existWAFSet( $set ) )
	{
		my $msg = "Requested set $set does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	if ( exists $json_obj->{ default_action }
		 and $json_obj->{ default_action } ne 'redirect' )
	{
		$json_obj->{ redirect_url } = "";
	}

	#
	if ( exists $json_obj->{ only_logging }
		 and $json_obj->{ only_logging } eq 'true' )
	{
		if ( &getWAFSetStatus( $set ) eq 'down' )
		{
			my $msg =
			  "It is necessary to start the set before configuring the 'only logging' work mode.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	my $err = &setWAFSet( $set, $json_obj );
	if ( $err )
	{
		my $msg = "Modifying the set.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $set_st = &getZapiWAFSet( $set );
	my $body = { description => $desc, params => $set_st };

	return &httpResponse( { code => 200, body => $body } );

}

#  DELETE /ipds/waf/<set>
sub delete_waf_set
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $set = shift;

	include 'Zevenet::IPDS::WAF::Config';

	my $desc = "Delete the WAF set $set";

	unless ( &existWAFSet( $set ) )
	{
		my $msg = "The WAF set $set does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my @farms = &listWAFBySet( $set );

	if ( @farms )
	{
		my $str = join ( ', ', @farms );
		my $msg = "This rule set is being used in the farm(s): $str.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	&deleteWAFSet( $set );

	if ( !&existWAFSet( $set ) )
	{
		my $msg = "The WAF set $set has been deleted successfully.";
		my $body = {
					 description => $desc,
					 success     => "true",
					 message     => $msg,
		};
		return &httpResponse( { code => 200, body => $body } );
	}
	else
	{
		my $msg = "Deleting the WAF set $set.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
}

#  POST /farms/<farm>/ipds/waf
sub add_farm_waf_set
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farm     = shift;

	require Zevenet::Farm::Core;
	include 'Zevenet::IPDS::WAF::Runtime';

	my $desc = "Apply a WAF set to a farm";

	if ( !&getFarmExists( $farm ) )
	{
		my $msg = "$farm does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $params = {
				   "name" => {
							   'valid_format' => 'waf_set_name',
							   'non_blank'    => 'true',
							   'required'     => 'true',
				   }
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	unless ( &existWAFSet( $json_obj->{ name } ) )
	{
		my $msg = "Requested set $json_obj->{name} does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( grep ( /^$json_obj->{ name }$/, &listWAFByFarm( $farm ) ) )
	{
		my $msg = "$json_obj->{ name } is already applied to $farm.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( &getFarmType( $farm ) !~ /http/ )
	{
		my $msg = "The farm must be of type HTTP.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $error = &addWAFsetToFarm( $farm, $json_obj->{ name } );
	if ( $error )
	{
		my $msg = "Applying $json_obj->{ name } to $farm";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_waf', 'reload_farm', $farm );

	my $msg = "WAF set $json_obj->{ name } was applied properly to the farm $farm.";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $msg
	};
	return &httpResponse( { code => 200, body => $body } );
}

#  DELETE /farms/<farm>/ipds/waf
sub remove_farm_waf_set
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farm = shift;
	my $set  = shift;

	include 'Zevenet::IPDS::WAF::Runtime';
	require Zevenet::Farm::Core;

	my $desc = "Unset a WAF set from a farm";

	if ( !&getFarmExists( $farm ) )
	{
		my $msg = "$farm does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( !&existWAFSet( $set ) )
	{
		my $msg = "The set $set does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( !grep ( /^$set$/, &listWAFByFarm( $farm ) ) )
	{
		my $msg = "Not found the set $set in the farm $farm.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $error = &removeWAFSetFromFarm( $farm, $set );
	if ( $error )
	{
		my $msg = "Error, removing the set $set from the farm $farm.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $msg = "The WAF set $set was removed successfully from the farm $farm.";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $msg,
	};

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_waf', 'reload_farm', $farm );

	return &httpResponse( { code => 200, body => $body } );
}

#  POST /farms/<farm>/ipds/waf/<set>/actions
sub move_farm_waf_set
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farm     = shift;
	my $set      = shift;
	my $err;

	require Zevenet::Farm::Core;
	include 'Zevenet::IPDS::WAF::Config';
	my $desc = "Move a set in farm";

	# check if the set exists
	if ( !&getFarmExists( $farm ) )
	{
		my $msg = "The farm $farm does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# check if the set exists
	if ( !&existWAFSet( $set ) )
	{
		my $msg = "The WAF set $set does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $params =
	  { "position" =>
		{ 'required' => 'true', 'non_blank' => 'true', 'valid_format' => 'integer' },
	  };

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# check if the set exists
	my @sets = &listWAFByFarm( $farm );
	my $size = scalar @sets;
	if ( !grep ( /^$set$/, @sets ) )
	{
		my $msg = "Not found the set $set in the farm $farm.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( $sets[$json_obj->{ position }] eq $set )
	{
		my $msg = "The set $set is already in the position $json_obj->{position}.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( $json_obj->{ position } >= $size )
	{
		my $ind = $size - 1;
		my $msg = "The biggest index for the farm $farm is $ind.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	$err = &moveWAFSet( $farm, $set, $json_obj->{ position } );
	if ( $err )
	{
		my $msg = "Error moving the set $set";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_waf', 'reload_farm', $farm );

	my $msg = "The set was moved properly to the position $json_obj->{ position }.";
	my $body = { description => $desc, message => $msg };

	return &httpResponse( { code => 200, body => $body } );
}

# POST /ipds/waf/WAF/actions
sub actions_waf
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $set      = shift;
	my $error;

	include 'Zevenet::IPDS::WAF::Config';
	include 'Zevenet::IPDS::WAF::Runtime';

	my $desc = "Apply an action to the set rule $set";
	my $msg  = "Error, applying the action to the set rule.";

	# check if the set exists
	if ( !&existWAFSet( $set ) )
	{
		my $msg = "The WAF set $set does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $params = {
				   "action" => {
								 'values'    => ['start', 'stop', 'restart'],
								 'non_blank' => 'true',
								 'required'  => 'true',
				   }
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# set the status
	my $rule_param->{ status } =
	  ( $json_obj->{ action } eq 'start' or $json_obj->{ action } eq 'restart' )
	  ? 'true'
	  : 'false';
	$error = &setWAFSet( $set, $rule_param );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error )
	  if $error;

	# reload the set
	$error = &reloadWAFByRule( $set );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $msg ) if $error;

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'ipds_waf', 'reload_rule', $set );

	my $status = &getWAFSetStatus( $set );
	if (    ( $status ne 'up' and $json_obj->{ action } eq 'start' )
		 or ( $status ne 'down' and $json_obj->{ action } eq 'stop' ) )
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

