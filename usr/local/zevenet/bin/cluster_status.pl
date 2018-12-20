#!/usr/bin/perl
###############################################################################
#
#    Zevenet Software License
#    This file is part of the Zevenet Load Balancer software package.
#
#    Copyright (C) 2014-today ZEVENET SL, Sevilla (Spain)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

use strict;
use warnings;

use Time::Local;
use Zevenet::Log;
use Zevenet::Debug;
use Zevenet::Config;
use Data::Dumper;
sub include;
use Zevenet::SystemInfo;

&setEnv();

my $DEBUG  = &debug();
my $SYMKEY = "1135628147310";
my $mod;

my $symbolic_link = "";
my $program_name  = "";
my $basename;

my $cmd_dir = "/usr/share/perl5/Zevenet/Cmd";

if ( defined $ARGV[0]
	 and ( -f "$cmd_dir/$ARGV[0].pm" or -f "$cmd_dir/$ARGV[0].pme" ) )
{
	$basename = shift @ARGV;
	&zenlog( "get basename from parameters: $basename", 'debug', 'enterprise.bin' );
}
else
{
	$symbolic_link =
	  ( exists $ENV{ _ } and -l $ENV{ _ } ) ? readlink ( $ENV{ _ } ) : "";
	$program_name =
	    ( $0 ne '-e' ) ? $0
	  : ( exists $ENV{ SCRIPT_NAME } && $ENV{ SCRIPT_NAME } =~ /\/v3\/zapi.cgi$/ )
	  ? $ENV{ SCRIPT_NAME }
	  : ( $symbolic_link && $symbolic_link =~ /enterprise.bin$/ ) ? $ENV{ _ }
	  :                                                             $^X;

# Exception for keepalived running zcluster-manager
# %ENV  = {
#           'PATH' => '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
#           'JOURNAL_STREAM' => '8:4800662',
#           'LANG' => 'en_US.UTF-8',
#           'DAEMON_ARGS' => '',
#           'PWD' => '/',
#           'INVOCATION_ID' => 'e411a760c957493eb7e1624ae2f67c61'
#         };
#~ if ( $program_name =~ /enterprise.bin$/ && exists $ENV{INVOCATION_ID} )
#~ {
#~ $program_name = 'zcluster-manager';
#~ }
	######################################################################

	$basename = ( split ( '/', $program_name ) )[-1];
}

if ( $DEBUG > 5 )
{
	&zenlog( "[ENTERPRISE.BIN] \$PROGRAM_NAME (\$0)     = '$0'",      'debug' );
	&zenlog( "[ENTERPRISE.BIN] \$EXECUTABLE_NAME (\$^X) = '$^X'",     'debug' );
	&zenlog( "[ENTERPRISE.BIN] \$ENV\{_\}               = '$ENV{_}'", 'debug' )
	  if exists $ENV{ _ };
	&zenlog( "[ENTERPRISE.BIN] \$SYMBOLIC_LINK          = $symbolic_link", 'debug' )
	  if exists $ENV{ _ };
	&zenlog( "[ENTERPRISE.BIN] \$ENV\{SCRIPT_NAME\}      = '$ENV{SCRIPT_NAME}'",
			 'debug' )
	  if exists $ENV{ SCRIPT_NAME };
	&zenlog( "[ENTERPRISE.BIN] \$ENV\{INVOCATION_ID\}    = '$ENV{INVOCATION_ID}'",
			 'debug' )
	  if exists $ENV{ INVOCATION_ID };
	&zenlog( "[ENTERPRISE.BIN] \$program_name          = '$program_name'",
			 'debug' );
	&zenlog( "[ENTERPRISE.BIN] \$basename              = '$basename'", 'debug' );
	&zenlog( "[ENTERPRISE.BIN] \@ARGV                  = '@ARGV'",     'debug' );

	#~ &zenlog('[ENTERPRISE.BIN] %ENV                     = ' . Dumper \%ENV );
}

