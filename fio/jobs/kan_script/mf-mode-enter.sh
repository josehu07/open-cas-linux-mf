#!/bin/bash

if [[ $# -ne 1 ]]; then
    echo "Please provide one argument: the mf cache mode"
    exit 1
fi

if [[ $1 -ne mfwa ]] && [[ $1 -ne mfwb ]] && [[ $1 -ne mfwt ]]; then
    echo "Unrecognized mf cache mode: $1"
    exit 2
fi

# Start multi-factor monitor kernel thread
sudo casadm -M -i 1 -j 1

# Switch to the proviced mf cache mode
sudo casadm -Q -i 1 -c $1

# List casadm to make sure
sudo casadm -L

