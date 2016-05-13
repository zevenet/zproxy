#!/usr/bin/perl -w

# POST Virtual Network Interface
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"name":"new2","ip":"1.1.1.3","netmask":"255.255.192.0"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/addvini/eth0
#
#####Documentation of POST VINI####
#**
#  @api {post} /addvini/<interface> Create a new virtual network interface
#  @apiGroup Interfaces
#  @apiName PostVini
#  @apiParam {String} interface  Interface name, unique ID.
#  @apiDescription Create a new virtual network interface of a given interface
#  @apiVersion 2.0.0
#
#
#
# @apiSuccess   {String}        name                     The name of the virtual network interface.
# @apiSuccess	{String}	ip			IP of the virtual network interface.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "New virtual network interface eth0:new2",
#   "params" : [
#      {
#         "HWaddr" : "04:01:41:01:86:01",
#         "gateway" : "",
#         "ip" : "192.168.0.150",
#         "name" : "eth0:new",
#         "netmask" : "255.255.192.0"
#      }
#   ]
#}
#
# @apiExample {curl} Example Usage:
#	curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	-u zapi:<password> -d '{"name":"new","ip":"192.168.0.150"}'
#	https://<zenlb_server>:444/zapi/v2/zapi.cgi/addvini/eth0
#
# @apiSampleRequest off
#
#**

our $origin;
if ( $origin ne 1 )
{
	exit;
}

