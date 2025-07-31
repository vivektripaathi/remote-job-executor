#!/usr/bin/env python3
"""
Test runner script for CLI commands.

This script provides different test execution modes:
- Full test suite
- Race condition tests only
- Unit tests only
- Integration tests only
- Quick tests (fast running tests only)
"""

import sys
import subprocess
import argparse
import os


def run_command(cmd):
    """Run shell command and return result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    return result.returncode


def install_test_dependencies():
    """Install test dependencies."""
    print("Installing test dependencies...")
    return run_command([sys.executable, "-m", "pip", "install", "-r", "test-requirements.txt"])


def run_tests(test_type="all", verbose=True, coverage=True, parallel=False):
    """Run tests based on type."""
    
    # Base pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=main", "--cov=utils", "--cov-report=term-missing"])
    
    if parallel:
        cmd.extend(["-n", "auto"])
    
    # Add test type specific options
    if test_type == "all":
        cmd.extend(["test_cli.py", "test_race_conditions.py"])
    elif test_type == "race":
        cmd.extend(["-m", "race_condition", "test_race_conditions.py"])
    elif test_type == "unit":
        cmd.extend(["-m", "unit", "test_cli.py"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration", "test_cli.py"])
    elif test_type == "quick":
        cmd.extend(["-m", "not slow", "test_cli.py"])
    elif test_type == "concurrent":
        cmd.extend(["-m", "concurrent"])
    else:
        print(f"Unknown test type: {test_type}")
        return 1
    
    return run_command(cmd)


def run_performance_test():
    """Run performance and load tests."""
    print("Running performance tests...")
    cmd = [
        sys.executable, "-m", "pytest",
        "-v",
        "--tb=short",
        "-k", "high_load or concurrent or rapid_fire",
        "test_race_conditions.py"
    ]
    return run_command(cmd)


def run_specific_test(test_name):
    """Run a specific test by name."""
    print(f"Running specific test: {test_name}")
    cmd = [
        sys.executable, "-m", "pytest",
        "-v",
        "--tb=short",
        "-k", test_name
    ]
    return run_command(cmd)


def generate_coverage_report():
    """Generate detailed coverage report."""
    print("Generating coverage report...")
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=main",
        "--cov=utils", 
        "--cov-report=html:htmlcov",
        "--cov-report=term-missing",
        "test_cli.py",
        "test_race_conditions.py"
    ]
    result = run_command(cmd)
    
    if result == 0:
        print("\nCoverage report generated in htmlcov/")
        print("Open htmlcov/index.html in your browser to view detailed coverage")
    
    return result


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="CLI Test Runner")
    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=["all", "race", "unit", "integration", "quick", "concurrent", "performance"],
        help="Type of tests to run"
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies before running tests"
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Skip coverage reporting"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )
    parser.add_argument(
        "--specific",
        type=str,
        help="Run specific test by name pattern"
    )
    parser.add_argument(
        "--coverage-report",
        action="store_true",
        help="Generate detailed coverage report"
    )
    
    args = parser.parse_args()
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    exit_code = 0
    
    # Install dependencies if requested
    if args.install_deps:
        exit_code = install_test_dependencies()
        if exit_code != 0:
            print("Failed to install test dependencies")
            return exit_code
    
    # Generate coverage report
    if args.coverage_report:
        return generate_coverage_report()
    
    # Run specific test
    if args.specific:
        return run_specific_test(args.specific)
    
    # Run performance tests  
    if args.test_type == "performance":
        return run_performance_test()
    
    # Run main tests
    coverage = not args.no_coverage
    exit_code = run_tests(
        test_type=args.test_type,
        verbose=True,
        coverage=coverage,
        parallel=args.parallel
    )
    
    if exit_code == 0:
        print(f"\n✅ All {args.test_type} tests passed!")
    else:
        print(f"\n❌ Some {args.test_type} tests failed!")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
