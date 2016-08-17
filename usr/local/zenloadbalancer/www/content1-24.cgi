###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, based in Sevilla (Spain)
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

### VIEW HTTP/HTTPS FARM ###

##########################################
# FARM GLOBAL PARAMETERS
##########################################

print "
    <div class=\"box container_12 grid_12\">
      <div class=\"box-head\">
           <span class=\"box-icon-24 fugue-24 globe\"></span>    
        <h2>Edit $farmname Farm global parameters</h2>
      </div>
      <div class=\"box-content grid-demo-12 global-farm\">
";

print "<div class=\"grid_6\">\n";

##########################################
# FARM NAME
##########################################

print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Farm's name.</b> Service will be restarted.</p>\n";
print "<form method=\"post\" action=\"index.cgi\" id=\"modify-param\">\n"
  ;    # form Modify Parameters
print "<input type=\"hidden\" name=\"action\" value=\"editfarm-Parameters\">\n";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">\n";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">\n";
print
  "<div class=\"form-item\"><input type=\"text\" class=\"fixedwidth\" value=\"$farmname\" size=\"25\" name=\"newfarmname\"></div>\n";
print "</div>\n";

##########################################
# FARM VIRTUAL IP AND VIRTUAL PORT
##########################################

my $vip   = &getFarmVip( "vip",  $farmname );
my $vport = &getFarmVip( "vipp", $farmname );
print "<div class=\"form-row\">\n";
print "<p class=\"form-label\"><b>Farm Virtual IP and Virtual port</b></p>\n";

$clrip = &getClusterRealIp();

my @interfaces_available = @{ &getActiveInterfaceList() };

print
  "<div class=\"form-item\"><select name=\"vip\" class=\"fixedwidth monospace\">\n";
print "<option value=\"\">-Select One-</option>\n";

for my $iface ( @interfaces_available )
{
	next if $$iface{ addr } eq $clrip;

	my $selected = '';

	if ( $$iface{ addr } eq $vip )
	{
		$selected = "selected=\"selected\"";
	}

	print
	  "<option value=\"$$iface{addr}\" $selected>$$iface{dev_ip_padded}</option>\n";
}

print
  "<input type=\"number\" class=\"fixedwidth-small\" value=\"$vport\" size=\"4\" name=\"vipp\"> \n";
print "</div>\n";
print "</div>\n";

##########################################
# BACKEND CONNECTION TIMEOUT
##########################################
my $connto = &getFarmConnTO( $farmname );
print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Backend connection timeout.</b> In seconds</p>\n";
print
  "<div class=\"form-item\"><input type=\"number\" class=\"fixedwidth\" value=\"$connto\" size=\"4\" name=\"conntout\"></div>\n";
print "</div>\n";

##########################################
# BACKEND RESPONSE TIMEOUT
##########################################
my $timeout = &getFarmTimeout( $farmname );
print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Backend response timeout.</b> In seconds</p>\n";
print
  "<div class=\"form-item\"><input type=\"number\" class=\"fixedwidth\" value=\"$timeout\" size=\"4\" name=\"resptout\"></div>\n";
print "</div>\n";

##########################################
# FREQUENCY TO CHECK RESURRECTED BACKENDS
##########################################
my $alive = &getFarmBlacklistTime( $farmname );
print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Frequency to check resurrected backends.</b> In seconds.</p>\n";
print
  "<div class=\"form-item\"><input type=\"number\" class=\"fixedwidth\" value=\"$alive\" size=\"4\" name=\"checkalive\"></div>\n";
print "</div>\n";

##########################################
# CLIENT TIMEOUT
##########################################
my $client = &getFarmClientTimeout( $farmname );
print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Client request timeout.</b> In seconds.</p>\n";
print
  "<div class=\"form-item\"><input type=\"number\" class=\"fixedwidth\" value=\"$client\" size=\"4\" name=\"clienttout\"></div>\n";
print "</div>\n";

##########################################
# REWRITE LOCATION
##########################################
my $type0 = "disabled";
my $type1 = "enabled";
my $type2 = "enabled and compare backends";

my $rewritelocation = &getFarmRewriteL( $farmname );

print "<div class=\"form-row\">\n";
print "<p class=\"form-label\"><b>Rewrite Location headers</b></p>\n";
print
  "<div class=\"form-item\"><select name=\"rewritelocation\" class=\"fixedwidth\">\n";

if ( $rewritelocation == 0 )
{
	print "<option value=\"0\" selected=\"selected\">$type0</option>\n";
}
else
{
	print "<option value=\"0\">$type0</option>\n";
}

if ( $rewritelocation == 1 )
{
	print "<option value=\"1\" selected=\"selected\">$type1</option>\n";
}
else
{
	print "<option value=\"1\">$type1</option>\n";
}

if ( $rewritelocation == 2 )
{
	print "<option value=\"2\" selected=\"selected\">$type2</option>\n";
}
else
{
	print "<option value=\"2\">$type2</option>\n";
}

print "</select> \n";
print "</div>\n";
print "</div>\n";

