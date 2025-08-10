#!/usr/bin/env python3
"""
Run PawVision tests with different test runners.
This script can be used for local development and CI/CD.
"""

import sys
import subprocess
from pathlib import Path
import argparse

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_pytest(target=None):
    """Run tests using pytest. If target is None, run all tests."""
    cmd = [sys.executable, '-m', 'pytest', '-v', '--tb=short']
    if target:
        cmd.append(target)
    else:
        cmd.append('tests/')
    print(f"🧪 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Run PawVision tests.")
    parser.add_argument('--all', action='store_true', help='Run all tests (default)')
    parser.add_argument('--file', type=str, help='Run tests in a specific file, e.g. tests/test_config.py')
    parser.add_argument('--class', dest='test_class', type=str, help='Run a specific test class, e.g. TestConfigManager')
    args = parser.parse_args()

    if args.file and args.test_class:
        # Run specific test class in a file
        target = f"{args.file}::{args.test_class}"
        success = run_pytest(target)
    elif args.file:
        # Run all tests in a file
        success = run_pytest(args.file)
    elif args.test_class:
        # Run test class in all files (pytest will search)
        target = f"tests/::{args.test_class}"
        success = run_pytest(target)
    else:
        # Default: run all tests
        success = run_pytest()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
