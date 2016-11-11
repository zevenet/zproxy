###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This library is free software; you can redistribute it and/or modify it
#     under the terms of the GNU Lesser General Public License as published
#     by the Free Software Foundation; either version 2.1 of the License, or
#     (at your option) any later version.
#
#     This library is distributed in the hope that it will be useful, but
#     WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
#     General Public License for more details.
#
#     You should have received a copy of the GNU Lesser General Public License
#     along with this library; if not, write to the Free Software Foundation,
#     Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
###############################################################################

use Time::HiRes qw (sleep);

print "
  <!--- CONTENT AREA -->
  <div class=\"content container_12\">
";

###############################
#BREADCRUMB
############################
my $type = &getFarmType( $farmname );
$file = &getFarmFile( $farmname );    # do not 'my' this variable

print "<div class=\"grid_6\">";
if ( $farmname ne "" && $type != 1 )
{
	if ( $action =~ "^editfarm" )
	{
		print
		  "<h1>Manage :: <a href=\"index.cgi?id=1-2\">Farms</a> \:\: <span style=\"cursor: pointer;\" onClick=\"jQuery('#bcform').submit();\">Edit $type farm '$farmname'</span></h1>";

		print
		  "<form method=\"post\" id=\"bcform\" class=\"myform\" action=\"index.cgi\">";
		print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
		print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
		print "<input type=\"hidden\" name=\"action\" value=\"editfarm\">";
		print "</form>";

	}
	else
	{
		print
		  "<h1>Manage :: <a href=\"index.cgi?id=1-2\">Farms</a> \:\: $type farm '$farmname'</h1>";
	}
}
else
{
	if ( $farmname ne "" )
	{
		print "<h1>Manage :: <a href=\"index.cgi?id=1-2\">Farms</a> :: $farmname</h1>";
	}
	else
	{
		print "<h1>Manage :: <a href=\"index.cgi?id=1-2\">Farms</a></h1>";
	}
}
print "</div>";

####################################
# CLUSTER STATUS
####################################
&getClusterStatus();

#evaluate the $action variable, used for manage forms
if ( $action eq "addfarm" || $action eq "Save" || $action eq "Save & continue" )
{
	require "./content1-21.cgi";
}

if ( $action eq "deletefarm" )
{
	my $stat = &runFarmStop( $farmname, "true" );
	if ( $stat == 0 )
	{
		# zcluster: stop and delete farm in remote node
		&runZClusterRemoteManager( 'farm', 'stop', $farmname );
		
		&successmsg( "The Farm $farmname is now disabled" );
	}

	$stat = &runFarmDelete( $farmname );
	if ( $stat == 0 )
	{
		&runZClusterRemoteManager( 'farm', 'delete', $farmname );
		
		&successmsg( "The Farm $farmname is now deleted" );
	}
	else
	{
		&successmsg( "The Farm $farmname hasn't been deleted" );
	}
}

if ( $action eq "startfarm" )
{
	my $stat = &runFarmStart( $farmname, "true" );
	if ( $stat == 0 )
	{
		# zcluster: start farm in remote node
		&runZClusterRemoteManager( 'farm', 'start', $farmname );

		&successmsg( "The Farm $farmname is now running" );
	}
	else
	{
		&errormsg(
			"The Farm $farmname isn't running, check if the IP address is up and the PORT is in use"
		);
	}
}

if ( $action eq "stopfarm" )
{
	my $stat = &runFarmStop( $farmname, "true" );

	if ( $stat == 0 )
	{
		# zcluster: stop farm in remote node
		&runZClusterRemoteManager( 'farm', 'stop', $farmname );

		&successmsg( "The Farm $farmname is now disabled" );
	}
	else
	{
		&errormsg( "The Farm $farmname is not disabled" );
	}
}

if ( $action =~ "^editfarm" )
{
	if ( $type == 1 )
	{
		&errormsg( "Unknown farm type of $farmname" );
	}
	else
	{
		if ( $type eq "tcp" || $type eq "udp" )
		{
			require "./controller_tcp.cgi";
			require "./content1-22.cgi";
		}
		if ( $type eq "http" || $type eq "https" )
		{
			require "./controller_http.cgi";
			require "./content1-24.cgi";
		}
		if ( $type eq "datalink" )
		{
			require "./controller_datalink.cgi";
			require "./content1-26.cgi";
		}
		if ( $type eq "l4xnat" )
		{
			require "./controller_l4xnat.cgi";
			require "./content1-28.cgi";
		}
		if ( $type eq "gslb" )
		{
			require "./controller_gslb.cgi";
			require "./content1-202.cgi";
		}
	}
}

