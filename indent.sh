#!/bin/sh

directories="zcutils src include"
mask="_NS_"
tmpf="/tmp/indent_tmp"
out="/tmp/indent.out"

function c_style () {
	local file="$1"

	[[ $file =~ \.([^\.]+)$ ]]
	local tmp="${tmpf}.${BASH_REMATCH[1]}"

	cp $file $tmp
	sed -Ei "s@::@$mask@g" $tmp
	./indent/checkpatch.pl --no-tree -f $tmp >$out
	sed -Ei "s@$tmp@$file@g" $out
	sed -E "s@$mask@::@g" $out
}

function cpp_style () {
	clang-format -i $1
}

function apply () {
	local file=$1

	echo  "Checking format: $file"
	echo  ""

	#~ if [[ "$file" =~ \.(cpp|h)$ ]]; then
	if [[ "$file" =~ \.cpp$ ]]; then
		cpp_style $file
	else
		c_style $file
	fi
}

function help () {
	echo "usage: $0 [file]"
	echo " - file: if this parameter is passed, the script only will check this file"
	echo ""
	echo "This script uses the linux checkpatch script in order to check the format."
	echo "If this script is executed without arguments, all project source code files"
	echo "will be analized"
}


if [[ $1 ]]; then
	if [[ "$1" =~ -h|--help ]]; then
		help
		exit 0
	fi
	if [[ ! -f $1 ]]; then
		echo "The file '$1' does not exist"
		exit 1
	fi
	apply $1
else
	for dir in $directories
	do
		for file in `find $dir -regextype egrep -regex '.*\.(h|c|cpp)$'`;
		do
			apply $file
			if [ $? -ne 0 ]; then exit 1; fi
			echo ""
			echo "--------------------------------------------------------"
			echo ""
		done
	done
fi
