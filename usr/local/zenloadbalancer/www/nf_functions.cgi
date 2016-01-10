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

use Data::Dumper;

#
sub loadNfModule    # ($modname,$params)
{
	my ( $modname, $params ) = @_;

	my $status  = 0;
	my @modules = `$lsmod`;

	if ( !grep { /^$modname /x } @modules )
	{
		my $modprobe_command = "$modprobe $modname $params";

		&logfile( "L4 loadNfModule: $modprobe_command" );
		system ( "$modprobe_command >/dev/null 2>&1" );
		$status = $?;
	}

	return $status;
}

#
sub removeNfModule    # ($modname)
{
	my $modname = shift;

	my $modprobe_command = "$modprobe -r $modname";

	&logfile( "L4 removeNfModule: $modprobe_command" );
	return system ( "$modprobe_command >/dev/null 2>&1" );
}

#
sub getIptFilter      # ($type, $desc, @iptables)
{
	my ( $type, $desc, @iptables ) = @_;    # input args

	my @selected_rules;

	@selected_rules = grep { / FARM\_$desc\_.* /x } @iptables
	  if ( $type eq 'farm' );

	# FIXME: cannot return conditionally
	return @selected_rules;
}

#
sub getIptList                              # ($table,$chain)
{
	my ( $table, $chain ) = @_;

	if ( $table ne "" )
	{
		$table = "--table $table";
	}

	my $iptables_command = "$iptables $table -L $chain -n -v --line-numbers";

	&logfile( $iptables_command );

	return `$iptables_command`;
}

#
sub deleteIptRules    # ($type,$desc,$table,$chain,@allrules)
{
	my ( $type, $desc, $table, $chain, @allrules ) = @_;

	my $status = 0;
	my @rules = &getIptFilter( $type, $desc, @allrules );

	# do not change rules id starting by the end
	chomp ( @rules = reverse ( @rules ) );
	foreach my $rule ( @rules )
	{
		my @sprule = split ( "\ ", $rule );
		if ( $type eq "farm" )
		{
			my $iptables_command = "$iptables --table $table --delete $chain $sprule[0]";

			&logfile( "deleteIptRules:: running '$iptables_command'" );
			system ( "$iptables_command >/dev/null 2>&1" );

			#~ &logfile( "deleteIptRules:: delete netfilter rule '$rule'" );

			$status = $status + $?;
		}
	}

	return $status;
}

#
sub getNewMark    # ($farm_name)
{
	my $farm_name = shift;

	my $found;
	my $marknum = 0x200;

	tie my @contents, 'Tie::File', "$fwmarksconf";

	for my $i ( 512 .. 1023 )
	{
		# end loop if found
		last if defined $found;

		my $num = sprintf ( "0x%x", $i );
		my $num = $i;
		if ( !grep { /^$num/x } @contents )
		{
			$found   = 'true';
			$marknum = $num;
		}
	}

	untie @contents;

	if ( $found eq 'true' )
	{
		open ( my $marksfile, ">>", "$fwmarksconf" );
		print $marksfile "$marknum // FARM\_$farm_name\_\n";
		close $marksfile;
	}

	return $marknum;
}

