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

# PUT /aws/ssh
sub modify_ssh    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $type = $json_obj->{ type } // 'add';

	my $desc = "Modify the SSH configuration for AWS";

	my $params = {
				   "remote_ip" => {
									'non_blank'    => 'true',
									'valid_format' => 'ssh_listen',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	include 'Zevenet::Aws';
	my $error = &setSshForCluster( $json_obj->{ remote_ip }, $type );
	if ( $error )
	{
		my $msg = "There was a error modifying ssh.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	return &httpResponse(
			   { code => 200, body => { description => $desc, params => $json_obj } } );
}

#GET /aws/credentials
sub get_credentials
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $desc = "Retrieve the AWS credentials";

	include 'Zevenet::Aws';
	my %file_credentials = %{ &getCredentials( 'credentials' ) };
	my %file_config      = %{ &getCredentials( 'config' ) };

	my %credentials = (
						access_key => '',
						secret_key => '',
						region     => ''
	);
	if ( %file_credentials && %file_config )
	{
		$credentials{ access_key } =
		  $file_credentials{ default }{ aws_access_key_id };
		$credentials{ secret_key } = '********************'
		  if $file_credentials{ default }{ aws_secret_access_key };
		$credentials{ region } = $file_config{ default }{ region };
	}

	return &httpResponse(
		   { code => 200, body => { description => $desc, params => \%credentials } } );
}

#POST /aws/credentials
sub modify_credentials
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	my $desc = "Modify the AWS credentials";
	my $params = {
				   "access_key" => {
									 'non_blank' => 'true'
				   },
				   "secret_key" => {
									 'non_blank' => 'true'
				   },
				   "region" => {
								 'non_blank' => 'true'
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	include 'Zevenet::Aws';
	my $error = &setCredentials( $json_obj );

	if ( $error )
	{
		$error_msg = 'There was an error to configure the AWS credentials';
		return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg );
	}

	return &httpResponse(
			   { code => 200, body => { description => $desc, params => $json_obj } } );
}

1;

