#!/bin/bash

# Scriptlet to auto-generate buku bookmarks
# Usage: genbm.sh n
#        where, n = number of records to generate
#
# Author: Arun Prakash Jana (engineerarun@gmail.com)

if [ "$#" -ne 1 ]; then
    echo "usage: genbm n"
    exit 1
fi

count=0

while [ $count -lt "$1" ]; do
    url=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
    buku -a https://www.$url.com --title Dummy bookmark for testing. --tag auto-generated, dummy bookmark --comment Generated from the test script $count.
    let count=count+1
done
