#!/usr/bin/env python3
"""
Test coverage configuration and reporting for EdgeMind MEC orchestration system.

Provides utilities for measuring and reporting test coverage across all components.
"""

import os
import subprocess
import sys
import unittest
from pathlib import Path


class TestCoverageConfig:
    """Configuration and utilities for test coverage measurement."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.src_dir = self.project_root / "src"
        self.tests_dir = self.project_root / "tests"
        self.coverage_dir = self.project_root / "coverage_reports"

        # Ensure coverage directory exists
        self.coverage_dir.mkdir(exist_ok=True)

    def install_coverage_tools(self):
        """Install coverage measurement tools if not present."""
        try:
            import coverage

            print("✓ Coverage.py already installed")
        except ImportError:
            print("Installing coverage.py...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "coverage"])

    def run_coverage_analysis(self, test_pattern="test_*.py"):
        """Run comprehensive coverage analysis."""
        self.install_coverage_tools()

        # Change to project root for coverage analysis
        original_cwd = os.getcwd()
        os.chdir(self.project_root)

        try:
            # Initialize coverage
            print("Initializing coverage measurement...")
            subprocess.run([sys.executable, "-m", "coverage", "erase"], check=True)

            # Run tests with coverage
            print(f"Running tests with coverage measurement...")
            test_files = list(self.tests_dir.glob(test_pattern))

            for test_file in test_files:
                print(f"  Running {test_file.name}...")
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "coverage",
                        "run",
                        "--append",
                        "--source=src",
                        str(test_file),
                    ],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    print(f"    Warning: {test_file.name} had issues:")
                    print(f"    {result.stderr}")

            # Generate coverage report
            print("Generating coverage reports...")

            # Console report
            subprocess.run(
                [sys.executable, "-m", "coverage", "report", "--show-missing"],
                check=True,
            )

            # HTML report
            html_dir = self.coverage_dir / "html"
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "coverage",
                    "html",
                    "--directory",
                    str(html_dir),
                ],
                check=True,
            )

            # XML report (for CI/CD)
            xml_file = self.coverage_dir / "coverage.xml"
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "coverage",
                    "xml",
                    "--output",
                    str(xml_file),
                ],
                check=True,
            )

            print(f"✓ Coverage reports generated in {self.coverage_dir}")
            print(f"  HTML report: {html_dir / 'index.html'}")
            print(f"  XML report: {xml_file}")

        finally:
            os.chdir(original_cwd)

    def get_coverage_summary(self):
        """Get coverage summary statistics."""
        try:
            import coverage

            cov = coverage.Coverage()
            cov.load()

            # Get coverage data
            total_lines = 0
            covered_lines = 0

            for filename in cov.get_data().measured_files():
                if "src/" in filename:
                    analysis = cov.analysis2(filename)
                    total_lines += len(analysis[1]) + len(analysis[2])
                    covered_lines += len(analysis[1])

            coverage_percentage = (
                (covered_lines / total_lines * 100) if total_lines > 0 else 0
            )

            return {
                "total_lines": total_lines,
                "covered_lines": covered_lines,
                "coverage_percentage": coverage_percentage,
                "uncovered_lines": total_lines - covered_lines,
            }

        except Exception as e:
            print(f"Error getting coverage summary: {e}")
            return None

    def generate_coverage_badge(self, coverage_percentage):
        """Generate a coverage badge for README."""
        if coverage_percentage >= 90:
            color = "brightgreen"
        elif coverage_percentage >= 80:
            color = "green"
        elif coverage_percentage >= 70:
            color = "yellowgreen"
        elif coverage_percentage >= 60:
            color = "yellow"
        else:
            color = "red"

        badge_url = f"https://img.shields.io/badge/coverage-{coverage_percentage:.1f}%25-{color}"
        badge_markdown = f"![Coverage]({badge_url})"

        return badge_markdown


class TestCoverageRunner(unittest.TestCase):
    """Test runner that includes coverage measurement."""

    def setUp(self):
        """Set up coverage configuration."""
        self.coverage_config = TestCoverageConfig()

    def test_run_all_tests_with_coverage(self):
        """Run all tests and measure coverage."""
        print("\n" + "=" * 60)
        print("RUNNING COMPREHENSIVE TEST SUITE WITH COVERAGE")
        print("=" * 60)

        # Run coverage analysis
        self.coverage_config.run_coverage_analysis()

        # Get summary
        summary = self.coverage_config.get_coverage_summary()
        if summary:
            print(f"\nCoverage Summary:")
            print(f"  Total lines: {summary['total_lines']}")
            print(f"  Covered lines: {summary['covered_lines']}")
            print(f"  Coverage: {summary['coverage_percentage']:.1f}%")

            # Generate badge
            badge = self.coverage_config.generate_coverage_badge(
                summary["coverage_percentage"]
            )
            print(f"  Badge: {badge}")

            # Coverage targets
            if summary["coverage_percentage"] >= 80:
                print("✓ Coverage target (80%) achieved!")
            else:
                print(
                    f"⚠ Coverage below target: {summary['coverage_percentage']:.1f}% < 80%"
                )

    def test_individual_module_coverage(self):
        """Test coverage for individual modules."""
        modules_to_test = [
            ("agents", "test_agents_unit.py"),
            ("swarm", "test_swarm_integration_comprehensive.py"),
            ("performance", "test_performance_orchestration.py"),
            ("mcp_tools", "test_mcp_tools_mock.py"),
            ("failure_recovery", "test_agent_failure_recovery.py"),
        ]

        print("\nModule-specific coverage analysis:")

        for module_name, test_file in modules_to_test:
            print(f"\n{module_name.upper()} MODULE:")

            # Run specific test file
            test_path = self.coverage_config.tests_dir / test_file
            if test_path.exists():
                try:
                    # Run test with coverage for this module only
                    result = subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "coverage",
                            "run",
                            "--source=src",
                            str(test_path),
                        ],
                        capture_output=True,
                        text=True,
                        cwd=self.coverage_config.project_root,
                    )

                    if result.returncode == 0:
                        print(f"  ✓ {test_file} passed")
                    else:
                        print(f"  ⚠ {test_file} had issues:")
                        print(f"    {result.stderr}")

                except Exception as e:
                    print(f"  ✗ Error running {test_file}: {e}")
            else:
                print(f"  ⚠ Test file {test_file} not found")

    def test_coverage_quality_gates(self):
        """Test coverage quality gates and requirements."""
        summary = self.coverage_config.get_coverage_summary()

        if not summary:
            self.skipTest("Coverage data not available")

        coverage_pct = summary["coverage_percentage"]

        # Quality gates
        self.assertGreaterEqual(
            coverage_pct,
            60.0,
            f"Minimum coverage (60%) not met: {coverage_pct:.1f}%",
        )

        if coverage_pct >= 80.0:
            print(f"✓ Excellent coverage: {coverage_pct:.1f}%")
        elif coverage_pct >= 70.0:
            print(f"✓ Good coverage: {coverage_pct:.1f}%")
        elif coverage_pct >= 60.0:
            print(f"⚠ Acceptable coverage: {coverage_pct:.1f}%")
        else:
            print(f"✗ Poor coverage: {coverage_pct:.1f}%")

    def test_generate_ci_coverage_report(self):
        """Generate coverage report suitable for CI/CD systems."""
        print("\nGenerating CI/CD coverage reports...")

        # Create CI-friendly coverage report
        ci_report_path = self.coverage_config.coverage_dir / "ci_report.txt"

        summary = self.coverage_config.get_coverage_summary()
        if summary:
            with open(ci_report_path, "w") as f:
                f.write("EdgeMind MEC Orchestration - Test Coverage Report\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Total Lines: {summary['total_lines']}\n")
                f.write(f"Covered Lines: {summary['covered_lines']}\n")
                f.write(f"Coverage Percentage: {summary['coverage_percentage']:.2f}%\n")
                f.write(f"Uncovered Lines: {summary['uncovered_lines']}\n\n")

                # Quality assessment
                if summary["coverage_percentage"] >= 80:
                    f.write("Quality: EXCELLENT\n")
                elif summary["coverage_percentage"] >= 70:
                    f.write("Quality: GOOD\n")
                elif summary["coverage_percentage"] >= 60:
                    f.write("Quality: ACCEPTABLE\n")
                else:
                    f.write("Quality: NEEDS_IMPROVEMENT\n")

                # Badge
                badge = self.coverage_config.generate_coverage_badge(
                    summary["coverage_percentage"]
                )
                f.write(f"\nBadge Markdown: {badge}\n")

            print(f"✓ CI report generated: {ci_report_path}")
        else:
            print("⚠ Could not generate CI report - coverage data unavailable")


def run_coverage_analysis():
    """Standalone function to run coverage analysis."""
    config = TestCoverageConfig()
    config.run_coverage_analysis()

    summary = config.get_coverage_summary()
    if summary:
        print(f"\nFinal Coverage: {summary['coverage_percentage']:.1f}%")
        return summary["coverage_percentage"]
    return 0.0


if __name__ == "__main__":
    # Check if running coverage analysis directly
    if len(sys.argv) > 1 and sys.argv[1] == "coverage":
        run_coverage_analysis()
    else:
        # Run coverage tests
        unittest.main(verbosity=2)
