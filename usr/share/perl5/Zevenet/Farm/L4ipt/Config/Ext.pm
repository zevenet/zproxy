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
require Zevenet::Farm::Core;
require Zevenet::Config;

sub setL4FarmLogsExt
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname = shift;
	my $action   = shift;    # true or false
	my $out;

  require Zevenet::Config;
  my $configdir = &getGlobalConfiguration( 'configdir' );


	# execute action
	&reloadL4FarmLogsRule( $farmname, $action );

	# write configuration
	require Tie::File;
	my $farm_filename = &getFarmFile( $farmname );
	tie my @configfile, 'Tie::File', "$configdir\/$farm_filename";

	my $i = 0;
	for my $line ( @configfile )
	{
		if ( $line =~ /^$farmname\;/ )
		{
			my @args = split ( "\;", $line );
			$line =
			  "$args[0]\;$args[1]\;$args[2]\;$args[3]\;$args[4]\;$args[5]\;$args[6]\;$args[7]\;$args[8]\;$action";
			splice @configfile, $i, $line;
		}
		$i++;
	}
	untie @configfile;

	return $out;
}

sub modifyLogsParam
{
  my $farmname  = shift;
  my $logsValue = shift;

  my $msg;
  my $err = 0;
  if ( $logsValue =~ /(?:true|false)/ )
  {
    $err = &setL4FarmLogsExt( $farmname, $logsValue );
  }
  else
  {
    $msg = "Invalid value for logs parameter.";
  }

  if ( $err )
  {
    $msg = "Error modifying the parameter logs.";
  }
  return $msg;
}

# if action is false, the rule won't be started
# if farm is in down status, the farm won't be started

sub reloadL4FarmLogsRule
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farmname, $action ) = @_;
  require Zevenet::Farm::L4xNAT::Config;
	require Zevenet::Netfilter;

	my $error;
	my $table     = "mangle";
	my $ipt_hook  = "FORWARD";
	my $log_chain = "LOG_CONNS";
	my $bin       = &getBinVersion( $farmname );
	my $farm      = &getL4FarmStruct( $farmname );

	my $comment = "conns,$farmname";

	# delete current rules
	&runIptDeleteByComment( $comment, $log_chain, $table );

	# delete chain if it was the last rule
	my @ipt_list = `$bin -S $log_chain -t $table 2>/dev/null`;
	my $err      = $?;

	# If the CHAIN is created, has a rule: -N LOG_CONNS
	if ( scalar @ipt_list <= 1 and !$err )
	{
		&iptSystem( "$bin -D $ipt_hook -t $table -j $log_chain" );
		&iptSystem( "$bin -X $log_chain -t $table" );
	}

	# not to apply rules if:
	return if ( $action eq 'false' );
	return
	  if ( &getL4FarmParam( 'logs', $farmname ) ne "true" and $action ne "true" );
	return if ( &getL4FarmParam( 'status', $farmname ) ne 'up' );

	my $comment_tag = "-m comment --comment \"$comment\"";
	my $log_tag     = "-j LOG --log-prefix \"l4: $farmname \" --log-level 4";

	# create chain if it does not exist
	if ( &iptSystem( "$bin -S $log_chain -t $table" ) )
	{
		$error = &iptSystem( "$bin -N $log_chain -t $table" );
		$error = &iptSystem( "$bin -A $ipt_hook -t $table -j $log_chain" );
	}

	my %farm_st = %{ &getL4FarmStruct( $farmname ) };
	foreach my $bk ( @{ $farm_st{ servers } } )
	{
		my $mark = "-m mark --mark $bk->{tag}";

		# log only the new connections
		if ( &getGlobalConfiguration( 'full_farm_logs' ) ne 'true' )
		{
			$error |= &iptSystem(
				 "$bin -A $log_chain -t $table -m state --state NEW $mark $log_tag $comment_tag"
			);
		}

		# log all trace
		else
		{
			$error |=
			  &iptSystem( "$bin -A $log_chain -t $table $mark $log_tag $comment_tag" );
		}
	}

}

1;
