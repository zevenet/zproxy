#!/usr/bin/perl

use strict;
use warnings;
use Zevenet::Core;


use Zevenet::IPDS::WAF::Core;
use Zevenet::IPDS::WAF::Config;
use Zevenet::IPDS::WAF::Actions;
use Zevenet::IPDS::WAF::Parser;


&initWAFModule();
&createWAFSet( 'rule1');
&copyWAFSet( 'rule_copied', 'rule1' );

exit;

############ debug
use Data::Dumper;
use Tie::File;
tie my @ru, 'Tie::File', '/tmp/sec.rule';
my $res = &parseWAFRule( \@ru );

#~ print Dumper($res);
untie @ru;

my $rulest = &buildWAFRule( $res );
open my $fh, '/tmp/sec.rule2';
print "rule $rulest\n";

#~ print $fh $rulest;
close $fh;

my $file_rules = &parseWAFSet( '/tmp/set.rule' );

#~ print Dumper(@{$file_rules}[41]);