sub new_vini()
{
	my $fdev = @_[0];

	use CGI;
	use JSON;

	my $q        = CGI->new;
	my $json     = JSON->new;
	my $data     = $q->param( 'POSTDATA' );
	my $json_obj = $json->decode( $data );

	$error = "false";

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );

	# Check interface errors
	if ( $fdev =~ /^$/ )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "Interface name can't be empty";
		my $output = $j->encode(
		{
		  description => "Interface $fdev",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}

	if ( $fdev =~ /\s+/ )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "Interface name is not valid";
		my $output = $j->encode(
		{
		  description => "Interface $fdev",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}

	my $parent_exist = &ifexist($fdev);
	if ( $parent_exist eq "false" )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "The parent interface $fdev doesn't exist.";
		my $output = $j->encode(
		{
		  description => "Interface $fdev",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}
	
	# Check name errors.
	if ( $json_obj->{ name } =~ /^$/ )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "The name parameter can't be empty";
		my $output = $j->encode(
		{
		  description => "Interface $fdev",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}
	
	# Check address errors
	if ( &ipisok( $json_obj->{ ip }, 4 ) eq "false" )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "IP Address $json_obj->{ip} structure is not ok.";
		my $output = $j->encode(
		{
		  description => "IP Address $json_obj->{ip}",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}

	if ( ! $json_obj->{ ip } )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);

		$errormsg = "IP Address parameter can't be empty";

		my $output = $j->encode(
		{
		  description => "Interface $ifn",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}

	# FIXME: check IPv6 compatibility
	# Check new IP address is already used
	my @activeips = &listallips();
	for my $ip ( @activeips )
	{
		if ( $ip eq $json_obj->{ ip } )
		{
			# Error
			$error = "true";
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);

			$errormsg = "IP Address $json_obj->{ip} is already in use.";

			my $output = $j->encode(
									 {
									   description => "IP Address $json_obj->{ip}",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;		
		}
	}

	# Check network interface errors
	my $ifn = "$fdev\:$json_obj->{name}";
	my $ip_v = &ipversion($json_obj->{ip});
	my $if_ref = &getInterfaceConfig( $ifn, $ip_v );
	
	if ( $if_ref )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "Network interface $ifn already exists.";
		my $output = $j->encode(
		{
		  description => "Network interface $ifn",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}

	# Get params from parent interface
	my $new_if_ref = &getInterfaceConfig( $fdev, $ip_v );
	$error = 'true' if ! $new_if_ref;

	$new_if_ref->{name} = $ifn;
	$new_if_ref->{vini} = $json_obj->{name};
	$new_if_ref->{addr} = $json_obj->{ip};
	$new_if_ref->{ip_v} = $ip_v;

	# No errors
	if ( $error eq "false" )
	{
		&addIp( $new_if_ref );		
		my $state = &upIf( $new_if_ref, 'writeconf' );

		if ( $state == 0 )
		{
			$new_if_ref{status} = "up";
		}
		else
		{
			$error = "true";
		}

		# Writing new parameters in configuration file
		# virtual interface ipv4
		if ( $new_if_ref{name} !~ /:/ )
		{
			&writeRoutes( $new_if_ref{name} );
		}
		
		&setInterfaceConfig( $new_if_ref );
		&applyRoutes( "local", $new_if_ref );
	}

	if ( $error eq "false" )
	{
		# Success
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '201 Created'
		);

		my $out_p = [];
		push $out_p,
		{
			name => $new_if_ref->{name},
			ip => $new_if_ref->{addr},
			netmask => $new_if_ref->{mask},
			gateway => $new_if_ref->{gateway},
			HWaddr => $new_if_ref->{mac},
		};
		my $j = JSON::XS->new->utf8->pretty( 1 );
		$j->canonical( $enabled );
		my $output = $j->encode(
		{
		  description => "New virtual network interface $ifn",
		  params      => $out_p
		}
		);
		print $output;
	}
	else
	{
		# Error
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "The $ifn virtual network interface can't be created";
		my $output = $j->encode(
		{
		  description => "New virtual network interface $ifn",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}
}

# POST Vlan Network Interface
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"name":"3","ip":"1.1.1.3","netmask":"255.255.192.0"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/addvlan/eth0
#
#####Documentation of POST VLAN####
#**
#  @api {post} /addvlan/<interface> Create a new vlan network interface
#  @apiGroup Interfaces
#  @apiName PostVlan
#  @apiParam {String} interface  Interface name, unique ID.
#  @apiDescription Create a new vlan network interface of a given interface
#  @apiVersion 2.0.0
#
#
#
# @apiSuccess   {String}        name                     The name of the vlan network interface.
# @apiSuccess   {String}        ip                       IP of the vlan network interface.
# @apiSuccess   {String}        netmask                  Netmask of the vlan network interface.
# @apiSuccess   {String}        gateway                  Gateway of the vlan network interface.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "New vlan network interface eth0.3",
#   "params" : [
#      {
#         "HWaddr" : "04:01:41:01:86:01",
#         "gateway" : "192.168.1.0",
#         "ip" : "192.168.1.150",
#         "name" : "eth0.3",
#         "netmask" : "255.255.255.0"
#      }
#   ]
#}
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"name":"new","ip":"192.168.1.150","netmask":"255.255.255.0",
#       "gateway":"192.168.1.0"}' https://<zenlb_server>:444/zapi/v2/zapi.cgi/addvlan/eth0
#
# @apiSampleRequest off
#
#**

sub new_vlan()
{
	my $fdev = @_[0];

	my $out_p = [];

	use CGI;
	use JSON;

	my $q        = CGI->new;
	my $json     = JSON->new;
	my $data     = $q->param( 'POSTDATA' );
	my $json_obj = $json->decode( $data );

	$error = "false";

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );

	# Check interface errors
	if ( $fdev =~ /^$/ )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "Interface name can't be empty";
		my $output = $j->encode(
		{
		  description => "Interface $fdev",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}

	if ( $fdev =~ /\s+/ )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "Interface name is not valid";
		my $output = $j->encode(
		{
		  description => "Interface $fdev",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}
	
	my $parent_exist = &ifexist($fdev);
	if ( $parent_exist eq "false" )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "The parent interface $fdev doesn't exist.";
		my $output = $j->encode(
		{
		  description => "Interface $fdev",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}

	if ( $json_obj->{ name } =~ /^$/ )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "The name parameter can't be empty";
		my $output = $j->encode(
		{
		  description => "Interface $fdev",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}
	
	# Check name errors. Must be numeric
	if ( $json_obj->{ name } !~ /^\d+$/ )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "The name for Vlan must be a number.";
		my $output = $j->encode(
		{
		  description => "Name $json_obj->{name} of Vlan",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}

	# Check network interface errors
	my $ifn = "$fdev\.$json_obj->{name}";
	my $ip_v = &ipversion($json_obj->{ip});
	
	# Check if interface already exists
	my $new_if_ref = &getInterfaceConfig( $ifn, $ip_v );

	if ( $new_if_ref )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "Vlan network interface $ifn already exists.";
		my $output = $j->encode(
		{
		  description => "Vlan network interface $ifn",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}

	# Check address errors
	if ( &ipisok( $json_obj->{ ip }, 4 ) eq "false" )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "IP Address $json_obj->{ip} structure is not ok.";
		my $output = $j->encode(
		{
		  description => "IP Address $json_obj->{ip}",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}

	if ( ! $json_obj->{ ip } )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "IP Address parameter can't be empty";
		my $output = $j->encode(
		{
		  description => "Interface $ifn",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}

	# FIXME: Check IPv6 compatibility
	# Check new IP address is not in use
	my @activeips = &listallips();
	for my $ip ( @activeips )
	{
		if ( $ip eq $json_obj->{ ip } )
		{
			# Error
			$error = "true";
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "IP Address $json_obj->{ip} is already in use.";
			my $output = $j->encode(
									 {
									   description => "IP Address $json_obj->{ip}",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;		
		}
	}

	# Check netmask errors for IPv4
	if (  $json_obj->{netmask} eq '' || ( $ip_v == 4 && &ipisok( $json_obj->{netmask}, 4 ) eq "false" && $json_obj->{netmask} !~ /^\d+$/ ) )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "Netmask parameter can't be empty";
		my $output = $j->encode(
		{
		  description => "Netmask Address $json_obj->{netmask}",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}
	
	# Check gateway errors
    if ( $json_obj->{gateway} !~ /^$/ && &ipisok( $json_obj->{gateway}, 4 ) eq "false") {
        # Error
        $error = "true";
        print $q->header(
           -type=> 'text/plain',
           -charset=> 'utf-8',
           -status=> '400 Bad Request'
        );
        $errormsg = "Gateway Address $json_obj->{gateway} structure is not ok.";
        my $output = $j->encode({
            description => "Gateway Address $json_obj->{gateway}",
            error => "true",
            message => $errormsg
        });
        print $output;
        exit;
    }

	# get params of fdev
	my $socket = IO::Socket::INET->new( Proto => 'udp' );
	my @system_interfaces = $socket->if_list;

	$new_if_ref->{name} = $ifn;
	$new_if_ref->{dev} = $fdev;
	$new_if_ref->{status} = "up";
	$new_if_ref->{vlan} = $json_obj->{name};
	$new_if_ref->{addr} = $json_obj->{ip};
	$new_if_ref->{mask} = $json_obj->{netmask};
	$new_if_ref->{gateway} = $json_obj->{gateway} // '';
	$new_if_ref->{ip_v} = $ip_v;
	$new_if_ref->{mac} = $socket->if_hwaddr( $new_if_ref->{ dev } );

	# No errors
	if ( $error eq "false" )
	{
		&createIf( $new_if_ref );
		&addIp( $new_if_ref );
		my $state = &upIf( $new_if_ref, 'writeconf' );

		if ( $state == 0 )
		{
			$new_if_ref->{status} = "up";
		}

		# Writing new parameters in configuration file
		# virtual interface ipv4
		if ( $new_if_ref->{name} !~ /:/ )
		{
			&writeRoutes( $new_if_ref->{name} );
		}
		
		&setInterfaceConfig( $new_if_ref );
		&applyRoutes( "local", $new_if_ref );
	}

	if ( $error eq "false" )
	{
		# Success
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '201 Created'
		);
		push $out_p,
		{
			name => $new_if_ref->{name},
			ip => $new_if_ref->{addr},
			netmask => $new_if_ref->{mask},
			gateway => $new_if_ref->{gateway},
			HWaddr => $new_if_ref->{mac},
		};
		my $j = JSON::XS->new->utf8->pretty( 1 );
		$j->canonical( $enabled );
		my $output = $j->encode(
		{
			description => "New vlan network interface $ifn",
			params      => $out_p
		}
		);
		print $output;
	}
	else
	{
		# Error
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "The $ifn vlan network interface can't be created";
		my $output = $j->encode(
		{
		  description => "New vlan network interface $ifn",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}
}

# DELETE Virtual Network Interface
#
# curl --tlsv1 -k -X DELETE -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin https://178.62.126.152:445/zapi/v1/zapi.cgi/deleteif/eth0:new
#
#
#####Documentation of DELETE INTERFACE####
#**
#  @api {delete} /deleteif/<interface> Delete a interface
#  @apiGroup Interfaces
#  @apiName DeleteIf
#  @apiParam {String} interface  Interface name, unique ID.
#  @apiDescription Delete a interface, a virtual network interface or a vlan
#  @apiVersion 2.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Delete interface eth0:new",
#   "message" : "The interface eth0:new has been deleted.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> https://<zenlb_server>:444/zapi/v2/zapi.cgi/deleteif/eth0:new
#
# @apiSampleRequest off
#
#**

sub delete_interface()
{
	my $if = @_[0];
	use CGI;
	my $q = CGI->new;
	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );
	
	$error = "false";

	# Check input errors and delete interface
	if ( $if !~ /^$/ )
	{
		my $if_ref = &getInterfaceConfig( $if, 4 );
		&delRoutes( "local", $if_ref );
		&downIf( $if_ref, 'writeconf' );
		&delIf( $if_ref );

		# Success
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '200 OK'
		);

		my $j = JSON::XS->new->utf8->pretty( 1 );
		$j->canonical( $enabled );

		$message = "The interface $if has been deleted.";
		my $output = $j->encode(
		{
		  description => "Delete interface $if",
		  success     => "true",
		  message     => $message,
		}
		);
		print $output;
	}
	else
	{
		# Error
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "The $if interface can't be deleted";
		my $output = $j->encode(
		{
		  description => "Delete interface $if",
		  error       => "true",
		  message     => $errormsg,
		}
		);
		print $output;
		exit;
	}
}

# GET Interface
#
# curl --tlsv1 -k -X GET -H 'Content- Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin https://178.62.126.152:445/zapi/v1/zapi.cgi/interfaces
#
#####Documentation of GET INTERFACES####
#**
#  @api {get} /interfaces Get params of the interfaces
#  @apiGroup Interfaces
#  @apiName GetInterfaces
#  @apiDescription Gat all the params of the interfaces
#  @apiVersion 2.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "List interfaces",
#   "interfaces" : [
#      {
#         "HWaddr" : "04:01:41:01:86:01",
#         "gateway" : "",
#         "ip" : "178.62.126.152",
#         "name" : "eth0",
#         "netmask" : "255.255.192.0",
#         "status" : "up"
#      },
#      {
#         "HDWaddr" : "04:01:41:01:86:01",
#         "gateway" : "192.168.0.1",
#         "ip" : "192.168.0.155",
#         "name" : "eth0.5:22",
#         "netmask" : "255.255.255.0",
#         "status" : "down"
#      },
#      {
#         "HDWaddr" : "04:01:41:01:86:01",
#         "gateway" : "",
#         "ip" : "172.62.125.10",
#         "name" : "eth0:n1",
#         "netmask" : "255.255.192.0",
#         "status" : "down"
#      },
#      {
#         "HWaddr" : "04:01:41:01:86:01",
#         "gateway" : "192.160.0.1",
#         "ip" : "192.168.0.150",
#         "name" : "eth0.5",
#         "netmask" : "255.255.255.0",
#         "status" : "up"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> https://<zenlb_server>:444/zapi/v2/zapi.cgi/interfaces
#
# @apiSampleRequest off
#
#**

sub get_interface()
{
	my $out = [];
	use CGI;
	my $q = CGI->new;
	
	# Configured interfaces list
	my @configured_interfaces = @{ &getConfigInterfaceList() };
	
	my @sorted =  sort { $a->{name} cmp $b->{name} } @configured_interfaces;
	$_->{status} = &getInterfaceSystemStatus( $_ ) for @configured_interfaces;
	
	for my $if_ref ( @sorted )
	{
		# Only IPv4
		next if $if_ref->{ip_v} == 6;
		
		# Any key must cotain a value or "" but can't be null
		if ( ! defined $if_ref->{ name } )    { $if_ref->{ name }    = ""; }
		if ( ! defined $if_ref->{ addr } )    { $if_ref->{ addr }    = ""; }
		if ( ! defined $if_ref->{ mask } )    { $if_ref->{ mask }    = ""; }
		if ( ! defined $if_ref->{ gateway } ) { $if_ref->{ gateway } = ""; }
		if ( ! defined $if_ref->{ status } )  { $if_ref->{ status }  = ""; }
		if ( ! defined $if_ref->{ mac } )     { $if_ref->{ mac }     = ""; }

		push $out,
		  {
			name    => $if_ref->{ name },
			ip      => $if_ref->{ addr },
			netmask => $if_ref->{ mask },
			gateway => $if_ref->{ gateway },
			status  => $if_ref->{ status },
			HDWaddr => $if_ref->{ mac },
		  };
	}

	print $q->header(
	  -type    => 'text/plain',
	  -charset => 'utf-8',
	  -status  => '200 OK'
	);

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );
	
	my $output = $j->encode(
			description => "List interfaces",
			interfaces  => $out,
		}
	);
	
	print $output;
}

# POST Interface actions
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"action":"down"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/ifaction/eth0
#
#####Documentation of POST INTERFACE ACTION####
#**
#  @api {post} /ifaction/<interface> Set an action in a interface
#  @apiGroup Interfaces
#  @apiName Postifaction
#  @apiParam {String} interface  Interface name, unique ID.
#  @apiDescription Set an action in a interface, virtual network interface or vlan
#  @apiVersion 2.0.0
#
#
#
# @apiSuccess   {String}        action                   The action that will be set in the interface. Could it be up or down.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Action in interface eth0:new",
#   "params" : [
#      {
#         "action" : "down"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"action":"down"}'
#       https://<zenlb_server>:444/zapi/v2/zapi.cgi/ifaction/eth0:new
#
# @apiSampleRequest off
#
#**

sub ifaction()
{
	my $fdev  = @_[0];

	use CGI;
	use JSON;

	my $q        = CGI->new;
	my $json     = JSON->new;
	my $data     = $q->param( 'POSTDATA' );
	my $json_obj = $json->decode( $data );

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );

	$error = "false";

	# Check interface errors
	if ( $fdev =~ /^$/ )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "Interface name can't be empty";
		my $output = $j->encode(
		{
		  description => "Interface $fdev",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}

	if ( $fdev =~ /\s+/ )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "Interface name is not valid";
		my $output = $j->encode(
		{
		  description => "Interface $fdev",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}

	# Check input errors
	if ( $json_obj->{ action } !~ /^(up|down)$/ )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "Action value must be up or down";
		my $output = $j->encode(
		{
		  description => "Action value $json_obj->{action}",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}

	# Open conf file to get the interface parameters
	#~ my $if = $fdev;
	tie my @array, 'Tie::File', "$configdir/if_$fdev\_conf", recsep => ':';
	
	# Check if the ip is already in use
	my @activeips = &listallips();
	for my $ip ( @activeips )
	{
		if ( $ip eq @array[2] && $json_obj->{ action } ne "down" )
		{
			# Error
			$error = "true";
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "Interface $fdev cannot be UP, IP Address @array[2] is already in use";
			my $output = $j->encode(
									 {
									   description => "Interface $fdev",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;
		}
	}

	# Everything is ok
	my $if_ref = &getInterfaceConfig( $fdev, 4 );
	
	if ( $json_obj->{action} eq "up" )
	{
		# Create a hash with interface name
		my %interface;
		$interface{ name }    = $fdev;
		
		# Create vlan if required if it doesn't exist
		my $exists = &ifexist( $if_ref->{name} );
		if ( $exists eq "false" )
		{
			#Get parameters 					
			$interface{ ip_v }    = 4;		
			my %if = %{ &getDevVlanVini( $interface{ name } ) };
			$interface{ dev }  	  = $if{ dev };
			$interface{ vlan }    = $if{ vlan };
			$interface{ vini }    = $if{ vini };
					
			$status = &createIf( \%interface );
		}
	
		# Delete routes in case that it is not a vini
		if ( $if_ref && $if_ref->{vini} eq '' )
		{
			&delRoutes( "local", $if_ref );
		}
		
		# Add IP
		&addIp( $if_ref ) if $if_ref;
		
		# Check the parent's status before up the interface
		my $parent_if_name = &getParentInterfaceName( $if_ref->{name} );
		if ( !$parent_if_name )
		{
			# &zenlog ("parent doesn't exist for $fdev");
			$parent_if_status = 'up';
		}
		else
		{
			# &zenlog ("parent exists");
			my $parent_if_ref = &getInterfaceConfig( $parent_if_name, 4 );
			$parent_if_status = &getInterfaceSystemStatus( $parent_if_ref, 4 );
		}
		
		if ( $parent_if_status eq 'up' )
		{	
			# &zenlog ("GO UP!");
			my $state = &upIf( \%interface, 'writeconf' );
			if ( $state != 0 )
			{
				$error = "true";
			}
			&applyRoutes( "local", $if_ref ) if $if_ref;
		}
		else
		{
			# Error
			$error = "true";
			# print $q->header(
			   # -type=> 'text/plain',
			   # -charset=> 'utf-8',
			   # -status=> '400 Bad Request'
			# );
			# $errormsg = "The interface $if_ref->{name} has a parent interface DOWN, check the interfaces status";
			# my $output = $j->encode({
				# description => "Action value $json_obj->{action}",
				# error => "true",
				# message => $errormsg
			# });
			# print $output;
			# exit;
		}		
	} 
	elsif ( $json_obj->{action} eq "down" )
	{
		#~ &delRoutes( "local", $fdev );
		my $state = &downIf( $if_ref, 'writeconf' );

		if ( $state != 0 )
		{
			$error = "true";
		}
	
		# &delRoutes("local",$fdev);
		# &downIf($fdev);
		# if ( $? == 0) {
			# @array[4] = "down";
		# } else {
			# $error = "true";
		# }
	}
	else
	{
		$error = "true";
	}

	if ( $error eq "false" )
	{
		# Success
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '201 Created'
		);

		my $out_p = [];
		push $out_p, { action => $json_obj->{ action } };
		my $j = JSON::XS->new->utf8->pretty( 1 );
		$j->canonical( $enabled );

		my $output = $j->encode(
		{
		  description => "Action in interface $fdev",
		  params      => $out_p,
		}
		);
		print $output;
	}
	else
	{
		# Error
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "The action $json_obj->{action} is not set in interface $fdev";
		my $output = $j->encode(
		{
		  description => "Action in interface $fdev",
		  error       => "true",
		  message     => $errormsg,
		}
		);
		print $output;
		exit;
	}
}

# PUT Interface
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"gateway":"1.1.1.0","ip":"1.1.1.3","netmask":"255.255.192.0"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/modifyif/eth0:n1
#
#####Documentation of PUT INTERFACE####
#**
#  @api {put} /modifyif/<interface> Modify a interface
#  @apiGroup Interfaces
#  @apiName PutIf
#  @apiParam {String} interface  Interface name, unique ID.
#  @apiDescription Modify a interface, vlan or a virtual network interface
#  @apiVersion 2.0.0
#
#
#
# @apiSuccess   {String}        ip                       IP of the interface.
# @apiSuccess   {String}        netmask                  Netmask of the interface.
# @apiSuccess   {String}        gateway                  Gateway of the interface. This value could not be modified in virtual network interface.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify interface eth0:new",
#   "params" : [
#      {
#         "gateway" : "192.168.1.0"
#      },
#      {
#         "ip" : "192.168.1.160"
#      },
#      {
#         "netmask" : "255.255.255.0"
#      }
#   ]
#}
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"ip":"192.168.1.160","netmask":"255.255.255.0",
#       "gateway":"192.168.1.0"}' https://<zenlb_server>:444/zapi/v2/zapi.cgi/modifyif/eth0:new
#
# @apiSampleRequest off
#
#**

sub modify_interface()
{
	my $fdev = @_[0];

	use CGI;
	use JSON;

	my $q        = CGI->new;
	my $json     = JSON->new;
	my $data     = $q->param( 'PUTDATA' );
	my $json_obj = $json->decode( $data );

	my $error = "false";

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );

	# Check interface errors
	if ( $fdev =~ /^$/ )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "Interface name can't be empty";
		my $output = $j->encode(
		{
		  description => "Modify interface $fdev",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}

	if ( $fdev =~ /\s+/ )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "Interface name is not valid";
		my $output = $j->encode(
		{
		  description => "Modify interface $fdev",
		  error       => "true",
		  message     => $errormsg,
		}
		);
		print $output;
		exit;
	}

	# Check address errors
	if ( &ipisok( $json_obj->{ ip }, 4 ) eq "false" )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "IP Address $json_obj->{ip} structure is not ok.";
		my $output = $j->encode(
		{
		  description => "IP Address $json_obj->{ip}",
		  error       => "true",
		  message     => $errormsg,
		}
		);
		print $output;
		exit;
	}

	# Check netmask errors
	if (    $json_obj->{ netmask } !~ /^$/
		 && &ipisok( $json_obj->{ netmask }, 4 ) eq "false" )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "Netmask Address $json_obj->{netmask} structure is not ok.";
		my $output = $j->encode(
		{
		  description => "Netmask Address $json_obj->{netmask}",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}

	# Check gateway errors
	if (    $json_obj->{ gateway } !~ /^$/
		 && &ipisok( $json_obj->{ gateway }, 4 ) eq "false" )
	{
		# Error
		$error = "true";
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "Gateway Address $json_obj->{gateway} structure is not ok.";
		my $output = $j->encode(
		{
		  description => "Gateway Address $json_obj->{gateway}",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}

	# No errors found
	if ( $error eq "false" )
	{
		# Get the current values
		my $if_ref = &getInterfaceConfig( $fdev, 4 );
		
		# Vlans need to be created if they don't already exist
		my $exists = &ifexist( $if_ref->{name} );
		if ( $exists eq "false" )
		{
			&createIf( $if_ref );
		}
		
		# Set the new params
		if ( exists( $json_obj->{ip} ) )
		{
			$if_ref->{addr} = $json_obj->{ip};
		}
		# If Vini is configured, only IP is the parameter editable
		if ( $if_ref->{vini} eq '' )
		{
			if ( exists( $json_obj->{netmask} ) )
			{
				$if_ref->{mask} = $json_obj->{netmask};
			}
			if ( exists( $json_obj->{gateway} ) && $name =~ /^$/ )
			{
				$if_ref->{gateway} = $json_obj->{gateway};
			}
		}

		# Delete old parameters
		my $old_iface_ref = &getInterfaceConfig( $fdev, 4 );

		if ( $old_iface_ref )
		{
			# Delete old IP and Netmask from system to replace it
			&delIp( $$old_iface_ref{name}, $$old_iface_ref{addr}, $$old_iface_ref{mask} );
		
			# Remove routes if the interface has its own route table: nic and vlan
			if ( $interface{vini} eq '' )
			{
				&delRoutes( "local", $old_iface_ref );
			}
		}
		
		# Add new IP, netmask and gateway
		&addIp( $if_ref );		
		my $state = &upIf( $if_ref, 'writeconf' );

		if ( $state == 0 )
		{
			$if_ref->{status} = "up";
		}

		# Writing new parameters in configuration file
		if ( $if_ref->{name} !~ /:/ )
		{
			&writeRoutes( $if_ref->{name} );
		}
		
		&setInterfaceConfig( $if_ref );
		&applyRoutes( "local", $if_ref );
	}

	# Print params
	if ( $error ne "true" )
	{
		# Success
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '200 OK'
		);

	        my $out_p = [];
		foreach $key ( keys %$json_obj )
		{
			push $out_p, { $key => $json_obj->{ $key } };
		}

		my $j = JSON::XS->new->utf8->pretty( 1 );
		$j->canonical( $enabled );
		my $output = $j->encode(
		{
		  description => "Modify interface $if",
		  params      => $out_p
		}
		);

		print $output;
	}
	else
	{
		# Error
		print $q->header(
		  -type    => 'text/plain',
		  -charset => 'utf-8',
		  -status  => '400 Bad Request'
		);
		$errormsg = "Errors found trying to modify interface $if";
		my $output = $j->encode(
		{
		  description => "Modify interface $if",
		  error       => "true",
		  message     => $errormsg
		}
		);
		print $output;
		exit;
	}
}

1;
