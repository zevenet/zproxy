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

$globalcfg = "/usr/local/zenloadbalancer/config/global.conf";

require "/usr/local/zenloadbalancer/www/farms_functions.cgi";
require "/usr/local/zenloadbalancer/www/networking_functions.cgi";
require "/usr/local/zenloadbalancer/www/nf_functions.cgi";
require "/usr/local/zenloadbalancer/www/cluster_functions.cgi";
require "/usr/local/zenloadbalancer/www/rrd_functions.cgi";
require "/usr/local/zenloadbalancer/www/cert_functions.cgi";
require "/usr/local/zenloadbalancer/www/l4_functions.cgi";
require "/usr/local/zenloadbalancer/www/gslb_functions.cgi";
require "/usr/local/zenloadbalancer/www/system_functions.cgi";
require "/usr/local/zenloadbalancer/www/gui_functions.cgi";
require "/usr/local/zenloadbalancer/www/snmp_functions.cgi";
require "/usr/local/zenloadbalancer/www/farmguardian_functions.cgi";
require "/usr/local/zenloadbalancer/www/datalink_functions.cgi";
require "/usr/local/zenloadbalancer/www/http_functions.cgi";
require "/usr/local/zenloadbalancer/www/tcpudp_functions.cgi";

if ( -e "/usr/local/zenloadbalancer/www/zapi_functions.cgi" )
{
	require "/usr/local/zenloadbalancer/www/zapi_functions.cgi";
}

if ( -e "/usr/local/zenloadbalancer/www/login_functions.cgi" )
{
	require "/usr/local/zenloadbalancer/www/login_functions.cgi";
}

#function that check if variable is a number no float
sub isnumber($num)
{
	my ( $num ) = @_;

	if ( $num !~ /[^0-9]/ )
	{
		return "true";
	}
	else
	{
		return "false";
	}
}

#check if the string is a valid multiport definition
sub ismport($string)
{
	my ( $string ) = @_;

	chomp ( $string );
	if ( $string eq "*" )
	{
		return "true";
	}
	elsif ( $string =~ /^[0-9]+(,[0-9]+|[0-9]+\:[0-9]+)*$/ )
	{
		return "true";
	}
	else
	{
		return "false";
	}
}

#check if the port has more than 1 port
sub checkmport($port)
{
	my ( $port ) = @_;

	if ( $port =~ /\,|\:|\*/ )
	{
		return "true";
	}
	else
	{
		return "false";
	}
}

#function that paint a static progess bar
sub progressbar($filename,$vbar)
{
	my ( $filename, $vbar ) = @_;
	$max = "150";

	# Create a new image
	use GD;
	$im = new GD::Image( $max, 12 );

	$white      = $im->colorAllocate( 255, 255, 255 );
	$blueborder = $im->colorAllocate( 77,  143, 204 );
	$grayborder = $im->colorAllocate( 102, 102, 102 );
	$blue       = $im->colorAllocate( 165, 192, 220 );
	$gray       = $im->colorAllocate( 156, 156, 156 );

	# Make the background transparent and interlaced
	$im->transparent( $white );
	$im->interlaced( 'true' );

	# Draw a border
	$im->rectangle( 0, 0, $max - 1, 11, $grayborder );

	#rectangle
	$im->filledRectangle( 1, 1, $vbar, 10, $grayborder );

	# Open a file for writing
	open ( PICTURE, ">$filename" ) or die ( "Cannot open file for writing" );

	# Make sure we are writing to a binary stream
	binmode PICTURE;

	# Convert the image to PNG and print it to the file PICTURE
	print PICTURE $im->png;
	close PICTURE;

}

#function that paint the date when started (uptime)
sub uptime()
{
	$timeseconds = time ();
	open TIME, '/proc/uptime' or die $!;

	#
	while ( <TIME> )
	{
		my @time = split ( "\ ", $_ );
		$uptimesec = @time[0];
	}

	$totaltime = $timeseconds - $uptimesec;

	#
	#my $time = time;       # or any other epoch timestamp
	my $time = $totaltime;
	my @months = (
				   "Jan", "Feb", "Mar", "Apr", "May", "Jun",
				   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
	);
	my ( $sec, $min, $hour, $day, $month, $year ) =
	  ( localtime ( $time ) )[0, 1, 2, 3, 4, 5, 6];

#print "Unix time ".$time." converts to ".$months[$month]." ".$day.", ".($year+1900) ." ". $hour .":".$min.":".$sec."\n";
	return
	    @months[$month] . ", "
	  . $day . " "
	  . $hour . ":"
	  . $min . ":"
	  . $sec . " "
	  . ( $year + 1900 ) . "\n";

}

