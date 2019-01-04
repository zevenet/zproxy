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

sub modify_logs_param
{
  my $err = 0;
  if ( $json_obj->{ logs } =~ /(?:true|false)/ )
  {
    $err = &setL4FarmParam( 'logs', $json_obj->{ logs }, $farmname );
  }
  else
  {
    my $msg = "Invalid value for logs parameter.";
  }

  if ( $err )
  {
    my $msg = "Error modifying the parameter logs.";
  }
  else
  {
    my $msg = "Logs feature not available.";
  }
  return $msg;
}

1;