##########################################
# ACEPTED VERBS
##########################################
my $type0    = "standard HTTP request";
my $type1    = "+ extended HTTP request";
my $type2    = "+ standard WebDAV verbs";
my $type3    = "+ MS extensions WebDAV verbs";
my $type4    = "+ MS RPC extensions verbs";
my $httpverb = &getFarmHttpVerb( $farmname );

print "<div class=\"form-row\">\n";
print "<p class=\"form-label\"><b>HTTP verbs accepted</b></p>\n";
print
  "<div class=\"form-item\"><select name=\"httpverb\" class=\"fixedwidth\">\n";

if ( $httpverb == 0 )
{
	print "<option value=\"0\" selected=\"selected\">$type0</option>\n";
}
else
{
	print "<option value=\"0\">$type0</option>\n";
}
if ( $httpverb == 1 )
{
	print "<option value=\"1\" selected=\"selected\">$type1</option>\n";
}
else
{
	print "<option value=\"1\">$type1</option>\n";
}
if ( $httpverb == 2 )
{
	print "<option value=\"2\" selected=\"selected\">$type2</option>\n";
}
else
{
	print "<option value=\"2\">$type2</option>\n";
}
if ( $httpverb == 3 )
{
	print "<option value=\"3\" selected=\"selected\">$type3</option>\n";
}
else
{
	print "<option value=\"3\">$type3</option>\n";
}
if ( $httpverb == 4 )
{
	print "<option value=\"4\" selected=\"selected\">$type4</option>\n";
}
else
{
	print "<option value=\"4\">$type4</option>\n";
}
print "</select> \n";
print "</div>\n";
print "</div>\n";

##########################################
# FARM LISTENER
##########################################

#farm listener HTTP or HTTPS
my $type = &getFarmType( $farmname );
print "</div><div class=\"grid_6\">\n";

print "<div class=\"form-row\">\n";
print "<p class=\"form-label\"><b>Farm listener</b></p>\n";
print
  "<div class=\"form-item\"><select name=\"farmlisten\" class=\"fixedwidth\">\n";

if ( $type eq "http" )
{
	print "<option value=\"http\" selected=\"selected\">HTTP</option>\n";
}
else
{
	print "<option value=\"http\">HTTP</option>\n";
}

if ( $type eq "https" )
{
	print "<option value=\"https\" selected=\"selected\">HTTPS</option>\n";
}
else
{
	print "<option value=\"https\">HTTPS</option>\n";
}

print "</select> \n";
print "</div>\n";
print "</div>\n";

##########################################
# ERROR MESSAGES
##########################################

##########################################
# ERROR 414 - Request URI too long
##########################################
my @err414 = &getFarmErr( $farmname, "414" );
my $formerr414 = join ( "", @err414 );
chomp ( $formerr414 );
print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Personalized message Error 414 \"Request URI too long\".</b> HTML tags accepted.</p>\n";
print
  "<div class=\"form-item\"><textarea name=\"err414\" class=\"fixedwidth\" cols=\"40\" rows=\"4\">$formerr414</textarea>\n";
print "</div>\n";
print "</div>\n";

##########################################
# ERROR 500 - Internal server error
##########################################
my @err500 = &getFarmErr( $farmname, "500" );
my $formerr500 = join ( "", @err500 );
chomp ( $formerr500 );
print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Personalized message Error 500 \"Internal server error\".</b> HTML tags accepted.</p>";
print
  "<div class=\"form-item\"><textarea name=\"err500\" class=\"fixedwidth\" cols=\"40\" rows=\"4\">$formerr500</textarea>\n";
print "</div>";
print "</div>\n";

##########################################
# ERROR 501 - Method may not be used
##########################################
my @err501 = &getFarmErr( $farmname, "501" );
my $formerr501 = join ( "", @err501 );
chomp ( $formerr501 );
print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Personalized message Error 501 \"Method may not be used\".</b> HTML tags accepted.</p>\n";
print
  "<div class=\"form-item\"><textarea name=\"err501\" class=\"fixedwidth\" cols=\"40\" rows=\"4\">$formerr501</textarea>\n";
print "</div>\n";
print "</div>\n";

##########################################
# ERROR 503 - Service is not available
##########################################
my @err503 = &getFarmErr( $farmname, "503" );
my $formerr503 = join ( "", @err503 );
chomp ( $formerr503 );
print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Personalized message Error 503 \"Service is not available\".</b> HTML tags accepted.</p>\n";
print
  "<div class=\"form-item\"><textarea name=\"err503\" class=\"fixedwidth\" cols=\"40\" rows=\"4\">$formerr503</textarea>\n";
print "</div>\n";
print "</div>\n";

#### Close form for HTTP
my $type = &getFarmType( $farmname );
if ( $type eq "http" )
{
	print "</form>";
}

print "</div>";    #close grid 6 right

##########################################
# HTTPS FARMS
##########################################
my $moreliness      = "false";
my $morelinescipher = "false";

