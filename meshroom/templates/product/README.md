# Generic Product capabilities catalog

This directory contains templates for the `meshroom create product --from <TEMPLATE>` command.

Templates categories are inspired from [Gartner's Hype Cycle for Security Operations, 2024](https://www.gartner.com/interactive/hc/5622491?ref=solrAll&refval=433161127)
and expose standard capabilities a product is expected to expose when it is belongs to a given category.

Feel free to contribute new templates to this folder, including:
* extensive description of the expected scope of the product category
* `produces` capabilities for certain topics (`events`, `alerts`, `threats`, etc)
* `consumes` capabilities for certain topics (`events`, `alerts`, `threats`, etc)
* `triggers` capabilities for certain actions (`scan`, `powershell`, `isolate`, etc)
* `executes` capabilities for certain actions (`scan`, `powershell`, `isolate`, etc)

You should avoid adding vendor-specific capabilities, instead trying to best reflect the standard functional scope of your product within a cybersecurity mesh ecosystem.

Consider those templates as a scaffolder starting point when contributing a new product definition via `meshroom create product --from <TEMPLATE>`, and make any desired changes to your scaffolded product capabilities to best reflect your product's capability. Try to stick as much as possible to the template's topics and capabilities namings to maximize the interop potential of your product in the mesh ecosystem.