# Code signing policy

## Current status

As of 12 October 2026, ZAVIX Remote 1.5.0.1 is unsigned. An application to SignPath Foundation was submitted on 12 October 2026; the form confirmed receipt. No active signing account, certificate assignment, sponsorship approval or signed ZAVIX release has been confirmed. Signing will remain disabled until eligibility, dependency licensing and release verification are complete.

The requested attribution, if sponsorship is approved, will be:

> Free code signing provided by SignPath.io, certificate by SignPath Foundation

The Foundation would appear as the verified publisher; the software would retain its ZAVIX Remote product identity.

## Responsible maintainer

Author and reviewer: [Robson Luis da Rosa — robson-linvix](https://github.com/robson-linvix).
Release approver: Robson Luis da Rosa. GitHub MFA was confirmed by the maintainer. SignPath account MFA must be enabled before signing access is used. Contributions by other authors require maintainer review, and signing requests require explicit human release approval.

## Release provenance

Only this repository's own Windows binaries and installer are candidates for signing. Artifacts must originate from the documented GitHub Actions build and an immutable source revision, include corresponding sources and notices, and pass Windows validation. Product name and version must match the intended release. Third-party files retain their original identity and signatures; we do not claim them as ZAVIX binaries.

The current compiled release corresponds to `09c9f2a057248cc009236e405ba98b9ba469edb5`, build [38284846770](https://github.com/robson-linvix/zavix-remote-client/actions/runs/38284846770). Packaging validation is separately documented in [BUILD-ZAVIX.md](BUILD-ZAVIX.md). An MSI is planned but not released.

For this RustDesk derivative, upstream signature evidence and review history must be retained. Missing license declarations, including `hbb_common`, remain an open eligibility question. We will not describe that review as complete or use sponsorship to sign an unresolved package.

## Privacy

See [PRIVACY.md](PRIVACY.md) and the [public operational privacy information](https://remote.zavix.app/privacidade).
