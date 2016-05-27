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

my $socket = IO::Socket::INET->new( Proto => 'udp' );

#~ use Devel::Size qw(size total_size);
#~ &zenlog(Dumper $socket);
#~ &zenlog(total_size($socket));

my $iface = &getInterfaceConfig( $if, $ipv );

$if_flags = $socket->if_flags( $$iface{ name } );

if ( !$$iface{ addr } )
{
	my %if = %{ &getDevVlanVini( $interface ) };

	# populate not configured interface
	$$iface{ status } = ( $if_flags & IFF_UP ) ? "up" : "down";
	$$iface{ mac }    = $socket->if_hwaddr( $if );
	$$iface{ name }   = $if;

	#~ $$iface{ addr }   = '-';
	#~ $$iface{ mask }   = '-';
	$$iface{ dev }  = $if{ dev };
	$$iface{ vlan } = $if{ vlan };
	$$iface{ vini } = $if{ vini };
	$$iface{ ip_v } = $ipv;
}

#~ &zenlog(Dumper $iface);

#~
#~ my (
#~ $ifmsg,
#~ $state,
#~ $ipaddr,
#~ $netmask,
#~ $broadcast,
#~ $gwaddr,
#~ $vlan,
#~ $if
#~ );

# state is global, from cgi
if ( $state eq "up" )
{
	# Reading from system
	$$iface{ ifmsg } = "The interface is running, getting config from system...";
}
else
{
	$$iface{ ifmsg } = "The interface is down, getting config from system files...";
}

$$iface{ bcast } = $socket->if_broadcast( $$iface{ name } );

#~ &zenlog(Dumper $iface);

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
print "<input type=\"hidden\" name=\"if\" value=\"$$iface{name}\">";
print "<input type=\"hidden\" name=\"toif\" value=\"$$iface{dev}\">";
print "<input type=\"hidden\" name=\"status\" value=\"$$iface{status}\">";

#print "<div class=\"form-row\"><p>$ifmsg</p></div>";

# Interface name
print "<div class=\"form-row\">";
print "<p class=\"form-label\">Interface Name:</p>";
print "<div class=\"form-item\">";
print "<p class=\"form-label\">$$iface{name}</p></div>";
print "</div>";

# Hardware address
print "<div class=\"form-row\">";
print "<p class=\"form-label\">HWaddr:</p>";
print "<div class=\"form-item\">";
print "<p class=\"form-label\">$$iface{mac}</p></div>";
print "</div>";

# IP version
print "<div class=\"form-row\">";
print "<p class=\"form-label\">IPv:</p>";
print "<div class=\"form-item\">";
print "<p class=\"form-label\">$$iface{ip_v}</p>";
print "</div>";

print "<input type=\"hidden\" name=\"ipv\" value=\"$$iface{ip_v}\">";
print "</div>";

# Ip address
print "<div class=\"form-row\">";
print "<p class=\"form-label\">IP Addr:</p>";
print "<div class=\"form-item\">";
print
  "<input type=\"text\" value=\"$$iface{addr}\" size=\"15\" class=\"fixedwidth\" name=\"newip\">";
print "</div>";
print "</div>";

# Netmask/Bitmask
print "<div class=\"form-row\">";
print "<p class=\"form-label\">Netmask/Bitmask:</p>";
if ( $if =~ /\:/ )
{
	print "<div class=\"form-item\">";
	print "<p class=\"form-label\">$$iface{mask}</p></div>";
	print "<input type=\"hidden\" name=\"netmask\" value=\"$$iface{mask}\">";
}
else
{
	print "<div class=\"form-item\">";
	print
	  "<input type=\"text\" value=\"$$iface{mask}\" size=\"15\" class=\"fixedwidth\" name=\"netmask\">";
	print "</div>";
}
print "</div>";

# Broadcast
if ( !$$iface{ ip_v } )
{
	print "<div class=\"form-row\">";
	print "<p class=\"form-label\">Broadcast:</p>";
	print "<div class=\"form-item\"><p class=\"form-label\">";

	if ( !$$iface{ bcast } )
	{
		print "-";
	}
	else
	{
		print "$$iface{bcast}";
	}
	print "</p></div></div>";
}

# Gateway
print "<div class=\"form-row\">";
print "<p class=\"form-label\">Default Gateway:</p>";
print "<div class=\"form-item\">";
if ( $$iface{ name } =~ /\:/ )
{
	if ( $$iface{ gateway } eq "" )
	{
		print "-";
	}
	else
	{
		my @splif = split ( "\:", $$iface{ name } );
		my $ifused = &uplinkUsed( $splif[0] );
		if ( $ifused eq "false" )
		{
			print "$$iface{gateway}";
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
	my $ifused = &uplinkUsed( $$iface{ name } );
	if ( $ifused eq "false" )
	{
		print
		  "<input type=\"text\" value=\"$$iface{gateway}\" size=\"15\" class=\"fixedwidth\" name=\"gwaddr\">";
	}
	else
	{
		print
		  "<img src=\"img/icons/small/lock.png\" title=\"A datalink farm is locking the gateway of this interface\">";
	}
}
print "</div></div>";

# VLAN tag
print "<div class=\"form-row\">";
print "<p class=\"form-label\">Vlan tag:</p>";
print "<div class=\"form-item\"><p class=\"form-label\">";
if ( !$$iface{ vlan } )
{
	print "-";
}
else
{
	print "$$iface{vlan}";
}
print "</p></div></div>";

# Buttons row
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

