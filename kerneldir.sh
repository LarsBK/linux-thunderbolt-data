#!/bin/sh
if [ $# -eq 0 ]
	then
	KERNEL=$(uname -rv)
else
	KERNEL=$1
fi
echo $KERNEL
for tb in tb_on tb_off no_tb; do
	for acpi in acpi_on acpi_off; do
		for boot in boot_in boot_out; do
			for event in add boot removed; do
				mkdir -p "$KERNEL/$tb/$acpi/$boot/$event"
				touch "$KERNEL/$tb/$acpi/$boot/$event/.ignore"
			done
		done
	done
done

