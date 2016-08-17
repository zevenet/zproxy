#!/usr/bin/perl

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

use Sys::Syslog;                          #use of syslog
use Sys::Syslog qw(:standard :macros);    #standard functions for Syslog

(my $msg) = @ARGV;
&zenlog($msg);

#function that insert info through syslog
#
#&zenlog($priority,$text);
#
#examples
#&zenlog("info","This is test.");
#&zenlog("err","Some errors happended.");
#&zenlog("debug","testing debug mode");
#
sub zenlog    # ($type,$string)
{
	my $string = shift;            # string = message
	my $type = shift // 'info';    # type   = log level (Default: info))

	# Get the program name
	my $program = "sec";

	openlog( $program, 'pid', 'local0' );    #open syslog

	my @lines = split /\n/, $string;

	foreach my $line ( @lines )
	{
		syslog( $type, "(" . uc ( $type ) . ") " . $line );
	}

	closelog();                              #close syslog
}


1;
