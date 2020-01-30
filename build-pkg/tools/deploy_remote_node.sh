#!/bin/bash

set -e

function print_help ()
{
  echo "Usage: \"$0.sh <remote_ip> [-c]\""
  echo "This script generates a package with the code of the current machine and it deploys it in a remote cluster node."
  echo "The <remote_ip> is the ip of the remote node."
  echo -e "-c, -compile \t\t\tIt is a flag to compile the package. The package is created without compiling by default."
  exit
}

DEVEL="--devel"

# get IP
if [ "-h" = "$1" ]; then
	print_help
	exit
else
	if [ "--help" = "$1" ]; then
		print_help
		exit
	fi
fi

REM_IP="$1"
shift

if [ -z "$REM_IP" ]; then
	echo "The remote IP is expected"
	exit
fi

while [[ $# -gt 0 ]]; do
  ARG="$1"
  case $ARG in
    "-compile"|"-c")
      DEVEL=""
      shift
      ;;
    "-h"|"--help")
      print_help
      exit
      ;;
    *)
      echo "Try: $0 -h or --help"
      exit
      ;;
  esac
done


PACKAGES_DIR="/build-pkg/packages"
GEN_SCRIPT="/build-pkg/gen_pkg.sh"


# execute script
$GEN_SCRIPT -u $DEVEL

# copy and install package
PACKAGE_NAME=`ls -s $PACKAGES_DIR | head -1`
scp ${PACKAGES_DIR}/${PACKAGE_NAME} root@$REM_IP:
ssh root@$REM_IP "dpkg -i /root/$PACKAGE_NAME"
# ssh root@$REM_IP "rm /root/$PACKAGE_NAME"
