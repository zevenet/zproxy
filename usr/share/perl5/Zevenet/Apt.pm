#!/usr/bin/perl
use strict;
use Zevenet::SystemInfo;
use Zevenet::Log;

# no imput params
sub setAPTRepo
{

	# Variables
	my $host = "repo.zevenet.com";
	my $port = "443";
	my $subserial =
	  "openssl x509 -in /usr/local/zevenet/www/zlbcertfile.pem -serial -noout";
	my $subkeyid =
	  "openssl x509 -in /usr/local/zevenet/www/zlbcertfile.pem -noout -text | grep \"4B:1B:18:EE:21:4A:B6:F9:76:DE:C3:D8:86:6D:DE:98:DE:44:93:B9\"";
	my $distribution1 = "stretch";
	my $distribution2 = "jessie";
	my $kernel1       = "4.9.13zva5000";
	my $kernel2       = "3.16.7-ckt20";
	my $kernel3       = "4.9.0-4-amd64";
	my $kernel4       = "3.16.0-4-amd64";
	my $kernel5       = "4.9.110-z5000";
	my $file          = "/etc/apt/sources.list.d/zevenet.list";
	my $gpgkey        = "ee.zevenet.com.gpg.key";
	my $from_version  = "5.2.10";

	# Function call to configure proxy (Zevenet::SystemInfo)
	&setEnv();

	# telnet
	if ( $ENV{ 'https_proxy' } eq "" )
	{
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
	}

	# check zevenet version. Versions prior to 5.2.10 will not be able to subscribe.
	my $cmd = "dpkg -l | grep \"^ii\\s\\szevenet\\s*[0-9]\"";

	my $version = `$cmd`;

	$version =~ s/[\r\n]//g;
	$version =~ s/^ii\s\szevenet\s*//;
	$version =~ s/\s*[a-zA-Z].*//;

	if ( $version lt $from_version )
	{
		&zenlog( "version is $version and moust the version be >= $from_version",
				 "error", "SYSTEM" );
		return 1;
	}

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
		"wget -q --no-check-certificate -T5 -t1 --header=\"User-Agent: $serial\" -O - https://$host/ee/$gpgkey | apt-key add -"
	);
	if ( $error )
	{
		&zenlog( "error adding key gpg", "error", "SYSTEM" );
		return 1;
	}

	# configuring user-agent
	open ( my $fh, '>', '/etc/apt/apt.conf' )
	  or die "Could not open file '/etc/apt/apt.conf' $!";
	print $fh "Acquire { http::User-Agent \"$serial\"; };\n";
	close $fh;

	# get the kernel version
	my $kernelversion = `uname -r`;
	if ( $? != 0 )
	{
		&zenlog( "error getting kernel version", "error", "SYSTEM" );
		return 1;
	}

	# delete line break of the variable
	$kernelversion =~ s/[\r\n]//g;

	# configuring repository
	open ( my $FH, '>', $file ) or die "Could not open file '$file' $!";

	if ( $kernelversion eq $kernel1 )
	{
		print $FH "deb https://$host/ee/v5/$kernel1 $distribution1 main\n";
	}
	if ( $kernelversion eq $kernel2 )
	{
		print $FH "deb https://$host/ee/v5/$kernel2 $distribution2 main\n";
	}
	if ( $kernelversion eq $kernel3 )
	{
		print $FH "deb https://$host/ee/v5/$kernel3 $distribution1 main\n";
	}
	if ( $kernelversion eq $kernel4 )
	{
		print $FH "deb https://$host/ee/v5/$kernel4 $distribution2 main\n";
	}
	if ( $kernelversion eq "$kernel5" )
	{
		print $FH "deb https://$host/ee/v5/$kernel5 $distribution1 main\n";
	}

	close $fh;

	# update repositories
	system ( "apt-get update | logger &" );
	return 0;
}
1;

