#!/usr/bin/perl -w

##############################################################################
#
#     This file is part of the Zen Load Balancer Enterprise Edition software
#     package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This file cannot be distributed, released in public domain and/or for
#     commercial purposes.
#
###############################################################################

#
#####Documentation of PUT TCP####
#**
#  @api {put} /farms/<farmname> Modify a tcp|udp Farm
#  @apiGroup Farm Modify
#  @apiName PutFarm
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Modify the params in a TCP|UDP Farm
#  @apiVersion 2.1.0
#
#
#
# @apiSuccess   {String}                algorithm       Type of load balancing algorithm used in the Farm. The options are: roundrobin, hash, weight or prio.
# @apiSuccess   {Number}                blacklist       This value in seconds is the period to get out a blacklisted real server and checks if is alive.
# @apiSuccess   {Number}                vport                   PORT of the farm, where is listening the virtual service.
# @apiSuccess   {String}                persistence     With this option enabled all the clients with the same ip address will be connected to the same server. The options are true and false.
# @apiSuccess   {Number}                maxclients      The max number of clients that will be possible to memorize.
# @apiSuccess   {Number}                maxservers      It’s the max number of real servers that the farm will be able to have configured.
# @apiSuccess   {String}                newfarmname     The new Farm's name.
# @apiSuccess   {Number}                timeout         It’s the max seconds that the real server has to respond for a request.
# @apiSuccess   {String}                vip                     IP of the farm, where is listening the virtual service.
# @apiSuccess   {Number}                tracking                is the max time of life for this clients to be memorized (the max client age).
# @apiSuccess   {Number}                connmax         It’s the max value of established connections and active clients that the virtual service will be able to manage.
# @apiSuccess   {String}                xforwardedfor   This option enables the HTTP header X-Forwarded-For to provide to the real server the ip client address.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify farm newfarmTCP",
#   "params" : [
#      {
#         "algorithm" : "prio"
#      },
#      {
#         "blacklist" : "39"
#      },
#      {
#         "vport" : "5432"
#      },
#      {
#         "persistence" : "false"
#      },
#      {
#         "maxclients" : "2000"
#      },
#      {
#         "maxservers" : "99"
#      },
#      {
#         "newfarmname" : "newFarmTCP2"}
#      {
#         "timeout" : "8"
#      },
#      {
#         "vip" : "178.62.126.152"
#      },
#      {
#         "tracking" : "9"
#      },
#      {
#         "connmax" : "513"
#      },
#      {
#         "xforwardedfor" : "true"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"algorithm":"prio","persistence":"false","maxclients":"2000","tracking":"10",
#       "newfarmname":"newFarmTCP2","connmax":"513",,"maxservers":"100","xforwardedfor":"false","vip":"178.62.126.152",
#       "vport":"54321","timeout":"10","blacklist":"40"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/newFarmTCP
#
# @apiSampleRequest off
#
#**

our $origin;
if ( $origin ne 1 )
{
	exit;
}

my $out_p = [];

use CGI;
use JSON;

my $q        = CGI->new;
my $json     = JSON->new;
my $data     = $q->param( 'PUTDATA' );
my $json_obj = $json->decode( $data );

my $j = JSON::XS->new->utf8->pretty( 1 );
$j->canonical( $enabled );

#global info for a farm
$maxtimeout   = "10000";
$maxmaxclient = "3000000";
$#maxsimconl  = "32760";
$maxbackend   = "10000";

#use Data::Dumper;
#print Dumper($json_obj);

my $reload_flag  = "false";
my $restart_flag = "false";
my $error        = "false";

#foreach $key (keys %$json_obj) {
#       printf "%s => '%s'\n", $key, $json_obj->{$key};
#}


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



if ( exists ( $json_obj->{ algorithm } ) )
{
	if ( $json_obj->{ algorithm } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid algorithm, can't be blank."
		);
	}
	if ( $json_obj->{ algorithm } =~ /^roundrobin|hash|weight|prio$/ )
	{
		my $status = &setFarmAlgorithm( $json_obj->{ algorithm }, $farmname );
		if ( $status == -1 )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a tcp farm $farmname, some errors happened trying to modify the algorithm."
			);
		}
	}
	else
	{
		$error = "true";
		&zenlog(
			   "ZAPI error, trying to modify a l4xnat farm $farmname, invalid algorithm." );
	}
}

if ( exists ( $json_obj->{ persistence } ) )
{
	if ( $json_obj->{ persistence } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid persistence, can't be blank."
		);
	}
	if ( $json_obj->{ persistence } =~ /^true|false$/ )
	{
		my $status = &setFarmPersistence( $json_obj->{ persistence }, $farmname );
		if ( $status == -1 )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a tcp farm $farmname, some errors happened trying to modify the persistence."
			);
		}
	}
	else
	{
		$error = "true";
		&zenlog(
				"ZAPI error, trying to modify a tcp farm $farmname, invalid persistence." );
	}
}

