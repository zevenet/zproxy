#!/usr/bin/perl
use strict;
use Zevenet::SystemInfo;
use Zevenet::Log;
include 'Zevenet::Certificate::Activation';

my $cert_path = &getGlobalConfiguration( 'zlbcertfile_path' );

sub setAPTRepo
{
	# Variables
	my $keyid     = &getKeySigned();
	my $host      = &getGlobalConfiguration( 'repo_url_zevenet' );
	my $port      = "443";
	my $subserial = "openssl x509 -in $cert_path -serial -noout";
	my $subkeyid  = "openssl x509 -in $cert_path -noout -text | grep \"$keyid\"";
	my $file      = &getGlobalConfiguration( 'apt_source_zevenet' );
	my $apt_conf_file = &getGlobalConfiguration( 'apt_conf_file' );
	my $gpgkey        = &getGlobalConfiguration( 'gpg_key_zevenet' );
	my $distribution1 = "stretch";
	my $distribution2 = "jessie";
	my $kernel1       = "4.9.13zva5000";
	my $kernel2       = "3.16.7-ckt20";
	my $kernel3       = "4.9.0-4-amd64";
	my $kernel4       = "3.16.0-4-amd64";

	#get binaries
	my $dpkg = &getGlobalConfiguration( 'dpkg_bin' );
	my $grep = &getGlobalConfiguration( 'grep_bin' );
	my $wget = &getGlobalConfiguration( 'wget' );

	# Function call to configure proxy (Zevenet::SystemInfo)
	&setEnv();

	# telnet
	require IO::Socket::INET;
	my $socket;
	if (
		 !(
			$socket = IO::Socket::INET->new(
											 PeerAddr => "$host",
											 PeerPort => $port,
											 Proto    => 'tcp',
											 Timeout  => 2
			)
		 )
	  )
	{
		return 1;
	}
	$socket->close();

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
		return 1;
	}

	# command to get the serial
	my $serial = `$subserial`;
	if ( $? != 0 )
	{
		return 1;
	}

	# creating the structure that apt understands
	$serial =~ s/serial=//;

	# delete line break of the variable
	$serial =~ s/[\r\n]//g;

	# adding key
	my $error = &logAndRun(
		"$wget --no-check-certificate -T5 -t1 --header=\"User-Agent: $serial\" -O - https://$host/ee/$gpgkey | apt-key add -"
	);
	if ( $error )
	{
		return 1;
	}

	# configuring user-agent
	open ( my $fh, '>', $apt_conf_file )
	  or die "Could not open file '$apt_conf_file' $!";
	print $fh "Acquire { http::User-Agent \"$serial\"; };\n";
	close $fh;

	# get the kernel version
	my $kernelversion = &getKernelVersion();

	# configuring repository
	open ( my $FH, '>', $file ) or die "Could not open file '$file' $!";

	if ( $kernelversion eq $kernel1 )
	{

		print $FH "deb https://$host/ee/v5/$kernel1 $distribution1 main\n";

	}
	elsif ( $kernelversion eq $kernel2 )
	{

		print $FH "deb https://$host/ee/v5/$kernel2 $distribution2 main\n";

	}
	elsif ( $kernelversion eq $kernel3 )
	{

		print $FH "deb https://$host/ee/v5/$kernel3 $distribution1 main\n";

	}
	elsif ( $kernelversion eq $kernel4 )
	{

		print $FH "deb https://$host/ee/v5/$kernel4 $distribution2 main\n";

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
		$error = &logAndRun( "apt-get update" );
	}

	return 0;
}
1;
