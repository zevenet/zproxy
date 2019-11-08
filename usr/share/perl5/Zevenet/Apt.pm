#!/usr/bin/perl
use strict;
use Zevenet::SystemInfo;
use Zevenet::Log;
include 'Zevenet::Certificate::Activation';

my $cert_path = &getGlobalConfiguration( 'zlbcertfile_path' );

sub setAPTRepo
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	# Variables
	my $keyid     = &getKeySigned();
	my $host      = &getGlobalConfiguration( 'repo_url_zevenet' );
	my $port      = "443";
	my $subserial = "openssl x509 -in $cert_path -serial -noout";
	my $subkeyid  = "openssl x509 -in $cert_path -noout -text | grep \"$keyid\"";
	my $subkeyidentifier =
	  "openssl x509 -in $cert_path -noout -text | grep -A1 \"Subject Key Identifier\"";
	my $file          = &getGlobalConfiguration( 'apt_source_zevenet' );
	my $apt_conf_file = &getGlobalConfiguration( 'apt_conf_file' );
	my $gpgkey        = &getGlobalConfiguration( 'gpg_key_zevenet' );
	my $aptget_bin    = &getGlobalConfiguration( 'aptget_bin' );
	my $aptkey_bin    = &getGlobalConfiguration( 'aptkey_bin' );
	my $distribution  = "buster";
	my $kernel        = "4.19-amd64";

	#get binaries
	my $dpkg = &getGlobalConfiguration( 'dpkg_bin' );
	my $grep = &getGlobalConfiguration( 'grep_bin' );
	my $wget = &getGlobalConfiguration( 'wget' );

	# Function call to configure proxy (Zevenet::SystemInfo)
	&setEnv();

# telnet
#require IO::Socket::INET;
#my $socket;
#if (
#	 !(
#		$socket = IO::Socket::INET->new(
#										 PeerAddr => "$host",
#										 PeerPort => $port,
#										 Proto    => 'tcp',
#										 Timeout  => 2
#		)
#	 )
#  )
#{
#	&zenlog(
#		"No connection to internet, please check connection and configure proxy if needed",
#		"error", "apt"
#	);
#	return 0;
#}
#$socket->close();

	# check zevenet version. Versions prior to 5.2.5 will not be able to subscribe.
	my $cmd = "$dpkg -l | $grep \"^ii\\s\\szevenet\\s*[0-9]\"";

	my $version = `$cmd`;

	$version =~ s/[\r\n]//g;
	$version =~ s/^ii\s\szevenet\s*//;
	$version =~ s/\s*[a-zA-Z].*//;

	# command to check keyid
	my $keyid = `$subkeyid`;
	if ( $? != 0 )
	{
		&zenlog( "Keyid is not correct", "error", "apt" );
		return 1;
	}

	# command to get the serial
	my $serial = `$subserial`;
	if ( $? != 0 )
	{
		&zenlog( "Serial is not correct", "error", "apt" );
		return 1;
	}

	# creating the structure that apt understands
	$serial =~ s/serial=//;

	# delete line break of the variable
	$serial =~ s/[\r\n]//g;

	# command to get the Subject Key Identifier
	my $subjectkeyidentifier = `$subkeyidentifier`;
	if ( $? != 0 )
	{
		&zenlog( "Subject ID is not correct", "error", "apt" );
		return 1;
	}
	$subjectkeyidentifier =~ s/[\r\n]//g;
	$subjectkeyidentifier =~ s/.*:\s+//g;

	# adding key
	my $error = &logAndRun(
		"$wget --no-check-certificate -T5 -t1 --header=\"User-Agent: $serial\" -O - https://$host/ee/$gpgkey | $aptkey_bin add -"
	);
	if ( $error )
	{
		&zenlog( "Error connecting to $host, $gpgkey couldn't be downloaded",
				 "error", "apt" );
		return 0;
	}

	my $http_proxy  = &getGlobalConfiguration( 'http_proxy' );
	my $https_proxy = &getGlobalConfiguration( 'https_proxy' );

	# configuring user-agent
	open ( my $fh, '>', $apt_conf_file )
	  or die "Could not open file '$apt_conf_file' $!";
	print $fh "Acquire { http::User-Agent \"$serial:$subjectkeyidentifier\"; };\n";
	print $fh "Acquire::http::proxy \"$http_proxy\/\";\n";
	print $fh "Acquire::https::proxy \"$http_proxy\/\";\n";
	close $fh;

	# get the kernel version
	my $kernelversion = &getKernelVersion();

	# configuring repository
	open ( my $FH, '>', $file ) or die "Could not open file '$file' $!";

	if ( $kernelversion =~ /^4.19/ )
	{
		print $FH "deb https://$host/ee/v6/$kernel $distribution main\n";

	}
	else
	{
		&zenlog( "The kernel version is not valid, $kernelversion", "error", "apt" );
		$error = 1;
	}

	close $fh;

	if ( !$error )
	{
		# update repositories
		$error = &logAndRun( "$aptget_bin update" );
	}

	return 0;
}

sub getAPTUpdatesList
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $package_list = &getGlobalConfiguration( 'apt_outdated_list' );
	my $message_file = &getGlobalConfiguration( 'apt_msg' );

	my @pkg_list = ();
	my $msg;
	my $date   = "";
	my $status = "unknown";
	my $install_msg =
	  "To upgrade the system, please, execute in a shell the following command:
	'apt-get --with-new-pkgs upgrade'";

	my $fh = &openlock( $package_list, '<' );
	if ( $fh )
	{
		@pkg_list = split ( ' ', <$fh> );
		close $fh;

		# remove the fisrt item
		shift @pkg_list if ( $pkg_list[0] eq 'Listing...' );
	}

	$fh = &openlock( $message_file, '<' );
	if ( $fh )
	{
		$msg = <$fh>;
		close $fh;

		if ( $msg =~ /last check at (.+) -/ )
		{
			$date   = $1;
			$status = "Updates available";
		}
		elsif ( $msg =~ /Zevenet Packages are up-to-date/ )
		{
			$status = "Updated";
		}
	}

	return {
			 'message'    => $install_msg,
			 'last_check' => $date,
			 'status'     => $status,
			 'number'     => scalar @pkg_list,
			 'packages'   => \@pkg_list
	};
}

#check if local APT config is done
#return 0 if OK
#return 1 if APT is not configured
sub getAPTConfig()
{

	my $file          = &getGlobalConfiguration( 'apt_source_zevenet' );
	my $apt_conf_file = &getGlobalConfiguration( 'apt_conf_file' );
	use File::Grep;

	if ( ( !-e $file ) or ( !-e $apt_conf_file ) )
	{
		&zenlog( "APT config files don't exist", "error", "apt" );
		return 1;

	}
	if (    ( !fgrep { /zevenet/ } $file )
		 or ( !fgrep { /http::User-Agent/ } $apt_conf_file ) )
	{
		&zenlog( "APT config is not done properly", "error", "apt" );
		return 1;

	}
	&zenlog( "return 0" );
	return 0;
}

#function used by checkupgrade in order to re-configre APT after any certificate key upload process
sub setCheckUpgradeAPT()
{
	if ( &getAPTConfig ne 0 )
	{
		&setAPTRepo();
	}

}

1;
