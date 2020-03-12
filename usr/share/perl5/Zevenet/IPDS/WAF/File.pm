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

use Zevenet::Core;

include 'Zevenet::IPDS::WAF::Core';
my $wafFileDir = &getWAFSetDir();

=begin nd
Function: listWAFFile

	It returns an object with the WAF scripts and data files and the blacklists sources files.

Parameters:
	none - .

Returns:
	Hash ref - The output of the hash is like:

	  "windows-powershell-commands" : {
         "module" : "waf",
         "name" : "windows-powershell-commands",
         "path" : "/usr/local/zevenet/config/ipds/waf/sets/windows-powershell-commands.data",
         "type" : "data"
      },
      "wordpress_list" : {
         "module" : "blacklist",
         "name" : "wordpress_list",
         "path" : "/usr/local/zevenet/config/ipds/blacklists/lists/wordpress_list.txt",
         "type" : "data"
      }

=cut

sub listWAFFile
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my %files = ();
	my @f_dir;
	my $reg_name = '[^\.\/]+';

	if ( opendir ( my $fd, $wafFileDir ) )
	{
		@f_dir = readdir ( $fd );
		closedir $fd;

		foreach my $f ( @f_dir )
		{
			my $type;
			if    ( $f =~ /($reg_name)\.lua$/ )  { $type = 'script'; }
			elsif ( $f =~ /($reg_name)\.data$/ ) { $type = 'data'; }
			else                                 { next; }

			$files{ $1 } = {
							 name   => $1,
							 type   => $type,
							 path   => "$wafFileDir/$f",
							 module => "waf",
			};
		}
	}

	# add blacklist files
	my $blacklistsPath = &getGlobalConfiguration( 'blacklistsPath' );
	if ( opendir ( my $fd, $blacklistsPath ) )
	{
		@f_dir = readdir ( $fd );
		closedir $fd;

		foreach my $f ( @f_dir )
		{
			if ( $f =~ /($reg_name)\.txt$/ )
			{
				$files{ $1 } = {
								 name   => $1,
								 type   => 'data',
								 path   => "${blacklistsPath}/$f",
								 module => "blacklist",
				};
			}
		}

	}

	return \%files;
}

=begin nd
Function: existWAFFile

	It checks if a WAF File exists using the output of the listWafFile function

Parameters:
	name - File name. It is the file name without extension

Returns:
	Integer - It returns 1 if the file exists or 0 if it does not exist

=cut

sub existWAFFile
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $name = shift;

	my $exist = ( exists &listWAFFile()->{ $name } ) ? 1 : 0;

	return $exist;
}

=begin nd
Function: getWAFFileContent

	It gets the content of a file.

Parameters:
	Path - It is the absolute path to the file

Returns:
	String - Returns an string with the content of the file

=cut

sub getWAFFileContent
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $path    = shift;
	my $content = "";

	my $fh = &openlock( $path, 'r' );
	if ( $fh )
	{
		while ( <$fh> )
		{
			$content .= $_;
		}
	}
	close $fh;

	return $content;
}

=begin nd
Function: createWAFFile

	It creates a file with a lua script or data to be linked with the WAF rules.

Parameters:
	File struct. It is a hash reference with the following parameters:
		content - string with the content file
		name - name of the file
		type - the possible values for this field are 'script' or 'data'

Returns:
	Integer - It is the error code. 0 on success or another value on failure

=cut

sub createWAFFile
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $file = shift;
	my $err  = 0;

	if (    !exists $file->{ content }
		 or !exists $file->{ name }
		 or ( $file->{ type } !~ /^(?:data|script)$/ ) )
	{
		&zenlog( "The parameters to create a WAF file are not correct", 'error',
				 'waf' );
		return 1;
	}

	my $extension = ( $file->{ type } eq 'script' ) ? 'lua' : 'data';
	my $path      = "$wafFileDir/$file->{name}.$extension";
	my $log_tag   = ( -f $path ) ? "Overwritten" : "Created";

	my $fh = &openlock( $path, '>' ) or return 1;
	print $fh $file->{ content };
	close $fh;

	&zenlog( "$log_tag the WAF file '$path'", 'info', 'waf' );

	&logAndRun( "chmod +x $path " ) if ( $file->{ type } eq 'script' );

	return $err;
}

=begin nd
Function: deleteWAFFile

	It deletes a file of the WAF module.

Parameters:
	Path - It is the absolute path to the file

Returns:
	Integer - It is the error code. 0 on success or another value on failure

=cut

sub deleteWAFFile
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $path = shift;

	my $del = unlink $path;
	if ( $del )
	{
		&zenlog( "The file '$path' was deleted", 'info', 'waf' );
	}
	else
	{
		&zenlog( "The file '$path' could not be deleted", 'error', 'waf' );
	}

	return ( $del ) ? 0 : 1;
}

=begin nd
Function: checkWAFFileUsed

	It checks if some WAF rule is using a required file

Parameters:
	File name - It is the file name without extension and without path

Returns:
	Array ref - It is a list with all WAF rulesets are using the file

=cut

sub checkWAFFileUsed
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $name = shift;
	my @sets = ();

	opendir ( my $fd, $wafFileDir );

	foreach my $file ( readdir ( $fd ) )
	{
		next if ( $file !~ /\.conf$/ );

		my $fh = &openlock( "$wafFileDir/$file", 'r' );
		push @sets, $file if ( grep ( /\b$name\b/, <$fh> ) );
		close $fh;
	}
	closedir ( $fd );

	grep ( s/\.conf$//, @sets );
	return \@sets;
}

1;

