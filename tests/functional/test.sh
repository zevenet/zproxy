#!/bin/bash

DIR=$(dirname $0)

cd $DIR
DIR="$PWD"
TEST_TPL="$DIR/tpl"

source "$DIR/variables"
if [[ $? -ne 0 ]]; then
	echo "Error: The 'variables' file was not found. Please, copy the 'tpl/variables.ini' file to 'variables'"
	exit 1
fi

REPORT_F="$DIR/report.tmp"
BENCH_REPORT="$DIR/benchmark_report.tmp"

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
	echo "Usage: $0 [start|stop|save_out|bck_benchmark|benchmark_report|exec [-dkfb] <test_dir>|all [-dfb]]"
	echo "  * all: it prepares the lab, launch all tests and remove the lab"
	echo "	    the -d (debug) parameter stop the tests after each command and it wait an enter to continue"
	echo "	    the -f (functional) parameter executes only the functional tests, don't the benchmark ones"
	echo "	    the -b (benchmark) parameter executes only the benchmark tests, don't the functional ones"
	echo "  * start: it prepares the lab for testing"
	echo "  * stop: it cleans the lab, removing the process and deleting the net namespaces"
	echo "  * exec [-dktb] <test_directory>: it executes a test"
	echo "	    the -d (debug) parameter stop the tests after each command and it wait an enter to continue"
	echo "	    the -k (keep running)parameter keeps zproxy running before the test finishes"
	echo "	    the -f (functional) parameter executes only the functional tests, don't the benchmark ones"
	echo "	    the -b (benchmark) parameter executes only the benchmark tests, don't the functional ones"
	echo "  * save: it overwrites the test output files which are used to validate the tests"
	echo "  * diff: it looks for the error files of the last test execution"
	echo "  * rm: it removes all .tmp files"
	echo "  * bck_benchmark: it checks the maximum backend throughput"
	echo "  * benchmark_report: it creates a report about the benchmark in the path '$BENCH_REPORT'"
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

	PREF="vars."
	csplit "test.in" -f "$PREF" '/^###/' '{*}' >/dev/null
	CMD_NUMB=0

	for V in `ls $PREF*`
	do
		CMD_NUMB=$(expr $CMD_NUMB + 1)
		clean_test
		source $V

		# output
		local OUT_DIR=$(get_test_out_dir $CMD_NUMB $CMD)
		mkdir -p $OUT_DIR

		if [[ "$CMD" == "killwrk" ]]; then
			clean_wrk
		elif [[ "$CMD" == "wait" ]]; then
			wait $TIMEOUT
		elif [[ "$CMD" == "reload" ]]; then
			reload_proxy $OUT_DIR "$FILE"
			# reloading and ctl actions cannot be applied in the same test, both are API requests
			if [[ $? -ne 0 ]]; then
				print_report "$TEST_F" "Reloading_CFG" "$TMP_ERR"
				return 1
			fi
		elif [[ "$CMD" == "ctl" ]]; then
			if [[ $FUNCTIONAL_FLAG -eq 0 ]]; then msg "The functional was skipped"; continue; fi
			apply_proxy_api $OUT_DIR
		elif [[ "$CMD" == "curl" ]]; then
			if [[ $FUNCTIONAL_FLAG -eq 0 ]]; then msg "The functional was skipped"; continue; fi
			exec_curl $OUT_DIR
		elif [[ "$CMD" == "average" ]]; then
			if [[ $FUNCTIONAL_FLAG -eq 0 ]]; then msg "The functional was skipped"; continue; fi
			exec_average $OUT_DIR
		elif [[ "$CMD" == "wrk" ]]; then
			if [[ $FUNCTIONAL_FLAG -eq 0 ]]; then msg "The functional was skipped"; continue; fi
			exec_wrk $OUT_DIR
		elif [[ "$CMD" == "benchmark" ]]; then
			if [[ $BENCHMARK_FLAG -eq 0 ]]; then msg "The benchmark was skipped"; continue; fi
			echo "Executing benchmark, this will take '$BENCH_DELAY' seconds"
			if [[ $BENCH_DELAY -eq 0 ]]; then msg "There isn't time configured, the test was skipped"; continue; fi
			exec_benchmark $OUT_DIR
		else
			rm "$PREF"*
			error "CMD variable '$CMD' is not recoignized"
		fi

		find_diff_errors $OUT_DIR >$DIFF_OUT
		if [[ -d "${OUT_DIR}_dump" ]]; then
			# add check for dump directory. After applying an API action
			find_diff_errors "${OUT_DIR}_dump" >>$DIFF_OUT
		fi
		if [[ -s $DIFF_OUT ]]; then
			TEST_ERR=1
			print_report "$TEST_F" "$OUT_DIR" "$DIFF_OUT"
		fi

		if [[ $DEBUG_FLAG -ne 0 ]]; then
			if [[ ! -f "$OUT_DIR/cmd.out.tmp" && -f "$OUT_DIR/cmd.out" ]]; then
				msg "command executed: $OUT_DIR"
				cat "$OUT_DIR/cmd.out"
				echo ""
			fi
			dev
		fi

		lookfor_segfault
	done
	rm "$PREF"*

	clean_wrk
	if [[ $ZPROXY_FLAG -ne 0 && $ZPROXY_KEEP_RUNNING -eq 0 ]]; then stop_proxy; fi

	return $TEST_ERR
}

