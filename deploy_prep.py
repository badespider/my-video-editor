#!/usr/bin/env python3
"""
Deployment Preparation Script
Rule 5.1: Comprehensive Testing & Deployment Preparation

This script prepares the AI Video Editor application for deployment by:
1. Running comprehensive tests
2. Generating coverage reports
3. Validating configuration
4. Creating deployment artifacts
5. Checking system requirements
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class DeploymentPreparation:
    """Handles all deployment preparation tasks."""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.results = {
            "timestamp": time.time(),
            "tests": {},
            "coverage": {},
            "validation": {},
            "artifacts": {},
            "ready_for_deployment": False
        }
        
    def run_comprehensive_tests(self) -> Dict:
        """Run the complete test suite with coverage."""
        print("🧪 Running comprehensive test suite...")
        
        try:
            # Run tests with coverage
            cmd = [
                "pytest", 
                "tests/",
                "--cov=backend",
                "--cov=coordinator", 
                "--cov=workers",
                "--cov=utils",
                "--cov-report=html:htmlcov",
                "--cov-report=xml",
                "--cov-report=term-missing",
                "--junitxml=test-results.xml",
                "-v"
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                cwd=self.project_root
            )
            
            self.results["tests"] = {
                "exit_code": result.returncode,
                "passed": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            print(f"✅ Tests completed with exit code: {result.returncode}")
            
            # Parse test results
            self._parse_test_results()
            
            return self.results["tests"]
            
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            self.results["tests"]["error"] = str(e)
            return self.results["tests"]
    
    def _parse_test_results(self):
        """Parse test results from JUnit XML."""
        try:
            import xml.etree.ElementTree as ET
            
            xml_file = self.project_root / "test-results.xml"
            if xml_file.exists():
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                self.results["tests"]["summary"] = {
                    "total": int(root.get("tests", 0)),
                    "failures": int(root.get("failures", 0)),
                    "errors": int(root.get("errors", 0)),
                    "skipped": int(root.get("skipped", 0)),
                    "time": float(root.get("time", 0))
                }
                
                # Calculate pass rate
                total = self.results["tests"]["summary"]["total"]
                failures = self.results["tests"]["summary"]["failures"]
                errors = self.results["tests"]["summary"]["errors"]
                passed = total - failures - errors
                
                self.results["tests"]["summary"]["passed"] = passed
                self.results["tests"]["summary"]["pass_rate"] = (passed / total * 100) if total > 0 else 0
                
        except Exception as e:
            print(f"⚠️  Could not parse test results: {e}")
    
    def validate_configuration(self) -> Dict:
        """Validate application configuration for deployment."""
        print("⚙️  Validating configuration...")
        
        validation_results = {
            "config_files": {},
            "environment": {},
            "dependencies": {},
            "directories": {}
        }
        
        # Check essential config files
        config_files = [
            "config.py",
            "requirements.txt",
            "pytest.ini",
            "backend/__init__.py",
            "backend/api.py"
        ]
        
        for config_file in config_files:
            file_path = self.project_root / config_file
            validation_results["config_files"][config_file] = {
                "exists": file_path.exists(),
                "size": file_path.stat().st_size if file_path.exists() else 0
            }
        
        # Check essential directories
        directories = [
            "backend",
            "tests",
            "utils",
            "workers",
            "uploads",
            "outputs"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            validation_results["directories"][directory] = {
                "exists": dir_path.exists(),
                "is_dir": dir_path.is_dir() if dir_path.exists() else False
            }
        
        # Check Python version
        validation_results["environment"]["python_version"] = sys.version
        validation_results["environment"]["python_executable"] = sys.executable
        
        # Check key dependencies
        try:
            import fastapi
            validation_results["dependencies"]["fastapi"] = fastapi.__version__
        except ImportError:
            validation_results["dependencies"]["fastapi"] = "NOT_INSTALLED"
        
        try:
            import pytest
            validation_results["dependencies"]["pytest"] = pytest.__version__
        except ImportError:
            validation_results["dependencies"]["pytest"] = "NOT_INSTALLED"
        
        try:
            import uvicorn
            validation_results["dependencies"]["uvicorn"] = uvicorn.__version__
        except ImportError:
            validation_results["dependencies"]["uvicorn"] = "NOT_INSTALLED"
        
        self.results["validation"] = validation_results
        print("✅ Configuration validation completed")
        
        return validation_results
    
    def check_system_requirements(self) -> Dict:
        """Check system requirements for deployment."""
        print("🖥️  Checking system requirements...")
        
        requirements = {
            "python_version": {
                "required": "3.8+",
                "current": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "satisfied": sys.version_info >= (3, 8)
            },
            "disk_space": {},
            "memory": {},
            "ports": {}
        }
        
        # Check disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.project_root)
            requirements["disk_space"] = {
                "total_gb": total // (1024**3),
                "free_gb": free // (1024**3),
                "sufficient": free > 1024**3  # At least 1GB free
            }
        except Exception as e:
            requirements["disk_space"]["error"] = str(e)
        
        # Check if ports are available (basic check)
        requirements["ports"]["8000"] = self._check_port(8000)
        requirements["ports"]["8080"] = self._check_port(8080)
        
        self.results["system_requirements"] = requirements
        print("✅ System requirements check completed")
        
        return requirements
    
    def _check_port(self, port: int) -> bool:
        """Check if a port is available."""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return True
        except OSError:
            return False
    
    def generate_deployment_artifacts(self) -> Dict:
        """Generate deployment artifacts."""
        print("📦 Generating deployment artifacts...")
        
        artifacts = {
            "dockerfile": self._generate_dockerfile(),
            "docker_compose": self._generate_docker_compose(),
            "startup_script": self._generate_startup_script(),
            "health_check": self._generate_health_check()
        }
        
        self.results["artifacts"] = artifacts
        print("✅ Deployment artifacts generated")
        
        return artifacts
    
    def _generate_dockerfile(self) -> str:
        """Generate Dockerfile for containerized deployment."""
        dockerfile_content = """# Multi-stage Dockerfile for AI Video Editor
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    ffmpeg \\
    libsm6 \\
    libxext6 \\
    libfontconfig1 \\
    libxrender1 \\
    libgl1-mesa-glx \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads outputs logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
