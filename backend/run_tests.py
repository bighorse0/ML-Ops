#!/usr/bin/env python3
"""
Comprehensive test runner for the Feature Store as a Service platform.

This script provides various options for running tests including:
- Unit tests
- Integration tests
- API tests
- Performance tests
- Coverage reports
- Test reports generation
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
from typing import List, Optional


class TestRunner:
    """Test runner for the Feature Store platform."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.tests_dir = self.project_root / "tests"
        self.reports_dir = self.project_root / "test_reports"
        self.reports_dir.mkdir(exist_ok=True)
        
    def run_command(self, command: List[str], capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        print(f"Running: {' '.join(command)}")
        return subprocess.run(command, capture_output=capture_output, text=True, cwd=self.project_root)
    
    def run_unit_tests(self, verbose: bool = False, coverage: bool = True) -> int:
        """Run unit tests."""
        print("\n=== Running Unit Tests ===")
        
        cmd = ["python", "-m", "pytest", "tests/", "-m", "unit"]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                "--cov=api",
                "--cov=services", 
                "--cov=models",
                "--cov=utils",
                "--cov-report=term-missing",
                "--cov-report=html:test_reports/coverage_html",
                "--cov-report=xml:test_reports/coverage.xml"
            ])
        
        result = self.run_command(cmd)
        return result.returncode
    
    def run_integration_tests(self, verbose: bool = False) -> int:
        """Run integration tests."""
        print("\n=== Running Integration Tests ===")
        
        cmd = ["python", "-m", "pytest", "tests/", "-m", "integration"]
        
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd)
        return result.returncode
    
    def run_api_tests(self, verbose: bool = False) -> int:
        """Run API tests."""
        print("\n=== Running API Tests ===")
        
        cmd = ["python", "-m", "pytest", "tests/", "-m", "api"]
        
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd)
        return result.returncode
    
    def run_feature_tests(self, verbose: bool = False) -> int:
        """Run feature-related tests."""
        print("\n=== Running Feature Tests ===")
        
        cmd = ["python", "-m", "pytest", "tests/test_features.py"]
        
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd)
        return result.returncode
    
    def run_monitoring_tests(self, verbose: bool = False) -> int:
        """Run monitoring tests."""
        print("\n=== Running Monitoring Tests ===")
        
        cmd = ["python", "-m", "pytest", "tests/test_monitoring.py"]
        
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd)
        return result.returncode
    
    def run_computation_tests(self, verbose: bool = False) -> int:
        """Run computation tests."""
        print("\n=== Running Computation Tests ===")
        
        cmd = ["python", "-m", "pytest", "tests/test_computation.py"]
        
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd)
        return result.returncode
    
    def run_lineage_tests(self, verbose: bool = False) -> int:
        """Run lineage tests."""
        print("\n=== Running Lineage Tests ===")
        
        cmd = ["python", "-m", "pytest", "tests/test_lineage.py"]
        
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd)
        return result.returncode
    
    def run_user_tests(self, verbose: bool = False) -> int:
        """Run user management tests."""
        print("\n=== Running User Tests ===")
        
        cmd = ["python", "-m", "pytest", "tests/test_users.py"]
        
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd)
        return result.returncode
    
    def run_organization_tests(self, verbose: bool = False) -> int:
        """Run organization tests."""
        print("\n=== Running Organization Tests ===")
        
        cmd = ["python", "-m", "pytest", "tests/test_organizations.py"]
        
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd)
        return result.returncode
    
    def run_validation_tests(self, verbose: bool = False) -> int:
        """Run validation tests."""
        print("\n=== Running Validation Tests ===")
        
        cmd = ["python", "-m", "pytest", "tests/", "-m", "validation"]
        
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd)
        return result.returncode
    
    def run_auth_tests(self, verbose: bool = False) -> int:
        """Run authentication tests."""
        print("\n=== Running Authentication Tests ===")
        
        cmd = ["python", "-m", "pytest", "tests/", "-m", "auth"]
        
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd)
        return result.returncode
    
    def run_performance_tests(self, verbose: bool = False) -> int:
        """Run performance tests."""
        print("\n=== Running Performance Tests ===")
        
        cmd = ["python", "-m", "pytest", "tests/", "-m", "slow"]
        
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd)
        return result.returncode
    
    def run_all_tests(self, verbose: bool = False, coverage: bool = True) -> int:
        """Run all tests."""
        print("\n=== Running All Tests ===")
        
        cmd = ["python", "-m", "pytest", "tests/"]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                "--cov=api",
                "--cov=services",
                "--cov=models", 
                "--cov=utils",
                "--cov-report=term-missing",
                "--cov-report=html:test_reports/coverage_html",
                "--cov-report=xml:test_reports/coverage.xml",
                "--junitxml=test_reports/junit.xml",
                "--html=test_reports/report.html",
                "--self-contained-html"
            ])
        
        result = self.run_command(cmd)
        return result.returncode
    
    def generate_test_report(self) -> int:
        """Generate comprehensive test report."""
        print("\n=== Generating Test Report ===")
        
        cmd = [
            "python", "-m", "pytest", "tests/",
            "--html=test_reports/comprehensive_report.html",
            "--self-contained-html",
            "--junitxml=test_reports/junit.xml",
            "--cov=api",
            "--cov=services",
            "--cov=models",
            "--cov=utils", 
            "--cov-report=html:test_reports/coverage_html",
            "--cov-report=xml:test_reports/coverage.xml",
            "--cov-report=term-missing"
        ]
        
        result = self.run_command(cmd)
        return result.returncode
    
    def run_specific_test(self, test_path: str, verbose: bool = False) -> int:
        """Run a specific test file or test function."""
        print(f"\n=== Running Specific Test: {test_path} ===")
        
        cmd = ["python", "-m", "pytest", test_path]
        
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd)
        return result.returncode
    
    def run_tests_with_marker(self, marker: str, verbose: bool = False) -> int:
        """Run tests with a specific marker."""
        print(f"\n=== Running Tests with Marker: {marker} ===")
        
        cmd = ["python", "-m", "pytest", "tests/", "-m", marker]
        
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd)
        return result.returncode
    
    def check_test_coverage(self) -> int:
        """Check test coverage without running tests."""
        print("\n=== Checking Test Coverage ===")
        
        cmd = [
            "python", "-m", "pytest", "tests/",
            "--cov=api",
            "--cov=services",
            "--cov=models",
            "--cov=utils",
            "--cov-report=term-missing",
            "--cov-report=html:test_reports/coverage_html",
            "--cov-report=xml:test_reports/coverage.xml",
            "--collect-only"
        ]
        
        result = self.run_command(cmd)
        return result.returncode
    
    def list_tests(self) -> int:
        """List all available tests."""
        print("\n=== Listing All Tests ===")
        
        cmd = ["python", "-m", "pytest", "tests/", "--collect-only", "-q"]
        
        result = self.run_command(cmd)
        return result.returncode


