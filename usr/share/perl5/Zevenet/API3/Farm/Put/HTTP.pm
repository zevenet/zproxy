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

# PUT /farms/<farmname> Modify a http|https Farm
sub modify_http_farm # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	# flag to reset IPDS rules when the farm changes the name.
	my $farmname_old;
	my $ipds;

	if ( eval { require Zevenet::IPDS; } )
	{
		require Zevenet::IPDS::Blacklist;
		require Zevenet::IPDS::DoS;
		$ipds = &getIPDSfarmsRules( $farmname );
	}
	
	# Flags
	my $reload_flag  = "false";
	my $restart_flag = "false";
	my $error        = "false";
	my $flag         = "false";

	my $status;
	my $zapierror;
	
	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		my $errormsg = "The farmname $farmname does not exist.";
		my $body = {
					 description => "Modify farm",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

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
				"ZAPI error, trying to modify a http farm $farmname, cannot change the farm name while running"
			);

			my $errormsg = 'Cannot change the farm name while the farm is running';

			my $body = {
						 description => "Modify farm",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		if ( $json_obj->{ newfarmname } eq '' )
		{
			$error = "true";
			$zapierror = "Error, trying to modify a http farm $farmname, invalid newfarmname, can't be blank.";
			&zenlog( "Zapi $zapierror" );
		}
		else
		{
			#Check if farmname has correct characters (letters, numbers and hyphens)
			if ( $json_obj->{ newfarmname } =~ /^[a-zA-Z0-9\-]*$/ )
			{
				if ($json_obj->{newfarmname} ne $farmname)
				{
					#Check if the new farm's name alredy exists
					my $newffile = &getFarmFile( $json_obj->{ newfarmname } );
					if ( $newffile != -1 )
					{
						$error = "true";
						$zapierror = "Error, trying to modify a http farm $farmname, the farm $json_obj->{newfarmname} already exists, try another name.";
						&zenlog( "Zapi $zapierror" );
					}
					else
					{
						my $oldfstat = &runFarmStop( $farmname, "true" );
						if ( $oldfstat != 0 )
						{
							$error = "true";
							$zapierror = "Error, trying to modify a http farm $farmname,the farm is not disabled, are you sure it's running?";
							&zenlog( "Zapi $zapierror" );
						}
						else
						{
							#Change farm name
							my $fnchange = &setNewFarmName( $farmname, $json_obj->{ newfarmname } );
							$changedname = "true";
							if ( $fnchange == -1 )
							{
								&error = "true";
								$zapierror = "Error, trying to modify a http farm $farmname, the name of the farm can't be modified, delete the farm and create a new one.";
								&zenlog( "Zapi $zapierror" );
							}
							elsif ( $fnchange == -2 )
							{
								$error = "true";
								$zapierror = "Error, trying to modify a http farm $farmname, invalid newfarmname, the new name can't be empty.";
								&zenlog( "Zapi $zapierror" );
							}
							else
							{
								$farmname_old = $farmname;
								$farmname = $json_obj->{ newfarmname };
							}
						}
					}
				}
			}
			else
			{
				$error = "true";
				$zapierror = "Error, trying to modify a http farm $farmname, invalid newfarmname.";
				&zenlog( "Zapi $zapierror" );
			}
		}
	}

	# Modify Backend Connection Timeout
	if ( exists ( $json_obj->{ contimeout } ) )
	{
		if ( $json_obj->{ contimeout } eq '' )
		{
			$error = "true";
			$zapierror = "Error, trying to modify a http farm $farmname, invalid contimeout, can't be blank.";
			&zenlog( "Zapi $zapierror" );
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
				$zapierror = "Error, trying to modify a http farm $farmname, some errors happened trying to modify the contimeout.";
				&zenlog( "Zapi $zapierror" );
			}
		}
		else
		{
			$error = "true";
			$zapierror = ( "Error, trying to modify a http farm $farmname, invalid contimeout." );
			&zenlog( "Zapi $zapierror" );
		}
	}

	# Modify Backend Respone Timeout
	if ( exists ( $json_obj->{ restimeout } ) )
	{
		if ( $json_obj->{ restimeout } eq '' )
		{
			$error = "true";
			$zapierror = "Error, trying to modify a http farm $farmname, invalid restimeout, can't be blank.";
			&zenlog( "Zapi $zapierror" );
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
				$zapierror = "Error, trying to modify a http farm $farmname, some errors happened trying to modify the restimeout.";
				&zenlog( "Zapi $zapierror" );
			}
		}
		else
		{
			$error = "true";
			$zapierror = "Error, trying to modify a http farm $farmname, invalid restimeout.";
			&zenlog( "Zapi $zapierror" );
		}
	}

	# Modify Frequency To Check Resurrected Backends
	if ( exists ( $json_obj->{ resurrectime } ) )
	{
		if ( $json_obj->{ resurrectime } eq '' )
		{
			$error = "true";
			$zapierror = "Error, trying to modify a http farm $farmname, invalid resurrectime, can't be blank.";
			&zenlog( "Zapi $zapierror" );
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
				$zapierror = "Error, trying to modify a http farm $farmname, some errors happened trying to modify the resurrectime.";
				&zenlog( "Zapi $zapierror" );
			}
		}
		else
		{
			$error = "true";
			$zapierror = "Error, trying to modify a http farm $farmname, invalid resurrectime.";
			&zenlog( "Zapi $zapierror" );	  
		}
	}

	# Modify Client Request Timeout
	if ( exists ( $json_obj->{ reqtimeout } ) )
	{
		if ( $json_obj->{ reqtimeout } eq '' )
		{
			$error = "true";
			$zapierror = "Error, trying to modify a http farm $farmname, invalid reqtimeout, can't be blank.";
			&zenlog( "Zapi $zapierror" );
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
				$zapierror = "Error, trying to modify a http farm $farmname, some errors happened trying to modify the reqtimeout.";
				&zenlog( "Zapi $zapierror" );
			}
		}
		else
		{
			$error = "true";
			$zapierror = "Error, trying to modify a http farm $farmname, invalid reqtimeout.";
			&zenlog( "Zapi $zapierror" );
		}
	}

	# Modify Rewrite Location Headers
	if ( exists ( $json_obj->{ rewritelocation } ) )
	{
		if ( $json_obj->{ rewritelocation } eq '' )
		{
			$error = "true";
			$zapierror = "Error, trying to modify a http farm $farmname, invalid rewritelocation, can't be blank.";
			&zenlog( "Zapi $zapierror" );
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
				$zapierror = "Error, trying to modify a http farm $farmname, some errors happened trying to modify the rewritelocation.";
				&zenlog( "Zapi $zapierror" );
			}
		}
		else
		{
			$error = "true";
			$zapierror = "Error, trying to modify a http farm $farmname, invalid rewritelocation.";
			&zenlog( "Zapi $zapierror" );
		}
	}

	# Enable or disable ignore 100 continue header
	if ( exists ( $json_obj->{ ignore_100_continue } ) )
	{
		if ( $json_obj->{ ignore_100_continue } =~ /^$/ )
		{
			$error = "true";
			$zapierror = "Error, trying to modify a http farm $farmname, invalid ignore_100_continue, can't be blank.";
			&zenlog( "Zapi $zapierror" );
		}
		elsif (
				$json_obj->{ ignore_100_continue } =~ /^true|false$/ )
		{
			my $action = 0;
			$action = 1 if( $json_obj->{ ignore_100_continue } =~ /^true$/ );
			
			
			if ( &getHTTPFarm100Continue( $farmname ) != $action )
			{
				$status = &setHTTPFarm100Continue($farmname, $action);
				if ( $status != -1 )
				{
					$restart_flag = "true";
				}
				else
				{
					$error = "true";
					$zapierror = "Error, trying to modify a http farm $farmname, some errors happened trying to modify the certname.";
					&zenlog( "Zapi $zapierror" );
				}
			}
		}
		else
		{
			$error = "true";
			$zapierror = "Error, trying to modify a http farm $farmname, invalid ignore_100_continue.";
			&zenlog( "Zapi $zapierror" );
		}
	}

	# Modify HTTP Verbs Accepted
	if ( exists ( $json_obj->{ httpverb } ) )
	{
		if ( $json_obj->{ httpverb } eq '' )
		{
			$error = "true";
			$zapierror = "Error, trying to modify a http farm $farmname, invalid httpverb, can't be blank.";
			&zenlog( "Zapi $zapierror" );
		}
		elsif ( $json_obj->{ httpverb } =~
				/^standardHTTP|extendedHTTP|standardWebDAV|MSextWebDAV|MSRPCext$/ )
		{
			my $httpverb = 0;

			if    ( $json_obj->{ httpverb } eq "standardHTTP" )   { $httpverb = 0; }
			elsif ( $json_obj->{ httpverb } eq "extendedHTTP" )   { $httpverb = 1; }
			elsif ( $json_obj->{ httpverb } eq "standardWebDAV" ) { $httpverb = 2; }
			elsif ( $json_obj->{ httpverb } eq "MSextWebDAV" )    { $httpverb = 3; }
			elsif ( $json_obj->{ httpverb } eq "MSRPCext" )       { $httpverb = 4; }

			$status = &setFarmHttpVerb( $httpverb, $farmname );

			if ( $status != -1 )
			{
				$restart_flag = "true";
			}
			else
			{
				$error = "true";
				$zapierror = "Error, trying to modify a http farm $farmname, some errors happened trying to modify the httpverb.";
				&zenlog( "Zapi $zapierror" );			
			}
		}
		else
		{
			$error = "true";
			$zapierror = "Error, trying to modify a http farm $farmname, invalid httpverb.";
			&zenlog( "Zapi $zapierror" );
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
			$zapierror = "Error, trying to modify a http farm $farmname, some errors happened trying to modify the error414.";
			&zenlog( "Zapi $zapierror" );		
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
			$zapierror = "Error, trying to modify a http farm $farmname, some errors happened trying to modify the error500.";
			&zenlog( "Zapi $zapierror" );
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
			$zapierror = "ZAPI error, trying to modify a http farm $farmname, some errors happened trying to modify the error501.";
			&zenlog( "Zapi $zapierror" );
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
			$zapierror = "Error, trying to modify a http farm $farmname, some errors happened trying to modify the error503.";
			&zenlog( "Zapi $zapierror" );
		}
	}

	# Modify Farm Listener
	if ( exists ( $json_obj->{ listener } ) )
	{
		if ( $json_obj->{ listener } =~ /^$/ )
		{
			$error = "true";
			$zapierror = "Error, trying to modify a http farm $farmname, invalid listener, can't be blank.";
			&zenlog( "Zapi $zapierror" );
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
				$zapierror = "Error, trying to modify a http farm $farmname, some errors happened trying to modify the listener.";
				&zenlog( "Zapi $zapierror" );
			}
		}
		else
		{
			$error = "true";
			$zapierror = "Error, trying to modify a http farm $farmname, invalid listener.";
			&zenlog( "Zapi $zapierror" );
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
				$zapierror = "Error, trying to modify a http farm $farmname, invalid ciphers, can't be blank."
				&zenlog( "Zapi $zapierror" );
			}
			elsif ( &getValidFormat( 'ciphers', $json_obj->{ ciphers } ) )
			{
				my $ssloffloading_error=0;
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
				elsif ( $json_obj->{ ciphers } eq "ssloffloading" )
				{
					if ( &getFarmCipherSSLOffLoadingSupport() )
					{
						$ciphers = "cipherssloffloading";
					}
					else
					{
						$ssloffloading_error = 1;
						$error = "true";
						$zapierror = "Error, the CPU not support SSL offloading.";
						&zenlog( "Zapi $zapierror" );
					}
				}
				if ( ! $ssloffloading_error )
				{
					$status = &setFarmCipherList( $farmname, $ciphers );
					$restart_flag = "true" if ( $status != -1 );
				}
				else
				{
					$error = "true";
					$zapierror = "Error, trying to modify a http farm $farmname, some errors happened trying to modify the ciphers.";
					&zenlog( "Zapi $zapierror" );
				}
			}
			else
			{
				$error = "true";
				$zapierror = "Error, trying to modify a http farm $farmname, invalid ciphers.";
				&zenlog( "Zapi $zapierror" );
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
					if ( $json_obj->{ cipherc } eq '' )
					{
						$error = "true";
						$zapierror = "Error, trying to modify a http farm $farmname, invalid cipherc, can't be blank.";
						&zenlog( "Zapi $zapierror" );
					}
					else
					{
						my $cipherc = $json_obj->{ cipherc };
						$cipherc =~ s/\ //g;

						if ( $cipherc eq "" )
						{
							$error = "true";
							$zapierror = "Error, trying to modify a http farm $farmname, invalid cipherc, can't be blank.";
							&zenlog( "Zapi $zapierror" );
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
								$zapierror = "Error, trying to modify a http farm $farmname, some errors happened trying to modify the cipherc.";
								&zenlog( "Zapi $zapierror" );
							}
						}
					}
				}
			}
		}

		# Add Certificate to SNI list
		if ( exists ( $json_obj->{ certname } ) )
		{
			$status = &setFarmCertificateSNI( $json_obj->{ certname }, $farmname );
			if ( $status != -1 )
			{
				$restart_flag = "true";
			}
			else
			{
				$error = "true";
				$zapierror = "Error, trying to modify a http farm $farmname, some errors happened trying to modify the certname.";
				&zenlog( "Zapi $zapierror" );
			}
		}

		# Disable security protocol
		my @protocols_ssl_keys = ( "disable_sslv2","disable_sslv3","disable_tlsv1",
			"disable_tlsv1_1","disable_tlsv1_2" );
		foreach my $key_ssl ( @protocols_ssl_keys )
		{
			if ( grep ( /^$key_ssl$/, keys %{$json_obj} ) )
			{
				my $ssl_proto;
				my $action = -1;
				$action = 1 if( $json_obj->{$key_ssl} eq "true" );
				$action = 0 if( $json_obj->{$key_ssl} eq "false" );
				
				$ssl_proto = "SSLv2" if( $key_ssl eq "disable_sslv2" );
				$ssl_proto = "SSLv3" if( $key_ssl eq "disable_sslv3" );
				$ssl_proto = "TLSv1" if( $key_ssl eq "disable_tlsv1" );
				$ssl_proto = "TLSv1_1" if( $key_ssl eq "disable_tlsv1_1" );
				$ssl_proto = "TLSv1_2" if( $key_ssl eq "disable_tlsv1_2" );
				
				
				if( $action != -1 )
				{
					if( $action != &getHTTPFarmDisableSSL($farmname, $ssl_proto) )
					{
						$status = &setHTTPFarmDisableSSL ($farmname, $ssl_proto, $action );
						if ( $status != -1 )
						{
							$restart_flag = "true";
						}
						else
						{
							$error = "true";
							$zapierror = "Error, trying to modify a http farm $farmname, some errors happened trying to modify the certname.";
							&zenlog( "Zapi $zapierror" );
						}
					}
				}
				else
				{
					$error = "true";
					$zapierror = "Error, the value is not valid for parameter $key_ssl.";
					&zenlog( "Zapi $zapierror" );
				}
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
			my $errormsg = "To modify ciphers, chiperc or certname, listener must be https.";
			my $body = {
						 description => "Modify farm $farmname",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}

	# Modify only vip
	if ( exists ( $json_obj->{ vip } ) && !exists ( $json_obj->{ vport } ) )
	{
		if ( $json_obj->{ vip } eq '' )
		{
			$error = "true";
			$zapierror =  "Error, trying to modify a http farm $farmname, invalid vip, can't be blank.";
			&zenlog( "Zapi $zapierror" );
		}
		elsif ( !$json_obj->{ vip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
		{
			$error = "true";
			$zapierror = "Error, trying to modify a l4xnat farm $farmname, invalid vip.";
			&zenlog( "Zapi $zapierror" );
		}
		else
		{
			$status = &setFarmVirtualConf( $json_obj->{ vip }, $vport, $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				$zapierror = "Error, trying to modify a http farm $farmname, invalid vip.";
				&zenlog( "Zapi $zapierror" );
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
		if ( $json_obj->{ vport } eq '' )
		{
			$error = "true";
			$zapierror = "Error, trying to modify a http farm $farmname, invalid port, can't be blank.";
			&zenlog( "Zapi $zapierror" );
		}
		elsif ( !$json_obj->{ vport } =~ /^\d+$/ )
		{
			$error = "true";
			$zapierror = "Error, trying to modify a http farm $farmname, invalid port.";
			&zenlog( "Zapi $zapierror" );
		}
		else
		{
			$status = &setFarmVirtualConf( $vip, $json_obj->{ vport }, $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				$zapierror = "Error, trying to modify a http farm $farmname, invalid port.";
				&zenlog( "Zapi $zapierror" );
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
		if ( $json_obj->{ vip } eq '' )
		{
			$error = "true";
			$zapierror = "Error, trying to modify a http farm $farmname, invalid vip, can't be blank.";
			&zenlog( "Zapi $zapierror" );
		}
		elsif ( !$json_obj->{ vip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
		{
			$error = "true";
			$zapierror = "Error, trying to modify a http farm $farmname, invalid vip.";
			&zenlog( "Zapi $zapierror" );
		}
		else
		{
			if ( exists ( $json_obj->{ vport } ) )
			{
				if ( $json_obj->{ vport } eq '' )
				{
					$error = "true";
					$zapierror = "Error, trying to modify a http farm $farmname, invalid port, can't be blank.";
					&zenlog( "Zapi $zapierror" );
				}
				elsif ( !$json_obj->{ vport } =~ /^\d+$/ )
				{
					$error = "true";
					$zapierror = "Error, trying to modify a http farm $farmname, invalid port.";
					&zenlog( "Zapi $zapierror" );
				}
				else
				{
					$status =
					  &setFarmVirtualConf( $json_obj->{ vip }, $json_obj->{ vport }, $farmname );
					if ( $status == -1 )
					{
						$error = "true";
						$zapierror = "Error, trying to modify a http farm $farmname, invalid port or invalid vip.";
						&zenlog( "Zapi $zapierror" );
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
		&zenlog(
				  "ZAPI success, some parameters have been changed in farm $farmname." );

		if ( eval { require Zevenet::IPDS; } )
		{
			# update the ipds rule applied to the farm
			if ( !$farmname_old )
			{
				&setBLReloadFarmRules ( $farmname );
				&setDOSReloadFarmRules ( $farmname );
			}
			# create new rules with the new farmname
			else
			{
				foreach my $list ( @{ $ipds->{ 'blacklists' } } )
				{
					&setBLRemFromFarm( $farmname_old, $list );
					&setBLApplyToFarm( $farmname, $list );
				}
				foreach my $rule ( @{ $ipds->{ 'dos' } } )
				{
					&setDOSDeleteRule( $rule, $farmname_old );
					&setDOSCreateRule( $rule, $farmname );
				}
			}
		}

		# set numeric values to numeric type
		for my $key ( keys %{ $json_obj } )
		{
			if ( $json_obj->{ $key } =~ /^\d+$/ )
			{
				$json_obj->{ $key } += 0;
			}
		}

		if ( $json_obj->{ listener } eq 'https' )
		{
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

		# Success
		my $body = {
			description => "Modify farm $farmname",
			params      => $json_obj,
		};

		if ( $restart_flag eq "true" && &getFarmStatus( $farmname ) eq 'up' )
		{
			&setFarmRestart( $farmname );
			$body->{ status } = 'needed restart';
			$body->{ info } = "There're changes that need to be applied, stop and start farm to apply them!";
		}

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to modify a http farm $farmname, it's not possible to modify the farm."
		);

		# Error
		my $body = {
					 description => "Modify farm $farmname",
					 error       => "true",
					 message     => $zapierror
		};

		&httpResponse({ code => 400, body => $body });
	}
}

1;
