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

package plugins;

use Exporter qw(import);
our @EXPORT = qw(
  getPluginsList
  plugins
  triggerAllPlugins
  triggerPlugin
  plugins_path
);

our $plugins_path = "$main::pluginsdir";

sub getPluginsList
{
	my @modules_list;

	opendir ( my $dir, $plugins_path )
	  or die ( "Could not read directory $plugins_path: $!" );

	# catch the module name
	foreach my $file ( readdir $dir )
	{
		if ( $file =~ /\.pm$/ )
		{
			# FIXME: eval module
			#~ print $module_name;
			$file =~ s/\.pm//;
			push ( @modules_list, $file );
		}
	}

	closedir $dir;

	@modules_list = sort @modules_list;

	#~ print "@modules_list";
	
	return \@modules_list;    # returns an array reference
}

# $<tagHTML> = getPluginsMenuList ($id, $version);
sub getPluginsMenuList
{
	my ( $id, $version, $name ) = @_;
	my $output;
	my %outputhash;

	my @plugin_list = @{ &getPluginsList() };

	# Fill a hash with POSTION => OUTPUT from each plugin
	foreach my $pi_name ( @plugin_list )
	{
		$outputhash{ &plugins::triggerPlugin( $pi_name, 'position' ) } .=
		  &plugins::triggerPlugin( $pi_name, 'menu', $id, $version, $name );
	}

	# Convert sort hash in string
	foreach my $key ( sort ( keys %outputhash ) )
	{
		$output .= $outputhash{ $key };
	}

	return \$output;
}

use feature 'state';

sub plugins
{
	my $pi = shift;
	state $plugins;    # array reference

	push @{ $plugins }, $pi;

	return $plugins;
}

sub loadAllModules
{
	opendir ( my $dir, $plugins_path )
	  or die ( "Could not read directory $plugins_path: $!" );

	foreach my $file ( readdir $dir )
	{
		if ( $file =~ /.pm$/ )
		{
			# FIXME: eval module
			require "$plugins_path/$file";
		}
	}

	closedir $dir;
}

&loadAllModules();

sub triggerAllPlugins
{
	my $action = shift;
	my @params = @_;

	for my $plugin ( @{ &getPluginsList() } )
	{
		if ( defined $$plugin{ $action } )
		{
			&{ $plugin{ $action } }( @params );
		}
	}
}

sub triggerPlugin
{
	my $plugin_name = shift;
	my $action      = shift;
	my @params      = @_;
	my $output;

	my @plugins_data_list = @{ &plugins() };

	for my $plugin ( @plugins_data_list )
	{
		if ( $$plugin{ name } eq $plugin_name && defined $$plugin{ $action } )
		{
			$output = &{ $$plugin{ $action } }( @params );
		}
	}

	return $output;
}

1;