def main():
    """Main function to run tests based on command line arguments."""
    parser = argparse.ArgumentParser(description="Feature Store Test Runner")
    
    # Test type options
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--api", action="store_true", help="Run API tests")
    parser.add_argument("--features", action="store_true", help="Run feature tests")
    parser.add_argument("--monitoring", action="store_true", help="Run monitoring tests")
    parser.add_argument("--computation", action="store_true", help="Run computation tests")
    parser.add_argument("--lineage", action="store_true", help="Run lineage tests")
    parser.add_argument("--users", action="store_true", help="Run user tests")
    parser.add_argument("--organizations", action="store_true", help="Run organization tests")
    parser.add_argument("--validation", action="store_true", help="Run validation tests")
    parser.add_argument("--auth", action="store_true", help="Run authentication tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    
    # Test execution options
    parser.add_argument("--test", type=str, help="Run specific test file or function")
    parser.add_argument("--marker", type=str, help="Run tests with specific marker")
    parser.add_argument("--list", action="store_true", help="List all available tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--report", action="store_true", help="Generate comprehensive test report")
    
    # Output options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    exit_code = 0
    
    try:
        if args.list:
            exit_code = runner.list_tests()
        elif args.test:
            exit_code = runner.run_specific_test(args.test, args.verbose)
        elif args.marker:
            exit_code = runner.run_tests_with_marker(args.marker, args.verbose)
        elif args.coverage:
            exit_code = runner.check_test_coverage()
        elif args.report:
            exit_code = runner.generate_test_report()
        elif args.all:
            exit_code = runner.run_all_tests(args.verbose, not args.no_coverage)
        elif args.unit:
            exit_code = runner.run_unit_tests(args.verbose, not args.no_coverage)
        elif args.integration:
            exit_code = runner.run_integration_tests(args.verbose)
        elif args.api:
            exit_code = runner.run_api_tests(args.verbose)
        elif args.features:
            exit_code = runner.run_feature_tests(args.verbose)
        elif args.monitoring:
            exit_code = runner.run_monitoring_tests(args.verbose)
        elif args.computation:
            exit_code = runner.run_computation_tests(args.verbose)
        elif args.lineage:
            exit_code = runner.run_lineage_tests(args.verbose)
        elif args.users:
            exit_code = runner.run_user_tests(args.verbose)
        elif args.organizations:
            exit_code = runner.run_organization_tests(args.verbose)
        elif args.validation:
            exit_code = runner.run_validation_tests(args.verbose)
        elif args.auth:
            exit_code = runner.run_auth_tests(args.verbose)
        elif args.performance:
            exit_code = runner.run_performance_tests(args.verbose)
        else:
            # Default: run all tests
            print("No specific test type specified. Running all tests...")
            exit_code = runner.run_all_tests(args.verbose, not args.no_coverage)
    
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user.")
        exit_code = 1
    except Exception as e:
        print(f"Error running tests: {e}")
        exit_code = 1
    
    if exit_code == 0:
        print("\n✅ All tests passed successfully!")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main() 