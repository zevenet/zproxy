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

use Zevenet::Alias;

# DELETE /alias/(alias_type)/(alias_re)
sub delete_alias
{
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
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	if ( $type eq 'interface' )
	{
		require Zevenet::Net::Interface;
		if ( !&getInterfaceConfig( $id ) )
		{
			my $msg = "The interfacace $id has not been found";
			return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
		}
	}

	my $message;
	if ( &getAlias( $type, $id ) )
	{
		$message = "Alias for $id has been updated successfully";
	}
	else { $message = "Alias for $id has been created successfully"; }

	&setAlias( $type, $id, $json_obj->{ alias } );

	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $message
	};

	return &httpResponse( { code => 200, body => $body } );
}

# GET /alias/(alias_type)
sub get_by_type
{
	my $type = shift;
	my $desc = "List the alias";

	my $alias_list = &getAlias( $type );

	my $body = {
				 description => $desc,
				 params      => $alias_list
	};

	return &httpResponse( { code => 200, body => $body } );
}

1;