# Run encrypted command
if ( $basename ne 'enterprise.bin' && $basename ne 'zevenet' )
{
	$basename =~ s!\.(?:pl|cgi)$!!;    # Remove trailing .pl or .cgi if exists

	if ( $basename eq 'zapi' )
	{
		my $api_ver =
		  ( split ( '/', $program_name ) )[-2];    # get zapi.cgi directory name
		$basename = "$basename-$api_ver";          # add version. E.g.: 'zapi-v3'
	}

	$mod->{ name } = "Zevenet::Cmd::$basename";

	#	if ( $DEBUG )
	#	{
	#		my $msg = '';
	#
	#		$msg = "enterprise.bin called: $0";
	#		#~ &zenlog( $msg );
	#		#~ say( $msg );
	#
	#		$msg = "enterprise.bin basename: $basename";
	#		#~ say( $msg );
	#
	#		$msg = "Module: $mod";
	#		#~ &zenlog( $msg );
	#		#~ say( $msg );
	#	}

	include $mod->{ name };
	exit;
}

require Zevenet::Validate;
use Crypt::CBC;
use POSIX 'strftime';

$mod->{ name } = shift @ARGV;

# check module name provided
unless ( $mod->{ name } )
{
	print STDERR "enterprise.bin: missing operand
Try 'enterprise.bin --help' for more information.\n";

	exit 1;
}

# command help and usage instructions
if ( $mod->{ name } =~ /^(?:-h|-help|--help)$/ )
{
	print "Usage: enterprise.bin MODULE [FUNCTION]
Decrypt Zevenet Enterprise Edition Module.

Example:\tenterprise.bin Zevenet::API31::System::Cluster get_cluster < JSONFILE

Run encrypted module accepting arguments from STDIN in JSON format, returning JSON output.
";

	exit 0;
}

&getModuleInfo( $mod );

#########################
## Required conditions ##
#########################

# check function name provided
my $func = shift @ARGV;
unless ( $func )
{
	die "$basename: No function name received.";
}

############################
## Activation certificate ##
############################

# check if the activation certificate is valid
my $hostname = &getHostname();
my $basedir  = &getGlobalConfiguration( 'basedir' );

### Exceptions to activation certificate check ### BEGIN
# Upload activation certificate
my $upload_cert = ( $mod->{ name } =~ /Zevenet::API3\d::Certificate::Activation/
					&& $func eq 'upload_activation_certificate' );

# Stopping zevenet service
my $stop_zevenet = (
				   $mod->{ name } eq 'Zevenet::Service' && ( $func eq 'stop_service'
													 || $func eq 'disable_cluster' )
);
### Exceptions to activation certificate check ### END
my $exception = (     $mod->{ name } eq 'Zevenet::RBAC::User::Core'
				  and $func eq 'validateRBACUserZapi' );
my $exception_rbac = (     $mod->{ name } eq 'Zevenet::RBAC::Core'
					   and $func eq 'getRBACPermissionsMsg' );

my $skip_cert_check =
  ( $upload_cert || $stop_zevenet || $exception || $exception_rbac );

unless ( $skip_cert_check )
{
	my $swcert = &certcontrol();

	if ( $swcert > 0 )
	{
		die "$basename: Invalid activation certificate ($swcert)";
	}
}

## Module. Find, decrypt and load the module
include $mod->{ name }, $func;

# Arguments. Passed from STDIN as a JSON string
# Load Input, then Decode JSON from intput string

# get input for api function
my $input;
{
	local $/ = undef;
	$input = <STDIN>;

	#~ if ( $DEBUG > 9 )
	#~ {
	#~ &zenlog("enterprise.bin INPUT: $input");
	#~ }
}

# my $input_l = length $input;
# unless ( $input_l >= 2 )
# { &zenlog("Function args input length: Not enough characters. Failed!" ); }
# &zenlog( "#### Function input: $input" ) if $input ne '["1"]';

# decode JSON
require JSON;
JSON->import();

# decode input into data reference
my $args;
if ( eval { $args = decode_json( $input ); } )
{
	1 || &zenlog( "#### Function input JSON decode: [OK]" );
}    ####
else { &zenlog( "#### Function input JSON decode: Failed!" ); }    ####

## Run call

# make code reference from function name
my $code_ref = \&{ $func };
my $returned_value;

# call api request function
eval { $returned_value = [$code_ref->( @{ $args } )] };

if ( $@ )
{
	&zenlog( "#### Function run $func: Failed!" );
	&zenlog( $@ );
	die $@;
}

#~ &zenlog("$mod->{ name }::$func returned ". $returned_value );
#~ &zenlog("$mod->{ name }::$func returned value dump ". Dumper( $returned_value ) );

