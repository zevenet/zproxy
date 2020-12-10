#!/bin/bash

source /usr/local/zevenet/bin/load_global_conf
load_global_conf

for i in $(find /usr/local/zevenet/config/ -name "*_proxy.cfg");
do
	if [[ "$proxy_ng" == 'false' ]]; then
		if [[ `grep -c WafBodySize $i` == '0' ]]; then
			echo "Adding directive 'WafBodySize' to farm $i"
			sed -Ei "0,/^\s*WafRules/{s/^\s*WafRules/WafBodySize $waf_max_body\nWafRules/}" $i
		fi
	fi
done
