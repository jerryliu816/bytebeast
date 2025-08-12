#!/usr/bin/env python3
"""
ByteBeast Test Runner

Runs all tests and provides summary report.
"""

import unittest
import sys
import logging
from pathlib import Path

# Add bytebeast to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Suppress debug logging during tests
logging.getLogger().setLevel(logging.WARNING)


def run_all_tests():
    """Run all ByteBeast tests."""
    print("ByteBeast Test Suite")
    print("===================")
    
    # Discover and run tests
    loader = unittest.TestLoader()
    test_dir = Path(__file__).parent
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Print summary
    print("\nTest Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\nFailures:")
        for test, failure in result.failures:
            print(f"  {test}: {failure.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\nErrors:")
        for test, error in result.errors:
            print(f"  {test}: {error.split('Exception:')[-1].strip()}")
    
    # Return success status
    return len(result.failures) == 0 and len(result.errors) == 0


def run_specific_test(test_name):
    """Run a specific test module."""
    if not test_name.startswith('test_'):
        test_name = f"test_{test_name}"
    
    try:
        module = __import__(test_name)
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return len(result.failures) == 0 and len(result.errors) == 0
        
    except ImportError as e:
        print(f"Error importing test module '{test_name}': {e}")
        return False


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
    else:
        success = run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()