unless ( defined $returned_value )
{
	&zenlog( "#### Function output defined: Failed!" );
}    ####

my $output = '';

if ( ref $returned_value )
{
	## Proccess output

	# Encode output in JSON and print it
	my $json = JSON->new();

	#~ unless ( eval { $json_out = encode_json( $returned_value ); } )
	unless (
		eval
		{
			$output =
			  $json->pretty->indent->canonical->allow_blessed->convert_blessed->encode(
																			  $returned_value );
		}
	  )
	{
		&zenlog( "#### Function output JSON encode: Failed!" );
	}

	# Optionally send JSON to system log
	#~ &zenlog( "json: '$_'" ) for split ( /\\n/, $output );
}
else
{
	$output = $returned_value;
}

# Send Output to STDOUT
print $output;

# Send memory usage info to system log
if ( &debug() )
{
	my $msg = "MODULE: $mod->{ name } FUNCTION: $func " . &getMemoryUsage();

	&zenlog( $msg );
}

exit 0;

=begin nd
Function: getModuleInfo

	Get some information from a module


	Variable		Example
	--------------------------------------------------------
	'lib_path'    '/usr/share/perl5',
	'path'        'Zevenet/Cluster.pm',
	'fullpath'    '/usr/share/perl5/Zevenet/Cluster.pm',
	'key'         'Zevenet/Cluster.pm',
	'name'        'Zevenet::Cluster',
	'epath'       'Zevenet/Cluster.pme',
	'enc'         'false'


Parameters:
	mod_space - .

Returns:
	undef
=cut

sub getModuleInfo
{
	my $mod = shift;

	# Predefined lib path
	$mod->{ lib_path } = '/usr/share/perl5';

	# There are 2 possible paths:
	# - path	=> is a .pm file
	# - epath	=> is a .pme file
	$mod->{ path } = "$mod->{ name }.pm";
	$mod->{ path } =~ s#\:\:#\/#g;    # Replace :: with /
	$mod->{ epath } = "$mod->{ path }e";
	$mod->{ enc }   = '';                  # to remove a warning

	# Store in $mod->{ key } the correct path relative to $mod->{ lib_path }

	if ( -f "$mod->{ lib_path }/$mod->{ path }" )
	{
		$mod->{ enc } = 'false';
		$mod->{ key } = "$mod->{ path }";
	}
	elsif ( -f "$mod->{ lib_path }/$mod->{ epath }" )
	{
		$mod->{ enc } = 'true';
		$mod->{ key } = "$mod->{ epath }";
	}
	else
	{
		use Data::Dumper;
		$mod->{ key } = '';
		&zenlog(
			"FAILURE!!! Not found module $mod->{ name } : $mod->{ lib_path }/$mod->{ path }(.e)"
		);
	}

	# Store in $mod->{ fullpath } the full path to the module
	$mod->{ fullpath } = "$mod->{ lib_path }/$mod->{ key }";

	# Debugging message
	#~ &zenlog( Data::Dumper->Dump( [$mod], ['mod'] ), 'debug2' );
}

=begin nd
Function: include

	Load Enterprise module, encrypted or not.


	Example %INC:
	{
		'Zevenet/Debug.pme' => '/usr/share/perl5/Zevenet/Debug.pme'
		...
	};


Parameters:
	mod_space - .

Returns:
	undef
=cut

sub include
{
	my $mod;
	$mod->{ name } = shift @_;
	my $func = shift;

	&getModuleInfo( $mod );

	# Finish if the module is already loaded
	return if exists $INC{ $mod->{ key } };

	my $code;

	if ( $mod->{ enc } eq 'false' )    # Load unencrypted module
	{
		require $mod->{ fullpath };
		$code = `cat $mod->{ fullpath }`;
	}
	elsif ( $mod->{ enc } eq 'true' )    # Load encrypted module
	{
		my $uname          = &getGlobalConfiguration( 'uname' );
		my $kernel_release = `$uname -r`;

		my $cmd =
		  "openssl aes-256-cbc -d -a -nosalt -k \"${SYMKEY}\" -in $mod->{ fullpath }";
		$cmd .= " -md md5" if $kernel_release =~ /^4.9/;

		# get code
		$code = `$cmd`;

		#~ &zenlog("[include] Module load BEGIN :: $mod->{ name }");

		# load module
		eval $code;

		#~ &zenlog("[include] Module load END :: $mod->{ name }");

		# log error messages if any happened
		if ( $@ )
		{
			&zenlog( "### Module name: $mod->{ name }" );
			&zenlog( "### Module path: $mod->{ fullpath }" );
			&zenlog( $@ );
			die $@;
		}
		else
		{
			$INC{ $mod->{ key } } = $mod->{ fullpath };
		}
	}

	if ( $func )
	{
		# Function. Check the function is in the module, load params from input in JSON
		my @code = split ( "\n", $code );
		my $func_found = grep { /^sub $func(?:\W|$)/ } split ( "\n", $code );

		# check if the function is available
		unless ( $func_found )
		{
			die "$basename: definition of function $func not found in $mod->{ name }";
		}
	}
}

