#!/usr/bin/env python3
"""
Test coverage for video helper utility specifically.
This script runs the video helper tests and reports coverage.
"""

import subprocess
import sys
import os

def main():
    """Run coverage test for video helper utility."""
    print("=== Video Helper Coverage Test ===")
    
    # Change to the project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run pytest with coverage for just the video helper
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/test_video_helper.py",
        "--cov=tests.utils.video_helper",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov_video_helper",
        "-v"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    print(f"\nExit code: {result.returncode}")
    
    # Extract coverage percentage from output
    lines = result.stdout.split('\n')
    for line in lines:
        if 'tests\\utils\\video_helper.py' in line and '%' in line:
            print(f"\n=== COVERAGE RESULT ===")
            print(line)
            
            # Check if coverage meets target
            try:
                coverage_str = line.split('%')[0].split()[-1]
                coverage_pct = int(coverage_str)
                if coverage_pct >= 95:
                    print(f"✅ COVERAGE TARGET MET: {coverage_pct}% >= 95%")
                else:
                    print(f"❌ COVERAGE TARGET NOT MET: {coverage_pct}% < 95%")
            except (ValueError, IndexError):
                print("Could not parse coverage percentage")
            break
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
