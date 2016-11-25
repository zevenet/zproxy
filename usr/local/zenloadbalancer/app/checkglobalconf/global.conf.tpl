#!!!!!!NO REMOVE COMMENTS LINES!!!!!!
#!!!!!!comments lines have a special patron that web application have to process 

#::INI Global information
#Document Root for Web Aplication  directory
$basedir="/usr/local/zenloadbalancer/www";
#configuration directory.In this section all config files are saved.
$configdir="/usr/local/zenloadbalancer/config";
#Log directory
$logdir="/usr/local/zenloadbalancer/logs/";
#log filename for this Graphic user interface.Some action with this GUI will be saved here.
$logfile="/usr/local/zenloadbalancer/logs/zenloadbalancer.log";
#.<b>Time out execution ZEVENET GUI CGIs.</b> <font size=1>When timeout is exceded the cgi execution is killed automatically.</font>
$timeouterrors="60";
#File configuration Zen Cluster
$filecluster="/usr/local/zenloadbalancer/config/cluster.conf";
#File configuration GUI
$confhttp="/usr/local/zenloadbalancer/app/cherokee/etc/cherokee/cherokee.conf";#update
#.<b>ntp server</b>
$ntp="pool.ntp.org";
#Do backup to
$backupfor="$configdir $confhttp /etc/iproute2/rt_tables";
#Save backups on
$backupdir="/usr/local/zenloadbalancer/backups/";
#rt tables file
$rttables = "/etc/iproute2/rt_tables";
#this file
$globalcfg = "/usr/local/zenloadbalancer/config/global.conf";
#version ZEVENET
$version="4.3";#update
#Cipher PCI
$cipher_pci="kEECDH+ECDSA+AES128:kEECDH+ECDSA+AES256:kEECDH+AES128:kEECDH+AES256:kEDH+AES128:kEDH+AES256:DES-CBC3-SHA:+SHA:!aNULL:!eNULL:!LOW:!kECDH:!DSS:!MD5:!EXP:!PSK:!SRP:!CAMELLIA:!SEED";#update
#BUY SSL Certificates
$buy_ssl="http://ecommerce.sofintel.net/ssl/ssl-certificate.aspx?ci=8347&prog_id=503889";
#URL of dinamic content in global view
$url="https://www.sofintel.net/json/eeinfo.php";
#HTPASSWD file
$htpass="/etc/passwd";#update
#ZAPI KEY
$zapikey="";

#dns file server?
$filedns="/etc/resolv.conf";
#apt file
$fileapt="/etc/apt/sources.list";
#Where is tar binary?
$tar="/bin/tar";
#where is ifconfig binary?
$ifconfig_bin="/sbin/ifconfig";
#Where is ip bynary?
$ip_bin="/sbin/ip";
#Where is pen (tcp) load balancer?
$pen_bin="/usr/local/zenloadbalancer/app/pen/bin/pen";
#Where is pen control load balancer?
$pen_ctl="/usr/local/zenloadbalancer/app/pen/bin/penctl";
#Where is fdisk binary?
$fdisk_bin="/sbin/fdisk";
#Where is df binary?
$df_bin="/bin/df";
#Where is ssh-keygen binary?
$sshkeygen="/usr/bin/ssh-keygen";
#Where is ssh client?
$ssh="/usr/bin/ssh";
#Where is scp binary?
$scp="/usr/bin/scp";
#Where is rsync binary?
$rsync="/usr/bin/rsync";
#Where is ucarp binary?
$ucarp="/usr/local/zenloadbalancer/app/ucarp/sbin/ucarp";
#Where is pidof binary?
$pidof="/bin/pidof";
#Where is ps binary?
$ps="/bin/ps";
#Where is tail binary?
$tail="/usr/bin/tail";
#Where is zcat binary?
$zcat="/bin/zcat";
#Where is ntpserver?
$datentp="/usr/sbin/ntpdate";
#Where is arping?
$arping_bin="/usr/bin/arping";
#Where is ping?
$ping_bin="/bin/ping";
#Where is openssl?
$openssl="/usr/bin/openssl";
#Where is unzip?
$unzip="/usr/bin/unzip";
#Where is mv?
$mv="/bin/mv";
#Where is ls?
$ls="/bin/ls";
#Where is cp?
$cp="/bin/cp";
#Where is iptables?
$iptables="/sbin/iptables";
#Where is modprobe?
$modprobe="/sbin/modprobe";
#Where is lsmod?
$lsmod="/sbin/lsmod";
#Where is netstat-nat?
$netstatNat="/usr/bin/netstat-nat";
#Where is gdnsd?
$gdnsd="/usr/local/zenloadbalancer/app/gdnsd/sbin/gdnsd";
#Where is l4sd?
$l4sd="/usr/local/zenloadbalancer/app/l4s/bin/l4sd";
#Where is id binary?
$bin_id="/usr/bin/id";
#Where is conntrack binary?
$conntrack="/usr/sbin/conntrack";

