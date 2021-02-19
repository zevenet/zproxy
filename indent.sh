#!/bin/sh

indent -i8 -br -npcs -npsl -nbc $1
find . -name "*~" -exec rm -rf {} \;
