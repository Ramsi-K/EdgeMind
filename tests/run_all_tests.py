#!/usr/bin/env python3
"""
Comprehensive test runner for EdgeMind MEC orchestration system.

Runs all test suites and provides detailed reporting on test results and coverage.
"""

import os
import sys
import time
import unittest
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()


class EdgeMindTestRunner:
    """Comprehensive test runner for EdgeMind system."""

    def __init__(self):
        self.tests_dir = Path(__file__).parent
        self.test_results = {}
        self.total_start_time = None

    def discover_and_run_tests(self):
        """Discover and run all test suites."""
        print("EdgeMind MEC Orchestration - Comprehensive Test Suite")
        print("=" * 60)

        self.total_start_time = time.time()

        # Test suites to run in order
        test_suites = [
            ("Unit Tests - Agents", "test_agents_unit.py"),
            (
                "Integration Tests - Swarm Coordination",
                "test_swarm_integration_comprehensive.py",
            ),
            (
                "Performance Tests - Orchestration",
                "test_performance_orchestration.py",
            ),
            ("Mock MCP Tools Tests", "test_mcp_tools_mock.py"),
            ("Failure Recovery Tests", "test_agent_failure_recovery.py"),
            ("Existing Integration Tests", "test_swarm_integration.py"),
            ("Existing Strands Tests", "test_strands_swarm.py"),
        ]

        total_tests = 0
        total_failures = 0
        total_errors = 0

        for suite_name, test_file in test_suites:
            print(f"\n{suite_name}")
            print("-" * len(suite_name))

            test_path = self.tests_dir / test_file
            if not test_path.exists():
                print(f"⚠ Test file {test_file} not found - skipping")
                continue

            # Run test suite
            suite_start = time.time()
            result = self.run_test_suite(test_path)
            suite_duration = time.time() - suite_start

            # Record results
            self.test_results[suite_name] = {
                "file": test_file,
                "duration": suite_duration,
                "tests_run": result.testsRun,
                "failures": len(result.failures),
                "errors": len(result.errors),
                "success": result.wasSuccessful(),
            }

            # Update totals
            total_tests += result.testsRun
            total_failures += len(result.failures)
            total_errors += len(result.errors)

            # Print suite summary
            status = "✓ PASSED" if result.wasSuccessful() else "✗ FAILED"
            print(f"{status} - {result.testsRun} tests in {suite_duration:.2f}s")

            if result.failures:
                print(f"  Failures: {len(result.failures)}")
            if result.errors:
                print(f"  Errors: {len(result.errors)}")

        # Print overall summary
        total_duration = time.time() - self.total_start_time
        self.print_final_summary(
            total_tests, total_failures, total_errors, total_duration
        )

        return total_failures + total_errors == 0

    def run_test_suite(self, test_file_path):
        """Run a single test suite and return results."""
        # Load the test module
        loader = unittest.TestLoader()

        # Import the test module dynamically
        import importlib.util

        spec = importlib.util.spec_from_file_location("test_module", test_file_path)
        test_module = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(test_module)
            suite = loader.loadTestsFromModule(test_module)
        except Exception as e:
            print(f"✗ Error loading {test_file_path.name}: {e}")
            # Create a dummy result for failed imports
            result = unittest.TestResult()
            result.testsRun = 0
            result.errors = [("Import Error", str(e))]
            return result

        # Run the tests
        runner = unittest.TextTestRunner(
            verbosity=1,
            stream=sys.stdout,
            buffer=True,  # Capture stdout/stderr during tests
        )

        return runner.run(suite)

    def print_final_summary(
        self, total_tests, total_failures, total_errors, total_duration
    ):
        """Print comprehensive test summary."""
        print("\n" + "=" * 60)
        print("FINAL TEST SUMMARY")
        print("=" * 60)

        # Overall statistics
        print(f"Total Tests Run: {total_tests}")
        print(f"Total Duration: {total_duration:.2f} seconds")
        print(
            f"Average Test Time: {(total_duration / total_tests):.3f}s"
            if total_tests > 0
            else "N/A"
        )

        # Results breakdown
        passed_tests = total_tests - total_failures - total_errors
        print(f"\nResults:")
        print(f"  ✓ Passed: {passed_tests}")
        print(f"  ✗ Failed: {total_failures}")
        print(f"  ⚠ Errors: {total_errors}")

        # Success rate
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            print(f"  Success Rate: {success_rate:.1f}%")

        # Per-suite breakdown
        print(f"\nPer-Suite Results:")
        for suite_name, results in self.test_results.items():
            status_icon = "✓" if results["success"] else "✗"
            print(
                f"  {status_icon} {suite_name}: {results['tests_run']} tests, {results['duration']:.2f}s"
            )

            if results["failures"] > 0 or results["errors"] > 0:
                print(
                    f"    Failures: {results['failures']}, Errors: {results['errors']}"
                )

        # Overall result
        print(f"\n{'='*60}")
        if total_failures == 0 and total_errors == 0:
            print("🎉 ALL TESTS PASSED!")
            print("EdgeMind MEC orchestration system is ready for deployment.")
        else:
            print("❌ SOME TESTS FAILED")
            print(
                f"Please review {total_failures + total_errors} failing test(s) before deployment."
            )
        print("=" * 60)

    def run_performance_benchmarks(self):
        """Run performance-specific benchmarks."""
        print("\n" + "=" * 60)
        print("PERFORMANCE BENCHMARKS")
        print("=" * 60)

        # Import performance test module
        try:
            from test_performance_orchestration import (
                TestOrchestrationPerformance,
            )

            # Create test suite with performance tests only
            suite = unittest.TestSuite()

            # Add specific performance tests
            performance_tests = [
                "test_single_threshold_breach_performance",
                "test_threshold_check_only_performance",
                "test_sub_100ms_orchestration_simulation",
            ]

            for test_name in performance_tests:
                if hasattr(TestOrchestrationPerformance, test_name):
                    suite.addTest(TestOrchestrationPerformance(test_name))

            # Run performance tests
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)

            print(
                f"\nPerformance Tests: {result.testsRun} run, {len(result.failures)} failed"
            )

        except ImportError as e:
            print(f"Could not run performance benchmarks: {e}")

    def validate_test_environment(self):
        """Validate that the test environment is properly set up."""
        print("Validating test environment...")

        # Check required modules
        required_modules = [
            "src.agents.orchestrator_agent",
            "src.swarm.swarm_coordinator",
            "src.orchestrator.threshold_monitor",
            "config",
        ]

        missing_modules = []
        for module_name in required_modules:
            try:
                __import__(module_name)
                print(f"  ✓ {module_name}")
            except ImportError:
                missing_modules.append(module_name)
                print(f"  ✗ {module_name}")

        if missing_modules:
            print(f"\n⚠ Missing modules: {missing_modules}")
            print("Please ensure all source modules are available.")
            return False

        # Check environment variables
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            print("  ✓ API key loaded from environment")
        else:
            print("  ⚠ No API key found - tests may fail")

        print("✓ Test environment validation complete\n")
        return True


def main():
    """Main test runner entry point."""
    runner = EdgeMindTestRunner()

    # Validate environment
    if not runner.validate_test_environment():
        print("Environment validation failed. Exiting.")
        return 1

    # Run comprehensive test suite
    success = runner.discover_and_run_tests()

    # Run performance benchmarks if main tests pass
    if success:
        runner.run_performance_benchmarks()

    # Return appropriate exit code
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
