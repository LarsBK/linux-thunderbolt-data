#!/bin/sh
if [ `whoami` != "root" ]
then
	echo "Please run me as root. Idiot"
	exit
fi
if [ $# -eq 0 ]
	then
	echo "please give dir as first arg"
	exit
else
	DIR="$@"
fi
echo "$DIR"
cd "$DIR"
pwd
ls -la
whoami
dmesg > ./dmesg.txt
lspci -vvv > lspci.txt
lspci -tv > tree.txt
chmod 644 dmesg.txt lspci.txt tree.txt
