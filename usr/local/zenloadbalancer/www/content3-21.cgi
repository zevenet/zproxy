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

my $s = IO::Socket::INET->new( Proto => 'udp' );
my $flags = $s->if_flags( $if );

$hwaddr = $s->if_hwaddr( $if );
if ( $flags & IFF_RUNNING )
{
	$state = "up";
}
else
{
	$state = "down";
}

if ( $source eq "system" && $state eq "up" )
{

	# Reading from system
	$ifmsg     = "The interface is running, getting config from system...";
	$state     = "up";
	$ipaddr    = $s->if_addr( $if );
	$netmask   = $s->if_netmask( $if );
	$broadcast = $s->if_broadcast( $if );

	#	$iface = "eth0.50:2";
	# Calculate VLAN
	@fiface = split ( /:/,  $if );
	@viface = split ( /\./, $fiface[0] );
	$vlan   = $viface[1];
	$gwaddr = &getDefaultGW( $if );
}
else
{

	# Reading from config files
	$ifmsg = "The interface is down, getting config from system files...";
	$state = "down";

	# Calculate VLAN
	@fiface = split ( /\:/, $if );
	@viface = split ( /\./, $fiface[0] );
	$vlan   = $viface[1];

	# Reading Config File
	$file = "$configdir/if_$if\_conf";
	tie @array, 'Tie::File', "$file", recsep => ':';
	$ipaddr  = $array[2];
	$netmask = $array[3];
	$state   = $array[4];
	$gwaddr  = $array[5];
	untie @array;
}

print "
               <div class=\"box grid_12\">
                 <div class=\"box-head\">
                       <span class=\"box-icon-24 fugue-24 server\"></span>       
                       <h2>Edit a new network interface</h2>
                 </div>
                 <div class=\"box-content global-farm\">
       ";

print "<form method=\"post\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"if\" value=\"$if\">";
print "<input type=\"hidden\" name=\"status\" value=\"$status\">";

#print "<div class=\"form-row\"><p>$ifmsg</p></div>";
print "<div class=\"form-row\">";
print "<p class=\"form-label\">Interface Name:</p>";
print "<div class=\"form-item\"><p class=\"form-label\">$if</p></div>";
print "</div>";
print "<div class=\"form-row\">";
print "<p class=\"form-label\">HWaddr:</p>";
print "<div class=\"form-item\"><p class=\"form-label\">$hwaddr</p></div>";
print "</div>";
print "<div class=\"form-row\">";
print "<p class=\"form-label\">IP Addr:</p>";
print
  "<div class=\"form-item\"><input type=\"text\" value=\"$ipaddr\" size=\"15\" class=\"fixedwidth\" name=\"newip\"></div>";
print "</div>";
print "<div class=\"form-row\">";
print "<p class=\"form-label\">Netmask:</p>";
print
  "<div class=\"form-item\"><input type=\"text\" value=\"$netmask\" size=\"15\" class=\"fixedwidth\" name=\"netmask\"></div>";
print "</div>";
print "<div class=\"form-row\">";
print
  "<p class=\"form-label\">Broadcast:</p><div class=\"form-item\"><p class=\"form-label\">";

if ( $broadcast eq "" )
{
	print "-";
}
else
{
	print "$broadcast";
}
print "</p></div></div>";

print "<div class=\"form-row\">";
print "<p class=\"form-label\">Default Gateway:</p>";
print "<div class=\"form-item\">";
if ( $if =~ /\:/ )
{
	if ( $gwaddr eq "" )
	{
		print "-";
	}
	else
	{
		my @splif = split ( "\:", $if );
		my $ifused = &uplinkUsed( @splif[0] );
		if ( $ifused eq "false" )
		{
			print "$gwaddr";
		}
		else
		{
			print
			  "<i class=\"fa fa-lock action-icon fa-fw\" title=\"A datalink farm is locking the gateway of this interface\"></i>";
		}
	}
}
else
{
	my $ifused = &uplinkUsed( $if );
	if ( $ifused eq "false" )
	{
		print
		  "<input type=\"text\" value=\"$gwaddr\" size=\"15\" class=\"fixedwidth\" name=\"gwaddr\">";
	}
	else
	{
		print
		  "<img src=\"img/icons/small/lock.png\" title=\"A datalink farm is locking the gateway of this interface\">";
	}
}
print "</div></div>";

print "<div class=\"form-row\">";
print "<p class=\"form-label\">Vlan tag:</p>";
print "<div class=\"form-item\"><p class=\"form-label\">";
if ( $vlan eq "" )
{
	print "-";
}
else
{
	print "$vlan";
}
print "</p></div></div>";
print "<div class=\"form-row\">";
print "<p class=\"form-label\">&nbsp;</p>";
print
  "<div class=\"form-item\"><input type=\"submit\" value=\"Save & Up!\" name=\"action\" class=\"button grey\"> ";
print
  "<input type=\"submit\" value=\"Cancel\" name=\"action\" class=\"button grey\"></div>";
print "</form>";
print "</div>";

print "</div>";
print "</div>";

