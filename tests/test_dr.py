import unittest

from oci_ootb_full_stack_dr_plan_check.dr import check_plan


def complete_plan():
    return {
        "plan_type": "switchover",
        "members": [
            {"id": "db", "role": "database"},
            {"id": "app", "role": "compute"},
        ],
        "steps": [
            {"id": "s1", "name": "precheck", "is_precheck": True, "members": []},
            {"id": "s2", "name": "switch-db", "members": ["db"], "depends_on": ["s1"]},
            {"id": "s3", "name": "start-app", "members": ["app"], "depends_on": ["s2"]},
        ],
    }


def ids(findings):
    return {f.rule_id for f in findings}


class TestDr(unittest.TestCase):
    def test_complete_plan_has_no_findings(self):
        self.assertEqual(check_plan(complete_plan()), [])

    def test_drp001_member_without_step(self):
        plan = complete_plan()
        plan["members"].append({"id": "bucket", "role": "storage"})
        findings = check_plan(plan)
        drp001 = [f for f in findings if f.rule_id == "DRP001"]
        self.assertEqual(len(drp001), 1)
        self.assertEqual(drp001[0].severity, "HIGH")
        self.assertIn("switchover", drp001[0].message)

    def test_drp002_duplicate_step_id(self):
        plan = complete_plan()
        plan["steps"].append(dict(plan["steps"][1]))
        self.assertIn("DRP002", ids(check_plan(plan)))

    def test_drp003_dangling_dependency(self):
        plan = complete_plan()
        plan["steps"][1]["depends_on"] = ["ghost"]
        self.assertIn("DRP003", ids(check_plan(plan)))

    def test_drp003_unknown_member_reference(self):
        plan = complete_plan()
        plan["steps"][1]["members"] = ["ghost-member"]
        self.assertIn("DRP003", ids(check_plan(plan)))

    def test_drp004_no_precheck_step(self):
        plan = complete_plan()
        plan["steps"] = [s for s in plan["steps"] if not s.get("is_precheck")]
        self.assertIn("DRP004", ids(check_plan(plan)))

    def test_drp004_skipped_for_drill_plans(self):
        plan = complete_plan()
        plan["plan_type"] = "drill"
        plan["steps"] = [s for s in plan["steps"] if not s.get("is_precheck")]
        self.assertNotIn("DRP004", ids(check_plan(plan)))

    def test_findings_sorted_high_first(self):
        plan = complete_plan()
        plan["members"].append({"id": "bucket", "role": "storage"})
        plan["steps"][1]["depends_on"] = ["ghost"]
        findings = check_plan(plan)
        self.assertEqual(findings[0].severity, "HIGH")

    def test_missing_members_list_rejected(self):
        with self.assertRaises(ValueError):
            check_plan({"steps": []})

    def test_step_missing_id_rejected(self):
        with self.assertRaises(ValueError):
            check_plan({"members": [], "steps": [{"name": "x"}]})

    def test_member_missing_id_rejected(self):
        with self.assertRaises(ValueError):
            check_plan({"members": [{"role": "db"}], "steps": []})


if __name__ == "__main__":
    unittest.main()