if ( $action eq "managefarm" )
{
	if ( $type == 1 )
	{
		&errormsg( "Unknown farm type of $farmname" );
	}
	else
	{
		if ( $type eq "tcp" || $type eq "udp" )
		{
			require "./content1-23.cgi";
		}
		if ( $type eq "http" || $type eq "https" )
		{
			require "./content1-25.cgi";
		}
		if ( $type eq "datalink" )
		{
			require "./content1-27.cgi";
		}
		if ( $type eq "l4xnat" )
		{
			require "./content1-29.cgi";
		}
		#~ if ( $type eq "gslb" )
		#~ {
			#~ require "./content1-203.cgi";
		#~ }
	}
	require "./content1-203.cgi";
}

##########################################
# LIST ALL FARMS CONFIGURATION AND STATUS
##########################################

if ( $action !~ /editfarm/ && $action !~ /managefarm/ )
{
	#first list all configuration files
	@files = &getFarmList();

	$size = $#files + 1;
	if ( $size == 0 )
	{
		$action   = 'addfarm';
		$farmname = '';
		require './content1-21.cgi';
	}

	# If value is true there is at least one Datalink Farm
	my $thereisdl;

	# If value is true there is at least one TCP, HTTP, HTTPS or Lx4NAT Farm
	my $otherthandl;

  NODL_LOOP:
	foreach my $file ( @files )
	{
		$name = &getFarmName( $file );

		## if farm is not the current farm then it isn't printed. only print for global view.
		$type = &getFarmType( $name );

		if ( $type eq 'datalink' )
		{
			$thereisdl = 'true';
			next NODL_LOOP;
		}

		if ( !$otherthandl )
		{
			print "
				<div class=\"box grid_12\">
				<div class=\"box-head\">
					<span class=\"box-icon-24 fugue-24 server\"></span>       
					<h2>Farms table</h2>
				</div>
				<div class=\"box-content no-pad\">
					<ul class=\"table-toolbar\">
						<li>
							<form method=\"post\" action=\"index.cgi\">
								<button type=\"submit\" class=\"noborder\">
								<img src=\"img/icons/basic/plus.png\" alt=\"Add\"> Add new Farm</button>
								<input type=\"hidden\" name=\"id\" value=\"$id\">
								<input type=\"hidden\" name=\"action\" value=\"addfarm\">
							</form>
						</li>
					</ul>
					<table class=\"display\" id=\"farms-table\">
					<thead>
						<tr>
							<th>Name</th>
							<th>Virtual IP</th>
							<th>Virtual Port(s)</th>
							<th>Status</th>
							<th>Profile</th>
							<th>Actions</th>
						</tr>
					</thead>
					<tbody>
			                       ";
			$otherthandl = 'true';
		}

		( $farmname eq $name && $action ne "addfarm" && $action ne "Cancel" )
		  ? print "<tr class=\"selected\">"
		  : print "<tr>";

		print
		  "<form method=\"post\" id=\"farm_$name\" class=\"myform\" action=\"index.cgi\">";
		print "<input type=\"hidden\" name=\"id\" value=\"1-2\">";
		print "<input type=\"hidden\" name=\"farmname\" value=\"$name\">";
		print "<input type=\"hidden\" name=\"action\" value=\"editfarm\">";
		print "</form>";

		#print global connections bar
		$status = &getFarmStatus( $name );

		my $onClick;
		if ( $type eq "tcp" && $status eq "down" )
		{
			$onClick = "";
		}
		else
		{
			$onClick =
			  "style=\"cursor: pointer;\" onClick=\"jQuery('#farm_$name').submit();\"";
		}

		#print the farm description name
		print "<td $onClick>$name</td>";

		#print the virtual ip
		$vip = &getFarmVip( "vip", $name );
		print "<td $onClick>$vip</td>";

		#print the virtual port where the vip is listening
		$vipp = &getFarmVip( "vipp", $name );
		print "<td $onClick>$vipp</td>";

		#print status of a farm
		print "<td class=\"aligncenter\" $onClick>";
		( $status ne "up" )
		  ? print "<img src=\"img/icons/small/stop.png\" title=\"down\">"
		  : print "<img src=\"img/icons/small/start.png\" title=\"up\">";
		print "</td>";

		#type of farm
		print "<td $onClick>$type</td>";

		#menu
		print "<td>";
		&createMenuVip_ext( $name );
		print "</td>";
		print "</tr>";
	}

	if ( $otherthandl )
	{
		print "
	</tbody>
	</table>
	</div>
	</div>";
	}

	# DATALINK
	if ( $thereisdl )
	{
		print "
		    <div class=\"box grid_12\">
				<div class=\"box-head\">
					<span class=\"box-icon-24 fugue-24 server\"></span>   
					<h2>Datalink Farms table</h2>
				</div>
				<div class=\"box-content no-pad\">
					<ul class=\"table-toolbar\">
						<li>
							<form method=\"post\" action=\"index.cgi\">
							<button type=\"submit\" class=\"noborder\">
							<img src=\"img/icons/basic/plus.png\" alt=\"Add\"> Add new Farm</button>
							<input type=\"hidden\" name=\"id\" value=\"$id\">
							<input type=\"hidden\" name=\"action\" value=\"addfarm\">
							</form>
						</li>
					</ul>
					<table class=\"display\" id=\"datalink-farms-table\">
						<thead>
			";

		print "<tr>";
		print "<th>Name</th>";
		print "<th>IP</th>";
		print "<th>Interface</th>";
		print "<th>Status</th>";
		print "<th>Profile</th>";
		print "<th>Actions</th>";
		print "</tr>";
		print "</thead>";
		print "<tbody>";

	  DL_LOOP:
		foreach my $file ( @files )
		{
			$name = &getFarmName( $file );
			$type = &getFarmType( $name );

			# skip to next farm if this is not datalink
			next DL_LOOP if $type ne "datalink";

			$vipp = &getFarmVip( "vipp", $name );
			my @startdata = &getDevData( $vipp );
			sleep ( 0.5 );
			my @enddata = &getDevData( $vipp );

			(     ( $farmname eq $name )
			   && ( $action ne "addfarm" )
			   && ( $action ne "Cancel" ) )
			  ? print "<tr class=\"selected\">"
			  : print "<tr>";

			print
			  "<form method=\"post\" id=\"farm_$name\" class=\"myform\" action=\"index.cgi\">";
			print "<input type=\"hidden\" name=\"id\" value=\"1-2\">";
			print "<input type=\"hidden\" name=\"farmname\" value=\"$name\">";
			print "<input type=\"hidden\" name=\"action\" value=\"editfarm\">";
			print "</form>";

			#print the farm description name
			print
			  "<td style=\"cursor: pointer;\" onClick=\"jQuery('#farm_$name').submit();\">$name</td>";

			#print the virtual ip
			$vip = &getFarmVip( "vip", $name );
			print
			  "<td style=\"cursor: pointer;\" onClick=\"jQuery('#farm_$name').submit();\">$vip</td>";

			#print the interface to be the defaut gw
			print
			  "<td style=\"cursor: pointer;\" onClick=\"jQuery('#farm_$name').submit();\">$vipp</td>";

			#print global connections bar
			$status = &getFarmStatus( $name );

			#print status of a farm
			print
			  "<td class=\"aligncenter\" style=\"cursor: pointer;\" onClick=\"jQuery('#farm_$name').submit();\">";
			( $status ne "up" )
			  ? print "<img src=\"img/icons/small/stop.png\" title=\"down\">"
			  : print "<img src=\"img/icons/small/start.png\" title=\"up\">";
			print "</td>";

			#type of farm
			print
			  "<td style=\"cursor: pointer;\" onClick=\"jQuery('#farm_$name').submit();\">$type</td>";

			#menu
			print "<td>";
			&createMenuVip_ext( $name );

			print "</td>";
			print "</tr>";

		}
		print "</tbody>";
	}
	## END DATALINK

	print "</table>";
	if ( $thereisdl )
	{
		print "</div>";
		print "</div>";
	}

	print "
		<script>
		\$(document).ready(function() {
		    \$('#datalink-farms-table').DataTable( {
		        \"bJQueryUI\": true,     
		        \"sPaginationType\": \"full_numbers\",
				\"aLengthMenu\": [
					[10, 25, 50, 100, 200, -1],
					[10, 25, 50, 100, 200, \"All\"]
				],
				\"iDisplayLength\": 10
		    });
		       \$('#farms-table').DataTable( {
		        \"bJQueryUI\": true,     
		        \"sPaginationType\": \"full_numbers\",
				\"aLengthMenu\": [
					[10, 25, 50, 100, 200, -1],
					[10, 25, 50, 100, 200, \"All\"]
				],
				\"iDisplayLength\": 10 
		    });
		} );
		</script>";
}

# Must end with a true value.
# DO NOT REMOVE NEXT LINE
1;
