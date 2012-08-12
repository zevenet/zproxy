#This cgi is part of Zen Load Balancer, is a Web GUI integrated with binary systems that
#create Highly Effective Bandwidth Managemen
#Copyright (C) 2010  Emilio Campos Martin / Laura Garcia Liebana
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You can read license.txt file for more information.

#Created by Emilio Campos Martin
#File that create the Zen Load Balancer GUI

### EDIT HTTP/HTTPS FARM ###
#maintenance mode for servers



if ($action eq "editfarm-maintenance"){
        &setFarmBackendMaintenance($farmname,$id_server);
        if ($? eq 0){
                &successmsg("Enabled maintenance mode for backend $id_server");
        }

}
#disable maintenance mode for servers
if ($action eq "editfarm-nomaintenance"){
        &setFarmBackendNoMaintenance($farmname,$id_server);
        if ($? eq 0){
                &successmsg("Disabled maintenance mode for backend");
        }

}




#manage ciphers
if ($action eq "editfarm-httpsciphers"){
	if ($ciphers eq "cipherglobal"){
		&setFarmCiphers($farmname,$ciphers);	
                &successmsg("Ciphers changed for farm $farmname");
                &setFarmRestart($farmname);
	}
	if ($ciphers eq "cipherpci"){
		&setFarmCiphers($farmname,$ciphers);	
                &successmsg("Ciphers changed for farm $farmname");
                &setFarmRestart($farmname);
	}
	if ($ciphers eq "ciphercustom"){
		&setFarmCiphers($farmname,$ciphers);	
	}

}

if ($action eq "editfarm-httpscipherscustom"){
	$cipherc =~ s/\ //g;
	if ($cipherc eq ""){
		&errormsg("Ciphers can't be blank");
	}else{
		&setFarmCiphers($farmname,"",$cipherc);	
                &successmsg("Ciphers changed for farm $farmname");
                &setFarmRestart($farmname);
		
	}
}

#change Farm's name

if ($action eq "editfarm-Name"){
	#Check the farm's name change
	if ("$newfarmname" eq "$farmname"){
		&errormsg("The new farm's name \"$newfarmname\" is the same as the old farm's name \"$farmname\": nothing to do");
	}
	else{
		#Check if the new farm's name alredy exists
		$newffile = &getFarmFile($newfarmname);
		if ($newffile != -1){
			&errormsg("The farm $newfarmname already exists, try another name");
		}
		else{
			#Stop farm 
		        $oldfstat = &runFarmStop($farmname,"true");
        		if ($oldfstat == 0){
                		&successmsg("The Farm $farmname is now disabled");
        		} 
			else{
                		&errormsg("The Farm $farmname is not disabled, are you sure it's running?");
        		}
			#Change farm name
			$fnchange = &setNewFarmName($farmname,$newfarmname);
			if ($fnchange != -1){
				&successmsg("The Farm $farmname can be renamed to $newfarmname");
				$farmname=$newfarmname;
				$file = &getFarmFile($newfarmname);
				#Start farm
				$newfstat = &runFarmStart($farmname,"true");
	        		if ($newfstat == 0){
	                		&successmsg("The Farm $farmname is now running");
	        		} 
				else{
			                &errormsg("The Farm $farmname isn't running, check if the IP address is up and the PORT is in use");
	        		}

			}
			else{
				&errormsg("The name of the Farm $farmname can't be modified, delete the farm and create a new one.");
			}

		}
	}
	$action="editfarm";
}

if ($action eq "editfarm-changevipvipp"){
        if ( &isnumber($vipp) eq "false"){
                &errormsg("Invalid Virtual Port $vipp value, it must be a numeric value");
                $error = 1;
        }
        if (&checkport($vip,$vipp) eq "true"){
                &errormsg("Virtual Port $vipp in Virtual IP $vip is in use, select another port");
                $error = 1;
        }
        if ($error == 0){
                $status = &setFarmVirtualConf($vip,$vipp,$farmname);
                if ($status != -1){
                	&setFarmRestart($farmname);
                        &successmsg("Virtual IP and Virtual Port has been modified, the $farmname farm need be restarted");
                } else {
                        &errormsg("It's not possible to change the $farmname farm virtual IP and port");
                }
        }
}


