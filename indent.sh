#!/bin/sh

directories="zcutils src"


function apply () {
	echo  "replacing: $1"
		indent -nbad -bap -nbc -bbo -hnl -br -brs -c33 -cd33 -ncdb -ce -ci4 \
-cli0 -d0 -di1 -nfc1 -i8 -ip0 -l80 -lp -npcs -nprs -npsl -sai \
-saf -saw -ncs -nsc -sob -nfca -cp33 -ss -ts8 -il1 $1
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

# replace files
find . -name "*~" -exec rm -rf {} \;
