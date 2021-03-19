#!/bin/sh

directories="zcutils src"

for dir in $directories
do
	for file in `find $dir -regextype egrep -regex '.*\.(h|c|cpp)$'`;
	do
		echo  "replacing: $file"
		indent -nbad -bap -nbc -bbo -hnl -br -brs -c33 -cd33 -ncdb -ce -ci4 \
-cli0 -d0 -di1 -nfc1 -i8 -ip0 -l80 -lp -npcs -nprs -npsl -sai \
-saf -saw -ncs -nsc -sob -nfca -cp33 -ss -ts8 -il1 $file
	done
done

# replace files
find . -name "*~" -exec rm -rf {} \;
