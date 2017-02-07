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

#~ use Sys::Syslog;                          #use of syslog
#~ use Sys::Syslog qw(:standard :macros);    #standard functions for Syslog
#~ use Fcntl ':flock';                       #use of lock functions
#~ use Tie::File;                            #use tie
#~ use Data::Dumper;

#~ $globalcfg = "/usr/local/zenloadbalancer/config/global.conf";

require "/usr/local/zenloadbalancer/www/functions_ext.cgi";
require "/usr/local/zenloadbalancer/www/farms_functions.cgi";
require "/usr/local/zenloadbalancer/www/networking_functions.cgi";
require "/usr/local/zenloadbalancer/www/nf_functions.cgi";
require "/usr/local/zenloadbalancer/www/zcluster_functions.cgi";
require "/usr/local/zenloadbalancer/www/rrd_functions.cgi";
require "/usr/local/zenloadbalancer/www/cert_functions.cgi";
require "/usr/local/zenloadbalancer/www/l4_functions.cgi";
require "/usr/local/zenloadbalancer/www/gslb_functions.cgi";
require "/usr/local/zenloadbalancer/www/system_functions.cgi";
require "/usr/local/zenloadbalancer/www/farmguardian_functions.cgi";
require "/usr/local/zenloadbalancer/www/datalink_functions.cgi";
require "/usr/local/zenloadbalancer/www/http_functions.cgi";
require "/usr/local/zenloadbalancer/www/tcpudp_functions.cgi";
require "/usr/local/zenloadbalancer/www/zapi_functions.cgi";
require "/usr/local/zenloadbalancer/www/login_functions.cgi";
require "/usr/local/zenloadbalancer/www/networking_functions_ext.cgi";
require "/usr/local/zenloadbalancer/www/snmp_functions.cgi";
require "/usr/local/zenloadbalancer/www/check_functions.cgi";  
require "/usr/local/zenloadbalancer/www/cgi_functions.cgi" if defined $ENV{GATEWAY_INTERFACE};

#function that check if variable is a number no float
sub isnumber    # ($num)
{
	my $num = shift;

	if ( $num =~ /^\d+$/ )    # \d = digit, equiv. to ([0-9])
	{
		return "true";
	}
	else
	{
		return "false";
	}
}

#function that paint the date when started (uptime)
sub uptime                    # ()
{
	$timeseconds = time ();
	open TIME, '/proc/uptime' or die $!;

	while ( <TIME> )
	{
		my @time = split ( "\ ", $_ );
		$uptimesec = $time[0];
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

	return
	    $months[$month] . ", "
	  . $day . " "
	  . $hour . ":"
	  . $min . ":"
	  . $sec . " "
	  . ( $year + 1900 ) . "\n";
}

#function that configure the graphs apareance.
sub graphs    # ($description,@data)
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
		background => { R => 238, G => 238, B => 238 },
		graybg     => { R => 238, G => 238, B => 238 },

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
		ibgcol   => 'graybg',       # COLOUR NAME; background colour
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

sub upload                            # ()
{
	print
	  "<a href=\"upload.cgi\" class=\"open-dialog\"><img src=\"img/icons/basic/up.png\" title=\"Upload backup\">Upload backup</a>";
	print
	  "<div id=\"dialog-container\" style=\"display: none;\"><iframe id=\"dialog\" width=\"350\" height=\"350\"></iframe></div>";
}

sub uploadcerts                       # ()
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
	print
	  "<a href=\"uploadcerts.cgi\" onclick=\"positionedPopup(this.href,'myWindow','500','300','100','200','yes');return false\"><img src='img/icons/small/arrow_up.png' title=\"upload certificate\"></a>";
}

1;
