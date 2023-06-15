#!/bin/sh

if [ $# -ne 1 ]
then
	echo "Usage: $0 <test-list>"
	exit 1
fi

LIST_FILE=$1

if ! [ -f $LIST_FILE ]
then
	echo "File does not exist or is not a file."
	exit 1
fi

grep '^# zproxy tests$' /etc/hosts > /dev/null
if [ $? -eq 1 ]
then
	SUITE_STARTED=1
	./test.sh start
else
	SUITE_STARTED=0
fi

for i in $(cat $LIST_FILE)
do
	./test.sh exec $i
done

if [ $SUITE_STARTED -eq 1 ]
then
	./test.sh stop
fi
