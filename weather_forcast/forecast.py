#!/usr/bin/env python3
"""
Weather forecast script that predicts temperature, humidity, and pressure
for a given geographical region using historical weather data.
"""

import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
TARGETS = ['temperature', 'humidity', 'pressure']
MODEL_PARAMS = {
    'n_estimators': 200,
    'max_depth': 5,
    'learning_rate': 0.1,
    'random_state': 42
}


def validate_data(df: pd.DataFrame) -> None:
    """
    Validate the input data for required columns and value ranges.
    
    Args:
        df: Input DataFrame with weather data
        
    Raises:
        ValueError: If data validation fails
    """
    # Check required columns
    required_columns = ['time'] + TARGETS
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Check value ranges based on actual data
    if (df['temperature'] < 1.6).any() or (df['temperature'] > 20.6).any():
        raise ValueError("Temperature values out of observed range (1.6 to 20.6)")
    if (df['humidity'] < 40).any() or (df['humidity'] > 96).any():
        raise ValueError("Humidity values out of observed range (40 to 96)")
    if (df['pressure'] < 998.1).any() or (df['pressure'] > 1032.7).any():
        raise ValueError("Pressure values out of observed range (998.1 to 1032.7)")


def load_data(path_to_csv: str) -> pd.DataFrame:
    """
    Load and preprocess the weather history data.
    
    Args:
        path_to_csv: Path to the CSV file with weather history
        
    Returns:
        Preprocessed DataFrame with datetime index
    """
    logger.info(f"Loading data from {path_to_csv}")
    df = pd.read_csv(path_to_csv)
    
    # Validate data
    validate_data(df)
    
    # Convert time column to datetime
    df['time'] = pd.to_datetime(df['time'])
    df.set_index('time', inplace=True)
    df.sort_index(inplace=True)
    
    # Check for missing values
    if df.isnull().any().any():
        raise ValueError("Input data contains missing values")
    
    logger.info(f"Loaded {len(df)} records")
    return df


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create time-based and climate features from the input data.
    
    Args:
        df: Input DataFrame with weather data
        
    Returns:
        DataFrame with additional features
    """
    # Create a copy to avoid modifying the original
    features = df.copy()
    
    # Time-based features
    features['month'] = features.index.month
    features['day_of_year'] = features.index.dayofyear
    features['day_of_week'] = features.index.dayofweek
    
    # Seasonal features using sine/cosine
    features['sin_month'] = np.sin(2 * np.pi * features['month'] / 12)
    features['cos_month'] = np.cos(2 * np.pi * features['month'] / 12)
    features['sin_day'] = np.sin(2 * np.pi * features['day_of_year'] / 365)
    features['cos_day'] = np.cos(2 * np.pi * features['day_of_year'] / 365)
    
    # Rolling means for different windows
    for col in TARGETS:
        # 7-day rolling mean
        features[f'{col}_rolling_mean_7d'] = features[col].rolling(window=7, min_periods=1).mean()
        # 7-day rolling std
        features[f'{col}_rolling_std_7d'] = features[col].rolling(window=7, min_periods=1).std()
        # 7-day rolling min/max
        features[f'{col}_rolling_min_7d'] = features[col].rolling(window=7, min_periods=1).min()
        features[f'{col}_rolling_max_7d'] = features[col].rolling(window=7, min_periods=1).max()
    
    # Lag features (previous day values)
    for col in TARGETS:
        features[f'{col}_lag_1'] = features[col].shift(1)
    
    # Drop the original timestamp-based columns as they're now in the index
    features = features.drop(['month', 'day_of_year', 'day_of_week'], axis=1)
    
    # Drop rows with NaN values (from lag features)
    features = features.dropna()
    
    return features


def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculate evaluation metrics for the model.
    
    Args:
        y_true: True target values
        y_pred: Predicted values
        
    Returns:
        Dictionary with evaluation metrics
    """
    return {
        'mae': mean_absolute_error(y_true, y_pred),
        'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
        'r2': r2_score(y_true, y_pred)
    }


