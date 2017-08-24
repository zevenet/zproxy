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

require "/usr/local/zevenet/www/functions_ext.cgi";
require "/usr/local/zevenet/www/farms_functions.cgi";
require "/usr/local/zevenet/www/networking_functions.cgi";
require "/usr/local/zevenet/www/nf_functions.cgi";
require "/usr/local/zevenet/www/zcluster_functions.cgi";
require "/usr/local/zevenet/www/rrd_functions.cgi";
require "/usr/local/zevenet/www/cert_functions.cgi";
require "/usr/local/zevenet/www/l4_functions.cgi";
require "/usr/local/zevenet/www/gslb_functions.cgi";
require "/usr/local/zevenet/www/system_functions.cgi";
require "/usr/local/zevenet/www/farmguardian_functions.cgi";
require "/usr/local/zevenet/www/datalink_functions.cgi";
require "/usr/local/zevenet/www/http_functions.cgi";
require "/usr/local/zevenet/www/zapi_functions.cgi";
require "/usr/local/zevenet/www/login_functions.cgi";
require "/usr/local/zevenet/www/snmp_functions.cgi";
require "/usr/local/zevenet/www/check_functions.cgi";  
require "/usr/local/zevenet/www/cgi_functions.cgi" if defined $ENV{GATEWAY_INTERFACE};

1;
