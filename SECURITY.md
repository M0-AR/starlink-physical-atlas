# Security policy

## Supported versions

| Version | Supported |
|---|---|
| 1.x | Yes |
| < 1.0 | No |

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting for this repository:

<https://github.com/M0-AR/starlink-physical-atlas/security/advisories/new>

Do not open a public issue for a vulnerability. Include the affected version or commit, a minimal reproduction, and the impact you believe is possible.

The project has no server component, accounts, credentials, telemetry, or user data. The most relevant risks are:

- a malicious dependency or build artifact;
- unsafe HTML injection in a generated page;
- a compromised release workflow or container image;
- a data file that causes excessive memory use in the browser.

## Response

The maintainer will acknowledge a report as soon as practical, investigate, and coordinate a fix and disclosure. Please allow time for a release before publishing details.

## Scope

This policy covers the code, static site, container image, and release artifacts in this repository. It does not cover the public catalog sources, GitHub, or third-party services. The atlas is not an operational safety, collision-avoidance, or traffic-management system.
