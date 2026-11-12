"""Sanity checks for OCI Full Stack Disaster Recovery plans.

OCI Full Stack Disaster Recovery (FSDR) is the built-in OCI service that
orchestrates switchover and failover of an application stack between regions
via DR protection groups and DR plans. A plan is only as good as its steps:
every protected member needs a step, steps must form a runnable order, and a
drill path should exist. This module reads a static JSON plan definition and
flags gaps. All analysis is offline; no OCI calls.
"""

from dataclasses import dataclass

SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

RECOVER_TYPES = {"switchover", "failover"}


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    subject: str
    message: str


def _plan(document):
    members = document.get("members")
    steps = document.get("steps")
    if not isinstance(members, list):
        raise ValueError("document must contain a top-level 'members' list")
    if not isinstance(steps, list):
        raise ValueError("document must contain a top-level 'steps' list")
    for member in members:
        if not member.get("id"):
            raise ValueError(f"member entry missing 'id': {member}")
    for step in steps:
        for field in ("id", "name"):
            if not step.get(field):
                raise ValueError(f"step entry missing {field!r}: {step}")
    return members, steps


def check_plan(document):
    members, steps = _plan(document)
    findings = []

    plan_type = document.get("plan_type", "switchover")
    step_by_id = {}
    seen_names = {}
    for step in steps:
        if step["id"] in step_by_id:
            findings.append(Finding("DRP002", "MEDIUM", step["id"], "duplicate step id"))
        step_by_id.setdefault(step["id"], step)
        if step["name"] in seen_names:
            findings.append(Finding("DRP002", "MEDIUM", step["id"],
                                    f"step name {step['name']!r} also used by step {seen_names[step['name']]}; duplicate names confuse operators mid-failover"))
        seen_names.setdefault(step["name"], step["id"])

    # DRP003: dangling depends_on references.
    for step in steps:
        for dep in step.get("depends_on") or []:
            if dep not in step_by_id:
                findings.append(Finding("DRP003", "MEDIUM", step["id"],
                                        f"depends on unknown step {dep!r}"))

    # DRP001: protected member with no step touching it.
    covered = set()
    for step in steps:
        for member_id in step.get("members") or []:
            covered.add(member_id)
            if member_id not in {m["id"] for m in members}:
                findings.append(Finding("DRP003", "MEDIUM", step["id"],
                                        f"references unknown member {member_id!r}"))
    for member in members:
        if member["id"] not in covered:
            findings.append(Finding("DRP001", "HIGH", member["id"],
                                    f"protected member ({member.get('role', 'resource')}) has no plan step; it would be skipped during {plan_type}"))

    # DRP004: a recovery plan with no drill/precheck step.
    if plan_type in RECOVER_TYPES and not any(s.get("is_precheck") for s in steps):
        findings.append(Finding("DRP004", "LOW", plan_type,
                                "no precheck/drill step; first real run doubles as the first rehearsal"))

    return sorted(findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.rule_id, f.subject, f.message))
