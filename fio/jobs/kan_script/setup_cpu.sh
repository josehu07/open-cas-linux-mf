for CPUFREQ in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor;
do [ -f $CPUFREQ ] || continue; echo -n performance > $CPUFREQ; done

# cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