if ($action eq "editfarm-httpscert"){
	$status = &setFarmCertificate($certname,$farmname);
	if ($status == 0){
		&setFarmRestart($farmname);
		&successmsg("Certificate is changed to $certname on farm $farmname, you need restart the farm to apply");
	} else {
		&errormsg("It's not possible to change the certificate for the $farmname farm");
	}
}


if ($action eq "editfarm-restart"){
	&runFarmStop($farmname,"true");
	$status = &runFarmStart($farmname,"true");
	if ($status == 0){
		&successmsg("The $farmname farm has been restarted");
		&setFarmHttpBackendStatus($farmname);
	} else {
		&errormsg("The $farmname farm hasn't been restarted");
	}
}

if ($action eq "editfarm-Err414"){
	$status = &setFarmErr($farmname,$err414,"414");
	if ($status == 0){
		&setFarmRestart($farmname);
		&successmsg("The Err414 message for the $farmname farm has been modified");
	} else {
		&errormsg("The Err414 message for the $farmname farm hasn't been modified");
	}
}

#err500
if ($action eq "editfarm-Err500"){
	$status = &setFarmErr($farmname,$err500,"500");
	if ($status == 0){
		&setFarmRestart($farmname);
		&successmsg("The Err500 message for the $farmname farm has been modified");
	} else {
		&errormsg("The Err500 message for the $farmname farm hasn't been modified");
	}
}

#err501
if ($action eq "editfarm-Err501"){
	$status = &setFarmErr($farmname,$err501,"501");
	if ($status == 0){
		&setFarmRestart($farmname);
		&successmsg("The Err501 message for the $farmname farm has been modified");
	} else {
		&errormsg("The Err501 message for the $farmname farm hasn't been modified");
	}
}

#err503
if ($action eq "editfarm-Err503"){
	$status = &setFarmErr($farmname,$err503,"503");
	if ($status == 0){
		&setFarmRestart($farmname);
		&successmsg("The Err503 message for the $farmname farm has been modified");
	} else {
		&errormsg("The Err503 message for the $farmname farm hasn't been modified");
	}
}

#delete server
if ($action eq "editfarm-deleteserver"){
	$status = &runFarmServerDelete($id_server,$farmname);
	if ($status != -1){
		&setFarmRestart($farmname);
		&successmsg("The real server with ID $id_server of the $farmname farm has been deleted");
	} else {
		&errormsg("It's not possible to delete the real server with ID $id_server of the $farmname farm");
	}
}

#save server
if ($action eq "editfarm-saveserver"){
	$error = 0;
	if (&ipisok($rip_server) eq "false"){
		&errormsg("Invalid real server IP value, please insert a valid value");
		$error = 1;
	}
	if ($priority_server  && ($priority_server > 9 || $priority_server < 1)){
		# For HTTP and HTTPS farms the priority field its the weight
		&errormsg("Invalid weight value for a real server, it must be 1-9");
		$error = 1;
	}
	if ($rip_server =~ /^$/ || $port_server =~ /^$/){
		&errormsg("Invalid IP address and port for a real server, it can't be blank");
		$error = 1;
	}

        if ($error == 0){
		$status = &setFarmServer($id_server,$rip_server,$port_server,$max_server,$weight_server,$priority_server,$timeout_server,$farmname);
		if ($status != -1){
			&setFarmRestart($farmname);
			&successmsg("The real server with ID $id_server and IP $rip_server of the $farmname farm has been modified");
		} else {
			&errormsg("It's not possible to modify the real server with ID $id_server and IP $rip_server of the $farmname farm");
		}
	}
}

#actions over farm
if ($action eq "editfarm-Timeout-http"){
	$error = 0;
	if (&isnumber($param) eq "false"){
		&errormsg("Invalid timeout $param value, it must be a numeric value");
		$error = 1;
	}
	if ($error == 0){
		$status = &setFarmTimeout($param,$farmname);
		if ($status != -1){
			&setFarmRestart($farmname);
			&successmsg("The timeout for $farmname farm has been modified");
		} else {
			&errormsg("It's not possible to change the $farmname farm timeout value");
		}
	}
}

