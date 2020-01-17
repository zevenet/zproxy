#!!!!!!NO REMOVE COMMENTS LINES!!!!!!
#!!!!!!comments lines have a special patron that web application have to process

#::INI Global information
#Zevenet root directory
$zdir="/usr/local/zevenet";
#Zevenet bin directory
$zbindir = "/usr/local/zevenet/bin";
#Zevenet bin directory
$templatedir = "/usr/local/zevenet/share";
#Zevenet lib directory
$zlibdir="/usr/share/perl5/Zevenet";#update
#Document Root for Web Aplication directory
$basedir="/usr/local/zevenet/www";
#configuration directory.In this section all config files are saved.
$configdir="/usr/local/zevenet/config";
#Log directory
$logdir="/var/log";#update
#File configuration Zen Cluster
$filecluster="/usr/local/zevenet/config/cluster.conf";
#File configuration GUI
$confhttp="/usr/local/zevenet/app/cherokee/etc/cherokee/cherokee.conf";#update
#ntp server
$ntp="pool.ntp.org";
#Do backup to
$backupfor="/usr/local/zevenet/config /usr/local/zevenet/www/*.pem /usr/local/zevenet/app/cherokee/etc/cherokee/cherokee.conf /etc/iproute2/rt_tables /etc/ssh/sshd_config /etc/snmp/snmpd.conf /etc/keepalived/keepalived.conf /etc/conntrackd/conntrackd.conf /etc/hostname /etc/resolv.conf /etc/cron.d/zevenet /zevenet_version";#update
#Save backups on
$backupdir="/usr/local/zevenet/backups/";
#rt tables file
$rttables = "/etc/iproute2/rt_tables";
#this file
$globalcfg = "/usr/local/zevenet/config/global.conf";
#version ZEVENET
$version="5.2.18-1";#update
#appliance version file
$applianceVersionFile="/etc/zevenet_version";
#Cipher PCI
$cipher_pci="kEECDH+ECDSA+AES128:kEECDH+ECDSA+AES256:kEECDH+AES128:kEECDH+AES256:kEDH+AES128:kEDH+AES256:DES-CBC3-SHA:+SHA:!aNULL:!eNULL:!LOW:!kECDH:!DSS:!MD5:!EXP:!PSK:!SRP:!CAMELLIA:!SEED";#update
#Cipher ssloffloading
$cipher_ssloffloading="AES";
#HTPASSWD file
$htpass="/etc/passwd";#update
#shadow file
$shadow_file="/etc/shadow";
#ZAPI KEY
$zapikey="";
# Zen license
$licenseFileTxt="/usr/local/zevenet/license.txt";
# Zen license
$licenseFileHtml="/usr/local/zevenet/license.html";
# debug level
$debug="0";

#dns file server?
$filedns="/etc/resolv.conf";
#Where is hostname binary?
$hostname="/bin/hostname";
#Where is kill binary?
$kill_bin="/bin/kill";
#Where is uname binary?
$uname="/bin/uname";
#Where is tar binary?
$tar="/bin/tar";
#where is ifconfig binary?
$ifconfig_bin="/sbin/ifconfig";
#Where is ip bynary?
$ip_bin="/sbin/ip";
#Where is wc binary?
$wc_bin="/usr/bin/wc";
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
#Where is mkdir?
$mkdir="/bin/mkdir";
#Where is awk binary?
$awk="/usr/bin/awk";
#Where is logger?
$logger="/usr/bin/logger";
#Where is sec?
$sec="/usr/bin/sec";
#Where is ipset?
$ipset = "/sbin/ipset";
#Where is touch?
$touch = "/usr/bin/touch";
#Where is ls?
$ls="/bin/ls";
#Where is stat?
$stat="/usr/bin/stat";
#Where is cp?
$cp="/bin/cp";
#Where is rm?
$rm="/bin/rm";
#Where is iptables?
$iptables="/sbin/iptables";
#Where is ip6tables?
$ip6tables="/sbin/ip6tables";
#Where is modprobe?
$modprobe="/sbin/modprobe";
#Where is lsmod?
$lsmod="/sbin/lsmod";
#Where is gdnsd?
$gdnsd="/usr/local/zevenet/app/gdnsd/sbin/gdnsd";
#Where is l4sd?
$l4sd="/usr/local/zevenet/bin/l4sd";#update
#Where is id binary?
$bin_id="/usr/bin/id";
#Where is wget binary?
$wget="/usr/bin/wget";
#Where is conntrack binary?
$conntrack="/usr/sbin/conntrack";
#systemctl
$systemctl="/bin/systemctl";
#Where is insserv?
$insserv="/sbin/insserv";
#Where is temperature file?
$temperatureFile="/proc/acpi/thermal_zone/THRM/temperature";
#Where is update-rc.d?
$updatercd="/usr/sbin/update-rc.d";
#Where is packetbl?
$packetbl_bin="/bin/packetbl";
#Where is adduser?
$adduser_bin="/usr/sbin/adduser";
#Where is deluser?
$deluser_bin="/usr/sbin/deluser";
#Where is groupadd?
$groupadd_bin="/usr/sbin/groupadd";
#Where is groupdel?
$groupdel_bin="/usr/sbin/groupdel";
#Where is groups?
$groups_bin="/usr/bin/groups";
#Where is echo?
$echo_bin="/bin/echo";
#Where id curl?
$curl_bin="/usr/bin/curl";
#Where is cat binary?
$cat_bin="/bin/cat";
#Where is dpkg binary?
$dpkg_bin="/usr/bin/dpkg";
#Where is grep binary?
$grep_bin="/bin/grep";

#proxy
$http_proxy="";
$https_proxy="";

