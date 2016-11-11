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

#STATUS of a GSLB farm
use JSON;

&refreshstats();

my $jsonObj = &getGSLBGdnsdStats();

my @services = @{ $jsonObj->{ 'services' } };
my @serviceDescriptors;
my @status;
my $activebackends = 0;
my $backendsize;

foreach my $service ( @services )
{
	push @serviceDescriptors, $service->{ 'service' };
	push @status,             $service->{ 'state' };
	if ( $service->{ 'state' } eq "UP" ) { $activebackends++; }
}

if ( scalar @serviceDescriptors != scalar @status )
{
	&zenlog( "Services number no equal service status " );
}

else
{
	print "
		<div class=\"box grid_12\">
		<div class=\"box-head\">
			<span class=\"box-icon-24 fugue-24 server\"></span>   
			<h2>Real servers status $backendsize servers, $activebackends current</h2>
		</div>
		<div class=\"box-content no-pad\">
			<table id=\"backends-table\" class=\"display\">
			<thead>
				<tr>
				<th>Server</th>                 
				<th>Service</th>
				<th>Address</th>
				<th>Port</th>
				<th>Status</th>
				</tr>
			</thead>
			<tbody>
	";

	my $ident = 0;
	my $i     = -1;
	foreach $descriptor ( @serviceDescriptors )
	{
		$i++;

		#   "service": "127.0.0.1/tcp_60",
		my @backends_data = split ( "/", $descriptor );
		my $host = $backends_data[0];

		# tcp_60
		my @serviceNames = &dnsServiceType( $farmname, $host, $backends_data[1] );

		my $numSameBackends = scalar @serviceNames;

		@backends_data = split ( "_", $backends_data[1] );
		my $port = $backends_data[1];

		foreach $srvName ( @serviceNames )
		{
			print "<tr>";
			print "<td> $ident </td>";
			print "<td> $srvName </td>";
			print "<td> $host </td> ";
			print "<td> $port </td> ";
			if ( $status[$i] eq "DOWN" )
			{
				print
				  "<td class=\"aligncenter\"><img src=\"img/icons/small/stop.png\" title=\"Down\"></td> ";
			}
			else
			{
				print
				  "<td class=\"aligncenter\"><img src=\"img/icons/small/start.png\" title=\"Up\"></td> ";
			}
			print "</tr>";
			$ident++;
		}
	}

	print "</tbody>";
	print "</table>";
	print "</div></div>\n\n";

	# More stats
	print "<div class=\"box-header\">";

	print "<form method=\"post\" action=\"index.cgi\" class=\"myform\">";
	if ( $viewtableclients eq "yes" )
	{
		print
		  "<p class=\"grid_12\"><input type=\"submit\" class=\"button grey\" value=\"Dismiss table\"></p>";
		print "<input type=\"hidden\" name=\"viewtableclients\" value=\"no\">";
	}
	else
	{
		print
		  "<p class=\"grid_12\"><input type=\"submit\" class=\"button grey\" value=\"Show table\"></p>";
		print "<input type=\"hidden\" name=\"viewtableclients\" value=\"yes\">";
	}
	print "<input type=\"hidden\" name=\"id\" value=\"1-2\">";
	print "<input type=\"hidden\" name=\"action\" value=\"managefarm\">";
	print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
	print "</form>";

	if ( $viewtableclients eq "yes" )
	{
		{
			# Client table
			my %clientStats = %{ $jsonObj->{ 'udp' } };

			print "
				<div class=\"box grid_12\">
					<div class=\"box-head\">
						<span class=\"box-icon-24 fugue-24 user-business\"></span>        
						<h2>Client stats</h2>
					</div>
					<div class=\"box-content no-pad\">
							<table  class=\"display\">
							<thead>
								<tr>
									<th>Reqs</th>
									<th>Recive fail</th>
									<th>Send fail</th>
									<th>Truncated Response (TC)</th>
									<th>Extended DNS big</th>
									<th>Extended DNS TC</th>
								</tr>
							</thead>
							<tbody>
		";

			print "<tr>";
			print "<td> $clientStats{'reqs'} 	</td> ";
			print "<td> $clientStats{'recvfail'} 	</td> ";
			print "<td> $clientStats{'sendfail'} 	</td> ";
			print "<td> $clientStats{'tc'} 		</td> ";
			print "<td> $clientStats{'edns_big'} 	</td> ";
			print "<td> $clientStats{'edns_tc'} 	</td> ";
			print "</tr>";

			print "</tbody>";
			print "</table>";
			print "</div>";
			print "</div>\n\n";
		}

		# Server table
		{
			my %serverStats = %{ $jsonObj->{ 'tcp' } };

			print "
				<div class=\"box grid_12\">
					<div class=\"box-head\">
						<span class=\"box-icon-24 fugue-24 user-business\"></span>        
						<h2>Server stats</h2>
					</div>
					<div class=\"box-content no-pad\">
							<table  class=\"display\">
							<thead>
								<tr>
									<th>Reqs</th>
									<th>Recive fail</th>
									<th>Send fail</th>
								</tr>
							</thead>
							<tbody>
		";

			print "<tr>";
			print "<td> $serverStats{'reqs'} 	</td> ";
			print "<td> $serverStats{'recvfail'} 	</td> ";
			print "<td> $serverStats{'sendfail'} 	</td> ";
			print "</tr>";

			print "</tbody>";
			print "</table>";
			print "</div>";
			print "</div>\n\n";
		}

		# Extended stats
		{
			my %extendedStats = %{ $jsonObj->{ 'stats' } };

			print "
				<div class=\"box grid_12\">
					<div class=\"box-head\">
						<span class=\"box-icon-24 fugue-24 user-business\"></span>        
						<h2>Extended stats</h2>
					</div>
					<div class=\"box-content no-pad\">
							<table  class=\"display\">
							<thead>
								<tr>
									<th>No Error</th>
									<th>Refused</th>
									<th>Non-Existent Domain</th>
									<th>NOTIMP</th>
									<th>Bad Version</th>
									<th>Format Error</th>
									<th>Dropped</th>
									<th>v6</th>
									<th>Extended DNS</th>
									<th>Extended DNS-clientsub</th>
								</tr>
							</thead>
							<tbody>
		";

			print "<tr>";
			print "<td> $extendedStats{'noerror'} 	</td> ";
			print "<td> $extendedStats{'refused'} 	</td> ";
			print "<td> $extendedStats{'nxdomain'} 	</td> ";
			print "<td> $extendedStats{'notimp'} 	</td> ";
			print "<td> $extendedStats{'badvers'} 	</td> ";
			print "<td> $extendedStats{'formerr'} 	</td> ";
			print "<td> $extendedStats{'dropped'} 	</td> ";
			print "<td> $extendedStats{'v6'} 	</td> ";
			print "<td> $extendedStats{'edns'} 	</td> ";
			print "<td> $extendedStats{'edns_clientsub'} 	</td> ";
			print "</tr>";

			print "</tbody>";
			print "</table>";
			print "</div>";
			print "</div>\n\n";
		}
	}
}
print "<!--END MANAGE-->";

print "
<script>
\$(document).ready(function() {
    \$('#backends-table').DataTable( {
        \"bJQueryUI\": true,     
        \"sPaginationType\": \"full_numbers\",
        \"aaSorting\": [[1,'asc']]   
    });
} );
</script>";

# do not remove this
1;
