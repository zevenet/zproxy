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

use warnings;
use strict;

require "/usr/local/zenloadbalancer/www/system_functions.cgi";
require "/usr/local/zenloadbalancer/www/rrd_functions.cgi";
require "/usr/local/zenloadbalancer/www/networking_functions_ext.cgi";

# Supported graphs periods
my $graph_period = {
					 'daily'   => 'd',
					 'weekly'  => 'w',
					 'monthly' => 'm',
					 'yearly'  => 'y',
};

# Get all farm stats
sub getAllFarmStats
{
	my @files = &getFarmList();
	my @farms;

	# FIXME: Verify stats are working with every type of farm

	foreach my $file ( @files )
	{
		my $name   = &getFarmName( $file );
		my $type   = &getFarmType( $name );
		my $status = &getFarmStatus( $name );
		my $vip    = &getFarmVip( 'vip', $name );
		my $port   = &getFarmVip( 'vipp', $name );
		my $established = 0;
		my $pending     = 0;
		$status = "needed restart" if $status eq 'up' && ! &getFarmLock($name);

		if ( $status eq "up" )
		{
			my @netstat = &getConntrack( "", $vip, "", "", "" );

			$established = scalar &getFarmSYNConns( $name, @netstat );
			$pending = scalar &getFarmEstConns( $name, @netstat );
		}

		push @farms,
		  {
			farmname    => $name,
			profile     => $type,
			status      => $status,
			vip         => $vip,
			vport       => $port,
			established => $established,
			pending     => $pending,
		  };
	}
	return \@farms;
}


graphs:
#####Documentation of Graphs####
#**
#  @api {get} /graphs/<param1>/<param2>/<frequency> Request graphs
#  @apiGroup System Stats
#  @apiName GetGraphs
#  @apiParam {String} param1  First parameter. The possible values are system, network or farm.
#  @apiParam {String} param2  Second parameter. The possible values if the first parameter is system are: cpu, disk, load, mem or memsw. The possible values if the first parameter is network are: eth0iface, eth0.1iface, eth1iface... The possible values if the first parameter is farm are: <farmname>-farm, for example httptest-farm.
#  @apiParam {String} frequency Third parameter. The possible values are: daily, weekly, monthly or yearly.
#  @apiDescription Get a graph in base 64 data
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#  "description" : "Graphs",
#  "graph" : "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\nDh48aNAvZRyYb93Y2JiRkfHGG28wjfSjZDSqq6sHDx5MCElISBgyZMi1a9c0UlJ2f++99xoaGpKT\nk+fNmzdo0CDmkKEdc+fOzc7OzsnJmTt3LtOibuhaWlr++OOPjIyMlStXav1x2mF2o5qfnx8XFxcX\nFyc/zzhhwgRm3nDs2LEJEyYwjUuXLh09enRFRcXjjz+u9WdpDf2oqsPPz08oFAYHB69ateru3bus\nGiPsq0qHhczMzK+//nr9+vXffPNNZmam1h+nNQKBwNnZ2c/Pb+vWrV9++aU6WVlZWU1Njb+/v5eX\nV3x8fGVlJSHk9u3b06dP37p1q6enJ8dH6HFUgXYYdq4wZ86cS5cuTZs2rWfPnnPmzHn33XcJIa+9\n9trHH38slUpPnDgxadIkRhkcHLxo0aJVq1Z9+eWXTNVBHSdOnJgxY4abm1t8fLziubG//e1vhJAn\nn3xSXdi5eVFYWBgWFubh4REbG1tbW8s00o8SgzFnDxzHCBplt91/+umnt99++5133omOjtbYnAL9\n+vUbMGDAwIEDfXx8uJXz589//PHHX3zxRaVfKhhVJTo6OgoLC2NiYmJjYwsLC5n68IQJE44ePUoI\nOXr0qHyucPr06fnz5zs6Os6ZM0dpJfwcVUVkMtnVq1dra2u/+uqrpqampKQkdUrD7aushwUXF5es\nrKyNGzdmZWU5OzsredbFACUymay5ubm0tDQsLIypcLDS2dnZ1tZ2/vz58vLy8PDwWbNmEUIWLlwY\nGxsbFxfX7afoa1SBdhj8nsk+ffo8//zzb7/9dn5+/rZt2wghcXFxFRUVq1ateuGFFxwdHRnZwYMH\n33vvPVdX19zc3BdffJHLsa1tQ0MDM79WnBb06NGDee3q6jLkFzISc+bMWbFiRV1dXV1dnfwb0Y+S\n0fD19ZXP2P7444/+/ftrpKTsfvDgwV9++SU7O5v5+4OZdGpNbm7u7t27u5Uxf/va2dk9evRIl4/T\nAvMa1Z9//rm1tXXAgAEDBgxobW39+eefCSFPPvlkQ0NDZWVlQ0PDk08+qd2a9Qv9qHJgb2/v7++f\nnp5eWFjIKjDovsp6WCCEVFVVEUK0qJToC3t7+0GDBqWnpx8/flydxtvbe9GiRS4uLo6OjnPnzr1w\n4QIh5MCBAzt27FA8l8raV7+jCrTAsHOFhISEU6dO3b59u6Wl5ZNPPvH19SWE2NvbT5o06dNPP339\n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\n0KBBhw4dqquru3Llire399ChQ9U10nc/cODAjh07FM+ksPa14JxJ1hE4depUcnKyk5OTs7PzokWL\nOJ6FzJqIaORR5WHOpI77KoNqdmJ5eXlUVJS9vf3Ro0eVfivLseCcSV1CTXXsjpxJk2OCuUJYWFhO\nTg6TM6nY7uPjo3RRwpgxY1JTU61tlsDA25zJ1tbWQ4cOrVixQvGPXdZG1k9XUipdQabuzyBepczp\nd1RZR2Do0KFM+N7t27f/9a9/Kf5WU/p01kREI48qb3MmddxXlbIT9+3bN3HixJSUlOzsbI5zKBac\nM6lpqCnNvmqOSbPWiQlyJjdu3HjkyBE/Pz8meFpOamrqf/3XfynuXhs3bmxqagoKCuK+5dICUL1H\ni4c5k8yn+/v7Z2Zmbt68mTlfy9pI350Sa8uZzM3NLS0tHTp06JAhQ0pKSjiqIPTZiapYcM6kXvZV\npezEWbNmXb9+fcqUKfL/p6rXMRBLyZlk/U+hS6ipjt2RM2lykDMJADAqyJkEwIxAziQAwNgIkDMJ\ngBmCnEkAgPHA3xsAmCM8ug8CAAAAADwEcwUAAAAAcGHinElNkRswciVTgBBCSwebGAAA1GHAuoKA\nDW59t+u0yAwq3e/TM+GdfjqmzBFC8vLyIiMjhUIhxx5i8TmTSphjdh+vciZZoR9VBu3CPy0jZ5IV\n1oM5zbGdQV3OpzGPAEBrDDhXUHoajEX+mgc6pszl5eUtXLgwOTn58uXLHHuIZWT30WN22X18y5lk\nhX5UGbQL/7TsfVU1fpP+wM6a82n8IwDQDhNcr1BZWTl27FgPD4+xY8dWVlYS9Q/DYX5UClWjR2lV\nzBvVqEaiJtCSPg/TELB+d9PmTLKiY8pcZmZmWlpafHy8i4sLx6dYds6kKmaX3ce3nElW6EeV6BD+\nacE5kzrCmvNp/CMA0A7T5ExGR0dXVFRERUUtWbKEqA9LZA1V0xHVqEaiJtCSPg/TELB+d9PmTLKi\nY8pcWVlZTU2Nv7+/l5dXfHw8M3dUxYJzJlkxu+w+vuVMskI/qrqEf1pwziTpLn6TG9acT+MfAYB2\nmGCucObMmblz5zo6Os6bN4+7WsAaqqYjrFGNrIGW9HmYhoCHOZPcaJcy19nZ2dbWdv78+fLy8vDw\n8FmzZqnrZak5k9yYRXYfD3Mmuel2WHQM/7TUnEmZ+vhNGlhzPo1/BADawet7JtWFqqkmUrIiTwhU\n/LXKGtXIw0BLHuZMsqJjypy3t/eiRYtcXFwcHR3nzp174cIF1r4WnDPJinll9/EwZ5IV+lHVJfzT\ngnMmGVTjNylhzfk0yREAaIEJ5gojRozIzs5mciZHjBghb1cNS2QNVSNsiZSs+Pr65uXltbW1KT5N\nljWqkTXQUl0epnHgbc6kEjqmzE2YMIEJVLxz5862bduGDx/O+im8Spnj/6gaObuPtzmTStCPqqbh\nn4pYcM4kg1L8Jgesn66U82mORwDrxARzhU2bNh07dszPz+/48eObNm2St6uGJbKGqhG2REpW3n33\n3WXLlg0ePFjxqhnmbwWlqEbWQEt1eZiGQPVmJB7mTLKiY8rcypUrW1paQkNDxWLx6dOnFb+UItaW\nM2le2X08zJlkRZdMTkId/mkZOZOsMP9BlOI36f/7MAKlnE8+HAEADciZBAAYFeRMAmBGIGcSAGBs\nBMiZBMAMQc4kAMB44O8NAMwRXt8HAQAAAACTg7kCAAAAALjAXAEAAAAAXGCuAAAAAAAuMFcAAAAA\nABc2JSUlt2/frqioMLUTAAAAAPCRHi0tLeqivQAAAAAA/h9WdjaavJt3twAAAABJRU5ErkJggg==\n"
#}
#
#
#@apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#         https://<zenlb_server>:444/zapi/v3/zapi.cgi/graphs/system/cpu/daily
#
#@apiSampleRequest off
#
#**

