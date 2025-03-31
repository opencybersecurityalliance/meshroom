#!/bin/bash

SCRIPT_DIR=$(dirname "$0")
cd $SCRIPT_DIR
SCRIPTS=$(find . -maxdepth 1 -name '*.sh' ! -name 'all.sh' | sort)

for SCRIPT in $SCRIPTS; {
    echo "Executing $SCRIPT..."
    bash "$SCRIPT" -f
}