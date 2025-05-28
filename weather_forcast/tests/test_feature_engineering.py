import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from forecast import make_features

class TestFeatureEngineering(unittest.TestCase):
    def setUp(self):
        # Create sample data with datetime index
        dates = pd.date_range(start='2024-01-01', periods=48, freq='H')
        self.sample_data = pd.DataFrame({
            'lat': [55.7558] * 48,
            'lon': [37.6173] * 48,
            'elevation_m': [156] * 48,
            'temperature': np.linspace(20, 25, 48),
            'humidity': np.linspace(60, 70, 48),
            'pressure': np.linspace(1013, 1015, 48)
        }, index=dates)

    def test_feature_creation(self):
        """Test if all required features are created"""
        features = make_features(self.sample_data)
        
        # Check if seasonal features are created
        seasonal_features = ['sin_month', 'cos_month', 'sin_day', 'cos_day']
        for feature in seasonal_features:
            self.assertIn(feature, features.columns)
        
        # Check if rolling means are created
        rolling_features = ['temperature_rolling_mean_24h', 
                          'humidity_rolling_mean_24h',
                          'pressure_rolling_mean_24h']
        for feature in rolling_features:
            self.assertIn(feature, features.columns)

    def test_seasonal_features_range(self):
        """Test if seasonal features are within correct ranges"""
        features = make_features(self.sample_data)
        
        # Check sine/cosine ranges
        for feature in ['sin_month', 'sin_day']:
            self.assertTrue(features[feature].between(-1, 1).all())
        for feature in ['cos_month', 'cos_day']:
            self.assertTrue(features[feature].between(-1, 1).all())

    def test_rolling_means(self):
        """Test if rolling means are calculated correctly"""
        features = make_features(self.sample_data)
        
        # Check if rolling means are calculated for the last 24 hours
        for col in ['temperature', 'humidity', 'pressure']:
            rolling_col = f'{col}_rolling_mean_24h'
            # First 23 values should be NaN (not enough data for 24h window)
            self.assertTrue(features[rolling_col].iloc[:23].isna().all())
            # After that, should have values
            self.assertTrue(features[rolling_col].iloc[23:].notna().all())

    def test_original_data_preservation(self):
        """Test if original data is preserved"""
        features = make_features(self.sample_data)
        
        # Check if original columns are preserved
        original_columns = ['lat', 'lon', 'elevation_m', 'temperature', 'humidity', 'pressure']
        for col in original_columns:
            self.assertIn(col, features.columns)
            # Check if values are preserved
            pd.testing.assert_series_equal(
                features[col],
                self.sample_data[col],
                check_names=False
            )

    def test_timestamp_features_removal(self):
        """Test if temporary timestamp features are removed"""
        features = make_features(self.sample_data)
        
        # Check if temporary columns are removed
        temp_columns = ['month', 'day_of_year', 'hour']
        for col in temp_columns:
            self.assertNotIn(col, features.columns)

if __name__ == '__main__':
    unittest.main() 