# Contributing to Container Experience Kits

Anyone is welcome to contribute.

Please file bugs under github issues.

Please submit git commits and request PRs for review and inclusion.  Titles should be clear and concise 
with details provided in commit log explaining the purpose and method.  Please include reference to github 
issue if applicable.  Providing testing details will expedite the review process.

## Licenses

The container-experience-kits source is covered under the Apache 2.0 License.
See http://www.apache.org/licenses/

Before submitting a patch, ensure there are no licensing issues by following the Developer Certificate of 
Origin (DCO) process.

The DCO is an attestation attached to every contribution.  The commit log must have a Signed-off-by line 
(-signoff option), which certifies that you wrote it and/or have the right to submit it.  The format of the 
sign-off message is expected to appear on each commit in the pull request like so:

```
Signed-off-by: First Last <firstlast@company.domain>
```

For additional explanation, see below or at https://developercertificate.org/.

```
Developer Certificate of Origin
Version 1.1

Copyright (C) 2004, 2006 The Linux Foundation and its contributors.

Everyone is permitted to copy and distribute verbatim copies of this
license document, but changing it is not allowed.


Developer's Certificate of Origin 1.1

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I
    have the right to submit it under the open source license
    indicated in the file; or

(b) The contribution is based upon previous work that, to the best
    of my knowledge, is covered under an appropriate open source
    license and I have the right under that license to submit that
    work with modifications, whether created in whole or in part
    by me, under the same open source license (unless I am
    permitted to submit under a different license), as indicated
    in the file; or

(c) The contribution was provided directly to me by some other
    person who certified (a), (b) or (c) and I have not modified
    it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including all
    personal information I submit with it, including my sign-off) is
    maintained indefinitely and may be redistributed consistent with
    this project or the open source license(s) involved.
```

## Releases

Our primary release mechanism is based on a calendar versioning standard, formatted as YY.MM.
- YY as the last two digits of the year.
- MM as the zero padded month of the year.

Fixes for issues will most often be rolled into a follow on release.  Any exceptions added outside of a release 
cycle will be accompanied by a tag update for the current released version.
