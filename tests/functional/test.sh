#!/bin/bash

DIR=$(dirname $0)

cd $DIR
source "$DIR/variables"
if [[ $? -ne 0 ]]; then
	echo "Error: The 'variables' file was not found. Please, copy the 'tpl/variables.ini' file to 'variables'"
	exit 1
fi

TEST_TPL="$PWD/tpl"
REPORT_F="$PWD/$DIR/report.tmp"
rm -f $REPORT_F

TMP="$TMP_DIR/env2"
set >$TMP
export $(grep -E '^[a-zA-Z0-9_-]+=' "$TMP" | cut -d= -f1)
rm $TMP

source "$DIR/lib"

stop_debug
if [[ $DEBUG -gt 0 ]]; then
	start_debug
fi
print_help_test () {
	echo "Usage: $0 [start|stop|save_out|bck_benchmark|exec [-kfb] <test_dir>|all [-fb]]"
	echo "  * all: it prepares the lab, launch all tests and remove the lab"
	echo "	    the -f parameter executes only the functional tests, don't the benchmark ones"
	echo "	    the -b parameter executes only the benchmark tests, don't the functional ones"
	echo "  * start: it prepares the lab for testing"
	echo "  * stop: it cleans the lab, removing the process and deleting the net namespaces"
	echo "  * exec [-ktb] <test_directory>: it executes a test"
	echo "	    the -k parameter keeps zproxy running before the test finishes"
	echo "	    the -f parameter executes only the functional tests, don't the benchmark ones"
	echo "	    the -b parameter executes only the benchmark tests, don't the functional ones"
	echo "  * save: it overwrites the test output files which are used to validate the tests"
	echo "  * diff: it looks for the error files of the last test execution"
	echo "  * bck_benchmark: it checks the maximum backend throughput"
}

start_test () {
	msg "Creating a lab with $TESTS_NUM_CL clients and $TESTS_NUM_BCK backends"
	echo "Clients: $CL_SUBNET.1-$TESTS_NUM_CL"
	echo "Backends: $BCK_SUBNET.1-$TESTS_NUM_BCK"
	create_proxy
	add_clients $TESTS_NUM_CL
	add_backends $TESTS_NUM_BCK
}

stop_test () {
	delete_clients $TESTS_NUM_CL
	delete_backends $TESTS_NUM_BCK
	delete_proxy
	stop_proxy_all
	rm -rf $TMP_DIR
	msg "The lab was deleted"
}

# This function expects running with the user path in the test path in going to be executed
exec_test () {
	local TEST_F="$1"
	local CFG=""
	local ERR=0
	local TEST_ERR=0
	local ZPROXY_FLAG=0
	local TMP_ERR="$TMP_DIR/err.out"
	local DIFF_OUT="$TMP_DIR/diff.out"

	msg "## Executing test '$TEST_F'"

	if [ -f "zproxy.cfg" ]; then
		restart_proxy "zproxy.cfg"
		ZPROXY_FLAG=1
    else
		msg "Continue with the configuration of the previous test"
	fi

	# reloading and ctl actions cannot be applied in the same test, both are API requests
    if [[ -f "reload_zproxy.cfg" ]]; then
		reload_proxy "reload_zproxy.cfg" >$TMP_ERR
		if [[ $? -ne 0 ]]; then
			print_report "$TEST_F" "Reloading_CFG" "$TMP_ERR"
			return 1
		fi
	elif [[ -f "ctl.in" ]]; then
    	clean_test
		source "ctl.in"
		apply_proxy_api >$TMP_ERR
		if [[ $? -ne 0 ]]; then
			print_report "$TEST_F" "Applying_CTL" "$TMP_ERR"
			return 1
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
		local DIFF_OUT

		if [[ "$CMD" == "curl" ]]; then
			if [[ $FUNCTIONAL_FLAG -eq 0 ]]; then msg "The functional was skipped"; continue; fi
			exec_request >$TMP_F 2>&1
			diff $DIFF_OPT $OUT_F $TMP_F >$DIFF_OUT
			ERR=$?
		elif [[ "$CMD" == "average" ]]; then
			if [[ $FUNCTIONAL_FLAG -eq 0 ]]; then msg "The functional was skipped"; continue; fi
			exec_average >$TMP_F 2>&1
			diff $DIFF_OPT $OUT_F $TMP_F >$DIFF_OUT
			ERR=$?
		elif [[ "$CMD" == "benchmark" ]]; then
			if [[ $BENCHMARK_FLAG -eq 0 ]]; then msg "The benchmark was skipped"; continue; fi

			echo "Executing benchmark, this will take '$BENCH_DELAY' seconds"
			if [[ $BENCH_DELAY -eq 0 ]]; then msg "There isn't time configured, the test was skipped"; continue; fi

			exec_benchmark >$TMP_F 2>&1

			# Get percentage
			NEW_BENCH=$(cat $TMP_F)
			OLD_BENCH=$(cat $OUT_F)
			RESULT=$(perl -E "\$v=100*$NEW_BENCH/$BENCH_WITHOUT_PROXY;say int \$v;")
			echo "$RESULT" >$TMP_F
			diff $DIFF_OPT $OUT_F $TMP_F >$DIFF_OUT

			ERR_EDGE=$(expr $OLD_BENCH + $BENCH_ERR_ACCEPTED)
			NEW_EDGE=$(expr $OLD_BENCH - $BENCH_ERR_ACCEPTED)
			debug "proxy-bench/client-bench: $NEW_BENCH/$BENCH_WITHOUT_PROXY = $RESULT%"
			if [[ $RESULT -lt $ERR_EDGE ]]; then
				echo "The new benchmark value '$RESULT%' is worse than the saved one '$OLD_BENCH+$BENCH_ERR_ACCEPTED%'"
				ERR=1
			elif [[ $RESULT -gt $NEW_EDGE ]]; then
				echo "The new benchmark value '$RESULT%' is better than the saved one '$OLD_BENCH~$BENCH_ERR_ACCEPTED%'"
				echo "Overwrite the file '$OUT_F' with the '$OUT_F.new' is you want to save it"
				cp $TMP_F "$OUT_F.new"
				# update diff output with new filename
				diff $DIFF_OPT $OUT_F "$OUT_F.new" >$DIFF_OUT
			fi
		else
			error "CMD variable '$CMD' is not recoignized"
			ERR=1
		fi

		if [[ $ERR -eq 0 ]]; then
			rm $TMP_F;
		else
			TEST_ERR=1
			print_report "$TEST_F" "$CMD_NUMB" "$DIFF_OUT"
		fi
	done
	rm "$PREF"*

	if [[ $ZPROXY_FLAG -ne 0 && $ZPROXY_KEEP_RUNNING -eq 0 ]]; then stop_proxy; fi

	return $TEST_ERR
}

