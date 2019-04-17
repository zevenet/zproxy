#!/bin/bash

# This script adds a PROFILLING line inside of each Zevenet function

cd /
find -L usr/share/perl5/Zevenet -type f -exec sed -i \
	'/^sub /{N;s/{.*/{\n\t\&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );/}' {} \;