exec_all_test () {
	TEST_DIR="$DIR/tests"
	ERRORS=0
	local LOCAL_PWD="$PWD"

	for LOC_DIR in `ls $TEST_DIR`; do

		if [ ! -d "$TEST_DIR/$LOC_DIR" ]; then
			error "The directroy '$LOC_DIR' does not exist"
		fi

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

if [[ "$BENCH_WITHOUT_PROXY" == "" && "$1" =~ "exec|all" ]]; then
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
	if [[ $? -ne 0 ]]; then
		exit 1
	fi
	;;
rm)
	rm_test_out
	;;
save)
	replace_test_out
	;;
exec)
	LOCAL_PWD="$PWD"

	if [[ $2 =~ ^-[dkfb]+$ ]]; then
		if [[ $2 =~ "d" ]]; then DEBUG_FLAG=1; fi
		if [[ $2 =~ ^[^kfb]$ ]]; then error "An option was not expected"; fi
		if [[ $2 =~ "k" ]]; then ZPROXY_KEEP_RUNNING=1; fi
		if [[ $2 =~ "f" ]]; then BENCHMARK_FLAG=0; msg "Benchmark tests were disabled"; fi
		if [[ $2 =~ "b" ]]; then FUNCTIONAL_FLAG=0; msg "Functional tests were disabled"; fi
		if [[ $BENCHMARK_FLAG == 0 && $FUNCTIONAL_FLAG == 0 ]]; then exit 0; fi
		shift;
	fi

	if [ ! -d "$2" ]; then
		error "The directroy '$2' does not exist"
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
	BENCH_DIR="$TMP_DIR/bck_benchmark"
	mkdir -p $BENCH_DIR
	exec_benchmark $BENCH_DIR
	VAL=$(cat $BENCH_DIR/benchmark.out.bm)
	cp $BENCH_DIR/benchmark.out.bm $DEFAULT_BCK_BENCH_PATH
	msg "The variable 'BENCH_WITHOUT_PROXY' should be set with the value '$VAL' in the file 'variables'"
	echo "The output was saved in $DEFAULT_BCK_BENCH_PATH"
	stop_test
	;;
benchmark_report)
	create_benchmark_report
	;;
all)
	if [[ $2 =~ ^-[dfb]+$ ]]; then
		if [[ $2 =~ "d" ]]; then DEBUG_FLAG=1; fi
		if [[ $2 =~ ^[^fb]$ ]]; then error "An option was not expected"; fi
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
	msg "The zproxy process is running, it can be stopped executing:"
	echo "./exec stop_proxy"
fi

exit $ERROR_T
