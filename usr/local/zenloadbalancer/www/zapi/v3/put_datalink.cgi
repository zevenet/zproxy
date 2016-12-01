#!/usr/bin/perl -w

######### PUT DATALINK
#
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -d '{"algorithm": "prio", "newfarmname":"newDATAFARM","interfacevip":"eth0 178.62.126.152"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/DATAFARM
#
#
#####Documentation of PUT DATALINK####
#**
#  @api {put} /farms/<farmname> Modify a datalink Farm
#  @apiGroup Farm Modify
#  @apiName PutFarmDATALINK
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Modify the params in a DATALINK Farm
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess	{String}		algorithm	Type of load balancing algorithm used in the Farm. The options are: weight or prio.
# @apiSuccess	{String}		newfarmname	The new Farm's name.
# @apiSuccess	{String}		interfacevip	P of the farm, where is listening the virtual service and the interface.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify farm newDATAFARM",
#   "params" : [
#      {
#         "algorithm" : "prio"
#      },
#      {
#         "interfacevip" : "eth0 178.62.126.152"
#      },
#      {
#         "newfarmname" : "newDATAFARM"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"algorithm":"prio","interfacevip":"eth0 178.62.126.152",
#       "newfarmname":"newDATAFARM"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/newDATAFARM
#
# @apiSampleRequest off
#
#**

sub modify_datalink_farm # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	my $reload_flag  = "false";
	my $restart_flag = "false";
	my $error        = "false";

	####### Functions

	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 ) {
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $output = {
					   description => "Modify farm",
					   error       => "true",
					   message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# Modify Farm's Name
	if ( exists ( $json_obj->{ newfarmname } ) )
	{
		unless ( &getFarmStatus( $farmname ) eq 'up' )
		{
			&zenlog(
				"ZAPI error, trying to modify a datalink farm $farmname, cannot change the farm name while running"
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
				"ZAPI error, trying to modify a datalink farm $farmname, invalid newfarmname, can't be blank."
			);
		}
		else
		{
			if ($json_obj->{newfarmname} ne $farmname)
			{
				#Check if farmname has correct characters (letters, numbers and hyphens)
				if ( $json_obj->{ newfarmname } =~ /^[a-zA-Z0-9\-]*$/ )
				{
					#Check if the new farm's name alredy exists
					my $newffile = &getFarmFile( $json_obj->{ newfarmname } );
					if ( $newffile != -1 )
					{
						$error = "true";
						&zenlog(
							"ZAPI error, trying to modify a datalink farm $farmname, the farm $json_obj->{newfarmname} already exists, try another name."
						);
					}
					else
					{
						#Change farm name
						my $fnchange = &setNewFarmName( $farmname, $json_obj->{ newfarmname } );
						if ( $fnchange == -1 )
						{
							&error = "true";
							&zenlog(
								"ZAPI error, trying to modify a datalink farm $farmname, the name of the farm can't be modified, delete the farm and create a new one."
							);
						}
						else
						{
							$restart_flag = "true";
							$farmname     = $json_obj->{ newfarmname };
						}
					}
				}
				else
				{
					$error = "true";
					&zenlog(
						  "ZAPI error, trying to modify a datalink farm $farmname, invalid newfarmname."
					);
				}
			}
		}
	}

	# Modify Load Balance Algorithm
	if ( exists ( $json_obj->{ algorithm } ) )
	{
		if ( $json_obj->{ algorithm } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a datalink farm $farmname, invalid algorithm, can't be blank."
			);
		}
		if ( $json_obj->{ algorithm } =~ /^weight|prio$/ )
		{
			$status = &setFarmAlgorithm( $json_obj->{ algorithm }, $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify a datalink farm $farmname, some errors happened trying to modify the algorithm."
				);
			}
			else
			{
				$restart_flag = "true";
			}
		}
		else
		{
			$error = "true";
			&zenlog(
				 "ZAPI error, trying to modify a datalink farm $farmname, invalid algorithm." );
		}
	}

	# Modify Virtual IP and Interface
	if ( exists ( $json_obj->{ interfacevip } ) )
	{
		if ( $json_obj->{ interfacevip } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a datalink farm $farmname, invalid interfacevip, can't be blank."
			);
		}
		elsif ( $json_obj->{ interfacevip } =~ /^[a-zA-Z0-9.]+/ )
		{
			my @fvip = split ( " ", $json_obj->{ interfacevip } );
			my $fdev = @fvip[0];
			my $vip  = @fvip[1];

			if ( $fdev eq "" )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify a datalink farm $farmname, invalid Interface value."
				);
			}
			elsif ( $vip eq "" )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify a datalink farm $farmname, invalid Virtual IP value."
				);
			}
			else
			{
				$status = &setFarmVirtualConf( $vip, $fdev, $farmname );
				if ( $status != -1 )
				{
					$restart_flag = "true";
				}
				else
				{
					$error = "true";
					&zenlog(
						"ZAPI error, trying to modify a datalink farm $farmname, it's not possible to change the farm virtual IP and interface."
					);
				}
			}

		}
		else
		{
			$error = "true";
			&zenlog(
				 "ZAPI error, trying to modify a datalink farm $farmname, invalid interfacevip."
			);
		}
	}

	# Restart Farm
	if ( $restart_flag eq "true" )
	{
		&runFarmStop( $farmname, "true" );
		&runFarmStart( $farmname, "true" );
	}

	# Check errors and print JSON
	if ( $error ne "true" )
	{
		&zenlog(
				  "ZAPI success, some parameters have been changed in farm $farmname." );

		# Success
		my $body = {
					 description => "Modify farm $farmname",
					 params      => $json_obj
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to modify a datalink farm $farmname, it's not possible to modify the farm."
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
