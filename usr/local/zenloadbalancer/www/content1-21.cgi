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

if ( $action eq "Save" )
{
	#check if farm name is ok
	$farmname =~ s/\ //g;
	$farmname =~ s/\_//g;
	&setFarmName( $farmname );

	#check ip is ok
	$error = 'false';
	@fvip  = split ( " ", $vip );
	$fdev  = $fvip[0];
	$vip   = $fvip[1];

	if ( $vip eq '' )
	{
		$error = 'true';
		&errormsg(
			"Please select a Virtual IP or add a new Virtual IP in \"Settings >> Interfaces\" Section"
		);
		$action = 'addfarm';
	}

	#check if vipp is a number and if vipp in the correct vip is not in use.
	if ( $farmname eq '' )
	{
		$error = 'true';
		&errormsg( "The farm name can't be empty" );
		$action = "addfarm";
	}

	if ( $farmprotocol =~ /TCP|HTTP|UDP|HTTPS|GSLB/ )
	{
		if ( $farmprotocol eq 'TCP' )
		{
			&warnmsg( "This profile is deprecated, use L4xNAT instead" );
		}
		if ( &isnumber( $vipp ) eq 'true' && &isValidPortNumber( $vipp ) eq 'true' )
		{
			$inuse = &checkport( $vip, $vipp );
			if ( $inuse eq 'true' )
			{
				$error = 'true';
				&errormsg(
					"The Virtual Port $vipp in Virtual IP $vip is in use, select another port or add another Virtual IP"
				);
				$action = 'addfarm';
			}
		}
		else
		{
			$error = 'true';
			&errormsg( 'Invalid Virtual Port value' );
			$action = 'addfarm';
		}
	}

	if ( $farmprotocol eq 'L4xNAT' && &GUIip() eq $vip )
	{
		&errormsg(
			"Invalid Virtual IP $vip, it's the same VIP than the GUI access. Please choose another one."
		);
		$error = 'true';
	}

	if ( $error eq 'false' )
	{
		$error = 0;

		# creating a new farm
		$status = &runFarmCreate( $farmprotocol, $vip, $vipp, $farmname, $fdev );
		if ( $status == -1 )
		{
			&errormsg( "The $farmname farm can't be created" );
			$error = 1;
		}
		if ( $status == -2 )
		{
			&errormsg(
					   "The $farmname farm already exists, please set a different farm name" );
			$error = 1;
		}
		if ( $error == 0 )
		{
			&successmsg(
				"The $farmname farm has been added to VIP $vip over $fdev, now you can manage it"
			);
		}
		else
		{
			$action = 'addfarm';
		}
	}
}

if ( $action eq 'addfarm' || $action eq "Save & continue" )
{
	if ( $farmprotocol eq "TCP" )
	{
		&warnmsg( "This profile is deprecated, use L4xNAT instead" );
	}

	print "
		<div class=\"box grid_6\">
		  <div class=\"box-head\">
			<span class=\"box-icon-24 fugue-24 plus\"></span>     
			<h2>Configure a new Farm</h2>
		  </div>
		  <div class=\"box-content addfarm\">
			<form method=\"post\" action=\"index.cgi\">
			  <input type=\"hidden\" name=\"id\" value=\"$id\">
			  <div class=\"form-row\">
				<p class=\"form-label\">
				  <b>Farm description name</b>
				</p>
				<div class=\"form-item\">
				  <input type=\"text\" value=\"$farmname\" name=\"farmname\">
				</div>
			  </div>
			  <div class=\"form-row\">
				<p class=\"form-label\">
				  <b>Profile</b>
				</p>
	";

	if ( $farmprotocol eq "" || $farmname eq "" )
	{
		print "
				<div class=\"form-item\">
				  <select name=\"farmprotocol\">
					<option value=\"L4xNAT\">L4xNAT (Default)</option>
					<option value=\"HTTP\">HTTP</option>
					<option value=\"DATALINK\">DATALINK</option>
					<option value=\"GSLB\">GSLB</option>
					<option value=\"TCP\">TCP</option>
				  </select>
				</div>
		";
	}
	else
	{
		print " <div class=\"form-item\">
				  <input type=\"text\" name=\"farmprotocol\" value=\"$farmprotocol\" disabled >
			    </div>
				<input type=\"hidden\" name=\"farmprotocol\" value=\"$farmprotocol\">";
	}
	print "	  </div>";
	if ( $farmprotocol ne "" && $farmname ne "" )
	{
		my @interfaces_available = @{ &getActiveInterfaceList() };

		#eth interface selection
		print "
			  <div class=\"form-row\">
				<p class=\"form-label\">";

		print "<b>Virtual IP</b>";

		print "
				</p>
			  <div class=\"form-item\">
				<select name=\"vip\" class=\"monospace width-initial\">
				  <option value=\"\">-Select One-</option>
			";

		for my $iface ( @interfaces_available )
		{
			# skip IPv6 interfaces for TCP farms
			next if $farmprotocol eq "TCP" && $$iface{ ip_v } == 6;

			# skip virtual interfaces for DataLink farms
			next if $farmprotocol eq "DATALINK" && $$iface{ vini } ne '';

			# skip local cluster IP
			next if &getClusterRealIp() eq $$iface{ addr };
			next if &GUIip eq $$iface{ addr } && (-e $filecluster);

			print
			  "<option value=\"$$iface{name} $$iface{addr}\">$$iface{dev_ip_padded}</option>\n";
		}

		print "
				</select>
			  </div>
			</div>
			<div class=\"form-row\">
			  <p class=\"form-label\"></p>
			  <div class=\"form-item\">
			    <p>
			      <b>Or add a
					<a href=\"index.cgi?id=3-2\"> new VIP interface
					</a>.
				  </b>
				</p>
			  </div>
			</div>
		";

		if ( $farmprotocol ne "DATALINK" )
		{    #vip port
			print "
			<div class=\"form-row\">
			  <p class=\"form-label\">
			    <b>Virtual Port(s)</b>
			  </p>
			  <div class=\"form-item\"><input type=\"text\" value=\"\" size=\"10\" name=\"vipp\">
			  </div>
			</div>
			";
		}

		print "
			<div class=\"form-row\">
			  <p class=\"form-label\"></p>
			  <div class=\"form-item\">
				<p>
				  <input type=\"submit\" value=\"Save\" name=\"action\" class=\"button grey\">
				</p>&nbsp;&nbsp;&nbsp;&nbsp;
				<p>
				  <input type=\"submit\" value=\"Cancel\" name=\"action\" class=\"button grey\">
				</p>
			  </div>
			</div>
		";
	}
	else
	{
		print "
			<div class=\"form-row\">
			  <p class=\"form-label\"></p>
			  <div class=\"form-item\">
				<p>
				  <input type=\"submit\" value=\"Save & continue\" name=\"action\" class=\"button grey\">
				</p>
				<p>
				  <input type=\"submit\" value=\"Cancel\" name=\"action\" class=\"button grey\">
				</p>
			  </div>
			</div>
		";
	}

	print "
		  </form>
		</div>
	  </div>";
}

print "<div class=\"clear\">&nbsp;</div>";

1;
