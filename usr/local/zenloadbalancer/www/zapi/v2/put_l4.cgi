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

######### PUT L4XNAT
#
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"algorithm":"weight","persistence":"none","newfarmname":"newfarmEUL4","protocol":"tcp","nattype":"nat","ttl":"125","vip":"178.62.126.152","vport":"81"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/L4FARM
#
#
#
#####Documentation of PUT L4XNAT####
#**
#  @api {put} /farms/<farmname> Modify a l4xnat Farm
#  @apiGroup Farm Modify
#  @apiName PutFarmL4XNAT
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Modify the params in a L4XNAT Farm
#  @apiVersion 2.0.0
#
#
#
# @apiSuccess	{String}		algorithm	Type of load balancing algorithm used in the Farm. The options are: leastconn, weight or prio.
# @apiSuccess	{String}		persistence	With this option enabled all the clients with the same ip address will be connected to the same server. The options are: none or ip.
# @apiSuccess	{String}		newfarmname	The new Farm's name.
# @apiSuccess	{String}		protocol	This field specifies the protocol to be balanced at layer 4. The options are: all, tcp, udp, sip, ftp or tftp.
# @apiSuccess	{String}		nattype		This field indicates the NAT type which means how the load balancer layer 4 core is going to operate. The options are: nat or dnat.
# @apiSuccess	{Number}		ttl			This field value indicates the number of seconds that the persistence between the client source and the backend is being assigned.
# @apiSuccess	{Number}		vport			PORT of the farm, where is listening the virtual service.
# @apiSuccess	{String}		vip			IP of the farm, where is listening the virtual service.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify farm newfarmEUL4",
#   "params" : [
#      {
#         "algorithm" : "weight"
#      },
#      {
#         "protocol" : "tcp"
#      },
#      {
#         "ttl" : "125"
#      },
#      {
#         "vport" : "81"
#      },
#      {
#         "persistence" : "none"
#      },
#      {
#         "newfarmname" : "newfarmL4"
#      },
#      {
#         "vip" : "178.62.126.152"
#      },
#      {
#         "nattype" : "nat"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"algorithm":"weight","persistence":"none","newfarmname":"newfarmL4",
#       "protocol":"tcp","nattype":"nat","ttl":"125","vip":"178.62.126.152","vport":"81"}'
#        https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/L4FARM
#
# @apiSampleRequest off
#
#**

our $origin;
if ( $origin ne 1 )
{
	exit;
}

####### Params

my $out_p = [];

use CGI;
use JSON;

my $q        = CGI->new;
my $json     = JSON->new;
my $data     = $q->param( 'PUTDATA' );
my $json_obj = $json->decode( $data );

my $j = JSON::XS->new->utf8->pretty( 1 );
$j->canonical( $enabled );

# Flags
my $reload_flag  = "false";
my $restart_flag = "false";
my $error        = "false";

# Check that the farm exists
if ( &getFarmFile( $farmname ) == -1 ) {
	# Error
	print $q->header(
	-type=> 'text/plain',
	-charset=> 'utf-8',
	-status=> '404 Not Found'
	);
	$errormsg = "The farmname $farmname does not exists.";
	my $output = $j->encode({
			description => "Modify farm",
			error => "true",
			message => $errormsg
	});
	print $output;
	exit;

}

# Get current vip & vport
$vip   = &getFarmVip( "vip",  $farmname );
$vport = &getFarmVip( "vipp", $farmname );

####### Functions

# Modify Load Balance Algorithm
if ( exists ( $json_obj->{ algorithm } ) )
{
	if ( $json_obj->{ algorithm } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a l4xnat farm $farmname, invalid algorithm, can't be blank."
		);
	}
	if ( $json_obj->{ algorithm } =~ /^leastconn|weight|prio$/ )
	{
		$status = &setFarmAlgorithm( $json_obj->{ algorithm }, $farmname );
		if ( $status == -1 )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a l4xnat farm $farmname, some errors happened trying to modify the algorithm."
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
			   "ZAPI error, trying to modify a l4xnat farm $farmname, invalid algorithm." );
	}
}

# Modify Persistence Mode
if ( exists ( $json_obj->{ persistence } ) )
{
	if ( $json_obj->{ persistence } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a l4xnat farm $farmname, invalid persistence, can't be blank."
		);
	}
	if ( $json_obj->{ persistence } =~ /^none|ip$/ )
	{
		if (&getFarmPersistence($farmname) ne $json_obj->{persistence})
		{
			$statusp = &setFarmSessionType( $json_obj->{ persistence }, $farmname, "" );
			if ( $statusp != 0 )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify a l4xnat farm $farmname, some errors happened trying to modify the persistence."
				);
			}
			else
			{
				$restart_flag = "true";
			}
		}
	}
	else
	{
		$error = "true";
		&zenlog(
			 "ZAPI error, trying to modify a l4xnat farm $farmname, invalid persistence." );
	}
}

# Modify Protocol Type
if ( exists ( $json_obj->{ protocol } ) )
{
	if ( $json_obj->{ protocol } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a l4xnat farm $farmname, invalid protocol, can't be blank."
		);
	}
	if ( $json_obj->{ protocol } =~ /^all|tcp|udp|sip|ftp|tftp$/ )
	{
		$status = &setFarmProto( $json_obj->{ protocol }, $farmname );
		if ( $status != 0 )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a l4xnat farm $farmname, some errors happened trying to modify the protocol."
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
				"ZAPI error, trying to modify a l4xnat farm $farmname, invalid protocol." );
	}
}

