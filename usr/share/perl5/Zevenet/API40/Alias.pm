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

use Zevenet::API40::HTTP;
use Zevenet::User;

include 'Zevenet::Alias';

# DELETE /alias/(alias_type)/(alias_re)
sub delete_alias
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $type = shift;
	my $id   = shift;
	my $desc = "Delete an alias";

	unless ( &getAlias( $type, $id ) )
	{
		my $msg = "Alias does not found";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	&delAlias( $type, $id );

	my $message = "The alias has been deleted.";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $message,
	};

	return &httpResponse( { code => 200, body => $body } );
}

# PUT /alias/(alias_type)/(alias_re)
sub set_alias
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $type     = shift;
	my $id       = shift;
	my $desc     = "Set an alias";

	my $params = {
				   "alias" => {
								'valid_format' => 'alias_name',
								'non_blank'    => 'true',
								'required'     => 'true',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	unless ( ( $type eq 'interface' and &getValidFormat( 'alias_interface', $id ) )
			 or ( $type eq 'backend' and &getValidFormat( 'alias_backend', $id ) ) )
	{
		my $msg = "The id $id is not correct";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $alias_list = &getAlias( $type );
	foreach my $key ( keys %{ $alias_list } )
	{
		if ( $alias_list->{ $key } eq $json_obj->{ alias } )
		{
			my $msg = "The alias $json_obj->{ alias } already exists in the $type $key.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => "Alias for $id has been updated successfully"
	};

	if ( !exists $alias_list->{ $id } )
	{
		$body->{ message } = "Alias for $id has been created successfully";
	}

	&setAlias( $type, $id, $json_obj->{ alias } );

	return &httpResponse( { code => 200, body => $body } );
}

# POST /alias/(alias_type)
sub add_alias
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $type     = shift;
	my $desc     = "Add an alias";

	my $params = {
				   "alias" => {
								'valid_format' => 'alias_name',
								'non_blank'    => 'true',
								'required'     => 'true',
				   },
	};

	if ( ( $type eq 'interface' ) or ( $type eq 'backend' ) )
	{
		$params->{ 'id' } = {
							  'valid_format' => 'alias_' . $type,
							  'non_blank'    => 'true',
							  'required'     => 'true',
		};
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	my $id = $json_obj->{ 'id' };

	if ( $type eq 'interface' )
	{
		require Zevenet::Net::Interface;
		unless ( grep ( /^$id$/, &getInterfaceList() ) )
		{
			my $msg = "The interfacace $id has not been found";
			return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
		}
	}

	my $alias_list = &getAlias( $type );

	foreach my $key ( keys %{ $alias_list } )
	{
		if ( $alias_list->{ $key } eq $json_obj->{ alias } )
		{
			my $msg = "The alias $json_obj->{ alias } already exists in the $type $key.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	&setAlias( $type, $id, $json_obj->{ alias } );

	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => "Alias for $id has been created successfully"
	};
	if ( exists $alias_list->{ $id } )
	{
		$body->{ message } = "Alias for $id has been updated successfully";
	}

	return &httpResponse( { code => 200, body => $body } );
}

# GET /alias/(alias_type)
sub get_by_type
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $type = shift;
	my $desc = "List the aliases";

	my $alias_list   = &getAlias( $type );
	my $user         = &getUser();
	my @others_alias = [];

	if ( $type eq 'interface' and $user ne 'root' )
	{
		my @virtual_alias =
		  map { { name => $_, alias => $alias_list->{ $_ } } }
		  grep { /:/ } keys %{ $alias_list };
		@others_alias =
		  map { { name => $_, alias => $alias_list->{ $_ } } }
		  grep { !/:/ } keys %{ $alias_list };

		include 'Zevenet::RBAC::Group::Core';
		my @out2 = @{ &getRBACUserSet( 'interfaces', \@virtual_alias ) };
		push ( @others_alias, @out2 );
	}
	else
	{
		@others_alias =
		  map { { name => $_, alias => $alias_list->{ $_ } } } keys %{ $alias_list };
	}

	my @out = map { { id => $_->{ name }, alias => $_->{ alias } } } @others_alias;
	my $body = {
				 description => $desc,
				 params      => \@out
	};

	return &httpResponse( { code => 200, body => $body } );
}

1;