#
sub delMarks    # ($farm_name,$mark)
{
	my ( $farm_name, $mark ) = @_;

	my $status = 0;

	if ( $farm_name ne "" )
	{
		tie my @contents, 'Tie::File', "$fwmarksconf";
		@contents = grep { !/ \/\/ FARM\_$farm_name\_$/x } @contents;
		$status = $?;
		untie @contents;
	}

	if ( $mark ne "" )
	{
		tie my @contents, 'Tie::File', "$fwmarksconf";
		@contents = grep { !/^$mark \/\//x } @contents;
		$status = $?;
		untie @contents;
	}

	return $status;
}

#
sub renameMarks    # ($farm_name,$newfname)
{
	my ( $farm_name, $newfname ) = @_;

	my $status = 0;

	if ( $farm_name ne "" )
	{
		tie my @contents, 'Tie::File', "$fwmarksconf";
		foreach my $line ( @contents )
		{
			$line =~ s/ \/\/ FARM\_$farm_name\_/ \/\/ FARM\_$newfname\_/x;
		}
		$status = $?;
		untie @contents;
	}

	return $status;
}

#
sub genIptMarkPersist    # ($farm_name,$vip,$vport,$protocol,$ttl,$index,$mark)
{
	# remove the first line when all calls to this function are passing
	# structure references
	my ( $farm_name, $vip, $vport, $protocol, $ttl, $index, $mark ) = @_;

	my $farm   = shift;    # input: first argument can be a farm reference
	my $server = shift;    # input: second argument can be a server reference
	my $rule;              # output: iptables rule template string

	if ( defined $index )
	{
		$farm   = &getL4FarmStruct( $farm_name );
		$server = $$farm{ servers }[$index];
	}

	my $layer = '';
	if ( $$farm{ proto } ne 'all' )
	{
		$layer = "--protocol $$farm{ proto } -m multiport --dports $$farm{ vport }";
	}

	$rule = "$iptables --table mangle --::ACTION_TAG:: PREROUTING "

	  . "--destination $$farm{ vip } "

	  #~ . "$layer "

	  . "--match recent --name \"\_$$farm{ name }\_$$server{ tag }\_sessions\" --rcheck --seconds $$farm{ ttl } "

	  #~ . "--match state ! --state NEW "    # new
	  . "$layer "
	  . "--match comment --comment ' FARM\_$$farm{ name }\_$$server{ id }\_ ' "
	  . "--jump MARK --set-xmark $$server{ tag } ";    # new
	    #~ . "--jump MARK --set-mark $$server{ tag } ";	# old

	#~ &logfile( $rule );
	return $rule;
}

#
sub genIptMark # ($farm_name,$lbalg,$vip,$vport,$protocol,$index,$mark,$value,$prob)
{
	# remove the first line when all calls to this function are passing
	# structure references
	my ( $farm_name, $lbalg, $vip, $vport, $protocol, $index, $mark, $value, $prob )
	  = @_;

	my $farm   = shift;    # input: first argument should be a farm reference
	my $server = shift;    # input: second argument should be a server reference
	my $rule;              # output: iptables rule template string

	# for compatibility with previous function call
	if ( defined $index )
	{
		$farm   = &getL4FarmStruct( $farm_name );
		$server = $$farm{ servers }[$index];
	}

	my $layer;
	if ( $$farm{ proto } ne 'all' )
	{
		$layer = "--protocol $$farm{ proto } -m multiport --dports $$farm{ vport }";
	}

	# Every rule starts with:
	# table, chain, destination(farm ip) and port(if required) definition
	$rule = "$iptables --table mangle --::ACTION_TAG:: PREROUTING "

	  #~ . "--destination $$farm{ vip } " . "$layer "
	  ;

	if ( $$farm{ lbalg } eq 'weight' )
	{
		$rule .= "--match statistic --mode random --probability $$server{ prob } ";
	}

	if ( $$farm{ lbalg } eq 'leastconn' )
	{
		$rule .= "--match condition --condition '\_$$farm{ name }\_$$server{ tag }\_' ";

	}

	#~ if ( $$farm{ lbalg } eq 'prio' )
	#~ {
	#~ $rule = $rule;
	#~ }

	# include for every rule:
	# - match new packets/connections
	# - add comment with farm name and backend id number
	# - set mark
	$rule = $rule

	  #~ . "--match state --state NEW "    # new
	  . "--destination $$farm{ vip } "
	  . "$layer "
	  . "--match comment --comment ' FARM\_$$farm{ name }\_$$server{ id }\_ ' "
	  . "--jump MARK --set-xmark $$server{ tag } ";    # new
	    #~ . "--jump MARK --set-mark $$server{ tag } ";	# old

	#~ &logfile( $rule );
	return $rule;
}

#
sub genIptRedirect    # ($farm_name,$index,$rip,$protocol,$mark,$persist)
{
	# remove the first line when all calls to this function are passing
	# structure references
	my ( $farm_name, $index, $vip, $vport, $protocol, $mark, $persist ) = @_;

	my $farm   = shift;    # input: first argument can be a farm reference
	my $server = shift;    # input: second argument can be a server reference
	my $rule;              # output: iptables rule template string

	if ( defined $vip )
	{
		$farm   = &getL4FarmStruct( $farm_name );
		$server = $$farm{ servers }[$index];
	}

	my $layer = '';
	my $rip   = $$farm{ vip };

	if ( $$farm{ proto } ne "all" )
	{
		$layer = "--protocol $$farm{ proto }";
		$rip   = "$rip:$$farm{ vport }";
	}

	my $persist_match = '';
	if ( $$farm{ persist } ne "none" )
	{
		$persist_match =
		  "--match recent --name \"\_$$farm{ name }\_$$server{ tag }\_sessions\" --set";
	}

	$rule =
	    "$iptables --table nat --::ACTION_TAG:: PREROUTING "
	  . "--match mark --mark $$server{ tag } "
	  . "$persist_match "
	  . "--match comment --comment ' FARM\_$$farm{ name }\_$$server{ id }\_ ' "
	  . "--jump DNAT $layer --to-destination $$server{ rip } ";

	#~ &logfile( $rule );
	return $rule;
}

#
sub genIptSourceNat    # ($farm_name,$vip,$index,$protocol,$mark)
{
	# remove the first line when all calls to this function are passing
	# structure references
	my ( $farm_name, $vip, $index, $protocol, $mark ) = @_;

	my $farm   = shift;    # input: first argument can be a farm reference
	my $server = shift;    # input: second argument can be a server reference
	my $rule;              # output: iptables rule template string

	if ( defined $index )
	{
		$farm   = &getL4FarmStruct( $farm_name );
		$server = $$farm{ servers }[$index];
	}

	my $layer = '';
	if ( $$farm{ proto } ne "all" )
	{
		$layer = "--protocol $$farm{ proto }";
	}

	$rule =
	    "$iptables --table nat --::ACTION_TAG:: POSTROUTING "
	  . "--match mark --mark $$server{ tag } "
	  . "--match comment --comment ' FARM\_$$farm{ name }\_$$server{ id }\_ ' "
	  . "--jump SNAT $layer --to-source $$server{ vip } ";

	#~ &logfile( $rule );
	return $rule;
}

#
sub genIptMasquerade    # ($farm_name,$index,$protocol,$mark)
{
	# remove the first line when all calls to this function are passing
	# structure references
	my ( $farm_name, $index, $protocol, $mark ) = @_;

	my $farm   = shift;    # input: first argument can be a farm reference
	my $server = shift;    # input: second argument can be a server reference
	my $rule;              # output: iptables rule template string

	if ( defined $protocol )
	{
		$farm   = &getL4FarmStruct( $farm_name );
		$server = $$farm{ servers }[$index];
	}

	my $layer = '';
	if ( $$farm{ proto } ne "all" )
	{
		$layer = "--protocol $$farm{ proto }";
	}

	$rule =
	    "$iptables --table nat --::ACTION_TAG:: POSTROUTING "
	  . "$layer "
	  . "--match mark --mark $$server{ tag } "
	  . "--match comment --comment ' FARM\_$$farm{ name }\_$$server{ id }\_ ' "
	  . "--jump MASQUERADE ";

	#~ &logfile( $rule );
	return $rule;
}

#
sub getConntrack    # ($orig_src, $orig_dst, $reply_src, $reply_dst, $protocol)
{
	my ( $orig_src, $orig_dst, $reply_src, $reply_dst, $protocol ) = @_;

	# remove newlines in every argument
	chomp ( $orig_src, $orig_dst, $reply_src, $reply_dst, $protocol );

	# add iptables options to every available value
	$orig_src  = "-s $orig_src"  if ( $orig_src );
	$orig_dst  = "-d $orig_dst"  if ( $orig_dst );
	$reply_src = "-r $reply_src" if ( $reply_src );
	$reply_dst = "-q $reply_dst" if ( $reply_dst );
	$protocol  = "-p $protocol"  if ( $protocol );

	my $conntrack_cmd =
	  "$conntrack -L $orig_src $orig_dst $reply_src $reply_dst $protocol 2>/dev/null";

	#~ &logfile( $conntrack_cmd );
	return `$conntrack_cmd`;
}

# insert restore mark on top of
sub getIptStringConnmarkRestore
{
	return "$iptables --table mangle --::ACTION_TAG:: PREROUTING "
	  . "--jump CONNMARK --restore-mark ";

	#~ . "--nfmask 0xffffffff --ctmask 0xffffffff "
}

# append restore mark at the end of
sub getIptStringConnmarkSave
{
	return
	    "$iptables --table mangle --::ACTION_TAG:: PREROUTING "
	  . "--match state --state NEW "
	  . "--jump CONNMARK --save-mark ";

	#~ . "--nfmask 0xffffffff --ctmask 0xffffffff "

}

sub setIptConnmarkRestore
{
	my $switch      = shift;    # 'true' or not true value
	my $return_code = -1;       # return value

	my $rule = &getIptStringConnmarkRestore();
	my $restore_on = ( &logAndRun( &applyIptRuleAction( $rule, 'check' ) ) == 0 );

	# if want to set it on but not already on
	if ( $switch eq 'true' && !$restore_on )
	{
		$return_code = &logAndRun( &applyIptRuleAction( $rule, 'insert' ) );
	}

	# if want to turn it off, is on and only one farm needs it
	elsif (    $switch ne 'true'
			&& $restore_on
			&& &getNumberOfFarmTypeRunning( 'l4xnat' ) == 0 )
	{
		$return_code = &logAndRun( &applyIptRuleAction( $rule, 'delete' ) );
	}

	return $return_code;
}

sub setIptConnmarkSave
{
	my $switch      = shift;    # 'true' or not true value
	my $return_code = -1;       # return value

	my $rule = &getIptStringConnmarkSave();
	my $restore_on = ( &logAndRun( &applyIptRuleAction( $rule, 'check' ) ) == 0 );

	# if want to set it on but not already on
	if ( $switch eq 'true' && !$restore_on )
	{
		$return_code = &logAndRun( &applyIptRuleAction( $rule, 'append' ) );
	}

	# if want to turn it off, is on and only one farm needs it
	elsif (    $switch ne 'true'
			&& $restore_on
			&& &getNumberOfFarmTypeRunning( 'l4xnat' ) == 0 )
	{
		$return_code = &logAndRun( &applyIptRuleAction( $rule, 'delete' ) );
	}

	return $return_code;
}

sub applyIptRuleAction
{
	my $rule    = shift;    # rule string with ::ACTION_TAG:: instead of action
	my $action  = shift;    # must be append|check|delete|insert|replace
	my $rulenum = shift;    # input: optional

	# return the action requested if not supported
	return $action if $action !~ /append|check|delete|insert|replace/x;

	if ( $action =~ /insert|replace|delete/ && defined $rulenum )
	{
		my @rule_args = split ( ' ', $rule );

		# include rule number in 5th position in the string
		splice @rule_args, 5, 0, $rulenum;
		$rule = ( $action eq 'delete' )
		  ? join ( ' ', @rule_args[0 .. 5] )    # delete rule number
		  : join ( ' ', @rule_args );           # include rule number
	}
	elsif ( $action eq 'replace' && !defined $rulenum )
	{
		&logfile( 'Error: Iptables \'replace\' action requires a rule number' );
	}

	# applied for any accepted action
	$rule =~ s/::ACTION_TAG::/$action/x;

	&logfile( "<< applyIptRuleAction:{action:$action,rulenum:$rulenum} $rule" ); ###

	return $rule;
}

sub getIptRuleNumber
{
	my (
		 $rule,         # rule string
		 $farm_name,    # farm name string
		 $index         # backend index number. OPTIONAL
	) = @_;

	( defined ( $rule ) && $rule ne '' )
	  or &logfile( ( caller ( 0 ) )[3] . ' $rule invalid' );
	( defined ( $farm_name ) && !ref $farm_name )
	  or &logfile( ( caller ( 0 ) )[3] . ' $farm_name invalid' );
	( defined ( $index ) && !ref $index )
	  or &logfile( ( caller ( 0 ) )[3] . ' $index invalid' );

	my $rule_num;      # output: rule number for requested rule

	# read rule table and chain
	my @rule_args = split / +/, $rule;    # ignore blanks
	my $table     = $rule_args[2];        # second argument of iptables is the table
	my $chain     = $rule_args[4];        # forth argument of iptables is the chain

	my $ipt_cmd = "$iptables --numeric --line-number --table $table --list $chain";
	my $filter;

	if ( defined ( $index ) )
	{
		my $farm = &getL4FarmStruct( $farm_name );
		$filter = $$farm{ servers }[$index]{ tag };
	}
	else
	{
		$filter = "FARM\_$farm_name\_";

		#~ $comment = $comment . "$index\_" if defined ( $index );
	}

	# pick rule by farm and optionally server id
	my @rules = grep { /$filter/ } `$ipt_cmd`;
	chomp ( @rules );

	# only for marking tags, when ip persistance is enabled
	if ( scalar @rules > 1 )
	{
		if ( $rule =~ /--match recent/ )    # for persistence rules
		{
			@rules = grep { /recent: CHECK/ } @rules;
		}
		else                                # for non persistence rules
		{
			@rules = grep { !/recent: CHECK/ } @rules;
		}
	}

	# take the first value (rule number)
	# e.g.: 1    DNAT       all  --  0.0.0.0/0 ...
	# if no rule was found: return -1
	$rule_num = ( split / +/, $rules[0] )[0] // -1;

	return $rule_num;
}

# apply every rule in the input
sub applyIptRules
{
	my @rules       = @_;    # input: rule array
	my $return_code = -1;    # output:

	foreach $rule ( @rules )
	{
		# skip cycle if $rule empty
		next if not $rule or $rule !~ 'iptables';

		$return_code = &logAndRun( $rule );
	}

	return $return_code;     # FIXME: make a proper return code control
}

########################################################################
sub setIptRuleCheck
{
	my $rule = shift;        # input: iptables rule string

	return &applyIptRules( &getIptRuleCheck( $rule ) );
}

sub getIptRuleCheck
{
	my $rule = shift;        # input: iptables rule string

	return &applyIptRuleAction( $rule, 'check' );
}
####################
sub setIptRuleInsert
{
	my $farm     = shift;    # input: farm struc reference
	my $server   = shift;    # input: server struc reference
	my $rule     = shift;    # input: iptables rule string
	my $rule_num = shift;    # input: possition to insert the rule

	return &applyIptRules( &getIptRuleInsert( $rule, $rule_num ) );
}

sub getIptRuleInsert
{
	my $farm     = shift;    # input: farm struc reference
	my $server   = shift;    # input: server struc reference
	my $rule     = shift;    # input: iptables rule string
	my $rule_num = shift;    # input(optional): possition to insert the rule

	if ( ( not defined $rule_num ) || $rule_num eq '' )
	{
		# FIXME: insert rule in proper place
		# by default insert in 2nd position to skip CONNMARK rule if applies
		$rule_num = 2;

		# do not insert a rule on a position higher than this, iptable will fail
		my $rule_max_position;

		{    # calculate rule_max_position
			    # read rule table and chain
			my @rule_args = split / +/, $rule;
			my $table     = $rule_args[2];       # second argument of iptables is the table
			my $chain     = $rule_args[4];       # forth argument of iptables is the chain

			my @rule_list = `$iptables -n --line-number --table $table --list $chain`;
			$rule_max_position = ( scalar @rule_list ) - 1;

			if ( $table eq 'mangle' && $rule =~ /--match recent/ )
			{
				@rule_list = grep { /recent: CHECK/ } @rule_list;

				&logfile( "getIptRuleInsert: @rule_list" );    ########

				@rule_args = split / +/, $rule_list[0];
				my $recent_rule_num = $rule_args[0];
				$rule_num = $recent_rule_num if $recent_rule_num > $rule_num;
			}
		}

		$rulenum = $rule_max_position if $rule_max_position < $rule_num;
	}

	# if the rule does not exist
	if ( &setIptRuleCheck( $rule ) != 0 )                      # 256
	{
		$rule = &applyIptRuleAction( $rule, 'insert', $rule_num );
		return $rule;
	}
	else    # if the rule exist replace it.
	{
		$rule = &setIptRuleReplace( $farm, $server, $rule );
	}
	return;    # do not return a rule if the rule already exist
}
####################
sub setIptRuleDelete
{
	my $rule = shift;    # input: iptables rule string

	return &applyIptRules( &getIptRuleDelete( $rule ) );
}

sub getIptRuleDelete
{
	my $rule = shift;    # input: iptables rule string

	# some regex magic to extract farm name and backend index
	$rule =~ m/ FARM_(.+)_(\d+)_ /;
	my $farm_name = $1;
	my $index     = $2;

	my $rule_num = &getIptRuleNumber( $rule, $farm_name, $index );

	# if the rule exist
	if ( $rule_num != -1 )
	{
		$rule = &applyIptRuleAction( $rule, 'delete', $rule_num );
	}
	else
	{
		&logfile( "Delete: rule not found: $rule" );
		my @rule_args = split / +/, $rule;
		my $table     = $rule_args[2];       # second argument of iptables is the table
		my $chain     = $rule_args[4];       # forth argument of iptables is the chain
		&logfile( `$iptables -n --line-number -t $table -L $chain` );
	}

	return $rule;
}

sub setIptRuleReplace    # $return_code ( \%farm, \%server, $rule)
{
	my $farm   = shift;    # input: farm struc reference
	my $server = shift;    # input: server struc reference
	my $rule   = shift;    # input: iptables rule string

	return &applyIptRules( &getIptRuleReplace( $farm, $server, $rule ) );
}

sub getIptRuleReplace      # $return_code ( \%farm, \%server, $rule)
{
	my $farm   = shift;    # input: farm struc reference
	my $server = shift;    # input: server struc reference
	my $rule   = shift;    # input: iptables rule string
	my $rule_num;          # possition to insert the rule

	# if the rule exist
	my $rule_num = &getIptRuleNumber( $rule, $$farm{ name }, $$server{ id } );

	return &applyIptRuleAction( $rule, 'replace', $rule_num );
}

sub setIptRuleAppend       # $return_code (\%farm, \%server, $rule)
{
	my $rule = shift;      # input: iptables rule string

	return &applyIptRules( &getIptRuleAppend( $rule ) );
}

sub getIptRuleAppend       # $return_code (\%farm, \%server, $rule)
{
	my $rule = shift;      # input: iptables rule string

	# if the rule does not exist
	if ( &setIptRuleCheck( $rule ) != 0 )
	{
		return &applyIptRuleAction( $rule, 'append' );
	}

	return;
}
##################################################################
sub getIptRulesStruct
{
	return {
			 t_mangle   => [],
			 t_nat      => [],
			 t_mangle_p => [],
			 t_snat     => [],
	};
}

# do not remove this
1;