# Modify NAT Type
if ( exists ( $json_obj->{ nattype } ) )
{
	if ( $json_obj->{ nattype } =~ /^$/ )
	{
		&error = "true";
		&zenlog(
			"ZAPI error, trying to modify a l4xnat farm $farmname, invalid nattype, can't be blank."
		);
	}
	if ( $json_obj->{ nattype } =~ /^nat|dnat$/ )
	{
		if (&getFarmNatType($farmname) ne $json_obj->{nattype})
		{
			$status = &setFarmNatType( $json_obj->{ nattype }, $farmname );
			if ( $status != 0 )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify a l4xnat farm $farmname, some errors happened trying to modify the nattype."
				);
			}
			else
			{
				$restart_flag = "true";
			}
		}
	}
	else
	{
		$error = "true";
		&zenlog(
				 "ZAPI error, trying to modify a l4xnat farm $farmname, invalid nattype." );
	}
}

# Modify IP Adress Persistence Time To Limit
if ( exists ( $json_obj->{ ttl } ) )
{
	if ( $json_obj->{ ttl } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a l4xnat farm $farmname, invalid ttl, can't be blank."
		);
	}
	elsif ( $json_obj->{ ttl } =~ /^\d+$/ )
	{
		$status = &setFarmMaxClientTime( 0, $json_obj->{ ttl }, $farmname );
		if ( $status != 0 )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a l4xnat farm $farmname, some errors happened trying to modify the ttl."
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
				  "ZAPI error, trying to modify a l4xnat farm $farmname, invalid ttl." );
	}
}

# Modify only vip
if ( exists ( $json_obj->{ vip } ) && !exists ( $json_obj->{ vport } ) )
{
	if ( $json_obj->{ vip } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a l4xnat farm $farmname, invalid vip, can't be blank."
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
			&zenlog(
					  "ZAPI error, trying to modify a l4xnat farm $farmname, invalid vip." );
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
			"ZAPI error, trying to modify a l4xnat farm $farmname, invalid vport, can't be blank."
		);
	}
	elsif ( !$json_obj->{ vport } =~ /^\d+((\:\d+)*(\,\d+)*)*$/ )
	{
		if ( $json_obj->{ vport } ne "*" )
		{
			$error = "true";
			&zenlog(
					  "ZAPI error, trying to modify a l4xnat farm $farmname, invalid vport." );
		}
	}
	else
	{
		$status = &setFarmVirtualConf( $vip, $json_obj->{ vport }, $farmname );
		if ( $status == -1 )
		{
			$error = "true";
			&zenlog(
					  "ZAPI error, trying to modify a l4xnat farm $farmname, invalid vport." );
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
			"ZAPI error, trying to modify a l4xnat farm $farmname, invalid vip, can't be blank."
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
		if ( exists ( $json_obj->{ vport } ) )
		{
			if ( $json_obj->{ vport } =~ /^$/ )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify a l4xnat farm $farmname, invalid vport, can't be blank."
				);
			}
			elsif ( !$json_obj->{ vport } =~ /^\d+((\:\d+)*(\,\d+)*)*$/ )
			{
				if ( $json_obj->{ vport } ne "*" )
				{
					$error = "true";
					&zenlog(
							  "ZAPI error, trying to modify a l4xnat farm $farmname, invalid vport." );
				}
			}
			else
			{
				$status =
				  &setFarmVirtualConf( $json_obj->{ vip }, $json_obj->{ vport }, $farmname );
				if ( $status == -1 )
				{
					$error = "true";
					&zenlog(
						"ZAPI error, trying to modify a l4xnat farm $farmname, invalid vport or invalid vip."
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
if ( exists ( $json_obj->{ newfarmname } ) )
{
	if ( $json_obj->{ newfarmname } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a l4xnat farm $farmname, invalid newfarmname, can't be blank."
		);
	}
	else
	{
		if ($json_obj->{newfarmname} ne $farmname) {
	
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
							"ZAPI error, trying to modify a l4xnat farm $farmname, the farm $json_obj->{newfarmname} already exists, try another name."
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
								"ZAPI error, trying to modify a l4xnat farm $farmname, the name of the farm can't be modified, delete the farm and create a new one."
							);
						}
						else
						{
							$restart_flag = "true";
							$farmname     = $json_obj->{ newfarmname };
						}
					}
				}
			}
			else
			{
				$error = "true";
				&zenlog(
					 "ZAPI error, trying to modify a l4xnat farm $farmname, invalid newfarmname." );
			}
		}
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
	print $q->header(
					  -type    => 'text/plain',
					  -charset => 'utf-8',
					  -status  => '200 OK'
	);

	foreach $key ( keys %$json_obj )
	{
		push $out_p, { $key => $json_obj->{ $key } };
	}

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );
	my $output = $j->encode(
							 {
							   description => "Modify farm $farmname",
							   params      => $out_p
							 }
	);
	print $output;

}
else
{
	&zenlog(
		"ZAPI error, trying to modify a l4xnat farm $farmname, it's not possible to modify the farm."
	);

	# Error
	print $q->header(
					  -type    => 'text/plain',
					  -charset => 'utf-8',
					  -status  => '400 Bad Request'
	);
	$errormsg = "Errors found trying to modify farm $farmname";
	my $output = $j->encode(
							 {
							   description => "Modify farm $farmname",
							   error       => "true",
							   message     => $errormsg
							 }
	);
	print $output;
	exit;
}

1;
