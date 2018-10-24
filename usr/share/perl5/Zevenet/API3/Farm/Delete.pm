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

use strict;

# DELETE /farms/FARMNAME
sub delete_farm # ( $farmname )
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my $farmname = shift;

	unless ( &getFarmExists( $farmname ) )
	{
		&zenlog(
			 "Error, trying to delete the farm $farmname, the farm name doesn't exist.", "error", "FARMS"
		);

		# Error
		my $errormsg = "The farm $farmname doesn't exist, try another name.";
		my $body = {
					 description => "Delete farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		&runFarmStop( $farmname, "true" );
		include 'Zevenet::Cluster';
		&runZClusterRemoteManager( 'farm', 'stop', $farmname );
	}

	my $stat = &runFarmDelete( $farmname );

	if ( $stat == 0 )
	{
		&zenlog( "Success, the farm $farmname has been deleted.", "info", "FARMS" );

		# Success
		include 'Zevenet::Cluster';
		&runZClusterRemoteManager( 'farm', 'delete', $farmname );

		my $message = "The Farm $farmname has been deleted.";
		my $body = {
					 description => "Delete farm $farmname",
					 success     => "true",
					 message     => $message
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"Error trying to delete the farm $farmname, the farm hasn't been deleted.", "error", "FARMS"
		);

		# Error
		my $errormsg = "The Farm $farmname hasn't been deleted";
		my $body = {
					 description => "Delete farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

1;
