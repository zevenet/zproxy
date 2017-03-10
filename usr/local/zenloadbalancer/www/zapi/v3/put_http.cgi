#!/usr/bin/perl -w

use strict;

# PUT /farms/<farmname> Modify a http|https Farm
sub modify_http_farm # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;
	# flag to reset IPDS rules when the farm changes the name.
	my $farmname_old;
	my $ipds = &getIPDSfarmsRules( $farmname );
	
	# Flags
	my $reload_flag  = "false";
	my $restart_flag = "false";
	my $error        = "false";
	my $flag         = "false";

	my $status;
	
	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
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

			my $errormsg = 'Cannot change the farm name while running';

			my $body = {
						 description => "Modify farm",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		if ( $json_obj->{ newfarmname } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a http farm $farmname, invalid newfarmname, can't be blank."
			);
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
						&zenlog(
							"ZAPI error, trying to modify a http farm $farmname, the farm $json_obj->{newfarmname} already exists, try another name."
						);
					}
					else
					{
						my $oldfstat = &runFarmStop( $farmname, "true" );
						if ( $oldfstat != 0 )
						{
							$error = "true";
							&zenlog(
								"ZAPI error, trying to modify a http farm $farmname,the farm is not disabled, are you sure it's running?"
							);
						}
						else
						{
							#Change farm name
							my $fnchange = &setNewFarmName( $farmname, $json_obj->{ newfarmname } );
							$changedname = "true";
							if ( $fnchange == -1 )
							{
								&error = "true";
								&zenlog(
									"ZAPI error, trying to modify a http farm $farmname, the name of the farm can't be modified, delete the farm and create a new one."
								);
							}
							elsif ( $fnchange == -2 )
							{
								$error = "true";
								&zenlog(
									"ZAPI error, trying to modify a http farm $farmname, invalid newfarmname, the new name can't be empty."
								);
								#~ $newfstat = &runFarmStart( $farmname, "true" );
								
								#~ if ( $newfstat != 0 )
								#~ {
									#~ $error = "true";
									#~ &zenlog(
										#~ "ZAPI error, trying to modify a http farm $farmname, the farm isn't running, check if the IP address is up and the PORT is in use."
									#~ );
								#~ }
							}
							else
							{
								$farmname_old = $farmname;
								$farmname = $json_obj->{ newfarmname };
								
								#~ $newfstat = &runFarmStart( $farmname, "true" );
								#~ if ( $newfstat != 0 )
								#~ {
									#~ $error = "true";
									#~ &zenlog(
										#~ "ZAPI error, trying to modify a http farm $farmname, the farm isn't running, check if the IP address is up and the PORT is in use."
									#~ );
								#~ }
							}
						}
					}
				}
			}
			else
			{
				$error = "true";
				&zenlog(
					   "ZAPI error, trying to modify a http farm $farmname, invalid newfarmname." );
			}
		}
	}

	# Modify Backend Connection Timeout
	if ( exists ( $json_obj->{ contimeout } ) )
	{
		if ( $json_obj->{ contimeout } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a http farm $farmname, invalid contimeout, can't be blank."
			);
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
				&zenlog(
					"ZAPI error, trying to modify a http farm $farmname, some errors happened trying to modify the contimeout."
				);
			}
		}
		else
		{
			$error = "true";
			&zenlog(
					"ZAPI error, trying to modify a http farm $farmname, invalid contimeout." );
		}
	}

	# Modify Backend Respone Timeout
	if ( exists ( $json_obj->{ restimeout } ) )
	{
		if ( $json_obj->{ restimeout } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a http farm $farmname, invalid restimeout, can't be blank."
			);
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
				&zenlog(
					"ZAPI error, trying to modify a http farm $farmname, some errors happened trying to modify the restimeout."
				);
			}
		}
		else
		{
			$error = "true";
			&zenlog(
					"ZAPI error, trying to modify a http farm $farmname, invalid restimeout." );
		}
	}

	# Modify Frequency To Check Resurrected Backends
	if ( exists ( $json_obj->{ resurrectime } ) )
	{
		if ( $json_obj->{ resurrectime } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a http farm $farmname, invalid resurrectime, can't be blank."
			);
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
				&zenlog(
					"ZAPI error, trying to modify a http farm $farmname, some errors happened trying to modify the resurrectime."
				);
			}
		}
		else
		{
			$error = "true";
			&zenlog(
				  "ZAPI error, trying to modify a http farm $farmname, invalid resurrectime." );
		}
	}

	# Modify Client Request Timeout
	if ( exists ( $json_obj->{ reqtimeout } ) )
	{
		if ( $json_obj->{ reqtimeout } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a http farm $farmname, invalid reqtimeout, can't be blank."
			);
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
				&zenlog(
					"ZAPI error, trying to modify a http farm $farmname, some errors happened trying to modify the reqtimeout."
				);
			}
		}
		else
		{
			$error = "true";
			&zenlog(
					"ZAPI error, trying to modify a http farm $farmname, invalid reqtimeout." );
		}
	}

	# Modify Rewrite Location Headers
	if ( exists ( $json_obj->{ rewritelocation } ) )
	{
		if ( $json_obj->{ rewritelocation } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a http farm $farmname, invalid rewritelocation, can't be blank."
			);
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

				#&runFarmRestart($farmname);
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify a http farm $farmname, some errors happened trying to modify the rewritelocation."
				);
			}
		}
		else
		{
			$error = "true";
			&zenlog(
				  "ZAPI error, trying to modify a http farm $farmname, invalid rewritelocation."
			);
		}
	}

	# Modify HTTP Verbs Accepted
	if ( exists ( $json_obj->{ httpverb } ) )
	{
		if ( $json_obj->{ httpverb } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a http farm $farmname, invalid httpverb, can't be blank."
			);
		}
		elsif ( $json_obj->{ httpverb } =~
				/^standardHTTP|extendedHTTP|standardWebDAV|MSextWebDAV|MSRPCext$/ )
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
			$status = &setFarmHttpVerb( $httpverb, $farmname );
			if ( $status != -1 )
			{
				$restart_flag = "true";

				#&runFarmRestart($farmname);
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify a http farm $farmname, some errors happened trying to modify the httpverb."
				);
			}
		}
		else
		{
			$error = "true";
			&zenlog(
					  "ZAPI error, trying to modify a http farm $farmname, invalid httpverb." );
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
			&zenlog(
				"ZAPI error, trying to modify a http farm $farmname, some errors happened trying to modify the error414."
			);
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
			&zenlog(
				"ZAPI error, trying to modify a http farm $farmname, some errors happened trying to modify the error500."
			);
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
			&zenlog(
				"ZAPI error, trying to modify a http farm $farmname, some errors happened trying to modify the error501."
			);
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
			&zenlog(
				"ZAPI error, trying to modify a http farm $farmname, some errors happened trying to modify the error503."
			);
		}
	}

	# Modify Farm Listener
	if ( exists ( $json_obj->{ listener } ) )
	{
		if ( $json_obj->{ listener } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a http farm $farmname, invalid listener, can't be blank."
			);
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
				&zenlog(
					"ZAPI error, trying to modify a http farm $farmname, some errors happened trying to modify the listener."
				);
			}
		}
		else
		{
			$error = "true";
			&zenlog(
					  "ZAPI error, trying to modify a http farm $farmname, invalid listener." );
		}
	}

	# Modify HTTPS Params
	my $farmtype = &getFarmType( $farmname );
	if ( $farmtype eq "https" )
	{
		# Modify Ciphers
		if ( exists ( $json_obj->{ ciphers } ) )
		{
			if ( $json_obj->{ ciphers } =~ /^$/ )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify a http farm $farmname, invalid ciphers, can't be blank."
				);
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
					&zenlog(
						"ZAPI error, trying to modify a http farm $farmname, some errors happened trying to modify the ciphers."
					);
				}
			}
			else
			{
				$error = "true";
				&zenlog(
						  "ZAPI error, trying to modify a http farm $farmname, invalid ciphers." );
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
						&zenlog(
							"ZAPI error, trying to modify a http farm $farmname, invalid cipherc, can't be blank."
						);
					}
					else
					{
						my $cipherc = $json_obj->{ cipherc };
						$cipherc =~ s/\ //g;

						if ( $cipherc eq "" )
						{
							$error = "true";
							&zenlog(
								"ZAPI error, trying to modify a http farm $farmname, invalid cipherc, can't be blank."
							);
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
								&zenlog(
									"ZAPI error, trying to modify a http farm $farmname, some errors happened trying to modify the cipherc."
								);
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
				&zenlog(
					"ZAPI error, trying to modify a http farm $farmname, some errors happened trying to modify the certname."
				);
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
		if ( $json_obj->{ vip } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a http farm $farmname, invalid vip, can't be blank."
			);
		}
		elsif ( !$json_obj->{ vip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
		{
			$error = "true";
			&zenlog(
					  "ZAPI error, trying to modify a l4xnat farm $farmname, invalid vip." );
		}
		else
		{
			$status = &setFarmVirtualConf( $json_obj->{ vip }, $vport, $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				&zenlog( "ZAPI error, trying to modify a http farm $farmname, invalid vip." );
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
			&zenlog(
				"ZAPI error, trying to modify a http farm $farmname, invalid port, can't be blank."
			);
		}
		elsif ( !$json_obj->{ vport } =~ /^\d+$/ )
		{
			$error = "true";
			&zenlog( "ZAPI error, trying to modify a http farm $farmname, invalid port." );
		}
		else
		{
			$status = &setFarmVirtualConf( $vip, $json_obj->{ vport }, $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				&zenlog( "ZAPI error, trying to modify a http farm $farmname, invalid port." );
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
			&zenlog(
				"ZAPI error, trying to modify a http farm $farmname, invalid vip, can't be blank."
			);
		}
		elsif ( !$json_obj->{ vip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
		{
			$error = "true";
			&zenlog( "ZAPI error, trying to modify a http farm $farmname, invalid vip." );
		}
		else
		{
			if ( exists ( $json_obj->{ vport } ) )
			{
				if ( $json_obj->{ vport } =~ /^$/ )
				{
					$error = "true";
					&zenlog(
						"ZAPI error, trying to modify a http farm $farmname, invalid port, can't be blank."
					);
				}
				elsif ( !$json_obj->{ vport } =~ /^\d+$/ )
				{
					$error = "true";
					&zenlog( "ZAPI error, trying to modify a http farm $farmname, invalid port." );
				}
				else
				{
					$status =
					  &setFarmVirtualConf( $json_obj->{ vip }, $json_obj->{ vport }, $farmname );
					if ( $status == -1 )
					{
						$error = "true";
						&zenlog(
							"ZAPI error, trying to modify a http farm $farmname, invalid port or invalid vip."
						);
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
		my $errormsg = "Errors found trying to modify farm $farmname";
		my $body = {
					 description => "Modify farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

1;
