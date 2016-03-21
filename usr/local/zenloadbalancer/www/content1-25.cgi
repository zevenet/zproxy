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

#STATUS of a HTTP(S) farm

if ( $viewtableclients eq "" ) { $viewtableclients = "no"; }

# Real Server Table
my @netstat;
$fvip = &getFarmVip( "vip", $farmname );
$fpid = &getFarmChildPid( $farmname );

my @content = &getFarmBackendStatusCtl( $farmname );
my @backends = &getFarmBackendsStatus( $farmname, @content );

#TEMPORAL:
my @a_services;
my $sv;
foreach ( @content )
{
	if ( $_ =~ /Service/ )
	{
		my @l = split ( "\ ", $_ );
		$sv = @l[2];
		$sv =~ s/"//g;
		chomp ( $sv );
		push ( @a_service, $sv );
	}
}

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

&refreshstats();

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
              <th>Service</th>                 
              <th>Server</th>
              <th>Address</th>
              <th>Port</th>
                         <th>Status</th>
                         <th>Pending Conns</th>
                         <th>Established Conns</th>
            </tr>
          </thead>
          <tbody>
";

my $i = -1;
foreach ( @backends )
{
	my @backends_data = split ( "\t", $_ );
	$activesessions = $activesessions + $backends_data[6];
	print "<tr>";
	print "<td>";
	if ( $backends_data[0] == 0 )
	{
		$i++;
	}
	print "@a_service[$i]";

	print "</td>";
	print "<td> $backends_data[0] </td> ";
	print "<td> $backends_data[1] </td> ";
	print "<td> $backends_data[2] </td> ";
	if ( $backends_data[3] eq "maintenance" )
	{
		print
		  "<td class=\"aligncenter\"><img src=\"img/icons/small/warning.png\" title=\"Maintenance\"></td> ";
	}
	elsif ( $backends_data[3] eq "up" )
	{
		print
		  "<td class=\"aligncenter\"><img src=\"img/icons/small/start.png\" title=\"Up\"></td> ";
	}
	elsif ( $backends_data[3] eq "fgDOWN" )
	{
		print
		  "<td class=\"aligncenter\"><img src=\"img/icons/small/disconnect.png\" title=\"FarmGuardian down\"></td> ";
	}
	else
	{
		print
		  "<td class=\"aligncenter\"><img src=\"img/icons/small/stop.png\" title=\"Down\"></td> ";
	}
	$ip_backend   = $backends_data[1];
	$port_backend = $backends_data[2];
	@netstat      = &getConntrack( "", $ip_backend, "", "", "tcp" );
	@synnetstatback =
	  &getBackendSYNConns( $farmname, $ip_backend, $port_backend, @netstat );
	$npend = @synnetstatback;
	print "<td>$npend</td>";
	@stabnetstatback =
	  &getBackendEstConns( $farmname, $ip_backend, $port_backend, @netstat );
	$nestab = @stabnetstatback;
	print "<td>$nestab</td>";

	#TODO count number of session by backend
	#print "<td> $backends_data[5] </td>";
	print "</tr>";
}

print "</tbody>";
print "</table>";
print "</div></div>\n\n";

# Client Sessions Table
print "<div class=\"box-header\">";

print "<form method=\"post\" action=\"index.cgi\" class=\"myform\">";
if ( $viewtableclients eq "yes" )
{
	print
	  "<p class=\"grid_12\"><input type=\"submit\" class=\"button grey\" value=\"Dismiss sessions status table\"></p>";
	print "<input type=\"hidden\" name=\"viewtableclients\" value=\"no\">";
}
else
{
	print
	  "<p class=\"grid_12\"><input type=\"submit\" class=\"button grey\" value=\"Show sessions status table\"></p>";
	print "<input type=\"hidden\" name=\"viewtableclients\" value=\"yes\">";
}
print "<input type=\"hidden\" name=\"id\" value=\"1-2\">";
print "<input type=\"hidden\" name=\"action\" value=\"managefarm\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "</form>";

my @sessions = &getFarmBackendsClientsList( $farmname, @content );
my $t_sessions = $#sessions + 1;

if ( $viewtableclients eq "yes" )
{
	print "
               <div class=\"box grid_12\">
                 <div class=\"box-head\">
                       <span class=\"box-icon-24 fugue-24 user-business\"></span>        
                       <h2>Client sessions status $t_sessions active sessions</h2>
                 </div>
                 <div class=\"box-content no-pad\">
                         <table id=\"clients-table\" class=\"display\">
                         <thead>
                               <tr>
                                 <th>Service</th>
                                 <th>Client</th>
                                 <th>Session ID</th>
                                 <th>Server</th>
                               </tr>
                         </thead>
                         <tbody>
       ";

	foreach ( @sessions )
	{
		my @sessions_data = split ( "\t", $_ );
		print "<tr>";
		print "<td> $sessions_data[0] </td> ";
		print "<td> $sessions_data[1] </td> ";
		print "<td> $sessions_data[2] </td> ";
		print "<td> $sessions_data[3] </td> ";
		print "</tr>";
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
} );
</script>";

