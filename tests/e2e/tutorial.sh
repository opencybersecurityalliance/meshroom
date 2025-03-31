#!/bin/bash
# E2E Test to validate the docs/tutorial.md works as expected

cd $(dirname $0)/../..
rm -rf tests/e2e/data

# ECHO

### 0. Setup a meshroom project

# A meshroom project is a git-backed directory on your computer. Let's setup one via

meshroom init tests/e2e/data
cd tests/e2e/data

# We can list our Products and Instances using
meshroom list products
meshroom list instances
# which confirms we have no products and no instances yet.

### 1. Gather knowledge about existing products

# Imagine we want to incorporate a Sekoia.io SOC platform tenant into our mesh. We can leverage existing definitions from [https://github.com/opencybersecurityalliance/meshroom/tree/master/products/sekoia](https://github.com/opencybersecurityalliance/meshroom/tree/master/example/products/sekoia), by simply copying the subdirectory to our project's `products/` folder:
mkdir -p tmp
curl -L -o tmp.tar.gz https://github.com/opencybersecurityalliance/meshroom/tarball/master
tar -xzf tmp.tar.gz -C tmp
mv tmp/*/example/products/sekoia products/sekoia
rm -rf tmp tmp.tar.gz

# Happily, the sekoia product contains `@pull` hooks, allowing us to gather from Sekoia's official catalog the whole set of integrations available between Sekoia.io and 3rd-party products (here, so-called intake formats and playbook actions). Calling
meshroom pull sekoia

# yields dozens of new products along with their own capabilities to the extent of what Sekoia.io can interop with. You'd probably need to gather and pull more product knowledge to enrich those 3rd-party product definitions and reach a sufficiently large and accurate capabilities graph to start instantiating a mesh from it.
meshroom list products

### 2. Integrate your product

rm -rf products/myedr

# This tutorial assumes we're a vendor of a new product that didn't get a meshroom definition yet. So let's create it from scratch, or better, using one of the provided product capabilities templates, found under [https://github.com/opencybersecurityalliance/meshroom/tree/master/meshroom/templates/products](https://github.com/opencybersecurityalliance/meshroom/tree/master/meshroom/templates/products)
meshroom create product myedr --from edr

cat >> products/myedr/definition.yaml <<EOF
consumes:
   threats:
      - format: stix
        mode: push
produces:
   threats:
      - format: stix
        mode: pull
   events:
      - format: json
        mode: push
executes:
   search_threat:
      - {}
EOF

# Create the `products/myedr/search_threat.py file containing
cat >> products/myedr/search_threat.py <<EOF
from meshroom.decorators import setup_executor
from meshroom.model import Integration, Plug, Instance

@setup_executor("search_threat")
def setup_threat_search_api_via_myedr_plugin(integration: Integration, plug: Plug, instance: Instance):
    some_value = instance.settings.get("some_setting")
    some_secret = plug.get_secret("SOME_SECRET")
    api_key = instance.get_secret("API_KEY")
    raise NotImplementedError("Implement the setup mechanism here")
EOF


# Let's add those required secrets and settings to our product's `definition.yaml`
cat >> products/myedr/definition.yaml <<EOF
settings:
  - name: API_KEY
    secret: true
  - name: some_setting
    default: whatever
EOF

# Let's create a suitable Integrations for that:
meshroom create integration myedr sekoia search_threat executor
meshroom create integration sekoia myedr events consumer --mode=push

# Meshroom has generated some files in products/sekoia/integrations/myedr folder, via Sekoia's @scaffold hook
# We can now implement the TODOs in those files to actually implement the logic of the integrations.

# We can confirm the existence of our new product and integrations via
meshroom list products mye
meshroom list integrations myedr

### 3. Create a mesh

pass MESHROOM_SEKOIA_API_KEY | meshroom add sekoia mysekoia -s API_KEY
echo "plop" | meshroom add myedr -s API_KEY

# Now, let's **plug** both products, so that mysekoia can consume myedr's events and myedr can execute mysekoia's queries for threat searches.

meshroom plug events myedr mysekoia
meshroom plug search_threat mysekoia myedr

# Oh no ! Meshroom CLI tells us that it can't find an integration for the trigger side of the second plug. Indeed, we've defined how to setup a myedr plugin to execute threat searches, but no Sekoia.io integration to actually trigger it from Sekoia.
# Let's fix that
meshroom create integration sekoia myedr search_threat trigger --mode=push

# and confirm it worked
meshroom list integrations sekoia myedr

# Make our sekoia->myedr integration be fully owned by sekoia (owns_both=True)
sed -i 's/owns_both=False/owns_both=True/' products/sekoia/integrations/myedr/search_threat_trigger.py

# Contrarily to the previous call to `meshroom create integration`, this has created many files under the `products/sekoia/integrations/myedr/` folder, where we may recognize an almost complete Sekoia.io custom playbook action as one can find examples at [https://github.com/SEKOIA-IO/automation-library](https://github.com/SEKOIA-IO/automation-library). This integration has been automatically scaffolded because Sekoia.io's vendor has defined a `@scaffold` hook for this kind of trigger. This hook generated all the boilerplate code required to build a custom playbook action that will trigger executions on 3rd-party APIs. All we need to do is to actually implement the TODOs left in the boilerplate. We won't cover this specific business here, but once you've coded your own logic, you can call again
meshroom plug search_threat mysekoia myedr

# should then show 2 instances and 2 plugs connecting them.
meshroom list instances
meshroom list plugs

# Let's commit our work to some git repository
git add .
git commit -a -m "Initial commit"
git remote add origin git@github.com:opencybersecurityalliance/test-meshroom-custom-integration1.git
git branch
git push -f -u origin master

### 4. Meshroom up 🎉 !

# Once you get a valid and satisfactory mesh of Instances and Plugs, you're ready to call
meshroom up

# To check everything works as expected, we can use two handy commands :
meshroom produce events myedr mysekoia <<EOF
{"activity_id": 1, "actor": {}, "process": {"cmd_line": "C:\\Windows\\system32\\wbem\\wmiprvse.exe -secured -Embedding", "created_time": 1732710936360, "file": {"type_id": 1, "hashes": [{"algorithm_id": 2, "value": "6bd539a3ab1f70081c9d99b9404826d757adc934", "algorithm": "SHA-1"}, {"algorithm_id": 3, "value": "6f2499d3a5b0ebf18dedc0b4ef0bfa2d72289bf593de53ca845e7c708f8f2098", "algorithm": "SHA-256"}, {"algorithm_id": 1, "value": "a138504be4fa90963d07bc1e277e874d", "algorithm": "MD5"}], "name": "WmiPrvSE.exe", "path": "C:\\Windows\\System32\\wbem\\WmiPrvSE.exe", "signature": {"algorithm_id": 99, "algorithm": "Other", "certificate": {"fingerprints": [{"algorithm_id": 3, "value": "e866d202865ed3d83c35dff4cde3a2d0fc1d2b17c084e8b26dd0ca28a8c75cfb", "algorithm": "SHA-256"}, {"algorithm_id": 1, "value": "ff82bc38e1da5e596df374c53e3617f7eda36b06", "algorithm": "MD5"}], "issuer": "Microsoft Windows Production PCA 2011", "serial_number": "330000023241fb59996dcc4dff000000000232", "subject": "Microsoft Windows"}, "state": "Valid", "state_id": 1}, "size": 496128, "type": "Regular File"}, "integrity": "System", "integrity_id": 5, "lineage": ["C:\\Windows\\System32\\svchost.exe", "C:\\Windows\\System32\\services.exe", "C:\\Windows\\System32\\wininit.exe"], "name": "WmiPrvSE.exe", "parent_process": {"cmd_line": "C:\\Windows\\system32\\svchost.exe -k DcomLaunch -p", "file": {"type_id": 1, "name": "svchost.exe", "path": "C:\\Windows\\System32\\svchost.exe", "type": "Regular File"}, "integrity": "System", "name": "svchost.exe", "parent_process": {"cmd_line": "C:\\Windows\\system32\\services.exe", "file": {"type_id": 1, "name": "services.exe", "path": "C:\\Windows\\System32\\services.exe", "type": "Regular File"}, "integrity": "System", "name": "services.exe", "uid": "4de77ae9-0aca-4626-bc02-00c357a01d93"}, "pid": 880, "uid": "4de77ae9-0aca-4626-7003-00f198123c19"}, "pid": 584, "uid": "4de77ae9-0aca-4626-4802-00e84f9c9b8f", "user": {"name": "NT AUTHORITY\\NETWORK SERVICE", "uid": "S-1-5-20"}}, "device": {"hostname": "hlab-windows-10", "type": "Desktop", "type_id": 2, "agent_list": [{"type_id": 1, "type": "Endpoint Detection and Response", "uid": "7198e7a9-0aca-4626-b136-01f7990cf2a4", "version": "9.11.0-c5baf8685a-dirty", "vendor_name": "Harfanglab", "name": "hurukai"}], "os": {"name": "Windows 10 Enterprise", "type_id": 100, "build": "10.0.19041", "type": "Windows", "version": "Windows 10 Enterprise"}}, "category_uid": 1, "class_uid": 1007, "metadata": {"product": {"vendor_name": "Harfanglab", "name": "hurukai", "uid": "cd135f97-c437-4e26-b489-7fb7f6a59ebf", "version": "9.11.0"}, "version": "1.3.0", "tenant_uid": "123456"}, "severity_id": 0, "time": 1732710936360, "type_uid": 100701}
EOF

timeout 30 meshroom watch events myedr mysekoia

### 5. Meshroom down

meshroom down

### 6. Meshroom publish

meshroom publish sekoia myedr search_threats

# By the way, you can also play the trigger from command line via
# meshroom trigger search_threats mysekoia myedr
