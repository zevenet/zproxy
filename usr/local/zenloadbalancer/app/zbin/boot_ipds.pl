#!/usr/bin/perl 

require "/usr/local/zenloadbalancer/www/blacklists.cgi";
require "/usr/local/zenloadbalancer/www/dos.cgi";

my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
my $touch          = &getGlobalConfiguration( 'touch' );
my $blacklistsPath = &getGlobalConfiguration( 'blacklistsPath' );

# blacklists
if ( !-d $blacklistsPath )
{
	system ( &getGlobalConfiguration( 'mkdir' ) . " -p $blacklistsPath" );
	&zenlog( "Created $blacklistsPath directory." );
}

# create list config if doesn't exist
if ( !-e $blacklistsConf )
{
	system ( "$touch $blacklistsConf" );
	&zenlog( "Created $blacklistsConf file." );
}

# load preload lists
&setBLAddPreloadLists();

#dos
&setDOSCreateFileConf();