#Get Graphs
#~ sub get_graphs()
#~ {
	#~ my $gtype     = shift;
	#~ my $gtype2    = shift;
	#~ my $frequency = shift;

	#~ # Check RRD files are generated
	#~ opendir ( DIR, "$rrdap_dir/$rrd_dir" );
	#~ my @rrdlist = grep ( /^*.rrd$/, readdir ( DIR ) );
	#~ closedir DIR;

	#~ if ( @rrdlist eq 0 )
	#~ {
		#~ &zenlog( "ZAPI error, there is no rrd files in folder yet." );

		#~ my $errormsg = "There is no rrd files yet.";
		#~ my $body = {
					 #~ description => "Get graphs",
					 #~ error       => "true",
					 #~ message     => $errormsg
		#~ };

		#~ &httpResponse({ code => 400, body => $body });
	#~ }

	#~ # Error handling
	#~ # First parameter
	#~ if ( $gtype =~ /^$/ )
	#~ {
		#~ &zenlog(
			 #~ "ZAPI error, trying to get graphs, invalid first parameter, can't be blank." );

		#~ my $errormsg =
		  #~ "Invalid first parameter value; the possible values are system, network and farm";
		#~ my $body = {
					 #~ description => "Get graphs",
					 #~ error       => "true",
					 #~ message     => $errormsg
		#~ };

		#~ &httpResponse({ code => 400, body => $body });
	#~ }
	#~ if ( $gtype =~ /^system|network|farm$/ )
	#~ {
		#~ if ( $gtype eq "system" )
		#~ {
			#~ $gtype = "System";
		#~ }
		#~ if ( $gtype eq "network" )
		#~ {
			#~ $gtype = "Network";
		#~ }
		#~ if ( $gtype eq "farm" )
		#~ {
			#~ $gtype = "Farm";
		#~ }
	#~ }
	#~ else
	#~ {
		#~ &zenlog(
			#~ "ZAPI error, trying to get graphs, invalid first parameter, the possible values are system, network and farm."
		#~ );

		#~ my $errormsg =
		  #~ "Invalid first parameter value; the possible values are system, network and farm";
		#~ my $body = {
					 #~ description => "Get graphs",
					 #~ error       => "true",
					 #~ message     => $errormsg
		#~ };

		#~ &httpResponse({ code => 400, body => $body });
	#~ }

	#~ # Second parameter
	#~ if ( $gtype eq "System" )
	#~ {
		#~ if ( $gtype2 =~ /dev/ )
		#~ {
			#~ $gtype2 = $gtype2 . "hd";
		#~ }
	#~ }

	#~ if ( $gtype eq "Network" )
	#~ {
		#~ $gtype2 = $gtype2 . "iface";
	#~ }

	#~ if ( $gtype eq "Farm" )
	#~ {
		#~ $gtype2 = $gtype2 . "-farm";
	#~ }

	#~ my $flag      = 0;
	#~ my @graphlist = &getGraphs2Show( $gtype );

	#~ foreach my $graphlist ( @graphlist )
	#~ {
		#~ if ( $gtype2 eq $graphlist )
		#~ {
			#~ $flag = 1;
		#~ }
	#~ }

	#~ # &zenlog("graphlist: @graphlist");
	#~ # &zenlog("parameters:$gtype $gtype2 $frequency");

	#~ if ( $gtype2 =~ /^$/ )
	#~ {
		#~ if ( $gtype eq "System" )
		#~ {
			#~ &zenlog(
				#~ "ZAPI error, trying to get graphs, invalid second parameter, the possible values are cpu load mem memsw and your disks"
			#~ );

			#~ my $errormsg =
			  #~ "Invalid second parameter value; the possible values are cpu load mem memsw or any of your disks";
			#~ my $body = {
						 #~ description => "Get graphs",
						 #~ error       => "true",
						 #~ message     => $errormsg
			#~ };

			#~ &httpResponse({ code => 400, body => $body });
		#~ }
		#~ elsif ( $gtype eq "Network" )
		#~ {
			#~ &zenlog(
				#~ "ZAPI error, trying to get graphs, invalid second parameter, the possible values are any available interface"
			#~ );

			#~ my $errormsg =
			  #~ "Invalid second parameter value; the possible values are any available interface";
			#~ my $body = {
						 #~ description => "Get graphs",
						 #~ error       => "true",
						 #~ message     => $errormsg
			#~ };

			#~ &httpResponse({ code => 400, body => $body });
		#~ }
		#~ elsif ( $gtype eq "Farm" )
		#~ {
			#~ &zenlog(
				#~ "ZAPI error, trying to get graphs, invalid second parameter, the possible values are any created farm"
			#~ );

			#~ my $errormsg =
			  #~ "Invalid second parameter value; the possible values are any created farm";
			#~ my $body = {
						 #~ description => "Get graphs",
						 #~ error       => "true",
						 #~ message     => $errormsg
			#~ };

			#~ &httpResponse({ code => 400, body => $body });
		#~ }
	#~ }

	#~ if ( $flag == 0 )
	#~ {
		#~ if ( $gtype eq "System" )
		#~ {
			#~ &zenlog( "ZAPI error, trying to get graphs, invalid second parameter." );

			#~ my $errormsg =
			  #~ "Invalid second parameter value; the possible values are cpu load mem memsw or any of your disks";
			#~ my $body = {
						 #~ description => "Get graphs",
						 #~ error       => "true",
						 #~ message     => $errormsg
			#~ };

			#~ &httpResponse({ code => 400, body => $body });
		#~ }
		#~ elsif ( $gtype eq "Network" )
		#~ {
			#~ &zenlog(
				#~ "ZAPI error, trying to get graphs, invalid second parameter, the possible values are any available interface"
			#~ );

			#~ my $errormsg =
			  #~ "Invalid second parameter value; the possible values are any available interface";
			#~ my $body = {
						 #~ description => "Get graphs",
						 #~ error       => "true",
						 #~ message     => $errormsg
			#~ };

			#~ &httpResponse({ code => 400, body => $body });
		#~ }
		#~ elsif ( $gtype eq "Farm" )
		#~ {
			#~ &zenlog(
				#~ "ZAPI error, trying to get graphs, invalid second parameter, the possible values are any created farm"
			#~ );

			#~ my $errormsg =
			  #~ "Invalid second parameter value; the possible values are any created farm";
			#~ my $body = {
						 #~ description => "Get graphs",
						 #~ error       => "true",
						 #~ message     => $errormsg
			#~ };

			#~ &httpResponse({ code => 400, body => $body });
		#~ }
	#~ }

	#~ # Third parameter
	#~ if ( $frequency =~ /^$/ )
	#~ {
		#~ &zenlog(
			#~ "ZAPI error, trying to get graphs, invalid third parameter, the possible values are daily, weekly, monthly and yearly."
		#~ );

		#~ my $errormsg =
		  #~ "Invalid third parameter value; the possible values are daily, weekly, monthly and yearly";
		#~ my $body = {
					 #~ description => "Get graphs",
					 #~ error       => "true",
					 #~ message     => $errormsg
		#~ };

		#~ &httpResponse({ code => 400, body => $body });
	#~ }

	#~ if ( $frequency =~ /^daily|weekly|monthly|yearly$/ )
	#~ {
		#~ if ( $frequency eq "daily" )   { $frequency = "d"; }
		#~ if ( $frequency eq "weekly" )  { $frequency = "w"; }
		#~ if ( $frequency eq "monthly" ) { $frequency = "m"; }
		#~ if ( $frequency eq "yearly" )  { $frequency = "y"; }
	#~ }
	#~ else
	#~ {
		#~ &zenlog(
			#~ "ZAPI error, trying to get graphs, invalid third parameter, the possible values are daily, weekly, monthly and yearly."
		#~ );

		#~ my $errormsg =
		  #~ "Invalid third parameter value; the possible values are daily, weekly, monthly and yearly";
		#~ my $body = {
					 #~ description => "Get graphs",
					 #~ error       => "true",
					 #~ message     => $errormsg
		#~ };

		#~ &httpResponse({ code => 400, body => $body });
	#~ }

	#~ # Print Graph Function
	#~ my $graph = &printGraph( $gtype2, $frequency );

	#~ # Print Success
	#~ &zenlog( "ZAPI success, trying to get graphs." );

	#~ my $body = {
				 #~ description => "Graphs",
				 #~ graph       => $graph,
	#~ };

	#~ &httpResponse({ code => 200, body => $body });