#where is pound binary?
$pound="/usr/local/zenloadbalancer/app/pound/sbin/pound";
#where is pound ctl?
$poundctl="/usr/local/zenloadbalancer/app/pound/sbin/poundctl";
#pound file configuration template?
$poundtpl="/usr/local/zenloadbalancer/app/pound/etc/poundtpl.cfg";
#piddir
$piddir="/var/run/";

## Network global configuration options ##
$fwmarksconf = "$configdir/fwmarks.conf";
#System Default Gateway
$defaultgw="";
#Interface Default Gateway
$defaultgwif="";
#Number of gratuitous pings
$pingc="1";

## L4xNat - netfilter
# Maximum recent ip list
$recent_ip_list_tot="6000";#update
# Recent ip hash
$recent_ip_list_hash_size="6000";#update
# Iptables lock filename
$iptlock = "/tmp/iptables.lock";

#Directory where is check script. In this directory you can save your own check scripts. 
$libexec_dir="/usr/local/zenloadbalancer/app/libexec";
#FarmGuardian binary, create advanced check for backend servers
$farmguardian="/usr/local/zenloadbalancer/app/farmguardian/bin/farmguardian";
#Directory where FarmGuardian save the configuration files
$farmguardian_dir="/usr/local/zenloadbalancer/app/farmguardian/etc";
#Directory where FarmGuadian save the logs
$farmguardian_logs="/usr/local/zenloadbalancer/logs";

#Where is ZenRRD Directory?. There is a perl script that create rrd database and images from Monitoring section
$rrdap_dir="/usr/local/zenloadbalancer/app/zenrrd";#update
#Relative path in Web Root directory ($basedir) where is graphs from ZenRRD *no modify
$img_dir="/img/graphs/";
#Relative path where is rrd databases from ZenRRD * no modify
$rrd_dir="rrd";#update
#File log name  for ZenRRD. A lot of disk space is needed. If it is blank no loggin
$log_rrd="";

#Service for configure Zen directory replication
$zenino="/usr/local/zenloadbalancer/app/zeninotify/zeninotify.pl"; 
#Zen Inotify pid file 
$zeninopid="/var/run/zeninotify.pid";
#Zen inotify log file
$zeninolog="/usr/local/zenloadbalancer/logs/zeninotify.log";
#.<b>Rsync replication parameters</b>
$zenrsync="-auzv --delete";

#Services for configure start latency service
$zenlatup="/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl";
#Services for configure stop latency service
$zenlatdown="/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl";
#Zen latency log file
$zenlatlog="/usr/local/zenloadbalancer/logs/zenlatency.log";

#Zen backup
$zenbackup="/usr/local/zenloadbalancer/app/zenbackup/zenbackup.pl";

#Plugins path
$pluginsdir="/usr/local/zenloadbalancer/www/Plugins";#update
#::END Global Section

#!!!!NOT REMOVE NEXT LINE!!!!!!
1
