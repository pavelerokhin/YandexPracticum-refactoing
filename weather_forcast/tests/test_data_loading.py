import unittest
import pandas as pd
import numpy as np
from datetime import datetime
import tempfile
import os
from forecast import load_data

class TestDataLoading(unittest.TestCase):
    def setUp(self):
        # Create sample data for testing
        self.sample_data = pd.DataFrame({
            'timestamp': [
                '2024-01-01T00:00:00Z',
                '2024-01-01T01:00:00Z',
                '2024-01-01T02:00:00Z'
            ],
            'lat': [55.7558, 55.7558, 55.7558],
            'lon': [37.6173, 37.6173, 37.6173],
            'elevation_m': [156, 156, 156],
            'temperature': [20.0, 21.0, 22.0],
            'humidity': [65, 66, 67],
            'pressure': [1013, 1014, 1015]
        })
        
        # Create a temporary CSV file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        self.sample_data.to_csv(self.temp_file.name, index=False)
        self.temp_file.close()

    def tearDown(self):
        # Clean up the temporary file
        os.unlink(self.temp_file.name)

    def test_load_data_success(self):
        """Test successful data loading"""
        df = load_data(self.temp_file.name)
        
        # Check if timestamp is set as index
        self.assertIsInstance(df.index, pd.DatetimeIndex)
        
        # Check if data is sorted
        self.assertTrue(df.index.is_monotonic_increasing)
        
        # Check if all required columns are present
        required_columns = ['lat', 'lon', 'elevation_m', 'temperature', 'humidity', 'pressure']
        for col in required_columns:
            self.assertIn(col, df.columns)

    def test_load_data_missing_values(self):
        """Test handling of missing values"""
        # Create data with missing values
        data_with_missing = self.sample_data.copy()
        data_with_missing.loc[0, 'temperature'] = np.nan
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        data_with_missing.to_csv(temp_file.name, index=False)
        temp_file.close()
        
        # Test that ValueError is raised
        with self.assertRaises(ValueError):
            load_data(temp_file.name)
        
        # Clean up
        os.unlink(temp_file.name)

    def test_load_data_invalid_timestamp(self):
        """Test handling of invalid timestamp format"""
        # Create data with invalid timestamp
        invalid_data = self.sample_data.copy()
        invalid_data.loc[0, 'timestamp'] = 'invalid_timestamp'
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        invalid_data.to_csv(temp_file.name, index=False)
        temp_file.close()
        
        # Test that error is raised
        with self.assertRaises(Exception):
            load_data(temp_file.name)
        
        # Clean up
        os.unlink(temp_file.name)

if __name__ == '__main__':
    unittest.main() 