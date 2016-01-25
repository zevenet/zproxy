#!/usr/bin/perl
###############################################################################
#
#     This file is part of the Zen Load Balancer Enterprise Edition software
#     package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This file cannot be distributed, released in public domain and/or for
#     commercial purposes.
#
###############################################################################

require "/usr/local/zenloadbalancer/config/global.conf";
require "/usr/local/zenloadbalancer/www/functions.cgi";
require "/usr/local/zenloadbalancer/www/login_functions.cgi";
use CGI qw(:standard escapeHTML);

&login();

print "Content-type: text/html\n\n";

print "
<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<!---CSS Files-->
<link rel=\"stylesheet\" href=\"css/master.css\">
<link rel=\"stylesheet\" href=\"css/tables.css\">
<link rel=\"stylesheet\" href=\"/font/font-aw/css/font-awesome.min.css\">
<title>Upload certificate file</title></head>";

print "<body onUnload=\"opener.location=('index.cgi?id=1-3')\">";

print "<img src=\"img/logo.png\" alt=\"Logo\">";

print "<div class=\"container_12\">";
print "<div class=\"grid_12\">";

my $query      = new CGI;
my $upload_dir = $basedir;
my $action     = $query->param( "action" );
my $filename   = $query->param( "fileup" );

my $upload_filehandle = $query->upload( "fileup" );

if ( $action eq "Upload" && $filename !~ /^$/ )
{
	if ( $filename =~ /\.pem$/ )
	{
		if ( $filename =~ /\\/ )
		{
			@filen = split ( /\\/, $filename );
			$filename = $filen[-1];
		}

		open ( UPLOADFILE, ">$upload_dir/$filename" ) or die "$!";
		binmode UPLOADFILE;

		while ( <$upload_filehandle> )
		{
			print UPLOADFILE;
		}
		close UPLOADFILE;

		print "<br>";
		move( $filename, "zlbcertfile\.pem" );
		&successmsg( "File $filename uploaded!" );
	}
	else
	{
		print "<br>";
		&errormsg( "file withuot pem extension" );
	}
}

print "<br>";
print "<br>";

print
  "<form method=\"post\" action=\"uploadcertfile.cgi\" enctype=\"multipart/form-data\">";

print "<p><b>Upload an activaction certificate file (filename.pem)</b><br>";
print "<input type=\"file\" name=\"fileup\" value=\"Ex\" ></p>";
print "<br>";
print "<br>";
print
  "<input type=\"submit\" value=\"Upload\" name=\"action\" class=\"button grey\">";
print "</form>";

print "</div>";
print "</div>";

print "</body>";
print "</html>";