if ( $type eq "https" )
{
	print "<div class=\"grid_12\">\n";
	print "<br>";
	print "<h6>HTTPS Parameters</h6>\n";
	print "<hr></hr>";
	print "<br>";
	print "</div>\n";

	##########################################
	# CIPHERS
	##########################################
	$moreliness = "true";

	my $cipher      = &getFarmCipherSet( $farmname );
	my $cipher_list = &getFarmCipherList( $farmname );

	print "<div class=\"grid_6\">\n";    #div ciphers
	print "<div class=\"form-row\">\n";
	print "<p class=\"form-label\"><b>Ciphers</b></p>\n";
	print
	  "<div class=\"form-item\"><select name=\"ciphers\" class=\"fixedwidth\">\n";

	if ( $cipher eq "cipherglobal" )
	{
		print "<option value=\"cipherglobal\" selected=\"selected\">All</option>\n";
	}
	else
	{
		print "<option value=\"cipherglobal\">All</option>\n";
	}
	if ( $cipher eq "cipherpci" )
	{
		print
		  "<option value=\"cipherpci\" selected=\"selected\">HIGH security</option>\n";
	}
	else
	{
		print "<option value=\"cipherpci\">HIGH security</option>\n";
	}
	if ( $cipher eq 'ciphercustom' )
	{
		print
		  "<option value=\"ciphercustom\" selected=\"selected\">Custom security</option>\n";
		$morelinescipher = "true";
	}
	else
	{
		print "<option value=\"ciphercustom\">Custom security</option>\n";
	}
	print "</select> \n";
	print "</div>\n";
	print "</div>\n";

	##########################################
	# CUSTOMIZE YOUR CIPHERS
	##########################################
	if ( $cipher eq 'ciphercustom' )
	{
		print "<div class=\"form-row\">\n";
		print "<p class=\"form-label\"><b>Customize your ciphers</b></p>\n";
		print
		  "<div class=\"form-item\"><input type=\"text\" class=\"fixedwidth\" value=\"$cipher_list\" size=\"50\" name=\"cipherc\">\n";
		print "</div>\n";
		print "</div>\n";
	}

	print "</form>\n";    #close form Modify Parameters
	print "</div>\n";     #close div ciphers

	####################################
	# MANAGE CERTIFICATES HTTPS
	####################################

	print "<div class=\"grid_6\">\n";    #div certificates

	print "<div class=\"form-row\">\n";
	print "<p class=\"form-label\"><b>HTTPS certificates availables</b></p>\n";
	print
	  "<form method=\"post\" action=\"index.cgi?id=$id&action=editfarm-httpscert&farmname=$farmname\">\n";
	print "<input type=\"hidden\" name=\"action\" value=\"editfarm-httpscert\">\n";
	print "<input type=\"hidden\" name=\"id\" value=\"$id\">\n";
	print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">\n";
	@certnames = &getFarmCertificatesSNI( $farmname );
	print
	  "<div class=\"form-item\"><select name=\"certname\" class=\"fixedwidth\" >\n";
	opendir ( DIR, $configdir );
	@files = grep ( /.*\.pem$/, readdir ( DIR ) );
	closedir ( DIR );
	print "<option value=\"\">--Add Certificate to SNI list--</option>\n";

	foreach $filecert ( @files )
	{
		print "<option value=\"$filecert\">CN: "
		  . &getCertCN( "$configdir/$filecert" )
		  . " , File: $filecert</option>\n";
	}
	print "</select> \n";
	print
	  "<input type=\"submit\" value=\"Add\" name=\"buttom\" class=\"button mdf\"></div>\n";
	print "</form>\n";
	print "</div>\n";

	my $i       = 0;
	my $default = "(Default)";

	##########################################
	# SNI LIST
	##########################################

	print "<div class=\"form-row\">\n";
	print "<p class=\"form-label\"><b>SNI list</b></p>\n";
	print
	  "<form method=\"post\" action=\"index.cgi?id=$id&action=editfarm-deletecert&farmname=$farmname\">\n";
	print "<input type=\"hidden\" name=\"action\" value=\"editfarm-deletecert\">\n";
	print "<input type=\"hidden\" name=\"id\" value=\"$id\">\n";
	print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">\n";
	print
	  "<div class=\"form-item\"><select name=\"certname\" size=\"4\" class=\"fixedwidth\">\n";

	foreach my $certname ( @certnames )
	{
		$i++;
		$certid = $i;
		print "<option value=\"$certid\">$default $certid: "
		  . &getCertCN( "$configdir/$certname" )
		  . " , File: $certname</option>\n";
		$default = "";
	}
	print "</select> \n";
	print
	  "<input type=\"submit\" value=\"Delete\" name=\"buttom\" class=\"button mdf\"></div>\n";
	print "</form>\n";
	print "</div>\n";

	print "</div>";    #close div certificates
}
print "<div class=\"clear\"></div>\n";
print
  "<input type=\"button\" value=\"Modify\" onClick=\"jQuery('#modify-param').submit()\" class=\"button grey\">\n"
  ;                    # button Modify

print "</div>";
print "</div>";

##########################################
# HTTPS FARM END
##########################################

##########################################
# ADD SERVICES
##########################################

print "
    <div class=\"box grid_6\">
      <div class=\"box-head\">
           <span class=\"box-icon-24 fugue-24 plus\"></span>     
        <h2>Add service</h2>
      </div>
      <div class=\"box-content global-farm\">
