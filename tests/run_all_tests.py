import unittest
import sys
import os

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Discover and run all tests in the 'tests' directory
loader = unittest.TestLoader()
suite = loader.discover('tests')

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

if result.wasSuccessful():
    print("All tests passed!")
else:
    print("Some tests failed.")
