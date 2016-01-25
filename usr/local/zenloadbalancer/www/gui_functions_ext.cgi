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

# create the menu to manage the farm
sub createMenuVip_ext    # ($farm_name)
{
	my $farm_name = shift;

	if ( &getFarmStatus( $farm_name ) eq 'up' )
	{
		# stop farm
		print "
		<form method=\"post\" action=\"index.cgi\" class=\"myform\">
		<button type=\"submit\" class=\"myicons\" title=\"Stop the $farm_name Farm\" onclick=\"return confirm('Are you sure you want to stop the farm: $farm_name?')\">
			<i class=\"fa fa-minus-circle action-icon fa-fw red\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"$id\">
		<input type=\"hidden\" name=\"action\" value=\"stopfarm\">
		<input type=\"hidden\" name=\"farmname\" value=\"$farm_name\">
		</form>";
	}
	else
	{
		# start farm
		print "
		<form method=\"post\" action=\"index.cgi\" class=\"myform\">
		<button type=\"submit\" class=\"myicons\" title=\"Start the $farm_name Farm\">
			<i class=\"fa fa-play-circle action-icon fa-fw green\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"$id\">
		<input type=\"hidden\" name=\"action\" value=\"startfarm\">
		<input type=\"hidden\" name=\"farmname\" value=\"$farm_name\">
		</form>";
	}

	# edit farm
	print "
		<form method=\"post\" action=\"index.cgi\" class=\"myform\">
		<button type=\"submit\" class=\"myicons\" title=\"Edit the $farm_name Farm\">
			<i class=\"fa fa-pencil-square-o action-icon fa-fw\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"$id\">
		<input type=\"hidden\" name=\"action\" value=\"editfarm\">
		<input type=\"hidden\" name=\"farmname\" value=\"$farm_name\">
		</form>"

	  # in any case with one exception: tcp farms which are down
	  unless (    &getFarmType( $farm_name ) eq 'tcp'
			   && &getFarmStatus( $farm_name ) eq 'down' );

	# delete farm
	print "
		<form method=\"post\" action=\"index.cgi\" class=\"myform\">
		<button type=\"submit\" class=\"myicons\" title=\"Delete the $farm_name Farm\" onclick=\"return confirm('Are you sure you wish to delete the farm: $farm_name?')\">
			<i class=\"fa fa-times-circle action-icon fa-fw red\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"$id\">
		<input type=\"hidden\" name=\"action\" value=\"deletefarm\">
		<input type=\"hidden\" name=\"farmname\" value=\"$farm_name\">
		</form>";
}

# do not remove this
1
