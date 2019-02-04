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
use Data::Dumper;

use Zevenet::Log;
use Zevenet::Debug;
use Zevenet::Config;
use Zevenet::SystemInfo;

my $SYMKEY = "1135628147310";
my $mod;
my $symbolic_link = "";
my $program_name  = "";
my $basename;

sub include;
include 'Zevenet::Certificate::Activation';

&setEnv();
my $DEBUG = &debug();
&setEnv();

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
	  : ( exists $ENV{ SCRIPT_NAME } && $ENV{ SCRIPT_NAME } =~ /\/zapi.cgi$/ )
	  ? $ENV{ SCRIPT_NAME }
	  : ( $symbolic_link && $symbolic_link =~ /enterprise.bin$/ ) ? $ENV{ _ }
	  : ( exists $ENV{ SCRIPT_NAME } ) ? $ENV{ SCRIPT_NAME }
	  :                                  $^X;

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

# Rewrite script variable. It is necessary to avoid looping calls from the API
$ENV{ SCRIPT_NAME } = 'enterprise.bin';

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

### Exceptions to activation certificate check ### END
# the zevenet script, check certificate itself
my $skip_cert_check = ( $basename eq 'zevenet' );

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

