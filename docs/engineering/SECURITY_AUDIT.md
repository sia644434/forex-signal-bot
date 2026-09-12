# Security Audit

## Scope

Dependency vulnerability auditing is enforced by `.github/workflows/security-audit.yml` using `pip-audit` against `requirements.txt`.

## Current Evidence

- Security Audit workflow run `34690739394` completed successfully on 2026-09-12.
- The dependency audit step completed successfully for commit `f463087c8b1c4bc6654f0f077768cd9af6600585`.
- No dependency-audit failure was reported by that run.

## Readiness Rule

A green dependency audit does not by itself prove complete production security. Application-level security, secrets handling, deployment configuration, and live runtime behavior still require separate verification before final production readiness.
