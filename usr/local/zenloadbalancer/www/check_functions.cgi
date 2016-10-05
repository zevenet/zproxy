#!/usr/bin/perl

###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2016 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
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

# Notes about regular expressions:
#
# \w matches the 63 characters [a-zA-Z0-9_] (most of the time)
#

my %format_re = (
	'farm_name'     => qr{[a-zA-Z0-9\-]+},
	'rbl_list_name' => qr{[a-zA-Z0-9]+},

	# certificates filenames
	'certificate' => qr{\w[\w\.-]*\.(?:pem|csr)},
	'cert_pem'    => qr{\w[\w\.-]*\.pem},
	'cert_csr'    => qr{\w[\w\.-]*\.csr},
	'cert_dh2048' => qr{\w[\w\.-]*_dh2048\.pem},

	#'' => qr{},
);

=begin nd
        Function: getValidFormat

        Validates a data format matching a value with a regular expression.
        If no value is passed as an argument the regular expression is returned.

        Usage:
			# validate exact data
			if ( ! &getValidFormat( "farm_name", $input_farmname ) ) {
				print "error";
			}

			# use the regular expression as a component for another regular expression 
			my $file_regex = &getValidFormat( "certificate" );
			if ( $file_path =~ /$configdir\/$file_regex/ ) { ... }

        Parameters:
				format_name	- type of format
				value		- value to be validated (optional)
				
        Returns:
				false	- If value failed to be validated
				true	- If value was successfuly validated
				regex	- If no value was passed to be matched

=cut
# &getValidFormat ( $format_name, $value );
sub getValidFormat
{
	my ( $format_name, $value ) = @_;

	#~ print "getValidFormat type:$format_name value:$value\n"; # DEBUG

	if ( exists $format_re{ $format_name } )
	{
		if ( defined $value )
		{
			#~ print "$format_re{ $format_name }\n"; # DEBUG
			return $value =~ /^$format_re{ $format_name }$/;
		}
		else
		{
			#~ print "$format_re{ $format_name }\n"; # DEBUG
			return $format_re{ $format_name };
		}
	}
	else
	{
		my $message = "getValidFormat: format $format_name not found.";
		&zenlog( $message );
		die ( $message );
	}
}

1;