#where is pound binary?
$pound="/usr/local/zevenet/app/pound/sbin/pound";
#where is pound ctl?
$poundctl="/usr/local/zevenet/app/pound/sbin/poundctl";
#pound file configuration template?
$poundtpl="/usr/local/zevenet/app/pound/etc/poundtpl.cfg";
#piddir
$piddir="/var/run";

## Network global configuration options ##
$fwmarksconf = "$configdir/fwmarks.conf";
#System Default Gateway
$defaultgw="";
#Interface Default Gateway
$defaultgwif="";
#System Default IPv6 Gateway
$defaultgw6="";
#Interface Default IPv6 Gateway
$defaultgwif6="";
#Number of gratuitous pings
$pingc="1";
#routing options
$routeparams="initcwnd 10 initrwnd 10";
#IPv6
$ipv6_enabled="false";

## L4xNat - netfilter
# Maximum recent ip list
$recent_ip_list_tot="6000";#update
# Recent ip hash
$recent_ip_list_hash_size="6000";#update
# Iptables lock filename
$iptlock = "/tmp/iptables.lock";

#Directory where is check script. In this directory you can save your own check scripts.
$libexec_dir="/usr/local/zevenet/app/libexec";
#FarmGuardian binary, create advanced check for backend servers
$farmguardian="/usr/local/zevenet/bin/farmguardian";#update

#Where is ZenRRD Directory?. There is a perl script that create rrd database and images from Monitoring section
$rrdap_dir="/usr/local/zevenet/app/zenrrd";#update
#Relative path in Web Root directory ($basedir) where is graphs from ZenRRD *no modify
$img_dir="/tmp";#update
#Relative path where is rrd databases from ZenRRD * no modify
$rrd_dir="rrd";#update

#Service for configure Zen directory replication
$zenino="/usr/local/zevenet/bin/enterprise.bin zeninotify";#update
#Zen Inotify pid file
$zeninopid="/var/run/zeninotify.pid";
#Rsync replication parameters
$zenrsync="-azvr --delete";#update
#Arptables
$arptables="/sbin/arptables";
#ARP unsolicited
$arp_unsolicited="";
#ARP announcement, true / false (default)
$arp_announce="";

#Script for Hook routing
$hookup="hookup";

# cron service
$cron_service = "/etc/init.d/cron";

# keepalived configuration file
$keepalived_conf="/etc/keepalived/keepalived.conf";
# conntrackd configuration file
$conntrackd_conf="/etc/conntrackd/conntrackd.conf";
# cluster floating interfaces configuration file path
$floatfile="/usr/local/zevenet/config/float.conf";
# node_status file path
$znode_status_file="/usr/local/zevenet/node_status";

# zcluster-manager command path
$zcluster_manager="/usr/local/zevenet/bin/zcluster-manager";#update
# ssh-copy-id file path
$ssh_copy_id="/usr/local/zevenet/bin/ssh-copy-id.sh";#update
# primary-backup conntrackd script
$primary_backup = "/usr/share/doc/conntrackd/examples/sync/primary-backup.sh";

# sshd file
$sshConf="/etc/ssh/sshd_config";
# ssh service
$sshService="/etc/init.d/ssh";
# sshkey file path
$key_path="/root/.ssh";
# sshkey file path
$key_id="id_rsa";
# ssh keygen command
$keygen_cmd="ssh-keygen -t rsa -f $key_path/$key_id -N '' -q";#update

# Bios version
$bios_version="/sys/devices/virtual/dmi/id/bios_version";

#Zen backup
$zenbackup="/usr/local/zevenet/bin/zenbackup.pl";#update

#SNMP Service
$snmpdconfig_file="/etc/snmp/snmpd.conf";

#Bonding interfaces
$bond_config_file="/usr/local/zevenet/config/bonding.conf";
$sys_net_dir="/sys/class/net";
$bonding_masters_filename="/sys/class/net/bonding_masters";
$bonding_mode_filename="bonding/mode";
$bonding_slaves_filename="bonding/slaves";
$bonding_miimon_filename="bonding/miimon";

#Notifications Module
$notifConfDir = "/usr/local/zevenet/config/notifications";
$secTemplate="/usr/local/zevenet/share/sec.rules";
$syslogFile="/var/log/syslog";

#IPDS Module
$blacklistsPath = "/usr/local/zevenet/config/ipds/blacklists/lists";
$blacklistsConf = "/usr/local/zevenet/config/ipds/blacklists/lists.conf";
$blacklistsLocalPreload = "/usr/local/zevenet/www/ipds/blacklists/local";#update
$blacklistsRemotePreload = "/usr/local/zevenet/www/ipds/blacklists/remote_lists.conf";#update
$blacklistsCronFile = "/etc/cron.d/blacklists";
$dosConf = "/usr/local/zevenet/config/ipds/dos/dos.conf";
$dosConfDir = "/usr/local/zevenet/config/ipds/dos";

#Ssyncd
$ssyncd_enabled = "true";
$ssyncd_bin     = "/usr/local/zevenet/app/ssyncd/bin/ssyncd";
$ssyncdctl_bin  = "/usr/local/zevenet/app/ssyncd/bin/ssyncdctl";
$ssyncd_port    = "9999";

# time period to get the interface throughput stats
$throughput_period = "5";
$throughput_enabled = "false";

# connection logs for farms. If this parameter is "true" all traffic will be logged
# else only the new connections will be logged
$full_farm_logs = "false";

# cloud
$cloud_address_metadata="169.254.169.254";
$aws_bin="/usr/bin/aws";
$aws_credentials="/root/.aws/credentials";
$aws_config="/root/.aws/config";

#::END Global Section

#!!!!NOT REMOVE NEXT LINE!!!!!!
1;
