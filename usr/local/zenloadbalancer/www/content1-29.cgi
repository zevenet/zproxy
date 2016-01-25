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

#STATUS of a L4xNAT Farm

if ( $viewtableclients eq "" ) { $viewtableclients = "no"; }

# Real Server Table
my $nattype = &getFarmNatType( $farmname );
my $proto   = &getFarmProto( $farmname );
if ( $proto eq "all" )
{
	$proto = "";
}

$fvip = &getFarmVip( "vip", $farmname );

my @content = &getFarmBackendStatusCtl( $farmname );
my @backends = &getFarmBackendsStatus( $farmname, @content );

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

&refreshstats();

print "
    <div class=\"box container_12 grid_12\">
      <div class=\"box-head\">
           <span class=\"box-icon-24 fugue-24 server\"></span>   
        <h2>Real servers status $backendsize servers, $activebackends active </h2>
      </div>
      <div class=\"box-content no-pad\">
";

print "<table class=\"display\">\n";
print "<thead>\n";
print
  "<tr><th>Server</th><th>Address</th><th>Port(s)</th><th>Status</th><th>Pending Conns</th><th>Established Conns</th></tr>";
print "</thead>\n";
print "<tbody>";

my $index = 0;
foreach ( @backends )
{
	my @backends_data = split ( ";", $_ );
	my $ip_backend    = $backends_data[0];
	my $port_backend  = $backends_data[1];
	print "<tr>";
	print "<td> $index </td> ";
	print "<td> $ip_backend </td> ";
	print "<td> $port_backend </td> ";
	if ( $backends_data[4] eq "maintenance" )
	{
		print "<td><img src=\"img/icons/small/warning.png\" title=\"up\"></td> ";
	}
	elsif ( $backends_data[4] eq "up" )
	{
		print "<td><img src=\"img/icons/small/start.png\" title=\"up\"></td> ";
	}
	elsif ( $backends_data[4] eq "fgDOWN" )
	{
		print
		  "<td><img src=\"img/icons/small/disconnect.png\" title=\"FarmGuardian down\"></td> ";
	}
	else
	{
		print "<td><img src=\"img/icons/small/stop.png\" title=\"down\"></td> ";
	}

	my @synnetstatback;
	@netstat = &getConntrack( "", $fvip, $ip_backend, "", "" );
	@synnetstatback =
	  &getBackendSYNConns( $farmname, $ip_backend, $port_backend, @netstat );
	my $npend = @synnetstatback;
	print "<td>$npend</td>";

	my @stabnetstatback;
	@stabnetstatback =
	  &getBackendEstConns( $farmname, ${ ip_backend }, $port_backend, @netstat );
	my $nestab = @stabnetstatback;
	print "<td>$nestab</td>";
	print "</tr>";
	$index++;
}

print "</tbody>";
print "</table>";
print "</div>\n</div>\n";

if ( $proto eq "sip" )
{

	# Active sessions
	print "<div class=\"box-header\">";
	my @csessions     = &getConntrackExpect();
	my $totalsessions = @csessions;

	if ( $viewtableclients eq "yes" )
	{
		print "
			<form method=\"post\" action=\"index.cgi\">
			<input type=\"submit\" value=\"Dismiss clients table\" name=\"buttom\" class=\"button grey\">
			<input type=\"hidden\" name=\"id\" value=\"1-2\">
			<input type=\"hidden\" name=\"action\" value=\"managefarm\">
			<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">
			<input type=\"hidden\" name=\"viewtableclients\" value=\"no\">
			<input type=\"hidden\" name=\"viewtableconn\" value=\"$viewtableconn\">
			</form>";
	}
	else
	{
		print "
			<form method=\"post\" action=\"index.cgi\">
			<input type=\"submit\" value=\"Show clients table\" name=\"buttom\" class=\"button grey\">
			<input type=\"hidden\" name=\"id\" value=\"1-2\">
			<input type=\"hidden\" name=\"action\" value=\"managefarm\">
			<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">
			<input type=\"hidden\" name=\"viewtableclients\" value=\"yes\">
			<input type=\"hidden\" name=\"viewtableconn\" value=\"$viewtableconn\">
			</form>";
	}

	if ( $viewtableclients eq "yes" )
	{
		print "
                       <div class=\"box container_12 grid_12\">
                         <div class=\"box-head\">
                               <span class=\"box-icon-24 fugue-24 server\"></span>       
                               <h2>Client sessions status $totalsessions active clients</h2>
                         </div>
                         <div class=\"box-content no-pad\">
               ";
		print "<div class=\"box table\"><table class=\"display\">\n";
		print "<thead>\n";
		print "<tr><th>Client Address</th></tr>\n";
		print "</thead>";
		print "<tbody>";

		foreach $session ( @csessions )
		{
			print "<tr><td>$session</td></tr>";
		}
		print "</tbody>";
	}

	print "</table>";
	print "</div></div>";

}

print "<!--END MANAGE-->";

