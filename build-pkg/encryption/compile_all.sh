#!/bin/bash

source encryption/config

for file in "${compiled_files[@]}"; do
	encryption/compile_perl_file.sh "$file"
done
