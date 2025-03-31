# Tutorial

This tutorial guides you through

* integrating a dummy product in a meshroom project's capabilities graph
* instantiating a mesh
* setting up this mesh with real product tenants
* playing and inspect data flowing through it

We take an hypothetical intelligence-driven EDR called "myedr" as the examplar product to showcase the Meshroom CLI and underlying concepts.

### 0. Setup a meshroom project

A meshroom project is a git-backed directory on your computer. Let's setup one via

```bash
meshroom init <path>
cd <path>
```

This has scaffolded a local git repo with two directories: `products` and `instances`

We can list list our Products and Instances using
```bash
meshroom list products
meshroom list instances
```
which confirms we have no products and no instances yet.

### 1. Gather knowledge about existing products

In Meshroom's spirit, users may have already shared products definitions via, say, github.com, so you can browse public shared meshroom repos for products of interest to build your mesh.

Imagine we want to incorporate a Sekoia.io SOC platform tenant into our mesh. We can leverage existing definitions from [https://github.com/opencybersecurityalliance/meshroom/tree/master/products/sekoia](https://github.com/opencybersecurityalliance/meshroom/tree/master/products/sekoia), by simply copying the subdirectory to our project's `products/` folder:

```bash
mkdir -p tmp
curl -L -o tmp.tar.gz https://github.com/opencybersecurityalliance/meshroom/tarball/master
tar -xzf tmp.tar.gz -C tmp
mv tmp/*/example/products/sekoia products/sekoia
rm -rf tmp tmp.tar.gz
```

Happily, the sekoia product contains `@pull` hooks, allowing us to gather from Sekoia's official catalog the whole set of integrations available between Sekoia.io and 3rd-party products (here, so-called intake formats and playbook actions). Calling

```bash
meshroom pull sekoia
```

yields dozen of new products along with their own capabilities to the extent of what Sekoia.io can interop with. You'd probably need to gather and pull more product knowledge to enrich those 3rd-party product definitions and reach a sufficiently large and accurate capabilities graph to start instantiating a mesh from it.

```bash
meshroom list products
```

now shows many products available for instanciation.

### 2. Integrate your product

This tutorial assumes we're a vendor of a new product that didn't get a meshroom definition yet. So let's create it from scratch, or better, using one of the provided product capabilities templates, found under [https://github.com/opencybersecurityalliance/meshroom/tree/master/meshroom/templates/products](https://github.com/opencybersecurityalliance/meshroom/tree/master/meshroom/templates/products)

```bash
meshroom create product myedr --from edr
```

This created and scaffolded the folder `products/myedr`, with a draft definition.yaml and several other files. Of course, this is not enough to fully express myedr's full interop surface, but can be considered as a good starting point:

* some typical capabilities of a standard EDR have been automatically added to `definition.yaml` (such as an events consumer, an alerts producer, a containment executor, *etc*).
* some basic hooks have been set in boilerplate files, ready for your own implementation to define how the myedr instance can be remotely provisioned and controlled.

Since myedr is advertised as intelligence-driven, let's add three more capabilities, by editing its `definition.yaml`:

```yaml
consumes:
   threats:
      - format: stix
        mode: push
produces:
   threats:
      - format: stix
        mode: pull
executes:
   search_threat:
      - {}
```

We just added:

* a capability to **consume** the `threats` topic in **push** mode (meaning that producers will actively call our myedr instance to provide original CTI data to it), following the well-known STIX standard.
* a capability to **produce** `threats` in **pull** mode (that is, 3rd-parties will have to query an API GET endpoint to obtain CTI from our myedr instance), again as STIX bundles.
* an **execution** capability for `search_threat` action, which by default works in **push** mode (triggers must make an active call to this executor to perform the action). No particular format constraint is set for it, 3rd-parties will have to figure out the expected payload to send to get a successful search.

Let's assume that while the CTI production and consumption APIs are builtin in myedr, the threat search isn't available via API out-of-the-box. But myedr exposes a plugin mechanism to add such new external surface. We can then implement a `@setup` hook that will leverage this mechanism to automate the setup of our search_threat capabilities on a live myedr instance:

* Create the `products/myedr/search_threat.py` file containing

```py
from meshroom.decorators import setup_executor
from meshroom.model import Integration, Plug, Instance

@setup_executor("search_threat")
def setup_threat_search_api_via_myedr_plugin(integration: Integration, plug: Plug, instance: Instance):
    some_value = instance.settings.get("some_setting")
    some_secret = plug.get_secret("SOME_SECRET")
    api_key = instance.get_secret("API_KEY")
    raise NotImplementedError("Implement the setup mechanism here")
```

We'll certainly have to implement the actual python logic (using HTTP requests libraries, or whatever is required to programmatically automate the configuration of a myedr plugin).

Notice the `.get_secret` methods on the Plug and Instance objects: they allow you to securely store and retrieve sensitive configuration tokens to remotely operate your Instances. Integrations, Instances and Plugs can define arbitrary settings in their `definition.yaml` so that users get prompted for necessary values upon `meshroom up`, interactively.

Let's add those required secrets and settings to our product's `definition.yaml`

```yaml
settings:
  - name: API_KEY
    secret: true
  - name: some_setting
    default: whatever
```

This tells meshroom that any Instance of our myedr Product will require an API_KEY, stored securely, and an optional `some_setting` configuration parameter, prompted upon `meshroom add` when creating the said Instances.

We may also require settings specific for myedr to interop with a particular 3rd-party, say, Sekoia.io

Let's create a suitable Integration for that:

```bash
meshroom create integration myedr sekoia search_threat executor
```

This created a `search_threat_executor.yaml` manifest under `products/myedr/integrations/sekoia/` to hold the integration-specific settings, in the same way we did at Product level. We can then add a `settings:` section akin to the Product's one. Upon `meshroom plug search_threat some_sekoia_instance some_myedr_instance`, because myedr has defined specific settings for the executor end of this Plug, the user we'll be prompted for necessary values.

We thus demonstrated the basic concepts of:

* hooks
* product and integration manifests with settings
* how settings and secrets get prompted at `meshroom add` and `meshroom plug`. Note that you can (re-)configure those settings using `meshroom configure`, *e.g.*, when you'll instantiate your mesh on a different information system

We can confirm the existence of our new product and integrations via
```bash
meshroom list products mye
meshroom list integrations myedr
```

### 3. Create a mesh

We'll create a basic mesh of 2 Instances:

* a Sekoia.io instance called "mysekoia"
* a myedr instance called "myedr" (same name as the corresponding product)

```bash
meshroom add sekoia mysekoia
meshroom add myedr
```

Each call will prompt you for the required secrets and settings. At this stage, nothing is submitted yet to the actual tenants, meshroom only created the `instances/sekoia/mysekoia/...` files and wrote all secrets to `secrets.gpg`, ready for calling `meshroom up`

Now, let's **plug** both products, so that mysekoia can consume myedr's events and myedr can execute mysekoia's queries for threat searches.

```bash
meshroom plug events myedr mysekoia
meshroom plug search_threat mysekoia myedr
```

Oh no ! Meshroom CLI tells us that it can't find an integration for the trigger side of the second plug. Indeed, we've defined how to setup a myedr plugin to execute threat searches, but no Sekoia.io integration to actually trigger it from Sekoia.

Let's fix that

```bash
meshroom create integration sekoia myedr search_threat trigger --mode=push
```

and confirm it worked

```bash
meshroom list integrations sekoia myedr
```

Contrarily to the previous call to `meshroom create integration`, this has created many files under the `products/sekoia/integrations/myedr/` folder, where we may recognize an almost complete Sekoia.io custom playbook action as one can find examples at [https://github.com/SEKOIA-IO/automation-library](https://github.com/SEKOIA-IO/automation-library). This integration has been automatically scaffolded because Sekoia.io's vendor has defined a `@scaffold` hook for this kind of trigger. This hook generated all the boilerplate code required to build a custom playbook action that will trigger executions on 3rd-party APIs. All we need to do is to actually implement the TODOs left in the boilerplate. We won't cover this specific business here, but once you've coded your own logic, you can call again

```bash
meshroom plug search_threat mysekoia myedr
```

which should now succeed !

```bash
meshroom list instances
meshroom list plugs
```
should then show 2 instances and 2 plugs connecting them.

We're done with the mesh creation part of this tutorial, it's now time to give it life...

### 4. Meshroom up 🎉 !

Once you get a valid and satisfactory mesh of Instances and Plugs, you're ready to call

```bash
meshroom up
```

As for a docker compose stack, this command should be enough to setup and configure all your tenants, and connect the required interops to make them communicate according to the mesh's graph. Sometimes, `meshroom up` will prompt for additional settings and secret required for the runtime. Another similary with docker compose or terraform stacks is that `meshroom up` is idempotent: if the mesh is already up, meshroom will tell you resources are already up. If only part of them are up, meshroom will setup those who are down, *etc*.

To check everything works as expected, we can use two handy commands :

```bash
meshroom produce events myedr mysekoia
```

and

```bash
meshroom watch events myedr mysekoia
```

The first one will read lines from standard input and send them through `myedr-[events]->mysekoia`'s plug, so that mysekoia can consume some test events.

The second command will wait for mysekoia instance to receive those events and will print them to standard output.

Those commands are available thanks to the `@produce` and `@consume` hooks implemented in Sekoia's product definition. One is responsible for the programmatic emulation of data flowing to an integration, the other is reponsible for watching data as received by the instance to assess that the plug correctly route well-formed data to the destination product.

`@produce` hook may be defined on both the producer and consumer side of an integration: if the producer defines a `@produce` hook it takes precedence over the consumer's one, the latter's role being to **emulate** data flowing to it, instead of sending data from the real producer.

Similarly, the `@consume` hook may be defined by both the producer and the consumer: if the consumer defines it, it takes precedence over the producer's one, thus reflecting what was really received by the destination product, otherwise we fallback to the producer's one that only prints what is flowing out of the producer without guaranteeing that data is actually received at consumer side.

Here, we left the destination product without `@produce` and `@consume` hooks, so we emulate data coming from myedr (meshroom generates this flow instead of really creating the data from myedr's output) but firmly assess this data is correctly received and parsed by mysekoia.

### 5. Meshroom down

To make our mesh work, our instances have been automatically provisionned by `meshroom up` with plugins, configurations, *etc*. You may want to shutdown those capabilities and leave them in a clean state. Just call

```bash
meshroom down
```

and your mesh setup should have been withdrawn from your products tenants.

Again, this works via hooks: your myedr product should define a `@teardown` hook taking care of programmatically cleaning the plugs.

### 6. Meshroom publish

Finally, you may want to publicly release and share your mesh, and perhaps even contribute your developed integrations to the vendor's official integrations catalog.

The first stage is to simply **commit** your git-backed meshroom project. By pushing it to github, every products, integrations and mesh definitions are versioned and pullable by your colleagues. They will be able to instantiate the mesh on a different information system as long as they run `meshroom configure ...` to adapt the settings and secrets to their own environment. Of course, because secrets are stored in a GPG-encrypted file, you may also share it with colleagues using their GPG key, as you would do with a vault or secrets bundle sharing utility.

The second stage is to promote your integration as public contributions to the vendor's official catalog. For that matter, the vendor must have defined suitable `@publish` hooks for the topics of interest, so that the integration is turned into a valid package for uploading. In this tutorial, we know that Sekoia vendor has defined a `@publish` hook for triggers, that publishes individual triggers as standalone sekoia.io playbook modules for use in their playbook automation workflows. Simply call

```bash
meshroom publish sekoia myedr search_threats
```
and you should get a Github PR to [https://github.com/SEKOIA-IO/automation-library](https://github.com/SEKOIA-IO/automation-library) ready for review by Sekoia.io's integrators.

By the way, you can also play the trigger from command line via
```bash
meshroom trigger search_threats mysekoia myedr -p <param>=<value> ...
```
to test the trigger/executor relationship, as long as the vendor has defined a `@trigger` hook for the topic (or a generic one of course, which is the case for sekoia.io playbook actions).


### 7. Participate into building a community-driven global capability graph

Naturally, it would be sad if your integration work remains under your sole ownership.

Sharing with friends and colleague is something, but contributing to the global capability graph hosted at github.com/oxa/TODO would make everyone so happy !

Thank you in advance and happy meshrooming ! 👋