if ($action eq "editfarm-Alive"){
	$error = 0;
	if (&isnumber($param) eq "false"){
		&errormsg("Invalid alive time $param value, it must be a numeric value");
		$error = 1;
	}
	if ($error == 0){
		$status = &setFarmBlacklistTime($param,$farmname);
		if ($status != -1){
			&setFarmRestart($farmname);
			&successmsg("The alive time for $farmname farm has been modified");
		} else {
			&errormsg("It's not possible to change the $farmname farm alive time value");
		}
	}
}

if ($action eq "editfarm-httpverb"){
	$status = &setFarmHttpVerb($httpverb,$farmname);
	if ($status == 0){
		&setFarmRestart($farmname);
		&successmsg("The HTTP verb for $farmname farm has been modified");
	} else {
		&errormsg("It's not possible to change the $farmname farm HTTP verb");
	}
}


if ($action eq "editfarm-Client"){
	$error = 0;
	if (&isnumber($param) eq "false"){
		&errormsg("Invalid client timeout $param value, it must be a numeric value");
		$error = 1;
	}
	if ($error == 0){
		$status = &setFarmClientTimeout($param,$farmname);
		if ($status == 0){
			&setFarmRestart($farmname);
			&successmsg("The client timeout for $farmname farm has been modified");
		} else {
			&errormsg("It's not possible to change the $farmname farm client timeout");
		}
	}
}

#TTL
if ($action eq "editfarm-TTL"){
	$error = 0;
	if (&isnumber($param) eq "false"){
		&errormsg("Invalid client timeout $param value, it must be a numeric value");
		$error = 1;
	}
	if ($error == 0){
		$status = &setFarmMaxClientTime(0,$param,$farmname);
		if ($status == 0){
			&setFarmRestart($farmname);
			&successmsg("The sessions TTL for $farmname farm has been modified");
		} else {
			&errormsg("It's not possible to change the $farmname farm sessions TTL");
		}
	}
}

#session ID
if ($action eq "editfarm-sessionid"){
	chomp($param);
	$param =~ s/ //eg;
	$error = 0;
	if ($param eq "" ){
		&errormsg("Invalid session id $param value");
		$error = 1;
	}
	if ($error == 0){
		$status = &setFarmSessionId($param,$farmname);
		if ($status == 0){
			&setFarmRestart($farmname);
			&successmsg("The session id for $farmname farm has been modified");
		} else {
			&errormsg("It's not possible to change the $farmname farm session id");
		}
	}
}

#session type
if ($action eq "editfarm-typesession"){
	$status = &setFarmSessionType($session,$farmname);
	if ($status == 0){
		&setFarmRestart($farmname);
		&successmsg("The session type for $farmname farm has been modified");
	} else {
		&errormsg("It's not possible to change the $farmname farm session type");
	}
}

#check if the farm need a restart
if (-e "/tmp/$farmname.lock"){
	&tipmsg("There're changes that need to be applied, stop and start farm to apply them!");
}

#global info for a farm
print "<div class=\"container_12\">";
print "<div class=\"grid_12\">";

#paint a form to the global configuration
print "<div class=\"box-header\">Edit $farmname Farm global parameters</div>";
print "<div class=\"box stats\">";
print "<div class=\"row\">";

print "<div style=\"float:left;\">";

#Change farm's name form
print "<b>Farm's name</b><font size=1> *service will be restarted</font><b>.</b><br>";
print "<form method=\"get\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"action\" value=\"editfarm-Name\">";
print "<input type=\"text\" value=\"$farmname\" size=\"25\" name=\"newfarmname\">";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<input type=\"hidden\" name=\"done\" value=\"yes\">";
print "<input type=\"hidden\" name=\"id_server\" value=\"@l_serv[0]\">";
print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";
print "<br>";

