#!/usr/bin/perl 

#Zen Load Balancer is a Web GUI integrated with binary systems that
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

#use CGI qw(:standard escapeHTML);
use CGI;
use CGI::Carp qw(warningsToBrowser fatalsToBrowser); 
print "Content-type: text/html\n\n";


#print "ident es $idpost";

##REQUIRES

require "functions.cgi";
#require 'functions.cgi';
require "config/global.conf";

#loading form variables
my(%Variables); #reset hash
#read query send get 
my $bufferget = $ENV{'QUERY_STRING'};

#read query send post
read(STDIN, $bufferpost, $ENV{'CONTENT_LENGTH'});

#split variable post
my @pairs = split(/&/, $bufferpost);


#split variable get
my @pairsget = split(/&/, $bufferget);

foreach my $pair (@pairsget)
{
#separate variable with its name
        my ($name, $value) = split(/=/, $pair);

        #
        $name =~ tr/+/ /;
        $name =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
        $value =~ tr/+/ /;
        $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
	#get method	
        #keys for values
        $Variables{$name} = $value;
}
#variables in get string
$id = $Variables{'id'};
$action = $Variables{'action'};
$line = $Variables{'line'};
$var = $Variables{'var'};
$toip = $Variables{'toip'};
$toipv = $Variables{'toipv'};
$ifname= $Variables{'ifname'};
$newip = $Variables{'newip'};
$if = $Variables{'if'};
$status = $Variables{'status'};
$bc = $Variables{'bc'};
$netmask = $Variables{'netmask'};
$gwaddr = $Variables{'gwaddr'};
$source = $Variables{'source'};
$toif = $Variables{'toif'};
$farmname = $Variables{'farmname'};
$vip = $Variables{'vip'};
$vipp = $Variables{'vipp'};
$farmpid = $Variables{'farmpid'};
$newfarmname = $Variables{'newfarmname'};
$cable = $Variables{'cable'};
$graphtype = $Variables{'graphtype'};
##servers value in a farm
$id_server = $Variables{'id_server'};
$id_serverr = $Variables{'id_serverr'};
$rip_server = $Variables{'rip_server'};
$port_server = $Variables{'port_server'};
$max_server = $Variables{'max_server'};
$timeout_server = $Variables{'timeout_server'};
$weight_server = $Variables{'weight_server'};
$priority_server = $Variables{'priority_server'};
#end servers variables in a farm
$timeout = $Variables{'timeout'};
$lb = $Variables{'lb'};
$persistence = $Variables{'persistence'};
$max_clients = $Variables{'max_clients'};
$conn_max = $Variables{'conn_max'};
$max_servers = $Variables{'max_servers'};
$viewtableservers = $Variables{'viewtableservers'};
$viewtableclients = $Variables{'viewtableclients'};
$viewtableconn = $Variables{'viewtableconn'};
$usefarmguardian = $Variables{'usefarmguardian'};
$farmguardianlog = $Variables{'farmguardianlog'};
$timetocheck = $Variables{'timetocheck'};
$check_script = $Variables{'check_script'};
$lhost = $Variables{'lhost'};
$rhost = $Variables{'rhost'};
$lip = $Variables{'lip'};
$rip = $Variables{'rip'};
$vipcl = $Variables{'vipcl'};
$xforwardedfor = $Variables{'xforwardedfor'};
$typecl = $Variables{'typecl'};
$clstatus = $Variables{'clstatus'};
$filelog = $Variables{'filelog'};
$nlines = $Variables{'nlines'};
$ipgui = $Variables{'ipgui'};
$guiport = $Variables{guiport};
$file = $Variables{'file'};
$name = $Variables{'name'};
$editfarm = $Variables{'editfarm.x'};
$editfarmsaveserver = $Variables{'editfarmsaveserver.x'};
$tracking = $Variables{'tracking'};
$farmprotocol = $Variables{"farmprotocol"};
$param = $Variables{"param"};
$session = $Variables{"session"};
$ttl = $Variables{"ttl"};
$blacklist = $Variables{"blacklist"};
$httpverb = $Variables{"httpverb"};
$certname = $Variables{"certname"};
$ciphers = $Variables{"ciphers"};
$cipherc = $Variables{"cipherc"};
$idcluster = $Variables{'idcluster'};
$nattype = $Variables{'nattype'};
$service = $Variables{'service'};
$string = $Variables{'string'};

#end variables in get string


#post to string
foreach $pair (@pairs) 
	{
        #Separamos la variable de su valor
        ($name, $value) = split(/=/, $pair);
        #Decodificamos
        $name =~ tr/+/ /;
        $name =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
        $value =~ tr/+/ /;
        $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
        $Variablespost{$name} = $value;
    	}

$pass= $Variablespost{'pass'} if(defined($Variablespost{'pass'}));
$newpass= $Variablespost{'newpass'} if(defined($Variablespost{'newpass'}));
$trustedpass= $Variablespost{'trustedpass'} if(defined($Variablespost{'trustedpass'}));
$idpost = $Variablespost{'id'} if(defined($Variablespost{'id'}));
#$id= $Variablespost{'id'} if(defined($Variablespost{'id'}));
$action = $Variablespost{'actionpost'} if(defined($Variablespost{'actionpost'}));
$err414 = $Variablespost{'err414'} if(defined($Variablespost{'err414'}));
$err500 = $Variablespost{'err500'} if(defined($Variablespost{'err500'}));
$err501 = $Variablespost{'err501'} if(defined($Variablespost{'err501'}));
$err503 = $Variablespost{'err503'} if(defined($Variablespost{'err503'}));
$farmname = $Variablespost{'farmname'} if(defined($Variablespost{'farmname'}));

#
###login 

#if ($id != '' )



if ($id)
        {
	$id = $Variables{'id'};
        }
elsif ($idpost)
	{
	$id = $idpost;
	}
else
        {
        $id ="1-1";
        }


##HEADER
require "header.cgi";
require "menu.cgi";

if (! -f "$basedir/lock")
{
eval {
	local $SIG{ALARM} = sub { die "alarm\n" };

	alarm $timeouterrors; 
	#LEFT LATERAL MENU
	require "content".$id.".cgi";
	alarm 0;
    };
	if ($@) { print "Error in content$id cgi execution, see ZEN logs\n";}	
}
else
{
&errormsg("Actually Zen GUI is locked, please unlock with '/etc/init.d/zenloadbalancer start' command");
}
#FOOTER
require "footer.cgi";
