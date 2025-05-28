import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import os
from forecast import train_model, predict_one_day, load_data

class TestModel(unittest.TestCase):
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

    def tearDown(self):
        # Clean up the temporary file
        os.unlink(self.temp_file.name)

    def test_model_training(self):
        """Test if models are trained correctly"""
        models = train_model(self.temp_file.name)
        
        # Check if models are created for all targets
        targets = ['temperature', 'humidity', 'pressure']
        for target in targets:
            self.assertIn(target, models)
            # Check if all model types are present
            self.assertIn('lower', models[target])
            self.assertIn('pred', models[target])
            self.assertIn('upper', models[target])
            
            # Check if models are trained
            for model_type, model in models[target].items():
                self.assertTrue(hasattr(model, 'predict'))

    def test_prediction_format(self):
        """Test if predictions are in correct format"""
        # Train model
        models = train_model(self.temp_file.name)
        
        # Load latest data
        latest_data = load_data(self.temp_file.name)
        
        # Make prediction
        forecast = predict_one_day(models, latest_data)
        
        # Check if all required columns are present
        required_columns = [
            'target_date',
            'temperature_pred', 'temperature_low', 'temperature_high',
            'humidity_pred', 'humidity_low', 'humidity_high',
            'pressure_pred', 'pressure_low', 'pressure_high'
        ]
        for col in required_columns:
            self.assertIn(col, forecast.columns)
        
        # Check if target_date is in the future
        self.assertTrue(forecast['target_date'].iloc[0] > latest_data.index[-1])

    def test_prediction_intervals(self):
        """Test if prediction intervals are valid"""
        # Train model
        models = train_model(self.temp_file.name)
        
        # Load latest data
        latest_data = load_data(self.temp_file.name)
        
        # Make prediction
        forecast = predict_one_day(models, latest_data)
        
        # Check if prediction intervals are valid
        for target in ['temperature', 'humidity', 'pressure']:
            self.assertTrue(
                (forecast[f'{target}_low'] <= forecast[f'{target}_pred']).all()
            )
            self.assertTrue(
                (forecast[f'{target}_pred'] <= forecast[f'{target}_high']).all()
            )

    def test_prediction_with_different_alpha(self):
        """Test if different alpha values affect prediction intervals"""
        # Train model
        models = train_model(self.temp_file.name)
        
        # Load latest data
        latest_data = load_data(self.temp_file.name)
        
        # Make predictions with different alpha values
        forecast_90 = predict_one_day(models, latest_data, alpha=0.9)
        forecast_95 = predict_one_day(models, latest_data, alpha=0.95)
        
        # Check if intervals are wider for higher alpha
        for target in ['temperature', 'humidity', 'pressure']:
            interval_90 = forecast_90[f'{target}_high'] - forecast_90[f'{target}_low']
            interval_95 = forecast_95[f'{target}_high'] - forecast_95[f'{target}_low']
            self.assertTrue((interval_95 >= interval_90).all())

if __name__ == '__main__':
    unittest.main() 