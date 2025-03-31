# Contributing

## Public Participation Invited

Meshroom is a sub-project within the Open Cybersecurity Alliance (OCA). OCA is an OASIS Open Project and welcomes participation by anyone, whether affiliated with OASIS or not. Substantive contributions and feedback are invited from all parties, following the common conventions for participation in GitHub public repository projects.

Participation is expected to be consistent with our [Code of Conduct](https://www.oasis-open.org/policies-guidelines/oasis-participants-code-of-conduct/), the licenses applicable for each repository, and the acceptance of our individual [Contributor License Agreement](https://www.oasis-open.org/open-projects/cla/oasis-open-projects-individual-contributor-license-agreement-i-cla/), generally at the time of first contribution.

## How to Contribute

Meshroom is reputed to work on python>=3.10.
CI matrix tests upon commit push are in place to ensure contributions won't break that compatibility.

### Pull Requests

We welcome pull requests! If you're planning to contribute code, please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeature`).
3. Make your changes.
4. Test your changes thoroughly.
5. Commit your changes (`git commit -m 'Add some feature'`).
6. Push to the branch (`git push origin feature/YourFeature`).
7. Open a pull request.
8. Your PR should pass CI test to be mergeable
9. Pull requests need at least one approval to get merged

### Style Guide

We strongly encourage (but don't mandate) the use of [ruff](https://docs.astral.sh/ruff/) linter

### Maintainers

Don't hesitate to reach out to [OXA project's](https://github.com/opencybersecurityalliance/oxa) contributors to become a maintainer.
Maintainers can trigger releases from the master branch using the provided [Makefile](Makefile) targets:

```bash
make patch # to release a new semver patch-level release
make minor # to release a new semver minor-level release
make major # to release a new semver major-level release
```

Release notes are automatically generated from merged PRs via github actions, as well as publishing to [pypi.org](pypi.org)


### Chat

The OCA community uses Slack for ad hoc discussion. If you wish to join the channel, use [slack invitation](https://join.slack.com/t/open-cybersecurity/shared_invite/zt-19pliofsm-L7eSSB8yzABM2Pls1nS12w) to join [Open Cybersecurity Alliance workspace](https://open-cybersecurity.slack.com/).

### About the CLA Bot

When you first submit a pull request, CLA Assistant, a bot, will check to see whether you have previously signed the [Individual CLA](https://github.com/oasis-open-projects/documentation/blob/master/policy/clas-and-special-covenant.md). If you have already done so, this check will pass. If not, the bot will comment on the PR with a link and instruction for you to click and sign the CLA electronically via GitHub. If you use different GitHub accounts for work and personal use, please make sure you are signed in to the correct account.

## Feedback

Questions or comments about this project's work may be composed as GitHub issues or comments. General questions about OASIS Open Projects may be directed to OASIS staff at [op-admin@lists.oasis-open-projects.org](op-admin@lists.oasis-open-projects.org).
