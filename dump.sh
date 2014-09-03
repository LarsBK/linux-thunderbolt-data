#!/bin/sh
if [ `whoami` != "root" ]
then
	echo "Please run me as root. Idiot"
	exit
fi
dmesg > dmesg.txt
lspci -vvv > lspci.txt
lspci -tv > tree.txt
chmod 644 dmesg.txt lspci.txt tree.txt