print "<b>Backend response timeout secs.<br>";
$timeout = &getFarmTimeout($farmname);
print "<form method=\"get\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"action\" value=\"editfarm-Timeout-http\">";
print "<input type=\"text\" value=\"$timeout\" size=\"4\" name=\"param\">";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";
print "<br>";

print "<b>Frequency to check resurrected backends.</b>";
$alive = &getFarmBlacklistTime($farmname);
print "<form method=\"get\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"action\" value=\"editfarm-Alive\">";
print "<input type=\"text\" value=\"$alive\" size=\"4\" name=\"param\">";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";
print "<br>";

#Timeout for client
print "<b>Timeout request from clients.</b>";
$client = &getFarmClientTimeout($farmname);
print "<form method=\"get\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"action\" value=\"editfarm-Client\">";
print "<input type=\"text\" value=\"$client\" size=\"4\" name=\"param\">";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";

#type session
print "<br>";
print "<b>Persistence session.</b>";
$session = &getFarmSessionType($farmname);
if ($session == -1){
	$session = "nothing";
}
print "<form method=\"get\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"action\" value=\"editfarm-typesession\">";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<select  name=\"session\">";
print "<option value=\"nothing\">no persistence</option>";
if ($session eq "IP"){	
	print "<option value=\"IP\" selected=\"selected\">IP: client address</option>";
} else {
	print "<option value=\"IP\">IP: client address</option>";
}
if ($session eq "BASIC"){
	print "<option value=\"BASIC\" selected=\"selected\">BASIC: basic authentication</option>";
} else {
	print "<option value=\"BASIC\">BASIC: basic authentication</option>";
}
if ($session eq "URL"){
	print "<option value=\"URL\" selected=\"selected\">URL: a request parameter</option>";
} else {
	print "<option value=\"URL\">URL: a request parameter</option>";
}
if ($session eq "PARM"){
	print "<option value=\"PARM\" selected=\"selected\">PARM: a  URI parameter</option>";
} else {
	print "<option value=\"PARM\">PARM: a URI parameter</option>";
}
if ($session eq "COOKIE"){
	print "<option value=\"COOKIE\" selected=\"selected\">COOKIE: a certain cookie</option>";
} else {
	print "<option value=\"COOKIE\">COOKIE: a certain cookie</option>";
}
if ($session eq "HEADER"){
	print "<option value=\"HEADER\" selected=\"selected\">HEADER: A certains request header</option>";
} else {
	print "<option value=\"HEADER\">HEADER: A certains request header</option>";
}
print "</select>";
print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";

#session TTL
if ($session ne "nothing" && $session){
	print "<br>";
	print "<b>Persistence session time to limit.</b>";
	@ttl = &getFarmMaxClientTime($farmname);
	print "<form method=\"get\" action=\"index.cgi\">";
	print "<input type=\"hidden\" name=\"action\" value=\"editfarm-TTL\">";
	print "<input type=\"text\" value=\"@ttl[1]\" size=\"4\" name=\"param\">";
	print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
	print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
	print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";
}

#session ID
$morelines = "false";
if ($session eq "URL" || $session eq "COOKIE" || $session eq "HEADER"){
	print "<br>";
	print "<b>Persistence session identifier.</b> <font size=1>*a cookie name, a header name or url value name</font>";
	$sessionid = &getFarmSessionId($farmname);
	print "<form method=\"get\" action=\"index.cgi\">";
	print "<input type=\"hidden\" name=\"action\" value=\"editfarm-sessionid\">";
	print "<input type=\"text\" value=\"$sessionid\" size=\"20\" name=\"param\">";
	print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
	print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
	print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";
	$morelines = "true";
}