############################################
### Activation certificate code ############
############################################
#~ use Time::Local;
#~ use Zevenet::Config;
#~ use Zevenet::SystemInfo;

##build CBC Object
sub buildcbc
{
	my $cipher = Crypt::CBC->new(
					 -literal_key => 1,
					 -key => 'wg2kx8VY2NVYDdQSAdqffmHYMd2d97ypYdJ4hwczAm8YBPtHv28EJJ66',
					 -cipher  => 'Blowfish',
					 -iv      => 'r5JLLw4f',
					 -header  => 'none',
					 -padding => 'null'
	);

	return $cipher;
}

#encrypt CBC and return result
sub encrypt    # string for encrypt
{
	my $data = shift;

	my $cipher = &buildcbc();
	my $result = $cipher->encrypt_hex( $data );

	return $result;
}

sub decrypt    # string for decrypt
{
	my $data = shift;

	my $cipher = &buildcbc();
	my $result = $cipher->decrypt_hex( $data );

	return $result;
}

# build local key
sub keycert
{
	#~ use Zevenet::SystemInfo;

	my $dmi      = &get_sys_uuid();
	my $hostname = &getHostname();
	my $mod_appl = &get_mod_appl();

	my $key = "$hostname::$dmi::$mod_appl";
	my $str = &encrypt( $key );

	return $str;
}

sub keycert_old
{
	#~ use Zevenet::SystemInfo;
	my $dmi      = get_sys_uuid();
	my $hostname = &getHostname();

	my $block1 = crypt ( "${dmi}${hostname}", "93" );
	my $block2 = crypt ( "${hostname}${dmi}", "a3" );
	my $block3 = crypt ( "${dmi}${hostname}", "ZH" );
	my $block4 = crypt ( "${hostname}${dmi}", "h7" );
	$block1 =~ s/^93//;
	$block2 =~ s/^a3//;
	$block3 =~ s/^ZH//;
	$block4 =~ s/^h7//;

	my $str = "${block1}-${block2}-${block3}-${block4}";
	return $str;
}

