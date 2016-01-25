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

if ( $viewtableclients eq "" ) { $viewtableclients = "no"; }
if ( $viewtableconn eq "" )    { $viewtableconn    = "no"; }

$type = &getFarmType( $farmname );

if ( $viewtableclients eq "" ) { $viewtableclients = "no"; }
if ( $viewtableconn eq "" )    { $viewtableconn    = "no"; }

my @content = &getFarmBackendStatusCtl( $farmname );

#sessions
my @sessions = &getFarmBackendsClientsList( $farmname, @content );

#Real servers
my @backends = &getFarmBackendsStatus( $farmname, @content );

my @netstat;
$fvip  = &getFarmVip( "vip",  $farmname );
$fvipp = &getFarmVip( "vipp", $farmname );
$fpid  = &getFarmPid( $farmname );

my $activebackends     = 0;
my $activeservbackends = 0;
my $totalsessions      = 0;
foreach ( @backends )
{
	my @backends_data = split ( "\t", $_ );
	if ( $backends_data[1] ne "0\.0\.0\.0" )
	{
		$activeservbackends++;
		if ( $backends_data[3] eq "UP" )
		{
			$activebackends++;
		}
	}
}

##
&refreshstats();
print "<br>";
my @back_header = split ( "\t", @backends[0] );

print "
    <div class=\"box grid_12\">
      <div class=\"box-head\">
           <span class=\"box-icon-24 fugue-24 server\"></span>   
        <h2>Real servers status $activeservbackends servers, $activebackends current</h2>
      </div>
      <div class=\"box-content no-pad\">
         <table id=\"backends-table\" class=\"display\">
          <thead>
            <tr>
              <th>Server</th>
              <th>Address</th>
              <th>Port</th>
                         <th>Status</th>
                         <th>Pending Conns</th>
                         <th>Established Conns</th>
                         <th>Clients</th>
            </tr>
          </thead>
          <tbody>
";

foreach ( @backends )
{
	my @backends_data = split ( "\t", $_ );
	if ( @backends_data[1] ne "0\.0\.0\.0" && @backends_data[0] =~ /^[0-9]/ )
	{
		print "<tr>";
		print "<td>@backends_data[0]</td>";
		print "<td>@backends_data[1]</td>";
		print "<td>@backends_data[2]</td>";
		if ( $backends_data[3] eq "MAINTENANCE" )
		{
			print
			  "<td class=\"aligncenter\"><img src=\"img/icons/small/warning.png\" title=\"maintenance\"></td> ";
		}
		elsif ( $backends_data[3] eq "UP" )
		{
			print
			  "<td class=\"aligncenter\"><img src=\"img/icons/small/start.png\" title=\"up\"></td> ";
		}
		else
		{
			print
			  "<td class=\"aligncenter\"><img src=\"img/icons/small/stop.png\" title=\"down\"></td> ";
		}
		$ip_backend   = $backends_data[1];
		$port_backend = $backends_data[2];
		@netstat      = &getConntrack( $fvip, $ip_backend, "", "", $type );
		@synnetstatback =
		  &getBackendSYNConns( $farmname, $ip_backend, $port_backend, @netstat );
		$npend = @synnetstatback;
		print "<td>$npend</td>";
		@stabnetstatback =
		  &getBackendEstConns( $farmname, $ip_backend, $port_backend, @netstat );
		$nestab = @stabnetstatback;
		print "<td>$nestab</td>";
		print "<td>@backends_data[6] </td>";
		$totalsessions = $totalsessions + @backends_data[6];
		print "</tr>\n";
	}
}

print "</tbody>";
print "</table>";
print "</div></div>\n\n";

#Client sessions status
my @ses_header = split ( "\t", @sessions[0] );
my @fclient = &getFarmMaxClientTime( $farmname );

if ( @fclient == -1 )
{
	$ftracking = 10;
}
else
{
	$ftracking = @fclient[1];
}

print "<form method=\"post\" action=\"index.cgi\" class=\"myform\">";
print "<input type=\"hidden\" name=\"id\" value=\"1-2\">";
print "<input type=\"hidden\" name=\"action\" value=\"managefarm\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<input type=\"hidden\" name=\"viewtableconn\" value=\"$viewtableconn\">";
if ( $viewtableclients eq "yes" )
{
	print "<input type=\"hidden\" name=\"viewtableclients\" value=\"no\">";
	print
	  "<p class=\"grid_12\"><input type=\"submit\" class=\"button grey\" value=\"Dismiss sessions status table\"></p>";

}
else
{
	print "<input type=\"hidden\" name=\"viewtableclients\" value=\"yes\">";
	print
	  "<p class=\"grid_12\"><input type=\"submit\" class=\"button grey\" value=\"Show sessions status table\"></p>";
}
print "</form>";

