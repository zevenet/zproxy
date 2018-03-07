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

use v5.14;
use strict;

use Zevenet::Log;

=begin nd
Function: getGlobalConfiguration

	Set the value of a configuration variable.

Parameters:
	parameter - Name of the global configuration variable. Optional.

Returns:
	scalar - Value of the configuration variable when a variable name is passed as an argument.
	scalar - Hash reference to all global configuration variables when no argument is passed.

See Also:
	Widely used.
=cut

sub getGlobalConfiguration
{
	my $parameter = shift;

	my $global_conf_filepath = "/usr/local/zevenet/config/global.conf";
	my $global_conf;

	open ( my $global_conf_file, '<', $global_conf_filepath );

	if ( !$global_conf_file )
	{
		my $msg = "Could not open $global_conf_filepath: $!";

		&zenlog( $msg, "error", "SYSTEM" );
		die $msg;
	}

	while ( my $conf_line = <$global_conf_file> )
	{
		next if $conf_line !~ /^\$/;

		# extract variable name and value
		$conf_line =~ /\$(\w+)\s*=\s*(?:"(.*)"|\'(.*)\');\s*$/;
		my $var_name  = $1;
		my $var_value = $2;

		# if the var value contains any variable
		if ( $var_value =~ /\$/ )
		{
			# replace every variable used in the $var_value by its content
			foreach my $var ( $var_value =~ /\$(\w+)/g )
			{
				$var_value =~ s/\$$var/$global_conf->{ $var }/;
			}
		}

		# early finish if the requested paremeter is found
		return $var_value if $parameter && $parameter eq $var_name;

		$global_conf->{ $var_name } = $var_value;
	}

	close $global_conf_file;

	return eval { $global_conf->{ $parameter } } if $parameter;
	return $global_conf;
}

=begin nd
Function: setGlobalConfiguration

	Set a value to a configuration variable

Parameters:
	param - Configuration variable name.
	value - New value to be set on the configuration variable.

Returns:
	scalar - 0 on success, or -1 if the variable was not found.

Bugs:
	Control file handling errors.

See Also:
	<applySnmpChanges>

	Zapi v3: <set_ntp>
=cut

sub setGlobalConfiguration    # ( parameter, value )
{
	my ( $param, $value ) = @_;

	my $global_conf_file = &getGlobalConfiguration( 'globalcfg' );
	my $output           = -1;

	require Tie::File;
	tie my @global_hf, 'Tie::File', $global_conf_file;

	foreach my $line ( @global_hf )
	{
		if ( $line =~ /^\$$param\s*=/ )
		{
			$line   = "\$$param = \"$value\";";
			$output = 0;
		}
	}
	untie @global_hf;

	return $output;
}

=begin nd
Function: setConfigStr2Arr

	Put a list of string parameters as array references

Parameters:
	object - reference to a hash
	parameters - list of parameters to change from string to array

Returns:
	hash ref - Object updated

=cut

sub setConfigStr2Arr
{
	my $obj        = shift;
	my $param_list = shift;

	foreach my $param_name ( @{ $param_list } )
	{
		my @list = ();

		# split parameter if it is not a blank string
		@list = sort split ( ' ', $obj->{ $param_name } )
		  if ( $obj->{ $param_name } );
		$obj->{ $param_name } = \@list;
	}

	return $obj;
}

=begin nd
Function: getTiny

	Get a Config::Tiny object from a file name.

Parameters:
	file_path - Path to file.

Returns:
	scalar - reference to Config::Tiny object, or undef on failure.

See Also:

=cut

sub getTiny
{
	my $file_path = shift;

	if ( !-f $file_path )
	{
		open my $fi, '>', $file_path;
		if ( $fi )
		{
			&zenlog( "The file was created $file_path", "info" );
		}
		else
		{
			&zenlog( "Could not open file $file_path: $!", "error" );
			return undef;
		}
		close $fi;
	}

	require Config::Tiny;

	# returns object on success or undef on error.
	return Config::Tiny->read( $file_path );
}

=begin nd
Function: setTinyObj

	Save a change in a config file. The file is locker before than applying the changes
	This function has 2 behaviors:
	it can receives a hash ref to save a struct
	or it can receive a key and parameter to replace a value

Parameters:
	path - Tiny conguration file where to apply the change
	object - Group to apply the change
	key - parameter to change or struct ref
	value - new value for the parameter
	action - This is a optional parameter. The possible values are: "add" to add
	a item to a list, or "del" to delete a item from a list

Returns:
	Integer -  Error code: 0 on success or other value on failure

=cut

sub setTinyObj
{
	my ( $path, $object, $key, $value, $action ) = @_;

	unless ( $object )
	{
		&zenlog( "Object not defined trying to save it in file $path" );
		return;
	}

	if ( !-f $path )
	{
		open my $fi, '>', $path;
		if ( $fi )
		{
			&zenlog( "The file was created $path", "info" );
		}
		else
		{
			&zenlog( "Could not open file $path: $!", "error" );
			return undef;
		}
		close $fi;
	}

	&zenlog( "Modify $object from $path", "debug2" );

	require Zevenet::Lock;
	my $lock_file = &getLockFile( $path );
	my $lock_fd   = &lockfile( $lock_file );

	my $fileHandle = Config::Tiny->read( $path );

	unless ( $fileHandle )
	{
		&zenlog( "Could not open file $path: $Config::Tiny::errstr" );
		return -1;
	}

	# save all struct
	if ( ref $key )
	{
		foreach my $param ( keys %{ $key } )
		{
			if ( ref $key->{ $param } eq 'ARRAY' )
			{
				$key->{ $param } = join ( ' ', @{ $key->{ $param } } );
			}
			$fileHandle->{ $object }->{ $param } = $key->{ $param };
		}

		#~ $fileHandle->{ $object } = $key;
	}

	# save a parameter
	else
	{
		if ( 'add' eq $action )
		{
			$fileHandle->{ $object }->{ $key } .= " $value";
		}
		elsif ( 'del' eq $action )
		{
			$fileHandle->{ $object }->{ $key } =~ s/(^| )$value( |$)/ /;
		}
		else
		{
			$fileHandle->{ $object }->{ $key } = $value;
		}
	}

	my $success = $fileHandle->write( $path );
	&unlockfile( $lock_fd );

	return ($success)? 0:1;
}

=begin nd
Function: delTinyObj

	It deletes a object of a tiny file. The tiny file is locked before than set the configuration

Parameters:
	object - Group name
	path - Tiny file where the object will be deleted

Returns:
	Integer -  Error code: 0 on success or other value on failure

=cut

sub delTinyObj
{
	my $path   = shift;
	my $object = shift;

	require Zevenet::Lock;
	my $lock_file = &getLockFile( $path );
	my $lock_fd   = &lockfile( $lock_file );

	my $fileHandle = Config::Tiny->read( $path );
	delete $fileHandle->{ $object };
	my $error = $fileHandle->write( $path );

	&unlockfile( $lock_fd );

	&zenlog( "Delete $object from $path", "debug2" );

	return $error;
}

1;
