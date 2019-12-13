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

include 'Zevenet::IPDS::WAF::File';

#GET /ipds/waf/files
sub list_waf_file
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $files = &listWAFFile();
	my $desc  = "List the WAF files";

	my @out = ();

	foreach my $f ( sort keys %{ $files } )
	{
		push @out, $files->{ $f };
	}

	return &httpResponse(
				   { code => 200, body => { description => $desc, params => \@out } } );
}

#  GET /ipds/waf/files/<file>
sub get_waf_file
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $file = shift;

	my $desc = "Get the WAF file $file";

	my $files = &listWAFFile();
	if ( !exists $files->{ $file } )
	{
		my $msg = "Requested file $file does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $content = &getWAFFileContent( $files->{ $file }->{ path } );
	my $out = {
				'content' => $content,
				'type'    => $files->{ $file }->{ 'type' },
	};

	my $body = { description => $desc, params => $out };

	return &httpResponse( { code => 200, body => $body } );
}

#  PUT ipds/waf/files/<file>
sub create_waf_file
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $name     = shift;

	my $desc = "Create the WAF file '$name'";
	my $params = {
				   "content" => {
								  'non_blank' => 'true',
								  'required'  => 'true',
				   },
				   "type" => {
							   'values'    => ['script', 'data'],
							   'non_blank' => 'true',
							   'required'  => 'true',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	my $file = &listWAFFile()->{ $name };
	if ( defined $file and $file->{ module } eq 'blacklist' )
	{
		my $msg = "'$name' is a blacklist file and cannot be edited from here";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	$json_obj->{ name } = $name;
	my $output = &createWAFFile( $json_obj );

	if ( !$output )
	{
		my $msg = "The file '$name' was created properly";
		my $body = {
					 description => $desc,
					 message     => $msg,
		};
		return &httpResponse( { code => 201, body => $body } );
	}
	else
	{
		my $msg = "Error, trying to create the WAF file $name";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
}

#  DELETE /ipds/waf/files/<set>
sub delete_waf_file
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $name = shift;

	my $desc = "Delete the WAF file '$name'";

	my $file = &listWAFFile()->{ $name };

	if ( not defined $file )
	{
		my $msg = "The WAF file '$name' does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}
	elsif ( $file->{ module } eq 'blacklist' )
	{
		my $msg = "'$name' is a blacklist file and cannot be deleted from here";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $sets = &checkWAFFileUsed( $name );
	if ( @{ $sets } )
	{
		my $string = join ( ', ', @{ $sets } );
		my $msg = "'$name' cannot be deleted. It is linked with the set(s): $string";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $err = &deleteWAFFile( $file->{ path } );

	if ( !$err )
	{
		my $msg = "The WAF file '$name' has been deleted successfully.";
		my $body = {
					 description => $desc,
					 success     => "true",
					 message     => $msg,
		};
		return &httpResponse( { code => 200, body => $body } );
	}
	else
	{
		my $msg = "Deleting the WAF file '$name'.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
}

1;
