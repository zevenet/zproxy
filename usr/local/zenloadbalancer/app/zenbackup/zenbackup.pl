#!/usr/bin/perl

require '/usr/local/zenloadbalancer/config/global.conf';

$name = $ARGV[0];

$action = $ARGV[1];


if ($action eq "-c")
	{
	my @eject = `$tar zcvf $backupdir\/backup-$name.tar.gz $backupfor`;
	}

if ($action eq "-d")
	{
	my @eject = `$tar -xvzf $backupdir\/backup-$name.tar.gz -C /`;
	}

