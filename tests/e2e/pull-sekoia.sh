#!/bin/bash
set -e
set +x


cd $(dirname $0)/../..


if [ "$1" == "-f" ]; then
    rm -rf tests/e2e/data
fi

set -x

meshroom init tests/e2e/data

# PERSONA 1) Simulate a vendor who defines the Sekoia product
cp -rf products tests/e2e/data/products

cd tests/e2e/data
meshroom pull sekoia


# PERSONA 2) The end user experience starts here

set +e
pass MESHROOM_SEKOIA_API_KEY | meshroom add sekoia -s API_KEY
set -e

meshroom list products sek
meshroom list instances sek

meshroom list integrations sekoia

meshroom add apache_http_server
meshroom add aws_vpc_flow_logs aws

meshroom plug --debug events apache_http_server sekoia
meshroom plug events aws sekoia

meshroom up

meshroom down

meshroom up
