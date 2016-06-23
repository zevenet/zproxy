###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, based in Sevilla (Spain)
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

package Skeleton;

#~ use strict;
#~ use warnings;

use Exporter qw(import);
our @EXPORT = qw(data);

#~ require "/usr/local/zenloadbalancer/config/global.conf";
#~ require "/usr/local/zenloadbalancer/www/functions.cgi";

our %data = (
	name => __PACKAGE__,

	content    => \&content,
	menu       => \&menu,
	zlbstart   => undef,
	zlbstop    => undef,
	startlocal => undef,
	stoplocal  => undef,

	startfarm => undef,
	stopfarm  => undef,

	position => \&position,
);

sub position
{
	my $position = 2;
	return $position;
}

sub menu
{
	my ( $idSession, $version ) = @_;
	my $output;
	my $url = "";

	my $fatherModuleId;
	my $idSessionMain;

	#	&main::zenlog("url: >$urlDocumentation<");

	# icono marcado
	my $monitoringiconclass = "";

	$data{ name } =~ /^(\w.*)/;
	$fatherModuleId = $1;

	#~ &main::zenlog( "1: >$idSession< eq >$fatherModuleId<" );

	$idSession =~ /^(\w.*)/;
	$idSessionMain = $1;

	#~ &main::zenlog( "2: >$idSessionMain< eq >$fatherModuleId<" );

	if ( $idSessionMain eq $fatherModuleId )
	{
		$monitoringiconclass = "active";
	}

# Copy this code for add a new submenu. Remember change IDVALUE, and CHANCEPAGE (this have to be unique)
#~ <li>
#~ <form action=\"index.cgi\" method=post name=\"changepage\">
#~ <input type=\"hidden\" name=\"id\" value=\"idvalue\"/>
#~ <a href=\"javascript:document.changepage.submit()\">Submenu</a>
#~ </form>
#~ </li>
	$output .= "
	  <li class=\"nav-item\">
		<a>
			<i class=\"fa fa-puzzle-piece $monitoringiconclass\"></i><p>$data{name}</p>
		</a>
	    <ul class=\"sub-nav\">	
			<li>					
				<form action=\"index.cgi\" method=post name=\"changepage\"> 
					<input type=\"hidden\" name=\"id\" value=\"Skeleton\"/> 					
					<a href=\"javascript:document.changepage.submit()\">Submenu</a>		
				</form>				
			</li>
        </ul>
	  </li>
	  ";

	return $output;
}

sub content
{
	my $output = "Mensaje de pruebas.\n";

	return $output;
}

&plugins::plugins( \%data );
1;
