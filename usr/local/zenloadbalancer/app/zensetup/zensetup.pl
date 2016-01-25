#!/usr/bin/perl
###############################################################################
#
#     This file is part of the Zen Load Balancer Enterprise Edition software 
#     package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This file cannot be distributed, released in public domain and/or for 
#     commercial purposes.
#
###############################################################################

#requires
$sw = 0;
require "/usr/local/zenloadbalancer/www/functions.cgi";
require "/usr/local/zenloadbalancer/config/global.conf";

#program
print "Zen Load Balancer first configuration\n";
print "\n";
print "Select one interface to configure...\n";

#interface
#@interfaces=&listActiveInterfaces();
@interfaces = `ifconfig -a| grep ' Link' | awk {'print \$1'} | grep -v lo | grep -v ':'`;
foreach (@interfaces){
	chomp($_);
	print "\t\tINTERFACE NAME: \t $_ \n";
	if ( $_ eq "mgmt" ){
		$sw = 1;		
	}
}

print "Enter NAME:";
if ($sw == 0 ){
	print "\n";
	$input_if = <>;
}else{
	print "mgmt\n";
	$input_if = "mgmt";
	print "Management interface will be configured through mgmt..\n"
}
chomp($input_if);
#ip for interface
print "Enter the IP for interface $input_if...\n";
$input_ip = <>;
chomp($input_ip);

#netmask for interface
print "Enter the NETMASK for interface $input_if...\n";
$input_netmask = <>;
chomp($input_netmask);

#gateway for interface
print "Enter the GATEWAY for interface $input_if...\n";
$input_gateway = <>;
chomp($input_gateway);

#hotstname 
print "Enter the HOSTNAME for this virtual machine...\n";
$input_hostname = <>;
chomp($input_hostname);
#my @run = `echo $input_hostname > /etc/hostname`;
#my @run = `hostname $input_hostname`;


print "You selected to configure the interface $input_if with this values...\n";
print "\t\tINTERFACE NAME:\t$input_if\n";
print "\t\tIP:\t\t$input_ip\n";
print "\t\tNETMASK:\t$input_netmask\n";
print "\t\tGATEWAY:\t$input_gateway\n";
print "\t\tHOSTNAME:\t$input_hostname\n";

print "Are you sure? y/n [y]\n";
$input_sn = <>;
chomp($input_sn);


if ( $input_sn ne "y" && $input_sn ne "Y" && $input_sn ne ""){
	exit 2;
}

print "Configuring...\n";

#configuring interface
$swaddif = "true";
# check all possible errors
# check if the interface is empty
$if = $input_if;
$newip = $input_ip;
$netmask  = $input_netmask;
$gwaddr = $input_gateway;
$hostn = $input_hostname;
if ( $if =~ /^$/) {
	print "Interface name can not be empty\n";
        $swaddif = "false";
	exit 1;
        }
#check if hostname is empty
if ($hostn =~ /^$/){
	print "Hostname can not be empty\n";
	$swaddif = "false";
	exit 1;
}
# check if the new newip is correct
if (&ipisok($newip) eq "false") {
	print "IP Address $newip structure is not ok\n";
        $swaddif = "false";
	exit 1;
        }
# check if the new netmask is correct, if empty don't worry
if ( $netmask !~ /^$/ && &ipisok($netmask) eq "false") {
        print "Netmask address $netmask structure is not ok\n";
        $swaddif = "false";
	exit 1;
        }
# check if the new gateway is correct, if empty don't worry
if ( $gwaddr !~ /^$/ && &ipisok($gwaddr) eq "false") 
	{
        print "Gateway address $gwaddr structure is not ok\n";
	exit 1;
	}
	#configure hostname 
	my @run = `echo $input_hostname > /etc/hostname`;
	my @run = `hostname $input_hostname`;

	&createIf($if);
        &delRoutes("local",$if);
        &logfile("running '$ifconfig_bin $if $newip netmask $netmask' ");
        @eject = `$ifconfig_bin $if $newip netmask $netmask 2> /dev/null`;
        &upIf($if);
        $state = $?;
        if ($state == 0){
        	$status = "up";
                print "Network interface $if is now UP\n";
         	&writeRoutes($if);
         	&writeConfigIf($if,"$if\:\:$newip\:$netmask\:$status\:$gwaddr\:");
         	&applyRoutes("local",$if,$gwaddr);
		#apply the GW to default gw. 
		&applyRoutes("global",$if,$gwaddr);

		print "Press ENTER to continue configuring your time zone...\n";
		$input_continue = <>;
		system("dpkg-reconfigure tzdata");
		print "Synchronizing time with pool.ntp.org, please wait...\n";
		system("ntpdate pool.ntp.org");
		print "\n\n";

         	print "All is ok, saved $if interface config file\n";
         	print "If this is your first boot you can access to Zen Web GUI through https://$newip:444 with user admin and password admin, remember change the password for security reasons in web GUI.\n";
         } else {
                print "A problem is detected configuring $if interface, you have to configure your $if through command line and after save the configuration in the web GUI\n";
         }

if ( -e "/etc/firstzlbboot" ){
	my @run = `rm /etc/firstzlbboot`;
}

print "If you want to rerun this quick first assistant create the file /etc/firstzlbboot and restart the virtual machine\n"