# evaluate certificate
sub certcontrol
{
	#~ require Time::Local;
	#~ use Zevenet::Config;
	require Zevenet::SystemInfo;

	my $basedir         = &getGlobalConfiguration( 'basedir' );
	my $zlbcertfilename = shift // "zlbcertfile.pem";
	my $zlbcertfile     = "$basedir/$zlbcertfilename";
	my $swcert          = 0;

	if ( !-e $zlbcertfile )
	{
		#swcert = 1 ==> There isn't certificate
		$swcert = 1;
		return $swcert;
	}
	my $openssl  = &getGlobalConfiguration( 'openssl' );
	my $keyid    = "4B:1B:18:EE:21:4A:B6:F9:76:DE:C3:D8:86:6D:DE:98:DE:44:93:B9";
	my @months   = qw(Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec);
	my $hostname = &getHostname();
	my $key      = &keycert_old();

	my @zen_cert = `$openssl x509 -in $zlbcertfile -noout -text 2>/dev/null`;

	my $serial = `$openssl x509 -in $zlbcertfile -serial -noout`;
	$serial =~ /serial\=(\w+)/;
	$serial = $1;

	my @key_cert = grep /Subject: ?.+/, @zen_cert;
	$key_cert[0] =~ /Subject: ?.+OU ?= ?([.\/0-9A-Za-z\-]+), ?/;
	my $cert_ou = $1;

	if ( $cert_ou eq 'false' )
	{
		$key_cert[0] =~ /Subject: ?.+1\.2\.3\.4\.5\.8 ?= ?(.+)/;
		my $cert_ou = $1;
		$key = &keycert();
	}
	if ( $cert_ou =~ m/-/ && $func eq 'upload_activation_certificate' )
	{
		$swcert = 5;
		return $swcert;
	}

	if ( !grep /keyid:$keyid/, @zen_cert )
	{
		#swcert = 2 ==> Cert isn't signed OK
		$swcert = 2;
		return $swcert;
	}
	elsif (    ( !grep /$key/, @zen_cert )
			|| ( !grep ( /(CN=$hostname\/|CN = $hostname\,)/, @zen_cert ) ) )
	{
		#swcert = 5 ==> Cert isn't valid
		$swcert = 5;
		return $swcert;
	}

	# Verify date of check
	my $date_today = strftime "%F", localtime;
	my $date_encode = &encrypt( $date_today );
	$date_encode =~ s/\s*$//;

	my $configdir  = &getGlobalConfiguration( 'configdir' );
	my $file_check = "$configdir/config_check";

	require Zevenet::Lock;
	my $file_lock = &getLockFile( $file_check );
	my $lock_fd = &openlock( $file_lock, '>' );

	my $read_check = &openlock( $file_check, '<' );
	my $date_check = <$read_check>;
	$date_check =~ s/\s*$//;
	close $read_check;

	if ( $date_check ne $date_encode )
	{
		my $write_check = &openlock( $file_check, '>' );
		print $write_check $date_encode;
		close $write_check;

		my $crl_path = "$configdir/cacrl.crl";

		my $date_mod = '';

		if ( -f $crl_path )
		{
			$date_mod = `stat -c%y $crl_path`;
		}
		else
		{
			&zenlog( "WARNING!!! File $crl_path not found." );
		}
		my $wget = &getGlobalConfiguration( 'wget' );
		my @modification = split /\ /, $date_mod;
		$modification[0] = $modification[0] // '';

		if ( $modification[0] ne $date_today )
		{
			require IO::Socket;

			if (
				 my $scan = IO::Socket::INET->new(
												   PeerAddr => "certs.zevenet.com",
												   PeerPort => 443,
												   Proto    => 'tcp',
												   Timeout  => 2
				 )
			  )
			{
				$scan->close();
				my $tmp_file = '/tmp/cacrl.crl';

				# Download CRL
				my $download =
				  `$wget -q -T5 -t1 -O $tmp_file https://certs.zevenet.com/pki/ca/index.php?stage=dl_crl`;
				if ( -s $tmp_file > 0 )
				{
					&zenlog( "CRL Downloaded on $date_today" );
					my $copy = `cp $tmp_file $crl_path`;
				}
				unlink $tmp_file;
			}
		}

		my @decoded;
		@decoded = `$openssl crl -inform DER -text -noout -in $crl_path`
		  if -f $crl_path;
		if ( !grep /keyid:$keyid/, @decoded )
		{
			#swcert = 2 ==> Cert isn't signed OK
			$swcert = 2;
			return $swcert;
		}

		foreach my $line ( @decoded )
		{
			if ( grep /Serial Number\: ?$serial/, $line )
			{
				my $isRevoked = grep /Serial Number\: ?$serial/, $line;
				if ( $isRevoked > 0 )
				{
					&zenlog( "Certificate Revoked (CRL check)" );
					$swcert = 4;
					return $swcert;
				}
			}
		}
	}
	close $lock_fd;

	# Certificate expiring date
	my ( $na ) = grep /Not After/i, @zen_cert;
	$na =~ s/.*not after.*:\ //i;
	my ( $month2, $day2, $hours2, $min2, $sec2, $year2 ) = split /[ :]+/, $na;
	( $month2 ) = grep { $months[$_] eq $month2 } 0 .. $#months;
	my $end       = timegm( $sec2, $min2, $hours2, $day2, $month2, $year2 );
	my $totaldays = '';
	my $type_cert = '';

	#Certificate with old format
	if ( $cert_ou =~ m/-/ )
	{
		# Certificate validity date
		my ( $nb ) = grep /Not Before/i, @zen_cert;
		$nb =~ s/.*not before.*:\ //i;

		my ( $month, $day, $hours, $min, $sec, $year ) = split /[ :]+/, $nb;
		( $month ) = grep { $months[$_] eq $month } 0 .. $#months;
		my $ini = timegm( $sec, $min, $hours, $day, $month, $year );

		$totaldays = ( $end - $ini ) / 86400;
		$totaldays =~ s/\-//g;

		#Certificate with new format
	}
	else
	{
		my $dmi      = &get_sys_uuid();
		my $mod_appl = &get_mod_appl();

		my $key_decrypy = &decrypt( $key );
		my @data_key = split /::/, $key_decrypy;

		my @type_cert_array = grep /C ?= ?(DE|TE)\,/, @zen_cert;
		$type_cert_array[0] =~ /C ?= ?(DE|TE)\,/;
		$type_cert = $1;

		if (    ( !grep /$hostname/, $data_key[0] )
			 || ( !grep /$dmi/,      $data_key[1] )
			 || ( !grep /$mod_appl/, $data_key[2] ) )
		{
			#swcert = 5 ==> Cert isn't valid
			$swcert = 5;
			return $swcert;
		}
	}

	my $dayright = ( $end - time () ) / 86400;

	if ( $dayright < 0 )
	{
		#control errors
		if (    ( $totaldays ne '' && $totaldays < 364 )
			 || ( $totaldays eq '' && $type_cert eq 'TE' ) )
		{
			# Policy: expired testing certificates would not stop zen service,
			# but rebooting the service would not start the service,
			# interfaces should always be available.
			$swcert = 3;
		}

		if (    ( $totaldays ne '' && $totaldays > 364 )
			 || ( $totaldays eq '' && $type_cert eq 'DE' ) )
		{
			# The contract support plan is expired you have to request a
			# new contract support. Only message alert!
			$swcert = -1;
		}
	}

	# error codes
	#swcert = 0 ==> OK
	#swcert = 1 ==> There isn't certificate
	#swcert = 2 ==> Cert isn't signed OK
	#swcert = 3 ==> Cert test and it's expired
	#swcert = 4 ==> Cert is revoked
	#swcert = 5 ==> Cert isn't valid

	#swcert = -1 ==> Cert support and it's expired

	#output
	return $swcert;
}

