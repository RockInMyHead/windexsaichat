#!/usr/bin/env python3
"""
Test runner script for WindexAI
"""
import subprocess
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_command(cmd, description):
    """Run command and print results"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print('='*60)

    try:
        result = subprocess.run(cmd, shell=True, cwd=project_root, capture_output=True, text=True)

        if result.stdout:
            print("📝 OUTPUT:")
            print(result.stdout)

        if result.stderr:
            print("⚠️  STDERR:")
            print(result.stderr)

        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            return True
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
            return False

    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 WindexAI Test Suite")
    print("======================")

    # Check if we're in virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not running in virtual environment")

    # Install test dependencies
    if not run_command("pip install -r tests/requirements.txt", "Installing test dependencies"):
        return False

    results = []

    # Unit Tests
    print("\n🎯 UNIT TESTS")
    results.append(run_command(
        "python -m pytest tests/unit/ -v --tb=short --cov=services --cov-report=term-missing",
        "Running unit tests with coverage"
    ))

    # Integration Tests
    print("\n🔗 INTEGRATION TESTS")
    results.append(run_command(
        "python -m pytest tests/integration/ -v --tb=short",
        "Running integration tests"
    ))

    # Load Tests (if locust is available)
    print("\n⚡ LOAD TESTS")
    print("💡 Load tests require a running server. Start the server first:")
    print("   python main_refactored.py")
    print("💡 Then run in another terminal:")
    print("   locust -f tests/load/locustfile.py --host=http://localhost:8003")
    print("💡 Or run web interface:")
    print("   locust -f tests/load/locustfile.py --host=http://localhost:8003 --web-host=localhost --web-port=8089")

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        return True
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total} passed)")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
