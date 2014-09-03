#!/bin/sh
for tb in tb_on tb_off; do
	for acpi in acpi_on acpi_off; do
		for boot in boot_in boot_out; do
			for event in add boot removed; do
				mkdir -p "$(uname -rv)/$tb/$acpi/$boot/$event"
			done
		done
	done
done

