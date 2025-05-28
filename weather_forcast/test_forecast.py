import unittest
import pandas as pd
import numpy as np
from datetime import datetime
from forecast import (
    validate_data,
    make_features,
    evaluate_model,
    TARGETS
)

class TestForecast(unittest.TestCase):
    def setUp(self):
        # Create sample data for testing
        self.sample_data = pd.DataFrame({
            'time': pd.date_range(start='2025-02-28', periods=5),
            'temperature': [3.4, 3.4, 3.5, 5.5, 4.8],
            'humidity': [96, 88, 85, 73, 69],
            'pressure': [1020.8, 1029.5, 1032.7, 1028.8, 1026.0]
        })
        # Don't set index here, as validate_data expects 'time' as a column
        self.sample_data_with_index = self.sample_data.copy()
        self.sample_data_with_index.set_index('time', inplace=True)

    def test_validate_data_valid(self):
        """Test data validation with valid data"""
        try:
            validate_data(self.sample_data)  # Use data with 'time' as column
        except ValueError as e:
            self.fail(f"validate_data raised ValueError unexpectedly: {e}")

    def test_validate_data_invalid_temperature(self):
        """Test data validation with invalid temperature"""
        invalid_data = self.sample_data.copy()
        invalid_data.loc[0, 'temperature'] = 0  # Below valid range
        with self.assertRaises(ValueError):
            validate_data(invalid_data)

    def test_validate_data_missing_column(self):
        """Test data validation with missing column"""
        invalid_data = self.sample_data.drop('temperature', axis=1)
        with self.assertRaises(ValueError):
            validate_data(invalid_data)

    def test_make_features(self):
        """Test feature engineering"""
        features = make_features(self.sample_data_with_index)  # Use data with time as index
        
        # Check if all expected features are present
        expected_features = [
            'sin_month', 'cos_month', 'sin_day', 'cos_day'
        ]
        for target in TARGETS:
            expected_features.extend([
                f'{target}_rolling_mean_7d',
                f'{target}_rolling_std_7d',
                f'{target}_rolling_min_7d',
                f'{target}_rolling_max_7d',
                f'{target}_lag_1'
            ])
        
        for feature in expected_features:
            self.assertIn(feature, features.columns)

    def test_evaluate_model(self):
        """Test model evaluation metrics"""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1.1, 2.1, 2.9, 4.1, 4.9])
        
        metrics = evaluate_model(y_true, y_pred)
        
        self.assertIn('mae', metrics)
        self.assertIn('rmse', metrics)
        self.assertIn('r2', metrics)
        
        # Check if metrics are reasonable
        self.assertGreaterEqual(metrics['r2'], 0)  # R² should be positive for good predictions
        self.assertGreaterEqual(metrics['mae'], 0)  # MAE should be non-negative
        self.assertGreaterEqual(metrics['rmse'], 0)  # RMSE should be non-negative

if __name__ == '__main__':
    unittest.main() 