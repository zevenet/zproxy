#!/bin/bash

# Exit at the first error
set -e

source config
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
DATE=$(date +%y%m%d_%H%M%S)
arch="amd64"

# Default options
devel="false"

function print_usage_and_exit() {
	echo "Usage: $(basename "$0") <distribution> [options]

	Distribution:
	-i		First installation package
	-u		Update package

	Options:
	--devel		Do not compile perl"
	exit 1
}

function msg() {
	echo -e "\n#### ${1} ####\n"
}

function die() {
	local bldred='\e[1;31m' # Red bold text
	local txtrst='\e[0m'    # Text Reset

	msg "${bldred}Error${txtrst}${1}"
	exit 1
}


##### Parse command arguments #####

# Distribution parameter (-i or -u) is not optional show
# how to use the command if no distribution was selected
if [[ $1 == "" ]]; then
	print_usage_and_exit
fi

while [ $# -gt 0 ]; do
	case $1 in
	-i)
		if [[ $distribution == "" ]]; then
			distribution="install"
		else
			echo "Select only one type of distribution"
			print_usage_and_exit
		fi
		;;
	-u)
		if [[ $distribution == "" ]]; then
			distribution="update"
		else
			echo "Select only one type of distribution"
			print_usage_and_exit
		fi
		;;
	--devel)
		devel="true"
		;;
	*)
		echo "Invalid option: $1"
		print_usage_and_exit
		;;
	esac

	shift
done


#### Initial setup ####

# Ensure we are in the correct directory
cd "$BASE_DIR"

# Setup docker images
msg "Setting up the docker environment..."

# Check whether docker is running
docker ps -q >/dev/null 2>&1 \
	|| die ": it seems that docker is not working"

for version in "${debian_versions[@]}"; do
	echo -e "\n>> Building ${version} image:"

	dockerimg="zvn-ee-builder-${version}"

	# Ensure that docker build context exists
	mkdir -p build-context

	# Build specific docker image
	sed "s/#{version}/${version}/g" dockerfile-base > build-context/Dockerfile
	docker build \
		--build-arg host_uid="$(id -u)" \
		--build-arg host_gid="$(id -g)" \
		-t "$dockerimg" \
		build-context/ || die " building docker image"

	# Remove docker build context
	rm -rf build-context
done

# Setup a clean environment
msg "Setting up a clean environment..."
rm -rf workdir
mkdir workdir
rsync -a --exclude "/$(basename "$BASE_DIR")" ../* workdir/
cp -r encryption/ workdir/
cp config workdir/encryption/
cd workdir

# Set version and package name
version=$(grep "Version:" DEBIAN/control | cut -d " " -f 2)
pkgname_prefix="zevenet_${version}_${arch}"

if [[ "$devel" == "false" ]]; then
	pkgname=${pkgname_prefix}_${distribution}_${DATE}.deb
else
	pkgname=${pkgname_prefix}_DEV_${distribution}_${DATE}.deb
fi


#### Package preparation ####

msg "Preparing package..."

# Remove .keep files
find . -name .keep -exec rm {} \;

# Bare-metal/installation files
for install_file in "${installation_files[@]}"; do
	# Bash built-in string substitution
	orig_file=${install_file//_BM/}

	if [[ $distribution == "install" ]]; then
		echo "Overwriting $orig_file with $install_file"
		mv "${install_file}" "${orig_file}"
	else
		echo "Deleting $install_file"
		rm "${install_file}"
	fi
done


# Release or development
if [[ $devel == "false" ]]; then
	# Remove warnings
	# Don't include API 3
	msg "Removing warnings..."
	find -L usr/local/zevenet/bin \
			usr/local/zevenet/lib \
			usr/local/zevenet/www/zapi/v3.1 \
			usr/local/zevenet/www/zapi/v3.2 \
			usr/local/zevenet/app/libexec/check_uplink \
			-type f \
			-exec sed --follow-symlinks -i 's/^use warnings.*//' {} \; \
			-exec sed --follow-symlinks -i '/zenlog.*PROFILING/d' {} \;

	# Compile files for all debian versions
	msg "Compiling perl files"
	for version in "${debian_versions[@]}"; do
		echo -e "\n>> Compiling binaries in ${version}"
		dockerimg="zvn-ee-builder-${version}"

		docker run --rm -v "$(pwd)":/workdir \
			"$dockerimg" \
			encryption/compile_all.sh || die " compiling files"
	done

	# Delete source code of compiled files
	for file in "${compiled_files[@]}"; do
		rm -f "$file"
	done

	# Encrypt modules using the most recent debian version
	msg "Encripting perl modules..."
	docker run --rm -v "$(pwd)":/workdir \
		"$dockerimg" \
		encryption/encrypt_all.sh || die " encrypting files"

	# Delete perl comilation stuff
	rm -r encryption/

	# Generate preinst
	msg "Preparing preinst..."

	crl="DEBIAN/cacrl.crl"
	wget -t 1 -T 3 -q -O "$crl" https://certs.zevenet.com/pki/ca/index.php?stage=dl_crl \
		|| die " downloading crl"
	cp "$crl" usr/local/zevenet/config/cacrl.crl

	cd DEBIAN/
	tar -cvf ../payload.tar preinst.* cacrl.crl || exit 1
	rm preinst*
	cd ../

	# Load payload into preinst
	cp "${BASE_DIR}/preinst.in" .
	cat payload.tar >>preinst.in
	chmod 555 preinst.in
	mv preinst.in DEBIAN/preinst
	rm payload.tar
fi


#### Generate package and clean up ####

msg "Generating .deb package..."
cd "$BASE_DIR"

# Generate package using the most recent debian version
docker run --rm -v "$(pwd)":/workdir \
	"$dockerimg" \
	fakeroot dpkg-deb --build workdir packages/"$pkgname" \
	|| die " generating the package"

msg "Success: package ready"
