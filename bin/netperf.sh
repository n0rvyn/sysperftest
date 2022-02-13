#!/bin/bash
#
# set -e
# for starting netperf client
HOME_OF_ALL='/tmp/sysperftest'
cd ${HOME_OF_ALL} || exit 127
log_prefix="${HOME_OF_ALL}/sysperftest_$(date +%y%m%d_%H%M)_$(hostname)_netperf"
pkg_prefix="netperf-netperf-2.7"

# print PID of script
echo "netperf client pid: " $$

# opts='make clean && make && make install'
find ${HOME_OF_ALL} -maxdepth 2 -type f -name "${pkg_prefix}*.gz" -exec tar -xvf {} \;
_HOME=$(find ${HOME_OF_ALL} -maxdepth 2 -type d -name "*${pkg_prefix}*" -print | head -1)
cd $_HOME || exit 127
# todo must test ARM-based machine
# shellcheck disable=SC2006
if [[ ! `which netperf` ]]; then
  # make clean && make && make install
  ./configure && make && make install
fi

no_cpus=$(lscpu | grep "^CPU...:" | awk -F':' '{print $2}' | sed 's/  //g')
total_mem_mib=$(free -m | grep "Mem" | awk '{print $2}')
total_swap_mib=$(free -m | grep "Swap" | awk '{print $2}')
no_disks=$(lsblk | grep -vE "├|─|NAME" | wc -l)

# take ip address +1 or -1 based on the last bite of own address
server_ipaddr1=$(ip a | grep -w inet | grep -wv lo | awk '{print $2}' | awk -F '/' '{print $1}' | awk -F'.' '{print $1"."$2"."$3"."($4+1)}')
server_ipaddr2=$(ip a | grep -w inet | grep -wv lo | awk '{print $2}' | awk -F '/' '{print $1}' | awk -F'.' '{print $1"."$2"."$3"."($4-1)}')

# choose the one connectable
ping -c1 -W1 $server_ipaddr1 &>/dev/null && server_ipaddr=$server_ipaddr1 || server_ipaddr=$server_ipaddr2
ping -c1 -W1 $server_ipaddr &>/dev/null || server_ipaddr='localhost'

# start netperf server
netserver >/dev/null

# TCP I/O Stream
netperf -t TCP_STREAM -H $server_ipaddr -l 3 | tee -a ${log_prefix}_tcp_stream.log

# TCP transfer rate
netperf -t TCP_RR -H $server_ipaddr -l 3 | tee -a ${log_prefix}_tcp_rr.log

# UDP Bite width
netperf -t UDP_STREAM -H $server_ipaddr -l 3 | tee -a ${log_prefix}_udp_stream.log

# UDP transfer rate
netperf -t UDP_RR -H $server_ipaddr -l 3 | tee -a ${log_prefix}_udp_rr.log