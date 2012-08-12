#!/usr/bin/perl

require '/usr/local/zenloadbalancer/config/global.conf';

if ($datentp !~ /^$/)
	{
	my @conf = `$datentp $ntp`;
	print @conf;
	}

