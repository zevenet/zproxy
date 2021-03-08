#!/bin/bash

DIR=$(dirname $0)
#~ DIR="."

cd $DIR
source "$DIR/variables"
if [[ $? -ne 0 ]]; then
	echo "Error: The 'variables' file was not found. Please, copy the 'tpl/variables.ini' file to 'variables'"
	exit 1
fi

TEST_TPL="$PWD/tpl"
REPORT_F="$PWD/$DIR/report.tmp"

TMP="/tmp/env2"
set >$TMP
export $(grep -E '^[a-zA-Z0-9_-]+=' "$TMP" | cut -d= -f1)
rm $TMP

source "$DIR/lib"

stop_debug
if [[ $DEBUG -gt 0 ]]; then
	start_debug
fi
print_help_test () {
	echo "Usage: $0 [start|stop|save_out|bck_benchmark|exec <test_dir>|all]"
	echo "  - start: it prepares the lab for testing"
	echo "  - stop: it removes the process that were started for testing"
	echo "  - save_out: it overwrites the test output files which are used to validate the tests"
	echo "  - bck_benchmark: it check the maximum backend throughput"
	echo "  - exec <test_directory>: it executes a test"
	echo "  - all: it prepares the lab, launch all tests and remove the lab"
}

start_test () {
	msg "Creating a lab with $TESTS_NUM_CL clients and $TESTS_NUM_BCK backends"
	create_proxy
	add_clients $TESTS_NUM_CL
	add_backends $TESTS_NUM_BCK
}

stop_test () {
	delete_clients $TESTS_NUM_CL
	delete_backends $TESTS_NUM_BCK
	delete_proxy
	stop_proxy_all
	msg "The lab was deleted"
}

exec_test () {
	local TEST_F="$1"
	local CFG=""
	local ZPROXY_FLAG=0
	local ERR=0
	local TMP_DIR="/tmp/variables"
	local TMP_ERR="/tmp/err.out"

	local LOCAL_PWD="$PWD"
	cd $TEST_F

	msg "Executing test '$TEST_F'"

	if [ -f "zproxy.cfg" ]; then
		start_proxy "zproxy.cfg"
		ZPROXY_FLAG=1
    else
		msg "Continue with the configuration of the previous test"
	fi

	# reloading and ctl actions cannot be applied in the same test, both are API requests
    if [[ -f "reload_zproxy.cfg" ]]; then
		reload_proxy "reload_zproxy.cfg" >$TMP_ERR
		if [[ $? -ne 0 ]]; then
			print_report "$TEST_F" "Reloading_CFG" "$TMP_ERR"
			return $ERR
		fi
	elif [[ -f "ctl.in" ]]; then
    	clean_test
		source "ctl.in"
		apply_proxy_api >$TMP_ERR
		if [[ $? -ne 0 ]]; then
			print_report "$TEST_F" "Applying_CTL" "$TMP_ERR"
			return $ERR
		fi
	fi

	PREF="vars."
	csplit "test.in" -f "$PREF" '/^###/' '{*}' >/dev/null
	CMD_NUMB=0

	for V in `ls $PREF*`
	do
		CMD_NUMB=$(expr $CMD_NUMB + 1)
		clean_test
		source $V
		local OUT_F=$(get_test_out_f $CMD_NUMB $CMD)
		local TMP_F=$(get_test_tmp_f $OUT_F)

		if [[ "$CMD" == "curl" ]]; then
			exec_request >$TMP_F 2>&1
			diff $OUT_F $TMP_F
			ERR=$?
		elif [[ "$CMD" == "average" ]]; then
			exec_average >$TMP_F 2>&1
			diff $OUT_F $TMP_F
			ERR=$?
		elif [[ "$CMD" == "benchmark" ]]; then
			echo "Executing benchmark, this will take '$BENCH_DELAY' seconds"
			exec_benchmark >$TMP_F 2>&1

			# Get percentage
			NEW_BENCH=$(cat $TMP_F)
			OLD_BENCH=$(cat $OUT_F)
			RESULT=$(perl -E "\$v=100*$NEW_BENCH/$BENCH_WITHOUT_PROXY;say int \$v;")
			echo "$RESULT" >$TMP_F

			ERR_EDGE=$(expr $OLD_BENCH + $BENCH_ERR_ACCEPTED)
			NEW_EDGE=$(expr $OLD_BENCH - $BENCH_ERR_ACCEPTED)
			debug "proxy-bench/client-bench: $NEW_BENCH/$BENCH_WITHOUT_PROXY = $RESULT%"
			if [[ $RESULT -gt $ERR_EDGE ]]; then
				echo "The new benchmark value is'$RESULT%' ant it is worse than the saved one '$OLD_BENCH+$BENCH_ERR_ACCEPTED%'"
				ERR=1
			elif [[ $RESULT -lt $NEW_EDGE ]]; then
				echo "The new benchmark value '$RESULT%' is better than the saved one '$OLD_BENCH~$BENCH_ERR_ACCEPTED%'"
				echo "Overwrite the file '$OUT_F' with the '$OUT_F.new' is you want to save it"
				cp $TMP_F "$OUT_F.new"
			fi
		else
			error "CMD variable '$CMD' is not recoignized"
			ERR=1
		fi

		if [[ $ERR -eq 0 ]]; then
			rm $TMP_F;
		else
			print_report "$TEST_F" "$CMD_NUMB" "$TMP_F"
		fi
	done
	rm "$PREF"*

	if [[ $ZPROXY_FLAG -ne 0 ]]; then stop_proxy; fi
	cd $LOCAL_PWD

	return $ERR
}

