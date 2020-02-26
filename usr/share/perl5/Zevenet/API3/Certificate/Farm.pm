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
my $eload;
if ( eval { require Zevenet::ELoad; } )
{
	$eload = 1;
}

# POST /farms/FARM/certificates (Add certificate to farm)
sub add_farm_certificate    # ( $json_obj, $farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;

	my $description = "Add certificate";

	# Check that the farm exists
	require Zevenet::Farm::Core;
	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		my $errormsg = "Farm not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	my $configdir   = &getGlobalConfiguration( 'certdir' );
	my $cert_pem_re = &getValidFormat( 'cert_pem' );

	unless ( -f $configdir . "/" . $json_obj->{ file }
			 && &getValidFormat( 'cert_pem', $json_obj->{ file } ) )
	{
		&zenlog(
			 "Error trying to add a certificate to the SNI list, invalid certificate name.",
			 "error", "LSLB"
		);

		# Error
		my $errormsg = "Invalid certificate name, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# FIXME: Show error if the certificate is already in the list
	include 'Zevenet::Farm::HTTP::HTTPS::Ext';
	my $status = &setFarmCertificateSNI( $json_obj->{ file }, $farmname );

	if ( $status == 0 )
	{
		&zenlog( "Success, trying to add a certificate to the SNI list.",
				 "info", "LSLB" );

		# Success
		my $message =
		  "The certificate $json_obj->{file} has been added to the SNI list of farm $farmname, you need restart the farm to apply";

		my $body = {
					 description => $description,
					 success     => "true",
					 message     => $message
		};

		require Zevenet::Farm::Base;
		if ( &getFarmStatus( $farmname ) eq 'up' )
		{
			require Zevenet::Farm::Action;
			if ( &getGlobalConfiguration( 'proxy_ng' ) ne 'true' )
			{
				&setFarmRestart( $farmname );
				$body->{ status } = 'needed restart';
			}
			else
			{
				&runFarmReload( $farmname );
				&eload(
						module => 'Zevenet::Cluster',
						func   => 'runZClusterRemoteManager',
						args   => ['farm', 'reload', $farmname],
				) if ( $eload );
			}
		}
		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		&zenlog(
			"Error trying to add a certificate to the SNI list, it's not possible to add the certificate.",
			"error", "LSLB"
		);

		# Error
		my $errormsg =
		  "It's not possible to add the certificate with name $json_obj->{file} for the $farmname farm";

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

# DELETE /farms/FARM/certificates/CERTIFICATE
sub delete_farm_certificate    # ( $farmname, $certfilename )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname     = shift;
	my $certfilename = shift;

	my $description = "Delete farm certificate";

	# Check that the farm exists
	require Zevenet::Farm::Core;
	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	if ( $certfilename && &getValidFormat( 'cert_pem', $certfilename ) )
	{
		include 'Zevenet::Farm::HTTP::HTTPS::Ext';
		my $status = &setFarmDeleteCertNameSNI( $certfilename, $farmname );

		if ( $status == 0 )
		{
			&zenlog( "Success, certificate deleted from the SNI list.", "info", "LSLB" );

			# Success
			my $message = "The Certificate $certfilename has been deleted";
			my $body = {
						 description => $description,
						 success     => "true",
						 message     => $message
			};

			require Zevenet::Farm::Base;
			if ( &getFarmStatus( $farmname ) eq 'up' )
			{
				require Zevenet::Farm::Action;
				if ( &getGlobalConfiguration( 'proxy_ng' ) ne 'true' )
				{
					&setFarmRestart( $farmname );
					$body->{ status } = 'needed restart';
				}
				else
				{
					&runFarmReload( $farmname );
					&eload(
							module => 'Zevenet::Cluster',
							func   => 'runZClusterRemoteManager',
							args   => ['farm', 'reload', $farmname],
					) if ( $eload );
				}
			}
			&httpResponse( { code => 200, body => $body } );
		}

		if ( $status == -1 )
		{
			&zenlog(
				"Error trying to delete a certificate to the SNI list, it's not possible to delete the certificate.",
				" error",
				"LSLB"
			);

			# Error
			my $errormsg =
			  "It isn't possible to delete the selected certificate $certfilename from the SNI list";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

		if ( $status == 1 )
		{
			&zenlog(
				"Error trying to delete the certificates from the SNI list, it's not possible to delete all certificates, at least one is required for HTTPS.",
				"error", "LSLB"
			);

			# Error
			my $errormsg =
			  "It isn't possible to delete all certificates, at least one is required for HTTPS profiles";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}
	}
	else
	{
		&zenlog(
			"Error trying to delete a certificate from the SNI list, invalid certificate id.",
			"error", "LSLB"
		);

		# Error
		my $errormsg = "Invalid certificate id, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

1;
