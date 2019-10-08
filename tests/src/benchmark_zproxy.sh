#!/bin/bash

connections=(100 200 300 500 1000)
duration=20
threads=4
destination="172.16.1.1:9000"
file_name="test_results"
output=""
output_proc=""
time_unit=""

while getopts d:t:i:f: opts; do
    case ${opts} in
        d)
            duration=${OPTARG}
            ;;
        t)
            threads=${OPTARG}
            ;;
        i)
            destination=${OPTARG}
            ;;
        f)
            file_name=${OPTARG}
            ;;
        *)
            echo "Unknown argument ${opts}"
            ;;
   esac
done

echo "Cleaning $file_name file.."
echo "" > $file_name

for i in {0..4}
	do
		avg_req_per_sec=0
		avg_latency=0
        avg_w_errors=0
        avg_r_errors=0
        avg_timeout_errors=0
        avg_connect_errors=0
        avg_non_2xx_5xx=0
		echo "Now testing with the following configuration -c${connections[$i]} -d$duration -t$threads"
		for j in {0..9}
            do
                output=$(./wrk -c${connections[$i]} -d$duration -t$threads $destination)
                time_unit=$(echo "$output" | grep Latency | awk '{print $2}' | grep -o 's\|ms\|us')
                output_proc=$(echo "$output" | grep Latency | awk '{print $2}' | tr -d 's\|ms\|us')
                case "$output_proc" in
                    "s")
                        output_proc="$(($output_proc * 1000))"
                        ;;
                    "us")
                        output_proc=0
                        ;;
                    *)  ;;
                esac

                avg_latency="$(echo $avg_latency + $output_proc | bc )"
				output_proc="$(echo "$output" | grep Requests/sec | awk '{print $2}' | tr -d 'u')"
				avg_req_per_sec="$(echo $avg_req_per_sec + $output_proc | bc )"

                output_proc="$(echo "$output" | grep 2xx | awk '{print $5}')"
                if [ "x$output_proc" != "x" ]
                then
                    avg_non_2xx_5xx=$(($avg_non_2xx_5xx + $output_proc))
                fi

                output_proc="$(echo "$output" | grep 'Socker errors' | awk '{print $4}' |  tr -d ',')"
                if [ "x$output_proc" != "x" ]
                then
                    avg_connect_errors=$(($avg_connect_errors + $output_proc))
                fi

                output_proc="$(echo "$output" | grep 'Socker errors' | awk '{print $6}' | tr -d ',')"
                if [ "x$output_proc" != "x" ]
                then
                    avg_r_errors=$(($avg_r_errors + $output_proc))
                fi

                output_proc="$(echo "$output" | grep 'Socker errors' | awk '{print $8}' | tr -d ',')"
                if [ "x$output_proc" != "x" ]
                then
                    avg_w_errors=$(($avg_w_errors + $output_proc))
                fi

                output_proc="$(echo "$output" | grep 'Socker errors' | awk '{print $10}')"
                if [ "x$output_proc" != "x" ]
                then
                    avg_timeout_errors=$(($avg_timeour_errors + $output_proc))
                fi
			done

			avg_latency="$(echo $avg_latency/10 | bc )"
			avg_req_per_sec="$(echo $avg_req_per_sec/10 | bc )"
            avg_non_2xx_5xx="$(echo $avg_non_2xx_5xx/10 | bc)"
            avg_connect_errors="$(echo $avg_connect_errors/10 | bc)"
            avg_r_errors="$(echo $avg_r_errors/10 | bc)"
            avg_w_errors="$(echo $avg_w_errors/10 | bc)"
            avg_timeout_errors="$(echo $avg_timeout_errors/10 | bc)"

			echo	"/**     CONFIG: -c${connections[$i]} -d$duration -t$threads     **/" >> $file_name
			echo	"Avg. Latency: $avg_latency ms " >> $file_name
			echo    "Avg. Requests/sec: $avg_req_per_sec" >> $file_name
            echo    "Avg. connect errors: $avg_connect_errors" >> $file_name
            echo    "Avg. read errors: $avg_read_errors" >> $file_name
            echo    "Avg. write errors: $avg_write_errors" >> $file_name
            echo    "Avg. timeout errors: $avg_timeout_errors" >> $file_name
            echo    "Avg. Non-2xx or 3xx responses: $avg_non_2xx_5xx" >> $file_name
            echo    "" >> $file_name
	done
