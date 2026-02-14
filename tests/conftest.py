"""
Test Configuration and Fixtures

Provides shared fixtures and the RubricTracker for scoring
test results against the PRD requirements.
"""

import json
import os
import sys
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class RubricTracker:
    """
    Tracks test results against PRD rubric criteria.

    Generates a rubric report showing pass/fail status,
    scores, and coverage against requirements.
    """

    def __init__(self):
        self.results = []

    def record(self, category, test_name, passed, weight=1.0, details="",
               criteria=""):
        self.results.append({
            "category": category,
            "test": test_name,
            "passed": passed,
            "weight": weight,
            "details": details,
            "criteria": criteria,
        })

    def report(self):
        """Generate a formatted rubric report."""
        lines = [
            "",
            "=" * 70,
            "  ASK AI SKILLS BUILDER - TEST RUBRIC REPORT",
            "=" * 70,
            "",
        ]

        categories = {}
        for r in self.results:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r)

        total_score = 0
        total_weight = 0

        for cat, tests in categories.items():
            lines.append(f"  {cat}")
            lines.append("  " + "-" * 60)

            for t in tests:
                status = "PASS" if t["passed"] else "FAIL"
                icon = "[+]" if t["passed"] else "[-]"
                score = t["weight"] if t["passed"] else 0
                total_score += score
                total_weight += t["weight"]

                lines.append(f"    {icon} {t['test']}: {status} ({score}/{t['weight']})")
                if t["criteria"]:
                    lines.append(f"        Criteria: {t['criteria']}")
                if t["details"]:
                    lines.append(f"        Details: {t['details']}")

            lines.append("")

        pct = (total_score / total_weight * 100) if total_weight > 0 else 0
        lines.append(f"  TOTAL SCORE: {total_score}/{total_weight} ({pct:.1f}%)")
        lines.append(f"  STATUS: {'PASS' if pct >= 70 else 'FAIL'} (threshold: 70%)")
        lines.append("=" * 70)

        return "\n".join(lines)


@pytest.fixture(scope="session")
def rubric():
    """Session-scoped rubric tracker."""
    tracker = RubricTracker()
    yield tracker
    # Print report at end of session
    print(tracker.report())


@pytest.fixture
def skills_dir(tmp_path):
    """Provide a temporary skills directory for tests."""
    d = tmp_path / "skills"
    d.mkdir()
    return str(d)
