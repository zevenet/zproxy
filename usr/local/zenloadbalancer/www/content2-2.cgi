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

print "
  <!--- CONTENT AREA -->
  <div class=\"content container_12\">
";

####################################
# CLUSTER INFO
####################################
&getClusterInfo();

###############################
#BREADCRUMB
############################
my $type = &getFarmType( $farmname );

print "<div class=\"grid_6\">";
print "<h1>Monitoring :: <a href=\"index.cgi?id=1-2\">Conns stats</a></h1>";
print "</div>";

####################################
# CLUSTER STATUS
####################################
&getClusterStatus();

##########################################
# LIST ALL FARMS CONFIGURATION AND STATUS
##########################################

if ( $action !~ /editfarm/ && $action !~ /managefarm/ )
{

	#first list all configuration files
	@files = &getFarmList();
	$size  = $#files + 1;
	if ( $size == 0 )
	{
		$action   = "addfarm";
		$farmname = "";
		require "./content1-21.cgi";
	}

	# If value is true there is at least one Datalink Farm
	my $thereisdl = "false";

	# If value is true there is at least one TCP, HTTP, HTTPS or Lx4NAT Farm
	my $thereisother = "false";

	foreach my $file ( @files )
	{
		$name = &getFarmName( $file );
##########if farm is not the current farm then it doesn't print. only print for global view.
#if ($farmname eq $name || !(defined $farmname) || $farmname eq "" || $action eq "deletefarm" || $action =~ /^Save|^Cancel/ ){
		$type = &getFarmType( $name );
		if ( $type ne "datalink" )
		{

			if ( $thereisother eq "false" )
			{
				print "
                               <div class=\"box grid_12\">
                                 <div class=\"box-head\">
                                       <span class=\"box-icon-24 fugue-24 server\"></span>       
                                       <h2>Conns Statistics</h2>
                                 </div>
                                 <div class=\"box-content no-pad\">
                                         <table class=\"display\" id=\"farms-table\">
                                         <thead>
                                               <tr>
                                                 <th>Name</th>
                                                 <th>Virtual IP</th>
                                                 <th>Virtual Port(s)</th>
                                                 <th>Pending Conns</th>
                                                 <th>Established Conns</th>
                                                 <th>Status</th>
                                                 <th>Profile</th>
                                                 <th>Actions</th>
                                               </tr>
                                         </thead>
                                         <tbody>
                       ";
				$thereisother = "true";
			}

			if ( $farmname eq $name && $action ne "addfarm" && $action ne "Cancel" )
			{
				print "<tr class=\"selected\">";
			}
			else
			{
				print "<tr>";
			}

			#print the farm description name
			print "<td>$name</td>";

			#print the virtual ip
			$vip = &getFarmVip( "vip", $name );
			print "<td>$vip</td>";

			#print the virtual port where the vip is listening
			$vipp = &getFarmVip( "vipp", $name );
			print "<td>$vipp</td>";

			#print global connections bar
			$status = &getFarmStatus( $name );
			if ( $status eq "up" )
			{
				@netstat = &getConntrack( "", $vip, "", "", "" );

				# SYN_RECV connections
				my @synconnslist = &getFarmSYNConns( $name, @netstat );
				$synconns = @synconnslist;
				print "<td> $synconns </td>";
			}
			else
			{
				print "<td>0</td>";
			}
			if ( $status eq "up" )
			{
				@gconns = &getFarmEstConns( $name, @netstat );
				$global_conns = @gconns;
				print "<td>";
				print " $global_conns ";
				print "</td>";
			}
			else
			{
				print "<td>0</td>";
			}

			#print status of a farm
			if ( $status ne "up" )
			{
				print
				  "<td class=\"aligncenter\"><img src=\"img/icons/small/stop.png\" title=\"down\"></td>";
			}
			else
			{
				print
				  "<td class=\"aligncenter\"><img src=\"img/icons/small/start.png\" title=\"up\"></td>";
			}

			#type of farm
			print "<td>$type</td>";

			#menu
			print "<td>";
			if ( $type eq "tcp" || $type eq "udp" || $type eq "l4xnat" || $type =~ /http/ )
			{
				&createmenuvipstats( $name, $id, $status, $type );
			}
			print "</td>";
			print "</tr>";
		}
		else
		{
			$thereisdl = "true";
		}

		#}
	}

	if ( $thereisother eq "true" )
	{
		print "
	</tbody>
	</table>
	</div>
	</div>";
	}

	# DATALINK

	if ( $thereisdl eq "true" )
	{

		print "
    <div class=\"box grid_12\">
      <div class=\"box-head\">
           <span class=\"box-icon-24 fugue-24 server\"></span>   
        <h2>Datalink Farms table</h2>
      </div>
      <div class=\"box-content no-pad\">
         <table class=\"display\" id=\"datalink-farms-table\">
          <thead>
";

		print "<tr>";
		print "<th>Name</th>";
		print "<th>IP</th>";
		print "<th>Interface</th>";
		print "<th>Rx Bytes/sec</th>";
		print "<th>Rx Packets/sec</th>";
		print "<th>Tx Bytes/sec</th>";
		print "<th>Tx Packets/sec</th>";
		print "<th>Status</th>";
		print "<th>Profile</th>";
		print "<th>Actions</th>";
		print "</tr>";
		print "</thead>";
		print "<tbody>";
		use Time::HiRes qw (sleep);

		foreach my $file ( @files )
		{
			$name = &getFarmName( $file );
			$type = &getFarmType( $name );

			if ( $type eq "datalink" )
			{

				$vipp = &getFarmVip( "vipp", $name );
				my @startdata = &getDevData( $vipp );
				sleep ( 0.5 );
				my @enddata = &getDevData( $vipp );

				if ( $farmname eq $name && $action ne "addfarm" && $action ne "Cancel" )
				{
					print "<tr class=\"selected\">";
				}
				else
				{
					print "<tr>";
				}

				#print the farm description name
				print "<td>$name</td>";

				#print the virtual ip
				$vip = &getFarmVip( "vip", $name );
				print "<td>$vip</td>";

				#print the interface to be the defaut gw
				print "<td>$vipp</td>";

				#print global packets
				$status = &getFarmStatus( $name );

				if ( $status eq "up" )
				{
					my $ncalc = ( @enddata[0] - @startdata[0] ) * 2;
					print "<td> $ncalc B/s </td>";
				}
				else
				{
					print "<td>0</td>";
				}

				if ( $status eq "up" )
				{
					my $ncalc = ( @enddata[1] - @startdata[1] ) * 2;
					print "<td> $ncalc Pkt/s </td>";
				}
				else
				{
					print "<td>0</td>";
				}

				if ( $status eq "up" )
				{
					my $ncalc = ( @enddata[2] - @startdata[2] ) * 2;
					print "<td> $ncalc B/s </td>";
				}
				else
				{
					print "<td>0</td>";
				}

				if ( $status eq "up" )
				{
					my $ncalc = ( @enddata[3] - @startdata[3] ) * 2;
					print "<td>$ncalc Pkt/s </td>";
				}
				else
				{
					print "<td>0</td>";
				}

				#print status of a farm

				if ( $status ne "up" )
				{
					print
					  "<td class=\"aligncenter\"><img src=\"img/icons/small/stop.png\" title=\"down\"></td>";
				}
				else
				{
					print
					  "<td class=\"aligncenter\"><img src=\"img/icons/small/start.png\" title=\"up\"></td>";
				}

				#type of farm
				print "<td>$type</td>";

				#menu
				print "<td>";
				&createmenuvipstats( $name, $vipp, $status, $type );

				print "</td>";
				print "</tr>";
			}
		}

## END DATALINK

		print "</tbody>";
	}

	print "</table>";
	if ( $thereisdl eq "true" )
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

# Delete this and you'll be killed!
print "";

