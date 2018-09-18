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

use strict;
use Zevenet::Core;
use Zevenet::Lock;

use Zevenet::IPDS::WAF::Core;
use Zevenet::IPDS::WAF::Parser;

#~ include 'Zevenet::IPDS::WAF::Core';
#~ include 'Zevenet::IPDS::WAF::Parser';

sub genWAFRuleId
{
	my $interval_limit_up   = 99999;
	my $interval_limit_down = 1;
	my $id                  = $interval_limit_down;
	my $fin = 0;

	do
	{
		if ( ! &existWAFRuleId( $id ) )
		{
			$fin = 1;
		}
		else
		{
			$id++;
		}
	} while ( $id <= $interval_limit_up and ! $fin);

	if ( $id > $interval_limit_up )
	{
		$id = 0;
		&zenlog( "The limit of WAF rule id has been alreached", "error", "waf" );
	}

	return $id;
}



# add a new rule in the end of the set file
# debe mandarse el id a modificar, la nueva regla puede tener un id differente
sub setWAFRule
{
	my $set      = shift;
	my $rule_ref = shift;
	my $id = shift;
 	my $rule;

	if ( ref $rule_ref eq 'HASH' )
	{
		$rule = &buildWAFRule( $rule_ref );
	}

	elsif ( ref $rule_ref eq 'ARRAY' )
	{
		$rule = join ( '\n', @{ $rule_ref } );
		$rule_ref = &parseWAFRule( $rule_ref );
	}

	# check syntax
	my $err_msg = &checkWAFRuleSyntax( $rule );
	if ( not $err_msg )
	{
		# get struct
		my $set_st = &parseWAFSet($set);
		foreach my $ru ( @{ $set_st } )
		{
			if ( $ru->{id} == $id )
			{
				$ru = $rule_ref;
				last;
			}
		}
		$err_msg = &buildWAFSet ( $set, $set_st );
	}

	return $err_msg;
}

# add a new rule in the end of the set file
sub createWAFRule
{
	my $set      = shift;
	my $rule_ref = shift;
	my $err_msg  = 0;
	my $rule;

	# In this way, the user has to add the rule id
	if ( ref $rule_ref eq 'ARRAY' )
	{
		$rule = join ( '\n', @{ $rule_ref } );
		$rule_ref = &parseWAFRule( $rule_ref );
		return "Error parsing the rule" if not defined $rule_ref;
		if ( &existWAFRuleId( $rule_ref->{ definition }->{ rule_id } ) and $rule_ref->{ definition }->{ rule_id } )
		{
			return "The rule id already exists";
		}
	}
	elsif ( ref $rule_ref eq 'HASH' )
	{}
	else
	{
		return "Rule format does not expected";
	}

	$rule_ref->{ definition }->{ rule_id } = &genWAFRuleId() if not $rule_ref->{ definition }->{ rule_id };

	# check syntax
	$rule = &buildWAFRule( $rule_ref );
	my $err_msg = &checkWAFRuleSyntax( $rule );
	if ( not $err_msg )
	{
		my $set_file = &getWAFSetFile( $set );
		my $fh = &openlock( $set_file, 'a' )
		  or $err_msg = "Error writting the set $set";
		if ( !$err_msg )
		{
			print $fh $rule . "\n\n";
			close $fh;
		}
	}

	return $err_msg;
}

sub copyWAFRule
{
	my $set = shift;
	my $id = shift;

	# get rule
	my $rule = &getWAFRuleById( $id );

	# create rule
	my $err = &createWAFRule( $set, $rule );

	return $err;
}

# add a new rule in the end of the set file
sub createWAFSet
{
	my $setName = shift;
	my $err     = 0;

	my $fh = &openlock( &getWAFSetFile( $setName ), 'w' ) or $err = 1;
	close $fh;

	return $err;
}

sub copyWAFSet
{
	my $dstSet    = shift;
	my $originSet = shift;

	my $err = &copyLock( &getWAFSetFile( $originSet ), &getWAFSetFile( $dstSet ) );

	my $set = &parseWAFSet( $dstSet );
	foreach my $rule ( @{$set} )
	{
		$rule->{ id } = &genWAFRuleId();
	}
	&buildWAFSet( $dstSet );

	return $err;
}

# util para copiar reglas
sub getWAFRuleById
{
	my $id = shift;
	my $rule;

	# get set,
	my $setRule = &getWAFSetByRuleId( $id );
	# parse the set
	my $setParsed = &parseWAFSet( $setRule );

	# get rule
	foreach my $ru ( @{$setParsed} )
	{
		if ( $ru->{ definition }->{ id } eq $id )
		{
			$rule = $ru;
			last;
		}
	}

	return $rule;
}

sub deleteWAFRule
{
	my $set = shift;
	my $rule_id = shift;
	my $err = 0;
	my $index = -1;

	my $set_st = &parseWAFSet($set);

	# look for id rule index
	foreach my $ru ( @{$set_st} )
	{
		$index++;
		last if ( $ru->{definition}->{id} eq $rule_id);
	}
	return 1 if ( $index == scalar @{$set_st} );  # it has not been found

	# delete
	return 1 if ( ! splice( @{$set_st}, $index, 1 ) );	# error if any item is deleted

	# save
	$err = &buildWAFSet( $set, $set_st );

	return $err;
}

sub deleteWAFSet
{
	my $set = shift;
	my $err = unlink &getWAFSetFile($set);
	return $err;
}


sub getWAFRuleLast
{
	my $set = shift;
	my $set_st = &parseWAFSet($set);
	return @{ $set_st }[-1];
}


1;
