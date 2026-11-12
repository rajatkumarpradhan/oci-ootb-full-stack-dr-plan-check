#!/bin/sh
# Checks the gappy plan (a protected member with no step -> exit 2), then the complete plan.
set -u
export PYTHONPATH="$(dirname "$0")/src"

echo "=== Checking samples/gappy-plan.json ==="
python3 -m oci_ootb_full_stack_dr_plan_check samples/gappy-plan.json
echo "exit code: $? (2 = a protected member would be skipped, expected for the gappy plan)"
echo
echo "=== Checking samples/complete-plan.json ==="
python3 -m oci_ootb_full_stack_dr_plan_check samples/complete-plan.json
echo "exit code: $? (0 = every member covered, expected)"