#acepted verbs
#
print "<br>";
$type0="standard HTTP request";
$type1="+ extended HTTP request";
$type2="+ standard WebDAV verbs";
$type3="+ MS extensions WebDAV verbs";
$type4="+ MS RPC extensions verbs";
print "<b>HTTP verbs accepted.</b>";
print "<br>";
$httpverb = &getFarmHttpVerb($farmname);
print "<form method=\"get\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"action\" value=\"editfarm-httpverb\">";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<select  name=\"httpverb\">";
if ($httpverb == 0){
	print "<option value=\"0\" selected=\"selected\">$type0</option>";
} else {
	print "<option value=\"0\">$type0</option>";
}
if ($httpverb == 1){
	print "<option value=\"1\" selected=\"selected\">$type1</option>";
} else {
	print "<option value=\"1\">$type1</option>";
}
if ($httpverb == 2){
	print "<option value=\"2\" selected=\"selected\">$type2</option>";
} else {
	print "<option value=\"2\">$type2</option>";
}
if ($httpverb == 3){
	print "<option value=\"3\" selected=\"selected\">$type3</option>";
} else {
	print "<option value=\"3\">$type3</option>";
}
if ($httpverb == 4){
	print "<option value=\"4\" selected=\"selected\">$type4</option>";
} else {
	print "<option value=\"4\">$type4</option>";
}
print "</select>";
print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";

# HTTPS FARMS
$moreliness="false";
$morelinescipher="false";
$type = &getFarmType($farmname);
if ($type eq "https"){
	print "<br>";
	print "<b>HTTPS certificate</b>.<font size=1>*Certificate with pem format is needed</font>";
	print "<br>";
	print "<form method=\"get\" action=\"\">";
	print "<input type=\"hidden\" name=\"action\" value=\"editfarm-httpscert\">";
	print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
	print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
	$certname = &getFarmCertificate($farmname);
	print "<select  name=\"certname\">";
	opendir(DIR, $configdir);
	@files = grep(/.*\.pem$/,readdir(DIR));
	closedir(DIR);
	foreach $filecert(@files){
		if ($certname eq $filecert){
			print "<option value=\"$filecert\" selected=\"selected\">$filecert</option>";
		} else {
			print "<option value=\"$filecert\">$filecert</option>";
		}
	}
	print "</select>";
	print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";
	
	$moreliness="true";

	print "<br>";
	$cipher = &getFarmCipher($farmname);
	print "Ciphers";
	chomp($cipher);
	print "<form method=\"get\" action=\"\">";
        print "<input type=\"hidden\" name=\"action\" value=\"editfarm-httpsciphers\">";
        print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
        print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
	print "<select name=\"ciphers\">\n";
	if ($cipher eq "cipherglobal"){
		print "<option value=\"cipherglobal\" selected=\"selected\">All</option>\n";
	}else{
		print "<option value=\"cipherglobal\">All</option>\n";
	}
	if ($cipher eq "cipherpci"){
		print "<option value=\"cipherpci\" selected=\"selected\">HIGH security / PCI compliance</option>\n";
	}else{
		print "<option value=\"cipherpci\">HIGH security / PCI compliance</option>\n";
	}
	if ($cipher ne "cipherglobal" && $cipher ne "cipherpci"){
		print "<option value=\"ciphercustom\" selected=\"selected\">Custom security</option>\n";
		$morelinescipher="true";
	}else{
		print "<option value=\"ciphercustom\">Custom security</option>\n";
	}
		
	
	print "</select>";
	print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";
	print "<br>";
	if ($cipher ne "cipherpci" && $cipher ne "cipherglobal"){
		print "Customize your ciphers.";
		print "<form method=\"get\" action=\"\">";
		print "<input type=\"hidden\" name=\"action\" value=\"editfarm-httpscipherscustom\">";
	        print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
        	print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
		print " <input type=\"text\" value=\"$cipher\" size=\"50\" name=\"cipherc\">";

		print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";
	}


}
#END HTTPS FARM:


print "<br>";
print "<b>Farm Virtual IP and Virtual port.</b>";
$vip = &getFarmVip("vip",$farmname);
$vport = &getFarmVip("vipp",$farmname);
print "<br>";
@listinterfaces = &listallips();
#print @listinterfaces;
$clrip = &clrip();
print "<form method=\"get\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"action\" value=\"editfarm-changevipvipp\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<select name=\"vip\">";
foreach $ip(@listinterfaces){
	if ($ip !~ $clrip){
		if ($vip eq $ip){
			print "<option value=\"$ip\" selected=\"selected\">$ip</option>";
		} else {
			print "<option value=\"$ip\">$ip</option>";
		}
	}
}
print "</select>";
print " <input type=\"text\" value=\"$vport\" size=\"4\" name=\"vipp\">";
print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";


