# Security Audit

## Scope

Dependency vulnerability auditing is enforced by `.github/workflows/security-audit.yml` using `pip-audit` against `requirements.txt`.

## Current Evidence

- Audit workflow added on 2026-09-12.
- The first audit result for commit `fc052affa5914a8a121a057c8a2d694bf15ce7cf` must be taken from GitHub Actions before declaring dependency security status.

## Readiness Rule

A green CI suite does not by itself prove production security. Dependency findings must be reviewed and either remediated or explicitly risk-accepted with evidence before final production readiness.