"""
        
        dockerfile_path = self.project_root / "Dockerfile"
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)
        
        return str(dockerfile_path)
    
    def _generate_docker_compose(self) -> str:
        """Generate Docker Compose file."""
        compose_content = """version: '3.8'

services:
  ai-video-editor:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
"""
        
        compose_path = self.project_root / "docker-compose.yml"
        with open(compose_path, "w") as f:
            f.write(compose_content)
        
        return str(compose_path)
    
    def _generate_startup_script(self) -> str:
        """Generate startup script."""
        startup_content = """#!/bin/bash
# AI Video Editor Startup Script

set -e

echo "🚀 Starting AI Video Editor..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p uploads outputs logs

# Run database migrations if needed
# python manage.py migrate

# Start the application
echo "🌟 Starting application server..."
uvicorn backend.api:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info
"""
        
        startup_path = self.project_root / "start.sh"
        with open(startup_path, "w") as f:
            f.write(startup_content)
        
        # Make executable
        os.chmod(startup_path, 0o755)
        
        return str(startup_path)
    
    def _generate_health_check(self) -> str:
        """Generate health check script."""
        health_check_content = """#!/usr/bin/env python3
import requests
import sys
import json

def check_health():
    try:
        # Check main health endpoint
        response = requests.get("http://localhost:8000/health", timeout=10)
        
        if response.status_code == 200:
            print("✅ Main application: HEALTHY")
            health_data = response.json()
            print(f"Status: {health_data.get('status', 'unknown')}")
        else:
            print(f"❌ Main application: UNHEALTHY (status: {response.status_code})")
            return False
        
        # Check API endpoints
        root_response = requests.get("http://localhost:8000/", timeout=5)
        if root_response.status_code == 200:
            print("✅ API root: ACCESSIBLE")
        else:
            print(f"⚠️  API root: ISSUE (status: {root_response.status_code})")
        
        print("🎉 Overall health check: PASSED")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    if check_health():
        sys.exit(0)
    else:
        sys.exit(1)
"""
        
        health_check_path = self.project_root / "health_check.py"
        with open(health_check_path, "w") as f:
            f.write(health_check_content)
        
        return str(health_check_path)
    
    def assess_deployment_readiness(self) -> bool:
        """Assess overall deployment readiness."""
        print("🔍 Assessing deployment readiness...")
        
        # Check test pass rate
        test_pass_rate = self.results.get("tests", {}).get("summary", {}).get("pass_rate", 0)
        tests_ready = test_pass_rate >= 80  # At least 80% pass rate
        
        # Check configuration
        config_files = self.results.get("validation", {}).get("config_files", {})
        essential_files_exist = all(
            config_files.get(f, {}).get("exists", False) 
            for f in ["config.py", "requirements.txt", "backend/api.py"]
        )
        
        # Check system requirements
        system_reqs = self.results.get("system_requirements", {})
        python_ok = system_reqs.get("python_version", {}).get("satisfied", False)
        disk_ok = system_reqs.get("disk_space", {}).get("sufficient", False)
        
        # Overall assessment
        ready = tests_ready and essential_files_exist and python_ok and disk_ok
        
        self.results["ready_for_deployment"] = ready
        
        print(f"📊 Deployment Readiness Assessment:")
        print(f"   Tests: {'✅' if tests_ready else '❌'} ({test_pass_rate:.1f}% pass rate)")
        print(f"   Config: {'✅' if essential_files_exist else '❌'}")
        print(f"   Python: {'✅' if python_ok else '❌'}")
        print(f"   Disk: {'✅' if disk_ok else '❌'}")
        print(f"   Overall: {'✅ READY' if ready else '❌ NOT READY'}")
        
        return ready
    
    def generate_deployment_report(self) -> str:
        """Generate comprehensive deployment report."""
        report_path = self.project_root / "deployment_report.json"
        
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"📋 Deployment report saved to: {report_path}")
        return str(report_path)
    
    def run_all_checks(self) -> Dict:
        """Run all deployment preparation checks."""
        print("🎯 Running comprehensive deployment preparation...")
        print("=" * 60)
        
        # Run all checks
        self.run_comprehensive_tests()
        self.validate_configuration()
        self.check_system_requirements()
        self.generate_deployment_artifacts()
        self.assess_deployment_readiness()
        
        # Generate final report
        report_path = self.generate_deployment_report()
        
        print("=" * 60)
        print("🏁 Deployment preparation completed!")
        print(f"📋 Full report: {report_path}")
        
        if self.results["ready_for_deployment"]:
            print("🎉 Application is READY for deployment!")
        else:
            print("⚠️  Application needs fixes before deployment")
        
        return self.results

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Video Editor Deployment Preparation")
    parser.add_argument("--project-root", help="Project root directory", default=".")
    parser.add_argument("--tests-only", action="store_true", help="Run tests only")
    parser.add_argument("--artifacts-only", action="store_true", help="Generate artifacts only")
    
    args = parser.parse_args()
    
    prep = DeploymentPreparation(args.project_root)
    
    if args.tests_only:
        prep.run_comprehensive_tests()
    elif args.artifacts_only:
        prep.generate_deployment_artifacts()
    else:
        prep.run_all_checks()

if __name__ == "__main__":
    main()