print "</div><div style=\"align:right; margin-left: 50%; \">";

#Error messages
#Err414
print "<b>Personalized message Error 414 \"Request URI too long\", HTML tags accepted.</b>";
@err414 = &getFarmErr($farmname,"414");
print "<form method=\"post\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"actionpost\" value=\"editfarm-Err414\">";
#print "<input type=\"textarea\" value=\"$err414\" size=\"4\" name=\"param\">";
print "<textarea name=\"err414\" cols=\"40\" rows=\"2\">";
foreach $line(@err414){
	print "$line";
}
print "</textarea>";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";

#Error500
print "<br>";
print "<b>Personalized message Error 500 \"Internal server error\", HTML tags accepted.</b>";
@err500 = &getFarmErr($farmname,"500");
print "<form method=\"post\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"actionpost\" value=\"editfarm-Err500\">";
#print "<input type=\"textarea\" value=\"$err500\" size=\"4\" name=\"param\">";
print "<textarea name=\"err500\" cols=\"40\" rows=\"2\">";
foreach $line(@err500){
	print "$line";
}
print "</textarea>";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";

#Error501
print "<br>";
print "<b>Personalized message Error 501 \"Method may not be used\", HTML tags accepted.</b>";
@err501 = &getFarmErr($farmname,"501");
print "<form method=\"post\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"actionpost\" value=\"editfarm-Err501\">";
#print "<input type=\"textarea\" value=\"$err501\" size=\"4\" name=\"param\">";
print "<textarea name=\"err501\" cols=\"40\" rows=\"2\">";
foreach $line(@err501){
	print "$line";
}
print "</textarea>";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";

#Err503
print "<br>";
print "<b>Personalized message Error 503 \"Service is not available\", HTML tags accepted.</b>";
@err503 = &getFarmErr($farmname,"503");
print "<form method=\"post\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"actionpost\" value=\"editfarm-Err503\">";
#print "<input type=\"textarea\" value=\"$err503\" size=\"4\" name=\"param\">";
print "<textarea name=\"err503\" cols=\"40\" rows=\"2\">";
foreach $line(@err503){
	print "$line";
}
print "</textarea>";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";

print "<br/> <br/> <br/> <br/> <br/> ";
if ($morelines eq "true"){
	print "<br><br><br><br>";
}
if ($moreliness eq "true"){
	print "<br><br><br><br>";
}
if ($morelinescipher eq "true"){
	print "<br><br><br><br>";

}



print "</div>";
#print "</td></tr></table>";

####end form for global parameters
print "</div><br>";
print "</div>";

print "<a name=\"backendlist\"></a>";

print "<div id=\"page-header\"></div>";
print "<div class=\"box-header\">Edit real IP servers configuration</div>";

if ($action eq "editfarm-editserver" || $action eq "editfarm-addserver"){
	print "<form method=\"get\" action=\"index.cgi\#backendlist\">";
}
print "<div class=\"box table\">  <table cellspacing=\"0\">";
#header table
print "<thead><tr><td>Server</td><td>Address</td><td>Port</td><td>Timeout</td><td>Weight</td><td>Actions</td></tr></thead><tbody>";
#
tie @contents, 'Tie::File', "$configdir\/$file";
$nserv=-1;
$index=-1;
$be_section=0;
$to_sw = 0;
$prio_sw = 0;

