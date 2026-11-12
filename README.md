# oci-ootb-full-stack-dr-plan-check

**Built-in services project (OOTB): OCI Full Stack Disaster Recovery (FSDR)**, with a custom offline checker on top. FSDR orchestrates switchover/failover of an application stack between regions via DR protection groups and DR plans. A plan is only as good as its steps: every protected member needs one, references must resolve, and a recovery plan should carry a precheck/drill step. This repo ships the Terraform template for the protection groups plus a checker that verifies a plan definition actually covers its members.

## What is custom code vs native service configuration

- **Native (OCI built-in features):** the primary/standby DR protection groups, their association, a member registration, and the switchover DR plan in `infra/main.tf`. That is configuration of OCI's own FSDR service, via Terraform.
- **Custom:** the Python checker in `src/` that reads a static JSON plan definition and flags members no step touches, duplicate step ids/names, dangling references, and missing prechecks.
- **What ran:** the checker and its 15 unit tests executed locally and in CI (Python 3.10/3.11/3.12), plus the seeded demo below.
- **What is template-only:** the Terraform in `infra/` has NOT been plan/apply validated against a tenancy. It is a structural template only; validate against the current OCI provider docs before any real apply. Nothing here talks to a live tenancy.

## What it is NOT (more honest limits)

- The checker works on a static JSON plan definition. It does not call the OCI API to read live DR plans, and it does not model step types, timeouts, or region capacity - only coverage and reference integrity.
- It cannot tell whether a step would succeed, only that it exists and is wired.

## Rules

| Rule | Severity | Finding |
| --- | --- | --- |
| DRP001 | HIGH | Protected member has no plan step; it would be skipped during switchover/failover |
| DRP002 | MEDIUM | Duplicate step id, or two steps sharing one display name |
| DRP003 | MEDIUM | Step depends on an unknown step, or references an unknown member |
| DRP004 | LOW | Recovery plan (switchover/failover) with no precheck/drill step |

Exit code 2 when any DRP001 fires; 1 on unreadable or malformed input; 0 otherwise.

## Run the local checker

Requires Python 3.10+, no third-party dependencies.

```sh
PYTHONPATH=src python3 -m oci_ootb_full_stack_dr_plan_check samples/gappy-plan.json
PYTHONPATH=src python3 -m oci_ootb_full_stack_dr_plan_check samples/complete-plan.json
```

Or the end-to-end demo:

```sh
sh demo.sh
```

Expected demo output: the gappy plan flags the storage member with no step (HIGH), the duplicate step name, and the dangling dependency, and exits 2; the complete plan reports zero findings and exits 0.

## Terraform wiring (template)

```sh
cd infra
cp terraform.tfvars.example terraform.tfvars   # fill in the compartment OCID
terraform init && terraform plan
```

This is a template - do NOT apply without reviewing against the current OCI provider docs. It was not validated against a live tenancy.

## Test

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```
