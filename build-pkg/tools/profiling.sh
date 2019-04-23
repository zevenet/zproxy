#!/bin/bash

# This script adds a PROFILLING line inside of each Zevenet function

# WARNING: it is important remove this line from the functions:
#	&debug(), &getGlobalConfiguration() and &zenlog()

LIB_DIR="usr/share/perl5/Zevenet"

cd ../../

if [ ! -d "$LIB_DIR" ]; then
	echo "Error, do not found the directory '$LIB_DIR'"
	exit 1;
fi

# remove current lines
find -L $LIB_DIR \
		-type f \
		-exec sed --follow-symlinks -i '/zenlog.*FILE.*LINE.*caller/d' {} \; \
		-exec sed --follow-symlinks -i '/debug.*PROFILING/d' {} \;

find -L $LIB_DIR -type f -exec sed -i \
	'/^sub /{N;s/{.*/{\n\t\&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );/}' {} \;
