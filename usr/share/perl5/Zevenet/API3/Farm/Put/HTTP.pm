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

# PUT /farms/<farmname> Modify a http|https Farm
sub modify_http_farm    # ( $json_obj, $farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;

	include 'Zevenet::IPDS::Base';

	# flag to reset IPDS rules when the farm changes the name.
	my $farmname_old;
	my $ipds = &getIPDSfarmsRules_zapiv3( $farmname );

	# Flags
	my $reload_flag  = "false";
	my $restart_flag = "false";
	my $error        = "false";
	my $flag         = "false";

	my $status;
	my $zapierror;

	# Check that the farm exists
	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exist.";
		my $body = {
					 description => "Modify farm",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	&runIPDSStopByFarm( $farmname );

	# Get current vip & vport
	my $vip   = &getFarmVip( "vip",  $farmname );
	my $vport = &getFarmVip( "vipp", $farmname );
	my $changedname = "false";

	######## Functions

	# Modify Farm's Name
	if ( exists ( $json_obj->{ newfarmname } ) )
	{
		unless ( &getFarmStatus( $farmname ) eq 'down' )
		{
			&zenlog(
				"Error trying to modify a http farm $farmname, cannot change the farm name while it is running",
				"error", "LSLB"
			);

			my $errormsg = 'Cannot change the farm name while the farm is running';

			my $body = {
						 description => "Modify farm",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

		if ( $json_obj->{ newfarmname } =~ /^$/ )
		{
			$error = "true";
			$zapierror =
			  "Error trying to modify a http farm $farmname, invalid new farm name, it can't be blank.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
		else
		{
			#Check if farmname has correct characters (letters, numbers and hyphens)
			if ( $json_obj->{ newfarmname } =~ /^[a-zA-Z0-9\-]*$/ )
			{
				if ( $json_obj->{ newfarmname } ne $farmname )
				{
					#Check if the new farm's name alredy exists
					my $newffile = &getFarmFile( $json_obj->{ newfarmname } );
					if ( $newffile != -1 )
					{
						$error = "true";
						$zapierror =
						  "Error trying to modify a http farm $farmname, the farm $json_obj->{newfarmname} already exists, try another name.";
						&zenlog( "$zapierror", "error", "LSLB" );
					}
					else
					{
						my $oldfstat = &runFarmStop( $farmname, "true" );
						if ( $oldfstat != 0 )
						{
							$error = "true";
							$zapierror =
							  "Error trying to modify a http farm $farmname,the farm is not disabled, are you sure it's running?";
							&zenlog( "$zapierror", "error", "LSLB" );
						}
						else
						{
							#Change farm name
							my $fnchange = &setNewFarmName( $farmname, $json_obj->{ newfarmname } );
							$changedname = "true";
							if ( $fnchange == -1 )
							{
								&error = "true";
								$zapierror =
								  "Error trying to modify a http farm $farmname, the name of the farm can't be modified, delete the farm and create a new one.";
								&zenlog( "$zapierror", "error", "LSLB" );
							}
							elsif ( $fnchange == -2 )
							{
								$error = "true";
								$zapierror =
								  "Error trying to modify a http farm $farmname, invalid new far mname, the new name can't be empty.";
								&zenlog( "$zapierror", "error", "LSLB" );
							}
							else
							{
								$farmname_old = $farmname;
								$farmname     = $json_obj->{ newfarmname };
							}
						}
					}
				}
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify a http farm $farmname, invalid new farm name.";
				&zenlog( "$zapierror", "error", "LSLB" );
			}
		}
	}

	# Modify Backend Connection Timeout
	if ( exists ( $json_obj->{ contimeout } ) )
	{
		if ( $json_obj->{ contimeout } =~ /^$/ )
		{
			$error = "true";
			$zapierror =
			  "Error trying to modify a http farm $farmname, invalid connection timeout, can't be blank.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
		elsif ( $json_obj->{ contimeout } =~ /^\d+$/ )
		{
			my $status = &setFarmConnTO( $json_obj->{ contimeout }, $farmname );
			if ( $status != -1 )
			{
				$restart_flag = "true";
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify a http farm $farmname, some errors happened trying to modify the connection timeout.";
				&zenlog( "$zapierror", "error", "LSLB" );
			}
		}
		else
		{
			$error = "true";
			$zapierror = (
				  "Error trying to modify a http farm $farmname, invalid connection timeout." );
			&zenlog( "$zapierror", "error", "LSLB" );
		}
	}

	# Modify Backend Respone Timeout
	if ( exists ( $json_obj->{ restimeout } ) )
	{
		if ( $json_obj->{ restimeout } =~ /^$/ )
		{
			$error = "true";
			$zapierror =
			  "Error, trying to modify a http farm $farmname, invalid response timeout, can't be blank.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
		elsif ( $json_obj->{ restimeout } =~ /^\d+$/ )
		{
			$status = &setFarmTimeout( $json_obj->{ restimeout }, $farmname );
			if ( $status != -1 )
			{
				$restart_flag = "true";
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error, trying to modify a http farm $farmname, some errors happened trying to modify the response timeout.";
				&zenlog( "$zapierror", "error", "LSLB" );
			}
		}
		else
		{
			$error = "true";
			$zapierror =
			  "Error trying to modify a http farm $farmname, invalid response timeout.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
	}

	# Modify Frequency To Check Resurrected Backends
	if ( exists ( $json_obj->{ resurrectime } ) )
	{
		if ( $json_obj->{ resurrectime } =~ /^$/ )
		{
			$error = "true";
			$zapierror =
			  "Error trying to modify a http farm $farmname, invalid resurrected time, can't be blank.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
		elsif ( $json_obj->{ resurrectime } =~ /^\d+$/ )
		{
			$status = &setFarmBlacklistTime( $json_obj->{ resurrectime }, $farmname );
			if ( $status != -1 )
			{
				$restart_flag = "true";
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify a http farm $farmname, some errors happened trying to modify the resurrected time.";
				&zenlog( "$zapierror", "error", "LSLB" );
			}
		}
		else
		{
			$error = "true";
			$zapierror =
			  "Error trying to modify a http farm $farmname, invalid resurrected time.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
	}

	# Modify Client Request Timeout
	if ( exists ( $json_obj->{ reqtimeout } ) )
	{
		if ( $json_obj->{ reqtimeout } =~ /^$/ )
		{
			$error = "true";
			$zapierror =
			  "Error, trying to modify a http farm $farmname, invalid request timeout, can't be blank.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
		elsif ( $json_obj->{ reqtimeout } =~ /^\d+$/ )
		{
			$status = &setFarmClientTimeout( $json_obj->{ reqtimeout }, $farmname );
			if ( $status != -1 )
			{
				$restart_flag = "true";
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify a http farm $farmname, some errors happened trying to modify the request timeout.";
				&zenlog( "$zapierror", "error", "LSLB" );
			}
		}
		else
		{
			$error = "true";
			$zapierror =
			  "Error trying to modify a http farm $farmname, invalid request timeout.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
	}

	# Modify Rewrite Location Headers
	if ( exists ( $json_obj->{ rewritelocation } ) )
	{
		if ( $json_obj->{ rewritelocation } =~ /^$/ )
		{
			$error = "true";
			$zapierror =
			  "Error, trying to modify a http farm $farmname, invalid rewrite location, can't be blank.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
		elsif (
				$json_obj->{ rewritelocation } =~ /^disabled|enabled|enabled-backends$/ )
		{
			my $rewritelocation = 0;
			if ( $json_obj->{ rewritelocation } eq "disabled" )
			{
				$rewritelocation = 0;
			}
			elsif ( $json_obj->{ rewritelocation } eq "enabled" )
			{
				$rewritelocation = 1;
			}
			elsif ( $json_obj->{ rewritelocation } eq "enabled-backends" )
			{
				$rewritelocation = 2;
			}
			my $status1 = &setFarmRewriteL( $farmname, $rewritelocation );
			if ( $status1 != -1 )
			{
				$restart_flag = "true";
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify a http farm $farmname, some errors happened trying to modify the rewrite location.";
				&zenlog( "$zapierror", "error", "LSLB" );
			}
		}
		else
		{
			$error = "true";
			$zapierror =
			  "Error trying to modify a http farm $farmname, invalid rewrite location.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
	}

	# Modify HTTP Verbs Accepted
	if ( exists ( $json_obj->{ httpverb } ) )
	{
		if ( $json_obj->{ httpverb } =~ /^$/ )
		{
			$error = "true";
			$zapierror =
			  "Error trying to modify a http farm $farmname, invalid HTTP verbs, can't be blank.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
		elsif ( $json_obj->{ httpverb } =~
			/^standardHTTP|extendedHTTP|standardWebDAV|MSextWebDAV|MSRPCext|optionsHTTP$/ )
		{
			my $httpverb = 0;
			if ( $json_obj->{ httpverb } eq "standardHTTP" )
			{
				$httpverb = 0;
			}
			elsif ( $json_obj->{ httpverb } eq "extendedHTTP" )
			{
				$httpverb = 1;
			}
			elsif ( $json_obj->{ httpverb } eq "standardWebDAV" )
			{
				$httpverb = 2;
			}
			elsif ( $json_obj->{ httpverb } eq "MSextWebDAV" )
			{
				$httpverb = 3;
			}
			elsif ( $json_obj->{ httpverb } eq "MSRPCext" )
			{
				$httpverb = 4;
			}
			elsif ( $json_obj->{ httpverb } eq "optionsHTTP" )
			{
				$httpverb = 5;
			}
			$status = &setFarmHttpVerb( $httpverb, $farmname );
			if ( $status != -1 )
			{
				$restart_flag = "true";
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify a http farm $farmname, some errors happened trying to modify the HTTP verbs.";
				&zenlog( "$zapierror", "error", "LSLB" );
			}
		}
		else
		{
			$error     = "true";
			$zapierror = "Error trying to modify a http farm $farmname, invalid HTTP verb.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
	}

	#Modify Error 414
	if ( exists ( $json_obj->{ error414 } ) )
	{
		$status = &setFarmErr( $farmname, $json_obj->{ error414 }, "414" );
		if ( $status != -1 )
		{
			$restart_flag = "true";
		}
		else
		{
			$error = "true";
			$zapierror =
			  "Error trying to modify a http farm $farmname, some errors happened trying to modify the error 414 message.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
	}

	#Modify Error 500
	if ( exists ( $json_obj->{ error500 } ) )
	{
		$status = &setFarmErr( $farmname, $json_obj->{ error500 }, "500" );
		if ( $status != -1 )
		{
			$restart_flag = "true";
		}
		else
		{
			$error = "true";
			$zapierror =
			  "Error trying to modify a http farm $farmname, some errors happened trying to modify the error 500 message.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
	}

	#Modify Error 501
	if ( exists ( $json_obj->{ error501 } ) )
	{
		$status = &setFarmErr( $farmname, $json_obj->{ error501 }, "501" );
		if ( $status != -1 )
		{
			$restart_flag = "true";
		}
		else
		{
			$error = "true";
			$zapierror =
			  "Error trying to modify a http farm $farmname, some errors happened trying to modify the error 501 message.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
	}

	#Modify Error 503
	if ( exists ( $json_obj->{ error503 } ) )
	{
		$status = &setFarmErr( $farmname, $json_obj->{ error503 }, "503" );
		if ( $status != -1 )
		{
			$restart_flag = "true";
		}
		else
		{
			$error = "true";
			$zapierror =
			  "Error trying to modify a http farm $farmname, some errors happened trying to modify the error 503 message.";
			&zenlog( " $zapierror", "error", "LSLB" );
		}
	}

	# Modify Farm Listener
	if ( exists ( $json_obj->{ listener } ) )
	{
		if ( $json_obj->{ listener } =~ /^$/ )
		{
			$error = "true";
			$zapierror =
			  "Error trying to modify a http farm $farmname, invalid listener, can't be blank.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
		elsif ( $json_obj->{ listener } =~ /^http|https$/ )
		{
			$status = &setFarmListen( $farmname, $json_obj->{ listener } );
			if ( $status != -1 )
			{
				$restart_flag = "true";
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify a http farm $farmname, some errors happened trying to modify the listener.";
				&zenlog( "$zapierror", "error", "LSLB" );
			}
		}
		else
		{
			$error     = "true";
			$zapierror = "Error trying to modify a http farm $farmname, invalid listener.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
	}

	# Modify HTTPS Params
	my $farmtype = &getFarmType( $farmname );
	if ( $farmtype eq "https" )
	{
		require Zevenet::Farm::HTTP::HTTPS;

		# Modify Ciphers
		if ( exists ( $json_obj->{ ciphers } ) )
		{
			if ( $json_obj->{ ciphers } =~ /^$/ )
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify a http farm $farmname, invalid ciphers, can't be blank."
				  & zenlog( "$zapierror", "error", "LSLB" );
			}
			elsif ( $json_obj->{ ciphers } =~ /^all|highsecurity|customsecurity$/ )
			{
				my $ciphers;
				if ( $json_obj->{ ciphers } eq "all" )
				{
					$ciphers = "cipherglobal";
					$flag    = "true";
				}
				elsif ( $json_obj->{ ciphers } eq "customsecurity" )
				{
					$ciphers = "ciphercustom";
				}
				elsif ( $json_obj->{ ciphers } eq "highsecurity" )
				{
					$ciphers = "cipherpci";
				}
				$status = &setFarmCipherList( $farmname, $ciphers );
				if ( $status != -1 )
				{
					$restart_flag = "true";
				}
				else
				{
					$error = "true";
					$zapierror =
					  "Error trying to modify a http farm $farmname, some errors happened trying to modify the ciphers.";
					&zenlog( "$zapierror", "error", "LSLB" );
				}
			}
			else
			{
				$error     = "true";
				$zapierror = "Error trying to modify a http farm $farmname, invalid ciphers.";
				&zenlog( "$zapierror", "error", "LSLB" );
			}
		}

		# Get ciphers value
		my $cipher = &getFarmCipherSet( $farmname );
		chomp ( $cipher );

		if ( $flag eq "false" )
		{
			if ( $cipher eq "ciphercustom" )
			{
				# Modify Customized Ciphers
				if ( exists ( $json_obj->{ cipherc } ) )
				{
					if ( $json_obj->{ cipherc } =~ /^$/ )
					{
						$error = "true";
						$zapierror =
						  "Error trying to modify a http farm $farmname, invalid cipherc, can't be blank.";
						&zenlog( "$zapierror", "error", "LSLB" );
					}
					else
					{
						my $cipherc = $json_obj->{ cipherc };
						$cipherc =~ s/\ //g;

						if ( $cipherc eq "" )
						{
							$error = "true";
							$zapierror =
							  "Error trying to modify a http farm $farmname, invalid cipherc, can't be blank.";
							&zenlog( "$zapierror", "error", "LSLB" );
						}
						else
						{
							$status = &setFarmCipherList( $farmname, $cipher, $cipherc );
							if ( $status != -1 )
							{
								$restart_flag = "true";
							}
							else
							{
								$error = "true";
								$zapierror =
								  "Error trying to modify a http farm $farmname, some errors happened trying to modify the custom cipher.";
								&zenlog( "$zapierror", "error", "LSLB" );
							}
						}
					}
				}
			}
		}

		# Add Certificate to SNI list
		if ( exists ( $json_obj->{ certname } ) )
		{
			include 'Zevenet::Farm::HTTP::HTTPS::Ext';

			$status = &setFarmCertificateSNI( $json_obj->{ certname }, $farmname );
			if ( $status != -1 )
			{
				$restart_flag = "true";
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify a http farm $farmname, some errors happened trying to modify the certificate name.";
				&zenlog( "$zapierror", "error", "LSLB" );
			}
		}
	}
	else
	{
		if (    exists ( $json_obj->{ ciphers } )
			 || exists ( $json_obj->{ cipherc } )
			 || exists ( $json_obj->{ certname } ) )
		{
			# Error
			my $errormsg =
			  "To modify ciphers, chiperc or certname, listener must be https.";
			my $body = {
						 description => "Modify farm $farmname",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}
	}

	# Modify only vip
	if ( exists ( $json_obj->{ vip } ) && !exists ( $json_obj->{ vport } ) )
	{
		if ( $json_obj->{ vip } =~ /^$/ )
		{
			$error = "true";
			$zapierror =
			  "Error trying to modify a http farm $farmname, invalid Virtual IP, can't be blank.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
		elsif ( !$json_obj->{ vip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
		{
			$error = "true";
			$zapierror =
			  "Error trying to modify a l4xnat farm $farmname, invalid Virtual IP.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
		else
		{
			$status = &setFarmVirtualConf( $json_obj->{ vip }, $vport, $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify a http farm $farmname, invalid Virtual IP.";
				&zenlog( "$zapierror", "error", "LSLB" );
			}
			else
			{
				$restart_flag = "true";
			}
		}
	}

	# Modify only vport
	if ( exists ( $json_obj->{ vport } ) && !exists ( $json_obj->{ vip } ) )
	{
		if ( $json_obj->{ vport } =~ /^$/ )
		{
			$error = "true";
			$zapierror =
			  "Error, trying to modify a http farm $farmname, invalid port, can't be blank.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
		elsif ( !$json_obj->{ vport } =~ /^\d+$/ )
		{
			$error     = "true";
			$zapierror = "Error trying to modify a http farm $farmname, invalid port.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
		else
		{
			$status = &setFarmVirtualConf( $vip, $json_obj->{ vport }, $farmname );
			if ( $status == -1 )
			{
				$error     = "true";
				$zapierror = "Error trying to modify a http farm $farmname, invalid port.";
				&zenlog( "$zapierror", "error", "LSLB" );
			}
			else
			{
				$restart_flag = "true";
			}
		}
	}

	# Modify both vip & vport
	if ( exists ( $json_obj->{ vip } ) && exists ( $json_obj->{ vport } ) )
	{
		if ( $json_obj->{ vip } =~ /^$/ )
		{
			$error = "true";
			$zapierror =
			  "Error trying to modify a http farm $farmname, invalid Virtual IP, can't be blank.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
		elsif ( !$json_obj->{ vip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
		{
			$error = "true";
			$zapierror =
			  "Error trying to modify a http farm $farmname, invalid Virtual IP.";
			&zenlog( "$zapierror", "error", "LSLB" );
		}
		else
		{
			if ( exists ( $json_obj->{ vport } ) )
			{
				if ( $json_obj->{ vport } =~ /^$/ )
				{
					$error = "true";
					$zapierror =
					  "Error trying to modify a http farm $farmname, invalid port, can't be blank.";
					&zenlog( "$zapierror", "error", "LSLB" );
				}
				elsif ( !$json_obj->{ vport } =~ /^\d+$/ )
				{
					$error     = "true";
					$zapierror = "Error trying to modify a http farm $farmname, invalid port.";
					&zenlog( "$zapierror", "error", "LSLB" );
				}
				else
				{
					$status =
					  &setFarmVirtualConf( $json_obj->{ vip }, $json_obj->{ vport }, $farmname );
					if ( $status == -1 )
					{
						$error = "true";
						$zapierror =
						  "Error trying to modify a http farm $farmname, invalid port or invalid Virtual IP.";
						&zenlog( "$zapierror", "error", "LSLB" );
					}
					else
					{
						$restart_flag = "true";
					}
				}
			}
		}
	}

	# Check errors and print JSON
	if ( $error ne "true" )
	{
		&zenlog( "Success, some parameters have been changed in farm $farmname.",
				 "info", "LSLB" );

		# set numeric values to numeric type
		for my $key ( keys %{ $json_obj } )
		{
			if ( $json_obj->{ $key } =~ /^\d+$/ )
			{
				$json_obj->{ $key } += 0;
			}
		}

		if ( exists $json_obj->{ listener } && $json_obj->{ listener } eq 'https' )
		{
			include 'Zevenet::Farm::HTTP::HTTPS::Ext';

			# certlist
			my @certlist;
			my @cnames = &getFarmCertificatesSNI( $farmname );
			my $elem   = scalar @cnames;

			for ( my $i = 0 ; $i < $elem ; $i++ )
			{
				push @certlist, { file => $cnames[$i], id => $i + 1 };
			}

			$json_obj->{ certlist } = \@certlist;

			# cipherlist
			unless ( exists $json_obj->{ cipherc } )
			{
				$json_obj->{ cipherc } = &getFarmCipherList( $farmname );
			}

			# cipherset
			unless ( exists $json_obj->{ ciphers } )
			{
				chomp ( $json_obj->{ ciphers } = &getFarmCipherSet( $farmname ) );

				if ( $json_obj->{ ciphers } eq "cipherglobal" )
				{
					$json_obj->{ ciphers } = "all";
				}
			}
		}

		&runIPDSStartByFarm( $farmname );

		# Success
		my $body = {
					 description => "Modify farm $farmname",
					 params      => $json_obj,
		};

		if ( $restart_flag eq "true" && &getFarmStatus( $farmname ) eq 'up' )
		{
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
			"Error trying to modify a http farm $farmname, it's not possible to modify the farm.",
			"error", "LSLB"
		);

		# Error
		my $body = {
					 description => "Modify farm $farmname",
					 error       => "true",
					 message     => $zapierror
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

# Get all IPDS rules applied to a farm
sub getIPDSfarmsRules_zapiv3
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmName = shift;

	require Config::Tiny;

	my $rules;
	my $fileHandle;
	my @dosRules        = ();
	my @blacklistsRules = ();
	my @rblRules        = ();

	my $dosConf        = &getGlobalConfiguration( 'dosConf' );
	my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
	my $rblPath        = &getGlobalConfiguration( 'configdir' ) . "/ipds/rbl";
	my $rblConf        = "$rblPath/rbl.conf";

	if ( -e $dosConf )
	{
		$fileHandle = Config::Tiny->read( $dosConf );
		foreach my $key ( keys %{ $fileHandle } )
		{
			if ( defined $fileHandle->{ $key }->{ 'farms' }
				 && $fileHandle->{ $key }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
			{
				push @dosRules, $key;
			}
		}
	}

	if ( -e $blacklistsConf )
	{
		$fileHandle = Config::Tiny->read( $blacklistsConf );
		foreach my $key ( keys %{ $fileHandle } )
		{
			if ( defined $fileHandle->{ $key }->{ 'farms' }
				 && $fileHandle->{ $key }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
			{
				push @blacklistsRules, $key;
			}
		}
	}

	if ( -e $rblConf )
	{
		$fileHandle = Config::Tiny->read( $rblConf );
		foreach my $key ( keys %{ $fileHandle } )
		{
			if ( defined $fileHandle->{ $key }->{ 'farms' }
				 && $fileHandle->{ $key }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
			{
				push @rblRules, $key;
			}
		}
	}

	$rules =
	  { dos => \@dosRules, blacklists => \@blacklistsRules, rbl => \@rblRules };
	return $rules;
}

1;