#~ }

#**
#  @api {get} /graphs Get all possible graphs
#  @apiGroup System Stats
#  @apiDescription Get all possible graphs
#  @apiName GetPossibleFarms
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "These are the possible graphs, you`ll be able to access to the daily, weekly, monthly or yearly graph",
#   "farm" : [
#      {
#         "farms" : [
#            {
#               "farmname" : "FarmL4"
#            },
#            {
#               "farmname" : "FarmGSLB"
#            },
#            {
#               "farmname" : "FarmHTTP"
#            }
#         ]
#      }
#   ],
#   "network" : [
#      {
#         "interfaces" : [
#            {
#               "iface" : "eth1"
#            },
#            {
#               "iface" : "eth1.1"
#            },
#            {
#               "iface" : "eth0"
#            }
#         ]
#      }
#   ],
#   "system" : [
#      {
#         "cpu_usage" : "cpu",
#        "disks" : [
#            {
#               "disk" : "dev-xvda1"
#            },
#            {
#               "disk" : "dev-dm-0"
#            },
#            {
#               "disk" : "dev-mapper-zva64-config"
#            },
#            {
#               "disk" : "dev-mapper-zva64-log"
#            }
#         ],
#         "load_average" : "load",
#         "ram_memory" : "ram",
#         "swap_memory" : "memsw"
#      }
#   ]
#}
#
#@apiExample {curl} Example Usage:
#       curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/graphs
#
#@apiSampleRequest off
#**