if ( $viewtableclients eq "yes" )
{

	print "
               <div class=\"box grid_12\">
                 <div class=\"box-head\">
                       <span class=\"box-icon-24 fugue-24 user-business\"></span>        
                       <h2>Client sessions status $totalsessions active clients</h2>
                 </div>
                 <div class=\"box-content no-pad\">
                         <table id=\"clients-table\" class=\"display\">
                         <thead>
                               <tr>
				 <th>Client</th>
                                 <th>Address</th>
                                 <th>Age(sec)</th>
                                 <th>Last Server</th>
                                 <th>Connects</th>
                                 <th>Sent(mb)</th>
                                 <th>Received(mb)</th>
                               </tr>
                         </thead>
                         <tbody>
       ";

	foreach ( @sessions )
	{
		my @s_backend = split ( "\t", $_ );
		if ( @s_backend[0] =~ /^[0-9]/
			 && ( $ftracking == 0 || @s_backend[2] <= $ftracking ) )
		{
			print
			  "<tr><td>@s_backend[0]  </td><td>@s_backend[1]  </td><td>@s_backend[2] </td><td>@s_backend[3] </td><td>@s_backend[4] </td><td>@s_backend[5] </td><td>@s_backend[6] </td></tr>";
		}
	}
	print "</tbody>";
	print "</table>";
	print "</div></div>\n\n";
}

###Active clients
my @activeclients = &getFarmBackendsClientsActives( $farmname, @content );
my @conns_header = split ( "\t", @activeclients[0] );

print "<form method=\"post\" action=\"index.cgi\" class=\"myform\">";
print "<input type=\"hidden\" name=\"id\" value=\"1-2\">";
print "<input type=\"hidden\" name=\"action\" value=\"managefarm\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print
  "<input type=\"hidden\" name=\"viewtableclients\" value=\"$viewtableclients\">";
if ( $viewtableconn eq "yes" )
{
	print "<input type=\"hidden\" name=\"viewtableconn\" value=\"no\">";
	print
	  "<p class=\"grid_12\"><input type=\"submit\" class=\"button grey\" value=\"Dismiss active connections table\"></p>";
}
else
{
	print "<input type=\"hidden\" name=\"viewtableconn\" value=\"yes\">";
	print
	  "<p class=\"grid_12\"><input type=\"submit\" class=\"button grey\" value=\"Show active connections table\"></p>";
}
print "</form>";

if ( $viewtableconn eq "yes" )
{

	print "
               <div class=\"box grid_12\">
                 <div class=\"box-head\">
                       <span class=\"box-icon-24 fugue-24 system-monitor\"></span>       
                       <h2>@conns_header[0] @conns_header[1]</h2>
                 </div>
                 <div class=\"box-content no-pad\">
                         <table id=\"connections-table\" class=\"display\">
                         <thead>
                               <tr>
                                 <th>Connection</th>
                                 <th>Client</th>
                                 <th>Server</th>
                               </tr>
                         </thead>
                         <tbody>
       ";

	foreach ( @activeclients )
	{
		my @s_backend = split ( "\t", $_ );
		if ( @s_backend[0] =~ /^[0-9]/ )
		{
			print
			  "<tr><td>@s_backend[0]  </td><td>@s_backend[1]  </td><td>@s_backend[2] </td></tr>";
		}
	}
	print "</tbody>";
	print "</table>";
	print "</div></div>\n\n";
}

print "<!--END MANAGE-->";

print "
<script>
\$(document).ready(function() {
    \$('#backends-table').DataTable( {
        \"bJQueryUI\": true,     
               \"sPaginationType\": \"full_numbers\"   
    });
       \$('#clients-table').DataTable( {
        \"bJQueryUI\": true,     
               \"sPaginationType\": \"full_numbers\"   
    });
       \$('#connections-table').DataTable( {
        \"bJQueryUI\": true,     
               \"sPaginationType\": \"full_numbers\"   
    });
} );
</script>";

