#!/usr/bin/perl -w

######### PUT GSLB
#
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -d '{"newfarmname":"newFarmGSLB","vip":"178.62.126.152","vport":"53"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB
#
#
#####Documentation of PUT GSLB####
#**
#  @api {put} /farms/<farmname> Modify a gslb Farm
#  @apiGroup Farm Modify
#  @apiName PutFarmGSLB
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Modify the params in a GSLB Farm
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess	{String}		newfarmname	The new Farm's name.
# @apiSuccess	{Number}		vport			PORT of the farm, where is listening the virtual service.
# @apiSuccess	{String}		vip			IP of the farm, where is listening the virtual service.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify farm newFarmGSLB",
#   "params" : [
#      {
#         "vip" : "178.62.126.152"
#      },
#      {
#         "vport" : "53"
#      },
#      {
#         "newfarmname" : "newFarmGSLB"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"vip":"178.62.126.152","vport":"53",
#       "newfarmname":"newFarmGSLB"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/newFarmGSLB
#
# @apiSampleRequest off
#
#**

sub modify_gslb_farm # ( $json_obj,	$farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	# Flags
	my $reload_flag  = "false";
	my $restart_flag = "false";
	my $error        = "false";

	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $output = {
					   description => "Modify farm",
					   error       => "true",
					   message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# Get current vip & vport
	my $vip   = &getFarmVip( "vip",  $farmname );
	my $vport = &getFarmVip( "vipp", $farmname );

	######## Functions

	# Modify only vip
	if ( exists ( $json_obj->{ vip } ) && !exists ( $json_obj->{ vport } ) )
	{
		if ( $json_obj->{ vip } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a gslb farm $farmname, invalid vip, can't be blank."
			);
		}
		elsif ( !$json_obj->{ vip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
		{
			$error = "true";
			&zenlog(
					  "ZAPI error, trying to modify a gslb farm $farmname, invalid vip." );
		}
		else
		{
			$status = &setFarmVirtualConf( $json_obj->{ vip }, $vport, $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				&zenlog(
						  "ZAPI error, trying to modify a gslb farm $farmname, invalid vip." );
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
				"ZAPI error, trying to modify a gslb farm $farmname, invalid vport, can't be blank."
			);
		}
		elsif ( !$json_obj->{ vport } =~ /^\d+$/ )
		{
			$error = "true";
			&zenlog(
					  "ZAPI error, trying to modify a gslb farm $farmname, invalid vport." );
		}
		else
		{
			$status = &setFarmVirtualConf( $vip, $json_obj->{ vport }, $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				&zenlog(
						  "ZAPI error, trying to modify a gslb farm $farmname, invalid vport." );
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
				"ZAPI error, trying to modify a gslb farm $farmname, invalid vip, can't be blank."
			);
		}
		elsif ( !$json_obj->{ vip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
		{
			$error = "true";
			&zenlog(
					  "ZAPI error, trying to modify a gslb farm $farmname, invalid vip." );
		}
		else
		{
			if ( exists ( $json_obj->{ vport } ) )
			{
				if ( $json_obj->{ vport } =~ /^$/ )
				{
					$error = "true";
					&zenlog(
						"ZAPI error, trying to modify a gslb farm $farmname, invalid vport, can't be blank."
					);
				}
				elsif ( !$json_obj->{ vport } =~ /^\d+$/ )
				{
					$error = "true";
					&zenlog(
							  "ZAPI error, trying to modify a gslb farm $farmname, invalid vport." );
				}
				else
				{
					$status =
					  &setFarmVirtualConf( $json_obj->{ vip }, $json_obj->{ vport }, $farmname );
					if ( $status == -1 )
					{
						$error = "true";
						&zenlog(
							"ZAPI error, trying to modify a gslb farm $farmname, invalid vport or invalid vip."
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

	# Modify Farm's Name
	#if(exists($json_obj->{newfarmname})){
	#        if($json_obj->{newfarmname} =~ /^$/){
	#                $error = "true";
	#        } else {
	#                #Check if farmname has correct characters (letters, numbers and hyphens)
	#                if($json_obj->{newfarmname} =~ /^[a-zA-Z0-9\-]*$/){
	#                        #Check if the new farm's name alredy exists
	#                        my $newffile = &getFarmFile($json_obj->{newfarmname});
	#                        if ($newffile != -1){
	#                                $error = "true";
	#                        } else {
	#                                #Change farm name
	#                                my $fnchange = &setNewFarmName($farmname,$json_obj->{newfarmname});
	#                                if ($fnchange == -1){
	#                                        &error = "true";
	#                                } else {
	#                                        $restart_flag = "true";
	#										  $farmname = $json_obj->{newfarmname};
	#                                }
	#                        }
	#                } else {
	#                        $error = "true";
	#                }
	#        }
	#}

	# Restart Farm
	#if($restart_flag eq "true"){
	#        &runFarmStop($farmname,"true");
	#        &runFarmStart($farmname,"true");
	#}

	# Modify Farm's Name
	if ( exists ( $json_obj->{ newfarmname } ) )
	{
		if ( $json_obj->{ newfarmname } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a gslb farm $farmname, invalid newfarmname, can't be blank."
			);
		}
		else
		{
			# Check if farmname has correct characters (letters, numbers and hyphens)
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
							"ZAPI error, trying to modify a gslb farm $farmname, the farm $json_obj->{newfarmname} already exists, try another name."
						);
					}
					else
					{
						$oldfstat = &runFarmStop( $farmname, "true" );
						if ( $oldfstat != 0 )
						{
							$error = "true";
							&zenlog(
								"ZAPI error, trying to modify a gslb farm $farmname,the farm is not disabled, are you sure it's running?"
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
									"ZAPI error, trying to modify a gslb farm $farmname, the name of the farm can't be modified, delete the farm and create a new one."
								);
							}
							elsif ( $fnchange == -2 )
							{
								$error = "true";
								&zenlog(
									"ZAPI error, trying to modify a gslb farm $farmname, invalid newfarmname, the new name can't be empty."
								);
								$newfstat = &runFarmStart( $farmname, "true" );
								if ( $newfstat != 0 )
								{
									$error = "true";
									&zenlog(
										"ZAPI error, trying to modify a gslb farm $farmname, the farm isn't running, chick if the IP address is up and the PORT is in use."
									);
								}
							}
							else
							{
								$farmname = $json_obj->{ newfarmname };
								$newfstat = &runFarmStart( $farmname, "true" );
								if ( $newfstat != 0 )
								{
									$error = "true";
									&zenlog(
										"ZAPI error, trying to modify a gslb farm $farmname, the farm isn't running, chick if the IP address is up and the PORT is in use."
									);
								}
							}
						}
					}
				}
			}
			else
			{
				$error = "true";
				&zenlog(
						   "ZAPI error, trying to modify a gslb farm $farmname, invalid newfarmname." );
			}
		}
	}

	# Check errors and print JSON
	#if ($error ne "true")
	#{
	#        if($changedname ne "true")
	#		 {
	#                if($restart_flag eq "true")
	#				 {
	#                        &setFarmRestart($farmname);
	#
	#                        my $body = {
	#                                description => "Modify farm $farmname",
	#                                params => $json_obj,
	#                                status => 'needed restart',
	#                                info => "There're changes that need to be applied, stop and start farm to apply them!"
	#                        };
	#
	#						 &httpResponse({ code => 200, body => $body });
	#                }
	#        }
	#		 else
	#		 {
	#                # Success
	#                        my $body = {
	#                                description => "Modify farm $farmname",
	#                                params => $json_obj,
	#                        };
	#
	#						 &httpResponse({ code => 200, body => $body });
	#        }
	#}
	#else
	#{
	#        # Error
	#        my $errormsg = "Errors found trying to modify farm $farmname";
	#        my $body = {
	#                description => "Modify farm $farmname",
	#                error => "true",
	#                message => $errormsg
	#        };
	#
	#		 &httpResponse({ code => 400, body => $body });
	#}

	# Check errors and print JSON
	if ( $error ne "true" )
	{
		&zenlog(
				  "ZAPI success, some parameters have been changed in farm $farmname." );

		if ( $changedname ne "true" )
		{
			&setFarmRestart( $farmname );

			# Success
			my $body = {
				description => "Modify farm $farmname",
				params      => $json_obj,
				status      => 'needed restart',
				info =>
				  "There're changes that need to be applied, stop and start farm to apply them!"
			};

			&httpResponse({ code => 200, body => $body });
		}
		else
		{
			# Success
			my $body = {
						 description => "Modify farm $farmname",
						 params      => $json_obj,
			};

			&httpResponse({ code => 200, body => $body });
		}
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to modify a gslb farm $farmname, it's not possible to modify the farm."
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



#
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -d '{"rname":"ww2","ttl":"8","type":"DYNA","rdata":"sev2","zone":"zone1"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB/zones/zone1/resources/3
#
#####Documentation of PUT RESOURCES####
#**
#  @api {put} /farms/<farmname>/zones/<zoneid>/resources/<resourceid> Modify a gslb Resource
#  @apiGroup Farm Modify
#  @apiName PutResource
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {Number} resourceid Resource ID, unique ID.
#  @apiDescription Modify the params of a resource of a zone in a GSLB Farm
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {String}        zone                     It's the zone where the resource will be created.
# @apiSuccess   {Number}	ttl		The Time to Live value for the current record.
# @apiSuccess   {String}        type		DNS record type. The options are: NS, A, AAAA, CNAME, DYNA, SRV, PTR,NAPTR, TXT and MX.
# @apiSuccess   {String}        rdata		It’s the real data needed by the record type.
# @apiSuccess	{String}	rname		Resource's name.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify resource 3 in farm FarmGSLB",
#   "params" : [
#      {
#         "zone" : "zone1"
#      },
#      {
#         "ttl" : "8"
#      },
#      {
#         "type" : "DYNA"
#      },
#      {
#         "rdata" : "sev2"
#      },
#      {
#         "rname" : "www"
#      }
#   ]
#}
#
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"rname":"www","ttl":"8","type":"DYNA","rdata":"sev2",
#       "zone":"zone1"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmGSLB/zones/zone1/resources/3
#
# @apiSampleRequest off
#
#**

sub modify_zone_resource # ( $json_obj, $farmname, $zone, $id_resource )
{
	my ( $json_obj, $farmname, $zone, $id_resource ) = @_;

	my $description = "Modify zone resource";
	my $error;

	# validate FARM NAME
	if ( &getFarmFile( $farmname ) == -1 )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $output = {
					   description => $description,
					   error       => "true",
					   message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# validate FARM TYPE
	if ( &getFarmType( $farmname ) ne 'gslb' )
	{
		my $errormsg = "Only GSLB profile is supported for this request.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# validate ZONE
	unless ( grep { $_ eq $zone } &getFarmZones( $farmname ) )
	{
		my $errormsg = "Could not find the requested zone.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $backendsvs = &getFarmVS( $farmname, $zone, "resources" );
	my @be = split ( "\n", $backendsvs );
	my ( $resource_line ) = grep { /;index_$id_resource$/ } @be;

	# validate RESOURCE
	unless ( $resource_line )
	{
		my $errormsg = "Could not find the requested resource.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# read resource
	my $rsc;

	( $rsc->{ name }, $rsc->{ ttl }, $rsc->{ type }, $rsc->{ data }, $rsc->{ id } )
	  = split ( /(?:\t| ;index_)/, $resource_line );

	# Functions
	if ( exists ( $json_obj->{ rname } ) )
	{
		if ( &getValidFormat( 'resource_name', $json_obj->{ rname } ) )
		{
			$rsc->{ name } = $json_obj->{ rname };
		}
		else
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the resources in a farm $farmname, invalid rname, can't be blank."
			);
		}
	}

	if ( !$error && exists ( $json_obj->{ ttl } ) )
	{
		if ( $json_obj->{ ttl } == undef || ( &getValidFormat( 'resource_ttl', $json_obj->{ ttl } ) && $json_obj->{ ttl } ) )
		{
			if ( $json_obj->{ ttl } == undef )
			{
				$rsc->{ ttl } = '';
			}
			else
			{
				$rsc->{ ttl } = $json_obj->{ ttl };
			}
		}
		else
		{
			$error = "true";
			&zenlog(
				  "ZAPI error, trying to modify the resources in a farm $farmname, invalid ttl."
			);
		}
	}


	my $auxType = $rsc->{ type };
	my $auxData = $rsc->{ data };

	if ( !$error && exists ( $json_obj->{ type } ) )
	{
		if ( &getValidFormat( 'resource_type', $json_obj->{ type } ) )
		{
			$auxType = $json_obj->{ type };
		}
		else
		{
			$error = "true";
			&zenlog(
				 "ZAPI error, trying to modify the resources in a farm $farmname, invalid type."
			);
		}
	}

	if ( !$error && exists ( $json_obj->{ rdata } ) )
	{
		#~ if ( &getValidFormat( 'resource_type', $json_obj->{ rdata } ) )
		#~ {
			$auxData = $json_obj->{ rdata };
		#~ }
		#~ else
		#~ {
			#~ $error = "true";
			#~ &zenlog(
				#~ "ZAPI error, trying to modify the resources in a farm $farmname, invalid rdata, can't be blank."
			#~ );
		#~ }
	}
	
	# validate RESOURCE DATA
	unless ( ! grep ( /$auxData/, &getGSLBFarmServices ( $farmname ) && $auxType eq 'DYNA' ) && 
						&getValidFormat( "resource_data_$auxType", $auxData ) )
	{
		my $errormsg = "If you choose $auxType type, ";
		
		$errormsg .= "RDATA must be a valid IPv4 address," 		if ($auxType eq "A" ); 
		$errormsg .= "RDATA must be a valid IPv6 address,"		if ($auxType eq "AAAA" ); 
		$errormsg .= "RDATA format is not valid,"						if ($auxType eq "NS" ); 
		$errormsg .= "RDATA must be a valid format ( foo.bar.com ),"		if ($auxType eq "CNAME" );
		$errormsg .= "RDATA must be a valid service,"									if ( $auxType eq 'DYNA' ); 
		$errormsg .= "RDATA must be a valid format ( mail.example.com ),"		if ( $auxType eq 'MX' ); 
		$errormsg .= "RDATA must be a valid format ( 10 60 5060 host.example.com ),"		if ( $auxType eq 'SRV' ); 
		$errormsg .= "RDATA must be a valid format ( foo.bar.com ),"			if ( $auxType eq 'PTR' ); 
		# TXT and NAPTR input let all characters
		
		&zenlog( $errormsg );

		# Error
		#~ $errormsg =
		  #~ "The parameter zone resource server (rdata) doesn't correct format for this type, please insert a valid value.";
		  
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
	else
	{
		$rsc->{ data } = $auxData;
		$rsc->{ type } =  $auxType;
	}
	
	if ( !$error )
	{
		my $status = &setFarmZoneResource(
										   $id_resource,
										   $rsc->{ name },
										   $rsc->{ ttl },
										   $rsc->{ type },
										   $rsc->{ data },
										   $farmname,
										   $zone,
		);

		if ( $status == -1 )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the resources in a farm $farmname, it's not possible to modify the resource $id_resource in zone $zone."
			);
		}
		elsif ($status == -2)
		{
			# Error
			my $errormsg = "The resource with ID $id_resource does not exist.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 404, body => $body });
		}
	}

	# Print params
	if ( !$error )
	{
		&zenlog(
			"ZAPI success, some parameters have been changed in the resource $id_resource in zone $zone in farm $farmname."
		);

		# Success
		my $message = "Resource modified";
		my $body = {
					 description => $description,
					 success       => "true",
					 message      => $message,
		};
		
		if(  $checkConf = &getGSLBCheckConf  ( $farmname ) )
		{	
			if ( $checkConf =~ /^(.+?)\s/ )
			{
				$checkConf = "The resource $1 gslb farm break the configuration. Please check the configuration";
			}
			$body->{ params }->{ warning }  =  $checkConf;
		}

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to modify the resources in a farm $farmname, it's not possible to modify the resource."
		);

		# Error
		my $errormsg = "Errors found trying to modify farm $farmname";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

#
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -d '{"defnamesv":"ns1"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB/zones/zone1
#
#####Documentation of PUT ZONE####
#**
#  @api {put} /farms/<farmname>/zones/<zoneid> Modify a gslb Zone
#  @apiGroup Farm Modify
#  @apiName PutZone
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {String} zoneid Zone name, unique ID.
#  @apiDescription Modify the params of a Zone in a GSLB Farm
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {String}        defnamesv		This will be the entry point root name server that will be available as the Start of Authority (SOA) DNS record.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify zone zone1 in farm FarmGSLB",
#   "params" : [
#      {
#         "defnamesv" : "ns1"
#      }
#   ]
#}
#
#
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"defnamesv":"ns1"}'
#       https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmGSLB/zones/zone1
#
# @apiSampleRequest off
#
#**

sub modify_zones # ( $json_obj, $farmname, $zone )
{
	my ( $json_obj, $farmname, $zone ) = @_;

	if ( $farmname =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to modify the zones in a farm $farmname, invalid farmname, can't be blank."
		);

		# Error
		my $errormsg = "Invalid farm name, please insert a valid value.";
		my $body = {
					 description => "Modify zone",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
	
	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 ) {
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => "Modify zone",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	$error = "false";

	# Functions
	if ( $json_obj->{ defnamesv } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify the zones in a farm $farmname, invalid defnamesv, can't be blank."
		);
	}

	if ( $error eq "false" )
	{
		&setFarmVS( $farmname, $zone, "ns", $json_obj->{ defnamesv } );
		if ( $? eq 0 )
		{
			&runFarmReload( $farmname );
		}
		else
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the zones in a farm $farmname, it's not possible to modify the zone $zone."
			);
		}
	}

	# Print params
	if ( $error ne "true" )
	{
		&zenlog(
			"ZAPI success, some parameters have been changed  in zone $zone in farm $farmname."
		);

		# Success
		my $body = {
					 description => "Modify zone $zone in farm $farmname",
					 params      => $json_obj,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to modify the zones in a farm $farmname, it's not possible to modify the zone $zone."
		);

		# Error
		my $errormsg = "Errors found trying to modify farm $farmname";
		my $body = {
					 description => "Modify zone $zone in farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}


1;
