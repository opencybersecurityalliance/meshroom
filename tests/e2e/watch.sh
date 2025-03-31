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
cp -rf products tests/e2e/data/product

cd tests/e2e/data

# Create dummy 3rd-party product with events production capability
meshroom create product myproduct
meshroom create capability myproduct events producer --mode=push --format=json

# Create an Sekoia integration to consumer the events from myproduct
meshroom create integration sekoia myproduct events consumer --mode=push

# Create instances and plug them
set +e
pass MESHROOM_SEKOIA_API_KEY | meshroom add sekoia -s API_KEY
set -e

meshroom add myproduct
meshroom plug events myproduct sekoia
meshroom up

# Produce multiple events
meshroom produce events myproduct sekoia <<EOF
{"activity_id": 1,"activity_name": "Logon","actor": {"idp": {"name": null},"invoked_by": null,"session": {"issuer": null},"user": {"account": {"uid": "111122223333"},"credential_uid": null,"name": "anaya","type": "IAMUser","uid": "arn:aws:iam::111122223333:user/anaya","uid_alt": "AIDACKCEVSQ6C2EXAMPLE"}},"api": {"operation": "ConsoleLogin","request": {"data": null,"uid": ""},"response": {"data": {"ConsoleLogin": "Success"},"error": null,"message": null},"service": {"name": "signin.amazonaws.com"},"version": null},"category_name": "Identity & Access Management Category","category_uid": 3,"class_name": "Authentication","class_uid": 3002,"cloud": {"provider": "AWS","region": "us-east-1"},"dst_endpoint": {"svc_name": "https://console.aws.amazon.com/console/home?state=hashArgs%23&isauthcode=true"},"http_request": {"user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"},"is_mfa": true,"metadata": {"event_code": "AwsConsoleSignIn","log_provider": "CloudTrail","product": {"feature": {"name": "Management"},"name": "CloudTrail","vendor_name": "AWS","version": "1.08"},"profiles": ["cloud","datetime"],"uid": "fed06f42-cb12-4764-8c69-example","version": "1.1.0"},"observables": [{"name": "src_endpoint.ip","type": "IP Address","type_id": 2,"value": "192.0.2.0"}],"session": {"expiration_time": null},"severity": "Informational","severity_id": 1,"src_endpoint": {"ip": "192.0.2.0"},"status": "Success","status_id": 1,"time": 1699633474000,"time_dt": "2023-11-10T16:24:34Z","type_name": "Authentication: Logon","type_uid": 300201,"unmapped": {"additionalEventData": {"LoginTo": "https://console.aws.amazon.com/console/home?state=hashArgs%23&isauthcode=true","MFAIdentifier": "arn:aws:iam::111122223333:u2f/user/anaya/default-AAAAAAAABBBBBBBBCCCCCCCCDD","MobileVersion": "No"},"eventType": "AwsConsoleSignIn","recipientAccountId": "111122223333","requestParameters": null,"responseElements": {},"userIdentity": {}},"user": {"uid": "arn:aws:iam::111122223333:user/anaya","uid_alt": "AIDACKCEVSQ6C2EXAMPLE"}}
EOF

meshroom watch events sekoia