";

print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Add new service. </b> Manage virtual host, url, redirect, persistence and backends.</p>\n";
print "<form method=\"post\" action=\"index.cgi\">\n";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"action\" value=\"editfarm-addservice\">\n";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">\n";

print
  "<div class=\"form-item\"><input type=\"text\" class=\"fixedwidth\" value=\"\" size=\"25\" name=\"service\"> \n";
print "</div>\n";
print "</div>\n";
print "<br>";
print
  "<input type=\"submit\" value=\"Add\" name=\"buttom\" class=\"button grey\"></div>\n";
print "</form>\n";
print "</div>\n";

print "<div class=\"clear\"></div>";

##########################################
# SERVICE PARAMETERS
##########################################

$service = $farmname;
if ( $sv ne "" )
{
	print "<a name=\"backendlist-$sv\"></a>";
}

#ZWACL-INI
open FR, "<$configdir\/$file";
my @file    = <FR>;
my $first   = 0;
my $vserver = -1;
my $pos     = 0;
$id_serverr = $id_server;
my $nService = 0;

foreach $line ( @file )
{

	if ( $line !~ /Service "$service"/ && $line =~ /\tService\ \"/ )
	{
		if ( $first eq 1 )
		{
			print "</div></div>\n";
		}

		$pos++;
		$first   = 1;
		$vserver = 0;
		@line    = split ( "\"", $line );
		$sv      = @line[1];
		$service = $sv;
		print "<div class=\"box grid_12\">\n";
		print "<div class=\"box-head\">\n";
		print "<span class=\"box-icon-24 fugue-24 monitor\"></span>\n";
		print "<h2 style=\"float: left; padding-left: 0px; padding-right: 0px;\">";
		&createmenuservice( $farmname, $sv, $pos );
		print "</h2><h2>";
		print "Service \"@line[1]\"</h2>\n";
		print "</div>\n";
		print "<div class=\"box-content global-farm\">\n";
		print "<div class=\"grid_6\">\n";
	}

	if ( $first == 1 && $line =~ /^\tService\ */ )
	{
		if ( $vserver == 0 )
		{
			#
			# Virtual Server
			#
			my $vser = &getFarmVS( $farmname, $sv, "vs" );

			print "<div class=\"form-row\">\n";
			print "<form method=\"post\" action=\"index.cgi\">\n";
			print "<input type=\"hidden\" name=\"action\" value=\"editfarm-Service\">\n";
			print "<input type=\"hidden\" name=\"id\" value=\"$id\">\n";
			print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">\n";
			print "<input type=\"hidden\" name=\"service\" value=\"$sv\">\n";
			print
			  "<p class=\"form-label\"><b>Virtual Host.</b> Empty value disabled.</p>\n";
			print
			  "<div class=\"form-item\"><input type=\"text\" class=\"fixedwidth\" size=\"60\" name=\"vser\" value=\"$vser\"></div>\n";
			print "</div>\n";

			#
			# URL
			#

			my $urlp = &getFarmVS( $farmname, $sv, "urlp" );

			print "<div class=\"form-row\">\n";
			print "<p class=\"form-label\"><b>Url pattern.</b> Empty value disabled.</p>\n";
			print
			  "<div class=\"form-item\"><input type=\"text\" class=\"fixedwidth\" size=\"60\" name=\"urlp\" value=\"$urlp\"></div>\n";
			print "</div>\n";

			#
			# Redirect
			#

			my $redirect     = &getFarmVS( $farmname, $sv, "redirect" );
			my $redirecttype = &getFarmVS( $farmname, $sv, "redirecttype" );
			print "<div class=\"form-row\">\n";
			print
			  "<p class=\"form-label\"><b>Redirect Value.</b> Empty value disabled.</p>";
			print
			  "<div class=\"form-item\"><input type=\"text\" class=\"fixedwidth\" size=\"60\" name=\"redirect\" value=\"$redirect\"></div>";
			print "<p class=\"form-label\"><b>Redirect Type.</b></p>";
			print
			  "<div class\"form-item\"><select name=\"redirecttype\" class=\"fixedwidth\">\n";

			if ( $redirecttype eq "default" )
			{
				print "<option value=\"default\" selected>Default</option>\n";
			}
			else
			{
				print "<option value=\"default\">Default</option>\n";
			}
			if ( $redirecttype eq "append" )
			{
				print "<option value=\"append\" selected>Append</option>\n";
			}
			else
			{
				print "<option value=\"append\">Append</option>\n";
			}
			print "</select></div>";
			print "<p class=\"form-label\"></p>";
			print "</div>\n";

			#
			# DynScale
			#

			my $dyns = &getFarmVS( $farmname, $sv, "dynscale" );

			print "<div class=\"form-row\">\n";
			print "<p class=\"form-label\"><b>Least response</b></p>\n";

			print "<div class=\"form-item mycheckbox\">\n";
			if ( $dyns eq "true" )
			{
				print "<input type=\"checkbox\" checked name=\"dynscale\">\n";
			}
			else
			{
				print "<input type=\"checkbox\" name=\"dynscale\">\n";
			}

			print "</div>\n";
			print "</div>\n";

			#
			# HTTPS Backends
			#

			my $httpsbe = &getFarmVS( $farmname, $sv, "httpsbackend" );

			print "<div class=\"form-row\">\n";
			print "<p class=\"form-label\"><b>HTTPS Backends</b></p>\n";
			print "<div class=\"form-item mycheckbox\">\n";
			if ( $httpsbe eq "true" )
			{
				print "<input type=\"checkbox\" checked name=\"httpsbackend\">\n";
			}
			else
			{
				print "<input type=\"checkbox\" name=\"httpsbackend\">\n";
			}

			print "</div>\n";
			print "</div>\n";

			print "</div><div class=\"grid_6\">\n";

			#
			# Cookie Insertion
			#

			my $cookiei = &getFarmVS( $farmname, $sv, "cookieins" );

			print "<br>\n";
			print "<div class=\"form-row\">\n";
			print "<p class=\"form-label\"><b>Cookie insertion.</b></p>";
			print "<div class=\"form-item mycheckbox\">\n";
			if ( $cookiei eq "true" )
			{
				print "<input type=\"checkbox\" checked name=\"cookieins\">";
			}
			else
			{
				print "<input type=\"checkbox\"  name=\"cookieins\">";
			}
			print "</div>";
			print "</div>\n";

			#
			# Cookie insertion definition
			#

			if ( $cookiei eq "true" )
			{
				print "<br>";
				$cookieinsname = &getFarmVS( $farmname, $sv, "cookieins-name" );
				$domainname    = &getFarmVS( $farmname, $sv, "cookieins-domain" );
				$path          = &getFarmVS( $farmname, $sv, "cookieins-path" );
				$ttlc          = &getFarmVS( $farmname, $sv, "cookieins-ttlc" );

				print "<div class=\"form-row\">\n";
				print
				  "<p class=\"form-label\"><b>Cookie Name:</b></p> <div class=\"form-item\"><input type=\"text\" class=\"fixedwidth\" name=\"cookieinsname\" value=\"$cookieinsname\"> </div>";
				print
				  "<p class=\"form-label\"><b>Domain:</b></p> <div class=\"form-item\"><input type=\"text\" class=\"fixedwidth\" name=\"domainname\" value=\"$domainname\"> </div>";
				print
				  "<p class=\"form-label\"><b>Path:</b></p> <div class=\"form-item\"><input type=\"text\" class=\"fixedwidth\"  name=\"path\" value=\"$path\"></div>";
				print
				  "<p class=\"form-label\"><b>TTL:</b>(In seconds. 0 until the browser closes)</p> <div class=\"form-item\"><input type=\"number\"  class=\"fixedwidth\"  name=\"ttlc\" value=\"$ttlc\"> ";
				print "</div>";
				print "</div>";
			}

			#
			# Session type
			#

			my $session = &getFarmVS( $farmname, $sv, "sesstype" );
			if ( $session =~ /^$/ )
			{
				$session = "nothing";
			}

			print "<div class=\"form-row\">\n";
			print "<p class=\"form-label\"><b>Persistence session</b></p>\n";
			print
			  "<div class=\"form-item\"><select name=\"session\" class=\"fixedwidth\">\n";
			print "<option value=\"nothing\">no persistence</option>\n";

			if ( $session eq "IP" )
			{
				print
				  "<option value=\"IP\" selected=\"selected\">IP: client address</option>\n";
			}
			else
			{
				print "<option value=\"IP\">IP: client address</option>\n";
			}

			if ( $session eq "BASIC" )
			{
				print
				  "<option value=\"BASIC\" selected=\"selected\">BASIC: basic authentication</option>\n";
			}
			else
			{
				print "<option value=\"BASIC\">BASIC: basic authentication</option>\n";
			}

			if ( $session eq "URL" )
			{
				print
				  "<option value=\"URL\" selected=\"selected\">URL: a request parameter</option>\n";
			}
			else
			{
				print "<option value=\"URL\">URL: a request parameter</option>\n";
			}

			if ( $session eq "PARM" )
			{
				print
				  "<option value=\"PARM\" selected=\"selected\">PARM: a  URI parameter</option>\n";
			}
			else
			{
				print "<option value=\"PARM\">PARM: a URI parameter</option>\n";
			}

			if ( $session eq "COOKIE" )
			{
				print
				  "<option value=\"COOKIE\" selected=\"selected\">COOKIE: a certain cookie</option>\n";
			}
			else
			{
				print "<option value=\"COOKIE\">COOKIE: a certain cookie</option>\n";
			}

			if ( $session eq "HEADER" )
			{
				print
				  "<option value=\"HEADER\" selected=\"selected\">HEADER: A certains request header</option>\n";
			}
			else
			{
				print "<option value=\"HEADER\">HEADER: A certains request header</option>\n";
			}
			print "</select> ";
			print "</div>\n";
			print "</div>\n";

			#
			# Session TTL
			#

			if ( $session ne "nothing" && $session )
			{
				my $ttl = &getFarmVS( $farmname, $sv, "ttl" );

				print "<div class=\"form-row\">\n";
				print "<p class=\"form-label\"><b>Persistence session time to limit</b></p>";
				print
				  "<div class=\"form-item\"><input type=\"number\" class=\"fixedwidth\" value=\"$ttl\" size=\"4\" name=\"ttlserv\"> ";
				print "</div>";
				print "</div>\n";
			}

			#
			# Session ID
			#

			$morelines = "false";
			if ( $session eq "URL" || $session eq "COOKIE" || $session eq "HEADER" )
			{
				my $sessionid = &getFarmVS( $farmname, $sv, "sessionid" );

				print "<div class=\"form-row\">\n";
				print
				  "<p class=\"form-label\"><b>Persistence session identifier.</b> A cookie name, a header name or url value name.</p>\n";
				print
				  "<div class=\"form-item\"><input type=\"text\" class=\"fixedwidth\" value=\"$sessionid\" size=\"20\" name=\"sessionid\"></div>\n";
				print "</div>\n";
				$morelines = "true";
			}

			print "</div><div class=\"grid_12\">\n";
			print "<br><br>";
			print "<h6>Farm Guardian</h6>\n";
			print "<hr></hr>";
			print "</div><div class=\"grid_6\">\n";    #div left

			#
			# FarmGuardian
			#

			my @fgconfig  = &getFarmGuardianConf( $farmname, $sv );
			my $fgttcheck = @fgconfig[1];
			my $fgscript  = @fgconfig[2];
			$fgscript =~ s/\n//g;
			$fgscript =~ s/\"/\'/g;
			my $fguse = @fgconfig[3];
			$fguse =~ s/\n//g;
			my $fglog = @fgconfig[4];
			if ( !$fgttcheck ) { $fgttcheck = 5; }

			print "<div class=\"form-row\">\n";
			print
			  "<p class=\"form-label\"><b>Use FarmGuardian to check Backend Servers</b></p>";
			print "<div class=\"form-item mycheckbox\">\n";

			# Enable FarmGuardian
			if ( $fguse eq "true" )
			{
				print "<input type=\"checkbox\" checked name=\"usefarmguardian\">";
			}
			else
			{
				print "<input type=\"checkbox\" name=\"usefarmguardian\">";
			}
			print "</div>\n";
			print "</div>\n";
			print "<br>";

			# Enable FarmGuardian logs
			print "<div class=\"form-row\">\n";
			print "<p class=\"form-label\"><b>Enable farmguardian logs</b></p>";
			print "<div class=\"form-item mycheckbox\">\n";

			if ( $fglog eq "true" )
			{
				print "<input type=\"checkbox\" checked name=\"farmguardianlog\">";
			}
			else
			{
				print "<input type=\"checkbox\" name=\"farmguardianlog\">";
			}

			print "</div>\n";
			print "</div>\n";
			print "</div>\n";    #close div left

			print "<div class=\"grid_6\">\n";    #div right

			# Check interval
			print "<div class=\"form-row\">\n";
			print
			  "<p class=\"form-label\"><b>Check interval.</b> Time between checks in seconds.</p>\n";
			print
			  "<div class=\"form-item\"><input type=\"number\" class=\"fixedwidth\" value=\"$fgttcheck\" size=\"1\" name=\"timetocheck\"> ";
			print "</div>\n";
			print "</div>\n";

			# Command to check
			print "<div class=\"form-row\">\n";
			print "<p class=\"form-label\"><b>Command to check</b></p>\n";
			print
			  "<div class=\"form-item\"><input type=\"text\" class=\"fixedwidth\" value=\"$fgscript\" size=\"60\" name=\"check_script\"> ";
			print "</div>\n";
			print "</div>\n";

			$vserver = 1;
		}

		print "</div>";    #close div right
		print "<div class=\"clear\"></div>";
		print "<br>";
		print
		  " <input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button grey\">";

		print "</form>\n";

		print " 
		<div style=\"float:right\">
			<div>
				<p>Warning: This action will restart the farm.</p>
			</div>
			<div>
		";

		# button to move the service up if this service it isn't the first
		print "
		<div class=\"botonMove\">
			<form action=\"index.cgi\" method=\"post\">
				<input type=\"hidden\" name=\"action\" value=\"editfarm-moveservice\"/>
				<input type=\"hidden\" name=\"farmname\" value=\"$farmname\"/>
				<input type=\"hidden\" name=\"service\" value=\"$service\"/>
				<input type=\"hidden\" name=\"id\" value=\"$id\"/>";

		if ( $nService != 0 )
		{
			print
			  "<input type=\"submit\" value=\"Move up\" name=\"moveservice\" class=\"button grey\">";
		}

		if ( $nService + 1 != scalar &getFarmServices( $farmname ) )
		{
			print
			  "<input type=\"submit\" value=\"Move down\" name=\"moveservice\" class=\"button grey\">";
		}

		print "</form>
		</div>
		";

		$nService += 1;

		print " </div>";
		print "</div></div></div>";

		#
		# Service Backends
		#

		$vserver = 0;
		print "
			<div class=\"box grid_12\">
				<div class=\"box-head\">
				<span class=\"box-icon-24 fugue-24 server\"></span>       
				<h2>Backends for service '$sv'</h2>
				</div>
				<div class=\"box-content no-pad\">
				<table class=\"display\">";
		print
		  "<thead><tr><th>Server</th><th>Address</th><th>Port</th><th>Timeout</th><th>Weight</th><th>Actions</th></tr></thead><tbody>";

		#search backends for this service
		#getBackends for this service
		my $backendsvs = &getFarmVS( $farmname, $sv, "backends" );
		my @be = split ( "\n", $backendsvs );
		my $rowcounter = 1;
		foreach $subline ( @be )
		{
			my @subbe = split ( "\ ", $subline );

			if (    $id_serverr == @subbe[1]
				 && $service eq "$actualservice"
				 && $action eq "editfarm-editserver" )
			{
				print "<form method=\"post\" class=\"myform\" action=\"index.cgi\">"
				  ;    #This form ends in createmenuserverfarm
				print "<tr class=\"selected\">";
				print "<td>@subbe[1]</td>";
				print
				  "<td><input type=\"text\" size=\"12\"  name=\"rip_server\" value=\"@subbe[3]\"> </td>";
				print
				  "<td><input type=\"number\" size=\"4\" name=\"port_server\" value=\"@subbe[5]\"> </td>";
				if ( @subbe[7] eq "-" ) { @subbe[7] =~ s/-//; }
				print
				  "<td><input type=\"number\" size=\"4\" name=\"timeout_server\" value=\"@subbe[7]\"> </td>";
				if ( @subbe[9] eq "-" ) { @subbe[9] =~ s/-//; }
				print
				  "<td><input type=\"number\" size=\"4\" name=\"priority_server\" value=\"@subbe[9]\"> </td>";
				$nserv = @subbe[1];

				print "<input type=\"hidden\" name=\"service\" value=\"$sv\">";
				&createmenuserversfarm( "edit", $farmname, $nserv );
			}
			else
			{
				if ( $rowcounter % 2 == 0 )
				{
					print "<tr class=\"even\">";
				}
				else
				{
					print "<tr class=\"odd\">";
				}
				$rowcounter++;

				print "<td>@subbe[1]</td>";
				print "<td>@subbe[3]</td>";
				print "<td>@subbe[5]</td>";
				print "<td>@subbe[7]</td>";
				print "<td>@subbe[9]</td>";

				$nserv = @subbe[1];
				&createmenuserversfarm( "normal", $farmname, $nserv );
				print "</tr>";
			}

		}

		print "<a name=\"backendlist-$sv\"></a>";

		#add new server to  server pool
		print "\n\n\n";
		if ( $action eq "editfarm-addserver" && $service eq "$actualservice" )
		{
			if ( ( $action eq "editfarm-editserver" || $action eq "editfarm-addserver" )
				 && $service eq "$actualservice" )
			{
				print "<form method=\"post\" class=\"myform\" action=\"index.cgi\">"
				  ;    #This form ends in createmenuserverfarm
			}

			print "<tr class=\"selected\">";

			#id server
			print "<td>-</td>";
			print "<input type=\"hidden\" name=\"id_server\" value=\"\">";

			#real server ip
			print
			  "<td><input type=\"text\" size=\"12\"  name=\"rip_server\" value=\"$rip_server\"> </td>";

			#port
			print
			  "<td><input type=\"number\" size=\"4\"  name=\"port_server\" value=\"$port_server\"> </td>";

			#timeout
			print
			  "<td><input type=\"number\" size=\"4\"  name=\"timeout_server\" value=\"$timeout_server\"> </td>";

			#Priority
			print
			  "<td><input type=\"number\" size=\"4\"  name=\"priority_server\" value=\"$priority_server\"> </td>";

			print "<input type=\"hidden\" name=\"service\" value=\"$sv\">";
			&createmenuserversfarm( "add", $farmname, @l_serv[0] );

			print "</tr>";
		}

		print "\n\n\n";
		print "<tr><td class='gray' colspan=\"5\"></td>";

		&createmenuserversfarm( "new", $farmname, @l_serv[0] );

		print "</tr>";
		print "</tbody></table>";
	}

	if ( $line =~ /Service "$farmname"/ )
	{
		$service = $farmname;
		break;
	}

	if ( $vserver == 0 && $first == 1 )
	{
	}

}

# If there are services
if ( $pos gt 0 )
{
	print "</div></div>";
}

close FR;

#ZWACL-END

###############################################
#JUMP BACKEND SECTION
goto BACKENDS;
##############################################

print "<br><br>";
print "<div class=\"box-header\">Edit real IP servers configuration</div>";

print "<div class=\"box table\">  <table cellspacing=\"0\">";

#header table
print
  "<thead><tr><td>Server</td><td>Address</td><td>Port</td><td>Timeout</td><td>Weight</td><td>Actions</td></tr></thead><tbody>";
#
tie my @contents, 'Tie::File', "$configdir\/$file";
$nserv      = -1;
$index      = -1;
$be_section = 0;
$to_sw      = 0;
$prio_sw    = 0;

$id_serverr = $id_server;
foreach my $line ( @contents )
{
	$index++;
	if ( $line =~ /#BackEnd/ )
	{
		$be_section = 1;
	}
	if ( $be_section == 1 )
	{
		if ( $line =~ /Address/ )
		{
			$nserv++;
			@ip = split ( /\ /, $line );
			chomp ( @ip[1] );
		}
		if ( $line =~ /Port/ )
		{
			@port = split ( /\ /, $line );
			chomp ( @port );
		}
		if ( $line =~ /TimeOut/ )
		{
			@timeout = split ( /\ /, $line );
			chomp ( @timeout );
			$to_sw = 1;
		}
		if ( $line =~ /Priority/ )
		{
			@priority = split ( /\ /, $line );
			chomp ( @priority );
			$po_sw = 1;
		}
		if ( $line !~ /\#/ && $line =~ /End/ && $line !~ /Back/ )
		{
			if ( $id_serverr == $nserv && $action eq "editfarm-editserver" )
			{
				print "<form method=\"post\" action=\"index.cgi\#backendlist-$sv\">";
				print "<tr class=\"selected\">";
				print "<td>$nserv</td>";
				print
				  "<td><input type=\"text\" size=\"12\"  name=\"rip_server\" value=\"@ip[1]\"> </td>";
				print
				  "<td><input type=\"text\" size=\"4\" name=\"port_server\" value=\"@port[1]\"> </td>";
				print
				  "<td><input type=\"text\" size=\"4\" name=\"timeout_server\" value=\"@timeout[1]\"> </td>";
				print
				  "<td><input type=\"text\" size=\"4\" name=\"priority_server\" value=\"@priority[1]\"> </td>";
				&createmenuserversfarm( "edit", $farmname, $nserv );
				print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
				print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
				print "<input type=\"hidden\" name=\"id_server\" value=\"$nserv\">";
				print "<input type=\"hidden\" name=\"service\" value=\"$service\">";
				print "</form>";
			}
			else
			{
				print "<tr>";
				print "<form method=\"post\" action=\"index.cgi\#backendlist-$sv\">";
				print "<td>$nserv</td>";
				print "<td>@ip[1]</td>";
				print "<td>@port[1]</td>";
				if ( $to_sw == 0 )
				{
					print "<td>-</td>";
				}
				else
				{
					print "<td>@timeout[1]</td>";
					$to_sw = 0;
				}
				if ( $po_sw == 0 )
				{
					print "<td>-</td>";
				}
				else
				{
					print "<td>@priority[1]</td>";
					$po_sw = 0;
				}

				&createmenuserversfarm( "normal", $farmname, $nserv );
				print "</tr>";
				print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
				print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
				print "<input type=\"hidden\" name=\"id_server\" value=\"$nserv\">";
				print "<input type=\"hidden\" name=\"service\" value=\"$service\">";
				print "</form>";
				undef @timeout;
				undef @priority;
			}
		}
	}
	if ( $be_section == 1 && $line =~ /#End/ )
	{
		$be_section = 0;
	}
}
untie @contents;

#content table
if ( $action eq "editfarm-addserver" && $actualservice eq $service )
{
	#add new server to  server pool
	$action = "editfarm";
	$isrs   = "true";
	print "<form method=\"post\" action=\"index.cgi\#backendlist-$sv\">";
	print "<tr class=\"selected\">";

	#id server
	print "<td>-</td>";
	print "<input type=\"hidden\" name=\"id_server\" value=\"\">";

	#real server ip
	print
	  "<td><input type=\"text\" size=\"12\"  name=\"rip_server\" value=\"$rip_server\"> </td>";

	#port
	print
	  "<td><input type=\"text\" size=\"4\"  name=\"port_server\" value=\"$port_server\"> </td>";

	#timeout
	print
	  "<td><input type=\"text\" class=\"fixedwidth\" size=\"4\"  name=\"timeout_server\" value=\"$timeout_server\"> </td>";

	#Priority
	print
	  "<td><input type=\"text\" class=\"fixedwidth\" size=\"4\"  name=\"priority_server\" value=\"$priority_server\"> </td>";
	&createmenuserversfarm( "add", $farmname, $l_serv[0] );
	print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
	print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
	print "<input type=\"hidden\" name=\"service\" value=\"$service\">";

	print "</form>";
	print "</tr>";
}

print "<tr><td colspan=\"5\"></td>";
print "<form method=\"post\" action=\"index.cgi\#backendlist-$sv\">";
&createmenuserversfarm( "new", $farmname, $l_serv[0] );
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<input type=\"hidden\" name=\"id_server\" value=\"$l_serv[0]\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<input type=\"hidden\" name=\"service\" value=\"$service\">";
print "</form>";

print "</tr>";

print "</tbody></table>";
print "<div style=\"clear:both;\"></div>";
print "</div>";

#end table

# If there are services
if ( $pos gt 0 )
{
	print "</div></div>";
}


#################################################################
BACKENDS:
##################################################################

1;
