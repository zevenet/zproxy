#!/usr/bin/perl 
 
##############################################################################
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

use CGI;
use CGI::Carp qw(warningsToBrowser fatalsToBrowser); 
use MIME::Base64;
#print "Content-type: text/javascript; charset=utf8\n\n";

my $q = CGI->new;
our $origin = 1;

require "/usr/local/zenloadbalancer/www/functions.cgi";
require "/usr/local/zenloadbalancer/www/farms_functions.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v1/global.cgi";
require "/usr/local/zenloadbalancer/config/global.conf";
require "/usr/local/zenloadbalancer/www/zapi/v1/get.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v1/post.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v1/put.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v1/action.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v1/interface.cgi";



####cert control functions######

#############function
$dmidecode_bin="/usr/sbin/dmidecode";
$openssl_bin="/usr/bin/openssl";
$keyid="4B:1B:18:EE:21:4A:B6:F9:76:DE:C3:D8:86:6D:DE:98:DE:44:93:B9";



sub keycert(){
	my @dmidec = `$dmidecode_bin`;
	my @dmidec2 = grep(/UUID\:/,@dmidec);	
	my $dmi = @dmidec2[0]; 
	$dmi =~ s/\"//g;
	$dmi =~ s/^\s+//;
	$dmi =~ s/\s+$//;

	$dmi =~ s/\ //g;
	my @dmidec3 = split(":",$dmi);
	$dmi = @dmidec3[1];
	$hostname = hostname();
        $hostname =~ s/\"//g;
        $hostname =~ s/^\s+//;
        $hostname =~ s/\s+$//;

	$n=2;

	$encrypted_string = crypt("${dmi}${hostname}","93"); 
	$encrypted_string2 = crypt("${hostname}${dmi}","a3"); 
	$encrypted_string3 = crypt("${dmi}${hostname}","ZH"); 
	$encrypted_string4 = crypt("${hostname}${dmi}","h7"); 
	$encrypted_string =~ s/^93//;
	$encrypted_string2 =~ s/^a3//;
	$encrypted_string3 =~ s/^ZH//;
	$encrypted_string4 =~ s/^h7//;
	$str = "${encrypted_string}-${encrypted_string2}-${encrypted_string3}-${encrypted_string4}";
        $str =~ s/\"//g;
        $str =~ s/^\s+//;
        $str =~ s/\s+$//;
	
	return $str;
	
	

}
sub certcontrol(){

$swcert = 0;
$zlbcertfile = "$basedir/zlbcertfile.pem";

my $key = &keycert();

my $notbefore;
my $nb;
my @notafter;
my $na;

if ( -e $zlbcertfile){
	my @run = `$openssl_bin x509 -in $zlbcertfile -noout -text 2>/dev/null`;
        if ( (!grep /$key/,@run) || (!grep /keyid:$keyid/,@run) || (!grep /CN=$hostname\//,@run) ){
        	#&errormsg( "Zen Load Balancer activation certificate isn't valid, please request one");
                $swcert = 2;
        }

	use Date::Parse;
        use Time::localtime;
        $now = ctime();
        @notbefore = grep /Not Before/i,@run;
        $nb = join '',@notbefore;
        $nb =~ s/not before.*:\ //i;
        $ini = str2time($nb);
        #
        @notafter = grep /Not After/i,@run;
        $na = join "",@notafter;
        $na =~ s/not after.*:\ //i;
        $end = str2time($na);
        my $totaldays = ($end - $ini) / 86400;
        $totaldays =~ s/\-//g;
        my $dayright = ( $end - time() ) / 86400;


                #control errors
        if ($totaldays < 364 && $dayright < 0 && $swcert == 0 ){
        	#it is working with test cert and cert is expired. It should goes down
                $swcert = 3;

        }

        if ($totaldays > 364 && $dayright < 0 && $swcert == 0){
        	#The contract support plan is expired you have to request a new contract support. Only message alert!
                $swcert = -1;

		}

       }else{
                #There isn't certificate in the machine
                $swcert = 1;

        }

#code errors
        #swcert = 0 ==> OK
        #swcert = 1 ==> There isn't certificate 
        #swcert = 2 ==> Cert isn't signed OK
        #swcert = 3 ==> Cert test and it's expired




#
if ($swcert != 0 ){

	if ($swcert == 1){
	        &errormsg("There isn't a valid ZLB certificate key, please request a new one");
	}
	if ($swcert == 2){
	        &errormsg("The certificate key isn't signed by the ZLB Certificate Authority, please request a new one");
	}
	if ($swcert == 3){
	        &errormsg("The ZLB certificate key you are using is for testing purposes and its expired, please request a new one");
	        #stop appliance
	        &logfile("ZLB is going down now");
		print "stop service ..."
	        #system("/etc/init.d/zenloadbalancer stop > /dev/null &");
	}
	
	if ($swcert == -1){
	        &warnmsg("The ZLB certificate key support is expired, please request a new one");
	}




	print "Certificate key: $key ";
	#key cert

	}


#output
return $swcert;
}






####end cert control functions######



#########################################
#
# Check user authentication
#
#########################################

$not_allowed = 0;
#my $userpass = $ENV{HTTP_AUTHORIZATION};
#$userpass =~ s/Basic\ //i;
#my $userpass_dec = decode_base64($userpass);
#my @user = split(":",$userpass_dec);
#my $user = @user[0];
#my $pass = @user[1];

if (!(&checkLoggedZapiUser()) ){
	print $q->header(
	   -type=> 'text/plain',
	   -charset=> 'utf-8',
	   -status=> '401 Unauthorized'
	);
    print "User not authorized";

    exit;
}

#########################################
#
# Check ZAPI key
#
#########################################

my %headers = map { $_ => $q->http($_) } $q->http();

foreach $key (keys(%ENV)) {
    #chomp($key);
    if ($key eq "HTTP_ZAPI_KEY"){
	if ($ENV{$key} eq &getZAPI("keyzapi","")  && &getZAPI("status","") eq "true"){
		$not_allowed = 1;
	}
  }


}

my $certerr = &certcontrol();

if ($not_allowed eq "0" || $certerr > 0){
	print $q->header(
	   -type=> 'text/plain',
	   -charset=> 'utf-8',
	   -status=> '401 Unauthorized'
	);
	print "Not authorized";
	exit;
}


#####################################

use JSON::XS;

$enabled = 1;

sub GET($$) {
	my ($path, $code) = @_;
	return unless $q->request_method eq 'GET' or $q->request_method eq 'HEAD';
	return unless $q->path_info =~ $path;
	$code->();
	exit;
}

sub POST($$) {
	my ($path, $code) = @_;
	return unless $q->request_method eq 'POST';
	return unless $q->path_info =~ $path;
	$code->();
	exit;
}

sub PUT($$) {
	my ($path, $code) = @_;
	return unless $q->request_method eq 'PUT';
	return unless $q->path_info =~ $path;
	$code->();
	exit;
}

sub DELETE($$) {
	my ($path, $code) = @_;
	return unless $q->request_method eq 'DELETE';
	return unless $q->path_info =~ $path;
	$code->();
	exit;
}

eval{

	#########################################
	#
	#  GET List all farms
	#
	#########################################
	GET qr{^/farms$} => sub {
	
		&farms();
	
	};

        #########################################
        #
        #  GET stats
        #
        #########################################

	GET qr{^/stats$} => sub {
		&stats();

	};

	#########################################
	#
	#  GET get farm info
	#
	#########################################
	GET qr{^/farms/(\w+$)} => sub {
	
		&farms_name();
	
	};

	#########################################
	#
	#  POST new farm
	#
	#########################################
	POST qr{^/farms/(\w+$)} => sub {
	
		&new_farm($1);
		
	};

	#########################################
	#
	#  POST new service
	#
	#########################################

	POST qr{^/farms/(\w+)/services$} => sub {

		&new_farm_service($1);
		
	};
	
	#########################################
	#
	#  POST new zone
	#
	#########################################

	POST qr{^/farms/(\w+)/zones$} => sub {

		&new_farm_zone($1);
		
	};
	
	#########################################
	#
	#  POST new backend
	#
	#########################################

	POST qr{^/farms/(\w+)/backends$} => sub {

		&new_farm_backend($1);
		
	};

	#########################################
	#
	#  POST new zone resource
	#
	#########################################

	POST qr{^/farms/(\w+)/zoneresources$} => sub {

		&new_farm_zoneresource($1);
		
	};

	#########################################
        #
        #  POST farm actions
        #
        #########################################

        POST qr{^/farms/(\w+)/actions$} => sub {

                &actions($1);

        };

       #########################################
        #
        #  POST Upload Certificate File .pem
        #
        #########################################

        POST qr{^/uploadcerts$} => sub {

                &upload_certs();

        };


	#########################################
	#
	#  DELETE farm
	#
	#########################################
	DELETE qr{^/farms/(\w+$)} => sub {
		
		&delete_farm($1);

	};
	
	#########################################
	#
	#  DELETE service
	#
	#########################################

	DELETE qr{^/farms/(\w+)/services/(\w+$)} => sub {

		&delete_service($1, $2);
		
	};
	
	#########################################
	#
	#  DELETE zone
	#
	#########################################

	#DELETE qr{^/farms/(\w+)/zones/(.*+$)} => sub {
	DELETE qr{^/farms/(\w+)/zones/(([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$)} => sub {

		&delete_zone($1, $2);
		
	};
	
	#########################################
	#
	#  DELETE backend (TCP/UDP/L4XNAT/DATALINK)
	#
	#########################################

	DELETE qr{^/farms/(\w+)/backends/(\w+$)} => sub {

		&delete_backend($1, $2);
		
	};
	
	#########################################
	#
	#  DELETE backend (HTTP/HTTPS/GSLB)
	#
	#########################################

	DELETE qr{^/farms/(\w+)/services/(\w+)/backends/(\w+$)} => sub {

		&delete_service_backend($1, $2, $3);
		
	};
	
	#########################################
	#
	#  DELETE zone resource
	#
	#########################################

	DELETE qr{^/farms/(\w+)/zones/([a-z0-9].*-*.*\.[a-z0-9].*)/resources/(\w+$)} => sub {
		&delete_zone_resource($1, $2, $3);
	
	};
	
	#########################################
	#
	#  PUT farm
	#
	#########################################

	PUT qr{^/farms/(\w+$)} => sub {
	
		&modify_farm($1);
		
	};

        #########################################
        #
        #  PUT backend
        #
        #########################################

        PUT qr{^/farms/(\w+)/backends/(\w+$)} => sub {

                &modify_backends($1,$2);

        };	

        #########################################
        #
        #  PUT farmguardian
        #
        #########################################

        PUT qr{^/farms/(\w+)/fg$} => sub {
                &modify_farmguardian($1);

        };

	#########################################
        #
        #  PUT resources
        #
        #########################################

        PUT qr{^/farms/(\w+)/resources/(\w+$)} => sub {
                &modify_resources($1,$2);

        };

	#########################################
        #
        #  PUT zones
        #
        #########################################

        PUT qr{^/farms/(\w+)/zones/(.*+$)} => sub {
                &modify_zones($1,$2);

        };

	#########################################
        #
        #  PUT services
        #
        #########################################

        PUT qr{^/farms/(\w+)/services/(\w+$)} => sub {
                &modify_services($1,$2);

        };

        #########################################
        #
        #  POST virtual interface
        #
        #########################################

        POST qr{^/addvini/(.*+$)} => sub {

                &new_vini($1);

        };

        #########################################
        #
        #  POST vlan interface
        #
        #########################################

        POST qr{^/addvlan/(\w+$)} => sub {

                &new_vlan($1);

        };


        #########################################
        #
        #  POST action interface
        #
        #########################################

        POST qr{^/ifaction/(.*+$)} => sub {

                &ifaction($1);

        };


        #########################################
        #
        #  DELETE virtual interface
        #
        #########################################

        DELETE qr{^/deleteif/(.*+$)} => sub {

                &delete_interface($1);

        };


	#########################################
        #
        #  GET interfaces
        #
        #########################################
        GET qr{^/interfaces$} => sub {
                &get_interface();

        };


        #########################################
        #
        #  PUT interface
        #
        #########################################

        PUT qr{^/modifyif/(.*+$)} => sub {

                &modify_interface($1);

        };

	
#end eval
};
