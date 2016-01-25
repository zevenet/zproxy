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

#header secction
use Sys::Hostname;
my $host = hostname();
$timeseconds = time ();

$now = ctime();

my @months = (
			   "Jan", "Feb", "Mar", "Apr", "May", "Jun",
			   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
);
my ( $sec, $min, $hour, $day, $month, $year ) =
  ( localtime ( $time ) )[0, 1, 2, 3, 4, 5, 6];
$month = $months[$month];
$year  = $year + 1900;

#print "$month $day $year $hour:$min:$sec\n";
print "
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
";

if ( $refresh )
{
	print "<meta http-equiv=\"refresh\" content=\"$refresh\">";
}

print "
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/>
  <!---CSS Files-->
  <link rel=\"stylesheet\" href=\"css/master.css\">
  <link rel=\"stylesheet\" href=\"css/tables.css\">
  <link rel='stylesheet' href='/font/font-aw/css/font-awesome.min.css'>
  <!---jQuery Files-->
  <script src=\"js/jquery-1.7.1.min.js\"></script>
  <script src=\"js/jquery-ui-1.8.17.min.js\"></script>
  <script src=\"js/styler.js\"></script>
  <script src=\"js/jquery.tipTip.js\"></script>
  <script src=\"js/colorpicker.js\"></script>
  <script src=\"js/sticky.full.js\"></script>
  <script src=\"js/global.js\"></script>
  <script src=\"js/flot/jquery.flot.min.js\"></script>
  <script src=\"js/flot/jquery.flot.resize.min.js\"></script>
  <script src=\"js/jquery.dataTables.min.js\"></script>
  <script src=\"js/forms/fileinput.js\"></script>
  <!---Fonts-->
  <link href='https://fonts.googleapis.com/css?family=Open+Sans:300,400,600,700' rel='stylesheet' type='text/css'>
  <link href='https://fonts.googleapis.com/css?family=Ubuntu:500' rel='stylesheet' type='text/css'>
  <!--[if lt IE 9]>
  <script src=\"https://html5shiv.googlecode.com/svn/trunk/html5.js\"></script>
  <![endif]-->
  <!--[if lte IE 8]>
  <script language=\"javascript\" type=\"text/javascript\" src=\"js/flot/excanvas.min.js\"></script>
  <![endif]-->
  <title>ZEN Load Balancer GUI v$version on $host</title>
  <link href=\"/img/favicon.ico\" rel=\"icon\" type=\"image/x-icon\" />
</head>
<body>
  <!--<div id=\"cover\"></div>-->
  <!--- HEADER -->
  <div class=\"header\">
    <a href=\"/index.cgi\"><img src=\"img/logo.png\" alt=\"Logo\" /></a>
  </div>";

