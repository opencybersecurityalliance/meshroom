<p align="center">
<img src="docs/logo.svg" width=170>
</p>

# Meshroom, the Cybersecurity Mesh Assistant



![release](https://img.shields.io/github/v/release/opencybersecurityalliance/meshroom?)
![build](https://img.shields.io/github/actions/workflow/status/opencybersecurityalliance/meshroom/pytest.yml?branch=master)
![MIT license](https://img.shields.io/github/license/opencybersecurityalliance/meshroom)
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Python 3.12](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)

A command-line tool to build and manage Cybersecurity Mesh Architectures (CSMA), initiated by the OXA sub-project under the [Open Cybersecurity Alliance (OCA)](https://opencybersecurityalliance.org/)

See [presentation slides](https://opencybersecurityalliance.github.io/meshroom/presentation-slides.pdf) for in-depth introduction, and [https://opencybersecurityalliance.github.io/meshroom](https://opencybersecurityalliance.github.io/meshroom) for public documentation.

I'm python-based, install me via pip using

```bash
pip install meshroom
```

### What is CSMA ?

A Cybersecurity Mesh Architecture is a graph of interoperated cybersecurity services, each fulfilling a specific functional need (SIEM, EDR, EASM, XDR, TIP, *etc*). Adopting Meshroom's philosophy means promoting an interconnected ecosystem of high-quality products with specialized scopes rather than a captive all-in-one solution.

![CSMA](docs/img/graph.svg)



### Where to start ?

Run

```bash
meshroom --help
```

or browse the documentation to start building meshes.

### Autocompletion

On Linux, you can enable meshroom's autocompletion in your terminal by running

```bash
eval "$(_MESHROOM_COMPLETE=bash_source meshroom)"
```

or adding it to your `.bashrc`