$id_serverr = $id_server;
foreach $line(@contents){
	$index++;
	if ($line =~ /#BackEnd/){
		$be_section=1;
	}
	if ($be_section == 1){
		if ($line =~ /Address/){	
			$nserv++;
			@ip=split (/\ /,$line);
			chomp(@ip[1]);
		}
		if ($line =~ /Port/){
			@port =split (/\ /,$line);
			chomp(@port);
		}
		if ($line =~ /TimeOut/){
			@timeout = split (/\ /,$line);
			chomp(@timeout);
			$to_sw = 1;
		}
		if ($line =~ /Priority/){
			@priority = split (/\ /,$line);
			chomp(@priority);
			$po_sw = 1;
		}
		if ($line !~ /\#/ && $line =~ /End/ && $line !~ /Back/){
			if ($id_serverr == $nserv && $action eq "editfarm-editserver"){
				print "<form method=\"get\" action=\"index.cgi\#backendlist\">";
				print "<tr class=\"selected\">";
				print "<td>$nserv</td>";
				print "<td><input type=\"text\" size=\"12\"  name=\"rip_server\" value=\"@ip[1]\"> </td>";
				print "<td><input type=\"text\" size=\"4\" name=\"port_server\" value=\"@port[1]\"> </td>";
				print "<td><input type=\"text\" size=\"4\" name=\"timeout_server\" value=\"@timeout[1]\"> </td>";
				print "<td><input type=\"text\" size=\"4\" name=\"priority_server\" value=\"@priority[1]\"> </td>";
				&createmenuserversfarm("edit",$farmname,$nserv);
				print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
                                print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
                                print "<input type=\"hidden\" name=\"id_server\" value=\"$nserv\">";
				print "</form>";
			} else {
				print "<tr>";
				print "<form method=\"get\" action=\"index.cgi\#backendlist\">";
				print "<td>$nserv</td>";
				print "<td>@ip[1]</td>";
				print "<td>@port[1]</td>";
				if ($to_sw == 0){
					print "<td>-</td>";
				} else {
					print "<td>@timeout[1]</td>";
					$to_sw = 0;
				}
				if ($po_sw == 0){
					print "<td>-</td>";
				} else {
	                        	print "<td>@priority[1]</td>";
					$po_sw = 0;
				}
				#print "<td></td>";
				&createmenuserversfarm("normal",$farmname,$nserv);
				print "</tr>";
				print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
			        print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
        			print "<input type=\"hidden\" name=\"id_server\" value=\"$nserv\">";
			
				print "</form>";
				undef @timeout;
				undef @priority;
			}
		}
	}
	if ($be_section == 1 && $line =~ /#End/){
		$be_section = 0;
	}
}
untie @contents;

#content table
if ($action eq "editfarm-addserver"){
	#add new server to  server pool
        $action ="editfarm";
        $isrs="true";
        print "<form method=\"get\" action=\"index.cgi\#backendlist\">";
        print "<tr class=\"selected\">";
        #id server
        print "<td>-</td>";
        print "<input type=\"hidden\" name=\"id_server\" value=\"\">";
        #real server ip
        print "<td><input type=\"text\" size=\"12\"  name=\"rip_server\" value=\"$rip_server\"> </td>";
        #port
        print "<td><input type=\"text\" size=\"4\"  name=\"port_server\" value=\"$port_server\"> </td>";
        #timeout
        print "<td><input type=\"text\" size=\"4\"  name=\"timeout_server\" value=\"$timeout_server\"> </td>";
        #Priority
        print "<td><input type=\"text\" size=\"4\"  name=\"priority_server\" value=\"$priority_server\"> </td>";
        &createmenuserversfarm("add",$farmname,@l_serv[0]);
        print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
        print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
        #print "<input type=\"hidden\" name=\"farmprotocol\" value=\"$farmprotocol\">";
        print "</form>";
        print "</tr>";
}


print "<tr><td colspan=\"5\"></td>";
print "<form method=\"get\" action=\"index.cgi\#backendlist\">";
&createmenuserversfarm("new",$farmname,@l_serv[0]);
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<input type=\"hidden\" name=\"id_server\" value=\"@l_serv[0]\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "</form>";


print "</tr>";

print "</tbody></table></div></div>";

#if ($action eq "editfarm-editserver" || $action eq "editfarm-addserver"){ print "</form>";}

#end table


print "<div id=\"page-header\"></div>";
print "<form method=\"get\" action=\"index.cgi\">";
print "<input type=\"hidden\" value=\"1-2\" name=\"id\">";
print "<input type=\"submit\" value=\"Cancel\" name=\"action\" class=\"button small\">";
print "</form>";
print "<div id=\"page-header\"></div>";
print "</div>";

