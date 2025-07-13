#!/bin/bash
###var area############
qci=0
if [ $qci -eq 1 ];then
	log_ser_ip="192.168.0.253"
else
	log_ser_ip="10.0.3.254"
fi
speed="100G"
dev="eth0"
######################
#kernel config
#sysctl -w net.ipv4.tcp_timestamps=0
#sysctl -w net.ipv4.tcp_sack=1
#sysctl -w net.core.netdev_max_backlog=250000
#sysctl -w net.core.rmem_max=4194304
#sysctl -w net.core.wmem_max=4194304
#sysctl -w net.core.rmem_default=4194304
#sysctl -w net.core.wmem_default=4194304
#sysctl -w net.core.optmem_max=4194304
#sysctl -w net.ipv4.tcp_rmem="4096 87380 4194304"
#sysctl -w net.ipv4.tcp_wmem="4096 65536 4194304"
#sysctl -w net.ipv4.tcp_low_latency=1
#sysctl -w net.ipv4.tcp_adv_win_scale=1
#ethtool -C eth0 adaptive-rx off rx-usecs 0 rx-frames 0
#ethtool -C eth1 adaptive-rx off rx-usecs 0 rx-frames 0
#install lspci skip by Congo
#rpm -i pciutils-3.5.4-1.fc26.x86_64.rpm
#cp -f libkmod.so.2.2.8 /lib64/
#rm -f /lib64/libkmod.so.2
#ln -s /lib64/libkmod.so.2.2.8 /lib64/libkmod.so.2
#cp -f liblzma.so.5.0.7 /lib64/
#rm -f /lib64/liblzma.so.5
#ln -s /lib64/liblzma.so.5.0.7 /lib64/liblzma.so.5
#cp -f libpci.so.3.5.4 /lib64/
#rm -f /lib64/libpci.so.3
#ln -s /lib64/libpci.so.3.5.4 /lib64/libpci.so.3
#set mtu
#ifconfig eth1 down
#mtu_eth0=`ifconfig eth0|egrep "MTU:"|awk '{print $5}'|awk -F : '{print $2}'`
#if [ "${mtu_eth0}" != "9216" ];then
#   ifconfig eth0 mtu 9216
#   sleep
#fi
##mlnx_optimize
#rpm -i mlnx_optimize/python27-python-libs-2.7.5-7.el6.x86_64.rpm
#rpm -i mlnx_optimize/python27-python-2.7.5-7.el6.x86_64.rpm
#cp -rf /opt/rh/python27/root/usr/* /usr/
#insmod mlnx_optimize/mst_pci.ko
#insmod mlnx_optimize/mst_pciconf.ko
#cp -rf mlnx_optimize/etc/* /etc/
#cp -rf mlnx_optimize/usr/* /usr/
#/etc/init.d/mst start
#./mlnx_optimize/mlnx_tune -p HIGH_THROUGHPUT
#sleep 3
#IRQ
#NUMA_NODE=$(cat /sys/class/net/eth0/device/numa_node)
#./set_irq_affinity_bynode.sh $NUMA_NODE eth0

#check network
! ping $log_ser_ip -c 3 > /dev/null && echo "can not ping6 log server" && exit 1
if [ ! -d /mnt/test_log ];then
    mkdir /mnt/test_log
fi
##mount log server
umount /mnt/test_log
if [  $qci -eq 1 ];then
	mount  \\\\$log_ser_ip\\RACKLOG /mnt/test_log -tcifs -ousername=test,password=qcitest,rw 
else
	mount -t cifs -o username=test,password=qcitest,rw,cache=none,vers=2.0 //$log_ser_ip/RACKLOG /mnt/test_log
fi
#if [ "$?" != "0" ];then
#  echo "can not mount teset log server"
#  exit 1
#fi
##
sleep 3
ip_bcast=`ifconfig $dev|egrep 'broadcast'|awk '{print $6}'|sed 's/\./-/g'|uniq`
#echo ib_bcast=$ib_bcast
vlan=`echo server-$ip_bcast`
echo vlan=$vlan
#ser_ip=`ifconfig eth0 | grep 'inet ' |awk '{{print $2}}'`
ser_ip=`ifconfig $dev | grep 'inet ' |awk '{{print $2}}'`
if [ ! -d /mnt/test_log/$speed/$vlan ];then
    mkdir -p /mnt/test_log/$speed/$vlan
fi

if [ ! -f /mnt/test_log/$speed/$vlan/t.log ];then
    touch /mnt/test_log/$speed/$vlan/t.log
fi

# if [ ! -f /mnt/test_log/$speed/$vlan/w.log ];then
#    touch /mnt/test_log/$speed/$vlan/w.log
# fi
/iperf/iperf -s -w 8M -l 64k &
for ((i=0;;i++))
do
	sleep 1
	#  20240116 Kent change the mechanism for checking waiting server, find by {SN}_eth0.log
	if [ `ls /mnt/test_log/$speed/$vlan/ | grep _eth0.log |wc -l` == "0" ];then
		continue
	else 
		slaverlog=`ls /mnt/test_log/$speed/$vlan/ | grep _eth0.log | head -n 1`
		echo "$slaverlog"
		cli_ser=`cat /mnt/test_log/$speed/$vlan/$slaverlog|head -n 1|awk -F = '{print $1}'`
		cli_ip=`cat /mnt/test_log/$speed/$vlan/$slaverlog|head -n 1|awk -F = '{print $2}'`
		echo -e "\n $cli_ser is testing ($cli_ip)\n" |tee -a s.log
        wait_num=`ls /mnt/test_log/$speed/$vlan/ | grep eth0.log |wc -l`
        echo -e "\e[33m:$((wait_num-1)) servers wait to test\e[0m "|tee -a s.log
		cat /mnt/test_log/$speed/$vlan/$slaverlog | tee -a s.log
		echo "ser_ip=$ser_ip" > /mnt/test_log/$speed/$vlan/t.log
        echo "$cli_ser=$cli_ip" >> /mnt/test_log/$speed/$vlan/t.log
        rm -f /mnt/test_log/$speed/$vlan/$slaverlog
        sleep 10
        re=2 
        tmp=1   
        while [ "$re" == "2" ]
		do
			sleep 2
			re=`cat /mnt/test_log/$speed/$vlan/t.log|wc -l`
			let tmp=tmp+1
			echo -e "\n iperf test already test $((tmp*2)) seconds....\n" |tee -a s.log
			####time out 480 secend
			if [ "$tmp" == "240" ];then
				echo -e "\n iperf test timout, reset the iperf server\n" |tee -a s.log
				echo " " > /mnt/test_log/$speed/$vlan/t.log
				task_num=`ps -aux | grep "/iperf/iperf -s -w 8M -l 64k" | head -n 1 | awk '{print $2}'`
				kill -9 $task_num
				sleep 5
				/iperf/iperf -s -w 8M -l 64k &
				break
			fi    
		done
		sleep 10
   fi
done