#function that configure the graphs apareance.
#sub graphs(@data,$description)
sub graphs($description,@data)
{
	my ( $description, @data ) = @_;
	####graph configuration
	#midblue     => { R => 165,  G => 192, B => 220 },
	my %options = (

		#  	'file' => 'img/graphs/mygraph.jpg',
		#	'quality' => '9',
		# colours

		black      => { R => 0,   G => 0,   B => 0 },
		white      => { R => 255, G => 255, B => 255 },
		vltgrey    => { R => 245, G => 245, B => 245 },
		ltgrey     => { R => 230, G => 230, B => 230 },
		midgreen   => { R => 143, G => 184, B => 32 },
		midblue    => { R => 165, G => 192, B => 220 },
		midgray    => { R => 156, G => 156, B => 156 },
		background => { R => 244, G => 244, B => 244 },

		# file output details

		file    => $description,    # file path and name; file extension
		                            # can be .jpg|gif|png
		quality => 9,               # image quality: 1 (worst) - 10 (best)
		                            # Only applies to jpg and png

		# main image properties

		imgw     => 500,            # preferred width in pixels
		imgh     => 250,            # preferred height in pixels
		iplotpad => 8,              # padding between axis vals & plot area
		ipadding => 14,             # padding between other items
		ibgcol   => 'white',        # COLOUR NAME; background colour
		iborder  => '',             # COLOUR NAME; border, if any

		# plot area properties

		plinecol => 'midgrey',      # COLOUR NAME; line colour
		pflcol   => 'ltgrey',       # COLOUR NAME; floor colour
		pbgcol   => 'ltgrey',       # COLOUR NAME; back/side colour
		pbgfill  => 'gradient',     # 'gradient' or 'solid'; back/side fill
		plnspace => 25,             # minimum pixel spacing between divisions
		pnumdivs => 30,             # maximum number of y-axis divisions

		# bar properties

		bstyle      => 'bar',         # 'bar' or 'column' style
		bcolumnfill => 'gradient',    # 'gradient' or 'solid' for columns
		bminspace   => 18,            # minimum spacing between bars
		bwidth      => 18,            # width of bar
		bfacecol    => 'midgray',     # COLOUR NAME or 'random'; bar face,
		                              # 'random' for random bar face colour
		                              # graph title

		ttext    => '',               # title text
		tfont    => '',               # uses gdGiantFont unless a true type
		                              # font is specified
		tsize    => 10,               # font point size
		tfontcol => 'black',          # COLOUR NAME; font colour

		# axis labels

		xltext   => '',               # x-axis label text
		yltext   => '',               # y-axis label text
		lfont    => '',               # uses gdLargeFont unless a true type
		                              # font is specified
		lsize    => 10,               # font point size
		lfontcol => 'midblue',        # COLOUR NAME; font colour

		# axis values

		vfont    => '',               # uses gdSmallFont unless a true type
		                              # font is specified
		vsize    => 8,                # font point size
		vfontcol => 'black',          # COLOUR NAME; font colour

	);

	my $imagemap = creategraph( \@data, \%options );

}

sub upload()
{
	print "<script language=\"javascript\">
                var popupWindow = null;
                function positionedPopup(url,winName,w,h,t,l,scroll)
                {
                settings ='height='+h+',width='+w+',top='+t+',left='+l+',scrollbars='+scroll+',resizable'
                popupWindow = window.open(url,winName,settings)
                }
        </script>";

	#print the information icon with the popup with info.
	print "<a "
	  . "href=\"upload.cgi\" "
	  . "onclick=\"positionedPopup(this.href,'myWindow','500','300','100','200','yes');return false\">";
	print "<img src='img/icons/small/arrow_up.png' title=\"upload backup\"></a>";
}

sub uploadcerts()
{
	print "<script language=\"javascript\">
                var popupWindow = null;
                function positionedPopup(url,winName,w,h,t,l,scroll)
                {
                settings ='height='+h+',width='+w+',top='+t+',left='+l+',scrollbars='+scroll+',resizable'
                popupWindow = window.open(url,winName,settings)
                }
        </script>";

	#print the information icon with the popup with info.
	print "<a "
	  . "href=\"uploadcerts.cgi\" "
	  . "onclick=\"positionedPopup(this.href,'myWindow','500','300','100','200','yes');return false\">";
	print "<img src='img/icons/small/arrow_up.png' title=\"upload certificate\">";
	print "</a>";
}

#function that put a popup with help about the product
sub help($cod)
{
	#code
	my ( $cod ) = @_;

	#this is javascript emmbebed in perl
	print "<script language=\"javascript\">
                var popupWindow = null;
                function positionedPopup(url,winName,w,h,t,l,scroll)
                {
                settings ='height='+h+',width='+w+',top='+t+',left='+l+',scrollbars='+scroll+',resizable'
                popupWindow = window.open(url,winName,settings)
                }
        </script>";

	#print the information icon with the popup with info.
	print "<a href=\"help.cgi?id=$cod\" "
	  . "onclick=\"positionedPopup(this.href,'myWindow','500','300','100','200','yes');return false\">";
	print "<img src='img/icons/small/information.png'>";
	print "</a>";
}

#insert info in log file
sub logfile($string)
{
	my ( $string ) = @_;

	my $date = `date`;
	$date =~ s/\n//g;
	open FO, ">> $logfile";
	print FO
	  "$date - $ENV{'SERVER_NAME'} - $ENV{'REMOTE_ADDR'} - $ENV{'REMOTE_USER'} - $string\n";
	close FO;
}

#
#no remove this
1
