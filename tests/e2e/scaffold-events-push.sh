#!/bin/bash
set -e
set +x

cd $(dirname $0)/../..


if [ "$1" == "-f" ]; then
    rm -rf tests/e2e/data
fi

set -x

meshroom init tests/e2e/data

# PERSONA 1) Simulate a Example vendor who wants to integrate with Sekoia
cp -rf products tests/e2e/data/products

cd tests/e2e/data

# Create dummy 3rd-party product
meshroom create product example

# Create custom integration
meshroom create integration sekoia example events consumer --mode=push
meshroom create capability example events producer --mode=push --format=json

# Make our example->sekoia integration be fully owned by sekoia (owns_both=True)
sed -i 's/owns_both=False/owns_both=True/' products/sekoia/integrations/example/events_consumer.py

# Create instances and plug them
set +e
pass MESHROOM_SEKOIA_API_KEY | meshroom add sekoia -s API_KEY
set -e
meshroom add example
meshroom plug events example sekoia

meshroom up

meshroom publish