def train_model(path_to_csv: str, save_model: bool = True) -> Tuple[Dict, Dict]:
    """
    Train the weather forecasting model.
    
    Args:
        path_to_csv: Path to the CSV file with weather history
        save_model: Whether to save the trained model
        
    Returns:
        Tuple of (models dictionary, evaluation metrics)
    """
    logger.info("Starting model training")
    
    # Load and preprocess data
    df = load_data(path_to_csv)
    features = make_features(df)
    
    # Split data into train and test sets
    train_size = int(len(features) * 0.8)
    train_data = features.iloc[:train_size]
    test_data = features.iloc[train_size:]
    
    # Prepare target variables
    X_train = train_data.drop(TARGETS, axis=1)
    X_test = test_data.drop(TARGETS, axis=1)
    
    models = {}
    metrics = {}
    
    for target in TARGETS:
        logger.info(f"Training model for {target}")
        y_train = train_data[target]
        y_test = test_data[target]
        
        # Train models for different quantiles
        models[target] = {
            'lower': GradientBoostingRegressor(
                loss='quantile',
                alpha=0.1,
                **MODEL_PARAMS
            ),
            'pred': GradientBoostingRegressor(
                loss='squared_error',
                **MODEL_PARAMS
            ),
            'upper': GradientBoostingRegressor(
                loss='quantile',
                alpha=0.9,
                **MODEL_PARAMS
            )
        }
        
        # Train each model
        for model_type, model in models[target].items():
            model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = models[target]['pred'].predict(X_test)
        metrics[target] = evaluate_model(y_test, y_pred)
        logger.info(f"Metrics for {target}: {metrics[target]}")
    
    # Save models if requested
    if save_model:
        model_dir = Path('models')
        model_dir.mkdir(exist_ok=True)
        
        for target in TARGETS:
            for model_type, model in models[target].items():
                model_path = model_dir / f'{target}_{model_type}.joblib'
                joblib.dump(model, model_path)
        
        # Save metrics
        with open(model_dir / 'metrics.json', 'w') as f:
            json.dump(metrics, f, indent=4)
        
        logger.info("Models and metrics saved to 'models' directory")
    
    return models, metrics


def load_trained_models() -> Optional[Dict]:
    """
    Load trained models from disk.
    
    Returns:
        Dictionary of trained models or None if models don't exist
    """
    model_dir = Path('models')
    if not model_dir.exists():
        return None
    
    models = {}
    for target in TARGETS:
        models[target] = {}
        for model_type in ['lower', 'pred', 'upper']:
            model_path = model_dir / f'{target}_{model_type}.joblib'
            if not model_path.exists():
                return None
            models[target][model_type] = joblib.load(model_path)
    
    return models


def predict_days(model: Dict, latest_rows_df: pd.DataFrame, 
                days_ahead: int = 1, alpha: float = 0.9) -> pd.DataFrame:
    """
    Make predictions for multiple days ahead.
    
    Args:
        model: Dictionary of trained models
        latest_rows_df: DataFrame with the latest weather data
        days_ahead: Number of days to predict
        alpha: Confidence level for prediction intervals
        
    Returns:
        DataFrame with predictions and confidence intervals
    """
    logger.info(f"Making predictions for {days_ahead} days ahead")
    
    # Create features for prediction
    features = make_features(latest_rows_df)
    
    # Get the last row for initial prediction
    current_features = features.iloc[[-1]].copy()
    
    predictions = []
    for day in range(days_ahead):
        # Make predictions for current day
        day_predictions = {}
        for target in TARGETS:
            # Drop target columns before prediction
            pred_features = current_features.drop(TARGETS, axis=1)
            day_predictions[f'{target}_pred'] = model[target]['pred'].predict(pred_features)[0]
            day_predictions[f'{target}_low'] = model[target]['lower'].predict(pred_features)[0]
            day_predictions[f'{target}_high'] = model[target]['upper'].predict(pred_features)[0]
        
        # Add target date
        target_date = latest_rows_df.index[-1] + timedelta(days=day + 1)
        day_predictions['target_date'] = target_date
        
        predictions.append(day_predictions)
        
        # Update features for next day prediction
        for target in TARGETS:
            current_features[f'{target}_lag_1'] = day_predictions[f'{target}_pred']
    
    return pd.DataFrame(predictions)


def main():
    parser = argparse.ArgumentParser(description='Weather forecast script')
    parser.add_argument('--data', required=True, help='Path to weather history CSV file')
    parser.add_argument('--days', type=int, default=1, help='Number of days to predict')
    parser.add_argument('--alpha', type=float, default=0.9, help='Confidence level for prediction intervals')
    parser.add_argument('--retrain', action='store_true', help='Force model retraining')
    args = parser.parse_args()
    
    try:
        # Try to load existing models
        models = None if args.retrain else load_trained_models()
        
        # Train new models if needed
        if models is None:
            logger.info("Training new models")
            models, metrics = train_model(args.data)
        else:
            logger.info("Using existing trained models")
        
        # Load latest data for prediction
        latest_data = load_data(args.data)
        
        # Make predictions
        forecast = predict_days(models, latest_data, args.days, args.alpha)
        
        # Save forecast
        output_path = 'forecast.csv'
        forecast.to_csv(output_path, index=False)
        logger.info(f"Forecast saved to: {output_path}")
        
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    main() 