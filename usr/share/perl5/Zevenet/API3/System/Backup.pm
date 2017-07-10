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

#	GET	/system/backup
sub get_backup
{
	require Zevenet::Backup;

	my $description = "Get backups";

	my $backups = &getBackup;

	&httpResponse(
		 { code => 200, body => { description => $description, params => $backups } } );
}

#	POST  /system/backup
sub create_backup
{
	my $json_obj       = shift;
	my $description    = "Create a backups";
	my @requiredParams = ( "name" );
	my $errormsg;

	$errormsg = getValidReqParams( $json_obj, \@requiredParams );
	if ( &getExistsBackup( $json_obj->{ 'name' } ) )
	{
		$errormsg = "A backup already exists with this name.";
	}
	elsif ( !&getValidFormat( 'backup', $json_obj->{ 'name' } ) )
	{
		$errormsg = "The backup name has invalid characters.";
	}
	else
	{
		$errormsg = &createBackup( $json_obj->{ 'name' } );
		if ( !$errormsg )
		{
			$errormsg = "Backup $json_obj->{ 'name' } was created successful.";
			my $body = {
						 description => $description,
						 params      => $json_obj->{ 'name' },
						 message     => $errormsg
			};
			&httpResponse( { code => 200, body => $body } );
		}
		else
		{
			$errormsg = "Error creating backup.";
		}
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

#	GET	/system/backup/BACKUP
sub download_backup
{
	my $backup      = shift;
	my $description = "Download a backup";
	my $errormsg    = "$backup was download successful.";

	if ( !&getExistsBackup( $backup ) )
	{
		$errormsg = "Not found $backup backup.";
		my $body =
		  { description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 404, body => $body } );
	}
	else
	{
# Download function ends communication if itself finishes successful. It is not necessary send "200 OK" msg
		$errormsg = &downloadBackup( $backup );
		if ( $errormsg )
		{
			$errormsg = "Error, downloading backup.";
		}
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 404, body => $body } );
}

#	PUT	/system/backup/BACKUP
sub upload_backup
{
	my $upload_filehandle = shift;
	my $name              = shift;

	my $description = "Upload a backup";
	my $errormsg;

	if ( !$upload_filehandle || !$name )
	{
		$errormsg = "It's necessary add a data binary file.";
	}
	elsif ( &getExistsBackup( $name ) )
	{
		$errormsg = "A backup already exists with this name.";
	}
	elsif ( !&getValidFormat( 'backup', $name ) )
	{
		$errormsg = "The backup name has invalid characters.";
	}
	else
	{
		$errormsg = &uploadBackup( $name, $upload_filehandle );
		if ( !$errormsg )
		{
			$errormsg = "Backup $name was created successful.";
			my $body =
			  { description => $description, params => $name, message => $errormsg };
			&httpResponse( { code => 200, body => $body } );
		}
		else
		{
			$errormsg = "Error creating backup.";
		}
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

#	DELETE /system/backup/BACKUP
sub del_backup
{
	my $backup = shift;
	my $errormsg;
	my $description = "Delete backup $backup'";

	if ( !&getExistsBackup( $backup ) )
	{
		$errormsg = "$backup doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};
		&httpResponse( { code => 404, body => $body } );
	}
	else
	{
		$errormsg = &deleteBackup( $backup );
		if ( !$errormsg )
		{
			$errormsg = "The list $backup has been deleted successful.";
			my $body = {
						 description => $description,
						 success     => "true",
						 message     => $errormsg,
			};
			&httpResponse( { code => 200, body => $body } );
		}
		else
		{
			$errormsg = "There was a error deleting list $backup.";
		}
	}
	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg,
	};
	&httpResponse( { code => 400, body => $body } );
}

#	POST /system/backup/BACKUP/actions
sub apply_backup
{
	my $json_obj    = shift;
	my $backup      = shift;
	my $description = "Apply a backup to the system";

	my @allowParams = ( "action" );
	my $errormsg = &getValidOptParams( $json_obj, \@allowParams );
	if ( !$errormsg )
	{
		if ( !&getExistsBackup( $backup ) )
		{
			$errormsg = "Not found $backup backup.";
			my $body =
			  { description => $description, error => "true", message => $errormsg };
			&httpResponse( { code => 404, body => $body } );
		}
		elsif ( !&getValidFormat( 'backup_action', $json_obj->{ 'action' } ) )
		{
			$errormsg = "Error, it's necessary add a valid action";
		}
		else
		{
			$errormsg = &applyBackup( $backup );
			if ( !$errormsg )
			{
				&httpResponse(
					{ code => 200, body => { description => $description, params => $json_obj } } );
			}
			else
			{
				$errormsg = "There was a error applying the backup.";
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

1;
