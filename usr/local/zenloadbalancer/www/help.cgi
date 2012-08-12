#!/usr/bin/perl
#This cgi is part of Zen Load Balancer, is a Web GUI integrated with binary systems that
#create Highly Effective Bandwidth Managemen
#Copyright (C) 2010  Emilio Campos Martin / Laura Garcia Liebana
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You can read license.txt file for more information.

#Created by Emilio Campos Martin
#File that create the Zen Load Balancer GUI


use CGI qw(:standard escapeHTML);
print "Content-type: text/html\n\n";

##REQUIRES
require "help-content.cgi";

#loading form variables
my(%Variables); #reset hash
#read query send get
my $buffer = $ENV{'QUERY_STRING'};


#split variable post
my @pairs = split(/&/, $buffer);
foreach my $pair (@pairs)
{
#separate variable with its name
        my ($name, $value) = split(/=/, $pair);

        #
        $name =~ tr/+/ /;
        $name =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
        $value =~ tr/+/ /;
        $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
        #get method
        #keys for values
        $Variables{$name} = $value;
}
#variables in get string
$id = $Variables{'id'};

print "
<HTML>
<head>
<meta http-equiv=\"content-type\" content=\"text/html; charset=utf-8\" />

<link type=\"text/css\" rel=\"stylesheet\" media=\"all\" href=\"css/base.css\" />
<link type=\"text/css\" rel=\"stylesheet\" media=\"all\" href=\"css/grid.css\" />
<title>Help</title></head>";

$id=1;
print "<BODY>";
print "<div id=\"header\">
	 <div class=\"header-top tr\">
	 $header[$id]
	 </div>
      </div>";

print "$body[$id]";
print "<br>";
print "</BODY>";
print "</HTML>"; 