sub checkActivationCertificate
{
	my $swcert         = 0;
	my $uploadCertFlag = 0;
	if ( scalar ( @_ ) > 0 )
	{
		my $tmpCertFile = $_[0];
		$uploadCertFlag = 1;
		$swcert         = &certcontrol( "$tmpCertFile" );
	}
	else
	{
		$swcert = &certcontrol();
	}

	# if $swcert is greater than 0 zapi should not work
	if ( $swcert > 0 )
	{
		my $msg;

		if ( $swcert == 1 )
		{
			$msg =
			  "There isn't a valid Zevenet Load Balancer certificate file, please request a new one";
		}
		elsif ( $swcert == 2 )
		{
			$msg =
			  "The certificate file isn't signed by the Zevenet Certificate Authority, please request a new one";
		}
		elsif ( $swcert == 3 )
		{
			# Policy: expired testing certificates would not stop zen service,
			# but rebooting the service would not start the service,
			# interfaces should always be available.
			$msg =
			  "The Zevenet Load Balancer certificate file you are using is for testing purposes and its expired, please request a new one";
		}
		elsif ( $swcert == 4 )
		{
			$msg =
			  "The Zevenet Load Balancer certificate file has been revoked, please request a new one";
		}
		elsif ( $swcert == 5 )
		{
			$msg =
			  "The Zevenet Load Balancer certificate file isn't valid for this machine.";
		}

		my $body = {
					 message         => $msg,
					 certificate_key => &keycert(),
					 hostname        => &getHostname(),
		};
		return ( { "msg" => $msg } ) if $uploadCertFlag == 1;
		return &httpResponse( { code => 402, body => $body } );
	}

	return $swcert;
}

sub get_sys_uuid
{
	my ( $dmi ) = grep ( /UUID\:/, `/usr/sbin/dmidecode` );
	( undef, $dmi ) = split ( /:\s+/, $dmi );

	chomp $dmi;

	return $dmi;
}

sub get_mod_appl
{
	my @mod = grep ( /\w{3} ?\d{4}/, `cat /etc/zevenet_version` );
	$mod[0] =~ /(\w{3} ?\d{4})/;

	my $mod_appl = $1;
	$mod_appl =~ s/ //;

	return $mod_appl;
}