#GET disk
sub possible_graphs	#()
{
	my @farms = grep ( s/-farm//, &getGraphs2Show( "Farm" ) );
	my @net = grep ( s/iface//, &getGraphs2Show( "Network" ) );
	my @sys = ( "cpu", "load", "ram", "swap" );
	
	# Get mount point of disks
	my @mount_points;
	my $partitions = &getDiskPartitionsInfo();
	for my $key ( keys %{ $partitions } )
	{
		# mount point : root/mount_point
		push( @mount_points, "root$partitions->{ $key }->{ mount_point }" );
	}
	@mount_points = sort @mount_points;
	push @sys, { disks => \@mount_points };

	# Success
	my $body = {
		description =>
		  "These are the possible graphs, you`ll be able to access to the daily, weekly, monthly or yearly graph",
		system  => \@sys,
		interfaces => \@net,
		farms    => \@farms
	};

	&httpResponse({ code => 200, body => $body });
}


# GET all system graphs
sub get_all_sys_graphs	 #()
{
	# System values
	my @graphlist = &getGraphs2Show( "System" );
	
	my @sys = ( "cpu", "load", "ram", "swap" );
	
	# Get mount point of disks
	my @mount_points;
	my $partitions = &getDiskPartitionsInfo();
	for my $key ( keys %{ $partitions } )
	{
		# mount point : root/mount_point
		push( @mount_points, "root$partitions->{ $key }->{ mount_point }" );
	}
	@mount_points = sort @mount_points;
	push @sys, { disk => \@mount_points };

	my $body = {
		description =>
		  "These are the possible system graphs, you`ll be able to access to the daily, weekly, monthly or yearly graph", 
		  system    => \@sys
	};
	&httpResponse({ code => 200, body => $body });
}


# GET system graphs
sub get_sys_graphs	#()
{
	my $key = shift;
	my $description = "Get $key graphs";
	
	$key = 'mem' if ( $key eq 'ram' );
	$key = 'memsw' if ( $key eq 'swap' );
	
	# Print Success
	&zenlog( "ZAPI success, trying to get graphs." );
	
	# Print Graph Function
	my @output;
	my $graph = &printGraph( $key, 'd' );
	push @output, { frequency => 'daily', graph => $graph };
	$graph = &printGraph( $key, 'w' );
	push @output, { frequency => 'weekly', graph => $graph };
	$graph = &printGraph( $key, 'm' );
	push @output, { frequency => 'monthly', graph => $graph };
	$graph = &printGraph( $key, 'y' );
	push @output, { frequency => 'yearly', graph => $graph };

	my $body = { description => $description, graphs => \@output };
	&httpResponse({ code => 200, body => $body });
}

# GET frequency system graphs
sub get_frec_sys_graphs	#()
{	
	my $key = shift;
	my $frequency = shift;
	my $description = "Get $frequency $key graphs";
	
	$key = 'mem' if ( $key eq 'ram' );
	$key = 'memsw' if ( $key eq 'swap' );
	
	 # take initial idenfiticative letter 
	$frequency = $1  if ( $frequency =~ /^(\w)/ );
	
	# Print Success
	&zenlog( "ZAPI success, trying to get graphs." );
	
	# Print Graph Function
	my @output;
	my $graph = &printGraph( $key, $frequency );

	my $body = { description => $description, graphs => $graph };
	&httpResponse({ code => 200, body => $body });
}


# GET all interface graphs
sub get_all_iface_graphs	#()
{
	my @iface = grep ( s/iface//, &getGraphs2Show( "Network" ) );
	my $body = {
		description =>
		  "These are the possible interface graphs, you`ll be able to access to the daily, weekly, monthly or yearly graph",
		  interfaces    => \@iface
	};
	&httpResponse({ code => 200, body => $body });
}

# GET interface graphs
sub get_iface_graphs	#()
{
	my $iface = shift;
	my $description = "Get interface graphs";
	my $errormsg;
	# validate NIC NAME
	my $socket = IO::Socket::INET->new( Proto => 'udp' );
	my @system_interfaces = $socket->if_list;

	if ( ! grep( /^$iface$/, @system_interfaces ) )
	{
		# Error
		my $errormsg = "Nic interface not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}
	# graph for this farm doesn't exist
	elsif ( ! grep ( /${iface}iface/, &getGraphs2Show( "Network" ) ) )
	{
		$errormsg = "There is no rrd files yet.";
	}
	else
	{
		# Print Success
		&zenlog( "ZAPI success, trying to get graphs." );
		
		# Print Graph Function
		my @output;
		my $graph = &printGraph( "${iface}iface", 'd' );
		push @output, { frequency => 'daily', graph => $graph };
		$graph = &printGraph( "${iface}iface", 'w' );
		push @output, { frequency => 'weekly', graph => $graph };
		$graph = &printGraph( "${iface}iface", 'm' );
		push @output, { frequency => 'monthly', graph => $graph };
		$graph = &printGraph( "${iface}iface", 'y' );
		push @output, { frequency => 'yearly', graph => $graph };

		my $body = { description => $description, graphs => \@output };
		&httpResponse({ code => 200, body => $body });
	}
	
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}


# GET frequency interface graphs
sub get_frec_iface_graphs	#()
{
	my $iface = shift;
	my $frequency = shift;
	my $description = "Get interface graphs";
	my $errormsg;
	# validate NIC NAME
	my $socket = IO::Socket::INET->new( Proto => 'udp' );
	my @system_interfaces = $socket->if_list;

	if ( ! grep( /^$iface$/, @system_interfaces ) )
	{
		# Error
		my $errormsg = "Nic interface not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}
	elsif ( ! grep ( /${iface}iface/, &getGraphs2Show( "Network" ) ) )
	{
		$errormsg = "There is no rrd files yet.";
	}
	else
	{
		if ( $frequency =~ /^daily|weekly|monthly|yearly$/ )
		{
			if ( $frequency eq "daily" )   { $frequency = "d"; }
			if ( $frequency eq "weekly" )  { $frequency = "w"; }
			if ( $frequency eq "monthly" ) { $frequency = "m"; }
			if ( $frequency eq "yearly" )  { $frequency = "y"; }
		}
		# Print Success
		&zenlog( "ZAPI success, trying to get graphs." );
		
		# Print Graph Function
		my $graph = &printGraph( "${iface}iface", $frequency );				
		my $body = { description => $description, graph => $graph };
		&httpResponse({ code => 200, body => $body });
	}
	
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}


# GET all farm graphs
sub get_all_farm_graphs	#()
{
	my @farms = grep ( s/-farm//, &getGraphs2Show( "Farm" ) );
	my $body = {
		description =>
		  "These are the possible farm graphs, you`ll be able to access to the daily, weekly, monthly or yearly graph", 
		  farms    => \@farms
	};
	&httpResponse({ code => 200, body => $body });
}

# GET farm graphs
sub get_farm_graphs	#()
{
	my $farmName = shift;
	my $description = "Get farm graphs";
	my $errormsg;

	# this farm doesn't exist
	if ( &getFarmFile( $farmName ) == -1 )
	{
		$errormsg = "$farmName doesn't exist.";
		my $body = { description => $description, error => "true", message => $errormsg, };
		&httpResponse( { code => 404, body => $body } );
	}	
	# graph for this farm doesn't exist
	elsif ( ! grep ( /$farmName-farm/, &getGraphs2Show( "Farm" ) ) )
	{
		$errormsg = "There is no rrd files yet.";
	}
	else
	{
		# Print Success
		&zenlog( "ZAPI success, trying to get graphs." );
		
		# Print Graph Function
		my @output;
		my $graph = &printGraph( "$farmName-farm", 'd' );
		push @output, { frequency => 'daily', graph => $graph };
		$graph = &printGraph( "$farmName-farm", 'w' );
		push @output, { frequency => 'weekly', graph => $graph };
		$graph = &printGraph( "$farmName-farm", 'm' );
		push @output, { frequency => 'monthly', graph => $graph };
		$graph = &printGraph( "$farmName-farm", 'y' );
		push @output, { frequency => 'yearly', graph => $graph };

		my $body = { description => $description, graphs => \@output };
		&httpResponse({ code => 200, body => $body });
	}
	
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

# GET frequency farm graphs
sub get_frec_farm_graphs	#()
{
	my $farmName = shift;
	my $frequency = shift;
	my $description = "Get farm graphs";
	my $errormsg;

	# this farm doesn't exist
	if ( &getFarmFile( $farmName ) == -1 )
	{
		$errormsg = "$farmName doesn't exist.";
		my $body = { description => $description, error => "true", message => $errormsg, };
		&httpResponse( { code => 404, body => $body } );
	}	
	# graph for this farm doesn't exist
	elsif ( ! grep ( /$farmName-farm/, &getGraphs2Show( "Farm" ) ) )
	{
		$errormsg = "There is no rrd files yet.";
	}
	else
	{
		if ( $frequency =~ /^daily|weekly|monthly|yearly$/ )
		{
			if ( $frequency eq "daily" )   { $frequency = "d"; }
			if ( $frequency eq "weekly" )  { $frequency = "w"; }
			if ( $frequency eq "monthly" ) { $frequency = "m"; }
			if ( $frequency eq "yearly" )  { $frequency = "y"; }
		}
		# Print Success
		&zenlog( "ZAPI success, trying to get graphs." );
		
		# Print Graph Function
		my $graph = &printGraph( "$farmName-farm", $frequency );				
		my $body = { description => $description, graph => $graph };
		&httpResponse({ code => 200, body => $body });
	}
	
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

#GET mount points list
sub list_disks	#()
{
	my @mount_points;
	my $partitions = &getDiskPartitionsInfo();

	for my $key ( keys %{ $partitions } )
	{
		# mount point : root/mount_point
		push( @mount_points, "root$partitions->{ $key }->{ mount_point }" );
	}

	@mount_points = sort @mount_points;

	my $body = {
		description => "List disk partitions",
		params => \@mount_points,
	};

	&httpResponse({ code => 200, body => $body });
}

#GET disk graphs for all periods
sub graphs_disk_mount_point_all	#()
{
	my $mount_point = shift;

	$mount_point =~ s/^root[\/]?/\//;

	my $description = "Disk partition usage graphs";
	my $parts = &getDiskPartitionsInfo();

	my ( $part_key ) = grep { $parts->{ $_ }->{ mount_point } eq $mount_point } keys %{ $parts };

	unless ( $part_key )
	{
		# Error
		my $errormsg = "Mount point not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $dev_id = $parts->{ $part_key }->{ rrd_id };

	# Success
	my @graphs = (
				   { frequency => 'daily',   graph => &printGraph( $dev_id, 'd' ) },
				   { frequency => 'weekly',  graph => &printGraph( $dev_id, 'w' ) },
				   { frequency => 'monthly', graph => &printGraph( $dev_id, 'm' ) },
				   { frequency => 'yearly',  graph => &printGraph( $dev_id, 'y' ) },
	);

	my $body = {
				 description => $description,
				 graphs      => \@graphs,
	};

	&httpResponse({ code => 200, body => $body });
}

#GET disk graph for a single period
sub graph_disk_mount_point_freq	#()
{
	my $mount_point = shift;
	my $frequency = shift;

	$mount_point =~ s/^root[\/]?/\//;

	my $description = "Disk partition usage graph";
	my $parts = &getDiskPartitionsInfo();

	my ( $part_key ) = grep { $parts->{ $_ }->{ mount_point } eq $mount_point } keys %{ $parts };

	unless ( $part_key )
	{
		# Error
		my $errormsg = "Mount point not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $dev_id = $parts->{ $part_key }->{ rrd_id };
	my $freq = $graph_period->{ $frequency };

	# Success
	my $body = {
				 description => $description,
				 frequency      => $frequency,
				 graph      => &printGraph( $dev_id, $freq ),
	};

	&httpResponse({ code => 200, body => $body });
}


stats:
########### GET FARM STATS
# curl --tlsv1 -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: l2ECjvrqitQZULPXbmwMV6luyooQ47SGJhn3LeX1KV6KNKa5uZfJqVVBnEJF4N2Cy" https://46.101.60.162:444/zapi/v3/zapi.cgi/farms/httptest1/stats
#
#
#####Documentation of GET L4XNAT####
#**
#  @api {get} /farms/<farmname>/stats Request info of backend stats in l4xnat Farm
#  @apiGroup System Stats
#  @apiName GetFarmStatsBackendsl4
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Get the backend stats of a given Farm <farmname> with L4XNAT profile
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "List farm stats",
#   "realserversstatus" : [
#      {
#         "Address" : "46.101.39.123",
#         "EstablishedConns" : 290,
#         "PendingConns" : 6,
#         "Port" : "80",
#         "Server" : 0,
#         "Status" : "up"
#      }
#   ]
#}
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k --header 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server:444/zapi/v3/zapi.cgi/farms/farml4/stats
#
# @apiSampleRequest off
#
#**

#####Documentation of GET HTTP####
#**
#  @api {get} /farms/<farmname>/stats Request info of backend stats in http|https Farm
#  @apiGroup System Stats
#  @apiName GetFarmStatsBackendshttp
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Get the backend stats of a given Farm <farmname> with HTTP or HTTPS profile
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "clientsessionstatus" : [],
#   "description" : "List farm stats",
#   "realserversstatus" : [
#      {
#         "Address" : "46.101.39.123",
#         "EstablishedConns" : 39,
#         "PendingConns" : 0,
#         "Port" : "80",
#         "Server" : "0",
#         "Service" : "service1",
#         "Status" : "up"
#      }
#   ]
#}
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k --header 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server:444/zapi/v3/zapi.cgi/stats/farms/FARM
#
# @apiSampleRequest off
#
#**
#Get Farm Stats
sub farm_stats # ( $farmname )
{
	my $farmname = shift;

	my $errormsg;
	my $description = "Get farm stats";

	if ( &getFarmFile( $farmname ) == -1 )
	{
		$errormsg = "The farmname $farmname does not exist.";
		my $body = { description => $description, error  => "true", message => $errormsg };
		&httpResponse( { code => 404, body => $body } );		
	}

	my $type = &getFarmType( $farmname );

	if ( $type eq "http" || $type eq "https" )
	{
		my @out_rss;
		my @out_css;

		# Real Server Table, from content1-25.cgi
		my @netstat;
		my $fvip = &getFarmVip( "vip", $farmname );
		my $fpid = &getFarmChildPid( $farmname );

		my @content = &getFarmBackendStatusCtl( $farmname );
		my @backends = &getFarmBackendsStatus( $farmname, @content );

		# List of services
		my @a_service;
		my $sv;

		foreach ( @content )
		{
			if ( $_ =~ /Service/ )
			{
				my @l = split ( "\ ", $_ );
				$sv = $l[2];
				$sv =~ s/"//g;
				chomp ( $sv );
				push ( @a_service, $sv );
			}
		}

		# List of backends
		my $backendsize    = @backends;
		my $activebackends = 0;
		my $activesessions = 0;

		foreach ( @backends )
		{
			my @backends_data = split ( "\t", $_ );
			if ( $backends_data[3] eq "up" )
			{
				$activebackends++;
			}
		}

		my $i = -1;

		foreach ( @backends )
		{
			my @backends_data = split ( "\t", $_ );
			$activesessions = $activesessions + $backends_data[6];
			if ( $backends_data[0] == 0 )
			{
				$i++;
			}
			my $ip_backend   = $backends_data[1];
			my $port_backend = $backends_data[2];

			@netstat = &getConntrack( "$fvip", $ip_backend, "", "", "tcp" );
			my @synnetstatback =
			&getBackendSYNConns( $farmname, $ip_backend, $port_backend, @netstat );
			my $npend = @synnetstatback;
			my @stabnetstatback =
			&getBackendEstConns( $farmname, $ip_backend, $port_backend, @netstat );
			my $nestab = @stabnetstatback;

			if ( $backends_data[3] == -1 )
			{
				$backends_data[3] = "down";
			}

			push @out_rss,
			  {
				service     => $a_service[$i],
				id          => $backends_data[0]+0,
				ip          => $backends_data[1],
				port        => $backends_data[2]+0,
				status      => $backends_data[3],
				pending     => $npend,
				established => $nestab
			  };
		}

		# Client Session Table
		my @sessions = &getFarmBackendsClientsList( $farmname, @content );
		my $t_sessions = $#sessions + 1;

		foreach ( @sessions )
		{
			my @sessions_data = split ( "\t", $_ );

			push @out_css,
			  {
				service => $sessions_data[0],
				client  => $sessions_data[1],
				session => $sessions_data[2],
				id      => $sessions_data[3]
			  };
		}

		# Print Success
		my $body = {
					description         => "List farm stats",
					backends => \@out_rss,
					sessions => \@out_css,
		};

		&httpResponse({ code => 200, body => $body });
	}

	if ( $type eq "l4xnat" )
	{
		# Parameters
		my @out_rss;

		my @args;
		my $nattype = &getFarmNatType( $farmname );
		my $proto   = &getFarmProto( $farmname );
		if ( $proto eq "all" )
		{
			$proto = "";
		}

		# my @netstat = &getNetstatNat($args);
		my $fvip     = &getFarmVip( "vip", $farmname );
		my @content  = &getFarmBackendStatusCtl( $farmname );
		my @backends = &getFarmBackendsStatus( $farmname, @content );

		# List of backends
		my $backendsize    = @backends;
		my $activebackends = 0;

		foreach ( @backends )
		{
			my @backends_data = split ( ";", $_ );
			if ( $backends_data[4] eq "up" )
			{
				$activebackends++;
			}
		}

		my $index = 0;

		foreach ( @backends )
		{
			my @backends_data = split ( ";", $_ );
			chomp @backends_data;
			#~ $activesessions = $activesessions + $backends_data[6];   # replace by next line
			my $activesessions = $backends_data[6];
			my $ip_backend   = $backends_data[0];
			my $port_backend = $backends_data[1];

			# Pending Conns
			my @synnetstatback;
			my @netstat = &getConntrack( "", $fvip, $ip_backend, "", "" );
			@synnetstatback =
			&getBackendSYNConns( $farmname, $ip_backend, $port_backend, @netstat );
			my $npend = @synnetstatback;


			if ( $backends_data[4] == -1 )
			{
				$backends_data[4] = "down";
			}

			push @out_rss,
			  {
				id          => $index,
				ip          => $ip_backend,
				port        => $port_backend,
				status      => $backends_data[4],
				pending     => $npend,
				established => $backends_data[7]
			  };

			$index = $index + 1;
		}

		# Print Success
		my $body = {
					description       => "List farm stats",
					backends => \@out_rss,
		};

		&httpResponse({ code => 200, body => $body });
	}

	if ( $type eq "gslb" )
	{
		my $out_rss;
		my $gslb_stats = &getGSLBGdnsdStats( $farmname );
		my @backendStats;
		my @services = &getGSLBFarmServices( $farmname );

		foreach my $srv ( @services )
		{
			# Default port health check
			my $port       = &getFarmVS( $farmname, $srv, "dpc" );
			my $lb         = &getFarmVS( $farmname, $srv, "algorithm" );
			my $backendsvs = &getFarmVS( $farmname, $srv, "backends" );
			my @be = split ( "\n", $backendsvs );
			my $out_b = [];

			#
			# Backends
			#

			foreach my $subline ( @be )
			{
				$subline =~ s/^\s+//;

				if ($subline =~ /^$/)
				{
					next;
				}

				# ID and IP
				my @subbe = split(" => ",$subline);
				my $id = $subbe[0];
				my $addr = $subbe[1];
				my $status;

				# look for backend status in stats
				foreach my $st_srv ( @{ $gslb_stats->{ 'services' } } )
				{
					if ( $st_srv->{ 'service' } =~ /^$addr\/[\w]+$port$/ )
					{
						$status = $st_srv->{ 'real_state' };
						last;
					}
				}

				$id =~ s/^primary$/1/;
				$id =~ s/^secondary$/2/;
				$status = lc $status if defined $status;

				push @backendStats,
				  {
					id      => $id + 0,
					ip      => $addr,
					service => $srv,
					port    => $port + 0,
					status  => $status
				  };
			}
		}

		# Print Success
		my $body = {
					 description => "List farm stats",
					 backends    => \@backendStats,
					 client      => $gslb_stats->{ 'udp' },
					 server      => $gslb_stats->{ 'tcp' },
					 extended    => $gslb_stats->{ 'stats' },
		};

		&httpResponse({ code => 200, body => $body });
	}
}


#Get Farm Stats
sub all_farms_stats # ()
{
	my $farms = &getAllFarmStats();

	# Print Success
	my $body = {
				 description       => "List all farms stats",
				 farms => $farms,
	};

	&httpResponse({ code => 200, body => $body });
}


# GET /stats/farms/modules
#Get a farm status resume 
sub module_stats_status
{
	my @farms = @{ &getAllFarmStats () };
	my $lslb = { 'total' => 0, 'up' => 0, 'down' => 0, };
	my $gslb = { 'total' => 0, 'up' => 0, 'down' => 0, };
	my $dslb = { 'total' => 0, 'up' => 0, 'down' => 0, };

	foreach my $farm ( @farms )
	{
		if ( $farm->{ 'profile' } =~ /(?:http|https|l4xnat)/ )
		{
			$lslb->{ 'total' } ++;
			$lslb->{ 'down' } ++ 	if ( $farm->{ 'status' } eq 'down' );
			$lslb->{ 'up' } ++ 		if ( $farm->{ 'status' } eq 'up' || $farm->{ 'status' } eq 'needed restart' );
		}
		elsif ( $farm->{ 'profile' } =~ /gslb/ )
		{
			$gslb->{ 'total' } ++;
			$gslb->{ 'down' } ++ 	if ( $farm->{ 'status' } eq 'down' );
			$gslb->{ 'up' } ++ 		if ( $farm->{ 'status' } eq 'up' || $farm->{ 'status' } eq 'needed restart' );
		}
		elsif ( $farm->{ 'profile' } =~ /datalink/ )
		{
			$dslb->{ 'total' } ++;
			$dslb->{ 'down' } ++ 	if ( $farm->{ 'status' } eq 'down' );
			$dslb->{ 'up' } ++ 		if ( $farm->{ 'status' } eq 'up' || $farm->{ 'status' } eq 'needed restart' );
		}
	}
	
	# Print Success
	my $body = {
				 description => "Module status", 	
				 params 		=> {
					 "lslb" => $lslb,
					 "gslb" => $gslb,
					 "dslb" => $dslb,
					 },
	};
	&httpResponse({ code => 200, body => $body });
}


#Get lslb|gslb|dslb Farm Stats
sub module_stats # ()
{
	my $module = shift;
	my @farms = @{ &getAllFarmStats () };
	my @farmModule;

	foreach my $farm ( @farms )
	{
		push @farmModule, $farm	if ( $farm->{ 'profile' } =~ /(?:http|https|l4xnat)/ && $module eq 'lslb' );
		push @farmModule, $farm	if ( $farm->{ 'profile' } =~ /gslb/ && $module eq 'gslb' );
		push @farmModule, $farm	if ( $farm->{ 'profile' } =~ /datalink/ && $module eq 'dslb' );
	}
	
	# Print Success
	my $body = {
				 description       => "List lslb farms stats", farms => \@farmModule,
	};
	&httpResponse({ code => 200, body => $body });
}


#**
#  @api {get} /stats Request system statistics
#  @apiGroup System Stats
#  @apiDescription Get the system's stats
#  @apiName GetStats
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "System stats",
#   "params" : [
#      {
#         "hostname" : "zvclouddev01"
#      },
#      {
#         "date" : "Wed Mar 18 16:17:09 2015"
#      },
#      {
#         "MemTotal" : 497.02
#      },
#      {
#         "MemFree" : 58.7
#      },
#      {
#         "MemUsed" : 438.32
#      },
#      {
#         "Buffers" : 103.57
#      },
#      {
#         "Cached" : 162.53
#      },
#      {
#         "SwapTotal" : 0
#      },
#      {
#         "SwapFree" : 0
#      },
#      {
#         "SwapUsed" : 0
#      },
#      {
#         "Last" : 0.05
#      },
#      {
#         "Last 5" : 0.04
#      },
#      {
#         "Last 15" : 0.05
#      },
#      {
#         "CPUuser" : 2
#      },
#      {
#         "CPUnice" : 0
#      },
#      {
#         "CPUsys" : 3
#      },
#      {
#         "CPUiowait" : 0
#      },
#      {
#         "CPUirq" : 0
#      },
#      {
#         "CPUsoftirq" : 0
#      },
#      {
#         "CPUidle" : 95
#      },
#      {
#         "CPUusage" : 5
#      },
#      {
#         "eth0 in" : 527.57
#      },
#      {
#         "eth0 out" : 592.84
#      }
#   ]
#}

#@apiExample {curl} Example Usage:
#       curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/stats
#
#@apiSampleRequest off
#**

#GET /stats
sub stats # ()
{
	my @data_mem  = &getMemStats();
	my @data_load = &getLoadStats();
	my @data_net  = &getNetworkStats();
	my @data_cpu  = &getCPU();

	my $out = {
		'hostname' => &getHostname(),
		'date'     => &getDate(),
	};

	foreach my $x ( 0 .. @data_mem - 1 )
	{
		my $name  = $data_mem[$x][0];
		my $value = $data_mem[$x][1] + 0;
		$out->{ memory }->{ $name } = $value;
	}

	foreach my $x ( 0 .. @data_load - 1 )
	{
		my $name  = $data_load[$x][0];
		my $value = $data_load[$x][1] + 0;

		$name =~ s/ /_/;
		$name = 'Last_1' if $name eq 'Last';
		$out->{ load }->{ $name } = $value;
	}

	foreach my $x ( 0 .. @data_cpu - 1 )
	{
		my $name  = $data_cpu[$x][0];
		my $value = $data_cpu[$x][1] + 0;

		$name =~ s/CPU//;
		$out->{ cpu }->{ $name } = $value;
	}

	$out->{ cpu }->{ cores } = &getCpuCores();

	foreach my $x ( 0 .. @data_net - 1 )
	{
		my $name;
		if ( $x % 2 == 0 )
		{
			$name = $data_net[$x][0] . ' in';
		}
		else
		{
			$name = $data_net[$x][0] . ' out';
		}
		my $value = $data_net[$x][1] + 0;
		$out->{ network }->{ $name } = $value;
	}

	# Success
	my $body = {
				 description => "System stats",
				 params      => $out
	};

	&httpResponse({ code => 200, body => $body });
}

#**
#  @api {get} /stats/mem Request system statistics memory
#  @apiGroup System Stats
#  @apiDescription Get the memory system's stats
#  @apiName GetStatsMem
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "System stats",
#   "params" : [
#      {
#         "hostname" : "zva64ee4000"
#      },
#      {
# 		  "date" : "Wed Dec 30 06:03:45 2015"
# 	   },
# 	   {
#		  "MemTotal" : 489.03
# 	   },
# 	   {
# 		  "MemFree" : 67.82
# 	   },
# 	   {
# 		  "MemUsed" : 421.21
# 	   },
# 	   {
# 		  "Buffers" : 110.02
# 	   },
# 	   {
# 		  "Cached" : 141.83
# 	   },
# 	   {
# 		  "SwapTotal" : 1504
# 	   },
# 	   {
# 		  "SwapFree" : 1503.62
# 	   },
# 	   {
# 		  "SwapUsed" : 0.38
# 	   }
#   ]
#}

#@apiExample {curl} Example Usage:
#       curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/stats/mem
#
#@apiSampleRequest off
#**

#GET /stats/mem
sub stats_mem # ()
{
	my @data_mem = &getMemStats();

	my $out = {
		'hostname' => &getHostname(),
		'date'     => &getDate(),
	};

	foreach my $x ( 0 .. @data_mem - 1 )
	{
		my $name  = $data_mem[$x][0];
		my $value = $data_mem[$x][1] + 0;
		$out->{ $name } = $value;
	}

	# Success
	my $body = {
				 description => "Memory usage",
				 params      => $out
	};

	&httpResponse({ code => 200, body => $body });
}

#**
#  @api {get} /stats/load Request system statistics load
#  @apiGroup System Stats
#  @apiDescription Get the load system's stats
#  @apiName GetStatsLoad
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "System stats",
#   "params" : [
#      {
#         "hostname" : "zva64ee4000"
#      },
#      {
# 		  "date" : "Wed Dec 30 06:03:45 2015"
# 	   },
#	   {
#         "Last" : 0.05
#      },
#      {
#         "Last 5" : 0.04
#      },
#      {
#         "Last 15" : 0.05
#      }
#   ]
#}

#@apiExample {curl} Example Usage:
#       curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/stats/load
#
#@apiSampleRequest off
#**

#GET /stats/load
sub stats_load # ()
{
	my @data_load = &getLoadStats();

	my $out = {
		'hostname' => &getHostname(),
		'date'     => &getDate(),
	};

	foreach my $x ( 0 .. @data_load - 1 )
	{
		my $name  = $data_load[$x][0];
		$name =~ s/ /_/;
		$name = 'Last_1' if $name eq 'Last';
		my $value = $data_load[$x][1] + 0;
		$out->{ $name } = $value;
	}

	# Success
	my $body = {
				 description => "System load",
				 params      => $out
	};

	&httpResponse({ code => 200, body => $body });
}

#**
#  @api {get} /stats/cpu Request system statistics cpu
#  @apiGroup System Stats
#  @apiDescription Get the cpu system's stats
#  @apiName GetStatsCpu
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "System stats",
#   "params" : [
#      {
#         "hostname" : "zva64ee4000"
#      },
#      {
# 		  "date" : "Wed Dec 30 06:03:45 2015"
# 	   },
#      {
#         "CPUuser" : 2
#      },
#      {
#         "CPUnice" : 0
#      },
#      {
#         "CPUsys" : 3
#      },
#      {
#         "CPUiowait" : 0
#      },
#      {
#         "CPUirq" : 0
#      },
#      {
#         "CPUsoftirq" : 0
#      },
#      {
#         "CPUidle" : 95
#      },
#      {
#         "CPUusage" : 5
#      }
#   ]
#}

#@apiExample {curl} Example Usage:
#       curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/stats/cpu
#
#@apiSampleRequest off
#**

#GET /stats/cpu
sub stats_cpu # ()
{
	my @data_cpu = &getCPU();

	my $out = {
		'hostname' => &getHostname(),
		'date'     => &getDate(),
	};

	foreach my $x ( 0 .. @data_cpu - 1 )
	{
		my $name  = $data_cpu[$x][0];
		my $value = $data_cpu[$x][1] + 0;
		(undef, $name) = split( 'CPU', $name );
		$out->{ $name } = $value;
	}

	$out->{ cores } = &getCpuCores();

	# Success
	my $body = {
				 description => "System CPU usage",
				 params      => $out
	};

	&httpResponse({ code => 200, body => $body });
}


#GET /stats/system/connections
sub stats_conns
{
	# Success
	my $out = &getTotalConnections ();
	my $body = {
				 description => "System connections",
				 params      => { "connections" => $out },
	};

	&httpResponse({ code => 200, body => $body });
}


#GET /stats/network/interfaces
sub stats_network_interfaces
{
	my $description = "Interfaces info";
	my @interfaces = &getNetworkStats( 'hash' );
	
	my @nic = &getInterfaceTypeList( 'nic' );
	my @bond = &getInterfaceTypeList( 'bond' );
	
	my @nicList;
	my @bondList;
	
	my @restIfaces;

	foreach my $iface ( @interfaces )
	{
		my $extrainfo;
		my $type = &getInterfaceType ( $iface->{ interface } );
		# Fill nic interface list
		if ( $type eq 'nic' )
		{
			foreach my $ifaceNic ( @nic )
			{
				if ( $iface->{ interface } eq $ifaceNic->{ name } )
				{
					$extrainfo = $ifaceNic;
					last;
				}
			}
			$iface->{ mac }	= $extrainfo->{ mac };
			$iface->{ ip } 		= $extrainfo->{ addr };
			$iface->{ status } = $extrainfo->{ status };
			$iface->{ vlan } = &getAppendInterfaces ( $iface->{ interface }, 'vlan' );
			$iface->{ virtual } = &getAppendInterfaces ( $iface->{ interface }, 'virtual' );
			
			push @nicList, $iface;
		}
		
		# Fill bond interface list
		elsif ( $type eq 'bond' )
		{
			foreach my $ifaceBond ( @bond )
			{
				if ( $iface->{ interface } eq $ifaceBond->{ name } )
				{
					$extrainfo = $ifaceBond;
					last;
				}
			}
			$iface->{ mac }	= $extrainfo->{ mac };
			$iface->{ ip } 		= $extrainfo->{ addr };
			$iface->{ status } = $extrainfo->{ status };
			$iface->{ vlan } = &getAppendInterfaces ( $iface->{ interface }, 'vlan' );
			$iface->{ virtual } = &getAppendInterfaces ( $iface->{ interface }, 'virtual' );
			
			$iface->{ slaves } = &getBondSlaves ( $iface->{ interface } );
			
			push @bondList, $iface;
		}
		
		else 
		{
			push @restIfaces, $iface;
		}
		
	}

	# Success
	my $body = {
				 description => $description,
				 params      => { nic => \@nicList, bond => \@bondList, }
	};
	&httpResponse({ code => 200, body => $body });
}

#**
#  @api {get} /stats/network Request network system statistics
#  @apiGroup System Stats
#  @apiDescription Get the network system's stats
#  @apiName GetStatsLoad
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "System stats",
#   "params" : [
#      {
#         "hostname" : "zva64ee4000"
#      },
#      {
# 		  "date" : "Wed Dec 30 06:03:45 2015"
# 	   },
#      {
#         "eth0 in in" : 213.18
#      },
#      {
#         "eth0 out out" : 404.32
#      },
#      {
#         "eth1 in in" : 4.8
#      },
#      {
#         "eth1 out out" : 0.18
#      },
#      {
#         "eth1.1 in in" : 0
#      },
#      {
#         "eth1.1 out out" : 0.01
#      }
#   ]
#}

#@apiExample {curl} Example Usage:
#       curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/stats/network
#
#@apiSampleRequest off
#**

#GET /stats/network
sub stats_network # ()
{
	my @interfaces = &getNetworkStats( 'hash' );

	my $output;
	$output->{ 'hostname'} = &getHostname();
	$output->{ 'date' } 		= &getDate();
	$output->{ 'interfaces' } = \@interfaces;

	# Success
	my $body = {
				 description => "Network interefaces usage",
				 params      => $output
	};

	&httpResponse({ code => 200, body => $body });
}

1;
