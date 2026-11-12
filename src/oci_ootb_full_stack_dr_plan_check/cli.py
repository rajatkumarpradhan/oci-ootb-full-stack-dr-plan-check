"""Command line interface for the DR plan checker."""

import argparse
import json
import sys

from .dr import SEVERITY_ORDER, check_plan

EXIT_HIGH_FINDINGS = 2
EXIT_INPUT_ERROR = 1
EXIT_OK = 0


def _load(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from exc


def _render(findings, n_members, n_steps):
    lines = []
    counts = {level: 0 for level in SEVERITY_ORDER}
    for finding in findings:
        counts[finding.severity] += 1
        lines.append(f"[{finding.severity:<6}] {finding.rule_id} {finding.subject}: {finding.message}")
    lines.append(
        "summary: {high} high, {medium} medium, {low} low finding(s); {m} member(s), {s} step(s)".format(
            high=counts["HIGH"], medium=counts["MEDIUM"], low=counts["LOW"], m=n_members, s=n_steps
        )
    )
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="oci-ootb-full-stack-dr-plan-check",
        description="Offline sanity check for OCI Full Stack DR plan definitions.",
    )
    parser.add_argument("path", help="DR plan JSON")
    args = parser.parse_args(argv)

    try:
        document = _load(args.path)
        findings = check_plan(document)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR

    print(_render(findings, len(document.get("members", [])), len(document.get("steps", []))))
    if any(f.severity == "HIGH" for f in findings):
        return EXIT_HIGH_FINDINGS
    return EXIT_OK
