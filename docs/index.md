# Meshroom

A command-line tool to build and manage Cybersecurity Mesh Architectures (CSMA).

## Overview
As defined by Gartner, a [Cybersecurity Mesh Architecture](https://www.gartner.com/en/information-technology/glossary/cybersecurity-mesh) is a graph of interoperated cybersecurity services, each fulfilling a specific functional need (SIEM, EDR, EASM, XDR, TIP, *etc*).
Adopting the CSMA and Meshroom's philosophy means choosing an interconnected ecosystem of high-quality products with specialized scopes rather than a captive all-in-one solution.
It then means :

- Adopting standard formats and protocols rather than proprietary ones to share data and information between products (OCSF, STIX, ECS, OpenC2, syslog, CEF, *etc*)
- Leveraging Open APIs to make your products communicate and interact eachother
- Exploiting products' extensibility via plugins and open-source components to encourage user-defined interoperability

## Audience

### As a vendor : fight the N-to-N integration curse

Cybersecurity vendors know it well : integrating with other cybersecurity products burns **time and human resources**. Integration teams feel so sad when every vendor has to spend those resources developing an integration with every other vendor, without work factorization : this is the **N-to-N integration curse**. This curse mostly originates from:

* Poor adoption of **standard formats, protocols and API layouts** to interoperate cybersecurity solutions
* Lack of **open resources and documentation** to start communicating and controling a given product
* Small actors are overwhelmed by the numerous integration opportunities with major actors, but won't **factorise** their contributions to make one integration suit all 3rd-party products
* Every actor must keep **hundreds of vendor-specific integrations** up to date according to hundreds of **non-coordinated roadmaps** and constantly breaking changes

Meshroom helps cybersecurity vendors **build integrations** between their products and other solutions, keeping the integration burden as low a possible.
To do so, `meshroom` comes with a set of predefined **product templates** aligned with different market analyst categories that help the vendor to align its product integration with full category scope. If you are this vendor, by publishing your product's functional surface from one of this template, you encourage the adoption of open API layouts, formats and protocols. Whereby, you contributes to turn the N-to-N integration burden into an ideal repository of N **reusable product definitions**, where every new vendor can effortlessly plug with the N previously declared products.

### As a MSSP/MDR : setup a full cybersecurity mesh via declarative and versionable manifests

Setting up a SOC is also a time-consuming operation. Sadly, MSSPs in charge of many similar information systems will often **repeat** those very same time-consuming steps again and again, switching from one solution's configuration interface to another one's admin console. Eventually, this will involve wildly manipulating API keys and admin forms, resulting in errors, security holes and blind spots. Many MSSPs maintain a **run book** of manual setup steps, and most of them **automate** part of those steps to get a SOC up-and-running within hours or days.

Meshroom helps DevSec operators to **setup a full meshed SOC** made of dozens of tenants in a single CLI command : `meshroom up`.
Because Meshroom projects are **versioned**, you can push and **share SOC architectures** via GitHub or your favorite forge, while keeping trace of every setup and provisioning processes executed. You can think of `meshroom up` as the cyber mesh equivalent of Infrastructure-as-code's `terraform apply` or containerized stack's `docker compose up`.

When your SOC grows to dozens of interoperated products, it becomes hard to visualize where data and controls flow between them. Meshroom provides an easy to use graph model documenting:

* all capabilities exposed by the products you are using
* all available integrations they offer to other products
* all the active connections (know as `Plugs` within Meshroom) between products (aka `producer`/`consumer` and `trigger`/`executor` relationships)

### As a developer : painless developer experience to build and publish custom product additions

Many cybersecurity platforms offer extensible capabilities via **plugins**, custom formats, custom rules, custom actions, *etc*. Here again, there's no accepted standard and each vendor defines its own approach (YAML files, python code, no-code workflows, *etc*). Yet, products interoperability often rely on **contributing custom additions** to one or both ends. Of course, this scope is often badly documented, and developers are left with trial-and-error quasi-reverse ninja approaches to understand how to make product A talk to product B. In the end, you'll eventually succeed in getting a working plugin, but then face the un-coordinated maze of **homologation processes** each vendor mandates to make your contribution **public**.

Meshroom helps cybersecurity vendors to expose a **single standard contribution model** for:

* setting up **custom software additions** when interoperability mandates so
* compiling everything into a product **plugin** suitable for publication
* **publishing** as a PR to GitHub or other marketplaces

Meshroom also eases the tedious "playground" phase where developers need to **send** test data to their trial 3rd-party instances, **trigger** remote commands from their workstation, **watch** results, make changes to their integration in an agile continous development workflow:

* `meshroom produce` helps you sending data through plugged integrations
* `meshroom watch` helps you watching data flowing through a plugged integration
