import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import os
import sys
from io import StringIO
from forecast import main

class TestCLI(unittest.TestCase):
    def setUp(self):
        # Create sample data for testing
        dates = pd.date_range(start='2024-01-01', periods=100, freq='H')
        self.sample_data = pd.DataFrame({
            'timestamp': dates,
            'lat': [55.7558] * 100,
            'lon': [37.6173] * 100,
            'elevation_m': [156] * 100,
            'temperature': np.linspace(20, 25, 100) + np.random.normal(0, 1, 100),
            'humidity': np.linspace(60, 70, 100) + np.random.normal(0, 2, 100),
            'pressure': np.linspace(1013, 1015, 100) + np.random.normal(0, 0.5, 100)
        })
        
        # Create a temporary CSV file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        self.sample_data.to_csv(self.temp_file.name, index=False)
        self.temp_file.close()
        
        # Save original stdout
        self.original_stdout = sys.stdout
        self.captured_output = StringIO()
        sys.stdout = self.captured_output

    def tearDown(self):
        # Clean up the temporary file
        os.unlink(self.temp_file.name)
        
        # Restore stdout
        sys.stdout = self.original_stdout

    def test_cli_with_required_args(self):
        """Test CLI with required arguments"""
        # Set up command line arguments
        sys.argv = ['forecast.py', '--data', self.temp_file.name]
        
        # Run main function
        main()
        
        # Check if forecast.csv was created
        self.assertTrue(os.path.exists('forecast.csv'))
        
        # Check if output message is correct
        output = self.captured_output.getvalue()
        self.assertIn('Forecast saved to: forecast.csv', output)
        
        # Clean up forecast.csv
        os.unlink('forecast.csv')

    def test_cli_with_alpha(self):
        """Test CLI with alpha parameter"""
        # Set up command line arguments
        sys.argv = ['forecast.py', '--data', self.temp_file.name, '--alpha', '0.95']
        
        # Run main function
        main()
        
        # Check if forecast.csv was created
        self.assertTrue(os.path.exists('forecast.csv'))
        
        # Check if output message is correct
        output = self.captured_output.getvalue()
        self.assertIn('Forecast saved to: forecast.csv', output)
        
        # Clean up forecast.csv
        os.unlink('forecast.csv')

    def test_cli_missing_required_arg(self):
        """Test CLI with missing required argument"""
        # Set up command line arguments without --data
        sys.argv = ['forecast.py']
        
        # Run main function and check if it raises SystemExit
        with self.assertRaises(SystemExit):
            main()

    def test_cli_invalid_alpha(self):
        """Test CLI with invalid alpha value"""
        # Set up command line arguments with invalid alpha
        sys.argv = ['forecast.py', '--data', self.temp_file.name, '--alpha', '1.5']
        
        # Run main function and check if it raises SystemExit
        with self.assertRaises(SystemExit):
            main()

if __name__ == '__main__':
    unittest.main() 