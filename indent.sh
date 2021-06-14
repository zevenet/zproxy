#!/bin/sh

directories="zcutils src"

function apply () {
	echo  "replacing: $1"
	clang-format -i $1
}

if [[ $1 ]]; then
	apply $1
else
	for dir in $directories
	do
		for file in `find $dir -regextype egrep -regex '.*\.(h|c|cpp)$'`;
		do
			apply $file
		done
	done
fi