exec_all_test () {
	TEST_DIR="$DIR/tests"
	ERRORS=0

	rm -f $REPORT_F

	for LOC_DIR in `ls $TEST_DIR`; do
		exec_test "$TEST_DIR/$LOC_DIR"
		if [[ $? -ne 0 ]]; then
			echo -e "[${COLOR_ERR}Error${COLOR_NON}] $LOC_DIR"
			ERRORS=$(expr $ERRORS + 1);
		else
			echo -e "[${COLOR_SUC}OK${COLOR_NON}] $LOC_DIR"
		fi
	done

	msg "The tests finished"
	if [[ $ERRORS -ne 0 ]]; then
		echo -e "[${COLOR_ERR}FAILED${COLOR_NON}] There where '$ERRORS' tests that failed"
		echo "The report can be checked in the file '$REPORT_F'"
	else
		echo -e "[${COLOR_SUC}OK${COLOR_NON}] All tests were successfull"
	fi

	return $ERRORS
}

if [[ "$BENCH_WITHOUT_PROXY" == "" && "$1" != "bck_benchmark" ]]; then
	error "The variable 'BENCH_WITHOUT_PROXY' is not set. Please, execute '$0 bck_benchmark' and set the output value"
fi

check_dependencies

ERROR_T=0
case $1 in
"help"|"-h"|"--help")
	print_help_test
	;;
start)
	start_test
	;;
stop)
	stop_test
	;;
save_out)
	replace_test_out
	;;
exec)
	exec_test $2
	ERROR_T=$?
	;;
bck_benchmark)
	start_test
	CL=1; URL="/"; METHOD="GET";
	IP=$(get_bck_ip 1)
	VHOST="$IP:80"
	NS="$PROXY_NS"
	msg "Measuring the throughput between client and backend... (this will take $BENCH_DELAY seconds) "
	VAL=$(exec_benchmark)
	msg "The variable 'BENCH_WITHOUT_PROXY' should be set with the value '$VAL' in the file 'variables'"
	stop_test
	;;
all)
	start_test
	exec_all_test
	ERROR_T=$?
	stop_test
	;;
*)
	print_help_test
	;;
esac

exit $ERROR_T
