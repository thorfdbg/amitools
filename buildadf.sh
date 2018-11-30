#!/bin/bash

if [ "$#" == "0" ]; then
    echo "Usage: $0 [-b] source_directory output.adf"
    exit 5
fi
if [ "$1" == "-b" ]; then
    bootable="-B"
    shift 1
fi
python -m amitools.fs.Imager -I -F $bootable $1 $2