# Modify Backend response timeout secs
if ( exists ( $json_obj->{ timeout } ) )
{
	if ( $json_obj->{ timeout } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid timeout, can't be blank."
		);
	}
	elsif ( !$json_obj->{ timeout } =~ /^\d+$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid timeout, it must be a numeric value."
		);
	}
	elsif ( !$json_obj->{ timeout } > $maxtimeout )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid timeout, the max timeout value is $maxtimeout."
		);
	}
	else
	{
		my $status = &setFarmTimeout( $json_obj->{ timeout }, $farmname );
		if ( $status == -1 )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a tcp farm $farmname, some errors happened trying to modify the timeout."
			);
		}
		else
		{
			$restart_flag = "true";
		}
	}
}

# Modify Add X-Forwarded-For header to http requests
if ( exists ( $json_obj->{ xforwardedfor } ) )
{
	if ( $json_obj->{ xforwardedfor } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid xforwardedfor, can't be blank."
		);
	}
	if ( $json_obj->{ xforwardedfor } =~ /^true|false$/ )
	{
		my $status = &setFarmXForwFor( $json_obj->{ xforwardedfor }, $farmname );
		if ( $status == -1 )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a tcp farm $farmname, some errors happened trying to modify the xforwardedfor."
			);
		}
	}
	else
	{
		$error = "true";
		&zenlog(
			  "ZAPI error, trying to modify a tcp farm $farmname, invalid xforwardedfor." );
	}
}

# Modify Frequency to check resurrected backends secs
if ( exists ( $json_obj->{ blacklist } ) )
{
	if ( $json_obj->{ blacklist } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid blacklist, can't be blank."
		);
	}
	if ( $json_obj->{ blacklist } =~ /^\d+$/ )
	{
		my $status = &setFarmBlacklistTime( $json_obj->{ blacklist }, $farmname );
		if ( $status == -1 )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a tcp farm $farmname, some errors happened trying to modify the blacklist."
			);
		}
	}
	else
	{
		$error = "true";
		&zenlog(
				  "ZAPI error, trying to modify a tcp farm $farmname, invalid blacklist." );
	}
}

# Get current max_clients & tracking time
@client = &getFarmMaxClientTime( $farmname );
if ( @client == -1 )
{
	$maxclients = 256;
	$tracking   = 10;
}
else
{
	$maxclients = @client[0];
	$tracking   = @client[1];
}

# Modify both max_clients & tracking
if (    exists ( $json_obj->{ maxclients } )
	 && exists ( $json_obj->{ tracking } ) )
{
	if ( $json_obj->{ maxclients } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid maxclients, can't be blank."
		);
	}
	elsif ( !$json_obj->{ maxclients } =~ /^\d+$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid maxclients, it must be a numeric value."
		);
	}
	elsif ( $json_obj->{ maxclients } > $maxmaxclient )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid maxclients value, the max value is $maxmaxclient."
		);
	}
	else
	{
		if ( exists ( $json_obj->{ tracking } ) )
		{
			if ( $json_obj->{ tracking } =~ /^$/ )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify a tcp farm $farmname, invalid tracking, can't be blank."
				);
			}
			elsif ( !$json_obj->{ tracking } =~ /^\d+$/ )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify a tcp farm $farmname, invalid tracking, it must be a numeric value."
				);
			}
			else
			{

				# No error
				my $status = &setFarmMaxClientTime( $json_obj->{ maxclients },
													$json_obj->{ tracking }, $farmname );
				if ( $status == -1 )
				{
					$error = "true";
					&zenlog(
						"ZAPI error, trying to modify a tcp farm $farmname, some errors happened trying to modify the maxclients and the tracking."
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

# Modify only max_clients param
if ( exists ( $json_obj->{ maxclients } )
	 && !exists ( $json_obj->{ tracking } ) )
{
	if ( $json_obj->{ maxclients } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid maxclients, can't be blank."
		);
	}
	elsif ( !$json_obj->{ maxclients } =~ /^\d+$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid maxclients, it must be a numeric value."
		);
	}
	elsif ( $json_obj->{ maxclients } > $maxmaxclient )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid maxclients value, the max value is $maxmaxclient."
		);
	}
	else
	{
		# No error
		my $status =
		  &setFarmMaxClientTime( $json_obj->{ maxclients }, $tracking, $farmname );
		if ( $status == -1 )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a tcp farm $farmname, some errors happened trying to modify the maxclients."
			);
		}
		else
		{
			$restart_flag = "true";
		}
	}
}

# Modify only tracking param
if (   !exists ( $json_obj->{ maxclients } )
	 && exists ( $json_obj->{ tracking } ) )
{
	if ( $json_obj->{ tracking } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid tracking, can't be blank."
		);
	}
	elsif ( !$json_obj->{ tracking } =~ /^\d+$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid tracking, it must be a numeric value."
		);
	}
	else
	{
		# No error
		my $status =
		  &setFarmMaxClientTime( $maxclients, $json_obj->{ tracking }, $farmname );
		if ( $status == -1 )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a tcp farm $farmname, some errors happened trying to modify the tracking."
			);
		}
		else
		{
			$restart_flag = "true";
		}
	}
}

