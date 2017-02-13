###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This library is free software; you can redistribute it and/or modify it
#     under the terms of the GNU Lesser General Public License as published
#     by the Free Software Foundation; either version 2.1 of the License, or
#     (at your option) any later version.
#
#     This library is distributed in the hope that it will be useful, but
#     WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
#     General Public License for more details.
#
#     You should have received a copy of the GNU Lesser General Public License
#     along with this library; if not, write to the Free Software Foundation,
#     Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
###############################################################################

use strict;

#get zapi status
sub getZAPI    #($name)
{

	my ( $name ) = @_;
	my $result = "false";

	#return if zapi user is enabled or not true = enable, false = disabled
	if ( $name eq "status" )
	{
		use File::Grep qw( fgrep fmap fdo );
		if ( fgrep { /^zapi/ } &getGlobalConfiguration('htpass') )
		{
			$result = "true";
		}
	}
	if ( $name eq "keyzapi" )
	{
		$result = &getGlobalConfiguration ( 'zapikey' );
	}

	return $result;

}

#set zapi values

sub setZAPI    #($name,$value)
{

	my ( $name, $value ) = @_;
	my $result = "false";

	my $globalcfg = &getGlobalConfiguration('globalcfg');

	#Enable ZAPI
	if ( $name eq "enable" )
	{

		my @run =
		  `adduser --system --shell /bin/false --no-create-home zapi 1> /dev/null 2> /dev/null`;
		return $?;
	}

	#Disable ZAPI
	if ( $name eq "disable" )
	{

		my @run = `deluser zapi 1> /dev/null 2> /dev/null`;
		return $?;

	}

	#Set Random key for zapi
	if ( $name eq "randomkey" )
	{
		my $random = &setZAPIKey( 64 );
		tie my @contents, 'Tie::File', "$globalcfg";
		foreach my $line ( @contents )
		{
			if ( $line =~ /zapi/ )
			{
				$line =~ s/^\$zapikey.*/\$zapikey="$random"\;/g;
			}
		}
		untie @contents;

	}

	#Set ZAPI KEY
	if ( $name eq "key" )
	{
		tie my @contents, 'Tie::File', "$globalcfg";
		foreach my $line ( @contents )
		{
			if ( $line =~ /zapi/ )
			{
				$line =~ s/^\$zapikey.*/\$zapikey="$value"\;/g;
			}
		}
		untie @contents;

	}

}

#Generate random key for API user
sub setZAPIKey    #()
{
	my $passwordsize = shift;
	my @alphanumeric = ( 'a' .. 'z', 'A' .. 'Z', 0 .. 9 );
	my $randpassword = join '', map $alphanumeric[rand @alphanumeric],
	  0 .. $passwordsize;

	return $randpassword;
}

# do not remove this
1;
