#!/usr/bin/env python3
"""
Test runner script for the weather forecast project.
"""

import unittest
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import all test modules
from tests.test_data_loading import TestDataLoading
from tests.test_feature_engineering import TestFeatureEngineering
from tests.test_model import TestModel
from tests.test_cli import TestCLI

def run_tests():
    """Run all test cases."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestDataLoading))
    test_suite.addTest(unittest.makeSuite(TestFeatureEngineering))
    test_suite.addTest(unittest.makeSuite(TestModel))
    test_suite.addTest(unittest.makeSuite(TestCLI))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return appropriate exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests()) 