# Modify Max number of simultaneous connections that manage in Virtual IP
if ( exists ( $json_obj->{ connmax } ) )
{
	if ( $json_obj->{ connmax } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid connmax, can't be blank."
		);
	}
	elsif ( !$json_obj->{ connmax } =~ /^\d+$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid connmax, it must be a numeric value."
		);
	}
	elsif ( !$json_obj->{ connmax } > $maxsimconn )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid connmax value, the max value is $maxsimconn."
		);
	}
	else
	{
		my $status = &setFarmMaxConn( $json_obj->{ connmax }, $farmname );
		if ( $status == -1 )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a tcp farm $farmname, some errors happened trying to modify the connmax."
			);
		}
		else
		{
			$restart_flag = "true";
		}
	}
}

# Modify Max number of real ip servers
if ( exists ( $json_obj->{ maxservers } ) )
{
	if ( $json_obj->{ maxservers } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid maxservers, can't be blank."
		);
	}
	elsif ( !$json_obj->{ maxservers } =~ /^\d+$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid maxservers, it must be a numeric value."
		);
	}
	elsif ( !$json_obj->{ maxservers } > $maxbackend )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid maxservers value, the max value is $maxbackend."
		);
	}
	else
	{
		my $status = &setFarmMaxServers( $json_obj->{ maxservers }, $farmname );
		if ( $status == -1 )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a tcp farm $farmname, some errors happened trying to modify the maxservers."
			);
		}
		else
		{
			$restart_flag = "true";
		}
	}
}

# Get current vip & vport
$vip   = &getFarmVip( "vip",  $farmname );
$vport = &getFarmVip( "vipp", $farmname );

# Modify both vip & vport
if ( exists ( $json_obj->{ vip } ) && exists ( $json_obj->{ vport } ) )
{
	if ( $json_obj->{ vip } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid vip, can't be blank."
		);
	}
	elsif ( !$json_obj->{ vip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
	{
		$error = "true";
		&zenlog( "ZAPI error, trying to modify a tcp farm $farmname, invalid vip." );
	}
	else
	{
		if ( exists ( $json_obj->{ vport } ) )
		{
			if ( $json_obj->{ vport } =~ /^$/ )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify a tcp farm $farmname, invalid vport, can't be blank."
				);
			}
			elsif ( !$json_obj->{ vport } =~ /^\d+$/ )
			{
				$error = "true";
				&zenlog( "ZAPI error, trying to modify a tcp farm $farmname, invalid vport." );
			}
			else
			{

				# No error
				my $status =
				  &setFarmVirtualConf( $json_obj->{ vip }, $json_obj->{ vport }, $farmname );
				if ( $status == -1 )
				{
					$error = "true";
					&zenlog(
						"ZAPI error, trying to modify a tcp farm $farmname, invalid vport or invalid vip."
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

# Modify only vip
if ( exists ( $json_obj->{ vip } ) && !exists ( $json_obj->{ vport } ) )
{
	if ( $json_obj->{ vip } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid vip, can't be blank."
		);
	}
	elsif ( !$json_obj->{ vip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
	{
		$error = "true";
		&zenlog( "ZAPI error, trying to modify a tcp farm $farmname, invalid vip." );
	}
	else
	{
		# No error
		my $status = &setFarmVirtualConf( $json_obj->{ vip }, $vport, $farmname );
		if ( $status == -1 )
		{
			$error = "true";
			&zenlog( "ZAPI error, trying to modify a tcp farm $farmname, invalid vip." );
		}
		else
		{
			$restart_flag = "true";
		}
	}
}

# Modify only vport
if ( !exists ( $json_obj->{ vip } ) && exists ( $json_obj->{ vport } ) )
{
	if ( $json_obj->{ vport } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify a tcp farm $farmname, invalid vport, can't be blank."
		);
	}
	elsif ( !$json_obj->{ vport } =~ /^\d+$/ )
	{
		$error = "true";
		&zenlog( "ZAPI error, trying to modify a tcp farm $farmname, invalid vport." );
	}
	else
	{
		# No error
		my $status = &setFarmVirtualConf( $vip, $json_obj->{ vport }, $farmname );
		if ( $status == -1 )
		{
			$error = "true";
			&zenlog( "ZAPI error, trying to modify a tcp farm $farmname, invalid vport." );
		}
		else
		{
			$restart_flag = "true";
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
			"ZAPI error, trying to modify a tcp farm $farmname, invalid newfarmname, can't be blank."
		);
	}
	else
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
					"ZAPI error, trying to modify a tcp farm $farmname, the farm $json_obj->{newfarmname} already exists, try another name."
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
						"ZAPI error, trying to modify a tcp farm $farmname, the name of the farm can't be modified, delete the farm and create a new one."
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
					"ZAPI error, trying to modify a tcp farm $farmname, invalid newfarmname." );
		}
	}
}

# Restart farm if needed
if ( $restart_flag eq "true" )
{
	&runFarmStop( $farmname, "true" );
	&runFarmStart( $farmname, "true" );
}

# Print params
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
		"ZAPI error, trying to modify a tcp farm $farmname, it's not possible to modify the farm."
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

1
