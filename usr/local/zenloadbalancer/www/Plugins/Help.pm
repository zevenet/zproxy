#!/usr/bin/perl

package Help;

#~ use strict;
#~ use warnings;

use Exporter qw(import);
our @EXPORT = qw(data);

require "/usr/local/zenloadbalancer/config/global.conf";
require "/usr/local/zenloadbalancer/www/functions.cgi";
require "/usr/local/zenloadbalancer/www/farms_functions.cgi";
require "/usr/local/zenloadbalancer/www/plugins_functions.cgi";

#our $plugins::plugins_path;

our %data = (
	name => __PACKAGE__,

	content    => undef,
	menu       => \&menu,
	zlbstart   => undef,
	zlbstop    => undef,
	startlocal => undef,
	stoplocal  => undef,

	startfarm => undef,
	stopfarm  => undef,

	position => \&position,
);

my $helpPath = $plugins::plugins_path . "/" . __PACKAGE__;

sub position
{
	my $position = 1;
	return $position;
}

sub menu
{
	my ( $id, $version, $name ) = @_;
	my $urlDocumentation;
	my $output;

	# icono marcado
	my $monitoringiconclass = "";
	my $idType              = $id;
	my $type;

	if ( $id eq "1-2" )
	{
		$type = &main::getFarmType( $name );

		if ( $type eq "tcp" )
		{
			$idType = "1-21";
		}
		if ( $type eq "http" )
		{
			$idType = "1-22";
		}
		if ( $type eq "l4xnat" )
		{
			$idType = "1-23";
		}
		if ( $type eq "datalink" )
		{
			$idType = "1-24";
		}
		if ( $type eq "gslb" )
		{
			$idType = "1-25";
		}

	}

	$urlDocumentation = &forwardingToHelp( $idType, $version );

	if ( $urlDocumentation eq "" )
	{
		$output = "
		<li class=\"nav-item\">
			<a>
				<i class=\"fa fa-info-circle $monitorinconclass\"></i>
				<p>$data{name}</p>
			</a>
		</li>
		";
	}
	else
	{
		$output = "
		<li class=\"nav-item\">
			<a target=\"_blank\" href=\"$urlDocumentation\">
				<i class=\"fa fa-info-circle $monitorinconclass\"></i>
				<p>$data{name}</p>
			</a>
		</li>
	  ";
	}

	return $output;
}

# \params: idPage, versionZen
sub forwardingToHelp
{
	# Recolect params
	my ( $idPage, $versionZen ) = @_;

	# Name for data storage file
	my $fileName = "$helpPath/url.conf";

	# Keep url to forwarding
	my $url = "";

	# Keep the html message necesary to forwarding to helper url
	my $urlMsg = "";

	# Keep end url field ID
	my %urlEnd = %{ &getDataHash( $fileName, "" ) };
	my $params = scalar @_;

	$url = "";

	if ( $params == 2 )
	{
		if ( $urlEnd{ $idPage } )
		{

			# Get main zen version
			$versionZen =~ s/^(\d+\.\d+).*$/$1/e;

			$url =
			    "https://www.zenloadbalancer.com/knowledge-base/enterprise-edition-v"
			  . $versionZen
			  . "-administration-guide/enterprise-edition-v"
			  . $versionZen . "-"
			  . $urlEnd{ $idPage };
		}
	}

	return $url;
}

# Fill a hash with data get from a file
# the file has the next format:
#	key"(split)"value
# 	\param
#		$fileName
#		$splitSymbol	# the default value = ":";
#
# 	\return
#		\%hashFile
#		0				return 0, if there was a error
#
sub getDataHash
{
	use Tie::File;
	my @hf;    # handle file
	my ( $fileName, $splitSymbol ) = @_; # file name, this param is passed as param.
	my %dataHash;                        # keep hash struct from file.
	my @keyValue;
	my $key;
	my $value;

	if ( $splitSymbol =~ "" )
	{
		$splitSymbol = ':';
	}

	if ( @_ > 2 or @_ == 0 )
	{
		&logfile("Error in number of parameters. Function: >getDataHash<.\n");
	}
	else
	{
		tie @hf, 'Tie::File', $fileName;

		if ( ! @hf )
		{
			&logfile("Error! Don\'t find the file $fileName.\n");
			return -1;
		}

		foreach my $iteration ( @hf )
		{
			@keyValue = split ( /$splitSymbol/, $iteration );
			( $key, $value ) = @keyValue;
			$dataHash{ $key } = $value;
		}

		untie @hf;
	}

	return \%dataHash;
}

&plugins::plugins( \%data );

1;