exec_all_test () {
	TEST_DIR="$DIR/tests"
	ERRORS=0
	local LOCAL_PWD="$PWD"

	for LOC_DIR in `ls $TEST_DIR`; do

		cd $TEST_DIR/$LOC_DIR
		exec_test "$LOC_DIR"
		if [[ $? -ne 0 ]]; then
			echo -e "[${COLOR_ERR}Error${COLOR_NON}] $LOC_DIR"
			ERRORS=$(expr $ERRORS + 1);
		else
			echo -e "[${COLOR_SUC}OK${COLOR_NON}] $LOC_DIR"
		fi
		echo ""
		echo "##########################################################################################"

		cd $LOCAL_PWD
	done

	msg "The tests finished"
	if [[ $ERRORS -ne 0 ]]; then
		echo -e "[${COLOR_ERR}FAILED${COLOR_NON}] There were '$ERRORS' tests that failed"
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
diff)
	find_diff_files
	;;
save)
	replace_test_out
	;;
exec)
	LOCAL_PWD="$PWD"

	if [[ $2 =~ ^-[ktb]+$ ]]; then
		if [[ $2 =~ "k" ]]; then ZPROXY_KEEP_RUNNING=1; fi
		if [[ $2 =~ "f" ]]; then BENCHMARK_FLAG=0; msg "Benchmark tests were disabled"; fi
		if [[ $2 =~ "b" ]]; then FUNCTIONAL_FLAG=0; msg "Functional tests were disabled"; fi
		if [[ $BENCHMARK_FLAG == 0 && $FUNCTIONAL_FLAG == 0 ]]; then exit 0; fi
		shift;
	fi
	cd $2
	exec_test $2
	ERROR_T=$?
	cd $LOCAL_PWD
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
	if [[ $2 =~ ^-[tb]+$ ]]; then
		if [[ $2 =~ "f" ]]; then BENCHMARK_FLAG=0; msg "Benchmark tests were disabled"; fi
		if [[ $2 =~ "b" ]]; then FUNCTIONAL_FLAG=0; msg "Functional tests were disabled"; fi
		if [[ $BENCHMARK_FLAG == 0 && $FUNCTIONAL_FLAG == 0 ]]; then exit 0; fi
		shift;
	fi

	start_test
	exec_all_test
	ERROR_T=$?
	stop_test
	;;
*)
	print_help_test
	;;
esac

if [[ $ZPROXY_KEEP_RUNNING -ne 0 ]]; then
	msg "The zproxy process is running, stop it after executing a new test with the following command:"
	echo "./exec stop_proxy"
fi

exit $ERROR_T
