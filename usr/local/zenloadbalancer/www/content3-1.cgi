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

my $host = getHostname();

print "
  <!--- CONTENT AREA -->
  <div class=\"content container_12\">
";

###################################
#BREADCRUMB
###################################
print "<div class=\"grid_6\"><h1>Settings :: Server</h1></div>\n";

####################################
# CLUSTER STATUS
####################################
&getClusterStatus();

#process changes in global.conf when action=Modify

if ( $action =~ /^Modify$/ )
{
	#Get actual values
	$nextline = "false";
	open FR, "$globalcfg";
	my $i      = 0;    #Counter
	my $linea  = 0;
	my $flag   = 0;    #For showing changes
	my @linea  = ();
	my @values = ();
	while ( <FR> )
	{

		if ( $_ =~ /^#::INI/ )
		{
			$linea = $_;
			$linea =~ s/^#::INI//;
			my @actionform = split ( /\ /, $linea );
		}
		if ( $_ =~ /^#\./ )
		{
			$nextline = "true";
			$linea    = $_;
			$linea =~ s/^#\.//;
		}

		if ( $_ =~ /^\$/ && $nextline eq "true" )
		{
			$nextline = "false";
			@linea = split ( /=/, $_ );
			@linea[1] =~ s/"||\;//g;
			@linea[0] =~ s/^\$//g;
			chomp ( @linea[0] );
			chomp ( @linea[1] );
			if (    @linea[0] =~ /timeouterrors/
				 or @linea[0] =~ /ntp/
				 or @linea[0] =~ /zenrsync/ )
			{
				@values[$i]     = @linea[0];
				@values[$i + 1] = @linea[1];
				$i              = $i + 2;
			}
		}

	}
	close FR;

	#Modify Time Out Execution
	if ( $touterr ne @values[1] )
	{
		use Tie::File;
		tie @array, 'Tie::File', "$globalcfg";
		for ( @array )
		{
			s/\$$var1.*/\$$var1=\"$touterr\";/g;
		}
		untie @array;
		&successmsg( "Time out execution has been modified" );
	}

	#Modify Ntp Server
	if ( $ntp ne @values[3] )
	{
		use Tie::File;
		tie @array, 'Tie::File', "$globalcfg";
		for ( @array )
		{
			s/\$$var2.*/\$$var2=\"$ntp\";/g;
		}
		untie @array;
		&successmsg( "Ntp server has been modified" );
	}

	#Modify Rsync Replication Parameters
	if ( $zenrsync ne @values[5] )
	{
		use Tie::File;
		tie @array, 'Tie::File', "$globalcfg";
		for ( @array )
		{
			s/\$$var3.*/\$$var3=\"$zenrsync\";/g;
		}
		untie @array;
		&successmsg( "Rsync replication parameters have been modified" );
	}

	#dns modifications
	if ( $var eq "dns" )
	{
		print "var es $var";
		@dns = split ( "\ ", $line );
		open FW, ">$filedns";
		foreach $dnsserv ( @dns )
		{
			print FW "nameserver $dnsserv\n";
		}
		close FW;
	}
	if ( $var eq "mgwebip" || $var eq "mgwebport" )
	{
		&successmsg( "Changes OK, restart web service now" );
	}

	#actions with Modify buttom
}

#Modify Configuration
if ( $action eq "Modify Configuration" )
{
	#action Save DNS
	open FW, ">$filedns";
	print FW "$dnsserv";
	close FW;

	#action save ip
	use Tie::File;
	tie @array, 'Tie::File', "$confhttp";
	if ( $ipgui =~ /^\*$/ )
	{
		@array[1] = "#server!bind!1!interface = \n";
		&zenlog( "The interface where is running is --All interfaces--" );
	}
	else
	{
		@array[1] = "server!bind!1!interface = $ipgui\n";

		#~ if ( &ipversion( $ipgui ) eq "IPv6" )
		#~ {
		#~ @array[4] = "server!ipv6 = 1\n";
		#~ &zenlog(
		#~ "The interface where is running the GUI service is: $ipgui with IPv6" );
		#~ }
		#~ elsif ( &ipversion( $ipgui ) eq "IPv4" )
		#~ {
		#~ @array[4] = "server!ipv6 = 0\n";
		#~ &zenlog(
		#~ "The interface where is running the GUI service is: $ipgui with IPv4" );
		#~ }
	}
	untie @array;

	# save snmp ip
	my $mgmt_ip = &getHttpServerIp();
	my %snmp    = %{ &getSnmpdConfig() };

	&zenlog( "mgmt_ip:$mgmt_ip" );

	# if snmp ip is different to management ip
	if ( $snmp{ ip } ne $mgmt_ip )
	{
		# with the exception of * in management, it is 0.0.0.0 for snmp server
		if ( !( $mgmt_ip eq '*' && $snmp{ ip } eq '0.0.0.0' ) )
		{
			$snmp{ ip } = $mgmt_ip;
			&setSnmpdConfig( \%snmp );
		}
	}

	#Change GUI https port
	&setHttpServerPort( $guiport, $confhttp );

	&successmsg( "Some changes were applied for Local configuration" );
}

#Restart GUI Server Button
if ( $action eq "Restart GUI Service" )
{
	if ( $pid = fork )
	{

		#$SIG{'CHLD'}='IGNORE';
		#print "Proceso de restart lanzado ...";
	}
	elsif ( defined $pid )
	{
		# snmpd restart if running
		if ( &getSnmpdStatus() eq 'true' )
		{
			&setSnmpdStatus( 'false' );    # stopping snmp
			&setSnmpdStatus( 'true' );     # starting snmp
		}

		system ( "/etc/init.d/cherokee restart > /dev/null &" );
		exit ( 0 );
	}
	if ( $ipgui =~ /^$/ )
	{
		$ipgui = &getHttpServerIp();
	}
	if ( $guiport =~ /^$/ )
	{
		$guiport = &getHttpServerPort( $confhttp );
	}
	if ( $ipgui =~ /\*/ )
	{
		&successmsg( "Restarted Service, access to GUI over any IP on port $guiport" );
	}
	else
	{
		&successmsg(
			"Restarted Service, access to GUI over $ipgui IP on port $guiport <a href=\"https:\/\/$ipgui:$guiport\/index.cgi?id=$id\">go here</a>"
		);
	}
}

my %snmp;

if ( $action eq "Apply" )
{
	%snmp = (
			  status => $snmpd_enabled // 'false',
			  port => $snmpd_port,
			  community => $snmpd_community,
			  scope     => $snmpd_scope,
	);

	$snmp{ ip } = &getHttpServerIp();

	my $snmp_error = &applySnmpChanges( \%snmp );

	if ( $snmp_error )
	{
		&errormsg( "SNMP service change could not be applied." );

	}
	else
	{
		&successmsg( "SNMP service change applied." );
	}
}

%snmp = %{ &getSnmpdConfig() };
$snmp{ status } = &getSnmpdStatus();
my $snmp_check = 'checked' if $snmp{ status } eq 'true';

#~ &zenlog( Dumper \%snmp );

print "<form method=\"post\" action=\"index.cgi\">";

#open glogal file config
$nextline = "false";
open FR, "$globalcfg";
while ( <FR> )
{
	if ( $_ =~ /^#::INI/ )
	{
		$linea = $_;
		$linea =~ s/^#::INI//;
		my @actionform = split ( /\ /, $linea );
		print "
                       <div class=\"box grid_12\">
                         <div class=\"box-head\">
                               <span class=\"box-icon-24 fugue-24 globe\"></span>        
                               <h2>$linea</h2>
                         </div>
                         <div class=\"box-content global-farm\">
		";
	}
	if ( $_ =~ /^#\./ )
	{
		$nextline = "true";
		print "<div class=\"form-row\">";
		$linea = $_;
		$linea =~ s/^#\.//;
		print "<p class=\"form-label\"><label>$linea</label></p>";
	}

	if ( $_ =~ /^\$/ && $nextline eq "true" )
	{
		$nextline = "false";
		my @linea = split ( /=/, $_ );
		@linea[1] =~ s/"||\;//g;
		@linea[0] =~ s/^\$//g;
		chomp ( @linea[1] );
		chomp ( @linea[0] );

		print "<input type=\"hidden\" name=\"id\" value=\"3-1\">";
		print "<div class=\"form-item\">";
		if ( @linea[0] eq "timeouterrors" )
		{
			print
			  "<input type=\"number\" value=\"@linea[1]\" size=\"20\" name=\"touterr\" class=\"fixedwidth\"> ";
			print "<input type=\"hidden\" name=\"var1\" value=\"@linea[0]\">";
		}
		elsif ( @linea[0] eq "ntp" )
		{
			print
			  "<input type=\"text\" value=\"@linea[1]\" size=\"20\" name=\"ntp\" class=\"fixedwidth\"> ";
			print "<input type=\"hidden\" name=\"var2\" value=\"@linea[0]\">";
		}
		elsif ( @linea[0] eq "zenrsync" )
		{
			print
			  "<input type=\"text\" value=\"@linea[1]\" size=\"20\" name=\"zenrsync\" class=\"fixedwidth\"> ";
			print "<input type=\"hidden\" name=\"var3\" value=\"@linea[0]\">";
		}

		print "</div>";
		print "</div>";
	}

	if ( $_ =~ /^#::END/ )
	{
		print "<br>";
		print
		  "<input type=\"submit\" value=\"Modify\" name=\"action\" class=\"button grey\">";
		print "</div></div>";
	}
}

close FR;

print "</form>";

#
#Local configuration
#

print "
<div class=\"box grid_12\">
	<div class=\"box-head\">
		<span class=\"box-icon-24 fugue-24 server\"></span>
		<h2>Local configuration</h2>
	</div>
	<div class=\"box-content global-farm\">
";

#
# Physical interface
#

print "
		<form method=\"post\" action=\"index.cgi\">
			<div class=\"form-row\">
				<p class=\"form-label\">
					<b>Physical interface where is running GUI service. </b>
					 If cluster is up you only can select \"--All interfaces--\" option, or \"the cluster interface\". Changes need restart GUI service.
				</p>
				<input type=\"hidden\" name=\"id\" value=\"3-1\">
";

my $hosthttp = &getHttpServerIp();

# Print "Zen cluster service is UP, Zen GUI should works over ip $lip";
print "
				<div class=\"form-item\">
					<select name=\"ipgui\" class=\"fixedwidth monospace\">
";

#~ $existiphttp = "false";
if ( $hosthttp eq '*' )
{
	print "<option value=\"*\" selected=\"selected\">--All interfaces--</option>\n";

	#~ $existiphttp = "true";
}
else
{
	print "<option value=\"*\">--All interfaces--</option>\n";
}

# management interface candidates
my @interfaces_available = @{ &getActiveInterfaceList() };

foreach my $iface ( @interfaces_available )
{
	next if $$iface{ vini } ne ''; # discard virtual interfaces

	my $selected = '';

	if ( $hosthttp eq $$iface{ addr } )
	{
		$selected = "selected=\"selected\"";
	}

	print
	  "<option value=\"$$iface{addr}\" $selected>$$iface{dev_ip_padded}</option>\n";

}

print "
					</select>
				</div>
			</div>
";

#
# HTTPS port for GUI interface
#
my $guiport = &getHttpServerPort();
if ( $guiport =~ /^$/ )
{
	$guiport = 444;
}

print "
			<div class=\"form-row\">
				<p class=\"form-label\">
					<b>HTTPS Port where is running GUI service.</b>
					Default is 444. Changes need restart GUI service.
				</p>
";

print "
				<div class=\"form-item\">
";
print "
					<input type=\"number\" name=\"guiport\" class=\"fixedwidth\" value=\"$guiport\" size=\"12\">
				</div>
			</div>
";

#
# DNS servers
#
print "
			<div class=\"form-row\">
				<p class=\"form-label\">
					<b>DNS servers</b>
				</p>
				<div class=\"form-item\">
					<textarea name=\"dnsserv\" cols=\"30\" rows=\"2\" align=\"center\" class=\"fixedwidth\">
";
open FR, "$filedns";
print <FR>;
print "
					</textarea>
				</div>
			</div>
";

print "
			<input type=\"submit\" value=\"Modify Configuration\" name=\"action\" class=\"button grey\">
			<input type=\"submit\" value=\"Restart GUI Service\" name=\"action\" class=\"button grey\">
";

print "
		</form>
	</div>
</div>
";

#
# SNMP service
#

print "
<div class=\"box grid_12\">
	<div class=\"box-head\">
		<span class=\"box-icon-24 fugue-24 server\"></span>
		<h2>SNMP</h2>
	</div>
	<div class=\"box-content global-farm\">
";

print "
		<form method=\"post\" action=\"index.cgi\">
			<input type=\"hidden\" name=\"id\" value=\"3-1\">
";

# SNMP enable

print "
			<div class=\"form-row\">
				<p class=\"form-label\">
					<b>SNMP Service</b>
				</p>
				<div class=\"form-item\">
					<input type=\"checkbox\" name=\"snmpd_enabled\" value=\"true\" $snmp_check>
				</div>
			</div>
";

# SNMP port
print "
			<div class=\"form-row\">
				<p class=\"form-label\">
					<b>Port</b>
				</p>
				<div class=\"form-item\">
					<input type=\"number\" name=\"snmpd_port\" class=\"fixedwidth\" value=\"$snmp{port}\" size=\"12\" required>
				</div>
			</div>
";

# SNMP community
print "
			<div class=\"form-row\">
				<p class=\"form-label\">
					<b>Community name</b>
				</p>
				<div class=\"form-item\">
					<input type=\"text\" name=\"snmpd_community\" class=\"fixedwidth\" value=\"$snmp{community}\" size=\"12\" required>
				</div>
			</div>
";

# SNMP scope
print "
			<div class=\"form-row\">
				<p class=\"form-label\">
					<b>IP or subnet with access (IP/bit)</b>
				</p>
				<div class=\"form-item\">
					<input type=\"text\" name=\"snmpd_scope\" class=\"fixedwidth\" value=\"$snmp{scope}\" size=\"12\" required>
				</div>
			</div>
";

# Buttons
print "
			<input type=\"submit\" value=\"Apply\" name=\"action\" class=\"button grey\">
";

# Close box
print "
		</form>
	</div>
</div>
";

# Content END
print "
</div>
<br class=\"cl\">
<!--Content END-->
";

1;
